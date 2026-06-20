"""Scheduled Lambda entrypoint. Collects all three evidence types and writes each
to the evidence bucket under its control ID.
"""

from __future__ import annotations

import datetime
import os

import boto3

from . import collectors, storage


def lambda_handler(event, context):
    evidence_bucket = os.environ["EVIDENCE_BUCKET"]
    conformance_pack_name = os.environ["CONFORMANCE_PACK_NAME"]
    trail_name = os.environ["TRAIL_NAME"]

    config = boto3.client("config")
    securityhub = boto3.client("securityhub")
    cloudtrail = boto3.client("cloudtrail")
    s3 = boto3.client("s3")

    generated_at = datetime.datetime.now(datetime.timezone.utc)
    keys = {}

    config_snapshot = collectors.collect_config_compliance(config, conformance_pack_name)
    keys["CTRL-CONFIG-NISTCSF"] = storage.write_evidence(
        s3, evidence_bucket, "CTRL-CONFIG-NISTCSF", config_snapshot, generated_at
    )

    securityhub_snapshot = collectors.collect_security_hub_findings(securityhub)
    keys["CTRL-SECURITYHUB-FINDINGS"] = storage.write_evidence(
        s3, evidence_bucket, "CTRL-SECURITYHUB-FINDINGS", securityhub_snapshot, generated_at
    )

    cloudtrail_snapshot = collectors.collect_cloudtrail_sample(cloudtrail, trail_name)
    keys["CTRL-CLOUDTRAIL-LOGGING"] = storage.write_evidence(
        s3, evidence_bucket, "CTRL-CLOUDTRAIL-LOGGING", cloudtrail_snapshot, generated_at
    )

    return {"evidence_bucket": evidence_bucket, "keys": keys}
