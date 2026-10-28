output "bucket_name" {
  value = aws_s3_bucket.pipeline.id
}
output "glue_job_name" {
  value = aws_glue_job.energy.name
}
output "athena_workgroup" {
  value = aws_athena_workgroup.energy.name
}
output "github_deploy_role_arn" {
  value = var.enable_github_deploy ? aws_iam_role.github_deploy[0].arn : null
}
