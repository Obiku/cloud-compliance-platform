variable "name_prefix" {
  description = "Prefix applied to all resource names/tags created by this module"
  type        = string
}

variable "create_workspace" {
  description = <<-EOT
    Whether to actually create the Amazon Managed Grafana workspace. Defaults to
    false so this module is fully defined as code but costs nothing until a demo
    is actually needed - set to true, apply, demo, then set back to false and
    apply again to tear it down. The IAM Identity Center user is created
    independently of this flag since it's free on its own.
  EOT
  type        = bool
  default     = false
}

variable "grafana_admin_username" {
  description = "IAM Identity Center username for the Grafana workspace admin"
  type        = string
}

variable "grafana_admin_email" {
  description = "Email address for the Grafana workspace admin's Identity Center user"
  type        = string
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default     = {}
}
