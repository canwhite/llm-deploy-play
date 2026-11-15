# 02 · 核心概念：并行、精度与冷启动

> **学习目标**
> 完成本节后，你应该能够：
> 1. 说出 TP / PP / DP 三种并行**各自在什么层级通信**，以及为什么这个差异决定了它们能否跨节点；
> 2. 解释"**TP 不能跨 PCIe Switch 边界**"这条铁律背后的机制；
> 3. 说清 **NVFP4 / FP8 / BF16** 三种精度的取舍维度，以及它们如何直接决定"模型塞不塞得下单卡"；
> 4. 把"**冷启动慢**"拆成三种**互不相同**的成本，并指出源文档的两个冷启动方案各解决哪一段；
> 5. 说明 `tp × pp = 20` 这个等式的**成立前提**。

### 证据标签约定

`【Source-derived · Sxx】` 来自根文档 `source-sglang.md`；`【Research-derived · Rxx】` 来自外部权威来源；`【Illustrative】` 为教学性构造，不主张 SGLang 的未经验证行为。完整定位码与出处见 [07 · 验证记录](07-verification-record.md)。

---

<a id="parallelism"></a>

## 2.1 三种并行：通信发生在哪一层

源文档的并行策略可以浓缩成一张表。**这张表是全课程最该背下来的一张**：

| 并行方式 | 切分什么 | 通信发生在哪一层 | 通信频率 | 跨节点可行性（源文档判断） |
|---|---|---|---|---|
| **TP**（张量并行） | 模型层**内**的权重 | 每一层的前向/反向都要做 **All-Reduce**【Illustrative】 | **每层**【Illustrative】 | **不可**——不能跨节点或跨 PCIe Switch【S2】 |
| **PP**（流水线并行） | 模型按**层**切成若干 stage | 只在**流水线阶段边界**做点对点通信 | 每个 stage 边界 | **可**——"对跨节点网络要求远低于TP"【S4】 |
| **DP**（数据并行） | **不切模型**，每个副本各持一份完整权重 | 副本之间**零通信** | **无** | **可**——GPU 之间"零通信开销"【S5】 |

源文档据此给出了那条总原则：**节点内只做 TP，跨节点只做 PP 或 DP**【S3】【S4】。

**这条原则有官方文档背书**。SGLang 官方的流水线并行文档写得很直白：

> "Although Tensor Parallelism (TP) remains the conventional approach for intra-node scaling, it frequently encounters communication bottlenecks during multi-node deployments. On the other hand, pipeline parallelism only requires cross-node communication at the boundaries of each pipeline stage, which can achieve better computation-communication overlap compared to a large TP."【Research-derived · R13】

数据并行一侧，源文档自己的说法是“GPU 之间零通信开销”【Source-derived · S5】；SGLang 官方文档同时提醒 **native DP “highly not recommended”**，生产级 DP 建议走 Model Gateway【Research-derived · R12】。

> **一处需要如实标出的措辞差异**：源文档写的是"**绝对不能**跨节点"【S2】。SGLang 官方的多节点部署文档里**确实有 TP 跨节点的示例**（`--tp 16 --nnodes 2`，8 卡 × 2 节点）【Research-derived · R14】。所以更准确的说法是：**在 PCIe-only、无 NVLink 的互联条件下，TP 跨节点是强烈不推荐的**——它的**方向**是对的，但"绝对不能"比官方指导更强。至于"跨 PCIe Switch 边界"这个具体措辞，**官方文档里没有对应表述**【R14】【UQ8】。本课程保留源文档的措辞，但把它标为**源文档的主张**而非官方规则。

### 为什么 TP 对互联最敏感

机制上，TP 把同一层的权重沿某个维度切开，因此**每个 transformer 层的输入与输出都必须在卡间重新拼接**——这意味着 TP 的通信不是"偶尔发生一次"，而是**每层、每步都要发生**。相比之下：

- **PP** 只在 stage 交接处通信，stage 内部（若干层）是纯本地计算；
- **DP** 根本不通信——每个副本独立处理自己的请求，副本之间没有任何数据依赖。

