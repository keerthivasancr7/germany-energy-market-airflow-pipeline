# These blocks record adoption of the manual deployment. No duplicate stack.
# Local `terraform plan` requires authentication; `validate` does not.
import {
  for_each = var.adopt_existing ? toset([var.bucket_name]) : toset([])
  to       = aws_s3_bucket.pipeline
  id       = each.value
}
import {
  for_each = var.adopt_existing ? toset([var.bucket_name]) : toset([])
  to       = aws_s3_bucket_public_access_block.pipeline
  id       = each.value
}
import {
  for_each = var.adopt_existing ? toset([var.bucket_name]) : toset([])
  to       = aws_s3_bucket_ownership_controls.pipeline
  id       = each.value
}
import {
  for_each = var.adopt_existing ? toset([var.bucket_name]) : toset([])
  to       = aws_s3_bucket_server_side_encryption_configuration.pipeline
  id       = each.value
}
import {
  for_each = var.adopt_existing ? toset([var.glue_role_name]) : toset([])
  to       = aws_iam_role.glue
  id       = each.value
}
import {
  for_each = var.adopt_existing ? toset([var.glue_role_name]) : toset([])
  to       = aws_iam_role_policy_attachment.glue_service
  id       = "${each.value}/arn:${local.partition}:iam::aws:policy/service-role/AWSGlueServiceRole"
}
import {
  for_each = var.adopt_existing ? toset([var.glue_role_name]) : toset([])
  to       = aws_iam_role_policy.project_s3
  id       = "${each.value}:EnergyPipelineS3Access"
}
import {
  for_each = var.adopt_existing ? toset([var.job_name]) : toset([])
  to       = aws_glue_job.energy
  id       = each.value
}
import {
  for_each = var.adopt_existing ? toset([local.script_key]) : toset([])
  to       = aws_s3_object.script
  id       = "${var.bucket_name}/${each.value}"
}
import {
  for_each = var.adopt_existing ? local.log_groups : toset([])
  to       = aws_cloudwatch_log_group.glue[each.value]
  id       = each.value
}
import {
  for_each = var.adopt_existing ? toset([var.database_name]) : toset([])
  to       = aws_glue_catalog_database.energy
  id       = "${var.aws_account_id}:${each.value}"
}
import {
  for_each = var.adopt_existing ? local.tables : {}
  to       = aws_glue_catalog_table.energy[each.key]
  id       = "${var.aws_account_id}:${var.database_name}:${each.key}"
}
