import unittest
import json
from pathlib import PureWindowsPath
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.build_open_data import (
    build_summary,
    canonical_company,
    document_type,
    parse_date,
    relative_posix,
    sum_ranges,
    write_javascript,
    write_json,
)


class BuildOpenDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1] / "data" / "normalized"
        load = lambda name: [json.loads(line) for line in (root / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()]
        cls.transactions = load("transactions")
        cls.summary = build_summary(load("documents"), load("pages"), load("assets"), cls.transactions)

    def test_parse_date_accepts_current_and_prior_reporting_years(self):
        self.assertEqual(parse_date("05/08/2025", 2025), "2025-05-08")
        self.assertEqual(parse_date("31-Dec-23", 2025), "2023-12-31")
        self.assertEqual(parse_date("01/06/2026", 2025), "2026-01-06")

    def test_parse_date_rejects_ocr_corrupted_and_future_years(self):
        self.assertIsNone(parse_date("05/08/2028", 2025))
        self.assertIsNone(parse_date("08/26/2509", 2025))
        self.assertIsNone(parse_date("05/08/1928", 2025))

    def test_document_type_distinguishes_non_ptr_filings(self):
        self.assertEqual(
            document_type("2016 Financial Disclosure (Form B, new member)"),
            "new_member_disclosure",
        )
        self.assertEqual(document_type("Gift Disclosure Waiver Request"), "gift_disclosure_waiver")
        self.assertEqual(document_type("2024 Annual Financial Disclosure (Form A)"), "annual_disclosure")
        self.assertEqual(document_type("2025 PTR #1"), "periodic_transaction_report")

    def test_relative_posix_is_platform_independent(self):
        root = PureWindowsPath("C:/release")
        path = root / "data" / "normalized" / "assets.csv"
        self.assertEqual(relative_posix(path, root), "data/normalized/assets.csv")

    def test_write_json_always_uses_lf(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            write_json(path, {"status": "pass"})
            self.assertNotIn(b"\r\n", path.read_bytes())

    def test_sum_ranges_preserves_open_upper_bounds(self):
        rows = [{"lo": 1, "hi": 10}, {"lo": 11, "hi": None}, {"lo": None, "hi": None}]
        self.assertEqual(
            sum_ranges(rows, "lo", "hi"),
            {"minimum": 12, "maximum_floor": 21, "open_ended": 1, "known_rows": 2},
        )

    def test_company_aliases_merge_share_classes_and_exclude_non_companies(self):
        common = {"asset_class": "Common stock", "description": ""}
        self.assertEqual(canonical_company({**common, "asset_name": "ALPHABET INC. CMN CLASS A"}), "Alphabet")
        self.assertEqual(canonical_company({**common, "asset_name": "GOOGLE INC CLASS C"}), "Alphabet")
        self.assertIsNone(canonical_company({**common, "asset_name": "[ILLEGIBLE]"}))
        self.assertIsNone(canonical_company({"asset_class": "Options", "asset_name": "CALL/GOOGL"}))
        self.assertNotEqual(canonical_company({**common, "asset_name": "Apple Global Management Inc"}), "Apple")
        self.assertNotEqual(
            canonical_company({**common, "asset_name": "INTERCONTINENTAL EXCHANGE INC = AMAZON COM INC CMN"}),
            "Amazon",
        )

    def test_summary_matches_current_release_baselines(self):
        summary = self.summary
        self.assertEqual(summary["transactions"]["count"], 48281)
        self.assertEqual(summary["transactions"]["range"]["minimum"], 307100028)
        self.assertEqual(summary["transactions"]["range"]["maximum_floor"], 1295738010)
        self.assertEqual(summary["transactions"]["range"]["open_ended"], 10)
        self.assertEqual(summary["highlights"]["busiest_year"], 2022)
        self.assertEqual(summary["highlights"]["busiest_year_count"], 7615)
        self.assertEqual(summary["highlights"]["standard_bucket_count"], 41073)
        self.assertEqual(summary["highlights"]["common_stock_count"], 42201)
        self.assertEqual(summary["highlights"]["minimum_holdings_peak_year"], 2022)
        self.assertEqual(summary["highlights"]["upper_holdings_peak_year"], 2024)
        self.assertEqual(summary["top_companies"][0]["name"], "Alphabet")

    def test_summary_owner_attribution_baseline(self):
        owners = {row["label"]: row["count"] for row in self.summary["transactions"]["owners"]}
        self.assertEqual(owners, {"Spouse": 33268, "Dependent children": 14982, "Not stated": 31})

    def test_company_drilldown_names_reproduce_summary_counts(self):
        for company in self.summary["top_companies"]:
            for year in company["years"]:
                names = set(year["asset_names"])
                matching = sum(
                    row["year"] == year["year"]
                    and row["asset_class"] == "Common stock"
                    and row["asset_name"] in names
                    for row in self.transactions
                )
                self.assertEqual(matching, year["count"])

    def test_summary_javascript_is_deterministic(self):
        with TemporaryDirectory() as directory:
            first = Path(directory) / "first.js"
            second = Path(directory) / "second.js"
            write_javascript(first, "FD_SUMMARY", self.summary)
            write_javascript(second, "FD_SUMMARY", self.summary)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertNotIn(b"\r\n", first.read_bytes())


if __name__ == "__main__":
    unittest.main()