> **把通信频率和通信量乘起来，才是代价。** TP 是"高频 × 大消息"，PP 是"低频 × 小消息"，DP 是"零"。这解释了为什么在**没有 NVLink** 的机器上，把 TP 扩大到跨节点会立刻成为瓶颈——源文档的原话是"跨边界TP的All-Reduce通信会成为严重瓶颈"【Source-derived · S2】。

【Illustrative】 一个便于记住的类比：TP 像**几个人共同抬一张长桌子**——每走一步都要重新对位；PP 像**接力赛跑**——只在交接棒的那一刻需要沟通；DP 像**八个人各抬一张小桌子**——各干各的，永不沟通。桌子越大、抬得越快（层数越多、token 越多），第一种的协调成本越可怕。

---

<a id="precision"></a>

## 2.2 精度的取舍：它直接决定"塞不塞得下"

源文档在 Blackwell 章节给出的量化要求是：**NVFP4（首选）或 FP8**，理由是"**BF16显存不够**"【Source-derived · S11】。

这就把三件事连成了一条因果链：

```
模型参数量（固定）
      ↓ ÷ 每参数字节数
权重占用显存
      ↓ 32GB 减去权重、运行时开销
留给 KV Cache 的空间  →  决定能并发多少请求
```

**精度的选择不是"质量 vs 速度"的取舍，而是"能不能装下"的前置条件**。降精度换来的是两样东西：

1. **权重变小** → 腾出显存给 KV Cache → 源文档据此说"NVFP4权重更小，可适当提高并发"【S15】；
2. **算力变快** → 4-bit 的 Tensor Core 吞吐显著高于 8-bit。

**"每参数字节数"到底怎么算**：NVFP4 不是简单的 4 bit/参数。NVIDIA 的官方技术博客给出了确切定义：NVFP4 的元素是 **E2M1（4 bit：1 符号 + 2 指数 + 1 尾数）**，每个 **16 个值的 micro-block** 共享一个 **E4M3 的 FP8 scale**，整个张量再叠加一个 **FP32 的 per-tensor scale**——因此**实际是 4.5 bit/参数**【Research-derived · R5】。相对 FP16 约省 **3.5×** 显存，相对 FP8 约省 **1.8×**【R5】。

> **注意它和 MXFP4 不是一回事**。NVFP4 用 **16** 元素分块 + E4M3 scale【R5】；MXFP4 是另一套分块规则（OCP 开放标准，**32** 元素分块 + E8M0 scale）——**这段对比是本课程的补充说明**【Illustrative】。在 Blackwell 上两者都受 TensorRT-LLM 的格式矩阵支持【R8】——**注意 R8 说的是 TensorRT-LLM 的量化格式矩阵，与 SGLang 命令行的取值名是两回事**（后者见 R30）；两种格式的检查点**不能互换**。

RTX 5090 的硬件层面也支持这套格式：RTX Blackwell 架构白皮书写明 "RTX Blackwell adds new support for FP4 and FP6 Tensor Core operations"，并配有第二代 FP8 Transformer Engine【Research-derived · R7】。

源文档在第三步给出了一张表，其中与精度相关的两行是：

| 配置项 | 必须设置 | 原因 |
|---|---|---|
| **量化** | **NVFP4（首选）或 FP8** | BF16显存不够；NVFP4是Blackwell原生格式，SGLang官方已验证RTX 5090单卡可跑【S11】【R1】 |
| **FP8 MoE注意** | 部分FP8 MoE路径在SM_120上**加载时会挂起** | 优先选用**NVFP4**检查点，避开FP8 MoE的已知问题【S13】 |

> **注意这两行不是并列的备选项，而是有优先级的**。源文档把 FP8 列为"可用"，但又指出 FP8 MoE 在 SM_120 上有加载挂起的已知问题——所以它给的实际建议是"**优先选用 NVFP4 检查点**"。在有 NVFP4 检查点可用时，FP8 不该是首选。

