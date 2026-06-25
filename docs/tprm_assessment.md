# Third-Party Risk Management Assessment: ServiceNow

A lightweight TPRM assessment treating ServiceNow as a SaaS third party, since the
platform's GRC system of record (Phase 7) is an external vendor dependency, not
something this project hosts or controls. Scoped to what a TPRM review for a single
SaaS dependency in a small project actually needs: what data goes there, who can
reach it, what the vendor's own assurances are, and what residual risk is left
after this project's own controls around it.

## Vendor profile

| | |
|---|---|
| Vendor | ServiceNow, Inc. |
| Service used | ServiceNow IRM (GRC) on a Personal Developer Instance, `dev397101.service-now.com` |
| Function | System of record for Authority Documents, Control Objectives, Controls, Risks, and Issues (`docs/phase7_servicenow_integration.md`) |
| Integration method | ServiceNow Table API (REST), Basic Auth |
| Contract type | Free developer instance (PDI) - not a production commercial agreement |

## Data flow and classification

| Data sent to ServiceNow | Classification | Notes |
|---|---|---|
| Control metadata (descriptions, owners, framework mappings) | Internal, non-sensitive | Authored directly in ServiceNow or pushed by `python/phase7_servicenow_integration/`. |
| Security Hub finding summaries (title, severity, resource type, S3 evidence URI) | Internal, non-sensitive | `sync.py`'s `push_security_hub_issues`; no raw credentials, account numbers are not secret but are account-identifying. |
| AWS Config compliance counts | Internal, non-sensitive | Aggregate pass/fail counts only, not raw resource configuration. |

**No AWS credentials, secrets, or personal data ever flow to ServiceNow.** The
integration is one-directional (this project pushes summaries into ServiceNow; it
never pulls ServiceNow data back into an AWS action), which limits the blast radius
of a ServiceNow-side compromise to data disclosure, not a path back into the AWS
account.

## Access scope

The integration authenticates as a single ServiceNow user via Basic Auth, with
credentials in `cred.env` (gitignored, parsed in Python only - never sourced into a
shell, per this project's credential handling practice). No OAuth, no scoped API
key, no IP allowlisting - a deliberate simplification appropriate for a developer
instance with no real data behind it, but a real production deployment would need a
scoped service account with table-level ACLs and credential rotation, not a shared
admin-equivalent login.

## Vendor security posture

ServiceNow is a large, publicly traded SaaS vendor with standard enterprise
attestations (SOC 2 Type II, ISO/IEC 27001) for its commercial cloud offering, which
the developer instance used here inherits the same underlying platform
infrastructure from. This assessment does not independently verify those
attestations - for a free developer instance with no production data, doing so
would be disproportionate to the actual risk. A production deployment handling real
control/risk data would warrant requesting the vendor's current SOC 2 report and
reviewing it before go-live, which is noted here as a gap for that future case
rather than something this assessment completes now.

## Platform limitations found during integration (relevant to vendor risk, not just delivery)

Two platform-level issues surfaced during Phase 7 and Phase 9 are relevant to a
TPRM review because they are vendor platform behavior, not this project's own
control gaps:

- **The segregation-of-duties ACL's Script field could not be edited** across three
  independent sessions/browsers, a genuine PDI form-rendering bug (`docs/phase7_servicenow_integration.md`).
- **Direct Table API writes to workflow-driven fields are silently reverted** once a
  record has advanced past its initial state - encountered first for Risk/Control
  `state` transitions (Phase 7) and again for Risk `likelihood`/`impact` scoring
  fields (Phase 9, `docs/risk_register.md`). This means any future integration that
  assumes the Table API can update these fields after go-live needs to route through
  the same UI workflow buttons instead, which is a meaningful integration
  constraint, not a one-off bug.

Neither issue is a security risk in itself, but both limit how much this
integration can be trusted to keep ServiceNow's record fully in sync with reality
without a recurring manual step - a residual operational risk worth carrying
forward rather than treating the integration as fully automated.

## Risk rating

| | Likelihood | Impact | Score | Band |
|---|---|---|---|---|
| Inherent | 2 | 2 | 4 | Low |
| Residual | 2 | 2 | 4 | Low |

No change between inherent and residual: the data sent is already low-sensitivity
and the access pattern is already narrow (one integration, one direction, no
credentials in transit), so there isn't a control this project could add that would
meaningfully lower this further. The main residual risk is the credential rotation
item below, not the vendor's own security posture.

## Outstanding

- **ServiceNow admin password rotation.** A password fragment for this instance was
  echoed into a debugging transcript earlier in the project (during a `cred.env`
  shell-sourcing issue) and has not yet been rotated. This is the one concrete,
  actionable item this assessment surfaces - low impact given this is a free
  developer instance with no real data, but it is the correct TPRM action regardless
  of the instance's stakes.
- This assessment is appropriately lightweight for a developer instance; it should
  be redone in full (vendor due diligence questionnaire, contract review, SOC 2
  report review) before any real production data is put into a ServiceNow instance
  on this integration.
