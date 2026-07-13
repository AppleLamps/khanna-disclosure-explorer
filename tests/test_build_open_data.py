import unittest
from pathlib import PureWindowsPath
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.build_open_data import document_type, parse_date, relative_posix, write_json


class BuildOpenDataTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
