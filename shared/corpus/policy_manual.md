# Lumenflow IT security & access policy

This document is the IT security and acceptable-use policy for Lumenflow employees and contractors. It covers account management, device security, data classification, network access, incident response, and vendor risk. The policy is engineered for the chunking-benchmarks demo: it has deeply nested headings, long numbered procedures that span chunk boundaries when split at fixed sizes, and tables of role/system mappings that lose their meaning when separated from their parent section.

---

## 1. Scope and applicability

### 1.1 Who this policy covers

This policy applies to every employee, contractor, intern, and third-party vendor with logical or physical access to Lumenflow systems or data. It applies regardless of employment location, contract type, or device ownership. Parts of the policy that are mandatory for full-time employees may be advisory for short-term contractors; where this distinction matters, it is called out explicitly in the relevant section.

### 1.2 What this policy covers

The policy covers (a) the logical security controls used to protect Lumenflow data and systems, (b) the acceptable-use rules for Lumenflow-issued and personally-owned devices accessing those systems, (c) the procedures for granting, reviewing, and revoking access, (d) the incident response and breach notification process, and (e) the vendor risk management process used when introducing third-party services into the Lumenflow operating environment.

### 1.3 Authority and exceptions

This policy is owned by the Chief Information Security Officer. The CISO may grant time-bound exceptions in writing when business need exceeds the protection the policy provides; exceptions older than 90 days must be re-approved or remediated. All exceptions are logged in the GRC system and reviewed at the quarterly security council.

---

## 2. Identity and access

### 2.1 Account lifecycle

Account provisioning, modification, and deprovisioning is managed centrally through the IdP (KeyVault Identity, SKU-7201) and SCIM-synchronised to downstream systems. Manual account creation outside the IdP is prohibited except where the system in question does not support SAML or SCIM, in which case the local account must be documented in the application registry and reviewed quarterly.

### 2.2 Joiner procedure

When an employee joins the company, the following must happen in order:

1. The hiring manager submits a joiner ticket in the HR system with the start date, role, manager, and proposed access groups.
2. The IT helpdesk validates the ticket and provisions a primary account in the IdP, scoped to the role-based access groups requested.
3. The new joiner receives a temporary password by encrypted message; the password must be changed at first sign-in.
4. The joiner enrolls a primary MFA factor (WebAuthn preferred, TOTP acceptable) and at least one backup factor.
5. The joiner accepts the acceptable-use policy electronically; this acceptance is logged in the GRC system.
6. The joiner is enrolled in role-appropriate security awareness training, which must be completed within 30 days.
7. The joiner is issued company hardware (laptop, phone if required) which is provisioned with the device management agent before delivery.
8. Access to systems beyond the role-based defaults requires a separate access request, even during onboarding.

### 2.3 Mover procedure

When an employee changes role or team, their access is reviewed in full. The departing manager submits a closure of role-based access, the new manager submits the new role-based access, and the helpdesk reconciles. Access is not stacked: the assumption is that role-based access for the prior role is removed unless explicitly retained with a documented justification. Project-specific access (not role-based) follows the same review.

### 2.4 Leaver procedure

When an employee or contractor leaves, the following steps must complete on the last working day or earlier if the departure is involuntary:

1. The HR system raises a leaver ticket no later than 24 hours before the planned end date; for involuntary terminations the ticket is raised at the moment of the decision.
2. The IT helpdesk schedules the leaver's IdP account for disablement at the end-of-day on the leaving date; for involuntary departures the disablement happens immediately on the HR signal.
3. SCIM propagation deprovisions downstream applications. Applications that do not support SCIM are flagged for manual revocation in the application registry; manual revocation must be confirmed within 4 hours.
4. Personal data on company hardware is preserved per the data preservation policy; the hardware is collected, wiped, and re-imaged.
5. The leaver's email address is converted to a no-reply forwarder for 90 days, then disabled. Mail received during the forwarding period is delivered to the leaver's manager unless redirected.
6. Audit log searches are performed for activity in the 30 days before the departure if there is reason to believe the leaver may have exfiltrated data.

### 2.5 Access review

Role-based access groups are reviewed quarterly by the group owner. Project-specific access is reviewed by the project sponsor at project close or, for ongoing projects, every six months. Privileged access (production, finance systems, customer data) is reviewed monthly. The access review process produces evidence that is retained for the audit cycle (currently 12 months for SOC 2, 7 years for any data subject to financial controls).

### 2.6 Role to system mapping

The default role-based access groups are described below. This is the baseline only; individual access requests on top of role defaults are managed as documented in section 2.7.

