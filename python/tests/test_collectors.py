"""Tests use MagicMock clients, not moto, for Config/Security Hub/CloudTrail.

moto's Security Hub get_findings does not actually apply the Filters parameter
server-side (confirmed by hand: importing FAILED/PASSED/ACTIVE/ARCHIVED findings
and calling get_findings with Filters still returns all of them) and moto has no
implementation at all for the conformance pack compliance or lookup_events APIs.
A moto-based test here would give false confidence about request shaping. MagicMock
verifies these collectors build the right request and parse the response shape
correctly; the request itself was verified against the real account by hand (see
docs/phase5_evidence_collection.md).
"""

import datetime
from unittest.mock import MagicMock

from phase5_evidence_collection.collectors import (
    collect_cloudtrail_sample,
    collect_config_compliance,
    collect_security_hub_findings,
)


def test_collect_config_compliance_single_page():
    config = MagicMock()
    config.get_conformance_pack_compliance_summary.return_value = {
        "ConformancePackComplianceSummaryList": [
            {"ConformancePackName": "my-pack", "ConformancePackComplianceStatus": "NON_COMPLIANT"}
        ]
    }
    config.get_conformance_pack_compliance_details.return_value = {
        "ConformancePackRuleEvaluationResults": [
            {
                "ComplianceType": "NON_COMPLIANT",
                "EvaluationResultIdentifier": {
                    "EvaluationResultQualifier": {
                        "ConfigRuleName": "rule-a",
                        "ResourceType": "AWS::IAM::User",
                        "ResourceId": "user-1",
                    }
                },
                "ResultRecordedTime": datetime.datetime(2026, 6, 20, tzinfo=datetime.timezone.utc),
            }
        ]
        # no NextToken -> single page
    }

    result = collect_config_compliance(config, "my-pack")

    assert result["overall_status"] == "NON_COMPLIANT"
    assert result["non_compliant_count"] == 1
    assert result["non_compliant"][0]["config_rule_name"] == "rule-a"
    config.get_conformance_pack_compliance_details.assert_called_once()
    call_kwargs = config.get_conformance_pack_compliance_details.call_args.kwargs
    assert call_kwargs["ConformancePackName"] == "my-pack"
    assert call_kwargs["Filters"] == {"ComplianceType": "NON_COMPLIANT"}


def test_collect_config_compliance_paginates():
    config = MagicMock()
    config.get_conformance_pack_compliance_summary.return_value = {
        "ConformancePackComplianceSummaryList": [
            {"ConformancePackName": "my-pack", "ConformancePackComplianceStatus": "NON_COMPLIANT"}
        ]
    }
    config.get_conformance_pack_compliance_details.side_effect = [
        {
            "ConformancePackRuleEvaluationResults": [
                {
                    "ComplianceType": "NON_COMPLIANT",
                    "EvaluationResultIdentifier": {
                        "EvaluationResultQualifier": {
                            "ConfigRuleName": "rule-a",
                            "ResourceType": "AWS::IAM::User",
                            "ResourceId": "user-1",
                        }
                    },
                    "ResultRecordedTime": "2026-06-20T00:00:00Z",
                }
            ],
            "NextToken": "page2",
        },
        {
            "ConformancePackRuleEvaluationResults": [
                {
                    "ComplianceType": "NON_COMPLIANT",
                    "EvaluationResultIdentifier": {
                        "EvaluationResultQualifier": {
                            "ConfigRuleName": "rule-b",
                            "ResourceType": "AWS::S3::Bucket",
                            "ResourceId": "bucket-1",
                        }
                    },
                    "ResultRecordedTime": "2026-06-20T01:00:00Z",
                }
            ],
        },
    ]

    result = collect_config_compliance(config, "my-pack")

    assert result["non_compliant_count"] == 2
    assert config.get_conformance_pack_compliance_details.call_count == 2
    second_call_kwargs = config.get_conformance_pack_compliance_details.call_args_list[1].kwargs
    assert second_call_kwargs["NextToken"] == "page2"


def test_collect_config_compliance_no_summary_returns_unknown():
    config = MagicMock()
    config.get_conformance_pack_compliance_summary.return_value = {
        "ConformancePackComplianceSummaryList": []
    }
    config.get_conformance_pack_compliance_details.return_value = {
        "ConformancePackRuleEvaluationResults": []
    }

    result = collect_config_compliance(config, "my-pack")

    assert result["overall_status"] == "UNKNOWN"
    assert result["non_compliant_count"] == 0


def test_collect_security_hub_findings_builds_correct_filter_and_parses():
    securityhub = MagicMock()
    securityhub.get_findings.return_value = {
        "Findings": [
            {
                "Title": "IAM users should not have IAM policies attached",
                "Severity": {"Label": "HIGH"},
                "Resources": [{"Id": "arn:aws:iam::123456789012:user/legacy-admin", "Type": "AwsIamUser"}],
            }
        ]
    }

    result = collect_security_hub_findings(securityhub, max_results=50)

    assert result["failed_finding_count"] == 1
    assert result["findings"][0]["resource_id"] == "arn:aws:iam::123456789012:user/legacy-admin"
    call_kwargs = securityhub.get_findings.call_args.kwargs
    assert call_kwargs["Filters"]["ComplianceStatus"] == [{"Value": "FAILED", "Comparison": "EQUALS"}]
    assert call_kwargs["Filters"]["RecordState"] == [{"Value": "ACTIVE", "Comparison": "EQUALS"}]
    assert call_kwargs["MaxResults"] == 50


def test_collect_security_hub_findings_paginates():
    securityhub = MagicMock()
    securityhub.get_findings.side_effect = [
        {"Findings": [{"Title": "a", "Severity": {}, "Resources": [{}]}], "NextToken": "p2"},
        {"Findings": [{"Title": "b", "Severity": {}, "Resources": [{}]}]},
    ]

    result = collect_security_hub_findings(securityhub)

    assert result["failed_finding_count"] == 2
    assert securityhub.get_findings.call_count == 2


def test_collect_cloudtrail_sample_parses_status_and_events():
    cloudtrail = MagicMock()
    cloudtrail.describe_trails.return_value = {
        "trailList": [{"Name": "my-trail", "IsMultiRegionTrail": True}]
    }
    cloudtrail.get_trail_status.return_value = {
        "IsLogging": True,
        "LatestDeliveryTime": datetime.datetime(2026, 6, 20, tzinfo=datetime.timezone.utc),
    }
    cloudtrail.lookup_events.return_value = {
        "Events": [
            {"EventName": "ConsoleLogin", "EventTime": datetime.datetime(2026, 6, 20), "Username": "alice"}
        ]
    }

    result = collect_cloudtrail_sample(cloudtrail, "my-trail")

    assert result["is_multi_region"] is True
    assert result["is_logging"] is True
    assert result["sample_event_count"] == 1
    assert result["sample_events"][0]["event_name"] == "ConsoleLogin"
    cloudtrail.describe_trails.assert_called_once_with(trailNameList=["my-trail"])
    cloudtrail.get_trail_status.assert_called_once_with(Name="my-trail")


def test_collect_cloudtrail_sample_handles_missing_trail():
    cloudtrail = MagicMock()
    cloudtrail.describe_trails.return_value = {"trailList": []}
    cloudtrail.get_trail_status.return_value = {"IsLogging": False}
    cloudtrail.lookup_events.return_value = {"Events": []}

    result = collect_cloudtrail_sample(cloudtrail, "missing-trail")

    assert result["is_multi_region"] is None
    assert result["sample_event_count"] == 0
