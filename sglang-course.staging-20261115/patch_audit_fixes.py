#!/usr/bin/env python3
"""Apply the 62 post-mortem audit findings to the staged SGLang course.

Exact match first; if that fails, retry with quote glyphs made flexible
(the source files mix U+201C/U+201D and ASCII ").
"""
import os
import re
import sys

STAGING = sys.argv[1]
applied, skipped = 0, []
Q = '"“”'


def patch(fname, old, new, note):
    global applied
    p = os.path.join(STAGING, fname)
    t = open(p, encoding="utf-8").read()
    if t.count(old) == 1:
        open(p, "w", encoding="utf-8").write(t.replace(old, new))
        applied += 1
        return
    # quote-glyph tolerant retry
    pat = "".join(("[" + Q + "]" if c in Q else re.escape(c)) for c in old)
    new_pat = new
    t2 = re.sub(pat, lambda m: new_pat, t, count=1)
    if t2 != t:
        open(p, "w", encoding="utf-8").write(t2)
        applied += 1
        return
    skipped.append((fname, note, f"count={t.count(old)}"))


# ============================================================ 01
F = "01-positioning-and-background.md"
patch(F, "> 1. 说出 20×RTX 5090 这套硬件与常规 GPU 集群的**三条关键差异**；",
      "> 1. 说出 20×RTX 5090 这套硬件的**三条关键特性**；", "01 goal")
patch(F, "它面向**一台拥有 20 张 RTX 5090 的集群**",
      "它面向**一套 20 张 RTX 5090 的集群**", "01 one-cluster")
patch(F, "| 1 | **单卡显存 32GB** | 大多数主流稠密模型以 BF16 权重**装不进单卡**，必须降精度或跨卡切分 | 【S11】【S5】【R6】 |",
      "| 1 | **单卡显存 32GB** | 源文档选定的 27B 模型以 BF16 权重**装不进单卡**，必须降精度或跨卡切分 | 【S11】【S5】【R6】 |",
      "01 bf16 scope")
patch(F, "| 3 | **节点间只有普通网络** | 跨节点通信必须走 InfiniBand 或高速 RoCE 这类外部网络 | 【S24】 |",
      "| 3 | **节点间网络** | 源文档把 InfiniBand 或高速 RoCE 列为**前提条件**（Ray Serve 生效的前提），**并未断言**本集群没有它们 | 【S24】 |",
      "01 network conditional")
patch(F, "注意这条铁律的**粒度是 PCIe Switch，不是“节点”**（⚠️ 这个具体措辞在官方文档里没有对应表述【UQ8】）。",
      "注意这条铁律**同时**禁止跨节点与跨 PCIe Switch；⚠️ 其中“跨 PCIe Switch 边界”这一具体措辞在官方文档里没有对应表述【UQ8】。",
      "01 pcie wording")
patch(F, "源文档把方案组织成五步【Source-derived · S1】【S25】。",
      "源文档用 `###` 标题把方案组织成五步（第一步 L5、第二步 L14、第三步 L43、第四步 L58、第五步 L82）——**这五行的归纳是本课程的结构化整理**，源文档本身没有“五步”这个总标题【Illustrative】。",
      "01 five steps")

# ============================================================ 02
F = "02-core-concepts.md"
patch(F, "| **TP**（张量并行） | 模型层**内**的权重 | 每一层的前向/反向都要做 **All-Reduce** | **每层** | **不可**——不能跨节点或跨 PCIe Switch【S2】 |",
      "| **TP**（张量并行） | 模型层**内**的权重 | 每一层的前向/反向都要做 **All-Reduce**【Illustrative】 | **每层**【Illustrative】 | **不可**——不能跨节点或跨 PCIe Switch【S2】 |",
      "02 tp allreduce label")
patch(F, "数据并行一侧同样有官方表述：每个副本持有一份完整模型副本，**请求推理过程中副本之间零通信**【Research-derived · R12】。",
      "数据并行一侧，源文档自己的说法是“GPU 之间零通信开销”【Source-derived · S5】；SGLang 官方文档同时提醒 **native DP “highly not recommended”**，生产级 DP 建议走 Model Gateway【Research-derived · R12】。",
      "02 dp zero comm")
