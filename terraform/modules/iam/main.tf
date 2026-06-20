# RBAC groups
#
# ComplianceAuditors : read-only access to inspect compliance/security state
# CloudEngineers     : power-user access to build/operate infrastructure
# ComplianceAdmins    : manage the compliance tooling itself (Config, Security Hub,
#                       GuardDuty, CloudTrail, Audit Manager) without broad IAM/account control

resource "aws_iam_group" "compliance_auditors" {
  name = "${var.name_prefix}-compliance-auditors"
}

resource "aws_iam_group_policy_attachment" "compliance_auditors_readonly" {
  group      = aws_iam_group.compliance_auditors.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

resource "aws_iam_group_policy_attachment" "compliance_auditors_security_audit" {
  group      = aws_iam_group.compliance_auditors.name
  policy_arn = "arn:aws:iam::aws:policy/SecurityAudit"
}

resource "aws_iam_group" "cloud_engineers" {
  name = "${var.name_prefix}-cloud-engineers"
}

resource "aws_iam_group_policy_attachment" "cloud_engineers_power_user" {
  group      = aws_iam_group.cloud_engineers.name
  policy_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
}

resource "aws_iam_group" "compliance_admins" {
  name = "${var.name_prefix}-compliance-admins"
}

data "aws_iam_policy_document" "compliance_admin" {
  statement {
    sid = "ManageComplianceTooling"
    actions = [
      "config:*",
      "securityhub:*",
      "guardduty:*",
      "cloudtrail:*",
      "auditmanager:*",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "ReadIamForAssessment"
    actions   = ["iam:Get*", "iam:List*", "iam:GenerateCredentialReport", "iam:GenerateServiceLastAccessedDetails"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "compliance_admin" {
  name   = "${var.name_prefix}-compliance-admin-policy"
  policy = data.aws_iam_policy_document.compliance_admin.json
}

resource "aws_iam_group_policy_attachment" "compliance_admins" {
  group      = aws_iam_group.compliance_admins.name
  policy_arn = aws_iam_policy.compliance_admin.arn
}

# Standard AWS-recommended "deny unless MFA present" template: blocks everything except
# the handful of self-service actions a user needs to sign in and enroll their own MFA
# device, so users can still bootstrap access on first login.
data "aws_iam_policy_document" "require_mfa" {
  statement {
    sid       = "AllowViewAccountInfo"
    effect    = "Allow"
    actions   = ["iam:GetAccountPasswordPolicy", "iam:ListVirtualMFADevices"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowManageOwnPasswordAndMfa"
    effect = "Allow"
    actions = [
      "iam:ChangePassword",
      "iam:GetUser",
      "iam:CreateVirtualMFADevice",
      "iam:EnableMFADevice",
      "iam:ResyncMFADevice",
      "iam:ListMFADevices",
      "iam:DeactivateMFADevice",
      "iam:DeleteVirtualMFADevice",
    ]
    resources = ["arn:aws:iam::*:user/$${aws:username}", "arn:aws:iam::*:mfa/$${aws:username}"]
  }

  statement {
    sid    = "DenyAllExceptListedIfNoMfa"
    effect = "Deny"
    not_actions = [
      "iam:ChangePassword",
      "iam:GetUser",
      "iam:GetAccountPasswordPolicy",
      "iam:ListVirtualMFADevices",
      "iam:ListMFADevices",
      "iam:CreateVirtualMFADevice",
      "iam:EnableMFADevice",
      "iam:ResyncMFADevice",
      "iam:DeactivateMFADevice",
      "iam:DeleteVirtualMFADevice",
      "sts:GetSessionToken",
    ]
    resources = ["*"]

    condition {
      test     = "BoolIfExists"
      variable = "aws:MultiFactorAuthPresent"
      values   = ["false"]
    }
  }
}

resource "aws_iam_policy" "require_mfa" {
  name   = "${var.name_prefix}-require-mfa"
  policy = data.aws_iam_policy_document.require_mfa.json
}

resource "aws_iam_group_policy_attachment" "compliance_auditors_require_mfa" {
  group      = aws_iam_group.compliance_auditors.name
  policy_arn = aws_iam_policy.require_mfa.arn
}

resource "aws_iam_group_policy_attachment" "cloud_engineers_require_mfa" {
  group      = aws_iam_group.cloud_engineers.name
  policy_arn = aws_iam_policy.require_mfa.arn
}

resource "aws_iam_group_policy_attachment" "compliance_admins_require_mfa" {
  group      = aws_iam_group.compliance_admins.name
  policy_arn = aws_iam_policy.require_mfa.arn
}

# --- Phase 1 seeded issue ---
# Intentionally insecure IAM user: AdministratorAccess attached directly, no group
# membership, and no MFA device enrolled. This is detected in Phase 3 (Security Hub /
# Config) and remediated in Phase 4 (IAM governance automation). Do not replicate this
# pattern elsewhere in the project. Tracked as an accepted finding in
# docs/vulnerability_log.md rather than fixed here, since fixing it would defeat its
# purpose as a seeded issue.
#trivy:ignore:AWS-0143
resource "aws_iam_user" "seeded_legacy_admin" {
  count = var.create_seeded_admin_user ? 1 : 0
  name  = "${var.name_prefix}-legacy-admin"

  tags = merge(var.tags, {
    Purpose = "phase1-seeded-issue"
  })
}

resource "aws_iam_user_policy_attachment" "seeded_legacy_admin" {
  count      = var.create_seeded_admin_user ? 1 : 0
  user       = aws_iam_user.seeded_legacy_admin[0].name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
