# AWS upgrade: deployment and automation

## Current status

On 28 October 2026 the author manually deployed the Energy Pipeline in Frankfurt (`eu-central-1`). Supplied screenshots show two successful Python Shell job runs, Parquet output folders in S3, SQL results in Athena, and CloudWatch output logs. The log groups' retention was set to one week; the user reported completing the error-log setting. The job timeout was subsequently changed to five minutes and saved; the historical run details still describe the earlier 2,880-minute configuration.

The downloaded [AWS-generated metrics](evidence/aws/pipeline_metrics-2026-10-28.json) match the raw CSV SHA256 and report 10,582 source rows, 61 Germany records, no duplicate years, and 2025 renewable generation of 295.74 TWh. Output counts are 61 fact rows, 61 trend rows, and four latest-mix rows. Screenshots show Athena reading 2025 values of 136.03 wind, 89.62 solar, 50.53 bioenergy/other, and 19.56 hydro TWh, and year-over-year change of 4.88 TWh (1.68%). These are demonstrated portfolio results, not a production SLA or benchmark.

Terraform and GitHub workflows have been prepared locally. They are **not yet applied/enabled or demonstrated on GitHub**. Local tests and mock plans must not be described as actual AWS deployment by Terraform or a successful GitHub Actions run.

## Architecture

```text
Public OWID CSV downloaded locally
  -> manual S3 raw/ upload
  -> AWS Glue Python Shell (Python 3.9 + duckdb 1.4.3)
  -> S3 curated/ (three Parquet datasets + metrics JSON)
  -> Athena external tables in the Glue Data Catalog

CloudWatch: job output/error logs, seven-day retention
GitHub Actions CI: offline tests + Terraform validation/mock plans
GitHub Actions CD (disabled initially): OIDC -> one S3 script object
Terraform: imports/adopts the manually created resources
```

The Glue job reads an existing S3 snapshot; it does not automatically ingest updates from OWID. Airflow remains the separate local orchestration implementation. No automatic AWS schedules, crawlers, VPC/NAT gateways, EC2 instances, or managed Airflow are provisioned.

## Run and test locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python tools/check_source.py
python -m unittest discover -s include/tests -v
```

Offline tests use synthetic fixtures. They cover legacy/split source headers, invalid records failing before uploads, real Parquet outputs, stable keys on replay, script checksum verification, and corrupted deployment detection. The network-based legacy integration test is opt-in with `RUN_LIVE_TESTS=1`; its certificate fallback is legacy local behavior, not used by the cloud script or CI.

The Glue script embeds the local transformation SQL for a self-contained deployment. `tools/check_source.py` checks that both copies agree and parses source with Python 3.9 grammar. CI additionally runs the tests under actual Python 3.9 and 3.12 when enabled on GitHub.

## Existing manual AWS configuration

| Setting | Value |
| --- | --- |
| Bucket | `keerthivasan-energy-pipeline-20261028` |
| Raw input | `raw/modern-renewable-energy-consumption.csv` |
| Glue job | `germany-energy-cloud-pipeline` |
| Role | `AWSGlueServiceRole-EnergyPipeline` |
| Script | `scripts/germany-energy-cloud-pipeline.py` |
| Python/runtime | Python Shell 3.9, analytics libraries enabled |
| Extra module | `duckdb==1.4.3` |
| Capacity | 1/16 DPU (0.0625) |
| Retries/concurrency/timeout | 0 / 1 / 5 minutes |
| Temporary path | `s3://keerthivasan-energy-pipeline-20261028/temp/` |
| Database | `energy_pipeline` |
| Query results | `s3://keerthivasan-energy-pipeline-20261028/athena-results/` |

The role keeps the previously attached `AWSGlueServiceRole` policy. The additional inline policy grants raw/script reads and curated/temp writes in this bucket. This is a practical portfolio configuration, not an assertion that the AWS-managed service policy is minimal. No secrets or access keys belong in Git.

## Adopt with Terraform

Install Terraform 1.7 or later; local validation uses 1.13.5. The AWS provider is recorded in `infra/.terraform.lock.hcl`. Provider `allowed_account_ids` guards against deploying to another account.

First validate without AWS credentials:

```bash
terraform -chdir=infra init -backend=false
terraform -chdir=infra fmt -check -recursive
terraform -chdir=infra validate
terraform -chdir=infra test
```

Then authenticate locally using an appropriate AWS CLI/SSO profile. Do not paste credentials into chat or commit them. Confirm the identity yourself, copy `infra/terraform.tfvars.example` to `infra/terraform.tfvars`, and enter the matching 12-digit account ID. Keep `adopt_existing=true` and `enable_github_deploy=false`.

```bash
aws sts get-caller-identity
terraform -chdir=infra plan -out=adoption.tfplan
terraform -chdir=infra show adoption.tfplan
```

The import blocks adopt the existing bucket, public-access/encryption/ownership configuration, role and policies, script object, Glue job, log groups, database, and all three tables. Existing objects are not recreated. The account's `primary` Athena workgroup and manually created billing budget are not managed by this stack.

