# Local validation — 2026-10-28

These checks validate the prepared repository files. They do not represent a new AWS deployment or a hosted GitHub Actions run.

- Python 3.12: nine offline unit tests passed; three opt-in live source tests skipped.
- Python 3.9 grammar check passed for the Glue script and shared source modules. Actual Python 3.9 execution is configured in GitHub Actions and remains to be verified there.
- Embedded Glue transformation SQL matches the shared SQL file.
- Parquet output schemas generated locally from the supplied CSV match the three Terraform catalog table definitions.
- Terraform 1.13.5 and AWS provider 6.71.0: configuration validation passed.
- Three Terraform mock plan tests passed: cost/access boundaries, script-only OIDC deployment, and rejection of wildcard OIDC subjects.
- Both workflow YAML files parsed locally; hosted action execution remains pending.

No authenticated Terraform plan, import or apply was run. Deployment is disabled by default. Existing manual AWS evidence is described separately in `docs/aws-upgrade.md` and the saved metrics JSON.
