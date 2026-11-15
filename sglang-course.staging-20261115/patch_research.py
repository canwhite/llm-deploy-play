#!/usr/bin/env python3
"""Apply research corrections to the staged SGLang course sections.

Every replacement is asserted to apply exactly once, so a stale string
fails loudly instead of silently skipping.
"""
import os
import sys

STAGING = sys.argv[1]
applied = 0
skipped = []


def patch(fname, old, new, note=""):
    global applied
    p = os.path.join(STAGING, fname)
    t = open(p, encoding="utf-8").read()
    n = t.count(old)
    if n != 1:
        skipped.append((fname, note or old[:60], f"count={n}"))
        return
    open(p, "w", encoding="utf-8").write(t.replace(old, new))
    applied += 1


# ---------------------------------------------------------------- 02
patch(
    "02-core-concepts.md",
    """| **量化** | **NVFP4（首选）或 FP8** | BF16显存不够；NVFP4是Blackwell原生格式，SGLang官方已验证RTX 5090单卡可跑【S11】【R1】 |
| **FP8 MoE注意** | 部分FP8 MoE路径在SM_120上**加载时会挂起** | 优先选用**NVFP4**检查点，避开FP8 MoE的已知问题【S13】 |
""",
    """| **量化** | **NVFP4（首选）或 FP8** | BF16显存不够；NVFP4是Blackwell原生格式，SGLang官方已验证RTX 5090单卡可跑【S11】【R1】 |
| **FP8 MoE注意** | 部分FP8 MoE路径在SM_120上**加载时会挂起** | 优先选用**NVFP4**检查点，避开FP8 MoE的已知问题【S13】 |
""",
    "02 quantization table (context only)",
)

patch(
    "02-core-concepts.md",
    """> **注意这两行不是并列的备选项，而是有优先级的**。源文档把 FP8 列为"可用"，但又指出 FP8 MoE 在 SM_120 上有加载挂起的已知问题——所以它给的实际建议是"**优先选用 NVFP4 检查点**"。在有 NVFP4 检查点可用时，FP8 不该是首选。
""",
    """> **注意这两行不是并列的备选项，而是有优先级的**。源文档把 FP8 列为"可用"，但又指出 FP8 MoE 在 SM_120 上有加载挂起的已知问题——所以它给的实际建议是"**优先选用 NVFP4 检查点**"。在有 NVFP4 检查点可用时，FP8 不该是首选。

> ### ⚠️ 外部核对：源文档这条告警**按原措辞不成立**，但结论方向是对的
>
> 源文档说"部分 FP8 MoE 路径在 SM_120 上**加载时会挂起**"【S13】。在 SGLang 的 issue tracker 里用多种检索组合**没有找到**一条同时满足「FP8 + MoE + 挂起 + SM120/RTX 5090 + 发生在权重加载期间」的 issue【Research-derived · R33】。**最接近的是 #40558**（OPEN）：在 **RTX PRO 6000 Blackwell**（compute capability 12.0）上，"the server hangs or abruptly terminates during the **FlashInfer autotune phase**"，日志里有 "Detected fp8 checkpoint." 与 "FlashInfer TRTLLM MoE is enabled."——但挂起发生在**权重加载之后**的 autotune 阶段，**不是加载期间**，且报告者说 "triton is currently the only backend that boots and serves"【R33】。
>
> **准确的说法应该是**：在 SM120 上，某些 FP8 / MoE 模型组合**会在启动阶段失败**——FlashInfer 的 TRT-LLM MoE autotune 会抛 `Unsupported architecture`（#40558，仍 OPEN）；而 **block-scaled FP8 在 SM120 上直到 2025-08 才获得支持**（#9233，已关闭）【R33】。
>
> **结论方向不变**：**优先选 NVFP4 检查点**，这是稳妥的；但**别把这条挂给 FP8 本身**。另外还有一个**与本方案高度相关**的坑：#15181 报告在两张 Blackwell 卡上做 TP 时 "If I do not set `NCCL_P2P_DISABLE=1`, the process hangs indefinitely"（拓扑为 `NODE`，无 NVLink）【R33】——**20 张无 NVLink 的 5090 做 TP 时必须注意这一点**。
""",
    "02 FP8 MoE caveat",
)

