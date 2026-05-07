# Lumenflow weekly product meeting — notes

These are the notes from the weekly product meeting at Lumenflow over a 10-week period. The notes are designed for the late-chunking demo. Each meeting references decisions from earlier meetings in a way that is only resolvable with the prior context — naive chunking by meeting isolates the references and produces wrong answers when queried.

Recurring attendees: **Sasha Chen** (VP Product), **Marcus Idris** (Head of Engineering), **Pri Veerasamy** (Design Lead), **Tomás Reyes** (Customer Success), **Hana Petersen** (Data). Other attendees noted per meeting.

---

## Meeting 1 — 2025-09-08

Attendees: Sasha, Marcus, Pri, Tomás, Hana.

Sasha kicked off the quarter. Three priorities: (a) reduce churn in the 50-200 seat segment, where renewal rates have slipped to 84%, (b) ship the long-promised custom-fields feature so we can compete on Pro pricing, (c) deliver a security-control story that lets us close two stuck Enterprise deals (Acme, Northwind).

Marcus said the platform team has capacity for two of the three. Custom fields is mostly built; a 4-week push gets it to GA. Security work is harder because it depends on the audit-log-retention rebuild that the Data team owns. Hana said audit-log retention is doable in 4 weeks if we accept a one-time backfill window.

Tomás flagged that the churn driver in the 50-200 segment is **not** missing features — it's onboarding. New workspaces that don't reach 5 active users in week 1 churn at 3x the baseline. He proposes an onboarding redesign to be scoped next week.

Decisions:

- **D1.1** Custom fields targets GA on 2025-10-13. Marcus drives.
- **D1.2** Audit-log-retention rebuild starts 2025-09-15 with a 4-week window. Hana drives.
- **D1.3** Tomás scopes the onboarding redesign for next week's meeting.

Open: Acme deal expects 7-year audit log retention; we currently support 90 days. Will the rebuild close that gap? — Hana to confirm.

---

## Meeting 2 — 2025-09-15

Attendees: Sasha, Marcus, Pri, Tomás, Hana, plus **Jordan Akehurst** (Sales, Acme account).

Tomás presented the onboarding redesign. The core insight: the empty-workspace state is what kills retention. He proposes a "starter content" pack — 3 sample projects with realistic tasks — that's auto-populated for new workspaces under 5 users. Pri took the design.

Hana confirmed the audit-log rebuild will support up to 7 years on Enterprise. That closes the gap from D1.3 — Acme's blocker. Jordan said this unlocks $410k ARR pending technical sign-off. Sasha asked for a hard date.

Marcus pushed back on stacking three workstreams. Custom fields is at risk of slipping if we add the onboarding work this quarter. He proposes deferring the onboarding redesign to next quarter; the audit-log work is already committed and not on the platform team's plate.

Decisions:

- **D2.1** Audit-log retention rebuild target completion: 2025-10-13 (same day as custom fields GA). Hana confirms feasibility next week.
- **D2.2** Onboarding redesign deferred to Q4. Tomás continues to scope; Pri's design lands by 2025-10-06 for Q4 kickoff.
- **D2.3** Acme commitment: 7-year audit log support is in by 2025-10-20. Jordan can communicate a 2025-11-01 customer go-live with a buffer.

Open: D1.3 from last week is now resolved (deferred).

---

## Meeting 3 — 2025-09-22

Attendees: Sasha, Marcus, Pri, Tomás, Hana.

Hana confirmed the 2025-10-13 target for the audit-log retention rebuild is **not** feasible — the cross-region replication step takes longer than the team modelled, primarily because eu-west-1 backup target capacity is tight. New target: 2025-10-27, two weeks slip.

Sasha asked what this does to D2.3. Jordan was on holiday but had emailed: a two-week slip is acceptable if Acme has a written commitment dated this week. Sasha will draft.

Marcus reported custom fields is on track for GA on the original 2025-10-13 date. The team built a "field templates" feature that wasn't in the original scope — a small extension that came up during dogfooding. Sasha approved keeping it in scope.

Pri showed the onboarding-redesign design. The starter-content pack will use the same 3 projects regardless of customer; content lives in `/seed/`. Pri raised that the seed projects should reflect the customer's industry but that's a follow-on, not v1.

Decisions:

- **D3.1** Audit-log retention rebuild now targets 2025-10-27. Hana drives. This supersedes D2.1.
- **D3.2** Custom fields adds field templates to v1 scope. Marcus drives. GA still 2025-10-13.
- **D3.3** Onboarding-redesign v1 ships generic seed content; per-industry seed deferred to v2.

