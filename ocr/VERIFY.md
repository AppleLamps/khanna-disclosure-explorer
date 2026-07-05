# Verification pass — independent second read

You are re-verifying a page-level OCR transcription of Ro Khanna's 2024 House Financial Disclosure (scan images under `ocr/`, first-pass JSON in `ocr/text/page-NNN.json`, produced per `ocr/SPEC.md`). Your job: catch and fix transcription errors the first pass made, and certify the page.

## Per page NNN — do the pages ONE AT A TIME, rewriting each file IMMEDIATELY before starting the next page
1. Read `ocr/SPEC.md` once at the start of your run (schema + column bucket enums).
2. Read the images FIRST, before the JSON, and form your own reading of the page: `ocr/pages/page-NNN.jpg` (layout, row count), then all four hi-res crops `ocr/quads/page-NNN-{TL,TR,BL,BR}.jpg`. Count rows independently. Note the printed page label.
3. Now read `ocr/text/page-NNN.json` and compare row-by-row, cell-by-cell against the images:
   - row count and order; owner codes; asset names (verbatim, including truncations/punctuation);
   - WHICH COLUMN each X sits in (value, income type(s), income amount, transaction for Schedule A; tx type, cap-gain checkbox, date, amount for Schedule B);
   - group headers; printed_label; section; page_type; free_text pages verbatim.
   Use `ocr/tess/page-NNN.txt` as a third opinion on name/date spellings.
4. Fix any errors directly in the JSON (keep the SPEC schema and exact bucket strings).
5. EIF capture: Schedule A pages have an EIF checkbox column between ASSET NAME and Block B. Where an X is visible in EIF, add `"eif": true` to that asset row (leave rows without it untouched).
6. Reconcile `uncertainties`: remove entries you can now resolve confidently (apply the resolution to the row); keep or add entries that remain genuinely ambiguous.
7. Add to the top level of the JSON:
   - `"verified": true`
   - `"verification_changes": ["row 7 value: $15,001-$50,000 -> $50,001-$100,000", ...]` — every substantive change you made, empty array if the first pass was fully correct.
   - re-assess `page_confidence` (high/medium/low) after your fixes.
8. Rewrite `ocr/text/page-NNN.json` (valid JSON) IMMEDIATELY, then move to the next page.

## Discipline
- You are a skeptical independent checker: do not assume the first pass is right; verify each cell from the crops. The most common pass-1 errors are: X assigned to an adjacent column (value/income amount off by one bucket), missed second income-type X, missed cap-gain checkbox, digit errors in strikes/dates, and row misalignment near the page bottom.
- Do not "improve" verbatim text (odd punctuation, truncated names stay as printed).
- If you disagree with pass 1, the hi-res crops win; if the crops are genuinely ambiguous, keep the more plausible reading and record it in `uncertainties`.

Final message (raw data): one line per page: `NNN | changes=K | confidence | note-if-any`.