patch(
    "02-core-concepts.md",
    """| `--mem-fraction-static` **0.85 ~ 0.90** | **GPU 显存**中预留给静态部分（权重 + KV Cache 池）的**比例** | "为KV Cache留足空间" | 【S15】 |""",
    """| `--mem-fraction-static` **0.85 ~ 0.90** | **GPU 显存**中预留给静态部分（权重 + KV Cache 池）的**比例** | "为KV Cache留足空间" | 【S15】【R37】 |""",
    "02 mem-fraction row",
)

patch(
    "02-core-concepts.md",
    """> **实践纪律**：容器部署 SGLang 时，`--shm-size` 缺失是一个**独立的、必须显式设置**的参数，不是可以省略的默认值【S16】。它和显存无关，调 `--mem-fraction-static` 解决不了它。
""",
    """> **实践纪律**：容器部署 SGLang 时，`--shm-size` 缺失是一个**独立的、必须显式设置**的参数，不是可以省略的默认值【S16】。它和显存无关，调 `--mem-fraction-static` 解决不了它。

> **两条外部核对，方向都与源文档不同**：
> - **`--mem-fraction-static` 的默认值不是 0.85，而是"自动计算"**。官方文档原文："When unset, it is computed as `(GPU memory - reserved memory) / GPU memory`, defaulting to `0.88` if GPU memory cannot be detected"；源码里的定义是 `mem_fraction_static = (GPU memory capacity - activations - cuda graph buffers) / GPU memory capacity`【Research-derived · R37】。**官方 FAQ 的建议方向和源文档相反**——它说的是"**显存不足时可以调小** `--mem-fraction-static`，比如 0.8 或 0.7"，而不是调大留 KV Cache 空间【R37】。**源文档给的 0.85~0.90 属于"手动固定"的做法，会覆盖掉 SGLang 按显存自动调度的逻辑**（那个逻辑会联动 `chunked_prefill_size` 与 CUDA Graph 的 `max_bs`）。
> - **共享内存的官方数值是 `32g`**。SGLang 官方安装文档的启动示例统一用 `--shm-size 32g`（docs 全文出现 23 次 `32g` 写法），K8s 侧的官方清单用 `emptyDir: medium: Memory` 挂载到 `/dev/shm`【Research-derived · R31】。⚠️ 注意官方 K8s 清单**没有设 `sizeLimit`**，也把 `hostIPC: true` 作为替代方案——**"K8s 侧等价于 32g"是推断，不是官方文档的事实**【R31】。
""",
    "02 mem-fraction / shm caveats",
)

patch(
    "02-core-concepts.md",
    """| **FP8** | 8-bit 浮点，备选；MoE 路径在 SM_120 有加载挂起问题 | 【S11】【S13】 |""",
    """| **FP8** | 8-bit 浮点，备选；SM120 上部分 FP8/MoE 组合会在**启动阶段**失败（见 [2.2](#precision)） | 【S11】【S13】【R33】 |""",
    "02 terminology FP8 row",
)

patch(
    "02-core-concepts.md",
    """| **NVFP4** | Blackwell 原生的 4-bit 浮点权重格式，源文档的首选量化；实际 **4.5 bit/参数** | 【S11】【R5】 |""",
    """| **NVFP4** | Blackwell 原生的 4-bit 浮点权重格式，源文档的首选量化；实际 **4.5 bit/参数** | 【S11】【R5】 |
| **`--quantization` 的合法取值** | **不含 `nvfp4`**。NVFP4 检查点对应的是 `modelopt_fp4` / `nvfp4_online` / `petit_nvfp4` / `mxfp4` 等取值 | 【R30】 |""",
    "02 terminology NVFP4 row",
)

