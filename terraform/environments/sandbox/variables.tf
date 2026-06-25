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
  description = "Set true only in CI, where no real AWS credentials are configured. Skips the AWS provider's credential validation call, plus any data source/resource that would otherwise make a live AWS API call regardless of credential validity (GuardDuty detector lookup, IAM Identity Center lookups)."
  type        = bool
  default     = false
}

variable "create_grafana_workspace" {
  description = "Set true to stand up the Amazon Managed Grafana workspace for a demo, false (default) to keep it torn down and cost-free. See terraform/modules/grafana."
  type        = bool
  default     = false
}

variable "grafana_admin_username" {
  description = "IAM Identity Center username for the Grafana workspace admin"
  type        = string
  default     = "grafana-admin"
}

variable "grafana_admin_email" {
  description = "Email address for the Grafana workspace admin's Identity Center user"
  type        = string
  default     = "kingsleyonyeemeosi@gmail.com"
}
