import json
import tempfile
import unittest
from pathlib import Path

from analysis import deterministic_map_sample, load_incidents, run


class IncidentAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.quality = load_incidents()

    def test_schema_and_coordinate_contract(self):
        self.assertEqual(len(self.data), 150500)
        self.assertTrue(self.data["X"].between(-123, -122).all())
        self.assertTrue(self.data["Y"].between(37, 38).all())
        self.assertEqual(self.quality["duplicate_incident_ids"], 0)

    def test_map_sample_is_deterministic(self):
        first = deterministic_map_sample(self.data)
        second = deterministic_map_sample(self.data)
        self.assertEqual(first["PdId"].tolist(), second["PdId"].tolist())
        self.assertEqual(len(first), 500)

    def test_metrics_are_serializable(self):
        with tempfile.TemporaryDirectory() as temp:
            metrics = run(Path(temp))
            self.assertEqual(metrics, json.loads((Path(temp) / "metrics.json").read_text()))
            self.assertEqual(metrics["largest_category"]["category"], "LARCENY/THEFT")


if __name__ == "__main__":
    unittest.main()
