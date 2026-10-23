import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import analysis
from analysis import category_counts, deterministic_map_sample, district_counts, incidents, load_incidents, run

ROOT = Path(__file__).resolve().parents[1]


class IncidentAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.quality = load_incidents()

    def test_source_checksum(self):
        sources = json.loads((ROOT / "data" / "SOURCES.json").read_text())
        digest = hashlib.sha256((ROOT / "data" / sources["file"]).read_bytes()).hexdigest()
        self.assertEqual(digest, sources["compressed_sha256"])

    def test_coordinates_inside_bounding_box(self):
        self.assertTrue(self.data["X"].between(*analysis.LON_BOUNDS).all())
        self.assertTrue(self.data["Y"].between(*analysis.LAT_BOUNDS).all())
        self.assertEqual(self.quality["duplicate_offense_ids"], 0)

    def test_rows_are_offenses_nested_in_incidents(self):
        self.assertGreater(len(self.data), self.data["IncidntNum"].nunique())
        self.assertEqual(len(incidents(self.data)), self.data["IncidntNum"].nunique())

    def test_counts_reconcile(self):
        categories = category_counts(self.data)
        self.assertEqual(categories["offense_records"].sum(), len(self.data))
        self.assertTrue((categories["incidents"] <= categories["offense_records"]).all())
        districts = district_counts(self.data)
        self.assertAlmostEqual(districts["share"].sum(), 1.0)
        self.assertGreaterEqual(districts["incidents"].sum(), self.data["IncidntNum"].nunique())

    def test_map_sample_is_deterministic_and_unique(self):
        first = deterministic_map_sample(self.data)
        second = deterministic_map_sample(self.data)
        self.assertEqual(first["IncidntNum"].tolist(), second["IncidntNum"].tolist())
        self.assertEqual(first["IncidntNum"].nunique(), 500)

    def test_metrics_are_serializable(self):
        with tempfile.TemporaryDirectory() as temp:
            metrics = run(Path(temp))
            self.assertEqual(metrics, json.loads((Path(temp) / "metrics.json").read_text()))
            self.assertEqual(metrics["top_categories_by_incidents"][0]["category"], "LARCENY/THEFT")


if __name__ == "__main__":
    unittest.main()
