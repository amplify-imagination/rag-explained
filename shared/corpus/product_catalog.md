# Lumenflow B2B software catalog

This document is the product catalog for Lumenflow's enterprise marketplace. It lists 30 fictional B2B SaaS products with stable SKU codes (`SKU-NNNN`), pricing per seat, descriptions, and technical specs in markdown tables.

The catalog is engineered to demonstrate the limits of pure-vector search. Five products in the same category have nearly identical descriptions but different SKUs — vector search returns the most semantically similar entry, but if the query specifies a SKU, it ignores that constraint. Hybrid search (BM25 + dense) recovers the correct match.

---

## Project & task management

### SKU-1042 · Lumenflow Standard

A team collaboration platform for managing projects, tasks, and deadlines across distributed teams. Includes Kanban, List, Calendar, and Gantt views with real-time multi-user editing and offline support on mobile. Suited for teams between 10 and 200 people.

**Cancellation terms.** Monthly plans can be cancelled at any time from Settings → Billing → Cancel; access continues to the end of the current billing period and no refund is issued for unused days. Annual plans can be cancelled within the first 14 days for a full refund; after that, access continues to the end of the paid year and the remainder is non-refundable. There is no restocking fee. Workspaces enter a 30-day grace period after cancellation, during which all data is recoverable; after 30 days, data is purged and cannot be restored.

| Attribute | Value |
|---|---|
| Category | Project management |
| Price per seat (monthly) | $8 |
| Storage per workspace | 50 GB |
| Members per workspace | Unlimited |
| Audit log retention | 30 days |
| SSO support | No |
| Cancellation notice | None — cancel any time |
| Refund window (annual) | 14 days |
| Restocking fee | None |
| Data grace period | 30 days |

### SKU-1043 · Lumenflow Pro

A team collaboration platform for managing projects, tasks, and deadlines across distributed teams. Adds custom fields, advanced automation, time tracking, and private projects on top of the Standard tier. Suited for organisations between 50 and 2000 people.

| Attribute | Value |
|---|---|
| Category | Project management |
| Price per seat (monthly) | $16 |
| Storage per workspace | 250 GB |
| Members per workspace | Unlimited |
| Audit log retention | 90 days |
| SSO support | SAML 2.0 |

### SKU-1044 · Lumenflow Enterprise

A team collaboration platform for managing projects, tasks, and deadlines across distributed teams. Adds SCIM, customer-managed encryption keys, audit log retention up to 7 years, and a named technical account manager. Suited for organisations of 1000+ people.

| Attribute | Value |
|---|---|
| Category | Project management |
| Price per seat (monthly) | $36 (typical) |
| Storage per workspace | 1 TB |
| Members per workspace | Unlimited |
| Audit log retention | Up to 7 years |
| SSO support | SAML 2.0 + SCIM |

### SKU-1045 · Lumenflow for Education

A team collaboration platform for managing projects, tasks, and deadlines across distributed teams, configured for academic institutions. Includes class roster sync from common LMS systems and per-semester archiving. Free for verified `.edu` domains up to 500 seats.

| Attribute | Value |
|---|---|
| Category | Project management |
| Price per seat (monthly) | $0 (under 500 seats) |
| Storage per workspace | 100 GB |
| Roster sync | Canvas, Moodle, Blackboard |
| Audit log retention | 90 days |
| SSO support | SAML 2.0 |

### SKU-1046 · Lumenflow for Non-profit

A team collaboration platform for managing projects, tasks, and deadlines across distributed teams, priced for registered non-profits. Identical features to Pro at half the per-seat cost. Requires 501(c)(3) verification.

| Attribute | Value |
|---|---|
| Category | Project management |
| Price per seat (monthly) | $8 |
| Storage per workspace | 250 GB |
| Members per workspace | Unlimited |
| Audit log retention | 90 days |
| SSO support | SAML 2.0 |

---

## Video conferencing

### SKU-2001 · MeetCadence Core

Browser-based video conferencing for distributed teams. Supports up to 25 participants per meeting, end-to-end encryption optional, recording to local file or cloud. Integrates with Lumenflow tasks for in-meeting note capture.

| Attribute | Value |
|---|---|
| Category | Video conferencing |
| Price per seat (monthly) | $6 |
| Max participants | 25 |
| Recording storage | 5 GB per user |
| E2E encryption | Optional |
| Live transcription | English only |

### SKU-2002 · MeetCadence Pro

Browser-based video conferencing for distributed teams. Increases participant cap to 100, adds breakout rooms, polls, and live captions in 12 languages. Suited for cross-functional standups and small webinars.

| Attribute | Value |
|---|---|
| Category | Video conferencing |
| Price per seat (monthly) | $12 |
| Max participants | 100 |
| Recording storage | 25 GB per user |
| E2E encryption | Optional |
| Live transcription | 12 languages |

### SKU-2003 · MeetCadence Webinar

Browser-based video conferencing for distributed teams configured for one-to-many broadcasts. Supports up to 5000 attendees in view-only mode with separate panellist audio/video. Includes registration pages, post-event analytics, and YouTube/RTMP simulcast.

