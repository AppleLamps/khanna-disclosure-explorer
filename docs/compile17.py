#!/usr/bin/env python3
"""Compile the 2016/2017 filing OCR JSONs into data-2016.js and data-2017.js."""
import glob, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ocr"))
import fdlib

PTRS = [(f"2017-{i}", f"Periodic Transaction Report #{i-1} (filed 2017)") for i in range(2, 15)]
FD2016 = ("2016-1", "2016 Financial Disclosure (Form B, new member)")
FD2017 = ("2017-1", "2017 Annual Financial Disclosure (Form A)")


def doc_pages(doc, label, seq_start):
    """Load a doc's transcribed pages, adding pending placeholders for untranscribed ones."""
    n_imgs = len(glob.glob(f"docs/{doc}/pages/page-*.jpg"))
    pages, problems = fdlib.load_pages(f"docs/{doc}/text")
    have = {p["_n"] for p in pages}
    for missing in sorted(set(range(1, n_imgs + 1)) - have):
        pages.append({"_n": missing, "printed_label": None, "section": None, "page_type": "pending",
                      "rows": [], "uncertainties": [], "page_confidence": "pending",
                      "free_text": "This page has not been transcribed yet."})
    pages.sort(key=lambda p: p["_n"])
    seq = seq_start
    for p in pages:
        p["pdf_page"] = seq
        p["image"] = f"docs/{doc}/pages/page-{p['_n']:03d}.jpg"
        p["doc"] = doc
        p["doc_label"] = label
        seq += 1
    return pages, seq, problems


def _blocksig(p):
    """Which field-blocks a schedule_a attachment page fills: v/i/a (empty if not mergeable)."""
    rows = [r for r in p.get("rows") or [] if r.get("kind") == "asset"]
    if not rows or p.get("page_type") != "schedule_a" or any(r.get("kind") == "group" for r in p.get("rows") or []):
        return rows, None
    sig = set()
    for r in rows:
        if r.get("value"): sig.add("v")
        if r.get("income_types") or r.get("other_income_spec"): sig.add("i")
        if r.get("amount_of_income") or r.get("amount_of_income_preceding_year") or r.get("amount_of_income_current_year"): sig.add("a")
    return rows, (sig if len(sig) == 1 else None)


def merge_block_runs(pages):
    """Return a copy of pages where consecutive single-block sheet pages with equal
    row counts and disjoint blocks are merged (rows land on the first page of the run)."""
    import copy
    pages = copy.deepcopy(pages)
    i = 0
    while i < len(pages):
        rows_i, sig_i = _blocksig(pages[i])
        if not sig_i:
            i += 1; continue
        run = [(pages[i], rows_i, sig_i)]
        j = i + 1
        while j < len(pages):
            rows_j, sig_j = _blocksig(pages[j])
            if sig_j and len(rows_j) == len(rows_i) and all(sig_j != s for _, _, s in run):
                run.append((pages[j], rows_j, sig_j)); j += 1
            else:
                break
        if len(run) > 1:
            base = run[0][1]
            for pg, rows, _ in run[1:]:
                for k, r in enumerate(rows):
                    b = base[k]
                    for f in ("value", "income_types", "other_income_spec", "amount_of_income",
                              "amount_of_income_preceding_year", "amount_of_income_current_year", "transaction"):
                        if not b.get(f) and r.get(f):
                            b[f] = r[f]
                pg["rows"] = []
        i = j if len(run) > 1 else i + 1
    return pages


def tx_year(t):
    m = re.search(r"/(\d{4})$", t.get("date") or "")
    return int(m.group(1)) if m else None


def build(year, docs, asset_doc, tx_rule, meta):
    all_pages, all_assets, all_txs, problems = [], [], [], []
    seq = 1
    for doc, label in docs:
        pages, seq, probs = doc_pages(doc, label, seq)
        problems += probs
        a, t = fdlib.flatten(merge_block_runs(pages), doc=doc)
        if doc == asset_doc:
            all_assets += a
        all_txs += [x for x in t if tx_rule(doc, x)]
        all_pages += pages
    for p in all_pages:
        p.pop("_n", None)
    fdlib.write_data_js(f"data-{year}.js", {"meta": meta, "source_pdf": meta["source_pdf"],
        "filer": "Rep. Ro Khanna (CA-17)", "filing": meta["kicker"],
        "pages": all_pages, "assets": all_assets, "transactions": all_txs})
    conf = {}
    for p in all_pages:
        conf[p.get("page_confidence", "?")] = conf.get(p.get("page_confidence", "?"), 0) + 1
    missing_desc = sorted({a["name"] for a in all_assets + all_txs if not a.get("desc")})
    import json
    json.dump(missing_desc, open(f"docs/descr-missing-{year}.json", "w"), indent=0)
    print(f"{year}: pages={len(all_pages)} assets={len(all_assets)} txs={len(all_txs)} "
          f"confidence={conf} missing_desc={len(missing_desc)}")
    for pr in problems[:5]:
        print("PROBLEM:", pr)


