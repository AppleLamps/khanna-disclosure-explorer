# Handoff — Ro Khanna Financial Disclosure OCR + site

You are continuing an in-progress project. This document is self-contained: read it, then
do the work. Everything runs in `/Users/multivac/Code/khanna` (the repo root). Use absolute
paths — the shell's working directory sometimes resets.

## What this project is

OCR of Congressman Ro Khanna's U.S. House financial-disclosure filings (2016–2026), rendered
as a static transparency website. Each year's scanned PDF(s) are transcribed page-by-page into
JSON, compiled into `data-YYYY.js`, and browsed via `index.html` (Overview / Assets /
Transactions / Document tabs, with a `?year=` selector). Deployed: private GitHub repo
`kanetronv2/khanna-disclosure-explorer`, auto-deploys to Vercel on push.

## Current state (as of 2026-07-07)

- **Complete:** 2016, 2017, 2024 (all pages), plus 2018/2019/2020 PTRs, and 2025-1 & 2025-2.
- **Partial annuals:** 2018-4 (180/309), 2019-2 (172/210), 2020-14 (95/326), 2021-13 (31/303),
  2022-15 (13/367), 2023-14 (20/327).
- **Untouched:** most 2021/2022/2023 PTRs, 2019-12/13/14, all 2025-3…13, all of 2026.
- ~2,480 pages remain. Everything transcribed so far is committed and pushed to `origin/main`.

There are TWO phases left: **(1) finish transcription**, then **(2) a verification pass**.
Do them in that order. Phase 2 needs the full structure of every annual visible.

---

## Repo layout

```
index.html                 the whole site (single file; JS + CSS inline)
data-YYYY.js               compiled dataset per year (GENERATED — do not hand-edit)
docs/SPEC.md               base per-page JSON schema (from the 2024 pass)
docs/SPEC17.md             2016–2026 schema addenda + per-year/per-document notes
docs/VERIFY_NOTES.md       the Phase-2 verification checklist (READ THIS for Phase 2)
docs/compile17.py          compiles docs/*/text/*.json  ->  data-YYYY.js  (all years)
docs/<year>-<n>/
    pages/page-NNN.jpg     full page, readable orientation  (layout + row inventory)
    quads/page-NNN-{TL,TR,BL,BR}.jpg   hi-res overlapping crops (read exact X columns here)
    tess/page-NNN.txt      tesseract text (cross-check names/dates only; often noisy)
    text/page-NNN.json     <-- YOU WRITE THIS, one per page
docs/src/<year>-<n>.pdf    original source PDFs
```

`hires/`, `quads/`, `tess/` are gitignored (regenerable); `pages/` and `text/` are tracked.

---

## PHASE 1 — Finish transcription

### How the work is done
Transcription is done by **background sub-agents**, ~6 pages each (whole small PTR docs at
once), running the vision model over the page JPG + 4 quad crops. Keep ~12 agents in flight;
launch the next chunk as each completes. Each agent MUST read `docs/SPEC.md` then
`docs/SPEC17.md` first, and write `docs/<doc>/text/page-NNN.json` immediately after each page
(so a mid-run crash still saves finished pages).

### Standard agent prompt (fill in DOC and PAGES)
> Transcribe scanned US House financial disclosure pages into JSON. Working dir:
> /Users/multivac/Code/khanna. Read /Users/multivac/Code/khanna/ocr/SPEC.md then
> /Users/multivac/Code/khanna/docs/SPEC17.md. Document: docs/<DOC>. Pages: <PAGES>.
> Per page NNN: Read docs/<DOC>/pages/page-NNN.jpg, then
> docs/<DOC>/quads/page-NNN-{TL,TR,BL,BR}.jpg, then docs/<DOC>/tess/page-NNN.txt. Write
> docs/<DOC>/text/page-NNN.json IMMEDIATELY per page. [+ the layout hints for that doc, below]
> Never skip a row; flag every uncertainty in `uncertainties`. Final message: one line per
> page: `NNN | page_type | rows=K | confidence | notes`.

### JSON schema (summary — authoritative version is docs/SPEC.md)
Each page file: `page_type`, `printed_label` (page number as printed, else null),
`page_confidence` (high|medium|low), `uncertainties` (array of strings), `free_text`
(markdown, for covers/letters), and `rows` (array). Row kinds:
- `{"kind":"group","text":"<trust/portfolio subheader>"}` — emit for every portfolio/trust header.
- `{"kind":"asset", owner, asset_name, value, income_types, other_income_spec,
   amount_of_income, transaction, eif}` — Schedule A holdings.