patch(F, "> **注意它和 MXFP4 不是一回事**。MXFP4 是 OCP 开放标准，用 **32** 元素分块 + E8M0 scale；NVFP4 用 **16** 元素分块 + E4M3 scale【R5】。在 Blackwell 上两者都受支持【R8】，但**它们的检查点不能互换**。",
      "> **注意它和 MXFP4 不是一回事**。NVFP4 用 **16** 元素分块 + E4M3 scale【R5】；MXFP4 是另一套分块规则（OCP 开放标准，**32** 元素分块 + E8M0 scale）——**这段对比是本课程的补充说明**【Illustrative】。在 Blackwell 上两者都受支持【R8】；但**它们的检查点不能互换**。",
      "02 mxfp4")
patch(F, "> - **`--mem-fraction-static` 的默认值不是 0.85，而是“自动计算”**。官方文档原文：“When unset, it is computed as `(GPU memory - reserved memory) / GPU memory`, defaulting to `0.88` if GPU memory cannot be detected”；源码里的定义是 `mem_fraction_static = (GPU memory capacity - activations - cuda graph buffers) / GPU memory capacity`【Research-derived · R37】。**官方 FAQ 的建议方向和源文档相反**——它说的是“**显存不足时可以调小** `--mem-fraction-static`，比如 0.8 或 0.7”，而不是调大留 KV Cache 空间【R37】。（另注：文档写检测不到显存时回落到 0.88，源码写 0.95，两者不一致——正常情况下能探测到显存，不走回退分支【UQ12】。）",
      "> - **`--mem-fraction-static` 的默认值不是 0.85，而是“自动计算”**。官方文档原文：“When unset, it is computed as `(GPU memory - reserved memory) / GPU memory`, defaulting to `0.88` if GPU memory cannot be detected”【Research-derived · R37】。**官方 FAQ 的建议方向和源文档相反**——它说的是“**显存不足时可以调小** `--mem-fraction-static`，比如 0.8 或 0.7”，而不是调大留 KV Cache 空间【Research-derived · R38】。（另注：文档写检测不到显存时回落到 0.88，源码的兜底分支写 0.95，两者不一致——正常情况下能探测到显存，不走回退分支【UQ12】。）",
      "02 mem-fraction quote")
patch(F, "R-Fork 能把“数分钟”压到“数秒”，但它**压不掉图编译**。",
      "R-Fork 能把“数分钟”压到“数秒”，但它**压不掉图编译**——后者是本课程依据 S17“只搬权重”的描述所做的推断【Illustrative】。",
      "02 rfork inference")
patch(F, "| **TP**（张量并行） | 把同一层权重切开，每层都要 All-Reduce | 【S2】【S3】 |",
      "| **TP**（张量并行） | 把同一层权重切开，每层都要 All-Reduce【Illustrative】 | 【S2】【S3】 |",
      "02 term tp")
patch(F, "| **MXFP4** | OCP 开放标准的 4-bit 格式（32 元素分块），**与 NVFP4 不可互换** | 【R5】 |",
      "| **MXFP4** | 另一套 4-bit 分块格式（32 元素分块 + E8M0 scale），**与 NVFP4 不可互换** | 【Illustrative】【R8】 |",
      "02 term mxfp4")

# ============================================================ 03
F = "03-core-functionality.md"
patch(F, "| **PP 会降低单请求延迟** | PP 让请求流经多个 stage，单请求的端到端延迟高于同规模 DP。源文档选 TP×PP 是因为**模型大到无法不拆**【S7】，不是因为它在延迟上优于 DP。 |",
      "| **PP 会降低单请求延迟** | PP 让请求流经多个 stage，单请求的端到端延迟高于同规模 DP——**这半句是本课程的常识性判断，源文档未作延迟断言**【Illustrative】。源文档选 TP×PP 是因为**模型大到无法不拆**【S7】，不是因为它在延迟上优于 DP。 |",
      "03 pp latency")
patch(F, "**型号真实存在，格式真实存在，但“官方验证”与“分数含义”两处需要修正**。",
      "**型号真实存在，格式真实存在，但“官方验证”归因、“W4A4”精度口径、“分数含义”三处需要修正**。",
      "03 three fixes")
patch(F, "| 模型是 **Qwen3.8-27B** | ✅ **真实存在**。`Qwen/Qwen3.8-27B` 与 `Qwen/Qwen3.8-27B-FP8` 均为官方发布（2026-08-14 上线） | 【R2】【R4】 |",
      "| 模型是 **Qwen3.8-27B** | ✅ **真实存在**。`Qwen/Qwen3.8-27B` 是官方发布（模型卡 created 2026-08-05；仓库公告 2026-08-14 上线） | 【R2】【R4】 |",
      "03 model repos")
