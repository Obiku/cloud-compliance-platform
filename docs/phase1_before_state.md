# Phase 1 — Seeded Issues ("Before" State)

Phase 1 deliberately provisions two non-compliant resources alongside the compliant
baseline, so that Phase 3 (continuous monitoring) has something real to detect and
Phase 4/5/6 (remediation, evidence, control testing) have something real to fix and
prove. This document records their state as built, for later comparison.

## Seeded issue 1 — IAM user with AdministratorAccess and no MFA

- **Resource:** IAM user `cloud-compliance-platform-legacy-admin`
- **Module:** `terraform/modules/iam` (`aws_iam_user.seeded_legacy_admin`)
- **Issue:** The `AdministratorAccess` managed policy is attached directly to the user
  (not via a group), and no MFA device is enrolled.
- **Why this is non-compliant:** violates least-privilege and fails CIS AWS Foundations
  checks 1.4/1.5/1.6 (root/IAM user MFA, no direct admin policy attachment).
- **Expected detection:** AWS Config managed rules (`iam-user-mfa-enabled`,
  `iam-policy-no-statements-with-admin-access`) and Security Hub CIS/FSBP findings,
  enabled in Phase 3.
- **Expected remediation:** Phase 4 IAM governance automation flags and (with approval)
  deactivates/downgrades this user.

## Seeded issue 2 — S3 bucket without encryption at rest

- **Resource:** S3 bucket `cloud-compliance-platform-legacy-data-575141563901`
- **Module:** `terraform/modules/s3` (`aws_s3_bucket.seeded_unencrypted`)
- **Issue:** No `aws_s3_bucket_server_side_encryption_configuration` is attached.
  Public access is still blocked — only the encryption-at-rest control is missing, to
  avoid any real exposure risk while still failing the relevant compliance check.
- **Why this is non-compliant:** fails CIS AWS Foundations check 2.1.1 and the
  AWS Config managed rule `s3-bucket-server-side-encryption-enabled`.
- **Expected detection:** AWS Config conformance pack and Security Hub FSBP findings,
  enabled in Phase 3.
- **Expected remediation:** Phase 4/5 automation applies a default SSE configuration
  and records the change as evidence.

## Compliant baseline for comparison

Everything else provisioned in Phase 1 is built to the compliant standard the seeded
issues are deviating from:

- `cloud-compliance-platform-evidence-575141563901` (S3): versioning enabled, SSE-KMS
  encryption, public access fully blocked.
- IAM RBAC groups (`compliance-auditors`, `cloud-engineers`, `compliance-admins`): scoped
  policies, no direct admin-policy attachments to individual users.
- VPC (`vpc-09155f5c82d5f25b3`): public/private subnet separation, no NAT gateway (no
  ongoing cost in the sandbox).
- Lambda execution role: scoped to `AWSLambdaBasicExecutionRole` only.

## How to re-seed if remediated

If Phase 4 remediation deactivates or fixes these resources directly via the AWS API
(bypassing Terraform), the Terraform state will drift. To restore the "before" state for
re-testing (re-performance testing in Phase 6), re-run `terraform apply` in
`terraform/environments/sandbox` — both seeded resources are controlled by the
`create_seeded_admin_user` and `create_seeded_unencrypted_bucket` module variables and
will be recreated to their original non-compliant configuration.
