terraform {
  backend "s3" {
    bucket         = "cloud-compliance-platform-terraform-state-575141563901"
    key            = "sandbox/terraform.tfstate"
    region         = "eu-west-2"
    dynamodb_table = "cloud-compliance-platform-terraform-lock"
    encrypt        = true
  }
}