Open: Northwind deal — same security ask as Acme, but additionally requires customer-managed encryption keys (CMEK). We don't have CMEK and it's not in any roadmap. Sasha to assess.

---

## Meeting 4 — 2025-09-29

Attendees: Sasha, Marcus, Pri, Tomás, Hana, plus **Devika Anand** (Security).

Devika joined for the CMEK discussion. CMEK is roughly 6-8 weeks of platform work, dependent on the existing key-management abstraction in KeyVault Identity (SKU-7201). She thinks we can scope it at 8 weeks if we constrain to AWS KMS only (i.e., not multi-cloud) and accept that CMEK applies only to data at rest, not in process.

Marcus said the platform team is fully booked through 2025-12-15 on custom fields, audit-log work, and a database migration. CMEK does not fit unless we drop something. He proposed dropping the data-tier migration to make room.

Sasha pushed back: Northwind ARR is $620k, the migration unlocks long-term cost savings of similar magnitude, but the ARR is in the next 6 months and the savings are in 2 years. Decision: Northwind first.

Tomás raised a concern: dropping the data-tier migration means the slow-query problem we promised to fix in Q3 stays. He'll need to set expectations with affected customers. Sasha agreed; talking points to be drafted.

Decisions:

- **D4.1** CMEK scoping locked to AWS KMS only, data-at-rest only. Devika and Marcus jointly drive.
- **D4.2** Data-tier migration deferred from Q4 to Q1. Marcus updates the public roadmap.
- **D4.3** CMEK target completion: 2025-11-24. Northwind sign-off targeted for 2025-12-08.

Open: Has anyone told the customers depending on the data-tier migration that it's slipping? — Tomás to handle by EOW.

---

## Meeting 5 — 2025-10-06

Attendees: Sasha, Marcus, Pri, Hana, Devika.

Tomás was out sick. Sasha covered for him on the customer-comms point.

Marcus reported custom fields is one week from GA (2025-10-13). All the field-templates work from D3.2 is integrated and tested. Two minor regressions found in dogfooding; both fixed.

Hana confirmed the audit-log retention rebuild is on the new 2025-10-27 target from D3.1. Cross-region replication has been validated end-to-end.

