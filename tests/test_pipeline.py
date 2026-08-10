from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.generate_data import generate, load_config
from scripts.validate_data import validate


REPO_ROOT = Path(__file__).resolve().parents[1]


class ForgeDataPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_config(REPO_ROOT / "config" / "default.json")
        cls.temp_one = tempfile.TemporaryDirectory()
        cls.temp_two = tempfile.TemporaryDirectory()
        cls.output_one = Path(cls.temp_one.name) / "data"
        cls.output_two = Path(cls.temp_two.name) / "data"
        cls.quality_one = Path(cls.temp_one.name) / "quality"
        cls.manifest_one = generate(cls.config, cls.output_one)
        cls.manifest_two = generate(cls.config, cls.output_two)
        cls.validation = validate(cls.output_one, cls.quality_one)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_one.cleanup()
        cls.temp_two.cleanup()

    def test_default_scope(self) -> None:
        self.assertEqual(self.config["project_count"], 25)
        self.assertEqual(self.config["employee_count"], 120)
        self.assertEqual(self.config["start_date"], "2024-01-01")
        self.assertEqual(self.config["end_date"], "2025-12-31")
        self.assertEqual(self.manifest_one["table_count"], 11)

    def test_required_row_counts(self) -> None:
        rows = {item["table"]: item["row_count"] for item in self.manifest_one["files"]}
        self.assertEqual(rows["DimDate"], 731)
        self.assertEqual(rows["DimProject"], 25)
        self.assertEqual(rows["DimEmployee"], 120)
        self.assertGreaterEqual(rows["FactLabor"], 8_000)
        self.assertLessEqual(rows["FactLabor"], 20_000)

    def test_intentional_defects_are_exact(self) -> None:
        defects = self.manifest_one["intentional_labor_data_quality"]
        self.assertEqual(defects["duplicate_rows"], 15)
        self.assertEqual(defects["missing_rows"], 12)

    def test_reproducible_checksums(self) -> None:
        hashes_one = {item["file"]: item["sha256"] for item in self.manifest_one["files"]}
        hashes_two = {item["file"]: item["sha256"] for item in self.manifest_two["files"]}
        self.assertEqual(hashes_one, hashes_two)
        for file_name in hashes_one:
            self.assertEqual(
                (self.output_one / file_name).read_bytes(),
                (self.output_two / file_name).read_bytes(),
            )

    def test_quality_suite_has_no_unexpected_failures(self) -> None:
        self.assertEqual(self.validation["overall_status"], "PASS_WITH_EXPECTED_ANOMALIES")
        self.assertEqual(self.validation["unexpected_failures"], [])
        self.assertEqual(self.validation["validated_anomalies"], [
            "A01", "A02", "A03", "A04", "A05", "A06", "A07"
        ])

    def test_committed_outputs_match_fresh_generation(self) -> None:
        committed_manifest = json.loads(
            (REPO_ROOT / "data" / "generated" / "manifest.json").read_text(encoding="utf-8")
        )
        committed_hashes = {item["file"]: item["sha256"] for item in committed_manifest["files"]}
        fresh_hashes = {item["file"]: item["sha256"] for item in self.manifest_one["files"]}
        self.assertEqual(committed_hashes, fresh_hashes)

    def test_power_bi_measure_catalog_contains_core_kpis(self) -> None:
        dax = (REPO_ROOT / "powerbi" / "measures.dax").read_text(encoding="utf-8")
        for measure in (
            "Forecast Variance $",
            "Labor Utilization %",
            "Capacity Gap FTE",
            "On-Time Milestone %",
            "Overall Project Health",
        ):
            self.assertIn(measure, dax)


if __name__ == "__main__":
    unittest.main()
