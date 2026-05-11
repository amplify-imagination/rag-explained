"""BGE-M3 — long-context embeddings, run locally via HuggingFace transformers.

Replaces the original Jina v3 plan for EP05's late-chunking demo. Same goals
(8K context, free, local, no API quota), cleaner load path (standard
XLM-RoBERTa, no flash-attn dance, no `trust_remote_code` dependency tree).

  embedding: BAAI/bge-m3                 (1024 dim, 8192-token context)
  chat:      not supported — use a separate provider for chat (Gemini Flash etc.)

EP05 (late chunking) composes providers explicitly:

    embedding_provider = get_provider("bge-m3")     # this module
    chat_provider      = get_provider("gemini")     # for the final answer step

Model size on disk: ~2.3 GB, downloads once into ~/.cache/huggingface/.
First call lazily loads the model onto Mac MPS (or CPU fallback).

Env:
  BGE_M3_MODEL    (override, default BAAI/bge-m3)
  BGE_M3_DEVICE   (force device: mps | cpu | cuda; default = auto)
"""
from __future__ import annotations

import os
import sys
from typing import Sequence

from .base import ChatResult, LLMProvider, ProviderError


class BGEM3Provider(LLMProvider):
    name = "bge-m3"

    def __init__(self) -> None:
        # Lazy imports so a missing torch doesn't break gemini/openai users.
        try:
            import torch  # noqa: F401
            from transformers import AutoModel, AutoTokenizer  # noqa: F401
        except ImportError as exc:
            raise ProviderError(
                "bge-m3 requires `torch` and `transformers`. "
                "Install with: pip install torch transformers --break-system-packages"
            ) from exc

        import torch
        from transformers import AutoModel, AutoTokenizer

        forced = os.getenv("BGE_M3_DEVICE")
        if forced:
            self.device = forced
        elif torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"

        self.model_name = os.getenv("BGE_M3_MODEL", "BAAI/bge-m3")
        self.embedding_model_name = self.model_name
        self.embedding_dim = 1024  # bge-m3 default

        # Sentinel — chat is NOT supported.
        self.chat_model_name = "(bge-m3: embed-only; pair with a chat provider)"

        print(
            f"[bge-m3] loading {self.model_name} on {self.device} "
            f"(first call downloads ~2.3 GB into ~/.cache/huggingface/)",
            file=sys.stderr,
        )
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModel.from_pretrained(self.model_name).to(self.device).eval()
        self._torch = torch
        self._max_length = 8192

    # ── Standard pooled embeddings (one vector per input text) ─────────
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one normalized 1024-dim vector per input text.

        Uses CLS pooling — BGE-M3's recommended pattern for dense retrieval.
        Mean pooling also works but CLS is what the model card uses.
        """
        if not texts:
            return []
        torch = self._torch
        # Process in batches of 8 to keep MPS memory reasonable on a Mac mini.
        BATCH = 8
        out: list[list[float]] = []
        for i in range(0, len(texts), BATCH):
            batch = list(texts[i : i + BATCH])
            enc = self._tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=self._max_length,
                return_tensors="pt",
            ).to(self.device)
            with torch.no_grad():
                model_out = self._model(**enc)
            # CLS pooling: take the first token's vector.
            cls_vecs = model_out.last_hidden_state[:, 0]
            # L2 normalize for cosine similarity.
            cls_vecs = torch.nn.functional.normalize(cls_vecs, p=2, dim=1)
            out.extend(cls_vecs.detach().cpu().tolist())
        return out

    def embed_query(self, text: str) -> list[float]:
        """Embed a query string. BGE-M3 is symmetric — same path as embed()."""
        return self.embed([text])[0]

    # ── Late chunking — the EP05-specific method ───────────────────────
    def embed_late(
        self,
        document: str,
        chunk_boundaries: list[tuple[int, int]],
    ) -> list[list[float]]:
        """Late chunking: embed the full document once, then pool token
        embeddings into chunk vectors using each chunk's character range.

        chunk_boundaries: list of (char_start, char_end) tuples in `document`.
        Returns: one L2-normalized 1024-dim vector per chunk.

        Pattern: tokenize the FULL document with offset_mapping, single forward
        pass through the encoder to get token-level last_hidden_state, then for
        each chunk's char range mean-pool the tokens whose offsets overlap it.
        This is the canonical late-chunking technique applied to BGE-M3.
        """
        if not chunk_boundaries:
            return []

        # 1. Tokenize the full document with offset mapping so we know which
        #    character range each token covers.
        enc = self._tokenizer(
            document,
            return_tensors="pt",
            return_offsets_mapping=True,
            truncation=True,
            max_length=self._max_length,
        )
        offsets = enc.pop("offset_mapping")[0].tolist()  # list[(char_start, char_end)]
        model_inputs = {k: v.to(self.device) for k, v in enc.items()}

        # 2. Forward pass — last_hidden_state has shape (1, T, D).
        with self._torch.no_grad():
            out = self._model(**model_inputs)
        token_embeddings = out.last_hidden_state[0]  # shape (T, D)

        # 3. For each requested chunk, mean-pool tokens whose char range
        #    overlaps the chunk's char range.
        chunk_vectors: list[list[float]] = []
        torch = self._torch
        for char_start, char_end in chunk_boundaries:
            mask_idx = [
                i for i, (t_s, t_e) in enumerate(offsets)
                if t_s != t_e and t_s < char_end and t_e > char_start
            ]
            if not mask_idx:
                # Should not happen if chunk_boundaries are valid char ranges
                # in `document`. Defensive fallback.
                chunk_vectors.append([0.0] * token_embeddings.shape[1])
                continue
            idx_tensor = torch.tensor(mask_idx, device=token_embeddings.device)
            pooled = token_embeddings.index_select(0, idx_tensor).mean(dim=0)
            # L2 normalize for cosine similarity.
            pooled = pooled / (pooled.norm() + 1e-9)
            chunk_vectors.append(pooled.detach().cpu().tolist())

        return chunk_vectors

    # ── Chat is intentionally unsupported ──────────────────────────────
    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> ChatResult:
        raise ProviderError(
            "BGEM3Provider is embed-only. EP05 composes providers: use "
            "get_provider('bge-m3') for embeddings and "
            "get_provider('gemini') for the answer step. "
            "See ep05-late-chunking/impl/pipeline.py for the pattern."
        )
