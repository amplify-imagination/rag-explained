"""Abstract base class for LLM providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence


class ProviderError(RuntimeError):
    """Raised when a provider is misconfigured or its backend is unavailable."""


@dataclass
class ChatResult:
    """Structured result of a chat call.

    text:           the model's textual reply
    input_tokens:   prompt token count (best-effort, may be None for ollama)
    output_tokens:  completion token count
    cost_usd:       estimated cost in USD (0.0 for local providers)
    raw_meta:       provider-specific metadata for trace inspection
    """
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float = 0.0
    raw_meta: dict | None = None


class LLMProvider(ABC):
    """Single interface for chat completions and embeddings.

    Concrete implementations must:
      * expose `name` (e.g. "gemini", "openai", "ollama")
      * expose `chat_model_name` and `embedding_model_name` for trace metadata
      * implement `embed()` and `chat()`

    The interface is intentionally narrow. Streaming, function-calling,
    and tool use are out of scope for the playlist's needs.
    """

    name: str = "abstract"
    chat_model_name: str = "?"
    embedding_model_name: str = "?"
    # Width of the embedding vector. Useful when scenes need to display dims.
    embedding_dim: int = 0

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one vector per input text."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> ChatResult:
        """Run a chat completion. Messages follow the OpenAI shape:
        [{'role': 'system'|'user'|'assistant', 'content': str}, ...].

        For vision inputs, messages may include {'role': 'user', 'image_path': '/path/to.png', 'content': 'prompt'}
        Providers that support vision must implement this; others should raise.
        """

    # Convenience for places that just want the text
    def chat_text(self, messages: list[dict], **kw) -> str:
        return self.chat(messages, **kw).text

    def info(self) -> dict:
        return {
            "provider": self.name,
            "chat_model": self.chat_model_name,
            "embedding_model": self.embedding_model_name,
            "embedding_dim": self.embedding_dim,
        }
