"""Formats scan findings into a JSON record and a human-readable Markdown report."""

from __future__ import annotations

import dataclasses
import datetime
import json

from .scanner import Finding

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def to_json(findings: list[Finding], generated_at: datetime.datetime) -> str:
    payload = {
        "generated_at": generated_at.isoformat(),
        "finding_count": len(findings),
        "findings": [dataclasses.asdict(f) for f in findings],
    }
    return json.dumps(payload, indent=2, default=str)


def to_markdown(findings: list[Finding], generated_at: datetime.datetime, name_prefix: str) -> str:
    ordered = sorted(findings, key=lambda f: (SEVERITY_ORDER.get(f.severity, 99), f.check))
    in_scope_count = sum(1 for f in ordered if f.in_scope_for_remediation)

    lines = [
        "# IAM Governance Scan Report",
        "",
        f"**Generated:** {generated_at.isoformat()}",
        f"**Total findings:** {len(ordered)} ({in_scope_count} in scope for "
        f"`{name_prefix}` remediation, {len(ordered) - in_scope_count} informational "
        "only - belong to other resources in this account)",
        "",
        "| Severity | Check | Resource | In scope | Detail |",
        "|---|---|---|---|---|",
    ]
    for f in ordered:
        resource = f"{f.resource_type}:{f.resource_id}"
        scope = "yes" if f.in_scope_for_remediation else "no"
        lines.append(f"| {f.severity} | {f.check} | {resource} | {scope} | {f.detail} |")
    lines.append("")
    return "\n".join(lines)
