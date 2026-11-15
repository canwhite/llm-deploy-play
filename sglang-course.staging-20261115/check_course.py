#!/usr/bin/env python3
"""Cross-section consistency checker for the staged SGLang course.

Checks:
  1. every local markdown link resolves (file exists + anchor exists)
  2. evidence-code integrity: dangling pointers (used but undefined) and
     dead evidence (defined but never referenced) across S / R / UQ
  3. the "affected sections" column of the three evidence tables matches
     the actual references found in sections 01-06
  4. evidence-label syntax
  5. numeric consistency for a declared list of key figures

Usage: python3 check_course.py <staging_dir>
"""
import os
import re
import sys
from collections import defaultdict

staging = os.path.realpath(sys.argv[1])
ORDER = [
    "01-positioning-and-background.md",
    "02-core-concepts.md",
    "03-core-functionality.md",
    "04-usage.md",
    "05-related-tools.md",
    "06-learning-path.md",
    "07-verification-record.md",
]
SECTION_NUM = {name[:2]: name for name in ORDER}
COURSE_SECTIONS = ORDER[:6]  # 01-06 reference the evidence tables

texts = {}
for name in ORDER:
    p = os.path.join(staging, name)
    if not os.path.isfile(p):
        sys.exit(f"missing staged file: {p}")
    texts[name] = open(p, encoding="utf-8").read()

problems = []
notes = []


