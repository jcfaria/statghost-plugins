#!/usr/bin/env python3
"""Minimal Markdown → HTML for news/News.md (stdlib only; no pandoc).

Same converter shape as sibling statghost/news/_md_to_html_news.py.
Re-run news/sync_news.sh after Markdown edits to regenerate news.html.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

STYLESHEET_HREF = "news.css"


def inline_fixed(s: str) -> str:
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        if s.startswith("[", i):
            m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", s[i:])
            if m:
                label, href = m.group(1), m.group(2)
                out.append(
                    f'<a href="{html.escape(href, quote=True)}">'
                    f"{inline_fixed(label)}</a>"
                )
                i += m.end()
                continue
        if s[i] == "`":
            j = s.find("`", i + 1)
            if j != -1:
                out.append("<code>" + html.escape(s[i + 1 : j]) + "</code>")
                i = j + 1
                continue
        if s.startswith("**", i):
            j = s.find("**", i + 2)
            if j != -1:
                out.append("<strong>" + inline_fixed(s[i + 2 : j]) + "</strong>")
                i = j + 2
                continue
        if s[i] == "*" and not s.startswith("**", i):
            j = s.find("*", i + 1)
            if j != -1 and not s.startswith("**", j):
                out.append("<em>" + inline_fixed(s[i + 1 : j]) + "</em>")
                i = j + 1
                continue
        ch = s[i]
        if ch == "&":
            out.append("&amp;")
        elif ch == "<":
            out.append("&lt;")
        elif ch == ">":
            out.append("&gt;")
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def is_table_sep(line: str) -> bool:
    return bool(
        re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", line)
    )


def md_to_html(md: str, title: str, source_name: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    body: list[str] = []
    i = 0
    n = len(lines)
    in_lede = False
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.strip() == "---":
            body.append("<hr>")
            in_lede = False
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            body.append(f"<h{level}>{inline_fixed(m.group(2))}</h{level}>")
            in_lede = level == 1
            i += 1
            continue
        if re.match(r"^[-*]\s+", line):
            in_lede = False
            items: list[str] = []
            while i < n and re.match(r"^[-*]\s+", lines[i]):
                item = re.sub(r"^[-*]\s+", "", lines[i])
                i += 1
                while i < n and lines[i].strip():
                    cont = lines[i]
                    if re.match(r"^[-*]\s+", cont):
                        break
                    if re.match(r"^(#{1,6})\s+", cont) or cont.strip() == "---":
                        break
                    if cont.startswith("  ") or cont.startswith("\t"):
                        item += " " + cont.strip()
                        i += 1
                        continue
                    break
                items.append(item)
            body.append("<ul>")
            for it in items:
                body.append(f"<li>{inline_fixed(it)}</li>")
            body.append("</ul>")
            continue
        para = [line]
        i += 1
        while (
            i < n
            and lines[i].strip()
            and not re.match(r"^(#{1,6})\s+", lines[i])
            and lines[i].strip() != "---"
            and not re.match(r"^[-*]\s+", lines[i])
            and not (
                lines[i].lstrip().startswith("|")
                and i + 1 < n
                and is_table_sep(lines[i + 1])
            )
        ):
            para.append(lines[i].strip())
            i += 1
        text = " ".join(p.strip() for p in para)
        cls = ' class="lede"' if in_lede else ""
        body.append(f"<p{cls}>{inline_fixed(text)}</p>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{STYLESHEET_HREF}">
</head>
<body>
{chr(10).join(body)}
<footer>Generated from <code>{html.escape(source_name)}</code> — run
<code>news/sync_news.sh</code> after editing the Markdown.</footer>
</body>
</html>
"""


def main() -> int:
    here = Path(__file__).resolve().parent
    md_path = here / "News.md"
    html_path = here / "news.html"
    if not md_path.is_file():
        print(f"missing: {md_path}", file=sys.stderr)
        return 1
    md = md_path.read_text(encoding="utf-8")
    title_m = re.match(r"^#\s+(.+)$", md, re.M)
    title = title_m.group(1).strip() if title_m else "STATghost-plugins — News"
    html_path.write_text(
        md_to_html(md, title, md_path.name), encoding="utf-8", newline="\n"
    )
    print(f"wrote {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
