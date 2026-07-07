# Verification / finalization checklist (run once 2017–2026 fully transcribed)

Accumulated during the 2018–2026 OCR marathon. The transcribed per-page JSON is
faithful; most items below are compile-time (aggregation/display) fixes that need
the FULL structure of each annual visible, plus targeted re-reads.

## 1. Annual Schedule-A block-split merge — TWO layouts (IMPORTANT)
Form A annuals split each asset's attributes across separate sheets. Two layouts seen:
- **Interleaved triplets** (2018-4): pages go Value, Income, Amount for the SAME asset
  set, repeating. Handled by `merge_block_runs` (consecutive disjoint blocks, same group,
  equal counts) — verified collapsing 3→1 on 2018-4 pp55-57.
- **Grouped-by-block** (2019-2): ALL Value pages, then ALL Income pages, then ALL Amount
  pages, each covering different alphabetical subsets of the same trust. Consecutive pages
  share the SAME block, so `merge_block_runs` does NOT merge them → assets fragment into
  value-only / income-only / amount-only rows and inflate counts.
- **FIX (finalization):** replace/augment with **name-based merge within each annual doc**:
  group asset rows by (normalized trust group, asset_name), then combine fields (value,
  income_types/other_income, amount_of_income[_preceding/current], transaction, eif) from
  whichever fragment set each. This handles BOTH layouts uniformly. Re-verify each annual
  year's asset count is sane (no 2x/3x inflation) after.

## 2. Transaction-code decoding (display)
Annual Schedule-A "Transaction Summary" uses P / PS / FS = Purchase / Partial Sale / Full
Sale (not the standard P/S). Extend index.html `txWords` decoder: P→Purchased,
PS→Partial sale, FS→Full sale (keep existing S→Sold, S(part)→Partial sale, E→Exchanged).

## 3. Re-read low/medium-confidence & flagged pages
- Wide **value-matrix** Schedule A pages (e.g. 2019-2 pp29-30): single X across 12 far-apart
  bucket columns — low confidence on exact bucket. Re-read at higher zoom / pixel-column
  detection.
- Amount-of-income block sheets: recurring "whole block could be one bucket off" calibration
  flag (2018-4 pp87/90 etc.). Standardize the Min/Max header→bucket mapping and re-verify.
- Any page with page_confidence low/medium or non-empty uncertainties.

## 4. Cross-year consistency
- All value/income/amount bucket strings match the SPEC enums (no OCR variants).
- Group aliases normalized (e.g. "Ritu Ahuja 1994 Trust" spelling consistent; the 1994 vs
  1995 trust are distinct — confirmed).
- descriptors.json covers 100% of asset names across ALL years (docs/descr-missing-*.json empty).
- Each year (2016–2026) loads in preview: cards, Assets/Transactions tables, filters,
  Document tab, no console errors. PTR-only years (2025/2026) show the "No annual filing"
  card and hidden holdings panels.
- Some docs filed as "PTR" are actually Form A amendments (2018-2, 2019-1) — transcribed with
  asset schema, browsable, correctly NOT feeding aggregates. Confirm.

## 5. Deploy-size check (at push time)
~11 years of page scans (~4,000 JPGs, multiple GB). Assess git/Vercel size; consider Git LFS
or trimming what deploys before pushing.
