# GitHub-to-AWS deployment verified — 2026-10-29

The reviewed access plan was applied in AWS CloudShell after user confirmation:

```text
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.
```

Created the GitHub OIDC provider, `EnergyPipelineGitHubDeploy` role and `DeployEnergyScriptOnly` inline policy. Trust matches the exact subject verified in the earlier identity preview. The role permits only S3 GetObject and PutObject for the Glue script object. The GitHub `aws-deploy` environment permits branch `main` only, with no tag rules. No long-lived AWS access keys were stored in GitHub.

Configured repository variables `AWS_DEPLOY_ROLE_ARN`, `ENERGY_BUCKET`, and `AWS_DEPLOY_ENABLED=true`. The enable flag allows the deployment workflow to run on relevant pushes to main or manual dispatch. Environment branch restrictions and the workflow main-branch condition remain in force. Required reviewers were not configured.

Observed [deployment run 40789678933](https://github.com/keerthivasancr7/germany-energy-market-airflow-pipeline/actions/runs/40789678933) on main at commit `14dba0ddeb52b1b2655e82c59628adb5f12f760f`:

- `tests`: succeeded, 13 seconds.
- `deploy`: succeeded, 29 seconds.
- Overall workflow: Success.

The deployment action uses temporary OIDC credentials. The publisher uploads the script and reads its actual bytes back for SHA256 verification. Independent CloudShell checks then downloaded the object and compared it with the repository script:

```text
object: s3://keerthivasan-energy-pipeline-20261028/scripts/germany-energy-cloud-pipeline.py
S3 metadata git-commit: 14dba0ddeb52b1b2655e82c59628adb5f12f760f
S3 metadata sha256: 4c84101eea349ac44ab095c27a9d2f429c36078940224960fe282eec7567be13
Downloaded object SHA256: 4c84101eea349ac44ab095c27a9d2f429c36078940224960fe282eec7567be13
Repository script SHA256: 4c84101eea349ac44ab095c27a9d2f429c36078940224960fe282eec7567be13
ServerSideEncryption: AES256
```

A follow-up authenticated Terraform plan exited 0 and reported no changes. Updated private backups in CloudShell:

- `/home/cloudshell-user/energy-terraform-backups/energy-pipeline-with-github-oidc-2026-10-29.tfstate`
- `/home/cloudshell-user/energy-terraform-backups/energy-pipeline-with-github-oidc-2026-10-29.tfvars`

Keep both state and opt-in variables for future infrastructure plans. The earlier pre-OIDC state backup is historical and is not the current state. No remote backend or infrastructure apply from GitHub is configured.

Scope: verified code delivery to S3. This workflow does not start Glue jobs, run Athena queries, modify IAM/infrastructure, or upload raw/curated data. No new ETL execution or scheduled pipeline was claimed from this deployment. AWS billing totals have not been measured here.
