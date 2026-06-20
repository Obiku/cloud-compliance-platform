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

# --- Phase 1 seeded issue ---
# Intentionally insecure IAM user: AdministratorAccess attached directly, no group
# membership, and no MFA device enrolled. This is detected in Phase 3 (Security Hub /
# Config) and remediated in Phase 4 (IAM governance automation). Do not replicate this
# pattern elsewhere in the project.
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
