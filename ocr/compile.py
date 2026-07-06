#!/usr/bin/env python3
"""Merge per-page OCR JSONs into site/data.js: pages + classified asset/tx rows + validation report."""
import json, glob, os, sys, re

SRC = sys.argv[1] if len(sys.argv) > 1 else "ocr/final"
SOURCE_PDF = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2024/9115596.pdf"

# ---------- bucket parsing ----------
def bucket_range(s):
    """Parse a disclosure bucket string into (min, max). max=None means unbounded."""
    if not s:
        return (None, None)
    t = s.strip().lower()
    if t == "none":
        return (0, 0)
    nums = [int(n.replace(",", "")) for n in re.findall(r"[\d,]+", s)]
    nums = [n for n in nums if n > 0]
    if not nums:
        return (None, None)
    if "over" in t or len(nums) == 1:
        return (nums[0] if "over" not in t else nums[0] + 1, None)
    return (nums[0], nums[1])

# ---------- asset classification ----------
CLASS_RULES = [
    ("Options", re.compile(r"^(CALL|PUT)[ /]|FLEX EURO PM|\bEXP \d{2}/\d{2}/\d{4}", re.I)),
    ("Structured notes", re.compile(r"LINKED TO|BASKET OF INDICES|BUFFERED|CONTINGENT|UPSIDE LEVERED|CAPPED|BUFFER STRUCTUR|COMMLNKED|COMM LINKED", re.I)),
    ("Preferred & hybrid securities", re.compile(r"\bPFD\b|HYBRID PERPETUAL|PERPETUAL USD|JRSUB|JR SUB|SR LIEN|\bCPN\b|PREFERRED", re.I)),
    ("Municipal & gov bonds", re.compile(r"\d(\.\d+)?%.*\d{2}/\d{2}/\d{2}|\b(GO|REV|SCH DIST|SCHS|WTR|SWR|DEV AUTH|EXMP|VLG|BLDG CORP|TRANSN|HWY|CONVENTION|CORRECTIONAL|ISSUES DTD|DB 5%|SPL REV|CAP FACS|RECPTS|OBLIG)\b", re.I)),
    ("Common stock", re.compile(r"\bCMN\b|COMMON STOCK", re.I)),
    ("Hedge funds & private funds", re.compile(r"HEDGE FUND|FUND SELECT|COMMITMENT|PARTNERS\b|PARTNERSHIP|OPPORTUNITIES|CREDIT PARTNERS|\bLLC\b|\bL\.?P\.?\b|CAPITAL ACCESS|ACCESS LLC", re.I)),
    ("Cash & deposits", re.compile(r"MONEY MARKET|CASH|DEPOSIT|CHECKING|SAVINGS|\bCD\b|TREASURY BILL|T-BILL", re.I)),
    ("Funds & ETFs", re.compile(r"\bETF\b|INDEX FUND|MUTUAL FUND|\bFUND\b|TRUST UNITS", re.I)),
    ("Common stock", re.compile(r"\bCMN\b|COMMON STOCK|CLASS [AB]\b|\bINC\b|\bCORP\b|\bPLC\b|\bCO\b|COMPANY|\bN\.?V\.?\b|\.COM", re.I)),
]
def classify(name):
    for label, rx in CLASS_RULES:
        if rx.search(name or ""):
            return label
    return "Other"

# ---------- descriptors ----------
# LLM-generated map of asset name -> short plain-English description (built by annotation agents).
DESCR = {}
if os.path.exists("ocr/descriptors.json"):
    with open("ocr/descriptors.json") as fh:
        DESCR = json.load(fh)

MONTH_CODES = {"JJ": "Jan/Jul", "FA": "Feb/Aug", "MS": "Mar/Sep", "AO": "Apr/Oct", "MN": "May/Nov", "JD": "Jun/Dec"}
OPT_RX = re.compile(r"^(CALL|PUT)[ /|]?([A-Z.]{1,6})\b.*?(?:@ ?)?([\d.]+)\s*EXP\s*(\d{2}/\d{2}/\d{4})", re.I)
MUNI_RX = re.compile(r"^(.*?)\s(\d+(?:\.\d+)?)%\s*(?:.*?)(\d{2}/\d{2}/\d{2,4})?\s*(JJ|FA|MS|AO|MN|JD)?$")

def title(s):
    small = {"of", "and", "the", "for", "de"}
    out = []
    for w in re.split(r"(\s+)", s.strip()):
        if w.isspace() or not w:
            out.append(w); continue
        lw = w.lower()
        out.append(lw if lw in small and out else (w if (len(w) <= 3 and w.isupper() and w not in ("THE", "AND", "FOR", "NEW", "SAN", "LTD", "INC", "CO.")) else w.capitalize()))
    return "".join(out)

