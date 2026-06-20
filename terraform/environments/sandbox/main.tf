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

module "compute" {
  source = "../../modules/compute"

  name_prefix = var.name_prefix
  tags        = local.tags
}

module "monitoring" {
  source = "../../modules/monitoring"

  name_prefix = var.name_prefix
  tags        = local.tags
}
