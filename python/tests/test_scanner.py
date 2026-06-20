import datetime

import boto3
import pytest
from moto import mock_aws

from phase4_iam_governance.scanner import (
    ADMIN_POLICY_ARN,
    scan_access_keys,
    scan_admin_access,
    scan_mfa,
    scan_unused_roles,
)

NAME_PREFIX = "cloud-compliance-platform"


@pytest.fixture
def iam():
    with mock_aws():
        yield boto3.client("iam", region_name="eu-west-2")


def test_scan_mfa_flags_console_user_without_mfa(iam):
    iam.create_user(UserName=f"{NAME_PREFIX}-no-mfa")
    iam.create_login_profile(UserName=f"{NAME_PREFIX}-no-mfa", Password="x-Aa1!2345678")

    findings = scan_mfa(iam, NAME_PREFIX)

    assert len(findings) == 1
    assert findings[0].check == "iam_user_console_no_mfa"
    assert findings[0].resource_id == f"{NAME_PREFIX}-no-mfa"
    assert findings[0].in_scope_for_remediation is True


def test_scan_mfa_ignores_api_only_user(iam):
    iam.create_user(UserName=f"{NAME_PREFIX}-api-only")

    findings = scan_mfa(iam, NAME_PREFIX)

    assert findings == []


def test_scan_mfa_ignores_user_with_mfa_enrolled(iam):
    user_name = f"{NAME_PREFIX}-has-mfa"
    iam.create_user(UserName=user_name)
    iam.create_login_profile(UserName=user_name, Password="x-Aa1!2345678")
    device = iam.create_virtual_mfa_device(VirtualMFADeviceName="device1")["VirtualMFADevice"]
    iam.enable_mfa_device(
        UserName=user_name,
        SerialNumber=device["SerialNumber"],
        AuthenticationCode1="123456",
        AuthenticationCode2="123456",
    )

    findings = scan_mfa(iam, NAME_PREFIX)

    assert findings == []


def test_scan_access_keys_flags_old_active_key(iam):
    user_name = f"{NAME_PREFIX}-old-key"
    iam.create_user(UserName=user_name)
    key = iam.create_access_key(UserName=user_name)["AccessKey"]

    # moto creates keys with CreateDate=now; simulate age by lowering the threshold
    # instead of mutating internal state.
    findings = scan_access_keys(iam, NAME_PREFIX, max_age_days=-1)

    assert len(findings) == 1
    assert findings[0].check == "iam_access_key_too_old"
    assert findings[0].resource_id == key["AccessKeyId"]
    assert findings[0].in_scope_for_remediation is True


def test_scan_access_keys_ignores_inactive_key(iam):
    user_name = f"{NAME_PREFIX}-inactive-key"
    iam.create_user(UserName=user_name)
    key = iam.create_access_key(UserName=user_name)["AccessKey"]
    iam.update_access_key(
        UserName=user_name, AccessKeyId=key["AccessKeyId"], Status="Inactive"
    )

    findings = scan_access_keys(iam, NAME_PREFIX, max_age_days=-1)

    assert findings == []


def test_scan_admin_access_flags_direct_user_attachment(iam):
    user_name = f"{NAME_PREFIX}-legacy-admin"
    iam.create_user(UserName=user_name)
    iam.attach_user_policy(UserName=user_name, PolicyArn=ADMIN_POLICY_ARN)

    findings = scan_admin_access(iam, NAME_PREFIX)

    assert len(findings) == 1
    assert findings[0].check == "iam_admin_access_attached"
    assert findings[0].resource_type == "user"
    assert findings[0].resource_id == user_name
    assert findings[0].in_scope_for_remediation is True


def test_scan_admin_access_marks_out_of_scope_resources(iam):
    iam.create_user(UserName="someone-elses-admin")
    iam.attach_user_policy(UserName="someone-elses-admin", PolicyArn=ADMIN_POLICY_ARN)

    findings = scan_admin_access(iam, NAME_PREFIX)

    assert len(findings) == 1
    assert findings[0].in_scope_for_remediation is False


def test_scan_admin_access_ignores_users_without_it(iam):
    iam.create_user(UserName=f"{NAME_PREFIX}-normal-user")

    findings = scan_admin_access(iam, NAME_PREFIX)

    assert findings == []


def test_scan_unused_roles_flags_never_used_role(iam):
    trust_policy = (
        '{"Version":"2012-10-17","Statement":[{"Effect":"Allow",'
        '"Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
    )
    role_name = f"{NAME_PREFIX}-stale-role"
    iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=trust_policy)

    findings = scan_unused_roles(iam, NAME_PREFIX, max_unused_days=-1)

    assert len(findings) == 1
    assert findings[0].check == "iam_role_unused"
    assert findings[0].resource_id == role_name


def test_scan_unused_roles_ignores_service_linked_roles(iam):
    trust_policy = (
        '{"Version":"2012-10-17","Statement":[{"Effect":"Allow",'
        '"Principal":{"Service":"guardduty.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
    )
    iam.create_role(
        RoleName="AWSServiceRoleForAmazonGuardDuty",
        Path="/aws-service-role/guardduty.amazonaws.com/",
        AssumeRolePolicyDocument=trust_policy,
    )

    findings = scan_unused_roles(iam, NAME_PREFIX, max_unused_days=-1)

    assert findings == []
