import csv
import io
import tempfile
import unittest
from pathlib import Path

import duckdb

from cloud.glue_energy_pipeline import build_outputs, run_pipeline, OUTPUT_TABLES


class MemoryS3:
    def __init__(self, csv_bytes):
        self.csv_bytes = csv_bytes
        self.objects = {}

    def download_file(self, bucket, key, destination):
        Path(destination).write_bytes(self.csv_bytes)

    def upload_file(self, source, bucket, key):
        self.objects[key] = Path(source).read_bytes()


def fixture(rows, split=True):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Entity", "Code", "Year"] +
                    (["Bioenergy", "Other renewables"] if split else
                     ["Bioenergy and other renewables"]) +
                    ["Solar", "Wind", "Hydropower"])
    writer.writerows(rows)
    return output.getvalue().encode()


class TestCloudPipeline(unittest.TestCase):
    def test_split_schema_parquet_and_replay(self):
        client = MemoryS3(fixture([
            ["Germany", "DEU", 2024, 2, 1, 10, 20, 5],
            ["Germany", "DEU", 2025, 3, 1, 11, 22, 6],
            ["France", "FRA", 2025, 99, 99, 99, 99, 99],
        ]))
        first = run_pipeline(client)
        second = run_pipeline(client)
        self.assertEqual(first["latest_total_renewable_twh"], 43)
        self.assertEqual(first["germany_years"], 2)
        self.assertEqual(first["source_sha256"], second["source_sha256"])
        self.assertEqual(len(client.objects), 4)
        with tempfile.TemporaryDirectory() as directory:
            for table in OUTPUT_TABLES:
                path = Path(directory) / (table + ".parquet")
                path.write_bytes(client.objects["curated/" + table + "/data.parquet"])
                with duckdb.connect() as conn:
                    count = conn.execute("SELECT COUNT(*) FROM read_parquet(?)",
                                         [str(path)]).fetchone()[0]
                self.assertEqual(count, 4 if table.endswith("latest") else 2)

    def test_legacy_schema(self):
        metrics = run_pipeline(MemoryS3(fixture([
            ["Germany", "DEU", 2025, 3, 10, 20, 5]], split=False)))
        self.assertEqual(metrics["latest_total_renewable_twh"], 38)

    def test_bad_data_does_not_upload(self):
        cases = [
            [["Germany", "DEU", 2025, 2, 1, -1, 20, 5]],
            [["Germany", "DEU", "", 2, 1, 10, 20, 5]],
            [["France", "FRA", 2025, 2, 1, 10, 20, 5]],
            [["Germany", "DEU", 2025, 2, 1, 10, 20, 5]] * 2,
        ]
        for rows in cases:
            with self.subTest(rows=rows):
                client = MemoryS3(fixture(rows))
                with self.assertRaises(ValueError):
                    run_pipeline(client)
                self.assertEqual(client.objects, {})
