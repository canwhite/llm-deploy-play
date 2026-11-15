#!/usr/bin/env python3
"""Close the remaining audit findings and correct the §7.5.3 wording."""
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


# === 01-F2: the five-step structure is the course's reading of the source headings
patch(
    "01-positioning-and-background.md",
    "源文档把方案组织成五步【Source-derived · S1】【S25】。",
    "源文档用五个 `###` 标题把方案组织成五步（第一步 L5、第二步 L14、第三步 L43、第四步 L58、第五步 L82）——**“五步”这个归纳是本课程对标题序列的整理**，源文档本身没有“步骤”字样【Illustrative】。",
    "01 five-step provenance",
)

# === 01-F4: the objective promised a comparison with conventional GPU clusters
patch(
    "01-positioning-and-background.md",
    "> 1. 说出 20×RTX 5090 这套硬件与常规 GPU 集群的**三条关键差异**；",
    "> 1. 说出 20×RTX 5090 这套硬件的**三条关键特性**；",
    "01 objective scope",
)
patch(
    "06-learning-path.md",
    "2. 说出 20×RTX 5090 的三条关键硬件差异。",
    "2. 说出 20×RTX 5090 的三条关键硬件特性。",
    "06 objective scope",
)

# === 02-F5: R8 is TensorRT-LLM's format matrix, R30 is SGLang's CLI value names
patch(
    "02-core-concepts.md",
    "在 Blackwell 上两者都受支持【R8】；但**它们的检查点不能互换**。",
    "在 Blackwell 上两者都受 TensorRT-LLM 的格式矩阵支持【R8】——**注意 R8 说的是 TensorRT-LLM 的量化格式矩阵，与 SGLang 命令行的取值名是两回事**（后者见 R30）；两种格式的检查点**不能互换**。",
    "02 R8 vs R30",
)

# === 02-F7: the issue status / date must be traceable to R33
patch(
    "02-core-concepts.md",
    "而 **block-scaled FP8 在 SM120 上直到 2025-08 才获得支持**（#9233，已关闭）【R33】【UQ4】。",
    "而 **block-scaled FP8 在 SM120 上直到 2025-08 才获得支持**（#9233，已关闭）——**这两个状态与日期以 R33 记录的 issue 页面为准**【R33】【UQ4】。",
    "02 issue status",
)

# === 03-F4: per-card GSM8K figures + the unverified "15 combos / five cards"
patch(
    "03-core-functionality.md",
    "| **RTX 5090** | **93.93 – 94.92%**（该卡全部 15 种组合） |",
    "| **RTX 5090** | **93.93 – 94.92%**（该卡的全部组合） |",
    "03 gsm8k combos",
)
patch(
    "03-core-functionality.md",
    "是跨五种硬件的全局区间",
    "是跨全部硬件的全局区间",
    "03 gsm8k hardware count",
)

# === 03-F8: unlabeled TP / PCIe-Domain assertions
patch(
    "03-core-functionality.md",
    "| **节点 ≠ PCIe 域** | 一个节点内的卡可能分属多个 Switch 域。此时 TP 上限是**域内卡数**，不是节点卡数。 |",
    "| **节点 ≠ PCIe 域** | 一个节点内的卡可能分属多个 Switch 域【Illustrative】。此时 TP 上限是**域内卡数**，不是节点卡数【S2】。 |",
    "03 pcie domain labels",
)
patch(
    "03-core-functionality.md",
    "而 PCIe 带宽远低于 NVLink",
    "而 PCIe 带宽远低于 NVLink【S2】",
    "03 pcie bandwidth label",
)

# === 03-F9: the Router naming in the capability table is stale
patch(
    "03-core-functionality.md",
    '| **路由层** | "**SGLang Router（现称Model Gateway）** 是官方推荐的多实例路由方案，支持DP场景下的请求分发"【S23】 |',
    '| **路由层** | "**SGLang Router（现称Model Gateway）** 是官方推荐的多实例路由方案，支持DP场景下的请求分发"【S23】——⚠️ **这是源文档的写法；当前应称 `sgl-router`**，见 [§3.6 ①](#36-第五步编排与路由) |',
    "03 router naming",
)

# === 05-F7: S6 belongs to the Router clause, not to the tool list as a whole
patch(
    "05-related-tools.md",
    "源文档提到了四个工具——SGLang Router、NVIDIA Snapshot、Ray Serve、KServe【S6】【S21】【S23】【S24】【S22】。",
    "源文档提到了四个工具——SGLang Router【S23】【S6】、NVIDIA Snapshot【S21】【S22】、Ray Serve【S24】、KServe【S22】。",
    "05 tool list citations",
)

# === 07 §7.5.3: the claim must say what "处理" actually meant
patch(
    "07-verification-record.md",
    "62 条发现**全部已处理**，无一条留作「已知不修」。整改方式分三类：",
    "62 条发现**全部已处理**，无一条留作「已知不修」。**但要说清楚「处理」的含义**：多数发现不是靠补证据解决的，而是靠**收窄断言**——把源文档没有支撑的说法改写成源文档确实说过的范围，或标为【Illustrative】；只有少数（如同名 R 码的引文与 URL 不符）是真的回到一手来源改正了记录。整改方式分三类：",
    "07 remediation wording",
)

print(f"applied: {applied}")
if skipped:
    print(f"SKIPPED: {len(skipped)}")
    for f, note, why in skipped:
        print(f"  {f}: {note} ({why})")
