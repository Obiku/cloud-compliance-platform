# Phase 2 — Policy-as-Code Mapping and Design Notes

## Pipeline overview

`.github/workflows/compliance-pipeline.yml` runs five independent jobs on every push
and pull request to `main`:

| Job | Tool | Gate |
|---|---|---|
| `terraform` | `terraform fmt` / `validate` / `plan` | Fails on any syntax/validation error |
| `checkov` | Checkov | Informational only — see below |
| `trivy` | Trivy (`config` scan) | Fails on CRITICAL/HIGH |
| `bandit` | Bandit | Fails on MEDIUM/HIGH severity findings |
| `pip-audit` | pip-audit | Fails on any known dependency vulnerability |

A failing job blocks the PR from being merged once branch protection rules require
these checks (branch protection itself is still an open item from Phase 0).

## Why Trivy instead of tfsec

The original plan named tfsec as the IaC scanner. tfsec was archived by Aqua Security
and its checks merged into **Trivy**'s `config` subcommand, which is now the maintained
successor and uses the same check engine. Trivy is used here instead, with no loss of
coverage.

## Why Checkov runs informationally, not as a blocking gate

The project plan calls for blocking on "critical/high findings from any stage."
Checkov's open-source edition does not assign a severity to findings (severity scoring
requires a paid Prisma Cloud/Bridgecrew platform connection) — every finding reports
`severity: null`. Without a severity field, Checkov findings cannot be classified as
critical/high, so they cannot drive that specific gate.

Checkov is still run on every build for its broad CIS AWS Benchmark-aligned coverage
(93 checks evaluated against this codebase as of Phase 2), with `soft_fail: true` so it
reports without blocking. **Trivy is the actual severity-based blocking gate** for IaC
misconfigurations, confirmed against this codebase to correctly flag real HIGH findings
(see "Verification" below).

## Why CI doesn't run a live `terraform plan` against AWS

CI's `terraform plan` runs with `-backend=false` and no AWS credentials. It always shows
"everything to create" (no real state to diff against), so it functions as a syntax and
logic smoke test, not a live drift check. No AWS credentials are stored in GitHub
Secrets. The real `plan`/`apply` against the live backend continues to run from the
maintainer's machine via the AWS CLI, as it has since Phase 1 — this avoids putting
long-lived AWS credentials (or the added complexity of OIDC federation) into CI for a
sandbox/lab project where it isn't yet justified.

## Verification performed before wiring the gate

Before writing the workflow, all four scanners were run locally against the actual
Phase 1 Terraform code (not assumed) to confirm real findings and avoid guessing at
rule IDs:

- **Checkov** (`checkov -d terraform`): 25 failing checks out of 93 evaluated, none with
  a usable severity field.
- **Trivy** (`trivy config terraform`): found 3 real HIGH and 7 MEDIUM/LOW findings.
  Three were fixed directly in code (not suppressed):
  - `AWS-0132` on the evidence bucket — added a customer-managed KMS key
    (`terraform/modules/s3/main.tf`) instead of the AWS-managed key.
  - `AWS-0164` ×2 on the public subnets — set `map_public_ip_on_launch = false`
    (`terraform/modules/vpc/main.tf`); no compute resources existed in those subnets
    yet, so this had no functional cost.
  - `AWS-0123` ×3 on the IAM groups (MFA not enforced) — added a standard AWS
    "deny-unless-MFA" group policy (`terraform/modules/iam/main.tf`). Trivy's static
    check does not trace through a separately-defined `aws_iam_policy` attached via
    `aws_iam_group_policy_attachment`, so it still reports this finding even though the
    control is in place — tracked as a known tool limitation in
    `docs/vulnerability_log.md`, not a real gap.

  After these fixes, the only remaining HIGH finding is `AWS-0132` on the intentionally
  seeded unencrypted bucket — suppressed with an inline `#trivy:ignore:AWS-0132`
  comment directly in `terraform/modules/s3/main.tf`, referencing the vulnerability log,
  so the gate stays meaningful for any *new* HIGH/CRITICAL issue introduced later.
- **Bandit** (`bandit -r python terraform/modules/compute/lambda_src -ll`): 0 findings
  (codebase has no Python logic yet beyond the Lambda placeholder).
- **pip-audit** (`pip-audit -r python/requirements.txt`): 0 known vulnerabilities in
  `boto3`.

## CIS AWS Benchmark / framework mapping

| Control area | Checkov / Trivy rule | CIS AWS Foundations | Resource |
|---|---|---|---|
| No IAM user with directly-attached AdministratorAccess | `CKV_AWS_274` / `AWS-0143` | 1.16 | `module.iam` seeded user (accepted exception) |
| IAM MFA enforcement | `AWS-0123` | 1.10 | `module.iam` group policy |
| S3 encryption at rest | `CKV_AWS_145` / `AWS-0132` | 2.1.1 | `module.s3` evidence + seeded buckets |
| S3 public access block | `CKV_AWS_53`–`56` / `CKV2_AWS_6` | 2.1.5 | `module.s3` |
| S3 versioning | `CKV_AWS_21` / `AWS-0090` | — (AWS FSBP) | `module.s3` |
| VPC Flow Logs | `CKV2_AWS_11` / `AWS-0178` | 3.9 | `module.vpc` (backlog, not blocking) |
| No hard-coded secrets in Lambda | `CKV_AWS_45` | — (AWS FSBP) | `module.compute` |
| Python SAST (no hard-coded secrets/injection) | Bandit | — (OWASP-aligned) | `python/`, Lambda source |
| Dependency vulnerabilities | pip-audit | — (Vulnerability Management) | `python/requirements.txt` |
