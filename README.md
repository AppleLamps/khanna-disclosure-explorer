# Ro Khanna — Financial Disclosure Explorer (2024)

An independent, searchable transcription of Rep. Ro Khanna's (CA-17) 2024 annual House Financial Disclosure Report, presented as a static website for political transparency.

**Official source filing:** https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2024/9115596.pdf (333-page paper scan, no machine-readable text; a copy is in `disclosures.pdf`).

## Run it

```sh
python3 -m http.server 8742
# open http://localhost:8742/site/index.html
```

Everything is static — `site/index.html` + `site/data.js` + images. Deploy by serving this directory on any static host. Before going live, replace the relative `og:image` / `twitter:image` URLs in `site/index.html` with absolute URLs on your domain.

## What's in the site

- **Overview** — holdings by asset class with statutory range sums (exact min / bounded max), largest holdings, family trusts & partnerships, trading activity
- **Assets** — all Schedule A line-items: search, filters (class, owner, portfolio, value, income type), plain-English "what it is" descriptor per asset, CSV export
- **Transactions** — all Schedule B trades: search, filters, CSV export
- **Document** — the original scan side-by-side with the structured transcription, page by page, with uncertain readings flagged

## How the transcription was made (`ocr/`)

The filing is a pure image scan. Each page was transcribed by a large vision model reading the full page plus four overlapping high-resolution crops (for the fine print and checkbox-column positions), cross-checked against Tesseract OCR, with uncertain readings flagged per cell (`ocr/SPEC.md`). An independent second-pass verification (`ocr/VERIFY.md`) re-reads every page against the first-pass JSON. Per-page structured data lives in `ocr/text/page-NNN.json`; `ocr/compile.py` builds `site/data.js`.

All dollar figures are the statutory range buckets the form requires — the filing never states exact values, and some holdings are reported only as "over $1,000,000" with no upper bound.

## Caveats

- This is an unofficial, best-effort transcription. For authoritative data, consult the original filing.
- The header/social-card photo is Getty Images editorial content (Kevin Dietsch); using it on a public site may require an editorial license.