> ### ⚠️ 外部核对：源文档这条告警**按原措辞不成立**，但结论方向是对的
>
> 源文档说"部分 FP8 MoE 路径在 SM_120 上**加载时会挂起**"【S13】。在 SGLang 的 issue tracker 里用多种检索组合**没有找到**一条同时满足「FP8 + MoE + 挂起 + SM120/RTX 5090 + 发生在权重加载期间」的 issue【Research-derived · R33】。**最接近的是 #40558**（OPEN）：在 **RTX PRO 6000 Blackwell**（compute capability 12.0）上，"the server hangs or abruptly terminates during the **FlashInfer autotune phase**"，日志里有 "Detected fp8 checkpoint." 与 "FlashInfer TRTLLM MoE is enabled."——但挂起发生在**权重加载之后**的 autotune 阶段，**不是加载期间**，且报告者说 "triton is currently the only backend that boots and serves"【R33】。
>
> **准确的说法应该是**：在 SM120 上，某些 FP8 / MoE 模型组合**会在启动阶段失败**——FlashInfer 的 TRT-LLM MoE autotune 会抛 `Unsupported architecture`（#40558，仍 OPEN）；而 **block-scaled FP8 在 SM120 上直到 2025-08 才获得支持**（#9233，已关闭）——**这两个状态与日期以 R33 记录的 issue 页面为准**【R33】【UQ4】。
>
> **结论方向不变**：**优先选 NVFP4 检查点**，这是稳妥的；但**别把这条挂给 FP8 本身**。另外还有一个**与本方案高度相关**的坑：#15181 报告在两张 Blackwell 卡上做 TP 时 "If I do not set `NCCL_P2P_DISABLE=1`, the process hangs indefinitely"（拓扑为 `NODE`，无 NVLink）【R33】——**20 张无 NVLink 的 5090 做 TP 时必须注意这一点**。

---

## 2.3 显存预算：`--mem-fraction-static` 与共享内存是两回事

源文档列出的 Blackwell 必配项里，有两条经常被混为一谈，其实分属**完全不同的资源**：

| 项 | 是什么 | 作用 | 出处 |
|---|---|---|---|
| `--mem-fraction-static` **0.85 ~ 0.90** | **GPU 显存**中预留给静态部分（权重 + KV Cache 池）的**比例** | "为KV Cache留足空间" | 【S15】【R37】 |
| **共享内存**（Docker `--shm-size` / K8s `/dev/shm`） | **主机内存**中的一块共享内存区域 | "SGLang进程间通信依赖共享内存" | 【S16】 |

**两者的失效表现完全不同**：

- `--mem-fraction-static` 设得太大 → 启动时 KV Cache 池分配失败，或可用并发低于预期；
- 共享内存不足 → 进程间通信异常（在容器里常见的表现是服务卡住或崩溃）。

> **实践纪律**：容器部署 SGLang 时，`--shm-size` 缺失是一个**独立的、必须显式设置**的参数，不是可以省略的默认值【S16】。它和显存无关，调 `--mem-fraction-static` 解决不了它。

> **两条外部核对，方向都与源文档不同**：
> - **`--mem-fraction-static` 的默认值不是 0.85，而是“自动计算”**。官方文档原文：“When unset, it is computed as `(GPU memory - reserved memory) / GPU memory`, defaulting to `0.88` if GPU memory cannot be detected”【Research-derived · R37】。**官方 FAQ 的建议方向和源文档相反**——它说的是“**显存不足时可以调小** `--mem-fraction-static`，比如 0.8 或 0.7”，而不是调大留 KV Cache 空间【Research-derived · R38】。（另注：文档写检测不到显存时回落到 0.88，源码的兜底分支写 0.95，两者不一致——正常情况下能探测到显存，不走回退分支【UQ12】。）**源文档给的 0.85~0.90 属于"手动固定"的做法，会覆盖掉 SGLang 按显存自动调度的逻辑**（那个逻辑会联动 `chunked_prefill_size` 与 CUDA Graph 的 `max_bs`）。
> - **共享内存的官方数值是 `32g`**。SGLang 官方安装文档的启动示例统一用 `--shm-size 32g`（docs 全文出现 23 次 `32g` 写法），K8s 侧的官方清单用 `emptyDir: medium: Memory` 挂载到 `/dev/shm`【Research-derived · R31】。⚠️ 注意官方 K8s 清单**没有设 `sizeLimit`**，也把 `hostIPC: true` 作为替代方案——**"K8s 侧等价于 32g"是推断，不是官方文档的事实**【R31】。

