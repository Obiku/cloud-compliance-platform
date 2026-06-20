import boto3
import pytest
from moto import mock_aws

from phase4_iam_governance import remediation
from phase4_iam_governance.scanner import (
    ADMIN_POLICY_ARN,
    scan_access_keys,
    scan_admin_access,
)

NAME_PREFIX = "cloud-compliance-platform"


@pytest.fixture
def iam():
    with mock_aws():
        yield boto3.client("iam", region_name="eu-west-2")


def test_remediate_admin_access_dry_run_makes_no_change(iam):
    user_name = f"{NAME_PREFIX}-legacy-admin"
    iam.create_user(UserName=user_name)
    iam.attach_user_policy(UserName=user_name, PolicyArn=ADMIN_POLICY_ARN)

    finding = scan_admin_access(iam, NAME_PREFIX)[0]
    result = remediation.remediate(iam, finding, approved=False)

    assert result.applied is False
    attached = iam.list_attached_user_policies(UserName=user_name)["AttachedPolicies"]
    assert any(p["PolicyArn"] == ADMIN_POLICY_ARN for p in attached)


def test_remediate_admin_access_approved_detaches_policy(iam):
    user_name = f"{NAME_PREFIX}-legacy-admin"
    iam.create_user(UserName=user_name)
    iam.attach_user_policy(UserName=user_name, PolicyArn=ADMIN_POLICY_ARN)

    finding = scan_admin_access(iam, NAME_PREFIX)[0]
    result = remediation.remediate(iam, finding, approved=True)

    assert result.applied is True
    attached = iam.list_attached_user_policies(UserName=user_name)["AttachedPolicies"]
    assert attached == []


def test_remediate_refuses_out_of_scope_resource(iam):
    iam.create_user(UserName="someone-elses-admin")
    iam.attach_user_policy(UserName="someone-elses-admin", PolicyArn=ADMIN_POLICY_ARN)

    finding = scan_admin_access(iam, NAME_PREFIX)[0]
    assert finding.in_scope_for_remediation is False

    with pytest.raises(remediation.ScopeError):
        remediation.remediate(iam, finding, approved=True)

    attached = iam.list_attached_user_policies(UserName="someone-elses-admin")[
        "AttachedPolicies"
    ]
    assert any(p["PolicyArn"] == ADMIN_POLICY_ARN for p in attached)


def test_remediate_stale_access_key_approved_deactivates(iam):
    user_name = f"{NAME_PREFIX}-old-key"
    iam.create_user(UserName=user_name)
    key = iam.create_access_key(UserName=user_name)["AccessKey"]

    finding = scan_access_keys(iam, NAME_PREFIX, max_age_days=-1)[0]
    result = remediation.remediate(iam, finding, approved=True)

    assert result.applied is True
    keys = iam.list_access_keys(UserName=user_name)["AccessKeyMetadata"]
    updated = next(k for k in keys if k["AccessKeyId"] == key["AccessKeyId"])
    assert updated["Status"] == "Inactive"


def test_remediate_unknown_check_raises(iam):
    from phase4_iam_governance.scanner import Finding

    finding = Finding(
        check="not_a_real_check",
        severity="LOW",
        resource_type="user",
        resource_id="x",
        resource_arn="arn:aws:iam::123456789012:user/x",
        detail="",
        in_scope_for_remediation=True,
    )
    with pytest.raises(ValueError):
        remediation.remediate(iam, finding, approved=True)
