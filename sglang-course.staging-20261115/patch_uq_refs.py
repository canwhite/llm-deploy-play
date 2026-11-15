#!/usr/bin/env python3
"""Cite each UQ code (and R36) from the course body, so no evidence row is dead."""
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


# --- R36: nvidia-smi topo -m is NVIDIA tooling, not SGLang guidance -----------
patch(
    "01-positioning-and-background.md",
    "源文档在讲 TP 大小时直接假设了",
    "> **这条建议属于 NVIDIA 工具链，不是 SGLang 官方指导**：`nvidia-smi topo -m` 是 NVIDIA 官方的拓扑查看工具【Research-derived · R36】；SGLang 官方文档中**没有**针对 LLM 服务的拓扑测量指引（全库仅在 diffusion cookbook 有一处附带提及）。**这是正确的工程实践，但请把出处记在 NVIDIA 头上。**\n\n源文档在讲 TP 大小时直接假设了",
    "01 R36",
)

# --- UQ8: "PCIe Switch 边界" has no official basis ---------------------------
patch(
    "01-positioning-and-background.md",
    "注意这条铁律的**粒度是 PCIe Switch，不是\"节点\"**。",
    "注意这条铁律的**粒度是 PCIe Switch，不是\"节点\"**（⚠️ 这个具体措辞在官方文档里没有对应表述【UQ8】）。",
    "01 UQ8",
)

# --- UQ1 / UQ10: no official 20x 5090 deployment doc -------------------------
patch(
    "03-core-functionality.md",
    "> **最后一条边界**：**没有任何官方文档描述过 20× RTX 5090 的 SGLang 部署**。SGLang cookbook 对这个模型的部署面板只覆盖**单卡**（H200 / RTX PRO 6000 / RTX 5090 / DGX Spark），其 \"Nodes\" 维度只有 `single` 一个选项【R1】。因此本课程讲的\"20 个副本\"是一个**合理但未经官方验证的推演**【Research-derived · R1】。",
    "> **最后一条边界**：**没有任何官方文档描述过 20× RTX 5090 的 SGLang 部署**。SGLang cookbook 对这个模型的部署面板只覆盖**单卡**（H200 / RTX PRO 6000 / RTX 5090 / DGX Spark），其 \"Nodes\" 维度只有 `single` 一个选项【R1】。因此本课程讲的\"20 个副本\"是一个**合理但未经官方验证的推演**【Research-derived · R1】【UQ1】【UQ10】。",
    "03 UQ1/UQ10",
)

# --- UQ6: 5-node TP4/PP5 layout has no official basis ------------------------
patch(
    "03-core-functionality.md",
    "| **PP 会降低单请求延迟** | PP 让请求流经多个 stage，单请求的端到端延迟高于同规模 DP。源文档选 TP×PP 是因为**模型大到无法不拆**【S7】，不是因为它在延迟上优于 DP。 |",
    "| **PP 会降低单请求延迟** | PP 让请求流经多个 stage，单请求的端到端延迟高于同规模 DP。源文档选 TP×PP 是因为**模型大到无法不拆**【S7】，不是因为它在延迟上优于 DP。 |\n| **这个布局不是官方指导** | SGLang 官方的 PP 示例**一律是 4 个节点**（`--nnodes 4 --tp 8 --pp-size 4`；`--nnodes 4 --tp 4 --pp-size 8`），官方**从未**给出\"一个 stage 一个节点\"或 5 节点的布局建议【R14】。5×(TP4/PP5) 是**合理的工程选择，但不是官方方案**【UQ6】 |",
    "03 UQ6",
)

# --- UQ4: FP8 MoE claim not verified as stated -------------------------------
patch(
    "02-core-concepts.md",
    "> **准确的说法应该是**：在 SM120 上，某些 FP8 / MoE 模型组合**会在启动阶段失败**——FlashInfer 的 TRT-LLM MoE autotune 会抛 `Unsupported architecture`（#40558，仍 OPEN）；而 **block-scaled FP8 在 SM120 上直到 2025-08 才获得支持**（#9233，已关闭）【R33】。",
    "> **准确的说法应该是**：在 SM120 上，某些 FP8 / MoE 模型组合**会在启动阶段失败**——FlashInfer 的 TRT-LLM MoE autotune 会抛 `Unsupported architecture`（#40558，仍 OPEN）；而 **block-scaled FP8 在 SM120 上直到 2025-08 才获得支持**（#9233，已关闭）【R33】【UQ4】。",
    "02 UQ4",
)