# ---- 2016: holdings from Form B; transactions from PTRs dated 2016 or earlier
build("2016", [FD2016] + PTRS, "2016-1",
      lambda doc, t: doc != "2016-1" and (tx_year(t) or 0) <= 2016,
      {"year": "2016", "source_pdf": "docs/src/2016-1.pdf",
       "kicker": "2016 Financial Disclosure (Form B) + PTRs · U.S. House · California 17th",
       "why_html": ("As a new Member, Rep. Ro Khanna (CA-17) filed his 2016 financial disclosure and 13 periodic "
                    "transaction reports as hand-delivered, unsearchable paper scans. This site is a transcription of "
                    "<a id=\"srclink\" href=\"docs/src/2016-1.pdf\" target=\"_blank\" rel=\"noopener\">those filings (PDF)</a> "
                    "that makes his finances readable, searchable, and analyzable. Dollar figures are the statutory ranges "
                    "reported on the forms. Holdings are from the 2016 Form B. No transactions are shown for 2016: the new-member "
                    "Form B has no transaction schedule, and all of his PTR trades are dated 2017 (switch to the 2017 view).")})

# ---- 2017: holdings + transactions from the Form A annual; PTRs browsable only
build("2017", [FD2017] + PTRS, "2017-1",
      lambda doc, t: doc == "2017-1",
      {"year": "2017", "source_pdf": "docs/src/2017-1.pdf",
       "kicker": "2017 Annual Financial Disclosure (Form A) + PTRs · U.S. House · California 17th",
       "why_html": ("Rep. Ro Khanna (CA-17) disclosed his 2017 finances as 149 pages of hand-delivered, unsearchable "
                    "paper scans rather than filing through the House's electronic system. This site is a transcription of "
                    "<a id=\"srclink\" href=\"docs/src/2017-1.pdf\" target=\"_blank\" rel=\"noopener\">his filing (PDF)</a> "
                    "that makes his finances readable, searchable, and analyzable. Dollar figures are the statutory ranges "
                    "reported on the form. Transactions are from the annual report's Schedule B; the separately filed PTRs "
                    "are viewable in the Document tab (their trades duplicate Schedule B).")})

# ---- 2018: holdings + transactions from the Form A annual; PTRs + admin forms browsable
FD2018 = ("2018-4", "2018 Annual Financial Disclosure (Form A)")
DOCS2018 = [FD2018,
    ("2018-2", "Periodic Transaction Report #1 (filed 2018)"),
    ("2018-3", "Gift Disclosure Waiver Request"),
    ("2018-5", "Periodic Transaction Report #2 (filed 2018)"),
    ("2018-6", "Periodic Transaction Report #3 (filed 2018)"),
    ("2018-7", "Periodic Transaction Report #4 (filed 2018)"),
    ("2018-8", "Periodic Transaction Report #5 (filed 2018)"),
    ("2018-9", "Periodic Transaction Report #6 (filed 2018)"),
    ("2018-10", "Periodic Transaction Report #7 (filed 2018)"),
    ("2018-11", "Periodic Transaction Report #8 (filed 2018)"),
    ("2018-12", "Periodic Transaction Report #9 (filed 2018)"),
    ("2018-13", "Periodic Transaction Report #10 (filed 2018)"),
    ("2018-14", "Periodic Transaction Report #11 (filed 2018)"),
    ("2018-15", "Periodic Transaction Report #12 (filed 2018)"),
    ("2018-16", "Periodic Transaction Report #13 (filed 2018)"),
    ("2018-17", "Periodic Transaction Report — Amendment (Nov 2018)"),
    ("2018-18", "Financial Disclosure Extension Request")]