| Attribute | Value |
|---|---|
| Category | Video conferencing |
| Price per seat (monthly) | $80 |
| Max participants | 5000 view-only |
| Recording storage | Unlimited |
| Registration pages | Included |
| RTMP simulcast | YouTube, Facebook, custom |

---

## Document collaboration

### SKU-3010 · ScribeFlow Editor

Real-time collaborative document editor with version history, inline comments, and granular block-level permissions. Markdown, rich-text, and structured content blocks (tables, code, embeds). Strong focus on engineering and product documentation.

| Attribute | Value |
|---|---|
| Category | Document collaboration |
| Price per seat (monthly) | $7 |
| Document size limit | 50 MB |
| Real-time collaborators | Up to 50 simultaneous |
| Version history | 90 days |
| Block-level permissions | Yes |

### SKU-3011 · ScribeFlow Wiki

Real-time collaborative document editor with version history, inline comments, and granular block-level permissions, configured as an internal company wiki. Adds page hierarchy enforcement, mandatory reviewer flows, and read receipts.

| Attribute | Value |
|---|---|
| Category | Document collaboration |
| Price per seat (monthly) | $9 |
| Document size limit | 50 MB |
| Real-time collaborators | Up to 50 simultaneous |
| Version history | Indefinite |
| Read receipts | Yes |

### SKU-3012 · ScribeFlow Drafts

Real-time collaborative document editor with version history, inline comments, and granular block-level permissions, focused on individual writers and small editorial teams. Strips workspace and admin features in favour of distraction-free composition.

| Attribute | Value |
|---|---|
| Category | Document collaboration |
| Price per seat (monthly) | $4 |
| Document size limit | 25 MB |
| Real-time collaborators | Up to 5 simultaneous |
| Version history | 30 days |
| Workspace admin | No |

---

## Customer support

### SKU-4001 · HelpForge Inbox

Multi-channel support inbox aggregating email, chat widget, social DMs, and webform submissions into one shared queue. Round-robin or load-balanced ticket assignment, canned replies, SLA timers per priority.

| Attribute | Value |
|---|---|
| Category | Customer support |
| Price per seat (monthly) | $19 |
| Channels | Email, Chat, Twitter, Instagram, Webform |
| SLA timers | Yes |
| Canned replies | Unlimited |
| Reporting | Standard dashboards |

### SKU-4002 · HelpForge Knowledge

Public-facing knowledge base with article authoring, multi-language support, version history, and feedback widgets. Designed to deflect inbound tickets via search before they reach the inbox.

| Attribute | Value |
|---|---|
| Category | Customer support |
| Price per seat (monthly) | $14 |
| Languages | 35 |
| Article version history | Indefinite |
| Search | Built-in (typo-tolerant) |
| Custom domain | Included |

### SKU-4003 · HelpForge AI Assist

AI-augmented response drafting on top of HelpForge Inbox. Uses your knowledge base and ticket history to draft replies; agents review and send. Includes hallucination guards (citations required) and feedback loop for continuous improvement.

| Attribute | Value |
|---|---|
| Category | Customer support |
| Price per seat (monthly) | $39 (add-on) |
| Required base | SKU-4001 |
| Citation enforcement | Yes |
| Languages | 12 |
| Feedback loop | Built-in |

---

## Sales & CRM

### SKU-5001 · PipelineSpark CRM

Sales CRM with contact and account management, deal pipeline visualisation, email tracking, and meeting scheduling. Designed for sales teams from 5 to 100 reps.

| Attribute | Value |
|---|---|
| Category | Sales & CRM |
| Price per seat (monthly) | $25 |
| Contacts | Unlimited |
| Pipelines | Up to 5 |
| Email tracking | Yes |
| Meeting scheduling | Built-in |

### SKU-5002 · PipelineSpark Outreach

Sales engagement platform layered on top of CRM. Multi-step email sequences, call dialler, sequence pause/resume, A/B testing of step content. Designed for SDR teams of 5+.

| Attribute | Value |
|---|---|
| Category | Sales & CRM |
| Price per seat (monthly) | $59 |
| Sequence steps | Unlimited |
| Call dialler | Browser-based |
| A/B testing | Per-step |
| Required base | SKU-5001 |

### SKU-5003 · PipelineSpark Forecast

Sales forecasting and pipeline analytics. Roll-up to manager and exec views, weighted forecasts by stage, deal-level commentary, win/loss reason capture. Designed for sales leadership.

| Attribute | Value |
|---|---|
| Category | Sales & CRM |
| Price per seat (monthly) | $89 |
| Pipeline rollups | Manager and exec |
| Forecast methods | Weighted, best/likely/commit |
| Win/loss reasons | Customisable |
| Required base | SKU-5001 |

---

## DevOps & monitoring

### SKU-6101 · NorthStar Metrics

Time-series metrics collection and dashboards. Open-metrics compatible scrape, native Prometheus remote-write, sub-second query latency on hot data. Long-term storage tiered to object storage.

