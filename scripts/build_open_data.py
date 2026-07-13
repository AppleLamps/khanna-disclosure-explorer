#!/usr/bin/env python3
"""Build and audit the repository's normalized, analysis-ready data release."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "normalized"
YEARS = [str(year) for year in range(2016, 2027)]
SCHEMA_VERSION = "1.0.0"
OWNER_LABELS = {
    "SP": "Spouse",
    "DC": "Dependent child",
    "JT": "Joint",
    "SELF": "Filer",
}
PAGE_TYPE_ALIASES = {
    "extension_request": "letter",
    "filer_notes": "other",
}
PAGE_TYPES = {
    "cover", "ptr_cover", "ptr_transactions", "letter", "schedule_a", "schedule_b",
    "schedule_c", "schedule_d", "schedule_h", "other",
}
PAGE_TYPE_ALIASES["ptr"] = "ptr_transactions"
DOCUMENT_TYPES = {
    "annual_disclosure",
    "extension_request",
    "gift_disclosure_waiver",
    "new_member_disclosure",
    "periodic_transaction_report",
    "other",
}
COMPANY_ALIASES = [
    ("Alphabet", re.compile(r"^\s*(?:ALPHABET|GOOGLE)\b", re.I)),
    ("Walt Disney", re.compile(r"^\s*(?:THE\s+)?(?:WALT\s+DISNEY|DISNEY\s+WALT)\b", re.I)),
    ("Berkshire Hathaway", re.compile(r"^\s*BERKSHIRE\s+HATHAWAY\b", re.I)),
    ("Amazon", re.compile(r"^\s*(?:DE\s+)?AMAZON(?:\.COM|\s+COM|\s+INC)\b", re.I)),
    ("Bank of America", re.compile(r"^\s*BANK\s+OF\s+AMERICA\b", re.I)),
    ("Pfizer", re.compile(r"^\s*PFIZER\b", re.I)),
    ("Micron Technology", re.compile(r"^\s*MICRON\b", re.I)),
    ("General Motors", re.compile(r"^\s*GENERAL\s+MOTORS\b", re.I)),
    ("Microsoft", re.compile(r"^\s*MICROSOFT\b", re.I)),
    ("AT&T", re.compile(r"^\s*AT\s*&?\s*T\b", re.I)),
    ("Merck", re.compile(r"^\s*MERCK\b", re.I)),
    ("Apple", re.compile(r"^\s*APPLE\s+(?:INC|JNC)\b", re.I)),
    ("Home Depot", re.compile(r"^\s*(?:THE\s+)?HOME\s+DEPOT\b", re.I)),
    ("PepsiCo", re.compile(r"^\s*PEPSICO\b", re.I)),
    ("Starbucks", re.compile(r"^\s*STARBUCKS\b", re.I)),
    ("Texas Instruments", re.compile(r"^\s*TEXAS\s+INSTRUMENTS\b", re.I)),
]


def clean(value):
    if not isinstance(value, str):
        return value
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def clean_multiline(value):
    if not isinstance(value, str):
        return value
    value = "\n".join(line.rstrip() for line in value.strip().splitlines())
    return value or None


def parse_date(value, filing_year):
    value = clean(value)
    if not value or value.startswith("["):
        return None
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%d-%b-%y", "%d-%b-%Y"):
        try:
            parsed = dt.datetime.strptime(value, fmt).date()
            # Annual disclosures can include prior reporting periods, while a
            # PTR notification can fall in the following calendar year. Reject
            # OCR-corrupted years instead of turning them into plausible but
            # false historical dates.
            if not filing_year - 2 <= parsed.year <= filing_year + 1:
                return None
            return parsed.isoformat()
        except ValueError:
            pass
    return None


def document_type(label):
    normalized = (clean(label) or "").casefold()
    if "gift disclosure waiver" in normalized:
        return "gift_disclosure_waiver"
    if "extension" in normalized:
        return "extension_request"
    if "periodic transaction" in normalized or re.search(r"\bptr\b", normalized):
        return "periodic_transaction_report"
    if "form b" in normalized or "new member" in normalized:
        return "new_member_disclosure"
    if "annual" in normalized and "financial disclosure" in normalized:
        return "annual_disclosure"
    return "other"


def relative_posix(path, root=ROOT):
    return path.relative_to(root).as_posix()


def normalized_transaction_type(value):
    value = (clean(value) or "").casefold()
    if "purchase" in value:
        return "Purchase"
    if "sale" in value or value in {"s", "s(part)"}:
        return "Sale"
    if "exchange" in value:
        return "Exchange"
    return "Unknown"


def canonical_company(row):
    if row.get("asset_class") != "Common stock":
        return None
    name = clean(row.get("asset_name"))
    if not name or re.search(r"ILLEGIBLE|UNKNOWN|UNIDENTIFIED", name, re.I):
        return None
    for company, pattern in COMPANY_ALIASES:
        if pattern.search(name):
            return company
    fallback = re.sub(r"\([^)]*\)", " ", name.upper())
    fallback = re.sub(
        r"\b(?:CMN|COM|COMMON STOCK|INCORPORATED|INC|CORPORATION|CORP|COMPANY|CO|LTD|PLC|"
        r"CLASS [A-Z]|CL [A-Z]|USD\d+(?:\.\d+)?|NEW|DELAWARE)\b",
        " ",
        fallback,
    )
    fallback = re.sub(r"[^A-Z0-9&.' -]", " ", fallback)
    fallback = re.sub(r"\s+", " ", fallback).strip(" -.,")
    return fallback.title() or None


def sum_ranges(rows, min_key, max_key):
    minimum = maximum_floor = open_count = known_count = 0
    for row in rows:
        lo, hi = row.get(min_key), row.get(max_key)
        if lo is None:
            continue
        known_count += 1
        minimum += lo
        if hi is None:
            open_count += 1
            maximum_floor += lo
        else:
            maximum_floor += hi
    return {
        "minimum": minimum,
        "maximum_floor": maximum_floor,
        "open_ended": open_count,
        "known_rows": known_count,
    }


def distribution(rows, key, missing="Not stated"):
    counts = Counter((row.get(key) if row.get(key) not in (None, "") else missing) for row in rows)
    total = len(rows) or 1
    return [
        {"label": label, "count": count, "share": count / total}
        for label, count in sorted(counts.items(), key=lambda item: (-item[1], str(item[0])))
    ]


def build_summary(documents, pages, assets, transactions):
    by_year = defaultdict(list)
    for row in transactions:
        by_year[row["year"]].append(row)
    yearly_transactions = []
    for year in range(2016, 2027):
        rows = by_year[year]
        type_counts = Counter(normalized_transaction_type(row.get("transaction_type")) for row in rows)
        yearly_transactions.append({
            "year": year,
            "ptr_only": year >= 2025,
            "count": len(rows),
            "range": sum_ranges(rows, "amount_min_usd", "amount_max_usd"),
            "types": dict(sorted(type_counts.items())),
        })

    yearly_holdings = []
    for year in range(2016, 2025):
        rows = [row for row in assets if row["year"] == year]
        yearly_holdings.append({
            "year": year,
            "count": len(rows),
            "holdings": sum_ranges(rows, "value_min_usd", "value_max_usd"),
            "income": sum_ranges(rows, "income_min_usd", "income_max_usd"),
        })

    companies = defaultdict(list)
    for row in transactions:
        company = canonical_company(row)
        if company:
            companies[company].append(row)
    top_companies = []
    for company, rows in companies.items():
        types = Counter(normalized_transaction_type(row.get("transaction_type")) for row in rows)
        years = []
        for year, year_rows in sorted(
            ((year, [row for row in rows if row["year"] == year]) for year in {row["year"] for row in rows})
        ):
            year_types = Counter(normalized_transaction_type(row.get("transaction_type")) for row in year_rows)
            years.append({
                "year": year,
                "count": len(year_rows),
                "purchases": year_types["Purchase"],
                "sales": year_types["Sale"],
                "asset_names": sorted({row["asset_name"] for row in year_rows}),
                "range": sum_ranges(year_rows, "amount_min_usd", "amount_max_usd"),
            })
        top_companies.append({
            "name": company,
            "count": len(rows),
            "purchases": types["Purchase"],
            "sales": types["Sale"],
            "exchanges": types["Exchange"],
            "unknown": types["Unknown"],
            "first_year": min(row["year"] for row in rows),
            "last_year": max(row["year"] for row in rows),
            "range": sum_ranges(rows, "amount_min_usd", "amount_max_usd"),
            "years": years,
        })
    top_companies.sort(key=lambda row: (-row["count"], row["name"]))

    transaction_types = Counter(normalized_transaction_type(row.get("transaction_type")) for row in transactions)
    amount_labels = distribution(transactions, "reported_amount", "Unknown / unreadable")
    owner_labels = {"SP": "Spouse", "DC": "Dependent children", "JT": "Joint", None: "Not stated"}
    owner_counts = Counter(owner_labels.get(row.get("owner_code"), row.get("owner_code") or "Not stated") for row in transactions)
    total_transactions = len(transactions)
    total_range = sum_ranges(transactions, "amount_min_usd", "amount_max_usd")
    busiest = max(yearly_transactions, key=lambda row: row["count"])
    standard_bucket_count = sum(row.get("reported_amount") == "$1,001-$15,000" for row in transactions)
    common_stock_count = sum(row.get("asset_class") == "Common stock" for row in transactions)
    latest_ptr_documents = sum(
        row["year"] == 2026 and row["document_type"] == "periodic_transaction_report" for row in documents
    )
    minimum_peak = max(yearly_holdings, key=lambda row: row["holdings"]["minimum"])
    upper_peak = max(yearly_holdings, key=lambda row: row["holdings"]["maximum_floor"])

    return {
        "schema_version": "1.0.0",
        "coverage": {
            "first_year": 2016,
            "last_year": 2026,
            "transaction_first_year": 2017,
            "transaction_last_year": 2026,
            "documents": len(documents),
            "pages": len(pages),
            "latest_year_ptr_documents": latest_ptr_documents,
            "latest_year_complete": False,
        },
        "transactions": {
            "count": total_transactions,
            "range": total_range,
            "by_year": yearly_transactions,
            "types": [
                {"label": label, "count": count, "share": count / total_transactions}
                for label, count in sorted(transaction_types.items(), key=lambda item: (-item[1], item[0]))
            ],
            "amount_labels": amount_labels,
            "asset_classes": distribution(transactions, "asset_class"),
            "owners": [
                {"label": label, "count": count, "share": count / total_transactions}
                for label, count in sorted(owner_counts.items(), key=lambda item: (-item[1], item[0]))
            ],
        },
        "holdings": {"by_year": yearly_holdings},
        "top_companies": top_companies[:15],
        "highlights": {
            "busiest_year": busiest["year"],
            "busiest_year_count": busiest["count"],
            "standard_bucket_count": standard_bucket_count,
            "standard_bucket_share": standard_bucket_count / total_transactions,
            "common_stock_count": common_stock_count,
            "common_stock_share": common_stock_count / total_transactions,
            "minimum_holdings_peak_year": minimum_peak["year"],
            "upper_holdings_peak_year": upper_peak["year"],
        },
        "methodology": {
            "annual_transaction_years": list(range(2017, 2025)),
            "ptr_only_years": [2025, 2026],
            "transaction_unit": "reported transaction rows",
        },
    }


def owner(value):
    reported = clean(value)
    reported = reported.upper() if reported else None
    code = reported if reported in OWNER_LABELS else None
    return code, OWNER_LABELS.get(code, "Unknown / not stated"), reported


def bucket_range(value):
    value = clean(value)
    if not value:
        return None, None
    lowered = value.lower()
    if lowered == "none":
        return 0, 0
    numbers = [int(number.replace(",", "")) for number in re.findall(r"[\d,]+", value)]
    numbers = [number for number in numbers if number > 0]
    if not numbers:
        return None, None
    if "over" in lowered or len(numbers) == 1:
        return numbers[0] + (1 if "over" in lowered else 0), None
    return numbers[0], numbers[1]


def page_type(value):
    raw = clean(value) or "other"
    normalized = PAGE_TYPE_ALIASES.get(raw, raw)
    return normalized if normalized in PAGE_TYPES else "other"


def read_data(year):
    path = ROOT / f"data-{year}.js"
    text = path.read_text(encoding="utf-8")
    prefix = "window.FD_DATA = "
    if not text.startswith(prefix):
        raise ValueError(f"{path}: expected {prefix!r}")
    return json.loads(text[len(prefix):].rstrip().rstrip(";"))


def local_page_number(image):
    match = re.search(r"page-(\d+)\.jpg$", image or "")
    return int(match.group(1)) if match else None


def source_paths(year, page):
    image = page.get("image")
    n = local_page_number(image)
    if year == "2024":
        return image, f"ocr/text/page-{n:03d}.json", f"ocr/tess/page-{n:03d}.txt"
    doc = page.get("doc")
    return image, f"docs/{doc}/text/page-{n:03d}.json", f"docs/{doc}/tess/page-{n:03d}.txt"


def source_pdf(doc):
    return "disclosures.pdf" if doc == "2024-1" else f"docs/src/{doc}.pdf"


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            fh.write("\n")


def write_json(path, value):
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(value, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def write_javascript(path, variable, value):
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"window.{variable} = ")
        json.dump(value, fh, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        fh.write(";\n")


def csv_value(value):
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return value


def write_csv(path, rows):
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: csv_value(row.get(key)) for key in fields})


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    documents, pages, page_rows, assets, transactions, uncertainties = [], [], [], [], [], []
    document_ids, page_ids = set(), set()
    issues, notes = [], []
    source_jsons, source_tess, source_images, source_pdfs = set(), set(), set(), set()
    raw_page_types, normalized_page_types = Counter(), Counter()
    unparsed_dates = Counter()
    page_index = {}

    for year in YEARS:
        data = read_data(year)
        year_pages = data.get("pages") or []
        seen_docs = defaultdict(list)
        for source_page in year_pages:
            pdf_page = source_page.get("pdf_page")
            doc = source_page.get("doc") or f"{year}-1"
            seen_docs[doc].append(source_page)
            image, source_json, tess = source_paths(year, source_page)
            source_images.add(image)
            source_jsons.add(source_json)
            source_tess.add(tess)
            ptype_raw = clean(source_page.get("page_type")) or "other"
            ptype = page_type(ptype_raw)
            document_page = local_page_number(image)
            page_id = f"page:{doc}:{document_page:04d}"
            page_index[(year, int(pdf_page))] = (page_id, doc)
            if page_id not in page_ids:
                page_ids.add(page_id)
                raw_page_types[ptype_raw] += 1
                normalized_page_types[ptype] += 1
                pages.append({
                    "page_id": page_id,
                    "year": int(doc.split("-", 1)[0]),
                    "document_id": doc,
                    "document_page_number": document_page,
                    "printed_label": clean(source_page.get("printed_label")),
                    "section": clean(source_page.get("section")),
                    "page_type": ptype,
                    "page_type_raw": ptype_raw,
                    "confidence": clean(source_page.get("page_confidence")) or "unknown",
                    "free_text": clean_multiline(source_page.get("free_text")),
                    "row_count": len(source_page.get("rows") or []),
                    "uncertainty_count": len(source_page.get("uncertainties") or []),
                    "page_image_path": image,
                    "source_json_path": source_json,
                    "tesseract_text_path": tess,
                })
                for row_number, row in enumerate(source_page.get("rows") or [], 1):
                    code, label, reported_owner = owner(row.get("owner"))
                    value_min, value_max = bucket_range(row.get("value"))
                    amount_min, amount_max = bucket_range(row.get("amount"))
                    income = row.get("amount_of_income") or row.get("amount_of_income_preceding_year")
                    income_min, income_max = bucket_range(income)
                    reported_date = clean(row.get("date"))
                    notification_date = clean(row.get("notification_date"))
                    page_rows.append({
                        "page_row_id": f"page-row:{doc}:{document_page:04d}:{row_number:04d}",
                        "page_id": page_id,
                        "year": int(doc.split("-", 1)[0]),
                        "document_id": doc,
                        "document_page_number": document_page,
                        "row_number": row_number,
                        "source_json_path": source_json,
                        "row_kind": clean(row.get("kind")) or "unknown",
                        "group_text": clean(row.get("text")),
                        "owner_code": code,
                        "owner_label": label,
                        "owner_reported": reported_owner,
                        "asset_name": clean(row.get("asset_name")),
                        "reported_value": clean(row.get("value")),
                        "value_min_usd": value_min,
                        "value_max_usd": value_max,
                        "income_types": row.get("income_types") or [],
                        "other_income": clean(row.get("other_income_spec")),
                        "reported_income": clean(income),
                        "income_min_usd": income_min,
                        "income_max_usd": income_max,
                        "transaction_type": clean(row.get("tx_type") or row.get("transaction")),
                        "transaction_date_reported": reported_date,
                        "transaction_date_iso": parse_date(reported_date, int(doc.split("-", 1)[0])),
                        "notification_date_reported": notification_date,
                        "notification_date_iso": parse_date(notification_date, int(doc.split("-", 1)[0])),
                        "reported_amount": clean(row.get("amount")),
                        "amount_min_usd": amount_min,
                        "amount_max_usd": amount_max,
                        "capital_gain_over_200_usd": bool(row.get("cap_gain_over_200")),
                        "partial_sale": bool(row.get("partial_sale")),
                        "eif": row.get("eif"),
                    })
                for offset, text in enumerate(source_page.get("uncertainties") or [], 1):
                    uncertainties.append({
                        "uncertainty_id": f"uncertainty:{doc}:{document_page:04d}:{offset:03d}",
                        "page_id": page_id,
                        "year": int(doc.split("-", 1)[0]),
                        "document_id": doc,
                        "document_page_number": document_page,
                        "text": clean(text),
                        "source_json_path": source_json,
                    })

        for doc, doc_pages in sorted(seen_docs.items()):
            pdf = source_pdf(doc)
            source_pdfs.add(pdf)
            if doc in document_ids:
                continue
            document_ids.add(doc)
            documents.append({
                "document_id": doc,
                "year": int(doc.split("-", 1)[0]),
                "title": clean(doc_pages[0].get("doc_label")) or data.get("filing"),
                "filer": clean(data.get("filer")),
                "document_type": document_type(doc_pages[0].get("doc_label")),
                "page_count": len(doc_pages),
                "source_pdf_path": pdf,
            })

        for index, item in enumerate(data.get("assets") or [], 1):
            page_no = int(item.get("page"))
            page_id, inferred_doc = page_index[(year, page_no)]
            document_page = int(page_id.rsplit(":", 1)[1])
            code, label, reported_owner = owner(item.get("owner"))
            lo, hi = item.get("vlo"), item.get("vhi")
            ilo, ihi = item.get("ilo"), item.get("ihi")
            assets.append({
                "asset_id": f"asset:{year}:{index:06d}",
                "year": int(year),
                "document_id": item.get("doc") or inferred_doc,
                "page_id": page_id,
                "collection_page_number": page_no,
                "document_page_number": document_page,
                "owner_code": code,
                "owner_label": label,
                "owner_reported": reported_owner,
                "portfolio_group": clean(item.get("group")),
                "asset_name": clean(item.get("name")),
                "asset_class": clean(item.get("cls")),
                "description": clean(item.get("desc")),
                "reported_value": clean(item.get("value")),
                "value_min_usd": lo,
                "value_max_usd": hi,
                "value_has_open_upper_bound": lo is not None and hi is None,
                "income_types": item.get("income_types") or [],
                "other_income": clean(item.get("other_income")),
                "reported_income": clean(item.get("income_amt")),
                "income_min_usd": ilo,
                "income_max_usd": ihi,
                "income_has_open_upper_bound": ilo is not None and ihi is None,
                "transaction_code": clean(item.get("tx")),
                "printed_page_label": clean(item.get("label")),
            })

        for index, item in enumerate(data.get("transactions") or [], 1):
            page_no = int(item.get("page"))
            page_id, inferred_doc = page_index[(year, page_no)]
            document_page = int(page_id.rsplit(":", 1)[1])
            code, label, reported_owner = owner(item.get("owner"))
            reported_date = clean(item.get("date"))
            notification = clean(item.get("notification_date"))
            date_iso = parse_date(reported_date, int(year))
            notification_iso = parse_date(notification, int(year))
            if reported_date and not date_iso:
                unparsed_dates["transaction_date"] += 1
            if notification and not notification_iso:
                unparsed_dates["notification_date"] += 1
            lo, hi = item.get("lo"), item.get("hi")
            transactions.append({
                "transaction_id": f"transaction:{year}:{index:06d}",
                "year": int(year),
                "document_id": item.get("doc") or inferred_doc,
                "page_id": page_id,
                "collection_page_number": page_no,
                "document_page_number": document_page,
                "owner_code": code,
                "owner_label": label,
                "owner_reported": reported_owner,
                "portfolio_group": clean(item.get("group")),
                "asset_name": clean(item.get("name")),
                "asset_class": clean(item.get("cls")),
                "description": clean(item.get("desc")),
                "transaction_type": clean(item.get("tx_type")),
                "capital_gain_over_200_usd": bool(item.get("cap_gain")),
                "transaction_date_reported": reported_date,
                "transaction_date_iso": date_iso,
                "notification_date_reported": notification,
                "notification_date_iso": notification_iso,
                "reported_amount": clean(item.get("amount")),
                "amount_min_usd": lo,
                "amount_max_usd": hi,
                "amount_has_open_upper_bound": lo is not None and hi is None,
                "printed_page_label": clean(item.get("label")),
            })

    tables = {
        "documents": documents,
        "pages": pages,
        "page_rows": page_rows,
        "assets": assets,
        "transactions": transactions,
        "uncertainties": uncertainties,
    }
    for name, rows in tables.items():
        write_jsonl(OUT / f"{name}.jsonl", rows)
        write_csv(OUT / f"{name}.csv", rows)
    summary_path = ROOT / "summary-data.js"
    write_javascript(summary_path, "FD_SUMMARY", build_summary(documents, pages, assets, transactions))

    for rel in sorted(source_images | source_jsons | source_tess | source_pdfs):
        if not rel or not (ROOT / rel).is_file():
            issues.append({"check": "source_file_exists", "path": rel, "severity": "error"})
    valid_source_json = 0
    for rel in sorted(source_jsons):
        try:
            raw_page = json.loads((ROOT / rel).read_text(encoding="utf-8"))
            if not isinstance(raw_page, dict) or not isinstance(raw_page.get("rows"), list):
                raise ValueError("expected an object with a rows array")
            valid_source_json += 1
        except Exception as error:
            issues.append({"check": "source_json_valid", "path": rel, "error": str(error), "severity": "error"})
    actual_sources = {
        "page_images": {
            relative_posix(path) for pattern in ("docs/*/pages/page-*.jpg", "ocr/pages/page-*.jpg")
            for path in ROOT.glob(pattern)
        },
        "page_source_json": {
            relative_posix(path) for pattern in ("docs/*/text/page-*.json", "ocr/text/page-*.json")
            for path in ROOT.glob(pattern)
        },
        "tesseract_text_files": {
            relative_posix(path) for pattern in ("docs/*/tess/page-*.txt", "ocr/tess/page-*.txt")
            for path in ROOT.glob(pattern)
        },
    }
    for label, actual in actual_sources.items():
        referenced = {"page_images": source_images, "page_source_json": source_jsons,
                      "tesseract_text_files": source_tess}[label]
        if actual != referenced:
            issues.append({"check": "source_inventory_matches", "source_type": label,
                           "unreferenced": sorted(actual - referenced), "missing": sorted(referenced - actual),
                           "severity": "error"})
    for row in assets:
        if not row["asset_name"] or not row["description"]:
            issues.append({"check": "asset_required_text", "record_id": row["asset_id"], "severity": "error"})
        if row["value_min_usd"] is not None and row["value_max_usd"] is not None and row["value_min_usd"] > row["value_max_usd"]:
            issues.append({"check": "asset_value_range", "record_id": row["asset_id"], "severity": "error"})
    for row in transactions:
        if not row["asset_name"] or not row["description"]:
            issues.append({"check": "transaction_required_text", "record_id": row["transaction_id"], "severity": "error"})
        if row["amount_min_usd"] is not None and row["amount_max_usd"] is not None and row["amount_min_usd"] > row["amount_max_usd"]:
            issues.append({"check": "transaction_amount_range", "record_id": row["transaction_id"], "severity": "error"})
    document_id_set = {row["document_id"] for row in documents}
    page_id_set = {row["page_id"] for row in pages}
    for table_name, rows in (("pages", pages), ("page_rows", page_rows), ("assets", assets),
                             ("transactions", transactions), ("uncertainties", uncertainties)):
        for row in rows:
            if row["document_id"] not in document_id_set:
                issues.append({"check": "document_reference", "table": table_name,
                               "record_id": next(value for key, value in row.items() if key.endswith("_id")),
                               "severity": "error"})
            if table_name != "pages" and row["page_id"] not in page_id_set:
                issues.append({"check": "page_reference", "table": table_name,
                               "record_id": next(value for key, value in row.items() if key.endswith("_id")),
                               "severity": "error"})
    for row in documents:
        if row["document_type"] not in DOCUMENT_TYPES:
            issues.append({"check": "document_type", "record_id": row["document_id"],
                           "value": row["document_type"], "severity": "error"})
    pending = sum(row["page_type_raw"] == "pending" for row in pages)
    if pending:
        issues.append({"check": "no_pending_pages", "count": pending, "severity": "error"})
    if unparsed_dates:
        notes.append({"check": "unparsed_dates_preserved", "counts": dict(unparsed_dates), "severity": "info"})
    notes.append({"check": "page_type_normalization", "raw": dict(sorted(raw_page_types.items())),
                  "normalized": dict(sorted(normalized_page_types.items())), "severity": "info"})

    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if not issues else "fail",
        "checks": {
            "years": YEARS,
            "compiled_year_files": len(YEARS),
            "source_pdfs": len(source_pdfs),
            "page_images": len(source_images),
            "page_source_json": len(source_jsons),
            "valid_page_source_json": valid_source_json,
            "tesseract_text_files": len(source_tess),
            "normalized_records": {name: len(rows) for name, rows in tables.items()},
            "confidence_distribution": dict(sorted(Counter(row["confidence"] for row in pages).items())),
            "page_type_distribution": dict(sorted(normalized_page_types.items())),
            "page_row_kind_distribution": dict(sorted(Counter(row["row_kind"] for row in page_rows).items())),
            "owner_code_distribution": dict(sorted(Counter((row["owner_code"] or "not_stated") for row in page_rows).items())),
            "pending_pages": pending,
            "missing_or_invalid_records": len(issues),
        },
        "issues": issues,
        "notes": notes,
    }
    report_path = ROOT / "data" / "quality-report.json"
    write_json(report_path, report)

    files = []
    for path in sorted(OUT.glob("*")):
        if path.is_file():
            stem = path.stem
            files.append({
                "path": relative_posix(path),
                "format": path.suffix.lstrip("."),
                "records": len(tables[stem]),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    files.append({"path": "data/quality-report.json", "format": "json", "records": 1,
                  "bytes": report_path.stat().st_size, "sha256": sha256(report_path)})
    files.append({"path": "summary-data.js", "format": "js", "records": 1,
                  "bytes": summary_path.stat().st_size, "sha256": sha256(summary_path)})
    manifest = {
        "title": "Ro Khanna financial disclosure open data",
        "schema_version": SCHEMA_VERSION,
        "years": YEARS,
        "license": "CC0-1.0 for original dataset contributions; see DATA_LICENSE.md",
        "files": files,
        "source_coverage": report["checks"],
    }
    write_json(ROOT / "data" / "manifest.json", manifest)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="rebuild and fail if the audit finds errors")
    args = parser.parse_args()
    report = build()
    counts = report["checks"]
    print(f"open-data audit: {report['status'].upper()}")
    print(json.dumps(counts, indent=2, sort_keys=True))
    if args.check and report["status"] != "pass":
        for issue in report["issues"][:25]:
            print("ERROR:", json.dumps(issue, sort_keys=True), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
