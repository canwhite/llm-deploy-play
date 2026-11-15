# 03 · 核心功能

> **学习目标**
> 完成本节后，你应该能够：
> 1. 说出这份方案调用了 SGLang 的**四类能力**，以及每类能力的输入与输出；
> 2. 走完源文档的五步，说出每一步的**产出物**；
> 3. 指出每类能力的**边界**——在什么条件下这套方案会失效；
> 4. 区分源文档的**主张**与已被外部证据**确认**的部分。

### 证据标签约定

`【Source-derived · Sxx】` 来自根文档 `source-sglang.md`；`【Research-derived · Rxx】` 来自外部权威来源；`【Illustrative】` 为教学性构造，不主张 SGLang 的未经验证行为。完整定位码与出处见 [07 · 验证记录](07-verification-record.md)。

---

## 3.1 能力总览

这份方案实际调用了 SGLang 的**四类能力**。把它们和源文档的五步对应起来：

| 能力 | 源文档在哪一步用到 | 输入 | 输出 |
|---|---|---|---|
| **并行执行** | 第一步、第二步 | 拓扑信息、模型规格 | 一个（或一组）可服务的推理实例 |
| **Blackwell 适配** | 第三步 | 计算能力代号、量化格式 | 一组必须显式设置的启动参数 |
| **冷启动加速** | 第四步 | 已就绪的实例或快照 | 秒级上线的副本 |
| **路由分发** | 第五步 | 多个实例副本 | 统一的请求入口 |

---

<a id="step-1-topology"></a>

## 3.2 第一步：拓扑测量 → 一条铁律

### 输入 / 输出

- **输入**：机器的物理连接关系；
- **输出**：一个**决策**——TP 的规模上限。

源文档的操作是"先用 `nvidia-smi topo -m` 确认20张卡的物理连接关系"【Source-derived · S2】，然后给出铁律："**张量并行（TP）绝对不能跨节点或跨PCIe Switch边界**"。

### 为什么这条铁律成立

RTX 5090 **没有 NVLink**【S2】——这一点已由 NVIDIA 产品页核实：RTX 5090 规格表中 "NVIDIA NVLink™ (SLI-Ready)" 一栏为 **No**，显存为 **32 GB GDDR7**、512-bit 位宽、21760 个 CUDA 核心【Research-derived · R6】。TP 要求每层都做 All-Reduce，因此它的通信代价取决于卡间带宽，而 PCIe 带宽远低于 NVLink。

> **这条铁律的官方背书与措辞差异**：SGLang 官方文档支持"TP 用于节点内、PP 用于跨节点"这个**方向**——"TP remains the conventional approach for intra-node scaling, it frequently encounters communication bottlenecks during multi-node deployments"【R13】。但官方多节点部署文档**确实有 TP 跨节点的示例**（`--tp 16 --nnodes 2`）【R14】，且"跨 PCIe Switch 边界"这个具体措辞在官方文档中**没有对应表述**【R14】。**在本课程的无 NVLink 硬件语境下，这条规则应当作强建议执行，而不是教条。**

### 边界

| 边界 | 说明 |
|---|---|
| **拓扑是实测值，不是假设值** | 源文档自己把测量放在第一步【S2】，但第二步又直接假设"5节点 × 4卡/节点"【S7】。**假设必须被实测覆盖**。 |
| **节点 ≠ PCIe 域** | 一个节点内的卡可能分属多个 Switch 域。此时 TP 上限是**域内卡数**，不是节点卡数。 |
| **这是 TP 的上限，不是 DP 的上限** | DP 场景下每卡跑独立副本，副本之间不通信，因此**不受 PCIe 拓扑约束**【S5】。 |

---

<a id="step-2-grading"></a>

## 3.3 第二步：模型分级 → 两个分支

### 输入 / 输出

- **输入**：模型权重规格 + 量化格式 → **能否装进 32GB**；
- **输出**：情况 A（纯 DP）或情况 B（TP × PP）。

### 3.3.1 情况 A：模型装得下单卡

| 项 | 内容 |
|---|---|
| **策略** | "**纯数据并行（DP），吞吐量最大化**"【S5】 |
| **实例数** | 20 个独立 SGLang 实例，每实例 1 张 GPU，`--tp-size 1`【S5】 |
| **通信** | GPU 之间"**零通信开销**"，源文档称之为"吞吐量的理论最优形态"【S5】 |
| **分发** | 用 SGLang Router 在 20 个副本之间分发请求【S6】 |

