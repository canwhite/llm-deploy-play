#!/usr/bin/env python3
"""Fix anchor targets: add explicit <a id> anchors and repoint links."""
import os
import sys

STAGING = sys.argv[1]
applied = 0
skipped = []


def patch(fname, old, new, note):
    global applied
    p = os.path.join(STAGING, fname)
    t = open(p, encoding="utf-8").read()
    n = t.count(old)
    if n != 1:
        skipped.append((fname, note, f"count={n}"))
        return
    open(p, "w", encoding="utf-8").write(t.replace(old, new))
    applied += 1


# --- 05: explicit anchors for the three sub-sections ------------------------
patch(
    "05-related-tools.md",
    "### 5.2.2 NVIDIA Snapshot —— 弹性层",
    '<a id="522-nvidia-snapshot"></a>\n\n### 5.2.2 NVIDIA Snapshot —— 弹性层',
    "05 anchor 522",
)
patch(
    "05-related-tools.md",
    "### 5.2.3 Ray Serve —— 编排层",
    '<a id="523-ray-serve"></a>\n\n### 5.2.3 Ray Serve —— 编排层',
    "05 anchor 523",
)
patch(
    "05-related-tools.md",
    "### 5.2.4 KServe —— 编排层（被负面对比）",
    '<a id="524-kserve"></a>\n\n### 5.2.4 KServe —— 编排层（被负面对比）',
    "05 anchor 524",
)

# --- 05: repoint internal links -------------------------------------------
patch(
    "05-related-tools.md",
    "[5.2.4](#524-kserve--编排层被负面对比)",
    "[5.2.4](#524-kserve)",
    "05 internal link 524",
)
patch(
    "05-related-tools.md",
    "[5.2.3](#523-ray-serve--编排层)",
    "[5.2.3](#523-ray-serve)",
    "05 internal link 523",
)

# --- 02: cross-file link to 05 --------------------------------------------
patch(
    "02-core-concepts.md",
    "[05 · 5.2.2](05-related-tools.md#52-nvidia-snapshot--弹性层)",
    "[05 · 5.2.2](05-related-tools.md#522-nvidia-snapshot)",
    "02 link to 05",
)

# --- 06: same-file link that actually points at 05 ------------------------
patch(
    "06-learning-path.md",
    "[05 · 5.7](#57-三条最实质的落差)",
    "[05 · 5.7](05-related-tools.md#57-三条最实质的落差)",
    "06 link to 05",
)

print(f"applied: {applied}")
if skipped:
    print(f"SKIPPED: {len(skipped)}")
    for f, note, why in skipped:
        print(f"  {f}: {note} ({why})")
