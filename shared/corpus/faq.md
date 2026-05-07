# Lumenflow FAQ

Lumenflow is a (fictional) project management SaaS used as the demo corpus for the RAG Explained playlist. This FAQ contains 50 question/answer pairs covering accounts, billing, projects, tasks, integrations, and security. Eight pairs are designed to be **surface-similar but materially different** — these are the entries used to demonstrate why bi-encoder cosine similarity alone is not enough and reranking matters.

The eight surface-similar pairs are flagged with `[similar-pair]` tags in the source. Bi-encoders will rank them as near-duplicates; cross-encoder rerankers will correctly separate them.

---

## Account & Login

### Q: How do I sign up for Lumenflow?

Visit lumenflow.example/signup and enter your work email. We send a verification link within 60 seconds. Click the link, set a password (12 characters minimum, mixed case, one number), and you'll land in your first workspace.

### Q: How do I reset my password?

Go to lumenflow.example/forgot, enter your email, and we send a reset link valid for 60 minutes. The link expires after one click, even if the reset is never completed. If the link expires, request a new one — there is no limit on retries within a 24-hour window.

### Q: How do I change my email address? `[similar-pair-1a]`

Open Settings → Account → Email. Enter the new email and click Save. We send a confirmation link to the new address. Until you click that link the change does not take effect — you continue receiving notifications at the old address. The pending change can be cancelled from the same screen.

### Q: How do I change my notification email? `[similar-pair-1b]`

Open Settings → Notifications → Delivery channels. Add the new email and click Verify. Once verified, you can route different notification categories (mentions, due dates, weekly digest) to different addresses. Your account email stays unchanged — this is purely about where notifications are sent.

### Q: How do I delete my Lumenflow account?

Go to Settings → Account → Delete Account. Type your email to confirm. We start a 30-day grace period during which the account can be restored by logging in. After 30 days all personal data is purged and any workspaces you owned are transferred to a designated backup admin or, if none, archived.

### Q: How do I enable two-factor authentication?

Settings → Security → Two-factor → Enable. Scan the QR code with any TOTP app (Google Authenticator, 1Password, Authy). Enter a 6-digit code to confirm. Save the 10 recovery codes — they are shown once and never again.

### Q: I lost my 2FA device. How do I get back in?

Use one of the 10 recovery codes saved when you enabled 2FA. Each code works once. If you have no recovery codes, contact support@lumenflow.example from the email on file. Identity verification takes 24-48 hours; we cannot expedite it.

### Q: How long do login sessions last?

Sessions last 30 days on devices you mark as trusted, 24 hours otherwise. You can review and revoke active sessions from Settings → Security → Active sessions. Revoking a session forces sign-out within 5 minutes.

### Q: Why was I logged out automatically?

Three reasons trigger automatic sign-out: (1) your password was reset from another device, (2) an admin revoked your session, or (3) suspicious activity (geographic anomaly, multiple failed re-auth attempts) was detected. You'll see the reason in the email sent at sign-out time.

### Q: Can I have multiple Lumenflow accounts on one email?

No. Each email maps to exactly one account. If you need to separate work and personal usage, use email aliases (work+personal@... and work+work@...) or different email addresses. We treat aliases as distinct accounts.

---

## Subscriptions & Billing

### Q: How do I cancel my subscription? `[similar-pair-2a]`

Settings → Billing → Cancel subscription. You retain access until the end of the current billing period — for monthly plans that's the next renewal date, for annual plans it's whenever the year ends. No refund is issued for unused months on annual plans.

### Q: How do I cancel a scheduled task? `[similar-pair-2b]`

Open the task, click the three-dot menu, choose Delete or Archive. Delete is permanent after 7 days in trash; Archive keeps the task searchable but removes it from active views. Cancelling a recurring task only removes the next instance unless you choose "Cancel all future instances".

### Q: What payment methods do you accept?

Visa, Mastercard, American Express, and ACH transfers for annual plans over $1,200. We do not currently accept PayPal, Apple Pay, or cryptocurrency. Invoicing for enterprise plans (50+ seats) is available with NET-30 terms.

### Q: How do I update my credit card?

Settings → Billing → Payment method → Update. Enter the new card details. The change applies to the next billing cycle; the current cycle is already paid against the old method. If a renewal failed because of an expired card, updating the card here does not retry — you must click "Retry payment" explicitly.

### Q: Why was my card charged twice this month?

Two common causes. First, you may have changed plans mid-cycle — we issue a prorated charge for the new plan. Second, if a previous payment failed and was retried, you'll see one decline and one successful charge. Both appear on the statement. Contact billing@lumenflow.example with the date and amount and we'll explain or refund.

