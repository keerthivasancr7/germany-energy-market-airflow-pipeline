import unittest
import os
from include.src.run_pipeline import run_pipeline


@unittest.skipUnless(os.environ.get("RUN_LIVE_TESTS") == "1", "Live OWID test is opt-in; offline regression tests run by default")
class TestGermanEnergyPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metrics = run_pipeline()

    def test_raw_data_loaded(self):
        self.assertGreater(self.metrics["loaded_rows"], 1000)

    def test_germany_history_available(self):
        self.assertGreater(self.metrics["germany_years"], 30)

    def test_quality_checks_pass(self):
        checks = self.metrics["quality_checks"]
        self.assertEqual(checks["duplicate_years"], 0)
        self.assertEqual(checks["null_years"], 0)
        self.assertEqual(checks["negative_generation_values"], 0)
        self.assertGreater(checks["mart_rows"], 30)


if __name__ == "__main__":
    unittest.main()