# --- UQ3: R-Fork timing has no official benchmark ----------------------------
patch(
    "02-core-concepts.md",
    "但**没有找到官方发布的权重加载耗时对比**。请把它当成**待实测**的假设，而不是既定结论。",
    "但**没有找到官方发布的权重加载耗时对比**，官方评测也只在 8×H20 + DeepSeek-R1 上做过【R24】。请把它当成**待实测**的假设，而不是既定结论【UQ3】。",
    "02 UQ3",
)

# --- UQ8 in 02 --------------------------------------------------------------
patch(
    "02-core-concepts.md",
    "至于\"跨 PCIe Switch 边界\"这个具体措辞，**官方文档里没有对应表述**【R14】。",
    "至于\"跨 PCIe Switch 边界\"这个具体措辞，**官方文档里没有对应表述**【R14】【UQ8】。",
    "02 UQ8",
)

# --- UQ12: mem-fraction fallback 0.88 vs 0.95 --------------------------------
patch(
    "02-core-concepts.md",
    "**官方 FAQ 的建议方向和源文档相反**——它说的是\"**显存不足时可以调小** `--mem-fraction-static`，比如 0.8 或 0.7\"，而不是调大留 KV Cache 空间【R37】。",
    "**官方 FAQ 的建议方向和源文档相反**——它说的是\"**显存不足时可以调小** `--mem-fraction-static`，比如 0.8 或 0.7\"，而不是调大留 KV Cache 空间【R37】。（另注：文档写检测不到显存时回落到 0.88，源码写 0.95，两者不一致——正常情况下能探测到显存，不走回退分支【UQ12】。）",
    "02 UQ12",
)

# --- UQ9: Snapshot does not support multi-node -------------------------------
patch(
    "03-core-functionality.md",
    "| **⚠️ 多 GPU 只支持单节点** | 官方限制原文：\"Workloads, including multi-GPU workloads, must run on a single node. **Multi-node is on the roadmap.**\"【R20】——**跨节点恢复尚未支持** |",
    "| **⚠️ 多 GPU 只支持单节点** | 官方限制原文：\"Workloads, including multi-GPU workloads, must run on a single node. **Multi-node is on the roadmap.**\"【R20】【UQ9】——**跨节点恢复尚未支持**，因此**情况 B 的跨 5 节点 PP 实例整体无法被快照** |",
    "03 UQ9",
)

# --- UQ7: cold-start-elasticity claim is the author's own --------------------
patch(
    "03-core-functionality.md",
    "把它标成\"源文档主张\"比标成\"官方建议\"更诚实。",
    "把它标成\"源文档主张\"比标成\"官方建议\"更诚实【UQ7】。",
    "03 UQ7",
)

# --- UQ5: KServe has no LLM cold-start figure -------------------------------
patch(
    "05-related-tools.md",
    "> **怎么读这张表**：\n> - **\"分钟级\"这个数字，KServe 官方没有发布过**【R28】。",
    "> **怎么读这张表**：\n> - **\"分钟级\"这个数字，KServe 官方没有发布过**【R28】【UQ5】。",
    "05 UQ5",
)

# --- UQ11: sgl-router policy set changed between versions --------------------
patch(
    "05-related-tools.md",
    "**路由策略**【R12】【R15】：`random`、`round_robin`、`power_of_two`、`cache_aware`（默认，维护近似 radix tree 做前缀命中路由）、`bucket`；1.0 后的 `sgl-router` 另有 `session_aware`。",
    "**路由策略**【R12】【R15】：`random`、`round_robin`、`power_of_two`、`cache_aware`（默认，维护近似 radix tree 做前缀命中路由）、`bucket`；1.0 后的 `sgl-router` 另有 `session_aware`。**两代的清单与默认值并不一致**——请以你安装版本的 `--help` 为准【UQ11】。",
    "05 UQ11",
)

# --- UQ2: the exact --quantization value -------------------------------------
patch(
    "04-usage.md",
    "> 另外注意：**NVFP4 的 GEMM 路径需要装 FlashInfer**",
    "> **这个值只能由你现场确定**【UQ2】——它随 SGLang 版本与检查点的导出方式变化，课程不替你选定。\n>\n> 另外注意：**NVFP4 的 GEMM 路径需要装 FlashInfer**",
    "04 UQ2",
)

print(f"applied: {applied}")
if skipped:
    print(f"SKIPPED: {len(skipped)}")
    for f, note, why in skipped:
        print(f"  {f}: {note} ({why})")
