# Risk & Control Matrix (RCM)

Expands `docs/control_matrix.md` (Phase 5's initial control-to-evidence mapping) into
a full RCM: control type, nature, frequency, and owner, for every control actually
built across Phases 1–5. Control IDs are reused as-is where Phase 5 already defined
one; new IDs are added for controls that didn't have a dedicated evidence artifact
yet.

| Control ID | Description | Framework mapping | Owner | Type | Nature | Frequency |
|---|---|---|---|---|---|---|
| `CTRL-IAM-NOADMIN` | No IAM user/role has `AdministratorAccess` attached directly (outside a group) | ISO 27001 A.9.2.3; SOC 2 CC6.1; CIS 1.16 | obiku | Detective + Corrective | Automated (scan: Phase 4 Lambda; fix: approval-gated CLI) | Scan: daily. Remediation: on demand, human-triggered |
| `CTRL-IAM-MFA` | Console-enabled IAM users have an MFA device enrolled | ISO 27001 A.9.4.2; SOC 2 CC6.1; CIS 1.10 | obiku | Detective | Automated (scan only — MFA enrollment can't be auto-remediated) | Daily |
| `CTRL-IAM-ACCESSKEY-AGE` | Active access keys are rotated within 90 days | ISO 27001 A.9.2.4; SOC 2 CC6.1; CIS 1.14 | obiku | Detective + Corrective | Automated (scan: Phase 4 Lambda; fix: approval-gated CLI, deactivate only) | Scan: daily. Remediation: on demand, human-triggered |
| `CTRL-IAM-UNUSED-ROLES` | IAM roles unused for 90+ days are identified | ISO 27001 A.9.2.6 | obiku | Detective | Automated (report only — deletion is a manual decision) | Daily |
| `CTRL-IAM-GROUP-MFA` | RBAC groups deny all actions unless MFA is present (except self-service MFA enrollment) | ISO 27001 A.9.4.2; SOC 2 CC6.1 | obiku | Preventive | Manual review (Terraform-defined, not continuously tested by automation — Trivy can't verify it; see VL-004) | Ad hoc / on Terraform change |
| `CTRL-S3-ENCRYPTION` | S3 buckets are encrypted at rest | ISO 27001 A.8.2.3; SOC 2 CC6.7; CIS 2.1.1 | obiku | Preventive | Hybrid (AWS account-wide default + Security Hub monitoring) | Continuous (AWS-enforced default) |
| `CTRL-CONFIG-NISTCSF` | AWS Config conformance pack (NIST CSF) compliance status | NIST CSF; ISO 27001 A.18.2.2; SOC 2 CC4.1 | obiku | Detective | Automated (Phase 5 Lambda evidence collection) | Daily |
| `CTRL-SECURITYHUB-FINDINGS` | Security Hub active FAILED findings (CIS AWS Foundations, AWS FSBP) | CIS AWS Foundations; AWS FSBP; ISO 27001 A.12.6.1; SOC 2 CC7.1 | obiku | Detective | Automated (Phase 5 Lambda evidence collection) | Daily |
| `CTRL-CLOUDTRAIL-LOGGING` | CloudTrail trail is multi-region, logging, and actively delivering events | ISO 27001 A.12.4.1; SOC 2 CC7.2 | obiku | Detective | Automated (Phase 5 Lambda evidence collection) | Daily |
| `CTRL-CICD-POLICYGATE` | CI pipeline blocks merges on CRITICAL/HIGH IaC findings (Trivy) and MEDIUM/HIGH SAST findings (Bandit) | ISO 27001 A.14.2.1; SOC 2 CC8.1 | obiku | Preventive | Automated (GitHub Actions) | Per commit/PR |

## Notes on classification

- **`CTRL-IAM-GROUP-MFA` is the one control without continuous automated testing.**
  No tool in this pipeline can verify a "deny unless MFA" policy's *effect* (Trivy's
  static check doesn't trace through the managed-policy attachment, per VL-004) —
  the only way to truly test it is to attempt an action as a non-MFA'd test user and
  confirm denial, which requires provisioning a real test identity. Out of scope for
  this phase; flagged here rather than silently treated as continuously assured.
- **`CTRL-S3-ENCRYPTION` is "Hybrid"** because the control's actual enforcement is an
  AWS platform default (since Jan 2023), not something this project's code enforces —
  Security Hub monitoring is what this project adds on top of an AWS-provided baseline.
  See `docs/phase3_monitoring.md`.
