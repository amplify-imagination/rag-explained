# Lumenflow architecture specification

This document is the architecture specification for the Lumenflow platform. It names exactly 15 components and describes their typed relationships using explicit verbs (`CALLS`, `READS_FROM`, `WRITES_TO`, `DEPENDS_ON`, `EMITS_TO`, `OWNS`). The specification is engineered for the Graph RAG demo: answering multi-hop questions about Lumenflow's architecture requires traversing these relationships, which pure vector search cannot do.

The 15 components are: **EdgeRouter**, **AuthService**, **UserDB**, **WorkspaceService**, **WorkspaceDB**, **TaskService**, **TaskDB**, **NotificationService**, **NotificationQueue**, **WebhookDispatcher**, **AuditLogService**, **AuditLogStore**, **SearchIndex**, **AnalyticsPipeline**, **ReportingService**.

---

## EdgeRouter

EdgeRouter is the public entry point for all browser, mobile, and API traffic to Lumenflow. It terminates TLS, applies rate limiting, validates session tokens, and routes requests to the appropriate downstream service. EdgeRouter does not hold business state; all decisions are made from the request itself plus a small in-memory cache of session validation results.

EdgeRouter `CALLS` AuthService for any request that requires session validation beyond the cache. EdgeRouter `EMITS_TO` AuditLogService for every authenticated request.

Failure mode: if EdgeRouter is unavailable, no traffic reaches Lumenflow. There are two redundant fleets in different availability zones; loss of one fleet causes a graceful failover with sub-second client retries.

---

## AuthService

AuthService is the identity authority for Lumenflow. It issues, validates, and revokes session tokens. It supports password, SAML SSO, and OIDC sign-in flows. It is responsible for MFA challenge orchestration and for the SCIM provisioning surface.

AuthService `READS_FROM` UserDB for credentials, MFA enrolments, session metadata, and SAML/SCIM configuration. AuthService `WRITES_TO` UserDB on session creation, token revocation, and password changes. AuthService `EMITS_TO` AuditLogService for every authentication event.

AuthService is `DEPENDS_ON` by EdgeRouter for session validation. Any component that performs identity-aware actions on behalf of a user `CALLS` AuthService.

---

## UserDB

UserDB is the durable store for user accounts, passwords (bcrypt-hashed), MFA enrolments, SAML/SCIM configuration, and active session metadata. UserDB is a regional Postgres cluster with synchronous replication within region and asynchronous backup to a cross-region standby.

UserDB is `OWNS` ed by AuthService. No other component reads from or writes to UserDB directly; identity data is exposed only via AuthService's API.

Failure mode: loss of UserDB disables sign-in but does not affect already-authenticated sessions until their existing tokens expire. The cross-region standby can be promoted within 5 minutes if needed.

---

## WorkspaceService

WorkspaceService manages workspaces, members, and workspace-level configuration. It is the authority for membership, role assignments, plan tier, and integration settings. It is the entry point for any operation that depends on "is this user a member of this workspace?" semantics.

WorkspaceService `READS_FROM` WorkspaceDB for workspace and member records. WorkspaceService `WRITES_TO` WorkspaceDB on member changes, plan changes, and integration configuration. WorkspaceService `CALLS` AuthService to verify user identity on every request. WorkspaceService `EMITS_TO` AuditLogService for member changes and plan changes.

TaskService and NotificationService both `CALLS` WorkspaceService to resolve workspace membership before performing privileged operations.

---

## WorkspaceDB

WorkspaceDB is the durable store for workspace records, member records, plan and billing snapshots, and integration configuration. It is a regional Postgres cluster mirrored synchronously within region.

WorkspaceDB is `OWNS` ed by WorkspaceService. No other component reads from or writes to WorkspaceDB directly.

---

## TaskService

TaskService is the core CRUD surface for Lumenflow's primary domain object: tasks. It also handles the task-level operations: assignment, status changes, comments, attachments metadata, and the relationship graph between tasks (blocks/blocked-by/duplicates). TaskService is responsible for emitting domain events when tasks change.

TaskService `READS_FROM` TaskDB for task content, comments, and relationships. TaskService `WRITES_TO` TaskDB on every mutation. TaskService `CALLS` WorkspaceService to verify membership. TaskService `EMITS_TO` NotificationQueue for changes that should produce notifications. TaskService `EMITS_TO` AuditLogService for restricted-data tasks. TaskService `WRITES_TO` SearchIndex (asynchronously, via change-data capture) on every mutation.

TaskService `DEPENDS_ON` AuthService (via WorkspaceService) for identity. TaskService `DEPENDS_ON` SearchIndex for read-side search queries.

---

## TaskDB

TaskDB is the durable store for tasks, comments, assignment history, and the task relationship graph. TaskDB is a sharded Postgres cluster; tasks are sharded by workspace ID so workspace-scoped queries hit a single shard.

TaskDB is `OWNS` ed by TaskService. Change-data capture from TaskDB is consumed by SearchIndex and AnalyticsPipeline.

---

## NotificationService

NotificationService delivers notifications across channels: email, push (mobile), in-product, and Slack. It does not own delivery preferences directly; preferences are stored on the user record in UserDB and read via AuthService.

