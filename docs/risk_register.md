# Risk Register

Finalises the two risks Phase 7 created in ServiceNow (`sn_risk_risk`) with a real
likelihood x impact scoring methodology, and adds one new risk surfaced by this
phase's review of live Security Hub findings. Phase 7 deliberately left both
existing risks at the criteria default (5/5) and scoped the actual scoring
methodology to this phase.

## Methodology

Each risk is scored on two axes, 1 to 5:

| Score | Likelihood | Impact |
|---|---|---|
| 1 | Extremely unlikely | Very low |
| 2 | Unlikely | Low |
| 3 | Possible | Moderate |
| 4 | Likely | Major |
| 5 | Extremely likely | Severe |

Inherent risk = likelihood x impact, scored before any of this platform's controls
are taken into account. Residual risk = likelihood x impact after applying the
controls in `docs/rcm.md` that actually exist and run today. A risk's impact axis
rarely moves between inherent and residual (a control reduces how often or how far
something gets, not how bad it would be if it succeeded); the likelihood axis is
where controls do most of the work.

| Band | Score range |
|---|---|
| Low | 1-5 |
| Medium | 6-12 |
| High | 13-19 |
| Critical | 20-25 |

## Scope

This register covers risks within this platform's own ownership: the resources and
controls built across Phases 1-8. The AWS sandbox account also runs an unrelated,
pre-existing workload (`access-review-prod`, see `docs/phase3_monitoring.md`), and
its account-wide Config/Security Hub/GuardDuty findings surface plenty of generic
AWS Foundational Security Best Practices noise belonging to that other project's own
resources (DynamoDB tables, CloudFormation stacks, EC2 VPC endpoints, and similar).
Those are excluded here, consistent with how `docs/rcm.md` and `docs/phase7_servicenow_integration.md`
already scope this platform's register to its own seeded scenarios rather than
generic account-wide findings.

## Register

### RK0020001 - Excessive IAM privileges

Pulled forward from Phase 7. An IAM identity holding `AdministratorAccess` directly
(outside a group, with no MFA) can take any action in the account, including
destructive ones, and a compromised credential for that identity is a full account
takeover.

| | Likelihood | Impact | Score | Band |
|---|---|---|---|---|
| Inherent | 4 | 5 | 20 | Critical |
| Residual | 2 | 4 | 8 | Medium |

Residual likelihood drops because the live AWS attachment was already detached in
Phase 4 (confirmed by before/after scan evidence) and `CTRL-IAM-GROUP-MFA` denies
all group actions without MFA even if a policy is reattached. Residual impact stays
high rather than dropping further, since admin-level access is severe by nature if
the control is ever bypassed; the Terraform code still defines the seeded
attachment on purpose for Phase 6 re-performance testing, so this is not yet a
fully closed gap. Controls applied: `CTRL-IAM-NOADMIN`, `CTRL-IAM-MFA`,
`CTRL-IAM-GROUP-MFA`.

### RK0020002 - Insufficient security monitoring

Pulled forward from Phase 7. Without reliable detection, a real incident (a
misconfiguration, an exposed credential, an unauthorized change) can go unnoticed
long enough to cause real damage.

| | Likelihood | Impact | Score | Band |
|---|---|---|---|---|
| Inherent | 3 | 4 | 12 | Medium |
| Residual | 2 | 3 | 6 | Low |

Residual likelihood and impact both drop: daily automated evidence collection
(`CTRL-CONFIG-NISTCSF`, `CTRL-SECURITYHUB-FINDINGS`, `CTRL-CLOUDTRAIL-LOGGING`) plus
the Phase 8 Grafana dashboard give near-real-time visibility instead of relying on
periodic manual review, shortening both the time to notice an issue and the window
in which it can do damage.

### RK0020003 - Root account compromise (no hardware MFA on root)

New, surfaced by this phase pulling live Security Hub findings rather than assumed
ones: `IAM.6` ("Hardware MFA should be enabled for the root user") is a current,
active CRITICAL finding on this account. Root credentials bypass every IAM control
this platform has built, so a compromised root login is a full account takeover
regardless of how well-governed the rest of IAM is.

| | Likelihood | Impact | Score | Band |
|---|---|---|---|---|
| Inherent | 2 | 5 | 10 | Medium |
| Residual | 2 | 5 | 10 | Medium |

No residual reduction: this is a genuine, currently unmitigated gap, not yet closed
by any control this platform has built. Root login events are already captured by
CloudTrail and would show up in `CTRL-CLOUDTRAIL-LOGGING`'s evidence, but detecting
a root login after the fact is not the same as preventing one with hardware MFA.
Logged as an open item rather than silently left out of the register - see "Open
items" below.

## Investigated and explained, not registered as risks

Two live findings were checked and ruled out as not representing new risk:

- **Two Security Hub findings for root-credential API usage** (`DescribeRegions`,
  `ConsoleLogin`) reflect this account's own legitimate setup activity, not
  unauthorized root usage - consistent with the account's known history (see
  `docs/phase1_before_state.md`), not a new finding.
- **One GuardDuty finding** flagging the real automation user (`Saintkings`) for
  "anomalously invoking APIs commonly used in Persistence tactics" is a known false
  positive: this account ran a high volume of unusual-for-a-human, scripted boto3
  calls across Phases 4 through 9 (IAM scans, evidence collection, Config/Security
  Hub/GuardDuty queries), which is exactly the kind of pattern GuardDuty's anomaly
  model flags from a normally low-activity account. No unexpected resource changes
  or unfamiliar source IPs accompany it.

## Open items

- **RK0020003 has no compensating control yet.** Enabling hardware MFA on the root
  user is a manual console action (AWS does not expose root MFA enrollment via
  Terraform or the API) and is not yet done. Tracked as a backlog item alongside
  the existing entries in `docs/vulnerability_log.md`.
- **Scoring these fields directly in ServiceNow via the Table API is blocked.**
  Attempting `PATCH` on `sn_risk_risk.likelihood`/`impact`/`residual_likelihood`/
  `residual_impact` for both RK0020001 and RK0020002 succeeded with a `200` but the
  values silently reverted to the unscored default in the same response - the same
  class of workflow-engine guardrail Phase 7 already documented for direct state
  writes on this table. This register is the source of truth for the actual scores;
  ServiceNow's two risk records still show the unscored default and would need the
  same manual UI-driven workflow path Phase 7 used for state changes to be updated,
  which is out of scope for this phase. RK0020003 does not yet exist in ServiceNow
  at all - creating it hits the same Risk workflow Phase 7 already worked through by
  hand, so it is recorded here first rather than blocked on a repeat of that effort.
