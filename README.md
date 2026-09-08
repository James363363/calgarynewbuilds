# calgarynewbuilds.ca

Independent directory of every actively selling new-construction community in Calgary, Alberta —
59 communities, 60+ builders, ~350 current product lines, on one map.

**Live site:** https://calgarynewbuilds.ca

## How it works

This repo holds the site *generator*, not the built pages. Cloudflare Pages runs the build on every push:

- **Build command:** `bash build.sh`  (Python standard library only — no dependencies)
- **Build output directory:** `site`

`gen/build.py` renders 64 static pages (homepage with quadrant map, 59 community pages, the
filterable Browse Homes app, builders directory, about page, sitemap, robots.txt) from
`data/source.json.gz.b64` — a gzip+base64 snapshot extracted from the master Excel workbook
(`Calgary_New_Build_Options_MASTER.xlsx`, kept offline).

## Updating the data

1. Edit the master workbook locally.
2. Regenerate the snapshot (needs `pandas` + `openpyxl` locally, not in CI):
   ```python
   import sys; sys.path.insert(0, 'gen')
   from data import extract_from_xlsx, save_source
   save_source(extract_from_xlsx('path/to/Calgary_New_Build_Options_MASTER.xlsx'))
   ```
3. Re-split it (`split -n 5 -d --additional-suffix=.b64part data/source.json.gz.b64 data/source_`),
   commit the parts, and push — Cloudflare Pages rebuilds automatically.

Large generator files are likewise committed as `.partN` pieces; `build.sh` reassembles them.

Data verified from builder/developer websites July 30–31, 2026. Prices change without notice;
this site is not affiliated with any builder or developer.
