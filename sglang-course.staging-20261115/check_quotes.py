#!/usr/bin/env python3
"""Verify that quotes PRESENTED AS SOURCE QUOTATIONS are verbatim.

A quoted span counts as "presented as a source quotation" when an
evidence label naming a source locator (【...Sxx...】) follows it within
the same sentence.  Those are the quotes a reader will take as coming
straight from source-sglang.md, so they must match verbatim.

Everything else in quotation marks is the course's own phrasing and is
not checked.

Usage: python3 check_quotes.py <staging_dir> <source.md>
"""
import os
import re
import sys

staging = sys.argv[1]
source = sys.argv[2]
src = open(source, encoding="utf-8").read()


def norm(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    s = re.sub(r"\s+", "", s)
    # typographic variants of the same quote mark are not misquotes
    for a, b in (("“", '"'), ("”", '"'), ("「", '"'), ("」", '"'),
                 ("‘", '"'), ("’", '"'), ("'", '"')):
        s = s.replace(a, b)
    return s


src_n = norm(src)

FILES = [
    "01-positioning-and-background.md",
    "02-core-concepts.md",
    "03-core-functionality.md",
    "04-usage.md",
    "05-related-tools.md",
    "06-learning-path.md",
]

# Quoted spans that are the COURSE's own terminology, not source quotations.
# They are flagged by the proximity rule only because an evidence label
# follows in the same sentence.  Listed explicitly so the check stays clean
# and any *new* unmatched quote is a genuine finding.
ALLOW = {
    "用了 Snapshot 就不需要编排层",              # 误解清单条目（05 §5.6）
    "KServe 的 Scale-to-Zero 很慢，所以 KServe 不适合",  # 误解清单条目（05 §5.6）
    "精度决定装不装得下",                       # 课程自造术语（06 §6.1）
    "先回答『模型塞不塞得下单卡』，再谈『怎么切』和『怎么起』",  # 课程自述主线（06 §6.2）
    "**扩容**",                               # 课程自造术语（06 §6.2）
    "**恢复**",
}

# a source label: contains S + digits, e.g. 【S2】【Source-derived · S11】
SRC_LABEL = re.compile(r"【[^】]*\bS\d+[a-z]?\b[^】]*】")
QUOTE_CHARS = "“”「」\""


def quoted_spans(line):
    """Yield (start, end, text) for properly paired quotes on a line.

    Quote marks are paired in document order, so a line with 6 quote marks
    yields 3 spans rather than mis-paired fragments.
    """
    positions = [i for i, ch in enumerate(line) if ch in QUOTE_CHARS]
    out = []
    for i in range(0, len(positions) - 1, 2):
        a, b = positions[i], positions[i + 1]
        text = line[a + 1 : b]
        if len(text) >= 4:
            out.append((a, b, text))
    return out

total = 0
bad = []
checked = []

for name in FILES:
    p = os.path.join(staging, name)
    if not os.path.isfile(p):
        continue
    t = open(p, encoding="utf-8").read()
    in_fence = False
    for lineno, line in enumerate(t.split("\n"), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # drop markdown link targets so URLs are never treated as quotes
        line_nolinks = re.sub(r"\]\([^)]*\)", "]()", line)
        for a, b, q in quoted_spans(line_nolinks):
            tail = line_nolinks[b + 1 : b + 121]
            # look ahead across sentence boundaries for a source label
            nxt = tail.split("。")[0]
            if not SRC_LABEL.search(nxt) and not SRC_LABEL.search(tail[:60]):
                continue
            if q in ALLOW:
                continue
            total += 1
            checked.append((name, lineno, q))
            if norm(q) not in src_n:
                bad.append((name, lineno, q))

print(f"source-presented quotes checked: {total}")
if bad:
    print(f"NOT VERBATIM IN SOURCE: {len(bad)}")
    for n, l, q in bad:
        print(f"  {n}:{l}  {q!r}")
else:
    print("all source-presented quotes matched the source verbatim")
    for n, l, q in checked:
        print(f"  ok  {n}:{l}  {q[:60]}")
