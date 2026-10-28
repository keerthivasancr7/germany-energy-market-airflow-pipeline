terraform {
  required_version = ">= 1.7.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  # Refuse accidental adoption/deployment into a different AWS account.
  allowed_account_ids = [var.aws_account_id]
}

data "aws_partition" "current" {}