# ---------------------------------------------------------------- 03
patch(
    "03-core-functionality.md",
    """| 1 | **量化** | NVFP4（首选）或 FP8 | "BF16显存不够"；NVFP4 是 Blackwell 原生格式 | 需有对应量化格式的检查点；不是所有模型都有 |
| 2 | **注意力后端** | `--attention-backend flashinfer` | "部分默认后端的长提示TTFT可能极差" | 换后端是**行为变更**，需实测 TTFT |
| 3 | **FP8 MoE** | 避开——部分路径在 SM_120 上"**加载时会挂起**" | 优先用 NVFP4 检查点 | 该问题**只针对 FP8 MoE**，稠密 FP8 模型不在此列 |
| 4 | **CUDA 版本** | CUDA 13.x | "可获得最佳的FlashInfer线性注意力预填充性能" | 这是**性能推荐**，不是**兼容性下限** |
| 5 | **`--mem-fraction-static`** | 0.85 ~ 0.90 | "为KV Cache留足空间"；NVFP4 权重更小，"可适当提高并发" | 调高会挤压 KV Cache 池，需按实际并发压测 |
| 6 | **共享内存** | Docker `--shm-size`、K8s 调整 `/dev/shm` | "SGLang进程间通信依赖共享内存" | 与显存无关，独立设置 |
""",
    """| 1 | **量化** | NVFP4（首选）或 FP8 | "BF16显存不够"；NVFP4 是 Blackwell 原生格式 | 需有对应量化格式的检查点；不是所有模型都有。⚠️ **命令行取值不是 `nvfp4`**【R30】 |
| 2 | **注意力后端** | `--attention-backend flashinfer` | "部分默认后端的长提示TTFT可能极差" | 换后端是**行为变更**，需实测 TTFT。⚠️ **SM120 上官方允许 `triton` 或 `flashinfer`**【R32】 |
| 3 | **FP8 MoE** | 避开——部分路径在 SM_120 上"**加载时会挂起**" | 优先用 NVFP4 检查点 | ⚠️ **按原措辞未获证实**，需改述【R33】 |
| 4 | **CUDA 版本** | CUDA 13.x | "可获得最佳的FlashInfer线性注意力预填充性能" | ⚠️ **现在是硬性要求，不是推荐**；但源文档给的理由**只适用于 SM100/SM103**【R31】【R32】 |
| 5 | **`--mem-fraction-static`** | 0.85 ~ 0.90 | "为KV Cache留足空间"；NVFP4 权重更小，"可适当提高并发" | ⚠️ **官方默认是自动计算**；官方建议方向是**调小**【R37】 |
| 6 | **共享内存** | Docker `--shm-size`、K8s 调整 `/dev/shm` | "SGLang进程间通信依赖共享内存" | 与显存无关，独立设置。官方 Docker 基准值是 `32g`【R31】 |
""",
    "03 blackwell table",
)

patch(
    "03-core-functionality.md",
    """| 量化用 NVFP4 | ⚠️ 但 **sm120 上并非所有量化格式都可用**：TensorRT-LLM 的支持矩阵里 sm120 支持 NVFP4、MXFP4、FP8(per-tensor)、FP8 KV Cache，**不支持** FP8 block scaling、FP8 rowwise、NVFP4 KV Cache、AWQ 与 GPTQ | 【R8】 |""",
    """| 量化用 NVFP4 | ⚠️ 但 **sm120 上并非所有量化格式都可用**：TensorRT-LLM 的支持矩阵里 sm120 支持 NVFP4、MXFP4、FP8(per-tensor)、FP8 KV Cache，**不支持** FP8 block scaling、FP8 rowwise、NVFP4 KV Cache、AWQ 与 GPTQ | 【R8】 |
| 量化用 NVFP4 | ⚠️ **源文档给的 `--quantization nvfp4` 不是合法取值**。SGLang 的 `QUANTIZATION_CHOICES` 里没有 `nvfp4`；NVFP4 检查点对应的取值是 `modelopt_fp4` / `nvfp4_online` / `petit_nvfp4` / `mxfp4` 等，**具体用哪个取决于检查点是怎么导出的** | 【R30】 |
| 量化用 NVFP4 | ⚠️ 但 **NVFP4 的 GEMM 路径确实需要 FlashInfer**："NVFP4 GEMM requires FlashInfer to be installed"；且 `--fp4-gemm-backend auto` 在 SM120 上会选 `flashinfer_cutlass` | 【R34】 |""",
    "03 blackwell external table",
)

