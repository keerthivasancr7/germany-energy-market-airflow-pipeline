resource "aws_iam_role" "github_deploy" {
  count = var.enable_github_deploy ? 1 : 0
  name  = "EnergyPipelineGitHubDeploy"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = var.github_oidc_provider_arn }
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
      condition     = var.github_oidc_provider_arn != null && var.github_oidc_subject != null
      error_message = "Verify and set the existing GitHub OIDC provider ARN and exact environment subject before enabling deployment."
    }
    precondition {
      condition     = var.github_oidc_provider_arn == "arn:${local.partition}:iam::${var.aws_account_id}:oidc-provider/token.actions.githubusercontent.com"
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
