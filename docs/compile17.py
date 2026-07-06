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


def tx_year(t):
    m = re.search(r"/(\d{4})$", t.get("date") or "")
    return int(m.group(1)) if m else None


def build(year, docs, asset_doc, tx_rule, meta):
    all_pages, all_assets, all_txs, problems = [], [], [], []
    seq = 1
    for doc, label in docs:
        pages, seq, probs = doc_pages(doc, label, seq)
        problems += probs
        a, t = fdlib.flatten(pages, doc=doc)
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
                    "reported on the forms. Holdings are from the 2016 Form B; transactions are PTR trades dated 2016 and earlier.")})

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