- `{"kind":"tx", owner, asset_name, tx_type, cap_gain_over_200, partial_sale, date,
   notification_date, amount}` — Schedule B / PTR transactions.
Copy bucket strings VERBATIM from the printed column header that holds the X (older forms word
them differently — do not force 2024 wording). Dates → MM/DD/YYYY.

### Page types you will encounter
- `cover` / `ptr_cover` — put all fields + yes/no answers into `free_text`.
- `letter` — extension requests / gift-waivers: `page_type:"letter"`, `rows:[]`, form → free_text.
- `schedule_a` — holdings grid. Two hard layouts (see below).
- `schedule_b` — transactions (row-per-tx tables OR transposed grids; see below).
- PTRs — transaction lists; page 1 usually `ptr_cover`.

### Two Schedule-A layouts that cause errors (IMPORTANT)
Annual Form-A filings split each asset's attributes across SEPARATE sheets ("field-split"):
one sheet has only Value, another only Type-of-Income, another only Amount+Transaction, for the
SAME asset slice under a trust header. On each such page: record ONLY the block that is present,
set the other fields null, and add `uncertainties[0]` = a layout note naming the block + the
alphabetical asset slice (e.g. "Value block, Ritu Ahuja 1995 Trust, slice A–C") so Phase 2 can
rejoin by name. Capture every asset name even when the checkbox matrix is unreadable.

Transaction Summary codes on annual Schedule A are **P / PS / FS = Purchase / Partial Sale /
Full Sale** (NOT the P/S of PTRs).

### Degraded scans
2019-2 and 2020-14 are heavily degraded (grey stipple / washed out). When a 12-column value or
amount matrix genuinely cannot be pixel-aligned to a bucket, transcribe the asset NAME and set
that bucket field to null with a flag — do NOT guess a column. These get a hi-res re-read in
Phase 2.

### Remaining documents and page gaps
Regenerate the live gap list any time with:
```
cd /Users/multivac/Code/khanna && python3 - <<'EOF'
import glob,re
for path in sorted(glob.glob('docs/[0-9]*-*/pages')):
    d=path.split('/')[1]
    pages=sorted(int(re.search(r'page-(\d+)\.jpg',p).group(1)) for p in glob.glob(f'docs/{d}/pages/page-*.jpg'))
    have={int(re.search(r'page-(\d+)\.json',p).group(1)) for p in glob.glob(f'docs/{d}/text/page-*.json')}
    miss=[p for p in pages if p not in have]
    if miss: print(f"{d}: {len(have)}/{len(pages)} missing {miss[:12]}{'...' if len(miss)>12 else ''}")
EOF
```
As of this writing the remaining work is:
- **2018-4**: pages 159,160,163,164,185–309 (~129 pages). Schedule A field-split → then
  Schedule B (typed tables + transposed grids).
- **2019-2**: pages 173–210 (~38). Schedule B, mostly typed row-per-tx tables (P/PS/FS columns).
- **2019-12, 2019-13, 2019-14**: whole PTR docs (8, 8, 5 pages).
- **2020-14**: pages 96–326 (~231). Transposed Schedule A over heavy stipple (null unreadable
  buckets), later Schedule B.
- **2021-13**: pages 32–303 (~272). Standard Schedule A grids (cleaner). Then all **2021 PTRs**:
  2021-1..12, 2021-14 (2021-12 is a 1p extension letter).
- **2022-15**: pages 14–367 (~354). Then all **2022 PTRs**: 2022-1..14, 2022-16 (2022-14 = 1p
  letter; 2022-6 is 67p, 2022-7 34p, 2022-10 32p — heavy).
- **2023-14**: pages 21–327 (~307). Then all **2023 PTRs**: 2023-1..13, 2023-15 (2023-13 = 1p
  letter).
- **2025-3 … 2025-13**: whole PTR docs (2025-13 = 1p letter). PTR-only year (no annual).
- **2026-1 … 2026-5**: whole PTR docs (~211 pages). PTR-only year.