NotificationService `READS_FROM` NotificationQueue for inbound delivery requests. NotificationService `CALLS` AuthService to look up delivery preferences. NotificationService `CALLS` WorkspaceService to verify the recipient is still a member at delivery time. NotificationService `EMITS_TO` WebhookDispatcher for workspace-configured webhook deliveries. NotificationService `EMITS_TO` AuditLogService for delivery attempts to Restricted-data tasks.

---

## NotificationQueue

NotificationQueue is a durable message queue that decouples task mutation events from notification delivery. Producers (TaskService, WorkspaceService) emit events; NotificationService consumes them.

NotificationQueue is `OWNS` ed by NotificationService. The queue is partitioned by workspace ID; ordering is guaranteed within a partition.

---

## WebhookDispatcher

WebhookDispatcher delivers signed HTTP POSTs to customer-configured webhook URLs. It implements retry-with-backoff, dead-letter queueing for repeated failures, and customer-visible delivery logs.

WebhookDispatcher `READS_FROM` WorkspaceService (via API) for the configured webhook URLs and shared secrets. WebhookDispatcher `EMITS_TO` AuditLogService for every delivery attempt and outcome.

---

## AuditLogService

AuditLogService is the write-side authority for Lumenflow's audit log. It receives events from every component that takes identity-aware actions and writes them to AuditLogStore. AuditLogService applies retention policies based on workspace plan tier (30 days on Standard, 90 days on Pro, up to 7 years on Enterprise).

AuditLogService `WRITES_TO` AuditLogStore for every event. AuditLogService `READS_FROM` WorkspaceService (cached) to determine retention policy.

AuditLogService is `CALLS` ed by virtually every other service: EdgeRouter, AuthService, WorkspaceService, TaskService, NotificationService, WebhookDispatcher.

---

## AuditLogStore

AuditLogStore is the durable, append-only store for audit log events. It is sharded by workspace ID and tiered: hot data (last 30 days) lives in a column store optimised for time-range queries, cold data lives in object storage with a metadata index.

AuditLogStore is `OWNS` ed by AuditLogService. ReportingService is the only read consumer of historical audit data, and it does so via AuditLogService's read API, not directly.

---

## SearchIndex

SearchIndex is the read-optimised search store for tasks, comments, and workspace metadata. It is fed by change-data capture from TaskDB and WorkspaceDB. The index supports full-text search, faceted filters, and the BM25 component of hybrid search.

SearchIndex is `READS_FROM` by TaskService for search queries, by WorkspaceService for member search, and by ReportingService for cross-workspace administrator views. SearchIndex `READS_FROM` TaskDB (via CDC) and `READS_FROM` WorkspaceDB (via CDC).

Failure mode: if SearchIndex is unavailable, search returns 503; CRUD operations on tasks continue uninterrupted.

---

## AnalyticsPipeline

AnalyticsPipeline is the offline batch and streaming pipeline that produces denormalised, query-optimised tables for reporting. It consumes change-data capture from TaskDB, WorkspaceDB, and AuditLogStore, transforms it, and writes derived tables.

AnalyticsPipeline `READS_FROM` TaskDB (via CDC), `READS_FROM` WorkspaceDB (via CDC), and `READS_FROM` AuditLogStore (via batch export). AnalyticsPipeline `WRITES_TO` a separate analytics warehouse (not listed as a Lumenflow-owned component because it's the underlying DataPrism Warehouse product, SKU-8050). AnalyticsPipeline `EMITS_TO` AuditLogService for governance events on its own pipeline runs.

ReportingService `READS_FROM` the AnalyticsPipeline output tables.

---

## ReportingService

ReportingService is the read-side service for in-product reports, dashboards, and exports. It is the only component that surfaces cross-workspace aggregate data to administrators (with appropriate authorisation).

ReportingService `READS_FROM` SearchIndex for current-state queries (e.g., "tasks open right now"). ReportingService `READS_FROM` AnalyticsPipeline output (via the analytics warehouse) for historical trend queries. ReportingService `CALLS` AuthService to verify caller identity and `CALLS` WorkspaceService to verify administrator role.

ReportingService `DEPENDS_ON` SearchIndex and `DEPENDS_ON` AnalyticsPipeline. Loss of either degrades specific report categories without affecting the others.

---

## Multi-hop dependency examples

Some dependencies span multiple components:

- A user's notification for a task assignment depends on a chain of: EdgeRouter → TaskService → NotificationQueue → NotificationService → WorkspaceService (for active membership check) → AuthService (for delivery preferences) → UserDB. If any one of these is unavailable, the notification fails.
- An administrator viewing a 2-year audit log report depends on: EdgeRouter → ReportingService → AnalyticsPipeline (via warehouse) → AuditLogStore (cold tier) → AuditLogService (read API). Audit log queries against the hot tier follow a shorter path: EdgeRouter → ReportingService → AuditLogService → AuditLogStore (hot tier).
- A SCIM provisioning request from an external IdP traverses: EdgeRouter → AuthService → UserDB (write) and then asynchronously AuthService → WorkspaceService for default workspace assignment, with both steps emitting to AuditLogService.

These chains are precisely what graph-aware retrieval solves. A flat vector index over this document cannot answer "which databases does a customer-facing webhook delivery touch?" without traversing WebhookDispatcher → WorkspaceService → WorkspaceDB *and* WebhookDispatcher → AuditLogService → AuditLogStore.
