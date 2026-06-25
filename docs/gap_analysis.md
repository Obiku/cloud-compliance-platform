# Gap Analysis: ISO 27001, SOC 2, NIST CSF, CIS Benchmarks

Compares what this platform actually built and automates (`docs/rcm.md`,
`docs/control_matrix.md`) against the four frameworks named in the project plan.
Each table lists every relevant area of the framework, not just the ones already
covered, so the gaps are visible rather than implied by omission.

This is a single-account sandbox project built by one person, not a production
estate with a security team, a facilities function, or an HR department behind it.
Several framework areas are marked **Not applicable** for that reason rather than
Gap - the distinction matters because a real audit treats an inapplicable control
differently from a missing one, and conflating the two would overstate how close
this project is to a production-ready compliance posture.

## ISO/IEC 27001:2013 Annex A

The 2022 revision restructured Annex A into four themes (Organizational, People,
Physical, Technological) with 93 controls; this project's existing control
mappings (`docs/rcm.md`, `docs/phase7_servicenow_integration.md`) were built
against the older 2013 clause numbering, so this gap analysis stays consistent
with that rather than introducing a second, conflicting numbering scheme.

| Annex A area | Status | Notes |
|---|---|---|
| A.6 Organization of information security | Partial | A control owner is assigned per control in `docs/rcm.md`; no formal information security organization, asset owner register, or mobile device/teleworking policy exists beyond this. |
| A.7 Human resource security | Not applicable | No employees, contractors, or onboarding/offboarding process - this is a single-operator sandbox. |
| A.8 Asset management | Partial | AWS resources are tracked in Terraform state and Config's resource inventory; no formal asset classification scheme or media handling policy. |
| A.9 Access control | Covered | `CTRL-IAM-NOADMIN`, `CTRL-IAM-MFA`, `CTRL-IAM-ACCESSKEY-AGE`, `CTRL-IAM-UNUSED-ROLES`, `CTRL-IAM-GROUP-MFA` (A.9.2.3, A.9.2.4, A.9.2.6, A.9.4.2). |
| A.10 Cryptography | Partial | S3 encryption at rest is covered (`CTRL-S3-ENCRYPTION`, AWS account-wide SSE-S3 default); no formal key management policy beyond the evidence bucket's customer-managed KMS key. |
| A.11 Physical and environmental security | Not applicable | Entirely cloud-hosted; physical security is AWS's responsibility under the shared responsibility model. |
| A.12 Operations security | Covered | `CTRL-CONFIG-NISTCSF`, `CTRL-SECURITYHUB-FINDINGS`, `CTRL-CLOUDTRAIL-LOGGING` (A.12.4.1, A.12.6.1); change management is informal (direct commits, no formal CAB), acceptable for a single-operator project. |
| A.13 Communications security | Gap | No network segmentation testing or formal data-in-transit policy beyond TLS defaults; VPC Flow Logs remain disabled (`docs/vulnerability_log.md` VL-005). |
| A.14 System acquisition, development and maintenance | Covered | `CTRL-CICD-POLICYGATE` (A.14.2.1) - Checkov/Trivy/Bandit/pip-audit gate every PR. |
| A.15 Supplier relationships | Partial | Addressed for ServiceNow specifically in `docs/tprm_assessment.md`; no formal supplier policy covering AWS itself or other dependencies. |
| A.16 Information security incident management | Gap | `CTRL-SOD-ISSUE-CLOSE` covers one segregation-of-duties control for ServiceNow Issues, but there is no formal incident response plan, severity classification, or escalation path. |
| A.17 Business continuity management | Not applicable | No production SLA or continuity requirement for a sandbox project; Terraform state and evidence are not backed up beyond S3 versioning. |
| A.18 Compliance | Partial | A.18.2.2 covered via `CTRL-CONFIG-NISTCSF`; this gap analysis and the RCM are the closest things to a formal independent review, but no third-party audit has been performed. |

## SOC 2 Trust Services Criteria

