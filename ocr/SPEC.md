# OCR extraction spec — Khanna 2024 Financial Disclosure (House Form A)

Document: /Users/multivac/Code/khanna/disclosures.pdf — 333 scanned pages, no text layer.
The filing is Rep. Ro Khanna's CY-2024 annual Financial Disclosure Report (printed labels "Page N of 309"; the PDF may contain extra/inserted pages so ALWAYS record the printed label you see).

## Image assets per page (NNN = zero-padded PDF page number, 001–333)
- `ocr/pages/page-NNN.jpg` — full page, correct reading orientation, 150 dpi. Use for layout, row inventory, and section headers.
- `ocr/quads/page-NNN-TL.jpg`, `-TR.jpg`, `-BL.jpg`, `-BR.jpg` — high-res overlapping quadrant crops (top-left, top-right, bottom-left, bottom-right of the READABLE page). Use these to resolve fine print: asset names, dates, and exactly which column an X sits in. Quadrants overlap ~8% so rows/columns at the seam appear in two crops.
- `ocr/tess/page-NNN.txt` — raw tesseract output. Noisy; use only as a cross-check for spelling of asset names/tickers/dates. When your reading and tesseract agree, confidence is high. When they disagree, re-examine the quadrant crop and decide; note it in `uncertainties` if still unsure.

## Method (per page) — follow exactly
1. Read the full page jpg. Identify the schedule/section, printed page label, and count the data rows.
2. Read all four quadrant crops. Transcribe rows from the high-res crops, using the full page to keep row order and to match left-half (names) with right-half (checkbox columns) of each row. Row counting discipline: the Nth asset row from the top on the left side corresponds to the Nth row on the right side. Count carefully — off-by-one row misalignment is the #1 error mode.
3. Cross-check names/dates against the tesseract txt.
4. Write the JSON file. Re-verify your row count matches step 1 before writing.

## Output: one file per page — `ocr/text/page-NNN.json`

```json
{
  "pdf_page": 17,
  "printed_label": "Page 13 of 309",
  "section": "SCHEDULE A - ASSETS & \"UNEARNED INCOME\"",
  "page_type": "schedule_a",
  "filer": "Rohit Khanna",
  "rows": [ ... ],
  "free_text": null,
  "uncertainties": [
    {"row": 12, "field": "asset_name", "read": "CALLGCV FLEX EURO PM @ 155 EXP 07/05/2024", "note": "strike price digit unclear, could be 165"}
  ],
  "page_confidence": "high"
}
```

`page_type`: one of `cover`, `schedule_a`, `schedule_b`, `schedule_c`, `schedule_d`, `schedule_e`, `schedule_f`, `schedule_g`, `schedule_h`, `schedule_i`, `exclusions`, `letter`, `other`.

`page_confidence`: `high` (everything legible, tesseract mostly agrees), `medium` (a few uncertain cells), `low` (significant illegible content).

### rows — ordered top-to-bottom, two kinds of entries

Group/subheader rows (bold portfolio headers like "Monte and Usha Ahuja 2010 Irrev Trust FBO Grandchildren", "Ritu Ahuja 1995 Trust", "M & R Trust Partnership - 2020 Trust FBO Khanna Children"):
```json
{"kind": "group", "text": "Ritu Ahuja 1995 Trust"}
```

### Schedule A data row
```json
{"kind": "asset", "owner": "DC", "asset_name": "ABBOTT LABORATORIES CMN",
 "value": "$15,001-$50,000", "income_types": ["DIVIDENDS"],
 "other_income_spec": null, "amount_of_income": "$201-$1,000", "transaction": "P"}
```
- `owner`: SP / DC / JT or null (left margin column).
- `value` (Block B) — transcribe as the exact bucket the X is under, one of:
  `None`, `$1-$1,000`, `$1,001-$15,000`, `$15,001-$50,000`, `$50,001-$100,000`, `$100,001-$250,000`, `$250,001-$500,000`, `$500,001-$1,000,000`, `$1,000,001-$5,000,000`, `$5,000,001-$25,000,000`, `$25,000,001-$50,000,000`, `Over $50,000,000`, `Spouse/DC Asset over $1,000,000`
- `income_types` (Block C), any of: `NONE`, `DIVIDENDS`, `RENT`, `INTEREST`, `CAPITAL GAINS`, `EXCEPTED/BLIND TRUST`, `TAX-DEFERRED`, plus `other_income_spec` for the write-in column (e.g. "PTN" = partnership income).
- `amount_of_income` (Block D), one of: `None`, `$1-$200`, `$201-$1,000`, `$1,001-$2,500`, `$2,501-$5,000`, `$5,001-$15,000`, `$15,001-$50,000`, `$50,001-$100,000`, `$100,001-$1,000,000`, `$1,000,001-$5,000,000`, `Over $5,000,000`, `Spouse/DC Asset with income over $1,000,000`
- `transaction` (Block E): verbatim, e.g. `P`, `S`, `S(part)`, `P,S(part)`, or null.

### Schedule B data row
```json
{"kind": "tx", "owner": "SP", "asset_name": "STRYKER CORPORATION CMN",
 "tx_type": "Purchase", "cap_gain_over_200": false, "date": "12/5/2024",
 "notification_date": null, "amount": "$1,001-$15,000"}
```
- `tx_type`: `Purchase` / `Sale` / `Partial Sale` / `Exchange` (from the X in Type of Transaction).
- `amount` buckets: `$1,001-$15,000`, `$15,001-$50,000`, `$50,001-$100,000`, `$100,001-$250,000`, `$250,001-$500,000`, `$500,001-$1,000,000`, `$1,000,001-$5,000,000`, `$5,000,001-$25,000,000`, `$25,000,001-$50,000,000`, `Over $50,000,000`, `Over $1,000,000 (Spouse/DC Asset)`.

### Other pages
- Cover page (`cover`): put every field into `free_text` as readable markdown (name, status, questions A–I with Yes/No answers, IPO/Trusts/Exemption answers, telephone, report type…). `rows`: [].
- Schedules C–I, exclusion pages, letters, and anything else: transcribe verbatim into `free_text` (markdown; use tables where the form is tabular). `rows`: [] unless clearly tabular asset/tx data.
- Blank/continuation pages: `page_type: "other"`, note "blank" in `free_text`.

## Rules
- Transcribe VERBATIM — preserve odd tickers, strike notations ("CALLxxx FLEX EURO PM @ 255 EXP 02/07/2025"), rate/date suffixes on bonds ("OHIO ST GO 5% 08/01/24 FA"). Do not normalize or "fix" names.
- Never guess silently: any cell you are not sure of goes into `uncertainties` with your best reading.
- An empty checkbox row cell = the bucket column with no X; exactly one X per block is expected for B and D (except None). If you see zero or multiple, record what you actually see and flag it.
- Do not skip rows. If a row is truly illegible, emit it with `"asset_name": "[ILLEGIBLE]"` and flag it.
- Write valid JSON (UTF-8, no trailing commas). File must parse with `json.load`.
