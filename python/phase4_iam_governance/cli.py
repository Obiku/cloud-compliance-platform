"""Local CLI for the IAM governance scanner and remediator.

Usage:
    python -m phase4_iam_governance.cli scan --name-prefix cloud-compliance-platform \
        [--out-json report.json] [--out-markdown report.md]

    python -m phase4_iam_governance.cli remediate --name-prefix cloud-compliance-platform \
        --check iam_admin_access_attached --resource-id cloud-compliance-platform-legacy-admin \
        --approve
"""

from __future__ import annotations

import argparse
import datetime
import sys

import boto3

from . import remediation, report
from .scanner import run_full_scan


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def cmd_scan(args: argparse.Namespace) -> int:
    iam = boto3.client("iam")
    findings = run_full_scan(iam, args.name_prefix)
    generated_at = _utcnow()

    if args.out_json:
        with open(args.out_json, "w", encoding="utf-8") as f:
            f.write(report.to_json(findings, generated_at))
    if args.out_markdown:
        with open(args.out_markdown, "w", encoding="utf-8") as f:
            f.write(report.to_markdown(findings, generated_at, args.name_prefix))

    print(report.to_markdown(findings, generated_at, args.name_prefix))
    return 0


def cmd_remediate(args: argparse.Namespace) -> int:
    iam = boto3.client("iam")
    findings = run_full_scan(iam, args.name_prefix)

    matches = [
        f
        for f in findings
        if f.check == args.check and f.resource_id == args.resource_id
    ]
    if not matches:
        print(
            f"No current finding matches check={args.check!r} resource_id={args.resource_id!r}. "
            "Nothing to do (it may already be remediated).",
            file=sys.stderr,
        )
        return 1

    for finding in matches:
        try:
            result = remediation.remediate(iam, finding, approved=args.approve)
        except remediation.ScopeError as exc:
            print(f"REFUSED: {exc}", file=sys.stderr)
            return 2
        status = "APPLIED" if result.applied else "DRY RUN"
        print(f"[{status}] {result.action}: {result.detail}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="phase4_iam_governance")
    parser.add_argument("--name-prefix", default="cloud-compliance-platform")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_parser = sub.add_parser("scan", help="Run the read-only IAM governance scan")
    scan_parser.add_argument("--out-json")
    scan_parser.add_argument("--out-markdown")
    scan_parser.set_defaults(func=cmd_scan)

    remediate_parser = sub.add_parser("remediate", help="Remediate a single finding")
    remediate_parser.add_argument("--check", required=True)
    remediate_parser.add_argument("--resource-id", required=True)
    remediate_parser.add_argument(
        "--approve",
        action="store_true",
        help="Actually apply the change. Without this flag, runs as a dry run.",
    )
    remediate_parser.set_defaults(func=cmd_remediate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
