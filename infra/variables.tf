variable "aws_region" {
  type        = string
  default     = "eu-central-1"
  description = "Keep resources with the existing Frankfurt bucket."
  validation {
    condition     = var.aws_region == "eu-central-1"
    error_message = "This adoption configuration targets the existing Frankfurt deployment."
  }
}

variable "aws_account_id" {
  type        = string
  description = "Your 12-digit account ID, used to guard the deployment and build import IDs."
  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "Enter your own 12-digit AWS account ID."
  }
}

variable "bucket_name" {
  type    = string
  default = "keerthivasan-energy-pipeline-20261028"
}

variable "job_name" {
  type    = string
  default = "germany-energy-cloud-pipeline"
}

variable "glue_role_name" {
  type    = string
  default = "AWSGlueServiceRole-EnergyPipeline"
}

variable "database_name" {
  type    = string
  default = "energy_pipeline"
}

variable "adopt_existing" {
  type        = bool
  default     = true
  description = "Import the manually created resources instead of trying to recreate them."
}

variable "enable_github_deploy" {
  type        = bool
  default     = false
  description = "Opt in only after reviewing the exact GitHub OIDC subject/provider and role permissions."
}

variable "github_oidc_provider_arn" {
  type        = string
  default     = null
  description = "Existing IAM OIDC provider ARN for token.actions.githubusercontent.com. Not created automatically."
}

variable "create_github_oidc_provider" {
  type        = bool
  default     = false
  description = "Opt in only after confirming no GitHub OIDC provider already exists in this AWS account."
}

variable "github_oidc_subject" {
  type        = string
  default     = null
  description = "Exact subject for this repository's aws-deploy environment; verify name-based vs immutable ID format. No wildcard."
  validation {
    condition = var.github_oidc_subject == null ? true : can(regex(
      "^repo:keerthivasancr7(@[0-9]+)?/germany-energy-market-airflow-pipeline(@[0-9]+)?:environment:aws-deploy$",
      var.github_oidc_subject
    ))
    error_message = "Use the exact environment subject for this repository without wildcards."
  }
}
