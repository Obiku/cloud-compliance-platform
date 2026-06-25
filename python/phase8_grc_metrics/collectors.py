"""Read-only collectors returning just the counts this dashboard plots - not
full evidence snapshots like Phase 5's collectors, since this Lambda is
packaged and deployed independently of phase5_evidence_collection (each
phaseN_* package is zipped on its own, so it can't import another phase's
package at runtime even though it would resolve fine locally).

Severity buckets follow GuardDuty's own published scale: Low 0.1-3.9, Medium
4.0-6.9, High 7.0-8.9 - https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_findings-severity.html
"""

from __future__ import annotations

import datetime

SEVERITY_BUCKETS = ("Low", "Medium", "High")


def _severity_bucket(score: float) -> str:
    if score < 4.0:
        return "Low"
    if score < 7.0:
        return "Medium"
    return "High"


def collect_guardduty_findings_by_severity(guardduty, detector_id: str) -> dict[str, int]:
    """Active (unarchived) GuardDuty findings, bucketed into Low/Medium/High."""
    stats = guardduty.get_findings_statistics(
        DetectorId=detector_id,
        FindingStatisticTypes=["COUNT_BY_SEVERITY"],
        FindingCriteria={"Criterion": {"service.archived": {"Eq": ["false"]}}},
    )
    counts = dict.fromkeys(SEVERITY_BUCKETS, 0)
    for score_str, count in stats["FindingStatistics"]["CountBySeverity"].items():
        counts[_severity_bucket(float(score_str))] += int(count)
    return counts


def collect_config_non_compliant_count(config, conformance_pack_name: str) -> int:
    """Count of NON_COMPLIANT rule/resource pairs in the conformance pack -
    same source Phase 5's collect_config_compliance reads, paginated the same way.
    """
    count = 0
    next_token = None
    while True:
        kwargs: dict = {
            "ConformancePackName": conformance_pack_name,
            "Filters": {"ComplianceType": "NON_COMPLIANT"},
        }
        if next_token:
            kwargs["NextToken"] = next_token
        page = config.get_conformance_pack_compliance_details(**kwargs)
        count += len(page.get("ConformancePackRuleEvaluationResults", []))
        next_token = page.get("NextToken")
        if not next_token:
            break
    return count


def collect_security_hub_failed_count(securityhub, max_results: int = 100) -> int:
    """Count of active FAILED findings - same filter Phase 5's
    collect_security_hub_findings uses.
    """
    count = 0
    next_token = None
    while True:
        kwargs: dict = {
            "Filters": {
                "ComplianceStatus": [{"Value": "FAILED", "Comparison": "EQUALS"}],
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
            },
            "MaxResults": max_results,
        }
        if next_token:
            kwargs["NextToken"] = next_token
        page = securityhub.get_findings(**kwargs)
        count += len(page.get("Findings", []))
        next_token = page.get("NextToken")
        if not next_token:
            break
    return count


def collect_cloudtrail_event_count(
    cloudtrail, lookback_hours: int = 24, max_events: int = 50
) -> int:
    """Sampled management-event count in the lookback window - a volume trend
    indicator, not an exact total (lookup_events is capped at max_events, the
    same limitation Phase 5 documented for its own CloudTrail collector).
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    start_time = now - datetime.timedelta(hours=lookback_hours)
    events_page = cloudtrail.lookup_events(
        StartTime=start_time, EndTime=now, MaxResults=max_events
    )
    return len(events_page.get("Events", []))
