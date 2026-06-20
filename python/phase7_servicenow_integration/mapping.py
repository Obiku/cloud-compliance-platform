"""Maps this project's AWS-evidence-producing controls (from docs/rcm.md) to the
ServiceNow Control records created for them under the "Cloud Compliance Automation
Platform - AWS Sandbox" entity (sn_grc_profile). Only the two controls Phase 7
actually syncs automatically are listed - CTRL-IAM-* controls are tested manually
per docs/rcm.md and are out of scope for this integration.

Looked up by `number` (not sys_id) so the mapping survives a re-import of the
instance; numbers are stable, sys_ids are not.
"""

from __future__ import annotations

from dataclasses import dataclass

from .client import ServiceNowClient

PROFILE_NAME = "Cloud Compliance Automation Platform - AWS Sandbox"

# Phase 5 control_id -> ServiceNow control number
CONTROL_NUMBER_BY_EVIDENCE_ID = {
    "CTRL-CONFIG-NISTCSF": "CTRL0020195",       # DE.CM-1 Network and system monitoring
    "CTRL-SECURITYHUB-FINDINGS": "CTRL0020196",  # CC7.1 Detection of security events
    "CTRL-CLOUDTRAIL-LOGGING": "CTRL0020197",    # A.12.4.1 Event logging
}


@dataclass(frozen=True)
class ResolvedControl:
    sys_id: str
    number: str
    name: str


def resolve_control(snow: ServiceNowClient, evidence_control_id: str) -> ResolvedControl:
    number = CONTROL_NUMBER_BY_EVIDENCE_ID[evidence_control_id]
    rows = snow.query("sn_compliance_control", f"number={number}", fields="sys_id,number,name")
    if not rows:
        raise LookupError(f"ServiceNow control {number} not found - was it deleted or renumbered?")
    row = rows[0]
    return ResolvedControl(sys_id=row["sys_id"], number=row["number"], name=row["name"])


def resolve_profile_sys_id(snow: ServiceNowClient) -> str:
    rows = snow.query("sn_grc_profile", f"name={PROFILE_NAME}", fields="sys_id")
    if not rows:
        raise LookupError(f"ServiceNow entity '{PROFILE_NAME}' not found")
    return rows[0]["sys_id"]