### Q: Can I get a refund? `[similar-pair-3a]`

Refunds are issued for: (1) accidental annual upgrades within 14 days, (2) duplicate charges on the same date, and (3) service outages exceeding the SLA on enterprise plans. Refunds are NOT issued for unused time on cancelled subscriptions or for plan downgrades.

### Q: Can I get a discount? `[similar-pair-3b]`

Annual plans receive 20% off the monthly price automatically. Educational institutions (.edu domains) get an additional 30%. Non-profits with 501(c)(3) status receive 50%. We do not negotiate discounts beyond these — no exceptions, including for large enterprise deals.

### Q: What happens when my trial ends?

You're moved to the Free tier automatically. The Free tier supports 3 workspaces, 10 members per workspace, and 1 GB of attachments. If you exceeded any of these during the trial, the relevant features lock until you either upgrade or remove items below the limit.

### Q: How do I switch from monthly to annual billing?

Settings → Billing → Change plan → Annual. We charge the difference today (12 × monthly minus already-paid). Annual plans renew on the upgrade date each subsequent year, not on your account creation date.

### Q: Where do I download invoices?

Settings → Billing → Invoices. PDF invoices for the last 24 months are available. Older invoices can be requested from billing@lumenflow.example with 48-hour turnaround. EU customers receive VAT-compliant invoices automatically; for other tax jurisdictions, contact us if a specific format is required.

---

## Workspaces & Projects

### Q: What is a workspace?

A workspace is the top-level container in Lumenflow. It holds projects, members, integrations, and billing. Most companies use one workspace; large organisations sometimes use one per business unit. Members are scoped to a workspace — guest access across workspaces requires Enterprise.

### Q: How do I create a project?

Click + New project from the workspace sidebar. Choose a template (Kanban, Sprint, Roadmap, Custom) or start blank. Name the project, choose a workspace if you have multiple, and optionally invite members at creation time.

### Q: How many projects can I have?

Free: 3 projects per workspace. Standard: 50. Pro: unlimited. Enterprise: unlimited with audit logging on project creation.

### Q: Can I duplicate a project?

Yes. Open the project, click ⋯ → Duplicate. You can choose to copy: tasks, members, integrations, automation rules. Attachments are copied by reference (not duplicated) to save storage.

### Q: How do I archive a project?

Open the project, click ⋯ → Archive. Archived projects are read-only, hidden from the sidebar, but searchable. They count toward your project limit unless you delete them. Restore via Settings → Projects → Archived.

### Q: What's the difference between archive and delete?

Archive: read-only, searchable, recoverable, counts toward limit. Delete: permanent after 30 days in trash, purged after 30 days, irrecoverable. Most teams archive completed projects rather than delete them, in case they need to reference past work.

### Q: How do I transfer a project to another workspace?

Pro and Enterprise only. Open the project, ⋯ → Move. Select the target workspace (you must be admin in both). All tasks, attachments, comments, and assignment history move with the project. Members not in the target workspace become guests.

### Q: Can I have private projects within a workspace?

Yes — Pro and above. Set the project visibility to Private at creation. Only invited members see it. Workspace admins can override and view private projects but the override is logged.

---

## Tasks

### Q: How do I create a task? `[similar-pair-4a]`

Inside any project, click + Add task or press T. Fill in the title (required), optional description, due date, assignee, and labels. Tasks save when you click out of the input or press Enter.

### Q: How do I create a recurring task? `[similar-pair-4b]`

Open or create a task, click the recurrence icon, choose a pattern (daily, weekly, monthly, custom). The task instance you create is the template — completing it creates the next instance based on the recurrence rule. Editing the template affects only future instances unless you choose "Apply to current".

### Q: How do I assign a task to multiple people?

Pro and above. In the task panel, click the assignee field, search, and add multiple people. The task appears in each assignee's My Tasks. Notifications fire to all assignees on changes.

### Q: How do I add a subtask?

Open the parent task, scroll to Subtasks, click + Add subtask. Subtasks have their own assignee, due date, and status. Completing all subtasks does not auto-complete the parent unless you turn that on in project settings.

### Q: Can subtasks have their own subtasks?

Yes, up to 5 levels deep. Beyond 5 levels we recommend a separate project linked from the task — at deeper nesting the UI becomes unreadable.

### Q: How do I link tasks?

Open a task, click Link → Add related task. Choose the relationship type: blocks, is blocked by, duplicates, is duplicated by, relates to. Blocks/blocked-by relationships are enforced — you cannot complete a task with open blockers unless you override and acknowledge.

### Q: What's the keyboard shortcut for completing a task?

