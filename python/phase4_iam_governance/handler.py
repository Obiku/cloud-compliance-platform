"""Scheduled Lambda entrypoint. Runs the read-only scan only - remediation is
deliberately not triggered automatically; see cli.py for the approval-gated path.
"""

from __future__ import annotations

import datetime
import os

import boto3

from . import report
from .scanner import run_full_scan


def lambda_handler(event, context):
    name_prefix = os.environ.get("NAME_PREFIX", "cloud-compliance-platform")
    evidence_bucket = os.environ["EVIDENCE_BUCKET"]

    iam = boto3.client("iam")
    s3 = boto3.client("s3")

    findings = run_full_scan(iam, name_prefix)
    generated_at = datetime.datetime.now(datetime.timezone.utc)
    timestamp = generated_at.strftime("%Y/%m/%d/%H%M%S")

    json_body = report.to_json(findings, generated_at)
    markdown_body = report.to_markdown(findings, generated_at, name_prefix)

    json_key = f"iam-governance/{timestamp}/report.json"
    markdown_key = f"iam-governance/{timestamp}/report.md"

    s3.put_object(Bucket=evidence_bucket, Key=json_key, Body=json_body.encode("utf-8"))
    s3.put_object(Bucket=evidence_bucket, Key=markdown_key, Body=markdown_body.encode("utf-8"))

    return {
        "finding_count": len(findings),
        "evidence_bucket": evidence_bucket,
        "json_key": json_key,
        "markdown_key": markdown_key,
    }