| Role | Default access |
|---|---|
| Engineer (backend) | Code repository, CI/CD, staging, dev VPN, on-call paging |
| Engineer (frontend) | Code repository, CI/CD, staging, design system, on-call paging |
| Site Reliability Engineer | All engineer access plus production read, monitoring, incident management |
| Product Manager | Code repository (read), staging, analytics, customer support inbox (read) |
| Designer | Code repository (read), design system, prototyping tools |
| Customer Support | Customer support inbox, knowledge base, training environment |
| Sales | CRM, contract management, prospect data |
| Finance | Accounting system, payroll, contract management |

Production write access, customer data access beyond the support inbox, and any access to financial systems beyond Finance role defaults requires explicit named approval through the privileged access workflow.

### 2.7 Privileged access

Privileged access is gated through KeyVault Privileged (SKU-7202) using just-in-time elevation. To obtain elevated access, the requester opens a session in KeyVault Privileged, selects the resource, provides a justification (linked ticket required), and waits for approval. Approval is automatic for the requester's pre-approved scope during business hours; out-of-hours and out-of-scope requests require manual approval from a duty approver.

Sessions to production are recorded in full. Recordings are retained for 12 months and are reviewed (a) on incident, (b) on a 5% random audit each month, and (c) for any session that exceeded the maximum session length. The maximum session length is 4 hours; sessions longer than this require explicit re-approval at the 4-hour mark.

---

## 3. Device security

### 3.1 Company-issued devices

Every employee receives a company-issued laptop running macOS or Linux. Windows is supported on request for specific roles. All company-issued devices are enrolled in the device management agent (DMA) before delivery; an unmanaged company-issued device is not permitted on the network.

The DMA enforces the following baseline:

1. Full-disk encryption is on and the encryption key is escrowed.
2. Screen lock activates after 5 minutes of inactivity and requires password or biometric to unlock.
3. The OS is current within the last two minor versions; security patches are forced within 7 days of vendor release.
4. The endpoint detection and response (EDR) agent is running and reporting healthily.
5. The local firewall is enabled with inbound deny by default.
6. The boot media is not modifiable without an admin password; unsigned boot loaders are blocked.
7. USB mass-storage is disabled by default; exceptions require ticket and are time-bound.
8. The device sends an inventory beacon every 24 hours; missing beacons for 14 days raise an inventory alert.

### 3.2 Personal devices

Personal devices are permitted to access Lumenflow services only via the browser and only after enrolling the device with a lightweight device-trust agent that attests to (a) screen lock enabled, (b) disk encryption enabled, (c) recent OS, and (d) absence of jailbreak/root. Personal devices may not have full client-side software (mail client, code editor with repository checkout, support inbox client) installed; access is browser-only.

### 3.3 Mobile devices

Mobile devices used for company purposes are enrolled in the mobile device management agent (MDM). The MDM enforces a separate work profile on Android and a managed app configuration on iOS. Personal apps and data are out of scope of company management; work apps are in a managed container. On separation, only the managed container is wiped.

### 3.4 Lost or stolen devices

Loss or theft must be reported to the IT helpdesk within 4 hours of discovery. The helpdesk:

1. Marks the device as lost in the DMA, which triggers remote lock and, after 24 hours, a remote wipe.
2. Reviews the audit log for activity from the device since the last known good time; flags anomalies for the security team.
3. Issues a replacement device on the standard provisioning timeline.
4. Tracks the lost device in the inventory system; if recovered, the device is returned for forensic review before re-issue.

---

## 4. Data classification and handling

### 4.1 Classification levels

Lumenflow data is classified at one of four levels:

| Level | Definition | Examples |
|---|---|---|
| Public | Approved for unrestricted external sharing | Marketing pages, the FAQ document, published docs |
| Internal | Default for unclassified work product | Internal wikis, draft docs, project plans |
| Confidential | Damaging if disclosed externally | Salary data, product roadmaps, customer lists |
| Restricted | Strictly controlled, regulatory exposure | Customer-stored content, payment data, security secrets |

### 4.2 Default classification

When in doubt, content is Internal. Confidential or Restricted classification must be set explicitly. Documents created in ScribeFlow Editor (SKU-3010) inherit the parent project's classification; tasks in Lumenflow projects inherit the project classification.

### 4.3 Handling requirements

Each level has specific handling requirements:

1. Public data may be transmitted by any means, stored on any sanctioned system, and shared externally without further approval.
2. Internal data may be transmitted on company-managed channels (corporate email, ScribeFlow, Lumenflow itself) and shared externally only with explicit authorisation. Internal data may not be stored on personal devices or personal cloud accounts.
3. Confidential data must be stored only in approved systems, transmitted only via TLS-encrypted channels, and may be shared externally only under an executed NDA. Access to Confidential data is logged.
4. Restricted data must be stored only in approved systems with field- or column-level encryption where supported. Transmission outside the production environment requires explicit security team approval. Access to Restricted data is logged and reviewed weekly.

### 4.4 Customer-stored content