**边界**：这条路成立的前提是"模型可完整放入单张RTX 5090（32GB显存）"【S5】。一旦要跨卡，情况 A 立刻失效。

### 3.3.2 情况 B：模型必须跨卡拆分

| 项 | 内容 |
|---|---|
| **策略** | "`TP = 单节点GPU数`，`PP = 节点数`"【S7】 |
| **示例** | 5 节点 × 4 卡/节点 → `--tp-size 4`、`--pp-size 5`，`tp × pp = 20`【S7】 |
| **启动命令** | 见 [04 节](04-usage.md#case-b-command) 的完整命令【S8】 |
| **跨节点协调** | 需配合 `--dist-init-addr`、`--nnodes` 和 `--node-rank` 协调各节点【S9】 |

**边界**：

| 边界 | 说明 |
|---|---|
| **`tp × pp = 20` 不是恒等式** | 它要求"TP 恰好吃满一个 PCIe 域"且"PP 覆盖其余节点"。当这两个前提不同时成立时，需要重新分配。 |
| **PP 会降低单请求延迟** | PP 让请求流经多个 stage，单请求的端到端延迟高于同规模 DP。源文档选 TP×PP 是因为**模型大到无法不拆**【S7】，不是因为它在延迟上优于 DP。 |
| **这个布局不是官方指导** | SGLang 官方的 PP 示例**一律是 4 个节点**（`--nnodes 4 --tp 8 --pp-size 4`；`--nnodes 4 --tp 4 --pp-size 8`），官方**从未**给出"一个 stage 一个节点"或 5 节点的布局建议【R14】。5×(TP4/PP5) 是**合理的工程选择，但不是官方方案**【UQ6】 |
| **节点间网络成为瓶颈** | 跨节点通信走外部网络；源文档提到 InfiniBand 或高速 RoCE 是这个场景的前提【S24】。 |

<a id="model-choice"></a>

### 3.3.3 模型选型：源文档给的具体型号，外部证据怎么说

源文档在情况 A 推荐了一个**非常具体**的组合："**Qwen3.8-27B的NVFP4 W4A4检查点**"，并称"该模型官方验证可在单张RTX 5090上以NVFP4精度运行，GSM8K得分93.18–95.15%"【Source-derived · S6】。

这条同时包含**型号**、**量化格式**与**基准分数**三个可独立证伪的部分。外部核对的结果是：**型号真实存在，格式真实存在，但"官方验证"与"分数含义"两处需要修正**。

#### 核对结果一览

| 源文档的说法 | 核对结果 | 证据 |
|---|---|---|
| 模型是 **Qwen3.8-27B** | ✅ **真实存在**。`Qwen/Qwen3.8-27B` 与 `Qwen/Qwen3.8-27B-FP8` 均为官方发布（2026-08-14 上线） | 【R2】【R4】 |
| 有 **NVFP4** 检查点 | ✅ **存在**。官方导出为 `nvidia/Qwen3.8-27B-NVFP4`；SGLang cookbook 实际推荐的是第三方 `RadixArk/Qwen3.8-27B-NVFP4` | 【R3】【R1】 |
| "**W4A4**" | ⚠️ **不精确**。官方导出是**混合精度**：MLP 层与 `lm_head` 用 NVFP4，**自注意力与线性注意力层用 FP8** | 【R3】 |
| "**官方验证**可在单张 RTX 5090 上运行" | ⚠️ **归因要改**。单卡 RTX 5090 的实测与发布者是 **SGLang（LMSYS）**，不是 NVIDIA、也不是 Qwen——NVIDIA 的模型卡只写了 GB300 作为测试硬件 | 【R1】【R3】 |
| "**GSM8K 得分 93.18–95.15%**" | ⚠️ **数字真实，但含义不同**。它不是模型能力分，而是 **202 个服务配置格子的最小–最大区间** | 【R1】 |

#### 关于 GSM8K 分数的含义

SGLang 官方 cookbook 的原文是：

> "That is 202 cells, each one served and scored on the full 1319-question GSM8K (93.18-95.15%)."【Research-derived · R1】

这 **202 个格子**是「检查点精度 × 投机解码选项 × 服务策略 × SSM 状态 dtype」的组合，每个格子都在完整的 1319 道题上跑一遍。**区间反映的是服务配置的波动，不是模型能力的波动**。

同一份文档给出的**分卡**数值：

| 硬件 | GSM8K（该卡全部配置格子） |
|---|---|
| **RTX 5090** | **93.93 – 94.92%**（该卡全部 15 种组合） |
| RTX PRO 6000 | 94.01 – 95.00% |
| DGX Spark | 94.16 – 95.07% |
| *（全部 202 格子的总区间）* | *93.18 – 95.15%* |

> **所以怎么读这个数**：如果你要的是"这个模型在 5090 上能做对多少题"，答案是 **93.93–94.92%**；**93.18–95.15%** 是跨五种硬件的全局区间。两者都不是官方模型卡的"基准分"——**Qwen 官方模型卡根本没有列 GSM8K**【R1】【R2】。

#### 单卡装不装得下：官方给了确切数字

SGLang cookbook 直接写明了两个量化格式的单卡占用：

> "FP8 weights ~28.5GB (not serviceable beyond bs≤2 on 32GB cards); NVFP4 weights ~16.5GB (recommended for RTX 5090-class GPUs)."【Research-derived · R1】

把这两句和源文档对上：

- **源文档说 "BF16显存不够"**【S11】——✅ **成立**。27B 参数按 BF16 算约 54GB，确实放不下 32GB。
- **源文档说 "NVFP4权重更小，可适当提高并发"**【S15】——✅ **成立**，且官方给了具体数字：FP8 约 28.5GB（32GB 卡上**并发上限只有 bs≤2**），NVFP4 约 16.5GB。

> **一个必须说清的口径差异**：cookbook 的 "NVFP4 weights ~16.5GB" 与 HF 上该检查点的**磁盘体积**（约 20.4–21.9GB）**对不上**——前者更像是不含 FP4 scale 开销、vision tower 与 MTP head 的**纯权重/运行时口径**。**这两个数字不能混用**【R1】。

#### 一个不依赖具体型号的通用判据

```
单卡可行性  ≈  参数量 × 每参数字节数  +  KV Cache 池  +  运行时开销  ≤  32GB
```

其中"每参数字节数"由量化格式决定（BF16 ≈ 2 bytes/param，FP8 ≈ 1 byte/param，**NVFP4 ≈ 0.5625 byte/param**（4.5 bit/参数）【R5】，**权重部分**）。**这是本课程自己的推导，不是源文档的主张**【Illustrative】——它给出一个量级判断方法，用来在你拿到真实模型规格时快速筛掉明显装不下的候选。

> **最后一条边界**：**没有任何官方文档描述过 20× RTX 5090 的 SGLang 部署**。SGLang cookbook 对这个模型的部署面板只覆盖**单卡**（H200 / RTX PRO 6000 / RTX 5090 / DGX Spark），其 "Nodes" 维度只有 `single` 一个选项【R1】。因此本课程讲的"20 个副本"是一个**合理但未经官方验证的推演**【Research-derived · R1】【UQ1】【UQ10】。

---

<a id="step-3-blackwell"></a>

## 3.4 第三步：Blackwell 六个必配项

源文档列出 RTX 5090（SM_120）上"**必须显式处理**的坑"【S10】，并给出一张表。本节逐条拆解其**能力边界**：

| # | 配置项 | 源文档的要求 | 目的 | 边界 |
|---|---|---|---|---|
| 1 | **量化** | NVFP4（首选）或 FP8 | "BF16显存不够"；NVFP4 是 Blackwell 原生格式 | 需有对应量化格式的检查点；不是所有模型都有。⚠️ **命令行取值不是 `nvfp4`**【R30】 |
| 2 | **注意力后端** | `--attention-backend flashinfer` | "部分默认后端的长提示TTFT可能极差" | 换后端是**行为变更**，需实测 TTFT。⚠️ **SM120 上官方允许 `triton` 或 `flashinfer`**【R32】 |
| 3 | **FP8 MoE** | 避开——部分路径在 SM_120 上"**加载时会挂起**" | 优先用 NVFP4 检查点 | ⚠️ **按原措辞未获证实**，需改述【R33】 |
| 4 | **CUDA 版本** | CUDA 13.x | "可获得最佳的FlashInfer线性注意力预填充性能" | ⚠️ **现在是硬性要求，不是推荐**；但源文档给的理由**只适用于 SM100/SM103**【R31】【R32】 |
| 5 | **`--mem-fraction-static`** | 0.85 ~ 0.90 | "为KV Cache留足空间"；NVFP4 权重更小，"可适当提高并发" | ⚠️ **官方默认是自动计算**；官方建议方向是**调小**【R37】 |
| 6 | **共享内存** | Docker `--shm-size`、K8s 调整 `/dev/shm` | "SGLang进程间通信依赖共享内存" | 与显存无关，独立设置。官方 Docker 基准值是 `32g`【R31】 |

**外部证据对这张表的补强与修正**：

| 源文档条目 | 外部核对 | 证据 |
|---|---|---|
| 量化用 NVFP4 | ✅ RTX Blackwell 白皮书确认支持 **FP4 / FP6 Tensor Core 操作**与第二代 FP8 Transformer Engine | 【R7】 |
| 量化用 NVFP4 | ⚠️ 但 **sm120 上并非所有量化格式都可用**：TensorRT-LLM 的支持矩阵里 sm120 支持 NVFP4、MXFP4、FP8(per-tensor)、FP8 KV Cache，**不支持** FP8 block scaling、FP8 rowwise、NVFP4 KV Cache、AWQ 与 GPTQ | 【R8】 |
| 量化用 NVFP4 | ⚠️ **源文档给的 `--quantization nvfp4` 不是合法取值**。SGLang 的 `QUANTIZATION_CHOICES` 里没有 `nvfp4`；NVFP4 检查点对应的取值是 `modelopt_fp4` / `nvfp4_online` / `petit_nvfp4` / `mxfp4` 等，**具体用哪个取决于检查点是怎么导出的** | 【R30】 |
| 量化用 NVFP4 | ⚠️ 但 **NVFP4 的 GEMM 路径确实需要 FlashInfer**："NVFP4 GEMM requires FlashInfer to be installed"；且 `--fp4-gemm-backend auto` 在 SM120 上会选 `flashinfer_cutlass` | 【R34】 |
| 量化用 NVFP4 | ⚠️ NVFP4 检查点本身是**混合精度**（MLP/lm_head 为 NVFP4，注意力层为 FP8），"W4A4" 只是近似说法 | 【R3】 |

### 三条容易踩的边界

**边界一：第 3 条不是"FP8 都不能用"，而且它的原措辞也查不到对应的官方 issue。**
源文档的措辞是"部分FP8 MoE路径在SM_120上加载时会挂起"【S13】。把它扩大成"FP8 在 5090 上不能用"，是**把一条范围有限的告警误读成全面禁用**。但**更严格的问题是**：在 SGLang 的 issue tracker 里**找不到**一条同时满足「FP8 + MoE + 挂起 + SM120/RTX 5090 + 发生在权重加载期间」的 issue【Research-derived · R33】。

**最接近的两条**：

| Issue | 实际内容 | 与源文档说法的差异 |
|---|---|---|
| **#40558**（OPEN） | RTX PRO 6000 Blackwell（cc 12.0）上，服务在 **FlashInfer autotune 阶段**挂起或异常退出，报 `Unsupported architecture`；日志含 "Detected fp8 checkpoint." 与 "FlashInfer TRTLLM MoE is enabled." | 挂起在**权重加载之后**，不是加载期间；报告者称 "triton is currently the only backend that boots and serves" |
| **#9233**（已关闭） | "the FP8 blockwise on blackwell sm120 is not supported by the sglang yet so we are not able to run GLM-45*-FP8 and other FP8 models on RTX 6000 PRO and RTX 5090" | 这是**特性请求**（block-scaled FP8 支持），**不是挂起报告**，也没提 MoE |

**所以准确的表述是**：在 SM120 上，某些 FP8 / MoE 模型组合**会在启动阶段失败**（autotune 阶段抛 `Unsupported architecture`），且 block-scaled FP8 长期缺支持；**"加载期间挂起"这个具体说法没有对应 issue**【R33】。

> **结论方向仍然成立**：**优先选 NVFP4 检查点**，这是稳妥的工程判断——但**理由要换成上面这些可查证的原因**，不要引用一条不存在的 issue。


**边界二：第 4 条的"是/不是硬约束"判断，恰好与现实相反——但理由也不是源文档给的那个。**
源文档说 CUDA 13.x 是"**推荐版本**"【S14】，理由是 FlashInfer 线性注意力预填充性能。**这条理由对 RTX 5090 不成立**：官方文档写的是 "On **SM100/SM103** with CUDA 13+, SGLang automatically selects FlashInfer for GDN prefill ..."——**SM100/SM103 是数据中心 Blackwell（B200/GB200），不是 SM120 的消费版**【Research-derived · R32】。

但**结论要反过来**：官方安装文档现在写的是 "**SGLang requires CUDA 13.** CUDA 12 (`cu129`) wheels and images were retired with the upgrade to PyTorch 2.14"；"CUDA 12 images (`-cu12` / `-cu129`) are **no longer published**"【Research-derived · R31】。**CUDA 13 从"推荐"变成了硬性要求**——源文档在这里是**低估**了要求，不是高估。

> **所以正确的说法是**：CUDA 13 是**必须**（当前版本已不发布 CUDA 12 镜像）【R31】；而"为了 FlashInfer 线性注意力性能"这个理由**只对 B200/GB200 成立**，在 5090 上不适用【R32】。

**边界三：第 5 条和第 6 条修的是完全不同的东西。**
`--mem-fraction-static` 治**显存**，共享内存治**进程间通信**。在容器里排查"服务起不来"时，先确认共享内存，再怀疑显存配额。

**边界四：第 5 条的方向可能与官方建议相反。**
`--mem-fraction-static` 的**默认值是自动计算**的：`mem_fraction_static = (GPU memory capacity - activations - cuda graph buffers) / GPU memory capacity`，检测不到显存时回落到 0.88【Research-derived · R37】。官方 FAQ 的建议是"**显存不足时可以调小** `--mem-fraction-static`，比如 0.8 或 0.7"【R37】——**方向是调小，不是调大**。

源文档说的"调大到 0.85~0.90 为 KV Cache 留足空间"【S15】是一种**手动固定**的做法，它会覆盖掉 SGLang 按显存自动联动的调度（那个逻辑会同步调整 `chunked_prefill_size` 与 CUDA Graph 的 `max_bs`）。**这不是错，只是要知道你在放弃什么**：手动固定换来的是可预测的显存占用，代价是失去按卡调优的空间。

**边界五：第 2 条在 SM120 上不是"必须选 FlashInfer"。**
官方文档对 SM120 的表述是 "`triton` **or** `flashinfer` for prefill/full attention"【R32】；`flashinfer` 是 SGLang 的**默认**注意力后端，但不是 SM120 上的强制项。**不过**：NVFP4 的 GEMM 路径确实需要 FlashInfer【R34】，而且已知 #40558 正是 FlashInfer TRT-LLM MoE autotune 在 SM120 上抛 `Unsupported architecture`【R33】。**实践建议**：以 FlashInfer 起步，**把它当默认值而不是教条**——真出问题时先试 `triton`。

---

<a id="step-4-cold-start"></a>

## 3.5 第四步：冷启动的两个层次

### 3.5.1 层次一：R-Fork（权重复用）

| 项 | 内容 |
|---|---|
| **定位** | "SGLang原生的'热启动'方案"；"从零冷启动的最快路径"【S17】 |
| **机制** | 新实例通过高速 GPU-to-GPU 通道，"**从已运行的实例零拷贝加载模型权重**"【S17】 |
| **收益** | "将权重加载时间从**数分钟压缩到数秒**"【S17】 |
| **角色划分** | **Seed 实例**：正常启动 `python -m sglang.launch_server [args]`【S18】；**新实例（Client）**：增加远程加载参数，从 Seed 拉取权重【S19】 |
| **后端** | `--remote-instance-weight-loader-backend nccl`；若用 `transfer_engine`，**Seed 实例**需额外加 `--remote-instance-weight-loader-start-seed-via-transfer-engine`【S19】【S20】 |

> **命名核对通过**：源文档写的 "**R-Fork（Tensor Remote Fork）**" **是官方名称，不是自造词**。官方文档原文："R-Fork (Tensor Remote Fork) is a novel weight loading methodology that leverages efficient inter-node GPU-to-GPU data transfer path to load tensors from a running SGLang instance to a new instance with zero-copy."【Research-derived · R23】；官方博客《Let Tensors Fly》也用 "Tensor R-Fork (stands for Tensor Remote Fork)"【R24】。

**边界**：

| 边界 | 说明 |
|---|---|
| **只解决权重加载** | 它跳过的是 ① 段，不跳过图编译与运行时初始化（见 [02 节](02-core-concepts.md#cold-start-costs) 的成本拆解） |
| **需要常驻 Seed 实例** | 没有正在运行的 Seed，权重复用就无从谈起【S18】 |
| **需要额外一个进程占资源** | Seed 实例本身要占一张卡的显存与一份主机内存 |
| **两端必须能互访** | 需要 Seed 的服务端口可达，且两端在可做 GPU-to-GPU 传输的物理域内 |
| **收益数字尚无官方基准** | "零拷贝""数分钟压缩到数秒"是**源文档的说法**【S17】，与官方文档的措辞一致【R23】。但**官方没有发布任何加速倍数或前后对比表**——R-Fork 评测用的是 **8×H20 + DeepSeek-R1**【R24】，**不是 RTX 5090**。请把它当成**待实测**的假设，不要给它安一个 "N×" |
| **⚠️ NCCL 后端还需要一个源文档漏掉的参数** | 官方文档写明 `--remote-instance-weight-loader-send-weights-group-ports` 是 **nccl 后端必需的**（"the list of available ports on the seed instance that will be used to build NCCL communication groups… Only needed by `nccl` backend"）【R25】。**源文档给的 NCCL 命令照抄是跑不通的**——见 [04 · 4.6.1](04-usage.md#461-rfork从运行中的实例拉权重) |
| **⚠️ Seed 与 Client 的并行策略必须一致** | 源码与官方文档都写明："Only support loading weights from instance with **same parallelism strategy**"【R25】。**TP 布局不一致就传不了** |
| **⚠️ NCCL 后端会打扰 Seed 的推理** | 官方文档："weight transfer disrupts the source instance's inference service"，传输期间会有延迟尖峰；且建通信组本身要数百毫秒【R25】 |
| **⚠️ `transfer_engine` 有额外依赖与已知冲突** | 需要装 `mooncake`；内存注册（`register_mr`）受 RDMA 驱动影响可能耗时数秒（可与其他初始化阶段重叠）；且该后端**与 HiCache 不兼容**【R25】 |
| **参数拼写请以 `--help` 为准** | 源码里的字段名是下划线形式（`remote_instance_weight_loader_seed_instance_ip`），命令行一般由 argparse 自动转成连字符；`--load-format remote_instance` 的取值也需核对。**源文档给的是 flag 字符串，不等于当前版本的正确拼写**【R22】 |

### 3.5.2 层次二：NVIDIA Snapshot（秒级恢复）

| 项 | 内容 |
|---|---|
| **定位** | "目前冷启动速度的**天花板**"；"生产级秒级弹性"【S21】 |
| **机制** | 对已完全初始化的 GPU 工作负载（"含CPU和GPU内存状态"）做检查点；恢复时"**跳过权重加载、图编译等全部初始化步骤**"【S21】 |
| **收益** | 推理副本上线时间压缩到 **3.6 ~ 42.7秒**，相比分钟级冷启动加速 **8~36倍**【S21】 |
| **后端支持** | "它**支持SGLang作为后端**"【S21】 |
| **运维要求** | "预先启动好服务、拍下快照"【S22】 |

**外部核对：数字与后端支持都成立，但有三处源文档没提的限制**

| 核对项 | 结论 | 证据 |
|---|---|---|
| 数字 3.6–42.7s / 8–36× | ✅ **完全属实**。官方博客与 `docs/overview/performance.md` 一致，且**区间的两个端点都是 SGLang 的行**（下界 Qwen3-0.6B/SGLang/TP1 = 3.59s；上界 DeepSeek-V4-Pro-NVFP4/SGLang/TEP8 = 42.69s） | 【R19】【R26】 |
| 支持 SGLang | ✅ 仓库有专门的 SGLang 指南与现成 manifest（`qwen3-0.6b.yaml`、`deepseek-v4.1-flash.yaml` 等） | 【R20】 |
| "**生产级**秒级弹性" | ⚠️ **与官方自述相冲突**。官方仓库 README 明写："Snapshot's APIs may still change, so it is **not yet recommended for production-critical workloads**" | 【R20】 |
| 基准的适用条件 | ⚠️ 官方基准跑在 **NVIDIA B200**（1/2/4/8 GPU）、driver 615.71.09、Snapshot v0.2.0-rc.2、**SGLang 0.5.21**、存储 VAST NFSv3 over TCP 之上 | 【R26】 |

**边界**：

| 边界 | 说明 |
|---|---|
| **快照有存储成本** | 需要保存 GPU + CPU 内存状态，体积不小。官方数据里快照**远大于**权重（例：gpt-oss-120b SGLang TP4，权重 65.25GB → 快照 **693.89GB**，因为含 CPU 状态、GPU 状态与 rootfs 归档）【R26】 |
| **快照是某一时刻的状态** | 拍完之后模型权重/配置若变更，快照不会自动跟随 |
| **它解决"恢复"，不解决"扩容"** | 源文档自己区分了两种需求："无论是故障恢复还是闲置缩容后的唤醒"【S22】——两者都是**把已有的东西恢复回来**，不是**创造新的副本**。真正需要扩容时，仍然要走正常启动路径。 |
| **⚠️ 它是 Kubernetes-only 的** | 官方仓库自述为 "a Kubernetes-native checkpoint and restore system for NVIDIA GPU workloads"，并要求 "use Kubernetes custom resources"【R20】。**源文档设想的 5 节点裸机 SSH 部署无法直接使用 Snapshot**——这是本课程核对出的**最实质的一条落差** |
| **⚠️ 多 GPU 只支持单节点** | 官方限制原文："Workloads, including multi-GPU workloads, must run on a single node. **Multi-node is on the roadmap.**"【R20】【UQ9】——**跨节点恢复尚未支持**，因此**情况 B 的跨 5 节点 PP 实例整体无法被快照** |
| **⚠️ 还有一堆前置条件** | Linux kernel 5.13+、NVIDIA GPU Operator 26.3+、内核态驱动 580+、containerd 2.2+ / NRI v0.10+、多 GPU 恢复还需要 `libcuda.so` 615+（GPU CustomStorage）、`ReadWriteMany` 存储类、特权 DaemonSet（hostPID/hostIPC/hostNetwork）【R20】 |
| **⚠️ 3.6–42.7 秒只是"恢复段"** | 官方明确 "infrastructure provisioning and container image loading remain outside the measured restore path"——**镜像拉取、Pod 调度、运行时初始化都不计入**【R19】【R20】 |
| **⚠️ 别和 Dynamo Snapshot 搞混** | 另有一个更早的 **NVIDIA Dynamo Snapshot**，是实验性产品，官方甚至警告 "for larger models, the restore time actually exceeds that of a cold start"【R27】。当前独立的 `ai-dynamo/snapshot` 才是源文档说的那个 |

> **这一条区分很重要**：源文档批评 KServe Scale-to-Zero 时用的说法是"KServe Scale-to-Zero那种分钟级冷启动"【S22】。但**缩容到 0 之后要拉起新副本**，本质上是**扩容**而非**恢复**——快照恢复帮不上这个忙，除非你的工作流是"先起后拍、再恢复"。这是本课程对源文档的一个**补充判断**。

---

## 3.6 第五步：编排与路由

| 项 | 内容 |
|---|---|
| **路由层** | "**SGLang Router（现称Model Gateway）** 是官方推荐的多实例路由方案，支持DP场景下的请求分发"【S23】 |
| **启动方式** | "20卡多节点场景下，**不建议手动逐个SSH启动**"【S23】 |
| **上层编排** | 网络为 InfiniBand 或高速 RoCE 时，可用 Ray Serve 把 SGLang 实例作为部署单元管理，实现统一的扩缩容和故障恢复【S24】 |
| **弹性来源** | "**冷启动弹性不应依赖Ray/K8s的默认调度**，而应通过**NVIDIA Snapshot**实现秒级恢复"【S24】 |

**边界**：

| 边界 | 说明 |
|---|---|
| **Router 管分发，不管冷启动** | 它解决"请求发给谁"，不解决"新实例怎么快速起来" |
| **编排层的能力 ≠ 弹性能力** | 源文档明确把弹性从 Ray/K8s 的默认调度中**剥离**出来交给 Snapshot【S24】——这是本方案里最值得注意的一个架构判断 |
| **大模型场景的路由不同** | 源文档的架构图显示，DP 场景路由到 20 个副本，大模型场景路由到 PP 组【S25】——路由的对象从"副本"变成了"模型组"。⚠️ 但**官方文档不支持"路由到 PP 组"**：`sgl-router` 自述为 "A router serves one model and spreads its requests across that model's SGLang **engines**"【R15】——它把请求分发到**完整的 SGLang 实例**，不是流水线 stage 组 |

### 外部核对：源文档的路由层主张基本成立，但有四处需要修正

**① 名字改了两次，源文档写的是中间态。** 源文档说"SGLang Router（**现称** Model Gateway）"【S23】。实际历史是：

| 时间 | 名称 | 证据 |
|---|---|---|
| 2024-12 | `sglang-router`（"SGLang DP Router"） | LMSYS v0.4 博客，`pip install sglang-router`【R9】 |
| **2025-10-23** | 改称 **"SGLang Model Gateway"（SMG）**，"fully rebuilt and renamed as 'SGLang Model Gateway'" | LMSYS 官方公告【R10】 |
| **2026-11（SGLang 1.0）** | **改回 `sgl-router`**；`sgl-model-gateway` 在 1.0 中弃用 | SGLang 1.0 跟踪 issue【R11】 |

**结论：当前应称 `sgl-router`**【R11】。源文档的"现称 Model Gateway"只在一个时间窗口内成立。

> **顺带消歧**：还有一个**独立的**项目也叫 "Shepherd Model Gateway (SMG)"，由 LightSeek 基金会维护，定位是引擎无关的 Rust 网关【R9】。**三个不同的 "SMG"** 在流通，看到这个词时先确认指的是哪一个。

**② "官方推荐"这个说法，比源文档说得更成立。** SGLang 官方 DP 文档写的是：

> "**We strongly recommend using the SGLang Model Gateway (SMG) for production-grade Data Parallelism.** SMG provides significant advantages over native DP mode."【Research-derived · R12】

并且对原生 DP 模式明确不推荐："Native DP is **highly not recommended for use right now**"【R12】。**这比源文档的"官方推荐"更强**——官方推荐的是**用网关做 DP**，而不是 SGLang 自带的 `--dp-size` 原生 DP。

**③ 路由策略有官方清单**【R12】【R15】：`random`、`round_robin`、`power_of_two`、`cache_aware`（默认）、`bucket`；1.0 之后的 `sgl-router` 还提供 `session_aware`。

**④ "冷启动弹性不应依赖 Ray/K8s 默认调度"是源文档作者的主观主张，不是官方建议。** Ray 官方的 benchmarks 文档承认 "Replica startup times involving large models can be slow"【R18】，但**没有任何官方文档说不要依赖自己的调度器**【R18】。把它标成"源文档主张"比标成"官方建议"更诚实【UQ7】。

---

## 3.7 能力边界汇总

| 能力 | 成立的前提 | 什么时候失效 |
|---|---|---|
| **纯 DP（情况 A）** | 模型完整装进 32GB | 模型超过单卡容量 |
| **TP×PP（情况 B）** | TP 不跨 PCIe 域；节点间有高速网络 | PCIe 域被切碎；网络不够快 |
| **NVFP4 量化** | 有对应 NVFP4 检查点 | 只有 BF16/FP8 检查点 |
| **FlashInfer 后端** | 后端与当前 SM_120 兼容 | 长提示 TTFT 未改善则说明选错了后端 |
| **R-Fork** | 有常驻 Seed 实例；两端可互访 | Seed 挂了；跨不可达域 |
| **NVIDIA Snapshot** | 有可用的快照存储；需事先拍摄；**跑在 Kubernetes 上** | 需要"扩容"而非"恢复"时；**裸机多节点部署** |
| **Router** | 有多个同构副本 | 副本异构（不同模型/不同并行度） |
| **Ray Serve 编排** | Ray Serve 的 SGLang 集成足够成熟 | 官方标注为"early development"，功能有缺口【R16】 |

---

## 本节小结

- 方案调用了 SGLang 的**四类能力**：并行执行、Blackwell 适配、冷启动加速、路由分发。
- **每一步都有产出物**：拓扑→TP 上限；模型规格→分支选择；SM_120→六个必配项；冷启动需求→两个层次；副本数→路由层。
- **每条建议都有边界**：DP 受单卡容量限制，TP×PP 受 PCIe 域与网络限制，R-Fork 只省权重加载，Snapshot 恢复而不扩容。
- 源文档的**型号与分数主张**（S6）经外部核对后**基本成立，但有三处需要修正**（"官方验证"的归因、"W4A4"的精度口径、GSM8K 区间的含义），详见 [3.3.3](#model-choice)。
- 三条**外部证据揭示的落差**要记住：**TP"绝对不能"跨节点**比官方指导更强【R14】；**Snapshot 是 Kubernetes-only**【R20】；**Ray Serve 的 SGLang 支持官方标注为早期开发**【R16】。

**下一节**：[04 · 使用方法](04-usage.md) —— 把前面四节变成一条可以照着跑的路径。