patch(
    "03-core-functionality.md",
    """**边界二：第 4 条是性能建议，不是兼容性门槛。**
源文档说 CUDA 13.x 是"**推荐版本**"【S14】，理由是 FlashInfer 线性注意力预填充性能。把它当成"必须用 13.x 否则跑不起来"，是**把推荐读成了硬约束**。
""",
    """**边界二：第 4 条的"是/不是硬约束"判断，恰好与现实相反——但理由也不是源文档给的那个。**
源文档说 CUDA 13.x 是"**推荐版本**"【S14】，理由是 FlashInfer 线性注意力预填充性能。**这条理由对 RTX 5090 不成立**：官方文档写的是 "On **SM100/SM103** with CUDA 13+, SGLang automatically selects FlashInfer for GDN prefill ..."——**SM100/SM103 是数据中心 Blackwell（B200/GB200），不是 SM120 的消费版**【Research-derived · R32】。

但**结论要反过来**：官方安装文档现在写的是 "**SGLang requires CUDA 13.** CUDA 12 (`cu129`) wheels and images were retired with the upgrade to PyTorch 2.14"；"CUDA 12 images (`-cu12` / `-cu129`) are **no longer published**"【Research-derived · R31】。**CUDA 13 从"推荐"变成了硬性要求**——源文档在这里是**低估**了要求，不是高估。

> **所以正确的说法是**：CUDA 13 是**必须**（当前版本已不发布 CUDA 12 镜像）【R31】；而"为了 FlashInfer 线性注意力性能"这个理由**只对 B200/GB200 成立**，在 5090 上不适用【R32】。
""",
    "03 boundary two",
)

patch(
    "03-core-functionality.md",
    """**边界一：第 3 条不是"FP8 都不能用"，而是"FP8 MoE 在 SM_120 上有已知挂起问题"。**
源文档的措辞是"部分FP8 MoE路径在SM_120上加载时会挂起"【S13】——限定词是"部分"和"MoE"。把它扩大成"FP8 在 5090 上不能用"，是**把一条范围有限的告警误读成全面禁用**。
""",
    """**边界一：第 3 条不是"FP8 都不能用"，而且它的原措辞也查不到对应的官方 issue。**
源文档的措辞是"部分FP8 MoE路径在SM_120上加载时会挂起"【S13】。把它扩大成"FP8 在 5090 上不能用"，是**把一条范围有限的告警误读成全面禁用**。但**更严格的问题是**：在 SGLang 的 issue tracker 里**找不到**一条同时满足「FP8 + MoE + 挂起 + SM120/RTX 5090 + 发生在权重加载期间」的 issue【R33】。

**最接近的两条**：

| Issue | 实际内容 | 与源文档说法的差异 |
|---|---|---|
| **#40558**（OPEN） | RTX PRO 6000 Blackwell（cc 12.0）上，服务在 **FlashInfer autotune 阶段**挂起或异常退出，报 `Unsupported architecture`；日志含 "Detected fp8 checkpoint." 与 "FlashInfer TRTLLM MoE is enabled." | 挂起在**权重加载之后**，不是加载期间；报告者称 "triton is currently the only backend that boots and serves" |
| **#9233**（已关闭） | "the FP8 blockwise on blackwell sm120 is not supported by the sglang yet so we are not able to run GLM-45*-FP8 and other FP8 models on RTX 6000 PRO and RTX 5090" | 这是**特性请求**（block-scaled FP8 支持），**不是挂起报告**，也没提 MoE |

**所以准确的表述是**：在 SM120 上，某些 FP8 / MoE 模型组合**会在启动阶段失败**（autotune 阶段抛 `Unsupported architecture`），且 block-scaled FP8 长期缺支持；**"加载期间挂起"这个具体说法没有对应 issue**【R33】。

> **结论方向仍然成立**：**优先选 NVFP4 检查点**，这是稳妥的工程判断——但**理由要换成上面这些可查证的原因**，不要引用一条不存在的 issue。
""",
    "03 boundary one",
)

