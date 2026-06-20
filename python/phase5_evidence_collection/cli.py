"""Local CLI for the evidence collectors.

Usage:
    python -m phase5_evidence_collection.cli collect \
        --conformance-pack-name cloud-compliance-platform-nist-csf \
        --trail-name cloud-compliance-platform-trail \
        [--evidence-bucket cloud-compliance-platform-evidence-575141563901]

Without --evidence-bucket, prints the snapshots to stdout instead of uploading.
"""

from __future__ import annotations

import argparse
import datetime
import json

import boto3

from . import collectors, storage


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def cmd_collect(args: argparse.Namespace) -> int:
    config = boto3.client("config")
    securityhub = boto3.client("securityhub")
    cloudtrail = boto3.client("cloudtrail")
    generated_at = _utcnow()

    snapshots = {
        "CTRL-CONFIG-NISTCSF": collectors.collect_config_compliance(
            config, args.conformance_pack_name
        ),
        "CTRL-SECURITYHUB-FINDINGS": collectors.collect_security_hub_findings(securityhub),
        "CTRL-CLOUDTRAIL-LOGGING": collectors.collect_cloudtrail_sample(
            cloudtrail, args.trail_name
        ),
    }

    if args.evidence_bucket:
        s3 = boto3.client("s3")
        for control_id, snapshot in snapshots.items():
            key = storage.write_evidence(s3, args.evidence_bucket, control_id, snapshot, generated_at)
            print(f"Wrote s3://{args.evidence_bucket}/{key}")
    else:
        for control_id, snapshot in snapshots.items():
            print(f"=== {control_id} ===")
            print(json.dumps(snapshot, indent=2, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="phase5_evidence_collection")
    sub = parser.add_subparsers(dest="command", required=True)

    collect_parser = sub.add_parser("collect", help="Run all evidence collectors")
    collect_parser.add_argument("--conformance-pack-name", required=True)
    collect_parser.add_argument("--trail-name", required=True)
    collect_parser.add_argument("--evidence-bucket")
    collect_parser.set_defaults(func=cmd_collect)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
