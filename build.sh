#!/usr/bin/env bash
# Cloudflare Pages build entrypoint - stdlib Python only, no pip installs needed.
set -e
# Reassemble any split files (committed in parts to keep commits small)
if ls data/source_*.b64part >/dev/null 2>&1; then
  cat data/source_*.b64part > data/source.json.gz.b64
fi
for stem in gen/build.py gen/homes_page.py; do
  if ls ${stem}.part* >/dev/null 2>&1; then
    cat ${stem}.part* > ${stem}
  fi
done
python3 gen/build.py
