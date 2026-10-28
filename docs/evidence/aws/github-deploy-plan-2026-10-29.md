# GitHub deployment access prepared — 2026-10-29

**Status: planned, not applied. Automatic deployment remains disabled.**

Read-only AWS inventory confirmed no OIDC providers and no `EnergyPipelineGitHubDeploy` role in the account. GitHub environment `aws-deploy` was created and restricted to exactly branch `main` (one branch, zero tags). No environment secrets or variables were created.

The [identity-only workflow run](https://github.com/keerthivasancr7/germany-energy-market-airflow-pipeline/actions/runs/40787893896) succeeded. It decoded the token in memory and printed only public identity claims, never the raw token or request credential. No AWS calls occurred in that workflow.

Verified claims:

```text
iss = https://token.actions.githubusercontent.com
aud = sts.amazonaws.com
sub = repo:keerthivasancr7/germany-energy-market-airflow-pipeline:environment:aws-deploy
repository_id = 1301010525
repository_owner_id = 194722354
ref = refs/heads/main
```

The subject is name-based for this repository; it must not be replaced with an assumed immutable-ID form without verifying an actual token.

The live Terraform plan from commit `178b828`, using the existing adopted state, reported:

```text
Plan: 3 to add, 0 to change, 0 to destroy.
```

Proposed resources:

1. GitHub OIDC identity provider, audience `sts.amazonaws.com`.
2. `EnergyPipelineGitHubDeploy` IAM role trusting only the exact verified environment subject and STS audience.
3. Inline policy `DeployEnergyScriptOnly`: only `s3:GetObject` and `s3:PutObject` on `s3://keerthivasan-energy-pipeline-20261028/scripts/germany-energy-cloud-pipeline.py`.

This role cannot start Glue jobs, query Athena, change IAM or infrastructure, delete objects, or access raw/curated data prefixes. Future code running in this authorized environment can replace the script, so AWS access creation requires explicit approval before apply. GitHub environment restrictions are part of the access boundary because an environment subject does not include the branch.

The private saved plan is `/home/cloudshell-user/energy-plan.5dtgaE/repo/infra/github-deploy.tfplan`. CloudShell's ignored `terraform.tfvars` records the opt-in settings; keep those values with the private state for future plans. Four local Terraform mock tests passed. No access role/provider has been created, no enable variable has been set, and no deployment has been claimed as demonstrated.
