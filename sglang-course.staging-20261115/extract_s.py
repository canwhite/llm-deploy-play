#!/usr/bin/env python3
"""Extract exact source excerpts for each S locator, mechanically from the source file.

Usage: python3 extract_s.py <source.md> <s_table.json>
Prints a markdown table row per S entry with a verbatim excerpt.
"""
import json
import sys
import re

src_path, table_path = sys.argv[1], sys.argv[2]
lines = open(src_path, encoding="utf-8").read().split("\n")
entries = json.load(open(table_path, encoding="utf-8"))


def strip_md(s: str) -> str:
    """Remove bold/italic markers and inline code ticks for compact excerpts."""
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    s = re.sub(r"^\s*[*-]\s+", "", s)
    return s.strip()


def md_escape(s: str) -> str:
    """Escape pipes so excerpts survive inside a markdown table cell."""
    return s.replace("|", "\\|")


for e in entries:
    a, b = e["range"]
    chunk = lines[a - 1 : b]
    body = [x for x in chunk if x.strip() and not x.strip().startswith("```")]
    if len(chunk) > 2 and any(x.strip() == "```" for x in chunk):
        # code block: quote first and last meaningful line
        excerpt = f"{strip_md(body[0])}……{strip_md(body[-1])}"
    elif len(body) > 2:
        excerpt = f"{strip_md(body[0])}……{strip_md(body[-1])}"
    else:
        excerpt = " ".join(strip_md(x) for x in body)
        excerpt = re.sub(r"\s+", " ", excerpt)
    rng = f"L{a}" if a == b else f"L{a}–L{b}"
    print(f"| **{e['id']}** | {e['heading']} | {rng} | {md_escape(excerpt)} |")