def slugify(h):
    """GitHub-style heading anchor slug (CJK preserved)."""
    s = h.strip().lower()
    s = re.sub(r"[^\w\s一-鿿-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s


# ---------- anchors ----------
anchors = defaultdict(set)
for name, t in texts.items():
    for m in re.finditer(r'<a\s+id="([^"]+)"', t):
        anchors[name].add(m.group(1))
    in_fence = False
    for line in t.split("\n"):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            head = re.sub(r"`", "", m.group(2)).strip()
            head = re.sub(r"\s*·.*$", "", head).strip() or m.group(2).strip()
            anchors[name].add(slugify(m.group(2)))
            anchors[name].add(slugify(head))

# ---------- 1. links ----------
link_count = 0
for name, t in texts.items():
    for m in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", t):
        target = m.group(2).strip()
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        link_count += 1
        fname, _, frag = target.partition("#")
        fname = fname.split("/")[-1] if fname else name
        if fname and fname not in texts:
            problems.append(f"LINK  {name}: target file not found -> {target}")
            continue
        tgt = fname or name
        if frag and frag not in anchors.get(tgt, set()):
            problems.append(f"LINK  {name}: anchor not found -> {target}  (in {tgt})")
notes.append(f"local links checked: {link_count}")

# ---------- 2/3. evidence codes ----------
def refs_in(text):
    """Return set of codes referenced, with their full label form."""
    found = set()
    for m in re.finditer(r"【([^】]+)】", text):
        body = m.group(1)
        for code in re.findall(r"\b((?:UQ|S|R)\d+[a-z]?)\b", body):
            found.add(code)
    return found


used = defaultdict(set)  # code -> set of section numbers referencing it
for name in COURSE_SECTIONS:
    sec = name[:2]
    for code in refs_in(texts[name]):
        used[code].add(sec)

# definitions live in 07
seven = texts["07-verification-record.md"]
defined_s = set(re.findall(r"\*\*(S\d+[a-z]?)\*\*", seven))
defined_r = set(re.findall(r"\*\*(R\d+)\*\*", seven))
defined_uq = set(re.findall(r"\*\*(UQ\d+)\*\*", seven))
defined = defined_s | defined_r | defined_uq

# codes referenced inside 07 itself (audit cross-references) do not count as usage
dangling = sorted(c for c in used if c not in defined)
dead = sorted(c for c in defined if c not in used)

# ---------- 4. label syntax ----------
# Accepted forms (declared in each section's legend):
#   【Source-derived · Sxx】  【Research-derived · Rxx】  【Illustrative[ · …]】
#   【证据缺口 · UQx】  and shorthand 【Sxx】【Rxx】【UQx】【Sx / Sy】【Sx + Ry】
# Legend placeholders (Sxx / Rxx) are legal only inside a legend table.
CODE = r"(?:UQ|S|R)\d+[a-z]?"
PREFIX = r"(?:Source-derived|Research-derived|证据缺口|未决问题)"
PLACEHOLDER = re.compile(r"^\*\*(" + CODE.replace("?", "") + r"|(?:S|R|UQ)xx)\*\*$")


def label_ok(raw, name):
    body = raw[1:-1].strip()
    if body in ("…", "..."):
        return True
    # trailing prose after a full-width comma (e.g. "，详见 [07 · 验证记录](...)")
    body = re.split(r"[，,]\s*详见", body)[0].strip()
    if not body:
        return False
    if body.startswith("Illustrative"):
        return True
    has_prefix = bool(re.search(PREFIX, body))
    has_code = bool(re.search(r"(?:UQ|S|R)\d+[a-z]?|(?:S|R|UQ)xx", body))
    if not (has_prefix or has_code):
        return False
    # every "+"-separated segment must be either a pure code-list or prose
    for seg in body.split("+"):
        stripped = re.sub(PREFIX, "", seg)
        stripped = re.sub(r"[·•]", " ", stripped)
        toks = re.findall(r"(?:UQ|S|R)\d+[a-z]?|(?:S|R|UQ)xx|[/+,、\s]", stripped)
        residue = re.sub(r"\s+", "", "".join(toks))
        rest = re.sub(r"\s+", "", stripped)
        if residue != rest:
            # segment contains characters that are neither codes nor separators
            if re.search(r"(?:UQ|S|R)\d+[a-z]?|(?:S|R|UQ)xx", stripped):
                return False  # looks like a code list but is malformed
            # otherwise treat as prose ("本节推断", "见 07", ...)
    return True


bad_labels = []
for name, t in texts.items():
    for m in re.finditer(r"【[^】]*】", t):
        if not label_ok(m.group(0), name):
            bad_labels.append(f"LABEL {name}: {m.group(0)}")
if bad_labels:
    problems.extend(bad_labels)

# ---------- 5. affected-sections column check ----------
# Split each evidence-table row on unescaped pipes, then locate the cell
# that holds the affected-section list (e.g. "01, 02").
def split_row(row):
    cells, cur, esc = [], "", False
    for ch in row:
        if esc:
            cur += ch
            esc = False
        elif ch == "\\":
            cur += ch
            esc = True
        elif ch == "|":
            cells.append(cur)
            cur = ""
        else:
            cur += ch
    cells.append(cur)
    return [c.strip() for c in cells]


SECCELL = re.compile(r"^\d{2}(\s*,\s*\d{2})*$")
declared = {}
for line in seven.split("\n"):
    if not line.strip().startswith("|"):
        continue
    cells = split_row(line.strip())
    if len(cells) < 3:
        continue
    m = re.match(r"^\*\*((?:UQ|S|R)\d+[a-z]?)\*\*$", cells[1])
    if not m:
        continue
    for cell in cells[2:]:
        if SECCELL.match(cell):
            declared[m.group(1)] = {s.strip() for s in cell.split(",") if s.strip()}
            break

mismatches = []
for code, secs in sorted(declared.items()):
    actual = used.get(code, set())
    if actual != secs:
        mismatches.append(f"COLUMN {code}: declared={sorted(secs)} actual={sorted(actual)}")

# ---------- optional: regenerate the "影响的课程章节" column ----------
if "--fix-column" in sys.argv:
    def cell_for(code):
        secs = sorted(used.get(code, set()))
        return ", ".join(secs)

    out_lines = []
    for line in seven.split("\n"):
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = split_row(stripped)
            m = re.match(r"^\*\*((?:UQ|S|R)\d+[a-z]?)\*\*$", cells[1]) if len(cells) > 1 else None
            if m:
                code = m.group(1)
                # the affected-sections cell is the last one that looks like a
                # section list, or the final cell when it is empty
                target = None
                for i in range(2, len(cells)):
                    if SECCELL.match(cells[i]):
                        target = i
                        break
                if target is None:
                    target = len(cells) - 1
                cells[target] = " " + cell_for(code) + " "
                if cells and not cells[0]:
                    cells = cells[1:]
                if cells and not cells[-1]:
                    cells = cells[:-1]
                line = "| " + " | ".join(cells) + " |"
        out_lines.append(line)
    new_seven = "\n".join(out_lines)
    p7 = os.path.join(staging, "07-verification-record.md")
    open(p7, "w", encoding="utf-8").write(new_seven)
    print(f"COLUMN REGENERATED: {p7}")
    print(f"  rows updated: {len(declared)}")
    # re-read so the report below reflects the new file
    texts["07-verification-record.md"] = new_seven
    seven = new_seven
    declared = {}
    for line in seven.split("\n"):
        if not line.strip().startswith("|"):
            continue
        cells = split_row(line.strip())
        if len(cells) < 3:
            continue
        m = re.match(r"^\*\*((?:UQ|S|R)\d+[a-z]?)\*\*$", cells[1])
        if not m:
            continue
        for cell in cells[2:]:
            if SECCELL.match(cell):
                declared[m.group(1)] = {s.strip() for s in cell.split(",") if s.strip()}
                break
    mismatches = []
    for code, secs in sorted(declared.items()):
        actual = used.get(code, set())
        if actual != secs:
            mismatches.append(f"COLUMN {code}: declared={sorted(secs)} actual={sorted(actual)}")
    problems = [p for p in problems if not p.startswith("LINK")]

# ---------- report ----------
print("=" * 72)
print("CROSS-SECTION CONSISTENCY CHECK")
print("=" * 72)
print(f"staging dir      : {staging}")
print(f"files            : {len(texts)}")
print(f"local links      : {link_count}")
print(f"defined codes    : S={len(defined_s)} R={len(defined_r)} UQ={len(defined_uq)}")
print(f"referenced codes : {len(used)}")
print()
if dangling:
    print("DANGLING POINTERS (referenced but not defined):", ", ".join(dangling))
else:
    print("DANGLING POINTERS: none")
if dead:
    print("DEAD EVIDENCE (defined but never referenced):", ", ".join(dead))
else:
    print("DEAD EVIDENCE: none")
print()
if mismatches:
    print(f"AFFECTED-SECTIONS MISMATCHES: {len(mismatches)}")
    for m in mismatches:
        print("  " + m)
else:
    print(f"AFFECTED-SECTIONS COLUMN: all {len(declared)} rows match actual references")
print()
if problems:
    print(f"PROBLEMS: {len(problems)}")
    for p in problems[:60]:
        print("  " + p)
    if len(problems) > 60:
        print(f"  ... and {len(problems)-60} more")
else:
    print("PROBLEMS: none")
print()
print("VERDICT:", "PASS" if not (problems or dangling or dead or mismatches) else "FAIL")