patch(F, "这 **202 个格子**是「检查点精度 × 投机解码选项 × 服务策略 × SSM 状态 dtype」的组合，每个格子都在完整的 1319 道题上跑一遍。",
      "这 **202 个格子**是「检查点精度 × 投机解码选项 × 服务策略 × SSM 状态 dtype」的组合，每个格子都在完整的 1319 道题上跑一遍——**四因子的拆法是本课程对 202 这个数字的解读，cookbook 只给了 202 / 1319 / 区间三个事实**【Illustrative】。",
      "03 202 cells")
patch(F, "> **一个必须说清的口径差异**：cookbook 的 “NVFP4 weights ~16.5GB” 与 HF 上该检查点的**磁盘体积**（约 20.4–21.9GB）**对不上**——前者更像是不含 FP4 scale 开销、vision tower 与 MTP head 的**纯权重/运行时口径**。**这两个数字不能混用**【R1】。",
      "> **一个必须说清的口径差异**：cookbook 给的是 **“NVFP4 weights ~16.5GB”**（权重体积口径）【R1】，而 Hugging Face 仓库页面显示的是**整个仓库的下载体积**（含 FP4 scale、vision tower、MTP head 等其他文件）。**这两个数字口径不同，不能混用**；HF 端的实际数值请以仓库文件列表为准【R3】。",
      "03 weight size")
patch(F, "源文档说的“调大到 0.85~0.90 为 KV Cache 留足空间”【S15】是一种**手动固定**的做法",
      "源文档直接给出 `0.85 ~ 0.90`，**并未说明方向**【S15】；把它读成“调大”是本课程的判断【Illustrative】。无论方向如何，这种**手动固定**的做法",
      "03 tune-up wording")
patch(F, "| 数字 3.6–42.7s / 8–36× | ✅ **完全属实**。官方博客与 `docs/overview/performance.md` 一致，且**区间的两个端点都是 SGLang 的行**（下界 Qwen3-0.6B/SGLang/TP1 = 3.59s；上界 DeepSeek-V4-Pro-NVFP4/SGLang/TEP8 = 42.69s） | 【R19】【R26】 |",
      "| 数字 3.6–42.7s / 8–36× | ✅ **属实**。官方博客口径为 8×–36×【R19】；`docs/overview/performance.md` 的口径为 **8.1–35.9×**【R26】——**两处都成立，数值略有出入**，引用时请说明用的是哪一个口径 |",
      "03 snapshot numbers")
patch(F, "**③ 路由策略有官方清单**【R12】【R15】：`random`、`round_robin`、`power_of_two`、`cache_aware`（默认）、`bucket`；1.0 之后的 `sgl-router` 还提供 `session_aware`。",
      "**③ 路由策略有官方清单**【R12】【R15】：`random`、`round_robin`、`power_of_two`、`cache_aware`（0.x 默认）、`bucket`；1.0 之后的 `sgl-router` 还提供 `session_aware`，且**默认策略改为 `power_of_two`**。**两代的清单与默认值并不一致**——以你安装版本的 `--help` 为准【UQ11】。",
      "03 router policies")

# ============================================================ 04
F = "04-usage.md"
patch(F, "> 4. 识别三类最常见的启动故障，并知道先查哪一项。",
      "> 4. 识别常见启动故障，并知道先查哪一项。", "04 goal")
patch(F, "## 4.0 开工前：确认三件事",
      '<a id="40-preflight"></a>\n\n## 4.0 开工前：确认五件事', "04 preflight heading")
patch(F, "⚠️ SM120 上官方允许 `triton` 或 `flashinfer`；FlashInfer 是默认值不是强制项【R32】",
      "⚠️ SM120 上官方允许 `triton` 或 `flashinfer`【R32】——**不是强制项**（官方文档里“自动选 FlashInfer”那句话只适用于 SM100/SM103，不适用 SM120）", "04 flashinfer default")
patch(F, "`--dist-init-addr`（别名 `--nccl-init-addr`）、", "`--dist-init-addr`、", "04 nccl alias")
patch(F, "| `--quantization nvfp4` | Blackwell 量化要求 | 【S11】 |",
      "| `--quantization <NVFP4 取值>` | Blackwell 量化要求（**源文档首选**，不是硬性要求）；⚠️ `nvfp4` 不是合法取值 | 【S11】【R30】 |", "04 param table")
