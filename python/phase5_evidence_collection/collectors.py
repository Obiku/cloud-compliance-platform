"""Read-only evidence collectors. Each function takes an already-constructed boto3
client and returns a JSON-serializable snapshot - no mutating calls anywhere here.
"""

from __future__ import annotations

import datetime
from typing import Any


def collect_config_compliance(config, conformance_pack_name: str) -> dict[str, Any]:
    """AWS Config conformance pack compliance: overall status plus every
    NON_COMPLIANT rule/resource pair currently recorded against it.
    """
    summary = config.get_conformance_pack_compliance_summary(
        ConformancePackNames=[conformance_pack_name]
    )["ConformancePackComplianceSummaryList"]
    overall_status = summary[0]["ConformancePackComplianceStatus"] if summary else "UNKNOWN"

    non_compliant: list[dict[str, Any]] = []
    next_token = None
    while True:
        kwargs: dict[str, Any] = {
            "ConformancePackName": conformance_pack_name,
            "Filters": {"ComplianceType": "NON_COMPLIANT"},
        }
        if next_token:
            kwargs["NextToken"] = next_token
        page = config.get_conformance_pack_compliance_details(**kwargs)
        for result in page.get("ConformancePackRuleEvaluationResults", []):
            qualifier = result["EvaluationResultIdentifier"]["EvaluationResultQualifier"]
            non_compliant.append(
                {
                    "config_rule_name": qualifier["ConfigRuleName"],
                    "resource_type": qualifier["ResourceType"],
                    "resource_id": qualifier["ResourceId"],
                    "result_recorded_time": result["ResultRecordedTime"],
                }
            )
        next_token = page.get("NextToken")
        if not next_token:
            break

    return {
        "conformance_pack_name": conformance_pack_name,
        "overall_status": overall_status,
        "non_compliant_count": len(non_compliant),
        "non_compliant": non_compliant,
    }


def collect_security_hub_findings(securityhub, max_results: int = 100) -> dict[str, Any]:
    """Security Hub findings currently FAILED and RecordState ACTIVE - the set a
    reviewer would actually need to act on, not the full noisy history.
    """
    findings: list[dict[str, Any]] = []
    next_token = None
    while True:
        kwargs: dict[str, Any] = {
            "Filters": {
                "ComplianceStatus": [{"Value": "FAILED", "Comparison": "EQUALS"}],
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
            },
            "MaxResults": max_results,
        }
        if next_token:
            kwargs["NextToken"] = next_token
        page = securityhub.get_findings(**kwargs)
        for finding in page.get("Findings", []):
            resource = finding.get("Resources", [{}])[0]
            findings.append(
                {
                    "title": finding.get("Title"),
                    "severity": finding.get("Severity", {}).get("Label"),
                    "resource_id": resource.get("Id"),
                    "resource_type": resource.get("Type"),
                }
            )
        next_token = page.get("NextToken")
        if not next_token:
            break

    return {
        "failed_finding_count": len(findings),
        "findings": findings,
    }


def collect_cloudtrail_sample(
    cloudtrail, trail_name: str, lookback_hours: int = 24, max_events: int = 50
) -> dict[str, Any]:
    """CloudTrail trail status, plus a sample of recent management events as
    evidence that logging is actually flowing, not just "enabled".
    """
    trail = cloudtrail.describe_trails(trailNameList=[trail_name])["trailList"]
    trail_info = trail[0] if trail else {}
    status = cloudtrail.get_trail_status(Name=trail_name)

    now = datetime.datetime.now(datetime.timezone.utc)
    start_time = now - datetime.timedelta(hours=lookback_hours)
    events_page = cloudtrail.lookup_events(
        StartTime=start_time,
        EndTime=now,
        MaxResults=max_events,
    )
    events = [
        {
            "event_name": e["EventName"],
            "event_time": e["EventTime"],
            "username": e.get("Username"),
        }
        for e in events_page.get("Events", [])
    ]

    return {
        "trail_name": trail_name,
        "is_multi_region": trail_info.get("IsMultiRegionTrail"),
        "is_logging": status.get("IsLogging"),
        "latest_delivery_time": status.get("LatestDeliveryTime"),
        "sample_event_count": len(events),
        "sample_events": events,
    }
