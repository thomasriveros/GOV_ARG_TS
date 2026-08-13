import csv
import io
import unittest

from scripts.update_data import long_series_csv


class LongSeriesTests(unittest.TestCase):
    def setUp(self):
        self.group = {
            "unit": "units",
            "series": {
                "industry_a": {
                    "series_id": "a",
                    "label": "Industry A",
                    "component_type": "industry",
                },
                "industry_b": {
                    "series_id": "b",
                    "label": "Industry B",
                    "component_type": "industry",
                },
                "gva": {
                    "series_id": "gva",
                    "label": "GVA",
                    "component_type": "subtotal",
                },
                "taxes": {
                    "series_id": "taxes",
                    "label": "Taxes",
                    "component_type": "bridge",
                },
                "gdp": {
                    "series_id": "gdp",
                    "label": "GDP",
                    "component_type": "total",
                },
            },
            "identities": [
                {"total": "gva", "components": ["industry_a", "industry_b"]},
                {"total": "gdp", "components": ["gva", "taxes"]},
            ],
        }

    @staticmethod
    def payload(value):
        return {"data": [["2024-01-01", value]]}

    def test_writes_long_rows_when_identities_hold(self):
        payloads = {
            "a": self.payload(2),
            "b": self.payload(3),
            "gva": self.payload(5),
            "taxes": self.payload(1),
            "gdp": self.payload(6),
        }
        rows = list(csv.DictReader(io.StringIO(long_series_csv(self.group, payloads))))
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["component"], "industry_a")
        self.assertEqual(rows[-1]["component_type"], "total")

    def test_rejects_failed_accounting_identity(self):
        payloads = {
            "a": self.payload(2),
            "b": self.payload(3),
            "gva": self.payload(99),
            "taxes": self.payload(1),
            "gdp": self.payload(100),
        }
        with self.assertRaisesRegex(RuntimeError, "Accounting identity failed"):
            long_series_csv(self.group, payloads)


if __name__ == "__main__":
    unittest.main()