Cmd-Enter (Mac) or Ctrl-Enter (Windows/Linux) when the task is selected. Press the same combo again to undo within 5 seconds.

### Q: How do I bulk-edit tasks?

Select multiple tasks (Shift-click or Cmd-click), then choose an action from the bulk-edit toolbar that appears at the bottom. Available actions: assign, change status, change due date, add label, delete. Bulk-edit is limited to 200 tasks per operation.

### Q: How do I sort or filter the task list?

Click the filter icon at the top of the list. Filter by assignee, label, status, due date, project, or custom field. Save filter combinations as views; views are sharable within a project.

### Q: How does Lumenflow handle task time zones?

Due dates are stored in UTC and displayed in the viewer's local time zone. A task due "Friday at 5pm" set by a New York user appears as "Friday at 10pm" to a London user. Recurring tasks recur in the *creator's* time zone, not the viewer's.

---

## Integrations

### Q: Does Lumenflow integrate with Slack?

Yes. Settings → Integrations → Slack → Connect. After OAuth, you can: (1) post task creation/completion to a channel, (2) create tasks from Slack messages with /lumenflow, (3) get DM notifications for assignments. Slack integration is available on Standard and above.

### Q: How does the GitHub integration work? `[similar-pair-5a]`

Connect a GitHub organisation in Settings → Integrations → GitHub. Lumenflow then watches commits and PRs for `LUMEN-1234` style references; mentioning a task ID in a commit message links the commit to that task. You can also auto-update task status when a linked PR merges.

### Q: How does the GitLab integration work? `[similar-pair-5b]`

