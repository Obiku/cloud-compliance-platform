"""Pushes AWS evidence into ServiceNow:
- Security Hub FAILED findings become GRC Issues (sn_grc_issue), deduplicated by
  correlation_id so re-runs don't create duplicates.
- AWS Config's conformance pack compliance state updates the mapped control's
  failed/passed indicator counts - this project doesn't build the full GRC
  Indicator/Indicator-Result framework (a deeper, separate configuration
  surface), so the rollup fields the platform itself uses for control status are
  written to directly instead.
Every record created or updated carries the S3 evidence URI it came from, so an
auditor can trace any Issue or Control's number straight back to underlying
evidence in the evidence bucket.
"""

from __future__ import annotations

import hashlib
from typing import Any

from .client import ServiceNowClient
from .evidence import LatestEvidence
from .mapping import ResolvedControl

MAX_ISSUES_PER_RUN = 5


def push_security_hub_issues(
    snow: ServiceNowClient, profile_sys_id: str, control: ResolvedControl, evidence: LatestEvidence
) -> dict[str, Any]:
    findings = evidence.snapshot.get("findings", [])[:MAX_ISSUES_PER_RUN]
    created: list[str] = []
    skipped_existing: list[str] = []

    for finding in findings:
        resource_id = finding.get("resource_id") or "unknown-resource"
        # correlation_id is truncated by ServiceNow at ~100 chars, which silently
        # broke exact-match dedup lookups for long ARNs/titles - hash instead so
        # the stored and queried values are always identical and well under the limit.
        digest = hashlib.sha256(f"{resource_id}:{finding.get('title')}".encode()).hexdigest()[:32]
        correlation_id = f"aws-securityhub:{digest}"

        existing = snow.query(
            "sn_grc_issue", f"correlation_id={correlation_id}", fields="number", limit=1
        )
        if existing:
            skipped_existing.append(existing[0]["number"])
            continue

        issue = snow.create(
            "sn_grc_issue",
            {
                "short_description": f"[{control.number}] {finding.get('title')}",
                "description": (
                    f"Security Hub finding (severity {finding.get('severity')}) on "
                    f"{finding.get('resource_type')} {resource_id}.\n\n"
                    f"Control: {control.number} - {control.name}\n"
                    f"Evidence: {evidence.s3_uri}"
                ),
                "profile": profile_sys_id,
                "correlation_id": correlation_id,
            },
        )
        created.append(issue["number"])

    return {
        "control": control.number,
        "evidence_uri": evidence.s3_uri,
        "issues_created": created,
        "issues_already_existed": skipped_existing,
    }


def update_compliance_assessment(
    snow: ServiceNowClient, control: ResolvedControl, evidence: LatestEvidence
) -> dict[str, Any]:
    snapshot = evidence.snapshot
    failed = snapshot.get("non_compliant_count", 0)
    overall_status = snapshot.get("overall_status", "UNKNOWN")
    passed = 1 if overall_status == "COMPLIANT" and failed == 0 else 0

    note = (
        f"Phase 7 sync: AWS Config conformance pack status={overall_status}, "
        f"non-compliant rule/resource pairs={failed}. Evidence: {evidence.s3_uri}"
    )
    snow.update(
        "sn_compliance_control",
        control.sys_id,
        {
            "failed_indicators": failed,
            "passed_indicators": passed,
            "comments": note,
        },
    )
    return {
        "control": control.number,
        "evidence_uri": evidence.s3_uri,
        "failed_indicators": failed,
        "passed_indicators": passed,
    }