| Category | Status | Notes |
|---|---|---|
| CC1 Control environment | Partial | A single named control owner exists for every control (`docs/rcm.md`); no board, ethics policy, or org-chart-level governance, consistent with a one-person project. |
| CC2 Communication and information | Partial | This documentation set (RCM, control matrix, vulnerability log, this gap analysis) is the communication artifact; no external stakeholder reporting cadence exists. |
| CC3 Risk assessment | Covered | `docs/risk_register.md`, this phase. |
| CC4 Monitoring activities | Covered | CC4.1 via `CTRL-CONFIG-NISTCSF`. |
| CC5 Control activities | Partial | Most controls are automated and tested (`docs/rcm.md`); CC5.3 (segregation of duties) only covers one ServiceNow workflow (`CTRL-SOD-ISSUE-CLOSE`), not a broader SoD matrix across all privileged actions. |
| CC6 Logical and physical access controls | Covered | CC6.1 via `CTRL-IAM-ACCESSKEY-AGE`, `CTRL-IAM-UNUSED-ROLES`; CC6.7 via `CTRL-S3-ENCRYPTION`. |
| CC7 System operations | Covered | CC7.1 via `CTRL-SECURITYHUB-FINDINGS`; CC7.2 via `CTRL-CLOUDTRAIL-LOGGING`. |
| CC8 Change management | Partial | `CTRL-CICD-POLICYGATE` gates every PR; no formal change advisory process, acceptable at this scale. |
| CC9 Risk mitigation | Partial | Phase 4's remediation CLI mitigates the IAM risks it scans for; no business continuity or vendor risk mitigation beyond `docs/tprm_assessment.md`. |
| Availability (additional criteria) | Not applicable | Not in scope - this project was never scoped to a production uptime commitment. |
| Confidentiality / Privacy (additional criteria) | Not applicable | No personal data is processed; the GDPR/data-flow review originally planned for this phase was dropped for that reason (`PROJECT_PLAN.md` Phase 9 change log). |

## NIST Cybersecurity Framework

The control mappings in `docs/rcm.md` were built against CSF 1.1's five functions.
CSF 2.0 (2024) added a sixth function, **Govern**, covering organizational context,
risk management strategy, and oversight - exactly the kind of structure this Phase 9
documentation set is informally building, but not yet a real, named Govern-function
program. Flagged here as a real gap against the current version of the framework,
not just the older one this project's mappings reference.

| Function | Status | Notes |
|---|---|---|
| Govern (CSF 2.0) | Gap | No formal risk management strategy document, roles/responsibilities charter, or supply chain risk management program beyond this gap analysis and `docs/tprm_assessment.md`. |
| Identify | Partial | Asset inventory exists informally via Terraform/Config; `docs/risk_register.md` covers risk assessment (ID.RA); no formal business environment or governance categories. |
| Protect | Covered | PR.AC-4 via `CTRL-IAM-GROUP-MFA`, `CTRL-IAM-MFA`. |
| Detect | Covered | DE.CM-1 via `CTRL-CONFIG-NISTCSF`. |
| Respond | Gap | No formal incident response plan or playbook; Phase 4's remediation CLI is corrective but reactive-on-demand, not a documented response process. |
| Recover | Not applicable | No production recovery time/point objectives have been defined for a sandbox account. |

## CIS AWS Foundations Benchmark

| Section | Status | Notes |
|---|---|---|
| 1. Identity and Access Management | Covered | 1.10 (MFA), 1.14 (key rotation), 1.16 (no direct admin policy) via `CTRL-IAM-MFA`, `CTRL-IAM-ACCESSKEY-AGE`, `CTRL-IAM-NOADMIN`. |
| 1.6 Hardware MFA for root | Gap | Live, current CRITICAL Security Hub finding (`IAM.6`) - see `docs/risk_register.md` RK0020003. Not closeable via Terraform; requires a manual console action. |
| 2. Storage | Partial | 2.1.1 (encryption) and 2.1.5 (public access block) covered via `CTRL-S3-ENCRYPTION`; S3 access logging and lifecycle configuration remain open (`docs/vulnerability_log.md` VL-007). |
| 3. Logging | Covered | 3.9-equivalent CloudTrail coverage via `CTRL-CLOUDTRAIL-LOGGING`. |
| 3.x CloudWatch log metric filters/alarms | Gap | Live Security Hub findings show none of the standard CIS log-metric-filter alarms (root usage, unauthorized API calls, console sign-in without MFA, IAM/CloudTrail/Config/NACL/security group/route table/network gateway changes) are configured. Detective coverage currently comes from Security Hub/Config/GuardDuty rather than these specific CloudWatch alarms. |
| 4. Networking | Gap | VPC Flow Logs remain disabled (`docs/vulnerability_log.md` VL-005, backlog, retest 2026-09-30). |

## Summary of genuine, currently open gaps

Excluding everything marked Not applicable (organizational scale, not a real gap)
and Partial items already tracked elsewhere, the concrete open items this analysis
surfaces are:

1. No hardware MFA on the AWS root user (CIS 1.6, ISO A.9 adjacent, new `docs/risk_register.md` RK0020003).
2. CIS-standard CloudWatch log metric filters/alarms are not configured.
3. VPC Flow Logs disabled (already tracked, `docs/vulnerability_log.md` VL-005).
4. S3 server access logging disabled on this platform's own buckets (already tracked, VL-007).
5. No formal incident response plan (ISO A.16, NIST CSF Respond).
6. No NIST CSF 2.0 Govern-function program (risk management strategy, supply chain risk management) beyond this documentation set.

Items 1, 2, and 5 are new findings from this phase; 3 and 4 were already tracked
and are restated here for completeness against the relevant framework.
