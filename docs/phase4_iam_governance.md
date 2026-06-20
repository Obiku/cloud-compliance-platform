# Phase 4 — IAM Governance Automation

## What this phase built

A Python package, `python/phase4_iam_governance/`, with two halves split deliberately
along a safety boundary:

- **`scanner.py`** — read-only. Checks IAM account-wide for: console users without
  MFA, active access keys older than 90 days, roles unused for 90+ days, and any user
  or role with `AdministratorAccess` attached directly. Makes no mutating API calls.
- **`remediation.py`** — the only code in this project that's allowed to change IAM
  state outside Terraform. Two actions are implemented: detaching a directly-attached
  `AdministratorAccess` policy, and deactivating (never deleting) a stale access key.

`report.py` formats findings as JSON and Markdown. `handler.py` is the Lambda
entrypoint (scan only). `cli.py` is the local entrypoint for both scanning and
the approval-gated remediation path.

## Why remediation is scoped the way it is

This AWS account is shared with another, unrelated project (`access-review-prod` —
see `docs/phase3_monitoring.md`). The scanner runs account-wide because IAM findings
are only useful in full context, but **remediation refuses to touch anything that
doesn't belong to this project**:

```python
def _is_in_scope(name, tags, name_prefix):
    if name.startswith(f"{name_prefix}-"):
        return True
    return tags.get("Project") == name_prefix
```

Every `Finding` carries an `in_scope_for_remediation` flag computed at scan time.
`remediation.py` re-checks this flag itself and raises `ScopeError` before doing
anything if it's `False` — this isn't just a CLI-layer convention, a caller can't
bypass it by constructing a `Finding` differently, since the check lives in the
remediation function itself.

On top of scope-checking, every remediation action defaults to dry-run: nothing
happens unless the caller passes `approved=True`, and at the CLI layer that requires
an explicit `--approve` flag plus an explicit `--check`/`--resource-id` pair (there is
no "remediate everything" command).

## Why some findings have no remediation action

Only `iam_admin_access_attached` and `iam_access_key_too_old` have a remediator.
`iam_user_console_no_mfa` and `iam_role_unused` deliberately don't:

- **No MFA** can't be safely auto-fixed by code — enrolling a virtual MFA device
  requires the user's own authenticator app. The correct action is human follow-up,
  not automation.
- **Unused roles** — the only undisputed "fix" is deletion, which is destructive and
  not reversible the way detaching a policy or deactivating a key is. Left as a
  reported finding for a human to assess.

This matches the project plan's "deactivating the worst offenders" framing — automate
the two actions that are safe and reversible, leave the rest as reported findings.

## Deployment: scheduled Lambda + manual CLI remediation

The scanner is deployed as the Lambda that Phase 1 created as a placeholder
(`cloud-compliance-platform-iam-governance-scan`), now running real code on a daily
EventBridge schedule (`rate(1 day)`), writing both report formats to
`s3://cloud-compliance-platform-evidence-575141563901/iam-governance/<timestamp>/`.
Its execution role has read-only IAM permissions and `s3:PutObject` scoped to that one
prefix - nothing else.

Remediation is **not** wired into the Lambda or the schedule. It only runs via the
local CLI (`python -m phase4_iam_governance.cli remediate ...`), invoked by a human
with their own AWS credentials. This keeps "approval-gated" meaningful - there's no
automated path that could apply a remediation without a person directly invoking it.

### A real packaging bug worth recording

The first Lambda deployment failed with `Runtime.ImportModuleError: attempted
relative import with no known parent package`. AWS Lambda's deployment zip is
flattened at its root, so `handler.py`'s relative imports (`from . import report`)
had no parent package to resolve against once deployed - despite working fine
locally and in tests, where `python/` itself is on `sys.path`.

Fixed by changing `terraform/modules/compute`'s archive step from a flat
`source_dir` to a `dynamic "source"` block that re-nests every `.py` file under a
`package_name` prefix inside the zip (`fileset(var.source_dir, "**/*.py")`), and
changing the Lambda `handler` to `phase4_iam_governance.handler.lambda_handler` to
match. This preserves the package as a real package at runtime instead of weakening
the import style to work around the flattening.

A second, smaller failure followed: `AccessDenied ... kms:GenerateDataKey`, since the
evidence bucket uses a customer-managed KMS key (Phase 2) and the Lambda's role had S3
write access but no permission to use that key. Added `evidence_bucket_kms_key_arn` as
an S3 module output and granted `kms:GenerateDataKey` on it specifically.

## Verification: before/after evidence against the real seeded issue

Ran the deployed Lambda manually (`aws lambda invoke`) before remediating:

| | Before | After |
|---|---|---|
| Total findings | 7 | 6 |
| In scope for `cloud-compliance-platform` | 1 | 0 |
| `legacy-admin` AdministratorAccess flagged | yes | no |

The one in-scope finding - `iam_admin_access_attached` on
`cloud-compliance-platform-legacy-admin` - was remediated via:

```
python -m phase4_iam_governance.cli remediate \
  --check iam_admin_access_attached \
  --resource-id cloud-compliance-platform-legacy-admin \
  --approve
```

Re-running the scan afterward confirmed the finding was gone. The other six findings
in both snapshots belong to `access-review-prod`'s own seeded users (`admin-charlie`,
`Saintkings`, `analyst-diana`, `dev-alice`, `dev-bob`) and were correctly left
untouched throughout - exactly the scope boundary this phase was built to enforce.

## Confirmed: this creates intentional Terraform drift

Immediately after remediating, `terraform plan` in `terraform/environments/sandbox`
showed:

```
# module.iam.aws_iam_user_policy_attachment.seeded_legacy_admin[0] will be created
Plan: 1 to add, 0 to change, 0 to destroy.
```

This is the exact behavior `docs/phase1_before_state.md` anticipated back in Phase 1:
boto3-based remediation bypasses Terraform state, so Terraform now wants to re-attach
the policy it still thinks should be there. This plan was deliberately **not**
applied, so the remediation stays in effect. Phase 6's control testing
(re-performance testing) is what's expected to run `terraform apply` again to
re-seed the issue and time how long detection takes.

## Testing

15 unit tests (`python/tests/test_scanner.py`, `test_remediation.py`) using `moto` to
mock IAM - covering each scan check's true/false-positive behavior, both remediation
actions in dry-run and approved modes, and the scope-refusal path. Wired into CI as a
new `pytest` job. `bandit -r python -ll` and `pip-audit` (both `requirements.txt` and
the new `requirements-dev.txt`) are clean.