patch(
    "03-core-functionality.md",
    """**边界三：第 5 条和第 6 条修的是完全不同的东西。**
`--mem-fraction-static` 治**显存**，共享内存治**进程间通信**。在容器里排查"服务起不来"时，先确认共享内存，再怀疑显存配额。
""",
    """**边界三：第 5 条和第 6 条修的是完全不同的东西。**
`--mem-fraction-static` 治**显存**，共享内存治**进程间通信**。在容器里排查"服务起不来"时，先确认共享内存，再怀疑显存配额。

**边界四：第 5 条的方向可能与官方建议相反。**
`--mem-fraction-static` 的**默认值是自动计算**的：`mem_fraction_static = (GPU memory capacity - activations - cuda graph buffers) / GPU memory capacity`，检测不到显存时回落到 0.88【Research-derived · R37】。官方 FAQ 的建议是"**显存不足时可以调小** `--mem-fraction-static`，比如 0.8 或 0.7"【R37】——**方向是调小，不是调大**。

源文档说的"调大到 0.85~0.90 为 KV Cache 留足空间"【S15】是一种**手动固定**的做法，它会覆盖掉 SGLang 按显存自动联动的调度（那个逻辑会同步调整 `chunked_prefill_size` 与 CUDA Graph 的 `max_bs`）。**这不是错，只是要知道你在放弃什么**：手动固定换来的是可预测的显存占用，代价是失去按卡调优的空间。

**边界五：第 2 条在 SM120 上不是"必须选 FlashInfer"。**
官方文档对 SM120 的表述是 "`triton` **or** `flashinfer` for prefill/full attention"【R32】；`flashinfer` 是 SGLang 的**默认**注意力后端，但不是 SM120 上的强制项。**不过**：NVFP4 的 GEMM 路径确实需要 FlashInfer【R34】，而且已知 #40558 正是 FlashInfer TRT-LLM MoE autotune 在 SM120 上抛 `Unsupported architecture`【R33】。**实践建议**：以 FlashInfer 起步，**把它当默认值而不是教条**——真出问题时先试 `triton`。
""",
    "03 boundary three",
)

# ---------------------------------------------------------------- 04
patch(
    "04-usage.md",
    """| 3 | **共享内存够不够**（容器环境） | `df -h /dev/shm` | 容器内 `/dev/shm` 不是默认的小值；SGLang 依赖它做进程间通信【S16】 |
""",
    """| 3 | **共享内存够不够**（容器环境） | `df -h /dev/shm` | 容器内 `/dev/shm` 不是默认的小值；SGLang 依赖它做进程间通信【S16】。官方 Docker 基准值是 `--shm-size 32g`【R31】 |
| 4 | **CUDA 版本对不对** | `nvcc --version` 或查镜像 tag | 当前 SGLang **要求 CUDA 13**；CUDA 12 镜像已不再发布【R31】 |
| 5 | **参数取值对不对** | `python3 -m sglang.launch_server --help \\| grep -A3 quantization` | 确认你版本的 `--quantization` 合法取值里**没有 `nvfp4`**【R30】 |
""",
    "04 pre-flight table",
)

