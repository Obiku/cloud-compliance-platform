# Phase 3 — Continuous Cloud Compliance Monitoring

## Important context: this account is shared with another project

Before building anything, a read-only audit of the AWS sandbox account found that AWS
Config, Security Hub, and GuardDuty were **already enabled** — not by this project, but
by an unrelated, pre-existing workload in the same account referred to as
`access-review-prod`:

| Service | Pre-existing resource | Since |
|---|---|---|
| AWS Config | Recorder `access-review-prod-recorder` (records all supported resource types, account-wide) | 2026-05-20 |
| AWS Config | Delivery channel `access-review-prod-delivery` | 2026-05-20 |
| Security Hub | Subscribed to CIS AWS Foundations v1.2.0 and AWS FSBP v1.0.0 | 2026-04-10 |
| GuardDuty | Detector with malware protection, EKS, RDS, Lambda monitoring, runtime monitoring | 2026-04-10 |
| Audit Manager | `INACTIVE` | — |

Config, Security Hub, and GuardDuty are **account/region-wide singletons** — AWS does
not allow a second configuration recorder or a second GuardDuty detector in the same
region. This means:

- They cannot be "enabled" again for this project specifically.
- Because they're account-wide, **they already cover every resource this project
  creates too**, with zero additional setup. Phase 1's IAM and S3 resources are
  recorded by Config and evaluated by Security Hub's existing standards exactly the
  same as the other project's resources.

So Phase 3's actual scope became: confirm what's already covered, add what's missing
and safe to add without disturbing the other project, and verify detection against the
seeded issues.

## What this phase added

- **AWS Config conformance pack** — `cloud-compliance-platform-nist-csf`
  (`terraform/modules/monitoring`), deployed from AWS's official NIST CSF sample
  template (130 managed rules). This is additive — multiple conformance packs can
  coexist on one Config recorder, so it doesn't conflict with `access-review-prod`'s
  setup.
- **CloudTrail** — already satisfied by Phase 0's `cloud-compliance-platform-trail`
  (multi-region, logging confirmed). The original plan's "organization CloudTrail"
  wording assumed AWS Organizations; this is a single-account sandbox, so a
  multi-region account trail is the correct equivalent.
- **Audit Manager** — not added. See `PROJECT_PLAN.md`'s Phase 3 change log: AWS put
  Audit Manager into maintenance mode on 2026-04-30 and no longer allows enabling it for
  new accounts. This account was never registered before that cutoff, confirmed by
  `aws_auditmanager_account_registration` failing with `RegisterAccount ...
  ValidationException`. No AWS-native alternative exists for automated ISO 27001/SOC 2
  control mapping — confirmed by enumerating Security Hub's available standards
  (`aws securityhub describe-standards`), which only covers CIS, AWS FSBP, NIST
  800-53/171, and PCI DSS. ISO 27001/SOC 2 mapping now comes entirely from the manual
  Risk & Control Matrix and gap analysis planned for Phases 5/6/9.

There was no AWS sample conformance pack template for ISO 27001 either — only NIST CSF
— so the conformance pack bullet itself was narrowed to NIST CSF (see `PROJECT_PLAN.md`
change log).

## Verifying the Phase 1 seeded issues — results

### Seeded issue 1: IAM user with AdministratorAccess and no MFA — confirmed flagged

Security Hub's existing AWS FSBP standard correctly flags `legacy-admin`:

| Finding | Status |
|---|---|
| "IAM users should not have IAM policies attached" | FAILED |
| `iam-user-group-membership-check` | FAILED |

This matches the seeded design exactly: the user has `AdministratorAccess` attached
directly instead of through a group, and Security Hub catches it without any extra
configuration from this project — it was already evaluating this account's IAM users.

### Seeded issue 2: S3 bucket without encryption at rest — no longer a real gap

Checking `cloud-compliance-platform-legacy-data-...` directly with
`aws s3api get-bucket-encryption` shows it **is** encrypted (SSE-S3/AES256), despite no
`aws_s3_bucket_server_side_encryption_configuration` resource ever being created for
it in Terraform. AWS enabled default server-side encryption for all S3 buckets
account-wide in January 2023 — every bucket gets baseline AES256 encryption whether or
not it's explicitly configured. Security Hub's encryption-related checks correctly
report this bucket as compliant, because it genuinely is.

This means the seeded issue, as originally designed in Phase 1, no longer represents a
real-world gap — it predates a platform-level default AWS introduced after that pattern
was a meaningful thing to seed. The bucket still fails other real Security Hub checks
that are *not* neutralized by an AWS default:

| Finding | Status |
|---|---|
| "S3 general purpose buckets should require requests to use SSL" | FAILED |
| "S3 general purpose buckets should have server access logging enabled" | FAILED |
| "S3 general purpose buckets should have Lifecycle configurations" | FAILED |

`docs/phase1_before_state.md` and `docs/vulnerability_log.md` should be read with this
correction in mind: the bucket is still a genuine "legacy, never-hardened" example for
Phase 4/5 remediation, just not specifically for encryption-at-rest.

## Conclusion

Both seeded issues from Phase 1 are detected by the account's existing continuous
monitoring, confirming Phase 3's monitoring stack works as intended — for the IAM issue,
exactly as designed; for the S3 issue, the underlying control turned out to already be
satisfied by an AWS platform default, which is itself a legitimate (if accidental)
finding worth recording rather than hiding.