patch(F, "python3 -m sglang.launch_server [args]",
      "python -m sglang.launch_server [args]", "04 seed python")
patch(F, "**可选路由策略**：`random`、`round_robin`、`power_of_two`、`cache_aware`（默认）、`bucket`；1.0 之后的 `sgl-router` 还提供 `session_aware`【R12】【R15】。",
      "**可选路由策略**：`random`、`round_robin`、`power_of_two`、`cache_aware`（0.x 默认）、`bucket`；1.0 之后的 `sgl-router` 还提供 `session_aware`，且**默认策略改为 `power_of_two`**【R12】【R15】。**两代的清单与默认值并不一致**——以你安装版本的 `--help` 为准【UQ11】。", "04 router policies")
patch(F, "- [ ] Router 的**后端地址清单**能覆盖全部 20 个副本（DP）或 5 个 PP 组（情况 B）——源文档的架构图正是这样区分的【S25】；",
      "- [ ] Router 的**后端地址清单**能覆盖全部 20 个副本（DP）；情况 B 下，每个 PP 组需**对外暴露为一个可路由实例**，共 5 个 engine 端点——源文档的架构图正是这样区分的【S25】【R15】；", "04 pp groups")
patch(F, "## 4.8 三类最常见的启动故障",
      '<a id="48-startup-faults"></a>\n\n## 4.8 常见启动故障排查顺序', "04 fault heading")
patch(F, "- **五类故障的排查顺序**：共享内存 → 量化格式 → 显存预算 → R-Fork 前提 → 快照前提。",
      "- **七类故障的排查顺序**：共享内存 → 量化格式 → 显存预算 → R-Fork 前提 → 快照前提 → **参数取值被拒** → **TP 无限挂起**。", "04 fault summary")

# ============================================================ 05
F = "05-related-tools.md"
patch(F, "**路由策略**【R12】【R15】：`random`、`round_robin`、`power_of_two`、`cache_aware`（默认，维护近似 radix tree 做前缀命中路由）、`bucket`；1.0 后的 `sgl-router` 另有 `session_aware`。",
      "**路由策略**【R12】【R15】：`random`、`round_robin`、`power_of_two`、`cache_aware`（0.x 默认，维护近似 radix tree 做前缀命中路由）、`bucket`；1.0 后的 `sgl-router` 另有 `session_aware`，且**默认策略改为 `power_of_two`**。", "05 router policies")
patch(F, "**外部核对：数字与后端支持都成立，但有四条限制源文档没提**【R19】【R20】【R26】：",
      "**外部核对：数字与后端支持都成立，但有两处限制源文档没提**【R19】【R20】【R26】：", "05 four limits")
patch(F, "| 数字 3.6–42.7s / 8–36× | ✅ **完全属实**。官方博客与 `docs/overview/performance.md` 一致，且**区间的两个端点都是 SGLang 的行**（下界 Qwen3-0.6B/SGLang/TP1 = 3.59s；上界 DeepSeek-V4-Pro-NVFP4/SGLang/TEP8 = 42.69s） |",
      "| 数字 3.6–42.7s / 8–36× | ✅ **属实**。官方博客口径为 8×–36×【R19】；`docs/overview/performance.md` 的口径为 **8.1–35.9×**【R26】——**两处都成立，数值略有出入**，引用时请说明用的是哪一个口径 |", "05 snapshot numbers")
patch(F, "源文档是**一份部署方案，不是选型报告**——它假定引擎选型已完成。本节补上同层的其他选项，供你自己评估。**这些工具在源文档中完全未被提及**。",
      "源文档是**一份部署方案，不是选型报告**——它假定引擎选型已完成。本节补上同层的其他选项，供你自己评估。**§5.3.1 的两个引擎在源文档中完全未被提及；§5.3.2 的两项则是源文档已锁定的强制配置项，此处只补外部核对。**", "05 scope")
patch(F, "| **vLLM** | 同样定位为高吞吐 LLM 推理引擎，同样提供 OpenAI 兼容 API，同样支持 TP/PP 与多 GPU 部署 | 两者的调度器与特性集不同；**本课程不对二者做性能优劣断言**——没有同硬件同负载的公开对比数据 |",
      "| **vLLM** | 同样定位为高吞吐 LLM 推理引擎，同样提供 OpenAI 兼容 API，同样支持 TP/PP 与多 GPU 部署【Illustrative】 | 两者的调度器与特性集不同；**本课程不对二者做性能优劣断言**——没有同硬件同负载的公开对比数据 |", "05 vllm label")