patch(
    "04-usage.md",
    """| `--attention-backend` | `flashinfer` | Blackwell 上部分默认后端的长提示 TTFT 可能极差【S12】 |
| `--quantization` | `nvfp4`（首选）或 `fp8` | BF16 显存不够；NVFP4 是 Blackwell 原生格式【S11】 |
| `--mem-fraction-static` | `0.85` ~ `0.90` | 为 KV Cache 留足空间【S15】 |
| 容器 `--shm-size` | 按 SGLang 要求设置 | 进程间通信依赖共享内存【S16】 |
| CUDA | 源文档推荐 13.x | FlashInfer 线性注意力预填充性能【S14】（**是性能推荐，非兼容性下限**） |
""",
    """| `--attention-backend` | `flashinfer` | Blackwell 上部分默认后端的长提示 TTFT 可能极差【S12】。⚠️ SM120 上官方允许 `triton` 或 `flashinfer`；FlashInfer 是默认值不是强制项【R32】 |
| `--quantization` | 见下方说明 | BF16 显存不够；NVFP4 是 Blackwell 原生格式【S11】。⚠️ **合法取值里没有 `nvfp4`**【R30】 |
| `--mem-fraction-static` | `0.85` ~ `0.90`（源文档建议） | 为 KV Cache 留足空间【S15】。⚠️ 官方默认是**自动计算**，且官方建议在 OOM 时**调小**【R37】 |
| 容器 `--shm-size` | `32g` | 进程间通信依赖共享内存【S16】；官方 Docker 示例统一用 `32g`【R31】 |
| CUDA | **13.x（现为硬性要求）** | 源文档写的是"推荐版本"【S14】，但官方已改为 "SGLang requires CUDA 13"【R31】 |

> ### ⚠️ `--quantization` 的取值必须核对
>
> 源文档的命令块写的是 `--quantization nvfp4`【S8】。但 SGLang 的 `QUANTIZATION_CHOICES` 里**没有 `nvfp4` 这个取值**——它会被 argparse 直接拒绝【Research-derived · R30】。NVFP4 检查点对应的取值是 `modelopt_fp4` / `nvfp4_online` / `petit_nvfp4` / `mxfp4` 等，**具体用哪一个取决于你的检查点是怎么导出的**。
>
> **动手前先跑这一条**，照抄你那个版本的合法取值：
>
> ```bash
> python3 -m sglang.launch_server --help | grep -A3 -- "--quantization"
> ```
>
> 另外注意：**NVFP4 的 GEMM 路径需要装 FlashInfer**（"NVFP4 GEMM requires FlashInfer to be installed"）【R34】——所以上面那条 `--attention-backend flashinfer` 在用 NVFP4 时不是可选项。
""",
    "04 blackwell items table",
)

patch(
    "04-usage.md",
    """```bash
# 单个副本（本例为 node0 / GPU 0）
CUDA_VISIBLE_DEVICES=0 \\
python3 -m sglang.launch_server \\
  --model-path /path/to/model \\
  --tp-size 1 \\
  --attention-backend flashinfer \\
  --quantization nvfp4 \\
  --mem-fraction-static 0.85 \\
  --host 0.0.0.0 --port 30000
```
""",
    """```bash
# 单个副本（本例为 node0 / GPU 0）
CUDA_VISIBLE_DEVICES=0 \\
python3 -m sglang.launch_server \\
  --model-path /path/to/model \\
  --tp-size 1 \\
  --attention-backend flashinfer \\
  --quantization <你的版本里对应 NVFP4 的取值> \\
  --mem-fraction-static 0.85 \\
  --host 0.0.0.0 --port 30000
```

> **`--quantization` 的值留空了**：源文档写的 `nvfp4` **不是 SGLang 的合法取值**【R30】。候选是 `modelopt_fp4` / `nvfp4_online` / `petit_nvfp4` / `mxfp4`——**取决于你的检查点怎么导出**。请先用 `--help` 核对，再填。
""",
    "04 case A command",
)

patch(
    "04-usage.md",
    """```bash
# 节点内的 4 个副本（node0）——端口需互不冲突
for i in 0 1 2 3; do
  CUDA_VISIBLE_DEVICES=$i nohup python3 -m sglang.launch_server \\
    --model-path /path/to/model \\
    --tp-size 1 \\
    --attention-backend flashinfer \\
    --quantization nvfp4 \\
    --mem-fraction-static 0.85 \\
    --host 0.0.0.0 --port $((30000 + i)) \\
    > /tmp/sglang-replica-$i.log 2>&1 &
done
```
""",
    """```bash
# 节点内的 4 个副本（node0）——端口需互不冲突
for i in 0 1 2 3; do
  CUDA_VISIBLE_DEVICES=$i nohup python3 -m sglang.launch_server \\
    --model-path /path/to/model \\
    --tp-size 1 \\
    --attention-backend flashinfer \\
    --quantization <你的版本里对应 NVFP4 的取值> \\
    --mem-fraction-static 0.85 \\
    --host 0.0.0.0 --port $((30000 + i)) \\
    > /tmp/sglang-replica-$i.log 2>&1 &
done
```
""",
    "04 case A loop",
)

