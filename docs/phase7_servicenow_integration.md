# Phase 7 — ServiceNow IRM integration

Builds out the ServiceNow governance layer (Policy & Compliance + Risk + Issues)
and connects it to the AWS environment via the Table API.

## Policy & Compliance configuration

The instance's GRC content pack ships hundreds of demo Authority Documents,
Control Objectives, and Controls (mostly unrelated SAP/PeopleSoft/retail demo
data). Rather than build from scratch, this phase reused the three correctly-named,
unlinked Authority Documents the pack provides and attached real content to them:

| Authority Document | Number | Control Objectives added |
|---|---|---|
| ISO/IEC 27001:2022 | AD0020002 | A.9.2.3 Management of privileged access rights; A.12.4.1 Event logging |
| SOC 2 Trust Services Criteria | AD0020003 | CC6.1 Logical access security; CC7.1 Detection of security events |
| NIST Cybersecurity Framework (CSF) | AD0020004 | PR.AC-4 Access permissions and authorizations; DE.CM-1 Network and system monitoring |

Each Control Objective has one linked Control (`sn_compliance_control`), scoped
to a new Entity (`sn_grc_profile`) named "Cloud Compliance Automation Platform -
AWS Sandbox" rather than any of the demo entities (Kodak, Seagate, etc.). Each
Control's `owner` and `implementation_statement` were set to point back at the
actual Phase 4/5 automation that satisfies it:

| Control | Number | Implements |
|---|---|---|
| A.9.2.3 Management of privileged access rights | CTRL0020192 | `CTRL-IAM-NOADMIN` |
| PR.AC-4 Access permissions and authorizations | CTRL0020193 | `CTRL-IAM-GROUP-MFA`, `CTRL-IAM-MFA` |
| CC6.1 Logical access security | CTRL0020194 | `CTRL-IAM-ACCESSKEY-AGE`, `CTRL-IAM-UNUSED-ROLES` |
| DE.CM-1 Network and system monitoring | CTRL0020195 | `CTRL-CONFIG-NISTCSF` |
| CC7.1 Detection of security events | CTRL0020196 | `CTRL-SECURITYHUB-FINDINGS` |
| A.12.4.1 Event logging | CTRL0020197 | `CTRL-CLOUDTRAIL-LOGGING` |

## Risk Register

Two risks were added to `sn_risk_risk`, matching the platform's own seeded
scenarios rather than generic examples:

- `RK0020001` — Excessive IAM privileges could allow unauthorized access or
  destructive actions
- `RK0020002` — Insufficient security monitoring could delay detection of a
  security incident

Likelihood/impact scoring was left at the criteria default rather than tuned —
the project plan scopes a proper likelihood × impact methodology to Phase 9,
not Phase 7; this phase only needed the register to exist and be populated.

**Resolved via the UI, with one layer turning out deeper than expected.**
Advancing the 6 Controls out of Draft required clicking through their actual
workflow buttons (Attest → Submit for Review → Monitor) rather than writing to
`state` directly - confirmed by testing a single-step PATCH (`draft` → `attest`)
via the API, which was *also* silently reverted, ruling out "just walk the
states one at a time via API" as a workaround. The 2 Risks needed the same
treatment via their own workflow (Assess → Submit for Review → Monitor). Both
were done by hand in the UI and verified via the API afterward (all 6 Controls
and both Risks confirmed `state=monitor`, `active=true`).

A third, undocumented layer then surfaced: the 6 **Control Objectives**
(`sn_compliance_policy_statement`) were still `active=false, state=draft`,
one level above the Controls. These don't expose Attest/Submit/Monitor buttons
at all - checking their `Active` checkbox and clicking Update was sufficient to
auto-publish them (`state` became `published`), confirmed via the API for all 6.

**Still outstanding: the actual `sn_risk_m2m_risk_control` link insert.** After
every record in the chain (Authority Documents, Risk Statements, the Entity,
both Risks, all 6 Controls, all 6 Control Objectives) was confirmed
active/published/monitor via the API, the link insert was retried and still
rejected with the identical `Avoid inactive items` business rule error. This
rules out record state as the actual cause - the rule (whose real script is
hidden from API reads due to cross-scope protection, see below) most likely
only permits this link to be created through the platform's own "Add" button
inside a related list (the curated UI flow for associating a Risk with a
Control), not via a direct Table API insert, regardless of state. Decided not
to chase this further: it only adds a traceability link in ServiceNow's UI
between the 2 Risks and their 6 Controls, with zero effect on any actual
control's operation or any automation in this project. The two risks and the
six controls each independently and correctly reflect the platform's evidence
and remediation that satisfies them (see the implementation_statement values
above) - they're just not cross-linked to each other within ServiceNow's data
model. **If this traceability matters later:** open a Risk record in the UI,
scroll past the standard tabs (Ownership/Assessment/Scoring/Response/
Monitoring/Activity journal) for a related list offering an "Add" button for
Controls, and use that instead of the API.

## GRC roles and segregation of duties

Rather than define new custom roles, this phase used the platform's own
built-in GRC roles directly and created one test user per persona:

| Test user | Role | Persona |
|---|---|---|
| `test.controlowner` | `sn_compliance.manager` | Control owner |
| `test.riskmanager` | `sn_risk.manager` | Risk manager |
| `test.auditor` | `sn_compliance.reader` + `sn_risk.reader` | Auditor (read-only) |

