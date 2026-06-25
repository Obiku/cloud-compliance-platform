# IAM Identity Center has no Terraform resource for creating the instance itself
# (only data sources for an already-existing one, plus resources that configure
# one) - the standalone instance was bootstrapped once via `aws sso-admin
# create-instance`, free and one-time, documented in docs/phase8_grc_reporting.md.
# Everything downstream of that is managed here.
data "aws_ssoadmin_instances" "this" {}

resource "aws_identitystore_user" "grafana_admin" {
  identity_store_id = tolist(data.aws_ssoadmin_instances.this.identity_store_ids)[0]
  display_name      = var.grafana_admin_username
  user_name         = var.grafana_admin_username

  name {
    given_name  = "Grafana"
    family_name = "Admin"
  }

  emails {
    value   = var.grafana_admin_email
    primary = true
  }
}

# permission_type = SERVICE_MANAGED only means AWS attaches/manages the
# policies on this role for the configured data_sources - the role itself
# still has to be created and passed in, confirmed by a real CreateWorkspace
# 400 ("a Workspace Role ARN should be provided") when role_arn was omitted.
data "aws_iam_policy_document" "grafana_assume_role" {
  count = var.create_workspace ? 1 : 0

  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["grafana.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "grafana_workspace" {
  count = var.create_workspace ? 1 : 0

  name               = "${var.name_prefix}-grafana-workspace-role"
  assume_role_policy = data.aws_iam_policy_document.grafana_assume_role[0].json
  tags               = var.tags
}

# permission_type = SERVICE_MANAGED does not attach this on its own - confirmed
# by a real dashboard query failing with AccessDenied on cloudwatch:GetMetricData
# until this was added.
resource "aws_iam_role_policy_attachment" "grafana_cloudwatch" {
  count = var.create_workspace ? 1 : 0

  role       = aws_iam_role.grafana_workspace[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonGrafanaCloudWatchAccess"
}

resource "aws_grafana_workspace" "this" {
  count = var.create_workspace ? 1 : 0

  name                     = "${var.name_prefix}-grc"
  account_access_type      = "CURRENT_ACCOUNT"
  authentication_providers = ["AWS_SSO"]
  permission_type          = "SERVICE_MANAGED"
  data_sources             = ["CLOUDWATCH"]
  role_arn                 = aws_iam_role.grafana_workspace[0].arn
  tags                     = var.tags
}

resource "aws_grafana_role_association" "admin" {
  count = var.create_workspace ? 1 : 0

  role         = "ADMIN"
  user_ids     = [aws_identitystore_user.grafana_admin.user_id]
  workspace_id = aws_grafana_workspace.this[0].id
}

# A service account + token so the dashboard JSON can be imported via the
# Grafana HTTP API (dashboard-as-code), rather than a manual UI import step.
resource "aws_grafana_workspace_service_account" "dashboard_importer" {
  count = var.create_workspace ? 1 : 0

  name         = "${var.name_prefix}-dashboard-importer"
  workspace_id = aws_grafana_workspace.this[0].id
  grafana_role = "ADMIN"
}

resource "aws_grafana_workspace_service_account_token" "dashboard_importer" {
  count = var.create_workspace ? 1 : 0

  name               = "${var.name_prefix}-dashboard-importer-token"
  service_account_id = aws_grafana_workspace_service_account.dashboard_importer[0].service_account_id
  workspace_id       = aws_grafana_workspace.this[0].id
  seconds_to_live    = 3600
}