Some documents filed as "PTR" are actually Form-A **amendments** (asset schedules, not
transactions) — e.g. 2018-2, 2019-1, 2020-15 were. If a "PTR" has holdings with no transaction
dates, use the asset schema; it is browsable but must NOT be aggregated as trades. Note it.

### After each wave
```
cd /Users/multivac/Code/khanna
# delete any truncated JSON from crashed agents, then recompile:
python3 - <<'EOF'
import glob,json,os
for f in glob.glob('docs/*/text/*.json'):
    try: json.load(open(f))
    except: os.remove(f)
EOF
python3 docs/compile17.py            # prints per-year page/asset/tx/confidence/missing_desc
git add -A && git commit -m "OCR: <what advanced>"
```
Commit periodically (every ~15 pages of progress) so a usage-limit interruption loses nothing.

### Operational gotchas
- **Usage limits** (spend and weekly) will interrupt the agent fleet. When they hit: salvage
  (validate JSON, delete corrupt, `compile17.py`, commit), then stop and wait for reset. As of
  handoff the **weekly limit resets 2026-07-12 20:00 PT**.
- Occasional agents die immediately with 0 tool-uses (spurious) — just relaunch that chunk.
- `compile17.py` is resilient to missing pages (they show as `pending`), so it's safe to run
  mid-marathon.

---

## PHASE 2 — Verification pass (only after ALL of 2016–2026 is transcribed)

Full detail is in `docs/VERIFY_NOTES.md`. The five items:

1. **Name-based asset merge for annual Schedule A.** The field-split layout currently produces
   one fragment row per block per asset, inflating counts (2019 shows ~5,335 raw asset rows;
   2020 similar). In `docs/compile17.py`, add a merge that groups asset rows within each annual
   document by (normalized trust group, asset_name) and combines fields (value, income_types,
   other_income_spec, amount_of_income, transaction, eif) from whichever fragment set each.
   This replaces/augments the existing adjacency-based `merge_block_runs`. Re-verify each annual
   year's asset count is sane (no 2×/3× inflation) afterward.
2. **Transaction-code decoder.** In `index.html`, extend the `txWords` map so annual Schedule A
   codes render: P→Purchased, PS→Partial sale, FS→Full sale (keep existing S→Sold,
   S(part)→Partial sale, E→Exchanged).
3. **Hi-res re-read** of the low-confidence pages: the washed-out value/amount matrices in
   2019-2 and 2020-14 (buckets currently null), and any page with `page_confidence: low` or a
   non-empty `uncertainties`. Re-read against the 300 dpi hires (regenerate with the year's
   `docs/prep<year>.sh` / `docs/crop<year>.py` if `hires/` is absent) at higher zoom.
4. **Cross-year consistency + descriptors.** All bucket strings match SPEC enums; trust-group
   aliases normalized (note: the 1993/1994/1995/1998/2004/2005 Ahuja trusts are DISTINCT — do
   not collapse); `docs/descr-missing-*.json` empty (top up `descriptors.json` for any asset
   names lacking a descriptor — no web search, ~50-name batches); standardize the `eif` field
   (some pages set it, some recorded EIF only in `uncertainties`).
5. **Per-year smoke test.** Load each year in the browser: cards, Assets/Transactions tables,
   filters, Document tab, no console errors. PTR-only years (2025, 2026) should show the
   "No annual filing" card and hide the holdings panels.

---

## Pushing to GitHub (do only when the user says to)

The repo tracks ~2 GB of page JPGs. A single `git push` of the whole backlog **fails** with
GitHub HTTP 500/408 on the oversized pack. Push **one commit at a time** instead — each is a
smaller pack GitHub accepts. Run it backgrounded (a big commit's push exceeds a 2-min foreground
timeout), and verify against the TRUE remote (`git ls-remote origin refs/heads/main`), because a
failed push can still report exit 0:
```
cd /Users/multivac/Code/khanna
git config http.postBuffer 2147483648
REMOTE=$(git ls-remote origin refs/heads/main | cut -f1)
for sha in $(git rev-list --reverse ${REMOTE}..HEAD); do
  for a in 1 2 3 4 5; do git push origin ${sha}:refs/heads/main && break || sleep 5; done
done
git ls-remote origin refs/heads/main   # confirm tip == local HEAD
```
Vercel auto-deploys from `origin/main` after the final commit lands.