Connect a GitLab group via OAuth in Settings → Integrations → GitLab. We watch merge requests and issues for `#LUMEN-1234` references (note the leading #, distinct from GitHub). Self-hosted GitLab is supported on Enterprise via a webhook URL.

### Q: Can I export tasks to a CSV?

Yes — any task list can be exported via the menu → Export → CSV. The export includes: ID, title, status, assignee, due date, labels, project, and any custom fields. Comments and attachments are not included in CSV exports; use Export → JSON for that.

### Q: Does Lumenflow have a public API?

Yes. REST and GraphQL endpoints are documented at lumenflow.example/docs/api. Authenticate with a personal API token (Settings → Developer → API tokens) or OAuth for third-party apps. Rate limit is 1000 requests/hour on Standard, 10,000/hour on Pro, custom on Enterprise.

### Q: Is there a webhook for task changes?

Yes. Settings → Integrations → Webhooks. Configure a URL to receive POST events when tasks are created, updated, completed, or deleted. Each event is signed with HMAC-SHA256 using a secret you set when configuring the webhook.

### Q: Can I import data from Asana / Jira / Trello?

Yes for Asana and Trello (Settings → Import). Choose a workspace and run the import — projects, tasks, comments, and attachments transfer. Jira import is paid migration only; contact sales@lumenflow.example for a quote.

### Q: Does Lumenflow have a desktop app?

Yes, for Mac and Windows. Download from lumenflow.example/desktop. The desktop app is an Electron wrapper around the web app with two extras: native notifications and a global hotkey to capture a task from anywhere.

### Q: Does Lumenflow have a mobile app?

Yes, iOS and Android. Both apps support read, create, update, and complete; advanced views (Gantt, custom fields editing) are web-only. Offline mode caches the last 7 days of activity for read-only access.

---

## Security & Compliance

### Q: Where is Lumenflow data hosted?

Primary US tenants: AWS us-east-1. EU tenants: AWS eu-west-1. Tenant region is set at workspace creation and cannot be changed without a paid migration. Data does not cross regions for normal operation; backups are replicated to a secondary region within the same legal jurisdiction.

### Q: Is Lumenflow SOC 2 compliant?

Yes — SOC 2 Type II. The current report is dated within the last 12 months and is available under NDA from security@lumenflow.example. Penetration tests are conducted annually by a third-party firm; high-level summaries are shared with Enterprise customers.

### Q: Does Lumenflow support SSO?

Yes, on Pro and Enterprise. Supported protocols: SAML 2.0, OpenID Connect. Pre-built integrations for Okta, Azure AD, Google Workspace, OneLogin. Enforce SSO from Settings → Security → SSO; once enforced, password login is disabled for all members.

### Q: Does Lumenflow support SCIM provisioning? `[similar-pair-6a]`

Yes, on Enterprise. SCIM 2.0 endpoint at lumenflow.example/scim/v2. Generate a SCIM token from Settings → Security → SCIM. Auto-provision and deprovision users from your IdP. Group sync to Lumenflow teams is supported.

### Q: Does Lumenflow support SAML SSO? `[similar-pair-6b]`

Yes, on Pro and Enterprise. SAML 2.0 with metadata XML or manual configuration. We send SP metadata at lumenflow.example/saml/metadata. Just-in-time provisioning is supported but limited to user creation — group memberships still require SCIM (Enterprise only) or manual assignment.

### Q: How are passwords stored?

bcrypt with cost factor 12. Passwords are never logged, never sent to third parties, and never stored in plaintext at any stage of the request lifecycle.

### Q: Can I require 2FA for all members in my workspace?

Yes — workspace admins can enforce 2FA from Settings → Security → 2FA enforcement. Existing members are given 14 days to enrol; new members must enrol at signup. Members without 2FA after the grace period are locked out until enrolment.

### Q: How long is data retained after deletion?

Tasks, projects, and comments stay in trash for 30 days, then are purged. Audit logs are retained for 12 months on Pro, 7 years on Enterprise. Deleted accounts are purged 30 days after the deletion request.

### Q: Does Lumenflow comply with GDPR?

Yes. We are a Data Processor under GDPR and a DPA is available from security@lumenflow.example. EU customer data is hosted in eu-west-1 (Ireland). Data subject access requests can be filed by any user from Settings → Privacy → Data export.

### Q: How do I request my personal data export?

Settings → Privacy → Export my data. We generate a ZIP within 24 hours containing: all tasks you created or commented on, your profile data, login history, and notification preferences. The download link expires after 7 days.

---

## Plans & Limits

### Q: What's included in the Free plan?

3 workspaces, 10 members per workspace, 1 GB attachments per workspace, 5 integrations per workspace, basic Kanban and List views. No automation rules, no time tracking, no reporting.

### Q: What's included in Standard ($8/user/month)?

Unlimited workspaces and members, 50 GB attachments per workspace, all integrations, Kanban + List + Calendar + Gantt views, basic automation (10 rules per project), 30-day audit log.

### Q: What's the difference between Standard and Pro? `[similar-pair-7a]`

Pro adds: unlimited automation rules, custom fields, time tracking, advanced reporting, private projects, multiple assignees per task, priority support. Pricing is $16/user/month.

### Q: What's the difference between Pro and Enterprise? `[similar-pair-7b]`

Enterprise adds: SSO/SAML, SCIM provisioning, audit log retention up to 7 years, customer-managed encryption keys, custom DPAs, named technical account manager, 99.9% uptime SLA. Pricing is per-quote, typically $32-50/user/month.

### Q: What attachment file types are supported? `[similar-pair-8a]`

Any file up to the per-attachment limit (25 MB Free, 100 MB Standard, 250 MB Pro, 1 GB Enterprise). We render previews for: images (PNG, JPG, GIF, SVG, WebP), PDFs, common Office documents, and text/code files. Other types upload but show a generic icon.

### Q: What kinds of files can I preview inline? `[similar-pair-8b]`

Inline preview is supported for images (PNG, JPG, GIF, SVG, WebP), PDFs (pages render in-browser), text and code files (syntax-highlighted with Shiki), and Office documents via a Microsoft viewer integration on Pro and above. Video and audio attachments are streamable inline; archive files (zip, tar) show a file listing.

### Q: How many guest users can I invite?

Free: 0. Standard: 5 per workspace. Pro: unlimited. Enterprise: unlimited with per-guest audit logging. Guests have read-only access by default; you can grant comment or task-create permissions per project.

### Q: What's the API rate limit?

Standard: 1000 requests/hour per token, 100 burst. Pro: 10,000/hour, 1000 burst. Enterprise: custom, typically 50,000/hour. Exceeding the limit returns HTTP 429 with a Retry-After header.

---

## Performance & Reliability

### Q: What's Lumenflow's uptime SLA?

99.5% on Pro (~3.6 hours downtime per month allowed). 99.9% on Enterprise (~43 minutes per month). Free and Standard have no formal SLA; status.lumenflow.example shows live status. SLA breaches result in service credits proportional to the downtime.

### Q: My tasks are slow to load. What can I help?

Three common causes: (1) a project with 5000+ open tasks — split or archive completed work; (2) a saved view with many filters and sorts on custom fields; (3) browser extensions injecting heavy DOM (ad blockers, password managers). The Performance panel in Settings → Help shows your account's measured load times.

### Q: Why am I getting "Workspace temporarily unavailable" errors?

Three possibilities: (1) a brief deploy is rolling out; (2) your workspace is migrating to a new database shard (rare, takes ~30 seconds); (3) an admin is restoring a recent snapshot, which makes the workspace read-only. Check status.lumenflow.example for the current status.
