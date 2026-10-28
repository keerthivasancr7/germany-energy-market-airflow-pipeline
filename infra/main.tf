locals {
  partition  = data.aws_partition.current.partition
  bucket_arn = "arn:${local.partition}:s3:::${var.bucket_name}"
  script_key = "scripts/${var.job_name}.py"
  log_groups = toset(["/aws-glue/python-jobs/output", "/aws-glue/python-jobs/error"])
}

resource "aws_s3_bucket" "pipeline" {
  bucket        = var.bucket_name
  force_destroy = false
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "pipeline" {
  bucket                  = aws_s3_bucket.pipeline.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "pipeline" {
  bucket = aws_s3_bucket.pipeline.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "pipeline" {
  bucket = aws_s3_bucket.pipeline.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_iam_role" "glue" {
  name        = var.glue_role_name
  description = "Allows Glue to call AWS services on your behalf."
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  lifecycle {
    prevent_destroy = true
  }
}

# Preserve the AWS-managed service policy already attached in the console.
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue.name
  policy_arn = "arn:${local.partition}:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "project_s3" {
  name = "EnergyPipelineS3Access"
  role = aws_iam_role.glue.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ProjectBucketMetadata"
        Effect   = "Allow"
        Action   = ["s3:ListBucket", "s3:GetBucketLocation"]
        Resource = local.bucket_arn
      },
      {
        Sid      = "ReadInputAndScripts"
        Effect   = "Allow"
        Action   = "s3:GetObject"
        Resource = ["${local.bucket_arn}/raw/*", "${local.bucket_arn}/scripts/*"]
      },
      {
        Sid      = "ReadWriteProcessedData"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:AbortMultipartUpload"]
        Resource = ["${local.bucket_arn}/curated/*", "${local.bucket_arn}/temp/*"]
      }
    ]
  })
}

resource "aws_s3_object" "script" {
  bucket = aws_s3_bucket.pipeline.id
  key    = local.script_key
  source = "${path.module}/../cloud/glue_energy_pipeline.py"
  etag   = filemd5("${path.module}/../cloud/glue_energy_pipeline.py")
  lifecycle {
    prevent_destroy = true
    # CI/CD owns script updates after initial adoption; Terraform owns its path.
    ignore_changes = [source, etag, source_hash, metadata]
  }
}

resource "aws_cloudwatch_log_group" "glue" {
  for_each          = local.log_groups
  name              = each.key
  retention_in_days = 7
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_glue_job" "energy" {
  name         = var.job_name
  role_arn     = aws_iam_role.glue.arn
  glue_version = "3.0"
  max_capacity = 0.0625
  max_retries  = 0
  timeout      = 5
  connections  = []
  command {
    name            = "pythonshell"
    python_version  = "3.9"
    script_location = "s3://${aws_s3_bucket.pipeline.id}/${aws_s3_object.script.key}"
  }
  execution_property {
    max_concurrent_runs = 1
  }
  default_arguments = {
    "--job-language"              = "python"
    "--library-set"               = "analytics"
    "--additional-python-modules" = "duckdb==1.4.3"
    "--TempDir"                   = "s3://${aws_s3_bucket.pipeline.id}/temp/"
  }
  depends_on = [aws_iam_role_policy.project_s3, aws_iam_role_policy_attachment.glue_service, aws_cloudwatch_log_group.glue]
  lifecycle {
    prevent_destroy = true
  }
}

# A separate workgroup leaves the account's primary workgroup alone.
resource "aws_athena_workgroup" "energy" {
  name          = "energy-pipeline"
  force_destroy = false
  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true
    bytes_scanned_cutoff_per_query     = 10485760
    result_configuration {
      output_location = "s3://${aws_s3_bucket.pipeline.id}/athena-results/"
      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }
}
