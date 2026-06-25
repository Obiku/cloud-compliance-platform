"""Publishes the reduced GRC numbers to CloudWatch as custom metrics, since none
of GuardDuty/Config/Security Hub/CloudTrail publish finding-level or compliance-
level data to CloudWatch natively (verified against the live account before
writing this - their AWS/* namespaces only carry operational metrics like
AnalyzedBytes or ConfigurationRecorderInsufficientPermissionsFailure).
"""

from __future__ import annotations

import datetime

NAMESPACE = "CloudCompliancePlatform/GRC"


def publish_metrics(
    cloudwatch,
    *,
    config_non_compliant_count: int,
    security_hub_failed_count: int,
    guardduty_counts_by_severity: dict[str, int],
    cloudtrail_event_count: int,
    timestamp: datetime.datetime,
) -> None:
    metric_data = [
        {
            "MetricName": "ConfigNonCompliantCount",
            "Timestamp": timestamp,
            "Value": config_non_compliant_count,
            "Unit": "Count",
        },
        {
            "MetricName": "SecurityHubFailedFindingsCount",
            "Timestamp": timestamp,
            "Value": security_hub_failed_count,
            "Unit": "Count",
        },
        {
            "MetricName": "CloudTrailEventVolume",
            "Timestamp": timestamp,
            "Value": cloudtrail_event_count,
            "Unit": "Count",
        },
    ]
    for severity, count in guardduty_counts_by_severity.items():
        metric_data.append(
            {
                "MetricName": "GuardDutyFindingsBySeverity",
                "Dimensions": [{"Name": "Severity", "Value": severity}],
                "Timestamp": timestamp,
                "Value": count,
                "Unit": "Count",
            }
        )

    # put_metric_data accepts at most 1000 data points per call - never close to
    # that here, but documenting why no batching loop exists.
    cloudwatch.put_metric_data(Namespace=NAMESPACE, MetricData=metric_data)