No separate admin test user was created — the real `admin` account already
represents that persona.

**Outstanding (manual, API-blocked, and hit a second platform bug):**
`sys_security_acl` cannot be written to via the Table API even as `admin` — ACL
changes require an elevated UI session (a deliberate platform guardrail, not a
permissions gap on this account). Confirmed this by reproducing the same `403`
twice. Elevating to `security_admin` via "Elevate Roles" then did make the rest
of the New ACL form editable (Type, Operation, Name, Description), but the
**Script** field itself stayed stuck in a "Cannot edit in read-only editor"
state across three independent attempts: the original session, a fresh
incognito window, and a completely different browser. Same result every time,
including after re-elevating roles in each new session. This is a genuine bug
in this PDI's form rendering for that field, not a permissions or session
issue - confirmed by ruling out every plausible cause (role elevation, cached
session state, browser-specific rendering).

The ACL therefore still needs to be created by hand once the platform bug is
worked around (e.g. via ServiceNow support, a future platform patch, or trying
the classic UI's non-workspace script editor if one can be reached) or
recreated via an Update Set imported from a different instance where the form
renders correctly:

**System Security > Access Control (ACL) > New** (requires Elevate Roles →
`security_admin` first)

| Field | Value |
|---|---|
| Type | `record` |
| Operation | `write` |
| Name | `sn_grc_issue` (leave the field-specific second dropdown as `-- None --` — it excludes `state` because an OOB ACL already exists for that exact field+operation, so the rule below applies at the whole-record level and self-scopes via its own state check instead) |
| Active | true |
| Admin overrides | false |
| Script | see below |

```javascript
var isClosing = (String(current.state) == '3' || String(current.state) == '4');
var isRaiser = (String(current.opened_by) == String(gs.getUserID()));
answer = !(isClosing && isRaiser);
```

This denies setting an Issue to Closed Complete (3) or Closed Incomplete (4)
when the acting user is also the Issue's `opened_by`. Once in place, test it by
impersonating `test.controlowner`, opening an Issue, and attempting to close
it (should be denied), then impersonating a different user and closing the
same Issue (should succeed).

## Python integration (`python/phase7_servicenow_integration/`)

A local CLI, not a scheduled Lambda — like Phase 4's remediation step, pushing
data into the GRC system of record is something a human runs on demand, not on
an unattended schedule.

- `client.py` — minimal Table API client (`requests`, Basic Auth from
  `SNOW_INSTANCE`/`SNOW_USER`/`SNOW_PASSWORD` env vars).
- `mapping.py` — resolves this project's evidence control IDs to ServiceNow
  control `number`s by querying the API, not hardcoded `sys_id`s, so the mapping
  survives a re-import of the instance.
- `evidence.py` — reads the most recent snapshot Phase 5 already wrote to the
  evidence bucket for a given control (no new AWS calls — reuses Phase 5's
  output, doesn't duplicate its collection logic).
- `sync.py` — `push_security_hub_issues` creates a GRC Issue per Security Hub
  FAILED finding (capped at 5 per run), deduplicated by a hashed
  `correlation_id`; `update_compliance_assessment` writes AWS Config's
  non-compliant count into the mapped control's `failed_indicators`/
  `passed_indicators` fields. Every Issue and assessment note carries the S3
  evidence URI it came from.
- `cli.py` — `python -m phase7_servicenow_integration.cli sync --evidence-bucket <bucket>`.

**Why `failed_indicators`/`passed_indicators` and not a dedicated "Compliance
Assessment" record:** the platform's real mechanism for this is the GRC
Indicator/Indicator Result framework (`sn_grc_indicator`, `sn_grc_indicator_result`),
which is a deeper configuration surface (defining indicator types, item
functions, smart-assessment rollup rules) than this phase's scope justifies.
`failed_indicators`/`passed_indicators` are the platform's own per-control
rollup fields and accept direct writes without hitting the workflow-engine
restrictions encountered elsewhere in this phase, so the integration writes to
them directly and documents the simplification here rather than silently
implying full Indicator-framework wiring.

### Bug found and fixed during real-instance testing

The first end-to-end run created 5 Issues; running it again immediately
(idempotency check) created 5 *more* instead of recognizing the existing ones.
Root cause: `correlation_id` is silently truncated by ServiceNow at roughly 100
characters, and the original implementation built it from the full finding
title and resource ARN — long AWS ARNs alone exceed that. The stored
(truncated) value never matched the full value used in the next run's lookup
query. Fixed by hashing `resource_id:title` into a fixed-length digest instead
of concatenating the raw strings, so the stored and queried values are always
identical. Verified by re-running the CLI twice against the real instance: run
1 created 5 Issues, run 2 reported all 5 as `issues_already_existed` with zero
new creates. The 10 duplicate Issues created while debugging this were deleted.

### Testing

`python/tests/test_phase7_evidence.py` (moto S3 — fully supported, per Phase
5's note that it's the AWS service moto handles well) and
`python/tests/test_phase7_sync.py` (MagicMock `ServiceNowClient` — the real API
was verified by hand against the dev397101 PDI instead, per Phase 5's
established pattern of not trusting a mocking library for behavior not
actually verified against the real service).
