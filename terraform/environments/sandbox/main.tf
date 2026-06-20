locals {
  tags = {
    Project     = "cloud-compliance-platform"
    Environment = "sandbox"
  }
}

module "vpc" {
  source = "../../modules/vpc"

  name_prefix          = var.name_prefix
  azs                  = var.azs
  public_subnet_cidrs  = ["10.0.0.0/24", "10.0.1.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]
  enable_nat_gateway   = false
  tags                 = local.tags
}

module "iam" {
  source = "../../modules/iam"

  name_prefix              = var.name_prefix
  create_seeded_admin_user = true
  tags                     = local.tags
}

module "s3" {
  source = "../../modules/s3"

  name_prefix                      = var.name_prefix
  account_id                       = var.account_id
  create_seeded_unencrypted_bucket = true
  tags                             = local.tags
}

data "aws_iam_policy_document" "iam_governance_lambda" {
  statement {
    sid    = "ReadOnlyIamForScanning"
    effect = "Allow"
    actions = [
      "iam:GenerateCredentialReport",
      "iam:GenerateServiceLastAccessedDetails",
      "iam:GetAccountSummary",
      "iam:GetLoginProfile",
      "iam:ListAccessKeys",
      "iam:ListAttachedRolePolicies",
      "iam:ListAttachedUserPolicies",
      "iam:ListMFADevices",
      "iam:ListRoleTags",
      "iam:ListRoles",
      "iam:ListUserTags",
      "iam:ListUsers",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "WriteEvidenceReports"
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${module.s3.evidence_bucket_arn}/iam-governance/*"]
  }

  statement {
    sid       = "EncryptEvidenceReports"
    effect    = "Allow"
    actions   = ["kms:GenerateDataKey"]
    resources = [module.s3.evidence_bucket_kms_key_arn]
  }
}

module "compute" {
  source = "../../modules/compute"

  name_prefix          = var.name_prefix
  function_name_suffix = "iam-governance-scan"
  source_dir           = "${path.root}/../../../python/phase4_iam_governance"
  package_name         = "phase4_iam_governance"
  handler              = "phase4_iam_governance.handler.lambda_handler"
  timeout              = 120
  schedule_expression  = "rate(1 day)"
  extra_policy_json    = data.aws_iam_policy_document.iam_governance_lambda.json
  environment_variables = {
    NAME_PREFIX     = var.name_prefix
    EVIDENCE_BUCKET = module.s3.evidence_bucket_name
  }
  tags = local.tags
}

module "monitoring" {
  source = "../../modules/monitoring"

  name_prefix = var.name_prefix
  tags        = local.tags
}

# The CloudTrail trail itself was created manually in Phase 0 (outside Terraform),
# so there is no module output to reference here - this name just has to match it.
locals {
  cloudtrail_trail_name = "${var.name_prefix}-trail"
}

data "aws_iam_policy_document" "evidence_collection_lambda" {
  statement {
    sid    = "ReadConfigCompliance"
    effect = "Allow"
    actions = [
      "config:GetConformancePackComplianceSummary",
      "config:GetConformancePackComplianceDetails",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "ReadSecurityHubFindings"
    effect    = "Allow"
    actions   = ["securityhub:GetFindings"]
    resources = ["*"]
  }

  statement {
    sid    = "ReadCloudTrail"
    effect = "Allow"
    actions = [
      "cloudtrail:DescribeTrails",
      "cloudtrail:GetTrailStatus",
      "cloudtrail:LookupEvents",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "WriteEvidenceReports"
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${module.s3.evidence_bucket_arn}/evidence/*"]
  }

  statement {
    sid       = "EncryptEvidenceReports"
    effect    = "Allow"
    actions   = ["kms:GenerateDataKey"]
    resources = [module.s3.evidence_bucket_kms_key_arn]
  }
}

module "evidence_collection_compute" {
  source = "../../modules/compute"

  name_prefix          = var.name_prefix
  function_name_suffix = "evidence-collection"
  source_dir           = "${path.root}/../../../python/phase5_evidence_collection"
  package_name         = "phase5_evidence_collection"
  handler              = "phase5_evidence_collection.handler.lambda_handler"
  timeout              = 120
  schedule_expression  = "rate(1 day)"
  extra_policy_json    = data.aws_iam_policy_document.evidence_collection_lambda.json
  environment_variables = {
    EVIDENCE_BUCKET       = module.s3.evidence_bucket_name
    CONFORMANCE_PACK_NAME = module.monitoring.conformance_pack_name
    TRAIL_NAME            = local.cloudtrail_trail_name
  }
  tags = local.tags
}