| Attribute | Value |
|---|---|
| Category | DevOps & monitoring |
| Price | $0.30 per million samples |
| Retention (hot) | 14 days |
| Retention (cold) | 13 months in object storage |
| Query language | PromQL compatible |
| Alerting | Yes |

### SKU-6102 · NorthStar Logs

Log aggregation and search at scale. Native ingest for syslog, journald, JSON, and OpenTelemetry. Indexed search with regex, structured field filters, and saved queries.

| Attribute | Value |
|---|---|
| Category | DevOps & monitoring |
| Price | $0.50 per GB ingested |
| Retention (default) | 30 days |
| Search | Indexed, regex, structured |
| Saved queries | Unlimited |
| Alerting | Threshold + anomaly |

### SKU-6103 · NorthStar Traces

Distributed tracing with OpenTelemetry-native ingest. Span search, service maps, latency-aware tail sampling, and trace-to-log correlation when paired with NorthStar Logs.

| Attribute | Value |
|---|---|
| Category | DevOps & monitoring |
| Price | $0.10 per million spans |
| Sampling | Head + tail (latency-aware) |
| Service maps | Built-in |
| Retention | 7 days |
| Trace ↔ logs correlation | Requires SKU-6102 |

### SKU-6104 · NorthStar Synthetics

Synthetic monitoring with browser-based and HTTP checks from 30+ global locations. Step-by-step browser scripts, video recording on failure, public status pages.

| Attribute | Value |
|---|---|
| Category | DevOps & monitoring |
| Price per check (monthly) | $5 |
| Locations | 30+ |
| Browser scripting | Playwright-compatible |
| Status pages | Public + private |
| Failure video | Yes |

### SKU-6105 · NorthStar Incident

On-call scheduling, paging, escalation policies, and post-mortem templates. Pages via voice, SMS, push, and email. Integrates with the metrics, logs, and traces products.

| Attribute | Value |
|---|---|
| Category | DevOps & monitoring |
| Price per seat (monthly) | $12 |
| Channels | Voice, SMS, push, email |
| Escalation depth | Unlimited |
| Post-mortem templates | Built-in |
| Required base | None |

---

## Identity & access

### SKU-7201 · KeyVault Identity

Workforce identity provider supporting SAML 2.0, OIDC, and SCIM 2.0. User, group, and role management with policy-driven access. MFA enrolment with TOTP, WebAuthn, and push.

| Attribute | Value |
|---|---|
| Category | Identity & access |
| Price per user (monthly) | $4 |
| Protocols | SAML 2.0, OIDC, SCIM 2.0 |
| MFA factors | TOTP, WebAuthn, push |
| User directory | Built-in or AD/LDAP sync |
| Audit log retention | 12 months |

### SKU-7202 · KeyVault Privileged

Privileged access management. Just-in-time elevation, session recording, vaulted secrets with rotation, and policy-driven approval workflows for production access.

| Attribute | Value |
|---|---|
| Category | Identity & access |
| Price per protected resource (monthly) | $30 |
| Just-in-time elevation | Yes |
| Session recording | Required for production |
| Secret rotation | Yes |
| Required base | SKU-7201 |

---

## Data & analytics

### SKU-8050 · DataPrism Warehouse

Cloud data warehouse with separation of compute and storage, sub-second metadata queries, and federated query across S3, GCS, and Azure Blob. Columnar storage with automatic partitioning and clustering.

| Attribute | Value |
|---|---|
| Category | Data & analytics |
| Price | $1.20 per credit |
| Storage | $23 per TB-month |
| Compute scaling | Per-warehouse, on demand |
| Federated query | S3, GCS, Azure Blob |
| Time travel | 90 days |

### SKU-8051 · DataPrism Catalog

Unified data catalog and lineage. Automated metadata harvesting from warehouses, databases, and BI tools. Column-level lineage, glossary management, data quality scoring.

| Attribute | Value |
|---|---|
| Category | Data & analytics |
| Price per managed asset (monthly) | $0.05 |
| Lineage granularity | Column-level |
| Glossary | Yes |
| Sources | 80+ connectors |
| Quality scoring | Built-in |

### SKU-8052 · DataPrism Reverse-ETL

Sync warehouse data back into operational tools. Scheduled or event-driven syncs, deep-merge upserts, and field-level mapping. Connectors for CRM, marketing automation, and customer support.

| Attribute | Value |
|---|---|
| Category | Data & analytics |
| Price per record synced (monthly) | $0.0001 |
| Connectors | 60+ |
| Trigger types | Schedule, webhook, change-data |
| Mapping | Field-level with transforms |
| Backfill | Supported |

### SKU-8053 · DataPrism BI

Self-serve business intelligence on top of DataPrism Warehouse. Drag-and-drop dashboards, embedded analytics SDK, alerting on metric thresholds. Caching tier for sub-second dashboard load.

| Attribute | Value |
|---|---|
| Category | Data & analytics |
| Price per viewer (monthly) | $14 |
| Dashboards | Unlimited |
| Embedded SDK | React, Vue, Angular |
| Alert delivery | Email, Slack, webhook |
| Cache | Sub-second |