The draft creates a **new** `energy-pipeline` Athena workgroup with enforced S3 query-result encryption/location and a 10 MiB per-query scan cutoff. It can also propose normalizing job arguments or catalog metadata. Review every change against the console configuration. Stop if the plan replaces/deletes existing resources or shows unexpected changes; reconcile configuration first. No authenticated plan has yet been inspected.

Only after reviewing the saved plan, apply that exact plan:

```bash
terraform -chdir=infra apply adoption.tfplan
```

No `-auto-approve` is used. Important resources have `prevent_destroy`; the bucket also has `force_destroy=false`. These guards are not substitutes for reviewing plans and do not prevent manual AWS deletions or an IAM user changing settings outside Terraform. A successful apply must be followed by a clean plan and console checks before claiming Terraform deployment.

Local state and plan files are ignored by Git. Back up state privately; avoid simultaneous Terraform users. If moving infrastructure execution into CI later, first configure a private encrypted backend with locking. This workflow does not apply Terraform from GitHub.

## Enable CI

Publish the branch and open a pull request. The CI workflow runs on PRs, pushes to main, and manual dispatch. It installs pinned actions and validates Python, embedded SQL, regression tests, Terraform formatting/schema, and mock plans without AWS credentials.

Wait for actual successful Actions checks before listing CI as demonstrated. Configure the repository's branch rules to require those checks before merging if available for the account.

## Enable CD only after CI works

1. Create a GitHub environment named `aws-deploy`, restrict deployment branches to `main`, and enable a required reviewer if supported for the repository/plan.
2. Confirm the GitHub OIDC provider exists in the correct AWS account. Do not create a duplicate or grant access to another provider. No OIDC provider is created by this Terraform.
3. Verify the exact `sub` claim for this repository and environment. GitHub now uses an immutable owner/repository-ID form for some repositories; do not guess which applies. Use one exact subject, never a wildcard.
4. Set the verified provider ARN and subject in the ignored Terraform variables; set `enable_github_deploy=true`. Review the role's trust and script-only S3 permissions before applying that change.
5. The optional role can only get/put `scripts/germany-energy-cloud-pipeline.py`. It cannot start Glue jobs, change IAM, deploy infrastructure, or modify data prefixes.
6. Set repository variables: `AWS_DEPLOY_ROLE_ARN` from Terraform output, `ENERGY_BUCKET` to the project bucket, and finally `AWS_DEPLOY_ENABLED` to `true`. The enable flag is a repository variable because the workflow tests it before entering the environment.
7. Merge a tested script change or dispatch the deployment workflow on main. The workflow repeats tests, obtains temporary OIDC credentials, uploads the script, and reads it back to verify SHA256. It does not run Glue or Athena.
8. Verify the actual Actions result and S3 object metadata (`sha256` and `git-commit`). Only then describe CD as working.

Disabling `AWS_DEPLOY_ENABLED` stops future workflow deployments; revoke the role trust as well if removing cloud access. Terraform ignores script source/hash drift after adoption because CI/CD owns subsequent code updates. Before enabling CD, script changes require a manual S3 upload or console save.

## Costs and cleanup

The user's project limit is **EUR 5 total**. The console budget is **USD 5 monthly**, with an actual-cost warning changed to 60% (USD 3); forecasts and 100% warnings remain. It is an alert, not an automatic cap. Email verification was still pending in the last evidence that showed that field; verify receipt before relying on alerts. Billing is delayed and the monthly budget resets, so track total project usage separately, including taxes/conversion.

Use manual short runs only. A timeout, concurrency limit, query scan cutoff, and short retention reduce exposure but cannot guarantee a EUR 5 hard cap. CI tests/mocked Terraform runs use no AWS services. Script-only CD makes S3 requests; real Glue execution and Athena queries incur their normal charges. The script is tested and demonstrated at the small snapshot size, not designed for large datasets at 1/16 DPU.

After preserving evidence: leave jobs unscheduled, disable deployment when finished, check billing, and remove test data/results when no longer needed. Bucket versioning remains disabled; keep code in Git and raw snapshot/metrics backups locally. Do not run Terraform destroy on the adopted stack casually: first inventory any data or shared log groups to retain. Billing alerts and log groups can cover more than one job in the account.

## Limitations

- Full batch snapshot rebuild with stable output filenames; not CDC or streaming.
- Multiple S3 outputs are published sequentially, not atomically. Metrics are uploaded last; a mid-upload failure can leave mixed generations. No concurrent runs are allowed.
- Missing generation values are treated as zero in the existing model. `bioenergy_twh` includes other renewables when separate source columns are combined. It is not pure bioenergy in that schema.
- Changing source headers fails explicitly. The cloud job retains raw data and validates Germany records before publishing; malformed data for other countries is not exhaustively validated.
- Logs are demonstrated, but automatic failure paging/operational SLAs are not.
- Local mock validation does not prove IAM authorization, live import success, hosted CI, or OIDC/CD execution.

## Official references

- [Glue Python Shell configuration](https://docs.aws.amazon.com/glue/latest/dg/add-job-python.html)
- [Terraform Glue job and imports](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/glue_job)
- [Terraform Glue table and imports](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/glue_catalog_table)
- [GitHub OIDC for AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
- [GitHub OIDC subject formats](https://docs.github.com/en/actions/reference/security/oidc)