Devika gave the CMEK status: scoping is complete, AWS KMS integration design is signed off, implementation starts 2025-10-13 (same day as custom fields GA, which frees up Marcus's team).

Pri presented the design for the per-industry seed-content (the v2 from D3.3). She wants to start building it in Q4 even though it's deferred, because the design work needs longer than implementation. Sasha approved exploration; no commitment to ship in Q4.

Decisions:

- **D5.1** Pri may explore per-industry seed content design in Q4; ship date Q1 at earliest. This is a soft extension of D3.3.
- **D5.2** Custom fields GA confirmed for 2025-10-13. Final go/no-go in next week's meeting.

Open: customer comms about the data-tier migration slip (D4.2) — Tomás had not done it yet last week. Status check next meeting.

---

## Meeting 6 — 2025-10-13

Attendees: Sasha, Marcus, Pri, Tomás, Hana, Devika.

Tomás reported that the customer-comms email about D4.2 went out yesterday. 14 enterprise customers were affected; 11 acknowledged, 3 escalated. The 3 escalations are all in the slow-query slug — they wanted the migration in Q4 specifically because of the slowness. Tomás is working with sales on bridging concessions.

Custom fields shipped to GA today (D5.2). 22 workspaces enabled it in the first hour. Marcus is monitoring.

Hana said the audit-log retention rebuild is **at risk**. Cross-region replication validated last week is hitting an unexpected throughput cap when run against full production load. Estimated slip: 1-2 weeks. New target 2025-11-10 best case, 2025-11-17 worst.

Sasha said this affects the Acme commitment from D2.3, which already absorbed one slip in D3.1. She'll re-engage with Jordan.

Devika reported CMEK on track for 2025-11-24 (D4.3). The first AWS KMS key flow is working end-to-end in dev.

Decisions:

- **D6.1** Audit-log retention rebuild now targets 2025-11-17 worst case. Sasha re-communicates with Acme; Jordan involved.
- **D6.2** Tomás and Jordan jointly handle the data-tier migration escalations from D4.2; weekly check-in until resolved.

Open: do we need to expand audit-log retention to also cover SCIM events? — Devika thinks yes, will check with Northwind contacts.

---

## Meeting 7 — 2025-10-20

Attendees: Sasha, Marcus, Pri, Tomás, Hana, Devika.

Hana reported the audit-log throughput problem resolved itself once she enabled batched writes — the constraint was per-write overhead, not per-byte. The new target is back to 2025-10-27, originally promised in D3.1, which means the rebuild does **not** miss its second deadline.

Sasha re-confirmed with Jordan: Acme go-live 2025-11-03, slightly later than D2.3's 2025-11-01 because Acme themselves wanted a buffer.

Devika confirmed Northwind has reviewed the CMEK design and is satisfied. She also confirmed (re: D6 open question) that SCIM events are not in their initial requirement; we can defer SCIM event coverage to Q1.

Custom fields adoption: 180 workspaces enabled in 7 days. 8% of eligible Pro workspaces. Within our internal target of 5-15% in week 1. Tomás reported customer-survey responses are mixed: positive on the feature, several requests for "field validation" (regex, min/max). Pri scoping a v1.1.

Decisions:

- **D7.1** SCIM events in audit log deferred to Q1. Devika tracks.
- **D7.2** Custom fields v1.1 (field validation) scoped for late November. Pri leads.

Open: none.

---

## Meeting 8 — 2025-10-27

Attendees: Sasha, Marcus, Pri, Tomás, Hana, Devika.

The audit-log retention rebuild shipped today, on the D3.1 target. Acme has been told. Jordan is preparing for the 2025-11-03 go-live.

Devika reported CMEK implementation progress: 60% feature-complete, integration tests passing, on track for D4.3's 2025-11-24 target.

Pri presented the field-validation v1.1 spec from D7.2. Three validators in v1.1: regex, numeric range, date range. Marcus said this is 2-3 weeks of engineering, fits in the November window before holidays.

Tomás brought up a customer escalation: a Pro workspace owner was confused that custom-field changes apply retroactively to existing tasks. Several tasks ended up with default values they didn't expect. Pri said this is documented behaviour but the docs are clearly not enough; she'll add an in-product warning at field-creation time.

Decisions:

- **D8.1** Custom fields v1.1 (regex + numeric range + date range validation) targets ship 2025-11-21. Pri + Marcus drive.
- **D8.2** In-product warning at custom-field creation: ships immediately as a docs/UI patch, not waiting for v1.1. Pri owns.

Open: Q4 onboarding redesign launch from D2.2 — we agreed to ship in Q4 but no date set. Tomás to bring a proposal.

---

## Meeting 9 — 2025-11-03

Attendees: Sasha, Marcus, Pri, Tomás, Hana, Devika.

Acme went live this morning. Jordan was at the customer's office for the cutover. No issues reported in the first 6 hours; full audit-log retention through 7 years confirmed working. This closes D2.3.

Tomás brought a proposal for the onboarding redesign launch (D2.2 / D8 open question): ship 2025-12-01 to all new workspaces, monitor activation rates for 2 weeks, gradually expand to existing under-5-user workspaces. Sasha approved.

Pri reported the in-product warning from D8.2 shipped on Friday (2025-10-31). Already deflecting the kind of confused-user tickets that triggered D8.2.

CMEK: Devika says implementation is 80% complete. On track for 2025-11-24. Northwind contract signature targeting 2025-12-08, same week.

Decisions:

- **D9.1** Onboarding redesign launches 2025-12-01 to all new workspaces. Tomás drives launch comms; Pri supports.
- **D9.2** Plan post-launch onboarding-redesign metrics review for 2025-12-15.

Open: holiday freeze starts 2025-12-15; need to lock all Q4 ship dates by 2025-12-08.

---

## Meeting 10 — 2025-11-10

Attendees: Sasha, Marcus, Pri, Tomás, Hana, Devika.

CMEK implementation is feature-complete; in QA today and tomorrow. Tracking 2025-11-24 (D4.3). Devika: confidence high.

Custom fields v1.1 (D8.1): 60% complete. Marcus expects tracking 2025-11-21 with one day of buffer.

Sasha asked about the data-tier migration deferral (D4.2). Marcus: still on plan for Q1 start. The 3 escalated customers from D6.2 are being handled with bridging concessions Tomás is running; one signed a 6-month extension at standard rates.

Hana asked about the late-Q1 picture: now that custom fields, audit-log retention, CMEK, and onboarding redesign are all landing, what do we de-risk in Q1? Sasha said the data-tier migration is the priority, but the planning meeting is in two weeks — let's not pre-commit.

Decisions:

- **D10.1** No new commitments for Q1 until the dedicated planning meeting on 2025-11-24.
- **D10.2** Holiday freeze locked: no production deploys 2025-12-15 through 2026-01-05 except for SEV-1/2 incidents and the previously-scheduled CMEK go-live for Northwind.

Open: post-mortem on the audit-log throughput slip from D6 — has it happened? Hana will write it up by end of next week.
