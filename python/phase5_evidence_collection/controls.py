"""Initial control matrix: maps each evidence artifact this phase collects to the
relevant ISO 27001 Annex A clause and SOC 2 Trust Services Criterion. This is the
single source of truth for control IDs - both the collectors and
docs/control_matrix.md reference these, not duplicated free-text elsewhere.

Audit Manager reports were dropped from this list (see PROJECT_PLAN.md's Phase 3
change log - Audit Manager can no longer be enabled for this account).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Control:
    control_id: str
    description: str
    evidence_source: str
    iso27001_annex_a: str
    soc2_tsc: str


CONTROLS: list[Control] = [
    Control(
        control_id="CTRL-CONFIG-NISTCSF",
        description="AWS Config conformance pack (NIST CSF) compliance status",
        evidence_source="config",
        iso27001_annex_a="A.18.2.2 Compliance with security policies and standards",
        soc2_tsc="CC4.1 Monitoring Activities",
    ),
    Control(
        control_id="CTRL-SECURITYHUB-FINDINGS",
        description="Security Hub active findings snapshot (CIS AWS Foundations, AWS FSBP)",
        evidence_source="security_hub",
        iso27001_annex_a="A.12.6.1 Management of technical vulnerabilities",
        soc2_tsc="CC7.1 Identification and analysis of security events",
    ),
    Control(
        control_id="CTRL-CLOUDTRAIL-LOGGING",
        description="CloudTrail trail status and recent management event sample",
        evidence_source="cloudtrail",
        iso27001_annex_a="A.12.4.1 Event logging",
        soc2_tsc="CC7.2 Monitoring of system components for anomalies",
    ),
]


def get_control(control_id: str) -> Control:
    for control in CONTROLS:
        if control.control_id == control_id:
            return control
    raise KeyError(f"No such control: {control_id}")