patch(F, "| **TensorRT-LLM** | 同样面向生产推理，同样支持多 GPU 与量化 | 更贴近 NVIDIA 自家栈（与 TensorRT、TensorRT Model Optimizer 集成更紧） |",
      "| **TensorRT-LLM** | 同样面向生产推理，同样支持多 GPU 与量化【Illustrative】 | 更贴近 NVIDIA 自家栈（与 TensorRT、TensorRT Model Optimizer 集成更紧）【Illustrative】 |", "05 trtllm label")
patch(F, "| ⑤ 弹性 | **NVIDIA Snapshot** | 秒级恢复 | **可叠加**：为 SGLang 后端 | 缩容到零、滚动升级、故障恢复；**要求 K8s 且单节点**【R20】 |",
      "| ⑤ 弹性 | **NVIDIA Snapshot** | 秒级恢复 | **依赖**：SGLang 后端 | 缩容到零、滚动升级、故障恢复；**要求 K8s 且单节点**【R20】 |", "05 snapshot layer")
patch(F, "> - **可叠加**（④⑤）：随时可以加进来或拿掉，不影响 ②③ 的选型。",
      "> - **可叠加**（④）：与引擎无关，随时可以加进来或拿掉。\n> - **依赖**（⑤）：NVIDIA Snapshot 只支持 **SGLang 后端**，换引擎就必须换掉它。", "05 layer note")
patch(F, "架构图里“大模型路由到 PP 组”【S23】【S25】",
      "架构图里“大模型场景路由到PP组”【S23】【S25】", "05 verbatim")

# ============================================================ 06
F = "06-learning-path.md"
patch(F, "| **分布式训练背景** | 理解“张量并行在训练里也是同样的通信模式” |",
      "| **分布式训练背景** | 理解“张量并行在训练里也是同样的通信模式”——**这是本课程的教学性类比**【Illustrative】 |", "06 dist train")
patch(F, "> **没有 GPU 也能学完阶段 0–2 的概念部分**。[01](01-positioning-and-background.md)、[02](02-core-concepts.md)、[03](03-core-functionality.md) 全部是概念性的；[05](05-related-tools.md) 的选型部分同样不需要动手。只有阶段 4 之后需要真实环境。",
      "> **没有 GPU 也能学完阶段 1–2 的概念部分**。[01](01-positioning-and-background.md)、[02](02-core-concepts.md)、[03](03-core-functionality.md) 全部是概念性的；[05](05-related-tools.md) 的选型部分同样不需要动手。**阶段 0 与阶段 3 需要真实 GPU**（前者要读 `nvidia-smi` 输出，后者要读 `nvidia-smi topo -m`）；阶段 4 之后需要真实环境。", "06 no-gpu")
patch(F, "- [ ] 你能指出**你那个版本**里对应 NVFP4 的 `--quantization` 取值——**不是 `nvfp4`**【R30】",
      "- [ ] 你能指出**你那个版本**里对应 NVFP4 的 `--quantization` 取值——**不是 `nvfp4`**【R30】【UQ2】", "06 uq2")
patch(F, "4. 说出这份方案**不覆盖的四件事**。",
      "4. 说出这份方案**不覆盖的五件事**。", "06 five things")
patch(F, "- [ ] 你能指出源文档里哪些内容**不在**它的覆盖范围内（容量/SLA/监控/鉴权/升级）",
      "- [ ] 你能指出源文档里哪些内容**不在**它的覆盖范围内（具体模型选型 / 容量与 SLA / 监控与告警 / 数据与权限 / 回滚与升级——共五项）", "06 five criteria")
patch(F, "**读** → [04 · 4.4 / 4.5](04-usage.md#case-a-command)",
      "**读** → [04 · 4.4](04-usage.md#case-a-command) · [04 · 4.5](04-usage.md#case-b-command) · [04 · 4.8](04-usage.md#48-startup-faults)", "06 stage4 links")

print(f"applied: {applied}")
if skipped:
    print(f"SKIPPED: {len(skipped)}")
    for f, note, why in skipped:
        print(f"  {f}: {note} ({why})")
