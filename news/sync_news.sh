#!/usr/bin/env bash
# Regenerate news/news.html from news/News.md (stdlib Python; no pandoc).
# Usage (from repo root or news/):
#   ./news/sync_news.sh
#   bash news/sync_news.sh
#
# Styling: news.html links to news.css in the same folder.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$ROOT/_md_to_html_news.py"
