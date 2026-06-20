"""Approval-gated remediation actions for findings produced by scanner.py.

Safety rules, enforced in code rather than left as a convention:
  - Every action requires `approved=True` from the caller. There is no default-on path.
  - Every action re-validates `finding.in_scope_for_remediation` and refuses (raises
    ScopeError) to act on anything outside this project, even if a caller passes in a
    finding that was somehow constructed with that flag set incorrectly.
  - Every action is dry-run by default at the CLI layer (see cli.py) - approval has to
    be requested explicitly per run, never assumed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .scanner import ADMIN_POLICY_ARN, Finding


class ScopeError(Exception):
    """Raised when a remediation action is attempted on an out-of-scope resource."""


@dataclass
class RemediationResult:
    finding: Finding
    action: str
    applied: bool
    detail: str


def _require_in_scope(finding: Finding) -> None:
    if not finding.in_scope_for_remediation:
        raise ScopeError(
            f"Refusing to remediate {finding.resource_type}:{finding.resource_id} - "
            "not in scope for this project."
        )


def remediate_admin_access(iam, finding: Finding, approved: bool) -> RemediationResult:
    """Detaches AdministratorAccess from a user or role with it directly attached."""
    if finding.check != "iam_admin_access_attached":
        raise ValueError(f"Not an admin-access finding: {finding.check}")
    _require_in_scope(finding)

    if not approved:
        return RemediationResult(
            finding=finding,
            action="detach_administrator_access",
            applied=False,
            detail="Dry run - would detach AdministratorAccess. Pass approved=True to apply.",
        )

    if finding.resource_type == "user":
        iam.detach_user_policy(UserName=finding.resource_id, PolicyArn=ADMIN_POLICY_ARN)
    elif finding.resource_type == "role":
        iam.detach_role_policy(RoleName=finding.resource_id, PolicyArn=ADMIN_POLICY_ARN)
    else:
        raise ValueError(f"Unsupported resource type for this action: {finding.resource_type}")

    return RemediationResult(
        finding=finding,
        action="detach_administrator_access",
        applied=True,
        detail=f"Detached AdministratorAccess from {finding.resource_type} {finding.resource_id}.",
    )


def remediate_stale_access_key(iam, finding: Finding, approved: bool) -> RemediationResult:
    """Deactivates (not deletes) an access key flagged as too old. Deactivation is
    reversible via the AWS console/CLI if it turns out to be a false positive;
    deletion is not, so this action never deletes a key.
    """
    if finding.check != "iam_access_key_too_old":
        raise ValueError(f"Not a stale-access-key finding: {finding.check}")
    _require_in_scope(finding)

    user_name = finding.resource_arn.rsplit("/", maxsplit=1)[-1]

    if not approved:
        return RemediationResult(
            finding=finding,
            action="deactivate_access_key",
            applied=False,
            detail="Dry run - would deactivate this access key. Pass approved=True to apply.",
        )

    iam.update_access_key(
        UserName=user_name,
        AccessKeyId=finding.resource_id,
        Status="Inactive",
    )
    return RemediationResult(
        finding=finding,
        action="deactivate_access_key",
        applied=True,
        detail=f"Deactivated access key {finding.resource_id} for user {user_name}.",
    )


REMEDIATORS = {
    "iam_admin_access_attached": remediate_admin_access,
    "iam_access_key_too_old": remediate_stale_access_key,
}


def remediate(iam, finding: Finding, approved: bool) -> RemediationResult:
    remediator = REMEDIATORS.get(finding.check)
    if remediator is None:
        raise ValueError(f"No remediation action defined for check: {finding.check}")
    return remediator(iam, finding, approved)