Customer content stored in Lumenflow on behalf of customers is Restricted by default. Engineers may not access customer content for development or testing purposes; the staging environment uses synthetic data generated from a separate fixture. Production access to customer content is gated through KeyVault Privileged and recorded.

### 4.5 Backups and retention

Production backups are encrypted at rest, replicated cross-region within the same legal jurisdiction, and retained per the data retention schedule:

1. Operational backups (24 hours) are kept for 30 days.
2. Weekly snapshots are kept for 90 days.
3. Monthly snapshots are kept for 12 months.
4. Annual snapshots are kept for 7 years where required for financial controls; otherwise destroyed at 12 months.

Backup restoration is tested quarterly. Restoration tests are documented and the documentation is presented at the security council.

---

## 5. Network and remote access

### 5.1 Office networks

Office networks are segmented into three zones: corporate (employee laptops, printers), guest (visitors, untrusted personal devices), and secure (engineering build infrastructure, finance terminals). Inter-zone traffic is denied by default; necessary flows are documented in the network allow-list.

### 5.2 Remote access

There is no full-tunnel VPN. Access to corporate services is via the IdP (KeyVault Identity, SKU-7201) for SaaS, and via short-lived bastions or service-specific tunnels for self-hosted infrastructure. The bastions enforce MFA and session recording for production, and a 4-hour session cap.

### 5.3 Wi-Fi

Office Wi-Fi has two SSIDs: a corporate SSID (WPA2-Enterprise, certificate-based) and a guest SSID (captive portal, time-limited code). Personal devices use the guest SSID even when used for work, because the corporate SSID is reserved for managed company devices.

### 5.4 Public Wi-Fi

Use of public Wi-Fi from a company device is permitted but requires (a) the device firewall be on, (b) the EDR be running, and (c) authentication to corporate services be performed only through the managed browser session. Tethering to a personal mobile hotspot is preferred where the network is untrusted.

---

## 6. Incident response

### 6.1 What counts as an incident

A security incident is any event that compromises the confidentiality, integrity, or availability of Lumenflow systems or data. This includes:

1. Suspected or confirmed unauthorised access to a Lumenflow system.
2. Loss or theft of a Lumenflow device or credential.
3. Unauthorised disclosure of Confidential or Restricted data.
4. A control failure that exposes data even if no exploitation has been observed.
5. A vendor incident affecting a system that holds Lumenflow data.

### 6.2 How to report

Any employee who notices something they believe may be an incident reports it to security@lumenflow.example (24x7, paging) or via the in-product "Report a security concern" link, which feeds the same queue. There is no penalty for reporting in good faith, even if the report turns out to be a false alarm.

### 6.3 Triage and severity

Inbound reports are triaged within 30 minutes during business hours and within 60 minutes outside. The triage assigns a severity:

1. SEV-1: customer data confidentiality breach, production outage, or a vulnerability under active exploit. Pages on-call security and on-call engineering immediately.
2. SEV-2: serious vulnerability without active exploit, partial outage, or compromise of internal systems with no customer data exposure. Pages on-call security; engineering pulled in within 4 hours.
3. SEV-3: lower-impact vulnerabilities, policy violations without compromise. Handled in business hours.
4. SEV-4: informational, near-miss, hygiene issue. Handled in normal weekly cadence.

### 6.4 Communication

For SEV-1 and SEV-2 incidents, communication is coordinated through the incident channel. External communication (customers, regulators, press) is handled by the legal and communications teams in coordination with the CISO. Engineers and analysts must not communicate externally about an active incident unless explicitly delegated.

### 6.5 Post-mortem

Every SEV-1 and SEV-2 incident receives a written post-mortem within 5 business days of resolution. The post-mortem covers timeline, root cause, customer impact, remediation, and follow-up actions with owners and dates. Post-mortems are blameless: the goal is system improvement, not individual accountability.

---

## 7. Vendor risk management

### 7.1 New vendors

Any new vendor that will hold Lumenflow data, integrate with our production systems, or handle authentication on our behalf must complete a vendor risk assessment before signature. The assessment covers SOC 2 status, GDPR/DPA requirements, data residency, breach history, and the security of the integration as designed.

### 7.2 Existing vendors

Existing vendors are reviewed annually. The review re-validates SOC 2 status, requests an updated penetration test summary, and re-confirms the data flow against current usage. Vendors that have lost certifications or had public breaches are flagged for accelerated review.

### 7.3 Vendor incidents

When a vendor reports an incident affecting Lumenflow, the incident response process from section 6 applies as if it were a Lumenflow incident, with the vendor as the primary investigator. Lumenflow's role is to assess customer impact, contain blast radius (rotate credentials, restrict integrations), and communicate to customers if their data is affected.

---

## 8. Policy maintenance

This policy is reviewed annually by the security council. Material changes are communicated to all employees via email and in-product banner. Minor changes (clarifications, formatting, contact updates) are made silently with an updated revision date in the policy footer. Last full review: see footer.