---

<a id="cold-start-costs"></a>

## 2.4 冷启动的三段成本（本节的核心）

源文档把冷启动分成"两个层次"【S17】【S21】，但从机制上看，真正需要区分的是**三段成本**。把这两层和三段对齐，是理解整个冷启动章节的关键：

| # | 成本段 | 做什么 | 量级 | 谁来解决 |
|---|---|---|---|---|
| **①** | **权重加载** | 从磁盘/网络把模型权重搬进显存 | 大模型上**数分钟** | **R-Fork**：从已运行实例"零拷贝加载"，"数分钟压缩到数秒"【S17】 |
| **②** | **图编译 / 运行时初始化** | CUDA graph 捕获、kernel 预编译、显存池规划 | 从秒到分钟不等 | **NVIDIA Snapshot**：恢复时"跳过权重加载、图编译等全部初始化步骤"【S21】 |
| **③** | **副本上线** | 服务真正开始接受请求 | 完成后即可服务 | 两者都需要 |

### 两个冷启动方案，分别解决哪一段

| 方案 | 层次 | 解决 ① | 解决 ② | 解决 ③ |
|---|---|---|---|---|
| **R-Fork**（权重复用） | 层次一：从零冷启动的最快路径【S17】 | ✅ **这是它的全部** | ❌ | ❌ |
| **NVIDIA Snapshot** | 层次二：生产级秒级弹性【S21】 | ✅ | ✅ | ✅ |

源文档对 R-Fork 的定位是"SGLang原生的'热启动'方案"，机制是"允许一个新实例通过高速GPU-to-GPU通道，**从已运行的实例零拷贝加载模型权重**"【S17】——它**只搬权重**。而 NVIDIA Snapshot 的定位是"对已完全初始化的GPU工作负载（含CPU和GPU内存状态）做检查点，恢复时**跳过权重加载、图编译等全部初始化步骤**"【S21】。

