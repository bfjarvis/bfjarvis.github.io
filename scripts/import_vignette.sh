#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: scripts/import_vignette.sh /path/to/source.qmd [published-slug]"
  exit 1
fi

source_qmd="$1"
slug="${2:-$(basename "$source_qmd" .qmd)}"
target="vignettes/${slug}.qmd"

if [ ! -f "$source_qmd" ]; then
  echo "Source file not found: $source_qmd"
  exit 1
fi

mkdir -p vignettes
cp "$source_qmd" "$target"
python3 scripts/build_vignette_index.py

echo "Imported $source_qmd -> $target"
echo "Run scripts/render_vignettes.sh when you are ready to render HTML."
