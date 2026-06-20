# Phase 5 — Automated Evidence Collection Pipeline

## What this phase built

`python/phase5_evidence_collection/` — three read-only collectors
(`collectors.py`), each wrapping one AWS API surface:

- `collect_config_compliance` — AWS Config conformance pack (NIST CSF) overall
  status plus every currently `NON_COMPLIANT` rule/resource pair, paginated.
- `collect_security_hub_findings` — active (`RecordState=ACTIVE`), `FAILED`
  Security Hub findings, paginated.
- `collect_cloudtrail_sample` — trail status (multi-region, logging state, last
  delivery time) plus a sample of recent management events via `lookup_events`.

`storage.py` writes each snapshot to the evidence bucket as
`evidence/<control-id>/<YYYY>/<MM>/<DD>/<HHMMSS>/snapshot.json`. `controls.py`
defines the three control IDs as the single source of truth — `docs/control_matrix.md`
mirrors it rather than duplicating the mapping in free text. `handler.py` is the
scheduled Lambda entrypoint; `cli.py` is the local/manual entrypoint (can print to
stdout instead of uploading, useful for inspecting a snapshot without writing
evidence).

Audit Manager reports were dropped from scope — see `PROJECT_PLAN.md`'s Phase 5
change log; this is a direct consequence of Phase 3's finding that Audit Manager
can no longer be enabled for this account.

## Deployment

A second Lambda, `cloud-compliance-platform-evidence-collection`, deployed the same
way as Phase 4's scanner (reusing the same parameterised `terraform/modules/compute`),
on its own daily EventBridge schedule. Its execution role is read-only: `config:Get*`
(conformance pack compliance only), `securityhub:GetFindings`, three CloudTrail read
actions, `s3:PutObject` scoped to the `evidence/` prefix, and `kms:GenerateDataKey` on
the evidence bucket's CMK — no overlap with Phase 4's role, no write access to
anything.

## Testing: why MagicMock instead of moto here

Phase 4's tests used `moto` successfully for IAM. For this phase, checked moto's
actual behavior before relying on it, rather than assuming parity:

- **Security Hub**: `get_findings` is implemented, but moto does **not** apply the
  `Filters` parameter server-side — importing findings with different
  `ComplianceStatus`/`RecordState` combinations and querying with filters returned
  all of them regardless. A moto-based test would pass even if the collector's
  filter construction were wrong.
- **AWS Config**: none of the conformance pack compliance APIs
  (`get_conformance_pack_compliance_summary`, `get_conformance_pack_compliance_details`,
  `describe_conformance_packs`) are implemented in moto at all — calling them inside
  `mock_aws()` raises `NotImplementedError`.
- **CloudTrail**: `lookup_events` is not implemented either, though `describe_trails`
  and `get_trail_status` are.

Given that, the 14 collector tests (`python/tests/test_collectors.py`) use
`unittest.mock.MagicMock` clients instead — verifying each collector builds the
correct request (filters, pagination tokens, parameter names) and parses the
response shape correctly, without depending on AWS API availability in moto. The 2
storage tests (`test_storage.py`) do use moto, since S3 is fully and correctly
supported there.

**The request/response contract itself was verified against the real account**, not
just assumed: ran `python -m phase5_evidence_collection.cli collect` directly against
`cloud-compliance-platform-nist-csf` and `cloud-compliance-platform-trail` before
writing any tests, confirming real shapes (e.g. `get_conformance_pack_compliance_summary`
returning `ConformancePackComplianceStatus: NON_COMPLIANT`, `lookup_events` returning
real recent `Username`/`EventName` pairs) and that pagination genuinely was needed
(101 non-compliant rule/resource pairs across multiple pages).

## Real evidence collected

First real run (`aws lambda invoke` after deployment) wrote three snapshots:

| Control | Result |
|---|---|
| `CTRL-CONFIG-NISTCSF` | `NON_COMPLIANT` overall, 101 non-compliant rule/resource pairs (across both this project's resources and `access-review-prod`'s, since Config evaluates the whole account — see `docs/phase3_monitoring.md`) |
| `CTRL-SECURITYHUB-FINDINGS` | 226 active FAILED findings |
| `CTRL-CLOUDTRAIL-LOGGING` | Trail confirmed multi-region and logging, 50-event sample of recent management activity |

This phase collects evidence account-wide, the same way Phase 4's scanner does —
it's a reporting/evidence function, not a remediation one, so there's no scope
restriction here the way there is in `phase4_iam_governance/remediation.py`.

## Documentation

`docs/control_matrix.md` — the initial control matrix itself (control ID, evidence
source, ISO 27001 Annex A clause, SOC 2 TSC), explicitly scoped as a starting point
for Phase 6 to expand into a full RCM.
