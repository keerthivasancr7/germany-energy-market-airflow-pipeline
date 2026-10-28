"""Offline regression coverage for the observed OWID column change."""
import tempfile
import unittest
from pathlib import Path

import duckdb

from include.src.transform import transform_energy_marts


class TestSourceSchema(unittest.TestCase):
    def transform_fixture(self, generation_columns, generation_values):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.duckdb"
            with duckdb.connect(str(path)) as conn:
                conn.execute(f'''CREATE TABLE raw_renewable_generation (
                    Entity VARCHAR, Code VARCHAR, Year INTEGER,
                    {generation_columns}, Solar DOUBLE, Wind DOUBLE,
                    Hydropower DOUBLE)''')
                conn.execute(f'''INSERT INTO raw_renewable_generation VALUES
                    ('Germany', 'DEU', 2025, {generation_values}, 10, 20, 5),
                    ('France', 'FRA', 2025, {generation_values}, 100, 200, 50)''')
            metrics = transform_energy_marts(path)
            with duckdb.connect(str(path)) as conn:
                bioenergy = conn.execute(
                    "SELECT bioenergy_twh FROM fact_germany_renewable_generation"
                ).fetchone()[0]
                # Source columns are not renamed or removed in the raw table.
                raw_columns = {r[0] for r in conn.execute(
                    "DESCRIBE raw_renewable_generation"
                ).fetchall()}
            return metrics, bioenergy, raw_columns

    def test_legacy_combined_column(self):
        metrics, bioenergy, columns = self.transform_fixture(
            '"Bioenergy and other renewables" DOUBLE', '3'
        )
        self.assertEqual(metrics["germany_years"], 1)
        self.assertEqual(metrics["latest_total_renewable_twh"], 38)
        self.assertEqual(bioenergy, 3)
        self.assertIn("Bioenergy and other renewables", columns)

    def test_new_split_columns(self):
        metrics, bioenergy, columns = self.transform_fixture(
            'Bioenergy DOUBLE, "Other renewables" DOUBLE', '2, 1'
        )
        self.assertEqual(metrics["latest_total_renewable_twh"], 38)
        self.assertEqual(bioenergy, 3)
        self.assertIn("Other renewables", columns)
        self.assertNotIn("Bioenergy and other renewables", columns)

    def test_null_other_renewables(self):
        metrics, bioenergy, _ = self.transform_fixture(
            'Bioenergy DOUBLE, "Other renewables" DOUBLE', '2, NULL'
        )
        self.assertEqual(bioenergy, 2)
        self.assertEqual(metrics["latest_total_renewable_twh"], 37)

    def test_unsupported_schema_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError, "Unsupported source schema"):
            self.transform_fixture('Bioenergy DOUBLE', '2')