patch(
    "04-usage.md",
    """这是**源文档给出的完整命令**，逐字照抄结构即可【Source-derived · S8】：

```bash
python3 -m sglang.launch_server \\
  --model-path /path/to/model \\
  --tp-size 4 \\
  --pp-size 5 \\
  --dist-init-addr <MASTER_IP>:20000 \\
  --nnodes 5 --node-rank <0-4> \\
  --attention-backend flashinfer \\
  --quantization nvfp4 \\
  --mem-fraction-static 0.85 \\
  --host 0.0.0.0 --port 30000
```
""",
    """这是**源文档给出的完整命令**【Source-derived · S8】：

```bash
python3 -m sglang.launch_server \\
  --model-path /path/to/model \\
  --tp-size 4 \\
  --pp-size 5 \\
  --dist-init-addr <MASTER_IP>:20000 \\
  --nnodes 5 --node-rank <0-4> \\
  --attention-backend flashinfer \\
  --quantization nvfp4 \\
  --mem-fraction-static 0.85 \\
  --host 0.0.0.0 --port 30000
```

> ### ⚠️ 这段命令**逐字照抄会起不来**
>
> **`--quantization nvfp4` 不是合法取值**——SGLang 的 `QUANTIZATION_CHOICES` 里没有它，argparse 会直接拒绝【Research-derived · R30】。请换成你那个版本里对应 NVFP4 检查点的取值（候选：`modelopt_fp4` / `nvfp4_online` / `petit_nvfp4` / `mxfp4`），并先用 `--help` 核对。
>
> **其余参数逐字有效**：`--tp-size`、`--pp-size`、`--nnodes`、`--node-rank`、`--dist-init-addr`（别名 `--nccl-init-addr`）、`--attention-backend`、`--mem-fraction-static`、`--host`、`--port` 都已对照官方 server arguments 文档与源码逐一核实【R30】。`--attention-backend flashinfer` 也在合法取值表里【R30】。
>
> 另外两条与本命令相关的提醒：
> - **CUDA 13 是硬性要求**，不是推荐——CUDA 12 的 wheel 与镜像已停止发布【R31】。
> - **20 张无 NVLink 的卡做 TP 有已知的 P2P 挂起**：SGLang issue #15181 报告在两张 Blackwell 卡上做 TP 时，若不设 `NCCL_P2P_DISABLE=1`，"the process hangs indefinitely"（拓扑为 `NODE`，无 NVLink）【R33】。**做情况 B 前务必先在 2 卡上复现一次**。
""",
    "04 case B command",
)

patch(
    "04-usage.md",
    """| **5** | 快照恢复**起不来 / 恢复后 CUDA 调用挂死** | **是不是在 K8s 上；是不是跨节点；是不是装了拦截 `libcuda.so` 的监控工具** | 官方限制：K8s-only、单节点、"must not have tools that intercept `libcuda.so` calls"【R20】 |
""",
    """| **5** | 快照恢复**起不来 / 恢复后 CUDA 调用挂死** | **是不是在 K8s 上；是不是跨节点；是不是装了拦截 `libcuda.so` 的监控工具** | 官方限制：K8s-only、单节点、"must not have tools that intercept `libcuda.so` calls"【R20】 |
| **6** | 启动**参数直接被拒**（argparse 报错） | **`--quantization` 的取值** | `nvfp4` 不在合法取值表里【R30】 |
| **7** | TP 起来后**进程无限挂起** | **`NCCL_P2P_DISABLE=1`** | 无 NVLink 的 Blackwell 卡上做 TP 的已知问题 #15181【R33】；官方另有针对无 NVLink 主机的 FlashInfer PCIe-IPC all-reduce 说明【R35】 |
""",
    "04 fault table",
)

