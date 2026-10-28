resource "aws_iam_openid_connect_provider" "github" {
  count          = var.enable_github_deploy && var.create_github_oidc_provider ? 1 : 0
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  lifecycle {
    precondition {
      condition     = var.github_oidc_provider_arn == null
      error_message = "Choose either an existing OIDC provider ARN or creation of a new provider, never both."
    }
  }
}

locals {
  github_provider_arn = var.create_github_oidc_provider && var.enable_github_deploy ? aws_iam_openid_connect_provider.github[0].arn : var.github_oidc_provider_arn
}

resource "aws_iam_role" "github_deploy" {
  count = var.enable_github_deploy ? 1 : 0
  name  = "EnergyPipelineGitHubDeploy"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = local.github_provider_arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          "token.actions.githubusercontent.com:sub" = var.github_oidc_subject
        }
      }
    }]
  })
  lifecycle {
    precondition {
      condition     = (var.create_github_oidc_provider || var.github_oidc_provider_arn != null) && var.github_oidc_subject != null
      error_message = "Verify the provider choice and exact environment subject before enabling deployment."
    }
    precondition {
      condition     = local.github_provider_arn == "arn:${local.partition}:iam::${var.aws_account_id}:oidc-provider/token.actions.githubusercontent.com"
      error_message = "Use the GitHub OIDC provider in the guarded AWS account."
    }
  }
}

resource "aws_iam_role_policy" "github_script_only" {
  count = var.enable_github_deploy ? 1 : 0
  name  = "DeployEnergyScriptOnly"
  role  = aws_iam_role.github_deploy[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:PutObject", "s3:GetObject"]
      Resource = "${local.bucket_arn}/${local.script_key}"
    }]
  })
}
