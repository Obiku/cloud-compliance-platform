"""Scheduled Lambda entrypoint. Collects the four GRC counts and publishes
them to CloudWatch for the Grafana dashboard to read.
"""

from __future__ import annotations

import datetime
import os

import boto3

from . import collectors, publisher


def lambda_handler(event, context):
    conformance_pack_name = os.environ["CONFORMANCE_PACK_NAME"]
    detector_id = os.environ["GUARDDUTY_DETECTOR_ID"]

    config = boto3.client("config")
    securityhub = boto3.client("securityhub")
    cloudtrail = boto3.client("cloudtrail")
    guardduty = boto3.client("guardduty")
    cloudwatch = boto3.client("cloudwatch")

    config_non_compliant_count = collectors.collect_config_non_compliant_count(
        config, conformance_pack_name
    )
    security_hub_failed_count = collectors.collect_security_hub_failed_count(securityhub)
    cloudtrail_event_count = collectors.collect_cloudtrail_event_count(cloudtrail)
    guardduty_counts = collectors.collect_guardduty_findings_by_severity(guardduty, detector_id)

    timestamp = datetime.datetime.now(datetime.timezone.utc)
    publisher.publish_metrics(
        cloudwatch,
        config_non_compliant_count=config_non_compliant_count,
        security_hub_failed_count=security_hub_failed_count,
        guardduty_counts_by_severity=guardduty_counts,
        cloudtrail_event_count=cloudtrail_event_count,
        timestamp=timestamp,
    )

    return {
        "namespace": publisher.NAMESPACE,
        "config_non_compliant_count": config_non_compliant_count,
        "security_hub_failed_count": security_hub_failed_count,
        "guardduty_counts_by_severity": guardduty_counts,
        "cloudtrail_event_count": cloudtrail_event_count,
    }
