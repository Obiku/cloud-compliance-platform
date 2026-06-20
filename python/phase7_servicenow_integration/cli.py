"""Local CLI for the ServiceNow integration. Deliberately not deployed as a
scheduled Lambda - like Phase 4's remediation step, pushing data into the GRC
system of record is run by a human, on demand, not on an unattended schedule.

Usage:
    python -m phase7_servicenow_integration.cli sync \
        --evidence-bucket cloud-compliance-platform-evidence-575141563901

Reads SNOW_INSTANCE / SNOW_USER / SNOW_PASSWORD from the environment (see
cred.env, gitignored).
"""

from __future__ import annotations

import argparse
import json

import boto3

from . import sync
from .client import ServiceNowClient
from .evidence import get_latest_evidence
from .mapping import resolve_control, resolve_profile_sys_id


def cmd_sync(args: argparse.Namespace) -> int:
    snow = ServiceNowClient()
    s3 = boto3.client("s3")
    profile_sys_id = resolve_profile_sys_id(snow)

    results: dict[str, object] = {}

    securityhub_control = resolve_control(snow, "CTRL-SECURITYHUB-FINDINGS")
    securityhub_evidence = get_latest_evidence(s3, args.evidence_bucket, "CTRL-SECURITYHUB-FINDINGS")
    results["security_hub_issues"] = sync.push_security_hub_issues(
        snow, profile_sys_id, securityhub_control, securityhub_evidence
    )

    config_control = resolve_control(snow, "CTRL-CONFIG-NISTCSF")
    config_evidence = get_latest_evidence(s3, args.evidence_bucket, "CTRL-CONFIG-NISTCSF")
    results["compliance_assessment"] = sync.update_compliance_assessment(
        snow, config_control, config_evidence
    )

    print(json.dumps(results, indent=2, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="phase7_servicenow_integration")
    sub = parser.add_subparsers(dest="command", required=True)

    sync_parser = sub.add_parser("sync", help="Push latest Phase 5 evidence into ServiceNow")
    sync_parser.add_argument("--evidence-bucket", required=True)
    sync_parser.set_defaults(func=cmd_sync)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
