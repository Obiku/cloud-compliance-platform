terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.region

  # Lets the CI smoke-test plan (no real AWS credentials, see
  # docs/policy_mapping.md) skip the GetCallerIdentity call the provider makes
  # on every run. Defaults to false so local plans/applies against the real
  # account are unaffected.
  skip_credentials_validation = var.ci_smoke_test
  skip_requesting_account_id  = var.ci_smoke_test

  default_tags {
    tags = {
      Project     = "cloud-compliance-platform"
      Environment = "sandbox"
      ManagedBy   = "terraform"
    }
  }
}
