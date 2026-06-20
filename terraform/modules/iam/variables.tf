variable "name_prefix" {
  description = "Prefix applied to all resource names/tags created by this module"
  type        = string
}

variable "create_seeded_admin_user" {
  description = "Whether to create the intentionally insecure IAM user (AdministratorAccess, no MFA) used as a Phase 1 seeded issue for Phase 3 detection and Phase 4 remediation"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default     = {}
}
