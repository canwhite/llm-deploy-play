#!/usr/bin/env python3
"""Final audit-fix batch: quote fidelity, count consistency, dangling pointers."""
import os
import re
import sys

STAGING = sys.argv[1]
applied, skipped = 0, []
Q = '"“”'


def patch(fname, old, new, note):
    """Exact match; on failure retry with quote glyphs made flexible."""
    global applied
    p = os.path.join(STAGING, fname)
    t = open(p, encoding="utf-8").read()
    if t.count(old) == 1:
        open(p, "w", encoding="utf-8").write(t.replace(old, new))
        applied += 1
        return
    pat = "".join(("[" + Q + "]" if c in Q else re.escape(c)) for c in old)
    t2 = re.sub(pat, lambda m: new, t, count=1)
    if t2 != t:
        open(p, "w", encoding="utf-8").write(t2)
        applied += 1
        return
    skipped.append((fname, note, f"count={t.count(old)}"))


# --- 04: split the R20 quote from the S21 label; fix the non-contiguous splice
patch(
    "04-usage.md",
    '【R20】。源文档把它写成"**生产级**秒级弹性（必选）"【S21】，这个定性与 NVIDIA 自己的措辞不一致。',
    '【R20】。\n>    而源文档把它写成"层次二：生产级秒级弹性——NVIDIA Snapshot（必选）"【S21】——这个定性与 NVIDIA 自己的措辞不一致。',
    "04 R20/S21 quote split",
)

# --- 06: four -> five uncovered items
patch(
    "06-learning-path.md",
    "不覆盖**的四件事",
    "不覆盖**的五件事",
    "06 five items",
)

# --- 06: explain the shorthand label form used throughout the course
patch(
    "06-learning-path.md",
    "`【Source-derived · Sxx】` 来自根文档 `source-sglang.md`；`【Research-derived · Rxx】` 来自外部权威来源；`【Illustrative】` 为教学性构造，不主张 SGLang 的未验证行为。完整定位码与出处见 [07 · 验证记录](07-verification-record.md)。",
    "`【Source-derived · Sxx】` 来自根文档 `source-sglang.md`；`【Research-derived · Rxx】` 来自外部权威来源；`【Illustrative】` 为教学性构造，不主张 SGLang 的未验证行为。完整定位码与出处见 [07 · 验证记录](07-verification-record.md)。\n\n> **正文里的简写**：为便于阅读，正文常把 `【Source-derived · S16】` 简写成 `【S16】`、`【Research-derived · R37】` 简写成 `【R37】`——**两种写法指向同一条定位记录**，完整码与出处见 [07 · 7.2](07-verification-record.md#s-locators) 与 [07 · 7.3](07-verification-record.md#r-locators)。",
    "06 shorthand label note",
)

# --- 01: the 数据与权限 row pointed at 05, which never discusses auth
patch(
    "01-positioning-and-background.md",
    "| **数据与权限** | 没有鉴权、多租户隔离、审计 | [05](05-related-tools.md) 在编排层讨论时点明这一层的职责边界 |",
    "| **数据与权限** | 没有鉴权、多租户隔离、审计 | **本课程不覆盖**——它属于编排层的职责边界；[05](05-related-tools.md) 只定位各编排工具的适用范围，不展开权限模型 |",
    "01 auth pointer",
)

# --- 05: "裸机" is the course's inference, not the source's wording
patch(
    "05-related-tools.md",
    "源文档的“裸机 SSH 起服务”路线",
    "源文档的“逐个 SSH 起服务”路线（源文档原文是“不建议手动逐个SSH启动”）",
    "05 baremetal wording",
)

# --- 04: mark the course-authored replica loop as Illustrative
patch(
    "04-usage.md",
    "```bash\n# 节点内的 4 个副本（node0）——端口需互不冲突",
    "```bash\n# 节点内的 4 个副本（node0）——端口需互不冲突\n# 【Illustrative】本循环是本课程按 S7 的 5 节点 × 4 卡假设构造的，源文档只给单实例命令",
    "04 loop illustrative",
)

print(f"applied: {applied}")
if skipped:
    print(f"SKIPPED: {len(skipped)}")
    for f, note, why in skipped:
        print(f"  {f}: {note} ({why})")
