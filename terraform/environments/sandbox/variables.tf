variable "region" {
  description = "AWS region for the sandbox environment"
  type        = string
  default     = "eu-west-2"
}

variable "account_id" {
  description = "AWS account ID the sandbox environment deploys into"
  type        = string
  default     = "575141563901"
}

variable "name_prefix" {
  description = "Prefix applied to all resource names/tags"
  type        = string
  default     = "cloud-compliance-platform"
}

variable "azs" {
  description = "Availability zones to spread subnets across"
  type        = list(string)
  default     = ["eu-west-2a", "eu-west-2b"]
}

variable "ci_smoke_test" {
  description = "Set true only in CI, where no real AWS credentials are configured, to skip the AWS provider's credential validation call"
  type        = bool
  default     = false
}