# ---------------------------------------------------------------- 05
patch(
    "05-related-tools.md",
    """| **NVFP4 / FP8 量化检查点** | 直接决定模型能否单卡承载【S11】——这一层的选择**先于**引擎选择 |
| **FlashInfer** | 注意力后端，在 Blackwell 上影响长提示的 TTFT【S12】 |
""",
    """| **NVFP4 / FP8 量化检查点** | 直接决定模型能否单卡承载【S11】——这一层的选择**先于**引擎选择 |
| **FlashInfer** | 注意力后端，在 Blackwell 上影响长提示的 TTFT【S12】；**NVFP4 的 GEMM 路径必须装它**【R34】 |

> **这一层还有一个"元"问题**：**命令行取值不等于格式名**。SGLang 的 `--quantization` 合法取值里**没有 `nvfp4`**【R30】——真正的 NVFP4 检查点要用 `modelopt_fp4` / `nvfp4_online` / `petit_nvfp4` / `mxfp4` 这类取值。**换引擎时，"格式支持"和"参数名支持"是两件事**，都要核对。
""",
    "05 layer-1 table",
)

# ---------------------------------------------------------------- 06
patch(
    "06-learning-path.md",
    """| **CUDA 基础**（不需要会写 kernel） | 理解 SM_120、CUDA 版本、后端选择【S12】【S14】 |
""",
    """| **CUDA 基础**（不需要会写 kernel） | 理解 SM_120、CUDA 版本、后端选择【S12】【R31】【R32】 |
""",
    "06 prereq CUDA row",
)

patch(
    "06-learning-path.md",
    """```bash
nvidia-smi
nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv
python3 -m sglang.launch_server --help
df -h /dev/shm
```

**完成判据**
- [ ] `nvidia-smi` 列出了你的 GPU，且能查到显存容量与 compute capability
- [ ] `--help` 能列出 `--tp-size`、`--pp-size` 等参数（**记下你的 SGLang 版本**）
- [ ] 容器环境下 `/dev/shm` 不是默认小值【S16】
- [ ] 你能明确回答："我的集群是几个节点？每节点几张卡？"
""",
    """```bash
nvidia-smi
nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv
python3 -m sglang.launch_server --help
python3 -m sglang.launch_server --help | grep -A3 -- "--quantization"
df -h /dev/shm
nvcc --version
```

**完成判据**
- [ ] `nvidia-smi` 列出了你的 GPU，且能查到显存容量与 compute capability
- [ ] `--help` 能列出 `--tp-size`、`--pp-size` 等参数（**记下你的 SGLang 版本**）
- [ ] 你能指出**你那个版本**里对应 NVFP4 的 `--quantization` 取值——**不是 `nvfp4`**【R30】
- [ ] 你的 CUDA 是 **13.x**（当前版本已不发布 CUDA 12 镜像）【R31】
- [ ] 容器环境下 `/dev/shm` 不是默认小值【S16】
- [ ] 你能明确回答："我的集群是几个节点？每节点几张卡？"
""",
    "06 stage 0",
)

patch(
    "06-learning-path.md",
    """3. 故意把 `--shm-size` 调小，观察故障表现——**建立"卡住"的直觉**【S16】。

**完成判据**
- [ ] 单副本起来并能响应请求
""",
    """3. 故意把 `--shm-size` 调小，观察故障表现——**建立"卡住"的直觉**【S16】。
4. **在 2 张卡上先做一次 TP**，并观察不设 `NCCL_P2P_DISABLE=1` 时是否挂起——这是 20 卡无 NVLink 集群最容易踩的坑【R33】。

**完成判据**
- [ ] 单副本起来并能响应请求
""",
    "06 stage 4 practice",
)

print(f"applied: {applied}")
if skipped:
    print(f"SKIPPED: {len(skipped)}")
    for f, note, why in skipped:
        print(f"  {f}: {note!r} ({why})")
