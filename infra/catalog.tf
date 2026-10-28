locals {
  # Types match the locally inspected Parquet schemas.
  tables = {
    fact_germany_renewable_generation = [
      { name = "country", type = "string" },
      { name = "country_code", type = "string" },
      { name = "year", type = "bigint" },
      { name = "bioenergy_twh", type = "double" },
      { name = "solar_twh", type = "double" },
      { name = "wind_twh", type = "double" },
      { name = "hydro_twh", type = "double" },
      { name = "total_renewable_twh", type = "double" }
    ]
    mart_germany_renewable_trends = [
      { name = "year", type = "bigint" },
      { name = "total_renewable_twh", type = "double" },
      { name = "wind_twh", type = "double" },
      { name = "solar_twh", type = "double" },
      { name = "hydro_twh", type = "double" },
      { name = "bioenergy_twh", type = "double" },
      { name = "yoy_change_twh", type = "double" },
      { name = "yoy_growth_pct", type = "double" }
    ]
    mart_germany_energy_mix_latest = [
      { name = "source", type = "string" },
      { name = "year", type = "bigint" },
      { name = "generation_twh", type = "double" },
      { name = "renewable_mix_pct", type = "double" }
    ]
  }
}

resource "aws_glue_catalog_database" "energy" {
  name = var.database_name
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_glue_catalog_table" "energy" {
  for_each      = local.tables
  name          = each.key
  database_name = aws_glue_catalog_database.energy.name
  table_type    = "EXTERNAL_TABLE"
  parameters = {
    EXTERNAL              = "TRUE"
    "parquet.compression" = "SNAPPY"
  }
  storage_descriptor {
    location      = "s3://${aws_s3_bucket.pipeline.id}/curated/${each.key}/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"
    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }
    dynamic "columns" {
      for_each = each.value
      content {
        name = columns.value.name
        type = columns.value.type
      }
    }
  }
  lifecycle {
    prevent_destroy = true
  }
}