def rule_descriptor(name, cls):
    n = (name or "").strip()
    m = OPT_RX.match(n)
    if m:
        kind, tick, strike, exp = m.groups()
        return f"{kind.capitalize()} option on {tick.upper()} — ${strike} strike, expires {exp}"
    if cls == "Municipal & gov bonds":
        m2 = MUNI_RX.match(n)
        if m2 and m2.group(2):
            issuer = title(re.sub(r"\b(GO|REV|DB|SCH DIST|SPL)\b.*$", "", m2.group(1)).strip()) or title(m2.group(1))
            cpn = m2.group(2); mat = m2.group(3); mc = MONTH_CODES.get(m2.group(4) or "")
            bits = [f"Municipal bond — {issuer}", f"{cpn}% coupon"]
            if mat: bits.append(f"due {mat}")
            if mc: bits.append(f"pays {mc}")
            return ", ".join(bits)
        return "Municipal / government bond"
    if cls == "Preferred & hybrid securities":
        issuer = title(re.split(r"\b(PFD|HYBRID|PERPETUAL|PREFERRED)\b", n, 1, re.I)[0].strip(" ,."))
        return f"Preferred / hybrid perpetual security issued by {issuer}" if issuer else "Preferred / hybrid security"
    if cls == "Structured notes":
        m3 = re.match(r"^(.*?)\s+(?:COMM ?LINKED|LINKED)\s+TO\s+(.*)$", n, re.I)
        if m3:
            return f"Structured note by {title(m3.group(1))} — return linked to {title(m3.group(2))}"
        return "Structured note (bank-issued, index-linked return)"
    if cls == "Common stock":
        base = re.sub(r"\b(CMN|COMMON STOCK|CLASS [AB]|ADR|SPONSORED)\b\.?", "", n, flags=re.I).strip(" ,.")
        return f"Common stock of {title(base)}" if base else "Common stock"
    if cls == "Hedge funds & private funds":
        return f"Private fund / partnership interest — {title(n)}"
    if cls == "Cash & deposits":
        return "Cash or bank deposit"
    if cls == "Funds & ETFs":
        return f"Investment fund — {title(n)}"
    return None

def descriptor(name, cls):
    d = DESCR.get(name)
    if d:
        return d
    return rule_descriptor(name, cls) or ""

# ---------- load pages ----------
pages, problems = [], []
for f in sorted(glob.glob(f"{SRC}/page-*.json")):
    try:
        with open(f) as fh:
            d = json.load(fh)
    except Exception as e:
        problems.append(f"{f}: JSON parse error: {e}")
        continue
    m = re.search(r"page-(\d+)\.json", f)
    d["pdf_page"] = int(m.group(1))
    d["image"] = f"ocr/pages/page-{m.group(1)}.jpg"
    pages.append(d)
pages.sort(key=lambda p: p["pdf_page"])

got = {p["pdf_page"] for p in pages}
for missing in sorted(set(range(1, 334)) - got):
    problems.append(f"missing page {missing}")
    pages.append({
        "pdf_page": missing, "image": f"ocr/pages/page-{missing:03d}.jpg",
        "printed_label": None, "section": None, "page_type": "pending",
        "rows": [], "uncertainties": [], "page_confidence": "pending",
        "free_text": "This page has not been transcribed yet. The original scan is shown here; the structured transcription will be added when the OCR run resumes.",
    })
pages.sort(key=lambda p: p["pdf_page"])

# ---------- flatten rows ----------
assets, txs = [], []
cur_group, cur_type = None, None
for p in pages:
    if p.get("page_type") != cur_type:
        cur_group, cur_type = None, p.get("page_type")
    for r in p.get("rows") or []:
        if r.get("kind") == "group":
            g = re.sub(r"^[\s\-\u2013\u2014]+", "", (r.get("text") or "")).strip()
            cur_group = g or cur_group
            continue
        name = r.get("asset_name") or ""
        cls = classify(name)
        base = {
            "page": p["pdf_page"], "label": p.get("printed_label"),
            "group": cur_group, "owner": r.get("owner"),
            "name": name, "cls": cls, "desc": descriptor(name, cls),
        }
        if r.get("kind") == "tx":
            lo, hi = bucket_range(r.get("amount"))
            tx_type = re.sub(r",\s*", ", ", (r.get("tx_type") or "").strip()) or None
            txs.append({**base, "tx_type": tx_type, "cap_gain": bool(r.get("cap_gain_over_200")),
                        "date": r.get("date"), "amount": r.get("amount"), "lo": lo, "hi": hi})
        else:
            vlo, vhi = bucket_range(r.get("value"))
            ilo, ihi = bucket_range(r.get("amount_of_income"))
            assets.append({**base, "value": r.get("value"), "vlo": vlo, "vhi": vhi,
                           "income_types": [("N/A" if t.strip().upper() == "NONE" else t.strip().capitalize()) for t in (r.get("income_types") or [])],
                           "other_income": r.get("other_income_spec"),
                           "income_amt": r.get("amount_of_income"), "ilo": ilo, "ihi": ihi,
                           "tx": r.get("transaction")})

# ---------- write ----------
out = {"source_pdf": SOURCE_PDF, "filer": "Rep. Ro Khanna (CA-17)", "filing": "2024 Annual Financial Disclosure (Form A), filed August 2025",
       "pages": pages, "assets": assets, "transactions": txs}
with open("data.js", "w") as fh:
    fh.write("window.FD_DATA = ")
    json.dump(out, fh, separators=(",", ":"))
    fh.write(";")

conf = {}
for p in pages:
    conf[p.get("page_confidence", "?")] = conf.get(p.get("page_confidence", "?"), 0) + 1
n_unc = sum(len(p.get("uncertainties") or []) for p in pages)
print(f"pages={len(pages)} assets={len(assets)} txs={len(txs)} uncertainties={n_unc} confidence={conf}")
cls_count = {}
for a in assets:
    cls_count[a["cls"]] = cls_count.get(a["cls"], 0) + 1
print("classes:", dict(sorted(cls_count.items(), key=lambda kv: -kv[1])))
for pr in problems:
    print("PROBLEM:", pr)
