# Mock provider: no AWS credentials, reads, writes, or charges.
mock_provider "aws" {
  mock_data "aws_partition" {
    defaults = {
      partition = "aws"
    }
  }
}

variables {
  aws_account_id = "123456789012"
  adopt_existing = false
}

run "cost_and_access_boundaries" {
  command = plan

  assert {
    condition     = aws_glue_job.energy.max_capacity == 0.0625 && aws_glue_job.energy.timeout == 5 && aws_glue_job.energy.max_retries == 0
    error_message = "The test job must retain small capacity, a five-minute timeout, and zero retries."
  }
  assert {
    condition     = aws_glue_job.energy.execution_property[0].max_concurrent_runs == 1
    error_message = "Do not start overlapping Glue runs."
  }
  assert {
    condition     = aws_athena_workgroup.energy.configuration[0].bytes_scanned_cutoff_per_query == 10485760
    error_message = "Athena needs its per-query scan limit."
  }
  assert {
    condition     = aws_s3_bucket_public_access_block.pipeline.block_public_acls && aws_s3_bucket_public_access_block.pipeline.block_public_policy
    error_message = "The project bucket must remain private."
  }
  assert {
    condition     = length(aws_iam_role.github_deploy) == 0
    error_message = "GitHub cloud access must remain disabled until configured explicitly."
  }
  assert {
    condition     = alltrue([for group in aws_cloudwatch_log_group.glue : group.retention_in_days == 7])
    error_message = "Both log groups require seven-day retention."
  }
}

run "oidc_deployment_is_script_only" {
  command = plan
  variables {
    enable_github_deploy     = true
    github_oidc_provider_arn = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
    github_oidc_subject      = "repo:keerthivasancr7/germany-energy-market-airflow-pipeline:environment:aws-deploy"
  }
  assert {
    condition     = jsondecode(aws_iam_role_policy.github_script_only[0].policy).Statement[0].Resource == "arn:aws:s3:::keerthivasan-energy-pipeline-20261028/scripts/germany-energy-cloud-pipeline.py"
    error_message = "Deployment must be scoped to exactly the Glue script object."
  }
  assert {
    condition     = toset(jsondecode(aws_iam_role_policy.github_script_only[0].policy).Statement[0].Action) == toset(["s3:GetObject", "s3:PutObject"])
    error_message = "Do not add job-start or IAM permissions to the deployment role."
  }
}

run "reject_wildcard_oidc_subject" {
  command = plan
  variables {
    github_oidc_subject = "repo:keerthivasancr7/germany-energy-market-airflow-pipeline:*"
  }
  expect_failures = [var.github_oidc_subject]
}
