# German Energy Market Data Pipeline with Airflow and Docker

A portfolio-grade data engineering project that uses Airflow, Docker, Python, DuckDB, and SQL to transform public renewable electricity data into analytics-ready tables for Germany.

## AWS cloud upgrade

The pipeline also has a manually demonstrated AWS deployment: **S3 raw CSV -> Glue Python Shell -> three Parquet datasets -> Athena SQL**, with CloudWatch output/error logs. On 28 October 2026, the downloaded AWS metrics recorded **10,582 source rows**, **61 Germany records**, **2025 total 295.74 TWh**, and passing quality checks. These are separate from the older local metrics below.

See the [AWS setup, evidence, Terraform adoption, and CI/CD guide](docs/aws-upgrade.md).

- `cloud/`: self-contained Glue script and Athena SQL.
- `infra/`: Terraform configuration to import the existing resources, with a five-minute Glue timeout, 1/16 DPU, and seven-day logs. It proposes a dedicated Athena workgroup with a 10 MiB query scan limit.
- `.github/workflows/`: offline regression CI and opt-in, OIDC-based script deployment. CD does not start jobs.
- `docs/evidence/aws/`: downloaded metrics from the demonstrated AWS run.

**Status:** manual AWS execution, Athena queries, hosted GitHub Actions CI, and Terraform adoption are verified. On 29 October 2026, Terraform imported 15 resources, created the Athena workgroup, updated four metadata configurations, and deleted none; a follow-up plan reported no changes. [Adoption evidence](docs/evidence/aws/adoption-apply-2026-10-29.md). Automatic AWS script deployment remains disabled and unverified. No production operation or streaming is claimed.

## Problem

Energy-market datasets are often raw, wide, and not ready for analysis. Analysts need repeatable pipelines that extract public data, load it into a warehouse, transform it into clean marts, and validate quality before reporting.

This project solves that by building a reproducible ETL pipeline for German renewable electricity generation trends.

## Business questions

- How has Germany's renewable electricity generation changed over time?
- Which renewable source contributes the most in the latest available year?
- How fast is total renewable generation growing year over year?
- Are there missing, duplicate, or invalid values in the analytics warehouse?

## Tech stack

- Apache Airflow for workflow orchestration
- Docker Compose for reproducible local infrastructure
- Python for extraction and loading
- DuckDB as an analytical warehouse
- SQL for transformations and marts
- CSV raw storage
- Data quality checks in Python/SQL

## Architecture

```text
Public renewable energy CSV
        ↓
Airflow DAG: extract
        ↓
data/raw/*.csv
        ↓
Airflow DAG: load
        ↓
DuckDB warehouse
        ↓
Airflow DAG: transform SQL
        ↓
Analytics marts
        ↓
Airflow DAG: data quality checks
```

## Data source

Source: Our World in Data / Energy data via public Grapher CSV endpoint.

The pipeline filters the dataset to Germany and models renewable electricity generation by source:

- Wind
- Solar
- Hydro
- Bioenergy

## Run locally without Airflow

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m include.src.run_pipeline
python -m unittest discover -s include/tests
```

## Run with Airflow + Docker

```bash
docker compose up airflow-init
docker compose up
```

For a one-off CLI verification run:

```bash
docker compose exec airflow-scheduler airflow dags test german_energy_market_pipeline 2026-07-16
```

Then open Airflow:

```text
http://localhost:8080
username: admin
password: admin
```

Trigger DAG:

```text
german_energy_market_pipeline
```


## Verified pipeline metrics

Latest verification:

- Raw rows loaded: **9,731**
- Germany historical records: **61 years**
- Latest year available: **2025**
- Latest total renewable generation: **295.74 TWh**
- Data quality checks: **passed**
- Local runtime without Airflow: about **1 second**
- Docker/Airflow DAG test: **passed**

## Warehouse tables

- `raw_renewable_generation`
- `stg_germany_renewables`
- `fact_germany_renewable_generation`
- `mart_germany_renewable_trends`
- `mart_germany_energy_mix_latest`

## Data quality checks

The pipeline validates:

- no duplicate year records for Germany
- no null years
- no negative generation values
- analytics mart is populated

## Portfolio value

This project demonstrates practical data engineering skills:

- orchestration with Airflow DAGs
- Dockerized reproducible environment
- API/CSV extraction
- analytical warehouse loading with DuckDB
- SQL transformations and marts
- automated data quality checks
- metrics captured in `data/pipeline_metrics.json`

## CV bullet

Built a Dockerized Airflow ETL pipeline using Python, DuckDB and SQL to transform public German renewable energy data into analytics-ready warehouse marts, with automated data quality checks for duplicates, nulls and invalid generation values.