build("2018", DOCS2018, "2018-4",
      lambda doc, t: doc == "2018-4",
      {"year": "2018", "source_pdf": "docs/src/2018-4.pdf",
       "kicker": "2018 Annual Financial Disclosure (Form A) + PTRs · U.S. House · California 17th",
       "why_html": ("Rep. Ro Khanna (CA-17) disclosed his 2018 finances as 309 pages of hand-delivered, unsearchable "
                    "paper scans rather than filing through the House's electronic system. This site is a transcription of "
                    "<a id=\"srclink\" href=\"docs/src/2018-4.pdf\" target=\"_blank\" rel=\"noopener\">his filing (PDF)</a> "
                    "that makes his finances readable, searchable, and analyzable. Dollar figures are the statutory ranges "
                    "reported on the form. Transactions are from the annual report's Schedule B; the separately filed PTRs "
                    "are viewable in the Document tab (their trades duplicate Schedule B).")})

# ---- 2019: holdings + transactions from the Form A annual; PTRs + admin forms browsable
FD2019 = ("2019-2", "2019 Annual Financial Disclosure (Form A)")
DOCS2019 = [FD2019,
    ("2019-1", "Periodic Transaction Report #1 (filed 2019)"),
    ("2019-3", "Periodic Transaction Report #2 (filed 2019)"),
    ("2019-4", "Periodic Transaction Report — Amendment (Jan 2019)"),
    ("2019-5", "Periodic Transaction Report #3 (filed 2019)"),
    ("2019-6", "Periodic Transaction Report #4 (filed 2019)"),
    ("2019-7", "Periodic Transaction Report #5 (filed 2019)"),
    ("2019-8", "Periodic Transaction Report #6 (filed 2019)"),
    ("2019-9", "Periodic Transaction Report #7 (filed 2019)"),
    ("2019-10", "Periodic Transaction Report #8 (filed 2019)"),
    ("2019-11", "Periodic Transaction Report #9 (filed 2019)"),
    ("2019-12", "Periodic Transaction Report #10 (filed 2019)"),
    ("2019-13", "Periodic Transaction Report #11 (filed 2019)"),
    ("2019-14", "Periodic Transaction Report #12 (filed 2019)"),
    ("2019-15", "Financial Disclosure Extension Request")]
build("2019", DOCS2019, "2019-2",
      lambda doc, t: doc == "2019-2",
      {"year": "2019", "source_pdf": "docs/src/2019-2.pdf",
       "kicker": "2019 Annual Financial Disclosure (Form A) + PTRs · U.S. House · California 17th",
       "why_html": ("Rep. Ro Khanna (CA-17) disclosed his 2019 finances as 210 pages of hand-delivered, unsearchable "
                    "paper scans rather than filing through the House's electronic system. This site is a transcription of "
                    "<a id=\"srclink\" href=\"docs/src/2019-2.pdf\" target=\"_blank\" rel=\"noopener\">his filing (PDF)</a> "
                    "that makes his finances readable, searchable, and analyzable. Dollar figures are the statutory ranges "
                    "reported on the form. Transactions are from the annual report's Schedule B; the separately filed PTRs "
                    "are viewable in the Document tab (their trades duplicate Schedule B).")})

# ---- 2020: holdings + transactions from the Form A annual; PTRs + admin forms browsable
FD2020 = ("2020-14", "2020 Annual Financial Disclosure (Form A)")
DOCS2020 = [FD2020] + \
    [(f"2020-{i}", f"Periodic Transaction Report #{i} (filed 2020)") for i in range(1, 14)] + \
    [("2020-15", "Periodic Transaction Report #14 (filed 2020)"),
     ("2020-16", "Financial Disclosure Extension Request")]
build("2020", DOCS2020, "2020-14",
      lambda doc, t: doc == "2020-14",
      {"year": "2020", "source_pdf": "docs/src/2020-14.pdf",
       "kicker": "2020 Annual Financial Disclosure (Form A) + PTRs · U.S. House · California 17th",
       "why_html": ("Rep. Ro Khanna (CA-17) disclosed his 2020 finances as 326 pages of hand-delivered, unsearchable "
                    "paper scans rather than filing through the House's electronic system. This site is a transcription of "
                    "<a id=\"srclink\" href=\"docs/src/2020-14.pdf\" target=\"_blank\" rel=\"noopener\">his filing (PDF)</a> "
                    "that makes his finances readable, searchable, and analyzable. Dollar figures are the statutory ranges "
                    "reported on the form. Transactions are from the annual report's Schedule B; the separately filed PTRs "
                    "are viewable in the Document tab (their trades duplicate Schedule B).")})
