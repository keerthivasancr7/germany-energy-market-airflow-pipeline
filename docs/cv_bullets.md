# CV bullets

- Built a Dockerized Airflow ETL pipeline using Python, DuckDB and SQL to transform public German renewable energy data into analytics-ready warehouse marts.
- Orchestrated extract, load, transform and data-quality tasks with an Airflow DAG and Docker Compose for reproducible local execution.
- Modeled Germany renewable electricity generation by source and created SQL marts for year-over-year trends and latest energy mix analysis.
- Implemented automated data-quality checks for duplicate years, null keys, negative generation values and populated marts.

Verified metrics from the earlier local snapshot:

- Loaded 9,731 raw renewable energy records.
- Modeled 61 years of Germany renewable generation history through 2025.
- Latest Germany renewable generation total: 295.74 TWh.
- Data quality checks passed for duplicates, null years, negative generation values and populated marts.

## AWS portfolio version

- Extended a German renewable energy pipeline to AWS using S3, an AWS Glue Python Shell job, DuckDB and Athena, producing three Parquet datasets for SQL analysis.
- Processed a 10,582-row source snapshot into 61 years of Germany data and validated duplicate years, required fields and generation values before publishing outputs.
- Verified successful Glue runs, Athena results and CloudWatch logs; configured short log retention and manual job execution for a small learning budget.

The AWS snapshot and original local snapshot have different raw row counts. Use the count matching the execution being described. The latest-year energy mix is the mix of the modeled renewable sources, not Germany's entire electricity mix.

- Adopted an existing AWS batch pipeline with Terraform and verified a clean follow-up plan; added GitHub Actions CI for Python regression tests and Terraform validation.

- Implemented GitHub Actions CI/CD with OIDC authentication, offline regression tests, Terraform validation, and checksum-verified deployment of a Glue script to S3 using a role restricted to one object.

Terraform adoption, hosted CI, and a real OIDC deployment run were verified on 29 October 2026. The deployment publishes code; pipeline execution remains manual and unscheduled. Avoid claims of automated ETL scheduling, production reliability, or streaming.
