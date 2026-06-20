variable "name_prefix" {
  description = "Prefix applied to all resource names/tags created by this module"
  type        = string
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default     = {}
}

variable "function_name_suffix" {
  description = "Suffix appended to name_prefix to form the Lambda function name"
  type        = string
  default     = "automation-placeholder"
}

variable "source_dir" {
  description = "Directory whose contents become the Lambda deployment package, nested under package_name so relative imports inside it keep working at runtime"
  type        = string
}

variable "package_name" {
  description = "Name of the Python package folder source_dir represents, preserved as a subfolder in the zip (e.g. handler value becomes \"<package_name>.handler.lambda_handler\")"
  type        = string
}

variable "handler" {
  description = "Lambda handler, in module.function format"
  type        = string
  default     = "handler.handler"
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.12"
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "environment_variables" {
  description = "Environment variables passed to the Lambda function"
  type        = map(string)
  default     = {}
}

variable "extra_policy_json" {
  description = "Additional IAM policy document (JSON) to attach to the Lambda execution role, beyond AWSLambdaBasicExecutionRole"
  type        = string
}

variable "schedule_expression" {
  description = "Optional EventBridge schedule expression (e.g. rate(1 day)) to invoke the function. Null disables scheduling."
  type        = string
  default     = null
}
