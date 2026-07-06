#!/usr/bin/env python3
"""Compile the 2024 per-page OCR JSONs into data-2024.js."""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import fdlib

SRC = sys.argv[1] if len(sys.argv) > 1 else "ocr/text"
SOURCE_PDF = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2024/9115596.pdf"

pages, problems = fdlib.load_pages(SRC)
for p in pages:
    p["pdf_page"] = p["_n"]
    p["image"] = f"ocr/pages/page-{p['_n']:03d}.jpg"

got = {p["pdf_page"] for p in pages}
for missing in sorted(set(range(1, 334)) - got):
    problems.append(f"missing page {missing}")
    pages.append({"pdf_page": missing, "_n": missing, "image": f"ocr/pages/page-{missing:03d}.jpg",
                  "printed_label": None, "section": None, "page_type": "pending", "rows": [],
                  "uncertainties": [], "page_confidence": "pending",
                  "free_text": "This page has not been transcribed yet."})
pages.sort(key=lambda p: p["pdf_page"])

assets, txs = fdlib.flatten(pages)

meta = {
    "year": "2024",
    "kicker": "2024 Annual Financial Disclosure · U.S. House · California 17th",
    "why_html": ("Rep. Ro Khanna (CA-17) disclosed at least $98.7 million in holdings as 333 pages of "
                 "hand-delivered, unsearchable paper scans rather than filing through the House's electronic system. "
                 f"This site is a transcription of his <a id=\"srclink\" href=\"{SOURCE_PDF}\" target=\"_blank\" rel=\"noopener\">"
                 "filing (Clerk of the House, PDF)</a> that makes his finances readable, searchable, and analyzable. "
                 "Dollar figures are the statutory ranges reported on the form."),
}

for p in pages:
    p.pop("_n", None)
fdlib.write_data_js("data-2024.js", {"meta": meta, "source_pdf": SOURCE_PDF,
    "filer": "Rep. Ro Khanna (CA-17)", "filing": "2024 Annual Financial Disclosure (Form A), filed August 2025",
    "pages": pages, "assets": assets, "transactions": txs})

conf = {}
for p in pages:
    conf[p.get("page_confidence", "?")] = conf.get(p.get("page_confidence", "?"), 0) + 1
print(f"2024: pages={len(pages)} assets={len(assets)} txs={len(txs)} confidence={conf}")
for pr in problems:
    print("PROBLEM:", pr)
