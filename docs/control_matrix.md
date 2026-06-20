# Initial Control Matrix

Maps each evidence artifact collected by `python/phase5_evidence_collection/` to its
control ID, ISO 27001 Annex A clause, and SOC 2 Trust Services Criterion. Control IDs
here are the single source of truth defined in `controls.py` — this table mirrors
that file rather than duplicating free-text definitions independently of the code.

Audit Manager reports are not part of this matrix: AWS put Audit Manager into
maintenance mode in April 2026 and this account was never registered before that
cutoff (see `PROJECT_PLAN.md`'s Phase 3 change log and `docs/phase3_monitoring.md`).

| Control ID | Description | Evidence source | ISO 27001 Annex A | SOC 2 TSC |
|---|---|---|---|---|
| `CTRL-CONFIG-NISTCSF` | AWS Config conformance pack (NIST CSF) compliance status | AWS Config (`get_conformance_pack_compliance_summary`, `get_conformance_pack_compliance_details`) | A.18.2.2 Compliance with security policies and standards | CC4.1 Monitoring Activities |
| `CTRL-SECURITYHUB-FINDINGS` | Security Hub active FAILED findings snapshot (CIS AWS Foundations, AWS FSBP) | Security Hub (`get_findings`) | A.12.6.1 Management of technical vulnerabilities | CC7.1 Identification and analysis of security events |
| `CTRL-CLOUDTRAIL-LOGGING` | CloudTrail trail status and recent management event sample | CloudTrail (`describe_trails`, `get_trail_status`, `lookup_events`) | A.12.4.1 Event logging | CC7.2 Monitoring of system components for anomalies |

## Evidence storage layout

```
s3://cloud-compliance-platform-evidence-575141563901/evidence/<control-id>/<YYYY>/<MM>/<DD>/<HHMMSS>/snapshot.json
```

Each snapshot is a timestamped, immutable JSON artifact (the evidence bucket has
versioning enabled) — collected daily by the scheduled
`cloud-compliance-platform-evidence-collection` Lambda, or on demand via
`python -m phase5_evidence_collection.cli collect`.

## This is intentionally an *initial* matrix

Phase 6 expands this into a full Risk & Control Matrix: control owner, control type
(preventive/detective/corrective), nature (automated/manual/hybrid), test frequency,
and a formal test procedure per control. This matrix only establishes the control ID
↔ evidence ↔ framework mapping that Phase 6 builds on.
