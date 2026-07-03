#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

find blog -maxdepth 1 -name "*.qmd" ! -name "_*" -print0 |
  while IFS= read -r -d "" qmd; do
    quarto render "$qmd"
  done

python3 scripts/build_blog_index.py