> **两条外部核对结果，方向不同**：
> - **R-Fork 的收益数字没有官方基准**。"零拷贝"与"数分钟压缩到数秒"是**源文档的说法**【S17】；在 SGLang 仓库里能确认的是那组 `--remote-instance-weight-loader-*` 参数**确实存在**【Research-derived · R22】，但**没有找到官方发布的权重加载耗时对比**，官方评测也只在 8×H20 + DeepSeek-R1 上做过【R24】。请把它当成**待实测**的假设，而不是既定结论【UQ3】。
> - **NVIDIA Snapshot 的数字有官方出处，但有源文档没提的硬限制**。官方博客确认 "Restoring from a Snapshot artifact brings inference replicas online in **3.6 to 42.7 seconds** across tested configurations, delivering **8x to 36x speedups** over cold starts that take minutes"，并明确 "NVIDIA provides ready-made examples for vLLM, **SGLang**, and NVIDIA TensorRT LLM"【Research-derived · R19】。**但** Snapshot 官方定位是 "a checkpoint and restore system for GPU workloads **on Kubernetes**"，且多 GPU 支持限定为 "compatible workloads that span multiple GPUs **on a single node**"【R20】——**源文档设想的 5 节点裸机 SSH 部署不在它的适用范围内**。详见 [05 · 5.2.2](05-related-tools.md#522-nvidia-snapshot)。

> **这张表解释了为什么源文档坚持"生产弹性用 NVIDIA Snapshot"**【S24】：R-Fork 能把“数分钟”压到“数秒”，但它**压不掉图编译**——后者是本课程依据 S17“只搬权重”的描述所做的推断【Illustrative】。当你的痛点是"缩容到 0 之后唤醒"，或者"滚动升级要等多久"，压掉的那段才是关键。

**代价也要说清楚**：这两条路都要**预先付出成本**。R-Fork 要求**有一个 Seed 实例正在运行**（源文档给的角色划分是：Seed 实例正常启动，新实例作为 Client 从它拉权重）【S18】【S19】；Snapshot 要求**事先启动好服务、拍下快照**【S22】。它们把"每次冷启动的等待"换成了"始终维持一份已就绪的副本或快照"。

---

## 2.5 术语速查表

| 术语 | 一句话解释 | 出处 |
|---|---|---|
| **TP**（张量并行） | 把同一层权重切开，每层都要 All-Reduce【Illustrative】 | 【S2】【S3】 |
| **PP**（流水线并行） | 按层切成 stage，只在边界通信 | 【S4】【S7】 |
| **DP**（数据并行） | 每个副本一份完整权重，互不通信 | 【S5】 |
| **PCIe 域 / PCIe Switch** | TP 不能跨越的物理边界 | 【S2】【S3】 |
| **NVLink** | GPU 间高速直连；RTX 5090 **没有** | 【S2】 |
| **SM_120** | RTX 5090（Blackwell 消费版）的计算能力代号 | 【S13】 |
| **NVFP4** | Blackwell 原生的 4-bit 浮点权重格式，源文档的首选量化；实际 **4.5 bit/参数** | 【S11】【R5】 |
| **`--quantization` 的合法取值** | **不含 `nvfp4`**。NVFP4 检查点对应的是 `modelopt_fp4` / `nvfp4_online` / `petit_nvfp4` / `mxfp4` 等取值 | 【R30】 |
| **MXFP4** | 另一套 4-bit 分块格式（32 元素分块 + E8M0 scale），**与 NVFP4 不可互换** | 【Illustrative】【R8】 |
| **FP8** | 8-bit 浮点，备选；SM120 上部分 FP8/MoE 组合会在**启动阶段**失败（见 [2.2](#precision)） | 【S11】【S13】【R33】 |
| **W4A4** | 权重 4-bit、激活 4-bit 的量化形态 | 【S6】 |
| **KV Cache** | 每个请求的注意力缓存；占用显存，决定并发上限 | 【S15】 |
| **`--mem-fraction-static`** | 预留给静态部分（权重 + KV Cache）的显存比例 | 【S15】 |
| **R-Fork** | 从运行中的实例零拷贝复用权重的冷启动方案 | 【S17】【S19】【R22】 |
| **Seed 实例** | R-Fork 中提供权重的那个已运行实例 | 【S18】 |
| **NVIDIA Snapshot** | 对已初始化 GPU 工作负载做检查点、秒级恢复的方案（**Kubernetes 限定**） | 【S21】【R19】【R20】 |
| **SGLang Router** | 多副本请求分发层（现名 `sgl-router`） | 【S6】【S23】【R9】【R11】 |

---

## 本节小结

- **TP 每层都要通信**，PP 只在 stage 边界通信，DP 完全不通信——这个差异决定了"**张量并行（TP）绝对不能跨节点或跨PCIe Switch边界**"【S2】【S4】【S5】。
- **精度决定装不装得下**：BF16 装不下 → 选 NVFP4（首选）或 FP8；权重变小还能换来更高并发【S11】【S15】。
- **显存预算与共享内存是两件事**：前者调 `--mem-fraction-static`，后者调容器的 `--shm-size`【S15】【S16】。
- **冷启动有三段成本**：权重加载、图编译/初始化、副本上线。R-Fork 只解决第 ① 段，NVIDIA Snapshot 三段都跳过——这是两者定位不同的根本原因【S17】【S21】。
- `tp × pp = 20` 成立的前提是 **TP 恰好吃满一个 PCIe 域、PP 覆盖其余节点**，不是恒等式【S7】。

**下一节**：[03 · 核心功能](03-core-functionality.md) —— 逐条走完源文档的五步，看每个决策的能力边界在哪里。
