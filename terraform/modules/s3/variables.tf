variable "name_prefix" {
  description = "Prefix applied to all resource names/tags created by this module"
  type        = string
}

variable "account_id" {
  description = "AWS account ID, used to guarantee globally-unique bucket names"
  type        = string
}

variable "create_seeded_unencrypted_bucket" {
  description = "Whether to create the intentionally insecure S3 bucket (no encryption at rest) used as a Phase 1 seeded issue for Phase 3 detection and Phase 4/5 remediation"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default     = {}
}
