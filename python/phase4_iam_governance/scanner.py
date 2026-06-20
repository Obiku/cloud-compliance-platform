"""Read-only IAM governance scan: MFA gaps, stale access keys, unused roles,
and AdministratorAccess grants. Safe to run against any account - makes no
mutating API calls.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

ADMIN_POLICY_ARN = "arn:aws:iam::aws:policy/AdministratorAccess"


@dataclass
class Finding:
    check: str
    severity: str
    resource_type: str
    resource_id: str
    resource_arn: str
    detail: str
    in_scope_for_remediation: bool


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _is_in_scope(name: str, tags: dict[str, str], name_prefix: str) -> bool:
    """Remediation only ever targets resources this project owns: name-prefixed or
    tagged Project=<name_prefix>. Everything else is reported but never touched.
    """
    if name.startswith(f"{name_prefix}-"):
        return True
    return tags.get("Project") == name_prefix


def _list_user_tags(iam, user_name: str) -> dict[str, str]:
    tags = iam.list_user_tags(UserName=user_name)["Tags"]
    return {t["Key"]: t["Value"] for t in tags}


def _list_role_tags(iam, role_name: str) -> dict[str, str]:
    tags = iam.list_role_tags(RoleName=role_name)["Tags"]
    return {t["Key"]: t["Value"] for t in tags}


def scan_mfa(iam, name_prefix: str) -> list[Finding]:
    """Flags console-enabled IAM users with no MFA device enrolled. Users with no
    login profile (API/programmatic-only) are not flagged - MFA protects console
    sign-in, not access keys.
    """
    findings = []
    paginator = iam.get_paginator("list_users")
    for page in paginator.paginate():
        for user in page["Users"]:
            user_name = user["UserName"]
            try:
                iam.get_login_profile(UserName=user_name)
            except iam.exceptions.NoSuchEntityException:
                continue

            mfa_devices = iam.list_mfa_devices(UserName=user_name)["MFADevices"]
            if mfa_devices:
                continue

            tags = _list_user_tags(iam, user_name)
            findings.append(
                Finding(
                    check="iam_user_console_no_mfa",
                    severity="HIGH",
                    resource_type="user",
                    resource_id=user_name,
                    resource_arn=user["Arn"],
                    detail="Console login enabled with no MFA device enrolled.",
                    in_scope_for_remediation=_is_in_scope(user_name, tags, name_prefix),
                )
            )
    return findings


def scan_access_keys(iam, name_prefix: str, max_age_days: int = 90) -> list[Finding]:
    """Flags active access keys older than max_age_days."""
    findings = []
    now = _utcnow()
    paginator = iam.get_paginator("list_users")
    for page in paginator.paginate():
        for user in page["Users"]:
            user_name = user["UserName"]
            keys = iam.list_access_keys(UserName=user_name)["AccessKeyMetadata"]
            for key in keys:
                if key["Status"] != "Active":
                    continue
                age_days = (now - key["CreateDate"]).days
                if age_days <= max_age_days:
                    continue
                tags = _list_user_tags(iam, user_name)
                findings.append(
                    Finding(
                        check="iam_access_key_too_old",
                        severity="MEDIUM",
                        resource_type="access_key",
                        resource_id=key["AccessKeyId"],
                        resource_arn=user["Arn"],
                        detail=f"Active access key is {age_days} days old (limit {max_age_days}).",
                        in_scope_for_remediation=_is_in_scope(user_name, tags, name_prefix),
                    )
                )
    return findings


def scan_unused_roles(iam, name_prefix: str, max_unused_days: int = 90) -> list[Finding]:
    """Flags roles never used, or not used in over max_unused_days. Service-linked
    roles are excluded - they're managed by AWS, not candidates for remediation.
    """
    findings = []
    now = _utcnow()
    paginator = iam.get_paginator("list_roles")
    for page in paginator.paginate():
        for role in page["Roles"]:
            if role["Path"].startswith("/aws-service-role/"):
                continue
            role_name = role["RoleName"]
            last_used = role.get("RoleLastUsed", {}).get("LastUsedDate")
            created = role["CreateDate"]
            reference_date = last_used or created
            age_days = (now - reference_date).days
            if age_days <= max_unused_days:
                continue

            tags = _list_role_tags(iam, role_name)
            state = "never used" if last_used is None else f"last used {age_days} days ago"
            findings.append(
                Finding(
                    check="iam_role_unused",
                    severity="LOW",
                    resource_type="role",
                    resource_id=role_name,
                    resource_arn=role["Arn"],
                    detail=f"Role {state} (created {created.date().isoformat()}).",
                    in_scope_for_remediation=_is_in_scope(role_name, tags, name_prefix),
                )
            )
    return findings


def scan_admin_access(iam, name_prefix: str) -> list[Finding]:
    """Flags IAM users and roles with AdministratorAccess attached directly
    (not via a group - direct attachment to a user/role is the excessive-privilege
    pattern this check targets).
    """
    findings = []

    paginator = iam.get_paginator("list_users")
    for page in paginator.paginate():
        for user in page["Users"]:
            user_name = user["UserName"]
            attached = iam.list_attached_user_policies(UserName=user_name)["AttachedPolicies"]
            if not any(p["PolicyArn"] == ADMIN_POLICY_ARN for p in attached):
                continue
            tags = _list_user_tags(iam, user_name)
            findings.append(
                Finding(
                    check="iam_admin_access_attached",
                    severity="HIGH",
                    resource_type="user",
                    resource_id=user_name,
                    resource_arn=user["Arn"],
                    detail="AdministratorAccess is attached directly to this user.",
                    in_scope_for_remediation=_is_in_scope(user_name, tags, name_prefix),
                )
            )

    role_paginator = iam.get_paginator("list_roles")
    for page in role_paginator.paginate():
        for role in page["Roles"]:
            if role["Path"].startswith("/aws-service-role/"):
                continue
            role_name = role["RoleName"]
            attached = iam.list_attached_role_policies(RoleName=role_name)["AttachedPolicies"]
            if not any(p["PolicyArn"] == ADMIN_POLICY_ARN for p in attached):
                continue
            tags = _list_role_tags(iam, role_name)
            findings.append(
                Finding(
                    check="iam_admin_access_attached",
                    severity="HIGH",
                    resource_type="role",
                    resource_id=role_name,
                    resource_arn=role["Arn"],
                    detail="AdministratorAccess is attached directly to this role.",
                    in_scope_for_remediation=_is_in_scope(role_name, tags, name_prefix),
                )
            )
    return findings


def run_full_scan(iam, name_prefix: str) -> list[Finding]:
    findings: list[Finding] = []
    findings += scan_mfa(iam, name_prefix)
    findings += scan_access_keys(iam, name_prefix)
    findings += scan_unused_roles(iam, name_prefix)
    findings += scan_admin_access(iam, name_prefix)
    return findings
