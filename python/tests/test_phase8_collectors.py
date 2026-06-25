"""GuardDuty's get_findings_statistics keys CountBySeverity by score string
("2.0", "7.5", etc.), not a bucket label - verified against the live account.
MagicMock is used throughout, for the same reason as Phase 5: moto has no
GuardDuty get_findings_statistics implementation, and its Security Hub
get_findings doesn't apply Filters server-side (see phase5's test_collectors.py),
so a moto test here would give false confidence about request shaping.
"""

import datetime
from unittest.mock import MagicMock

from phase8_grc_metrics.collectors import (
    collect_cloudtrail_event_count,
    collect_config_non_compliant_count,
    collect_guardduty_findings_by_severity,
    collect_security_hub_failed_count,
)


def test_collect_guardduty_findings_by_severity_buckets_scores():
    guardduty = MagicMock()
    guardduty.get_findings_statistics.return_value = {
        "FindingStatistics": {
            "CountBySeverity": {"2.0": 3, "5.5": 1, "8.0": 2, "3.9": 1}
        }
    }

    result = collect_guardduty_findings_by_severity(guardduty, "detector-1")

    assert result == {"Low": 4, "Medium": 1, "High": 2}
    call_kwargs = guardduty.get_findings_statistics.call_args.kwargs
    assert call_kwargs["DetectorId"] == "detector-1"
    assert call_kwargs["FindingCriteria"] == {"Criterion": {"service.archived": {"Eq": ["false"]}}}


def test_collect_guardduty_findings_by_severity_no_findings():
    guardduty = MagicMock()
    guardduty.get_findings_statistics.return_value = {"FindingStatistics": {"CountBySeverity": {}}}

    result = collect_guardduty_findings_by_severity(guardduty, "detector-1")

    assert result == {"Low": 0, "Medium": 0, "High": 0}


def test_collect_config_non_compliant_count_paginates():
    config = MagicMock()
    config.get_conformance_pack_compliance_details.side_effect = [
        {"ConformancePackRuleEvaluationResults": [{}], "NextToken": "page2"},
        {"ConformancePackRuleEvaluationResults": [{}, {}]},
    ]

    result = collect_config_non_compliant_count(config, "my-pack")

    assert result == 3
    assert config.get_conformance_pack_compliance_details.call_count == 2


def test_collect_security_hub_failed_count_builds_correct_filter():
    securityhub = MagicMock()
    securityhub.get_findings.return_value = {"Findings": [{}, {}]}

    result = collect_security_hub_failed_count(securityhub, max_results=50)

    assert result == 2
    call_kwargs = securityhub.get_findings.call_args.kwargs
    assert call_kwargs["Filters"]["ComplianceStatus"] == [{"Value": "FAILED", "Comparison": "EQUALS"}]
    assert call_kwargs["Filters"]["RecordState"] == [{"Value": "ACTIVE", "Comparison": "EQUALS"}]
    assert call_kwargs["MaxResults"] == 50


def test_collect_cloudtrail_event_count():
    cloudtrail = MagicMock()
    cloudtrail.lookup_events.return_value = {
        "Events": [
            {"EventName": "ConsoleLogin", "EventTime": datetime.datetime(2026, 6, 20), "Username": "alice"}
        ]
    }

    result = collect_cloudtrail_event_count(cloudtrail)

    assert result == 1
