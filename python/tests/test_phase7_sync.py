"""Tests use a MagicMock ServiceNowClient rather than hitting a real instance -
the real API was verified by hand against the dev397101 PDI (see
docs/phase7_servicenow_integration.md). These tests verify the request shaping,
deduplication logic, and indicator math.
"""

from unittest.mock import MagicMock

from phase7_servicenow_integration.evidence import LatestEvidence
from phase7_servicenow_integration.mapping import ResolvedControl
from phase7_servicenow_integration.sync import push_security_hub_issues, update_compliance_assessment

CONTROL = ResolvedControl(sys_id="ctrl-sys-id", number="CTRL0020196", name="CC7.1 Detection of security events")


def _evidence(snapshot):
    return LatestEvidence(key="evidence/x/snapshot.json", s3_uri="s3://bucket/evidence/x/snapshot.json", snapshot=snapshot)


def test_push_security_hub_issues_creates_one_issue_per_new_finding():
    snow = MagicMock()
    snow.query.return_value = []  # no existing issue for any correlation_id
    snow.create.side_effect = [{"number": "IPT0030001"}, {"number": "IPT0030002"}]
    evidence = _evidence(
        {
            "findings": [
                {"title": "MFA not enabled", "severity": "HIGH", "resource_type": "AWS::IAM::User", "resource_id": "user-1"},
                {"title": "Bucket not encrypted", "severity": "MEDIUM", "resource_type": "AWS::S3::Bucket", "resource_id": "bucket-1"},
            ]
        }
    )

    result = push_security_hub_issues(snow, "profile-sys-id", CONTROL, evidence)

    assert result["issues_created"] == ["IPT0030001", "IPT0030002"]
    assert result["issues_already_existed"] == []
    assert snow.create.call_count == 2
    first_payload = snow.create.call_args_list[0].args[1]
    assert first_payload["profile"] == "profile-sys-id"
    assert first_payload["correlation_id"].startswith("aws-securityhub:")
    assert len(first_payload["correlation_id"]) < 60
    assert "CTRL0020196" in first_payload["short_description"]
    assert evidence.s3_uri in first_payload["description"]


def test_push_security_hub_issues_skips_findings_already_pushed():
    snow = MagicMock()
    snow.query.return_value = [{"number": "IPT0030001"}]  # already exists
    evidence = _evidence(
        {"findings": [{"title": "MFA not enabled", "severity": "HIGH", "resource_type": "AWS::IAM::User", "resource_id": "user-1"}]}
    )

    result = push_security_hub_issues(snow, "profile-sys-id", CONTROL, evidence)

    assert result["issues_created"] == []
    assert result["issues_already_existed"] == ["IPT0030001"]
    snow.create.assert_not_called()


def test_push_security_hub_issues_caps_at_max_per_run():
    snow = MagicMock()
    snow.query.return_value = []
    snow.create.side_effect = [{"number": f"IPT003000{i}"} for i in range(10)]
    findings = [
        {"title": f"Finding {i}", "severity": "LOW", "resource_type": "AWS::S3::Bucket", "resource_id": f"bucket-{i}"}
        for i in range(10)
    ]

    result = push_security_hub_issues(snow, "profile-sys-id", CONTROL, _evidence({"findings": findings}))

    assert len(result["issues_created"]) == 5


def test_update_compliance_assessment_non_compliant():
    snow = MagicMock()
    evidence = _evidence({"overall_status": "NON_COMPLIANT", "non_compliant_count": 7})

    result = update_compliance_assessment(snow, CONTROL, evidence)

    assert result == {
        "control": "CTRL0020196",
        "evidence_uri": evidence.s3_uri,
        "failed_indicators": 7,
        "passed_indicators": 0,
    }
    snow.update.assert_called_once()
    table, sys_id, payload = snow.update.call_args.args
    assert table == "sn_compliance_control"
    assert sys_id == "ctrl-sys-id"
    assert payload["failed_indicators"] == 7
    assert payload["passed_indicators"] == 0
    assert evidence.s3_uri in payload["comments"]


def test_update_compliance_assessment_fully_compliant():
    snow = MagicMock()
    evidence = _evidence({"overall_status": "COMPLIANT", "non_compliant_count": 0})

    result = update_compliance_assessment(snow, CONTROL, evidence)

    assert result["failed_indicators"] == 0
    assert result["passed_indicators"] == 1
