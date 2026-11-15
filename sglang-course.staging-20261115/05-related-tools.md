# 05 · 相关工具

> **学习目标**
> 完成本节后，你应该能够：
> 1. 用**分层模型**给源文档提到的每个工具定位，说清它们**不在同一层**；
> 2. 说出每个工具与 SGLang 的**重叠面**与**差异面**；
> 3. 在具体场景下选出该用哪个工具——而不是凭"哪个更流行"；
> 4. 识别源文档对 KServe 的批评**是否成立**，以及它在什么前提下成立；
> 5. 说出本课程核对出的**三条最实质的落差**（见 [5.7](#57-三条最实质的落差)）。

### 证据标签约定

`【Source-derived · Sxx】` 来自根文档 `source-sglang.md`；`【Research-derived · Rxx】` 来自外部权威来源；`【Illustrative】` 为教学性构造，不主张 SGLang 的未经验证行为。完整定位码与出处见 [07 · 验证记录](07-verification-record.md)。

---

## 5.1 先分层：这些工具根本不在同一层

源文档提到了四个工具——SGLang Router、NVIDIA Snapshot、Ray Serve、KServe【S6】【S21】【S23】【S24】【S22】。把它们并排比较"谁更好"是**范畴错误**：它们分属不同的层，解决的不是同一个问题。

【Illustrative】 本课程用下面这个分层模型来定位它们。**这个分层是本课程的教学框架**，不是任何一方的官方分类：

| 层 | 职责 | 本方案里涉及的工具 |
|---|---|---|
| **① 量化与内核层** | 决定权重怎么存、算子怎么跑 | NVFP4 / FP8 量化格式、FlashInfer 后端【S11】【S12】 |
| **② 推理引擎层** | 把模型跑起来、暴露 API | **SGLang**（本方案选定） |
| **③ 路由层** | 把请求分发给多个实例 | **sgl-router**（源文档写作 "SGLang Router"）【S23】 |
| **④ 编排层** | 决定起几个实例、放哪台机器 | Ray Serve【S24】、KServe【S22】 |
| **⑤ 弹性层** | 让副本**秒级**回来 | NVIDIA Snapshot【S21】 |

**层的相邻关系是单向依赖**：② 依赖 ① 的能力；③ 需要知道 ② 的实例地址；④ 负责决定要起哪些 ③ 后端的实例；⑤ 在 ④ 拉起实例时**替代**常规启动路径。

> **这个模型立刻解释了源文档的一个关键判断**："**冷启动弹性不应依赖Ray/K8s的默认调度**，而应通过 **NVIDIA Snapshot** 实现秒级恢复"【S24】。为什么？因为**冷启动属于第 ⑤ 层的职责**，把它塞给第 ④ 层的默认调度，等于让编排层去做它不擅长的事。
>
> ⚠️ 但这个分工有个前提：Snapshot 本身**要求 K8s**【R20】。所以源文档实际上是在说"**要 K8s，但别指望 K8s 的默认调度给你秒级，要用 Snapshot**"——**这个组合是成立的**；只是它同时意味着**第 ④ 层的 KServe/Ray Serve 也得在 K8s 上**，源文档的"裸机 SSH 起服务"路线与之不兼容。详见 [5.7](#57-三条最实质的落差)。

---

## 5.2 源文档用到的四个工具

### 5.2.1 SGLang Router —— 路由层

| 项 | 内容 |
|---|---|
| **源文档定位** | "**SGLang Router（现称Model Gateway）** 是官方推荐的多实例路由方案，支持DP场景下的请求分发"【S23】 |
| **在这份方案里做什么** | 情况 A 下，在 20 个 DP 副本之间分发请求【S6】；情况 B 下，路由到 PP 组【S25】 |
| **源文档强调的一点** | "20卡多节点场景下，**不建议手动逐个SSH启动**"【S23】——Router 同时是**多实例的统一入口** |
| **它不做什么** | 它**不管副本怎么冷启动**。副本上线是第 ④/⑤ 层的事 |

> **名字改了两次，源文档写的是中间态。** 源文档说"SGLang Router（**现称** Model Gateway）"【S23】，但实际历史是：2024-12 是 `sglang-router`（当时叫 "SGLang DP Router"）→ 2025-10-23 改称 **"SGLang Model Gateway" (SMG)**（官方公告：fully rebuilt and renamed）→ **SGLang 1.0（2026-11）又改回 `sgl-router`**，并明确 "`sgl-router` … **replaces `sgl-model-gateway**"，"`sgl-model-gateway` is deprecated in 1.0"【Research-derived · R9】【R10】【R11】。
>
> **当前应称 `sgl-router`**【R11】。
>
> **顺带消歧**：另有一个**独立的** "**Shepherd Model Gateway (SMG)**"（LightSeek 基金会维护，引擎无关的 Rust 网关）【R9】。**流通中的 "SMG" 至少指三个东西**，看到它先确认是哪一个。源文档没有和 NVIDIA 的 AI Gateway / NIM 混淆——它指的确实是 SGLang 自己的产品【R9】。

**官方推荐强度比源文档说的更高**：

> "**We strongly recommend using the SGLang Model Gateway (SMG) for production-grade Data Parallelism.** SMG provides significant advantages over native DP mode." / "Native DP is **highly not recommended for use right now**."【Research-derived · R12】

**路由策略**【R12】【R15】：`random`、`round_robin`、`power_of_two`、`cache_aware`（默认，维护近似 radix tree 做前缀命中路由）、`bucket`；1.0 后的 `sgl-router` 另有 `session_aware`。**两代的清单与默认值并不一致**——请以你安装版本的 `--help` 为准【UQ11】。

**边界**：源文档的架构图显示，DP 场景路由到 20 个副本、大模型场景路由到 PP 组【S25】。⚠️ 但 **router 的工作单元是完整的 SGLang 实例，不是流水线 stage 组**——官方自述 "A router serves one model and spreads its requests across that model's SGLang **engines**"【R15】。**"路由到 PP 组"这个说法在官方文档里没有依据**；正确的做法是让每个 PP 组暴露为一个（或一组）可路由的实例。

<a id="522-nvidia-snapshot"></a>

### 5.2.2 NVIDIA Snapshot —— 弹性层

| 项 | 内容 |
|---|---|
| **源文档定位** | "生产级秒级弹性"；"目前冷启动速度的**天花板**"【S21】 |
| **机制** | 对已完全初始化的 GPU 工作负载（含 CPU 和 GPU 内存状态）做检查点；恢复时"**跳过权重加载、图编译等全部初始化步骤**"【S21】 |
| **收益** | 上线时间压缩到 **3.6 ~ 42.7秒**，相比分钟级冷启动加速 **8~36倍**【S21】 |
| **后端** | "它**支持SGLang作为后端**"【S21】 |
| **运维要求** | "预先启动好服务、拍下快照"【S22】 |

**外部核对：数字与后端支持都成立，但有四条限制源文档没提**【R19】【R20】【R26】：

| 核对项 | 结论 |
|---|---|
| 数字 3.6–42.7s / 8–36× | ✅ **完全属实**。官方博客与 `docs/overview/performance.md` 一致，且**区间的两个端点都是 SGLang 的行**（下界 Qwen3-0.6B/SGLang/TP1 = 3.59s；上界 DeepSeek-V4-Pro-NVFP4/SGLang/TEP8 = 42.69s） |
| 支持 SGLang | ✅ 仓库有专门的 SGLang 指南与现成 manifest（`qwen3-0.6b.yaml`、`deepseek-v4.1-flash.yaml`、`glm-5.3.yaml` 等） |
| 基准的适用条件 | ⚠️ 官方基准跑在 **NVIDIA B200**（1/2/4/8 GPU）、driver 615.71.09、Snapshot v0.2.0-rc.2、**SGLang 0.5.21**、存储 VAST NFSv3 over TCP。**不是 RTX 5090，也不是 20 卡** |
| "**生产级**" | ⚠️ 官方仓库 README 明写："Snapshot's APIs may still change, so it is **not yet recommended for production-critical workloads**" |

**边界**：

| 边界 | 说明 |
|---|---|
| **它解决"恢复"，不解决"扩容"** | 见 [03 · 3.5.2](03-core-functionality.md#step-4-cold-start) |
| **⚠️ Kubernetes-only** | 官方定位是 "a Kubernetes-native checkpoint and restore system for NVIDIA GPU workloads"，要求 Kubernetes 自定义资源【R20】 |
| **⚠️ 多 GPU 也只能单节点** | 官方限制原文："Workloads, including multi-GPU workloads, must run on a single node. **Multi-node is on the roadmap.**"【R20】 |
| **⚠️ 前置条件很硬** | Linux kernel 5.13+、NVIDIA GPU Operator 26.3+、内核态驱动 580+、containerd 2.2+/NRI v0.10+、多 GPU 恢复还需 `libcuda.so` 615+（GPU CustomStorage）、`ReadWriteMany` 存储类、特权 DaemonSet【R20】 |
| **⚠️ 那 3.6–42.7 秒只是"恢复段"** | 官方明确 "infrastructure provisioning and container image loading remain outside the measured restore path"——**镜像拉取、Pod 调度、运行时初始化都不计入**【R19】 |
| **⚠️ 快照体积远超权重** | 官方数据：gpt-oss-120b SGLang TP4，权重 65.25GB → 快照 **693.89GB**（含 CPU 状态、GPU 状态与 rootfs 归档）【R26】 |
| **⚠️ 别和 Dynamo Snapshot 搞混** | 另有一个更早的 **NVIDIA Dynamo Snapshot**，是实验性产品，官方甚至警告 "for larger models, the restore time actually exceeds that of a cold start"【R27】。当前独立的 `ai-dynamo/snapshot` 才是源文档说的那个 |

<a id="523-ray-serve"></a>

### 5.2.3 Ray Serve —— 编排层

| 项 | 内容 |
|---|---|
| **源文档定位** | "如果节点间网络是InfiniBand或高速RoCE，Ray Serve可以作为上层编排，将SGLang实例作为部署单元管理，实现统一的扩缩容和故障恢复"【S24】 |
| **触发条件** | 节点间网络是 InfiniBand 或高速 RoCE【S24】——这是**前提条件**，不是顺带一提 |
| **它负责什么** | 实例作为"部署单元"的统一扩缩容与故障恢复 |
| **它不负责什么** | 源文档明确把**冷启动弹性**从它手里拿走【S24】 |

**官方确实有 Ray Serve + SGLang 的集成**，通过 `LLMConfig` 的 `server_cls` 参数接入 SGLang，并支持 `tp_size` / `pp_size` / `mem_fraction_static` 等 engine 参数【Research-derived · R16】。

> **但官方给它加了一句警语**，源文档没提：**"Community SGLang support is in early development."**【R16】官方列出的缺口包括：同一 deployment 内多个 engine 副本、engine 遥测（KV Cache 利用率、请求队列深度）、独立的 prefill/decode worker 组、宽专家并行、弹性容错的专家并行【R16】。
>
> **也就是说**：源文档推荐的"Ray Serve 作为上层编排"，在 20 卡生产集群这个场景上，**站在官方标注为"早期开发"的软件上**。

**扩缩容与故障恢复的机制本身是成熟的**：`target_ongoing_requests` / `min_replicas` / `max_replicas` 控制扩缩容，Serve controller 定期健康检查并在失败时重启副本【Research-derived · R17】。

**冷启动方面**：Ray 官方 benchmarks 承认 "Replica startup times involving large models can be slow"，并给出分阶段拆解（节点供给 → 镜像下载 → Ray 初始化 → 模型加载 → Torch Compile → 显存剖析 → CUDA Graph 捕获 → 预热）与一批缓解手段（HF 快速下载、`runai_streamer` 直接流入显存、Torch compile 缓存等）【R18】。

> ⚠️ **这些缓解手段是围绕 vLLM 写的**；SGLang 路径官方标注为早期开发，**没有对应的 SGLang 专属启动优化文档**【R18】。另外——**没有任何 Ray 官方文档说"不要依赖我们自己的调度器做冷启动弹性"**【R18】，源文档那句是**作者的主观主张**。

<a id="524-kserve"></a>

### 5.2.4 KServe —— 编排层（被负面对比）

| 项 | 内容 |
|---|---|
| **源文档的批评** | "彻底告别'**KServe Scale-to-Zero那种分钟级冷启动**'的陷阱"【S22】 |
| **批评的对象** | **Scale-to-Zero 这条路径**，不是 KServe 整体 |
| **替代方案** | NVIDIA Snapshot【S22】 |

**外部核对的结论：批评的"方向"对，但"分钟级"这个数字不是 KServe 说的**【R21】【R28】【R29】。

**KServe 官方文档实际怎么说**：

| 官方说法 | 出处 |
|---|---|
| Scale-to-Zero：Standard Deployment **不支持** / Knative **原生支持** | 控制面文档的 Mode Comparison 表【R21】 |
| Cold Start：Standard **无冷启动** / Knative **有冷启动延迟** | 同上【R21】 |
| Knative 的代价清单里明确列了 "⚠️ **Cold Start Latency**: Initial requests may experience higher latency" | 同上【R21】 |
| 全站唯一的冷启动具体数字是 **~10 秒**，而且出自一个 **sklearn/iris 预测模型**的例子 | KPA autoscaler 文档【R28】 |
| LLM 路径（llmisvc）用 **WVA + HPA/KEDA**，`idleReplicaCount` 才能缩到 `minReplicas` 以下；并且需要 `initialCooldownPeriod` 来吸收模型加载时间 | llmisvc autoscaling 文档【R29】 |

> **怎么读这张表**：
> - **"分钟级"这个数字，KServe 官方没有发布过**【R28】【UQ5】。对 100B+ 模型在 20 卡上，分钟级冷启动是**合理推断**，但**不能写成"据 KServe 文档"**。
> - **KServe 自己承认缩容到零有冷启动代价**，并且它的 LLM 路径需要专门的 `initialCooldownPeriod` 来处理模型加载时间——**这恰恰是 KServe 知道这个问题、也给了应对手段的证据**【R29】。
> - **所以源文档这条批评是"方向正确、措辞过头"**：批评的是 **Scale-to-Zero 这条路径的冷启动速度**，不是 KServe 整体。KServe 在**编排、扩缩容策略、模型仓库、灰度发布**上的能力，与"冷启动快不快"是**正交**的问题。

---

## 5.3 源文档没有提到、但在同一层的工具

源文档是**一份部署方案，不是选型报告**——它假定引擎选型已完成。本节补上同层的其他选项，供你自己评估。**这些工具在源文档中完全未被提及**。

### 5.3.1 推理引擎层（第 ② 层）的其他选项

| 工具 | 它与 SGLang 的重叠面 | 差异面 |
|---|---|---|
| **vLLM** | 同样定位为高吞吐 LLM 推理引擎，同样提供 OpenAI 兼容 API，同样支持 TP/PP 与多 GPU 部署 | 两者的调度器与特性集不同；**本课程不对二者做性能优劣断言**——没有同硬件同负载的公开对比数据 |
| **TensorRT-LLM** | 同样面向生产推理，同样支持多 GPU 与量化 | 更贴近 NVIDIA 自家栈（与 TensorRT、TensorRT Model Optimizer 集成更紧） |

> **一条值得注意的事实**：TensorRT-LLM 的官方量化支持矩阵里，**sm120（RTX 5090）这一行是 `NVFP4 | MXFP4 | FP8(per-tensor) | FP8 KV Cache` 为支持，而 `FP8 block scaling`、`FP8 rowwise`、`NVFP4 KV Cache`、AWQ 与 GPTQ 全部为不支持**【Research-derived · R8】。这意味着**在 Blackwell 消费卡上，量化格式的选择空间比数据中心卡窄**——换引擎时这一层的可用性要重新核对。

> **本课程不提供"该换哪个引擎"的结论**，只给出**换的时候要重测什么**：
> 1. 你的 Blackwell 必配项是否被新引擎覆盖（量化格式、注意力后端、共享内存要求）；
> 2. 你的并行策略是否被支持（尤其 **PP** 的成熟度）；
> 3. 你的冷启动路径是否还有等价物（**R-Fork 是 SGLang 特有的**——换引擎意味着要重建第 ⑤ 层）；
> 4. 你的路由层是否还能对接（**`sgl-router` 是不是只认 SGLang 后端**，需要核对）。

### 5.3.2 量化与内核层（第 ① 层）

| 工具 | 作用 |
|---|---|
| **NVFP4 / FP8 量化检查点** | 直接决定模型能否单卡承载【S11】——这一层的选择**先于**引擎选择 |
| **FlashInfer** | 注意力后端，在 Blackwell 上影响长提示的 TTFT【S12】；**NVFP4 的 GEMM 路径必须装它**【R34】 |

> **这一层还有一个"元"问题**：**命令行取值不等于格式名**。SGLang 的 `--quantization` 合法取值里**没有 `nvfp4`**【R30】——真正的 NVFP4 检查点要用 `modelopt_fp4` / `nvfp4_online` / `petit_nvfp4` / `mxfp4` 这类取值。**换引擎时，"格式支持"和"参数名支持"是两件事**，都要核对。

> **一个反直觉的顺序**：在这一套硬件上，**量化格式的选择比引擎的选择更重要**。因为它决定了你**能不能用情况 A**（纯 DP）——如果精度选错导致模型必须跨卡，你就直接掉进了情况 B 的复杂度和延迟代价里。

---

## 5.4 重叠与差异对照

按层看，每个层内的工具才是**可比的**：

| 层 | 工具 | 解决的问题 | 与 SGLang 的关系 | 什么时候考虑换/加 |
|---|---|---|---|---|
| ① 量化与内核 | NVFP4 / FP8、FlashInfer | 权重精度、注意力实现 | **依赖**：SGLang 使用它们 | 显存不够、或长提示 TTFT 不达标时 |
| ② 推理引擎 | **SGLang**（本方案） | 把模型跑起来、暴露 API | **本方案选定** | 换引擎要重建第 ③/⑤ 层 |
| ② 推理引擎 | vLLM、TensorRT-LLM | 同上 | **可替代** | 生态、硬件绑定、既有代码资产 |
| ③ 路由 | **`sgl-router`**（源文档写作 "SGLang Router"） | 多实例分发 | **依赖**：服务于 SGLang 实例 | 副本数变多、需要缓存感知路由时 |
| ④ 编排 | **Ray Serve** | 起几个、放哪、故障恢复 | **可叠加**：把 SGLang 当部署单元 | 多节点、已有 Ray 栈时；注意 SGLang 集成仍是"早期开发"【R16】 |
| ④ 编排 | **KServe** | 同上 | **可叠加** | 已在 K8s 上、需要模型仓库与灰度时 |
| ⑤ 弹性 | **NVIDIA Snapshot** | 秒级恢复 | **可叠加**：为 SGLang 后端 | 缩容到零、滚动升级、故障恢复；**要求 K8s 且单节点**【R20】 |

> **这张表最重要的信息是"依赖"与"可叠加"的区别**：
> - **依赖**（①③）：换掉它，② 就得跟着换，或者方案就不成立；
> - **可叠加**（④⑤）：随时可以加进来或拿掉，不影响 ②③ 的选型。
>
> **这解释了为什么源文档在引擎层不做比较**——因为在 Blackwell + 20 卡这个具体场景下，**①③ 的约束比"哪个引擎更快"更能决定结果**。

---

## 5.5 选择规则（决策链）

遇到一个具体问题，按这条链往下走：

```
你的需求是什么？
│
├─ 要更高吞吐 / 更多并发
│   └─ 先问：模型能不能装进单卡？
│       ├─ 能 → 情况 A（20 副本 DP）—— 这条路上没有引擎之争
│       └─ 不能 → 情况 B（TP×PP）—— 此时才轮到引擎与并行策略的取舍
│
├─ 要缩短冷启动（扩容 / 唤醒 / 升级）
│   └─ 分清是"恢复"还是"扩容"？
│       ├─ 恢复 → 第 ⑤ 层：NVIDIA Snapshot
│       │         ⚠️ 但它要求 K8s + 单节点 + 一堆前置条件
│       │         若不满足，退回 R-Fork（只省权重加载段）
│       └─ 扩容（真正要拉起新副本）→ 没有快路径，只能优化常规启动
│
├─ 要跨节点部署
│   └─ 编排层选型：
│       ├─ 已有 Ray 栈 → Ray Serve（⚠️ SGLang 集成尚在早期开发）
│       ├─ 已有 K8s   → KServe（缩容到零需 Knative 或 KEDA + 冷却期调优）
│       └─ 都没有     → 手动脚本起步（源文档的路线）
│
└─ 要换推理引擎
    └─ 先确认 ① ③ ⑤ 三层是否还能复用——不能复用，换引擎的成本远高于引擎本身
```

**这套规则里最重要的一条**：**先分层，再比较**。在问"哪个引擎更好"之前，先问"这是哪一层的问题"。

---

## 5.6 三个常见误解

| 误解 | 为什么错 |
|---|---|
| **"Router 能替代 KServe"** | Router 在第 ③ 层（分发请求），KServe 在第 ④ 层（决定起几个实例）。**一个决定"请求给谁"，一个决定"实例在哪"。** 两者是**串联**关系，不是替代关系 |
| **"用了 Snapshot 就不需要编排层"** | Snapshot 解决**恢复**；编排层解决**扩容与放置**。源文档自己把这两件事分开处理【S22】【S24】 |
| **"KServe 的 Scale-to-Zero 很慢，所以 KServe 不适合"** | 源文档批评的是**冷启动速度**这一个维度【S22】，不是 KServe 的全部能力；且"分钟级"这个数字并非 KServe 官方发布【R28】。见 [5.2.4](#524-kserve) |

---

<a id="57-三条最实质的落差"></a>

## 5.7 三条最实质的落差

本课程把外部证据与源文档逐条对照后，**这三条是最影响可执行性的**：

| # | 落差 | 源文档的说法 | 外部证据 | 影响 |
|---|---|---|---|---|
| **1** | **Snapshot 的适用环境** | "生产级秒级弹性"，用于 20 卡集群【S21】【S22】 | **Kubernetes-only**、**多 GPU 只能单节点**、官方标注"暂不建议用于生产关键负载"【R20】 | **裸机多节点方案无法套用这一层**；要么整体改走 K8s，要么放弃 |
| **2** | **R-Fork 的 NCCL 示例不完整** | 给出了 `--remote-instance-weight-loader-backend nccl` 的完整命令【S19】 | `nccl` 后端**还需要** `--remote-instance-weight-loader-send-weights-group-ports`；且 **Seed 与 Client 并行策略必须一致**【R25】 | **照抄跑不通**；且多一个"并行策略必须对齐"的硬约束 |
| **3** | **路由层的名字与粒度** | "SGLang Router（现称 Model Gateway）"；架构图里"大模型路由到 PP 组"【S23】【S25】 | 名字改过两次，**当前是 `sgl-router`**【R11】；router 的工作单元是**完整实例**，不是 PP stage 组【R15】 | **命令与配置要按当前版本写**；PP 组的暴露方式要重新设计 |

其余较轻但仍需知悉的修正：GSM8K 区间的含义与归因（见 [03 · 3.3.3](03-core-functionality.md#model-choice)）、"TP 绝对不能跨节点"比官方指导更强（[03 · 3.2](03-core-functionality.md#step-1-topology)）、Ray Serve 的 SGLang 集成官方标注为早期开发（[5.2.3](#523-ray-serve)）。

---

## 本节小结

- **先分层**：量化/内核 → 推理引擎 → 路由 → 编排 → 弹性。**不在同一层的工具不可比**。
- **源文档用到的四个工具**：sgl-router（路由层）、Ray Serve（编排层）、NVIDIA Snapshot（弹性层）、KServe（编排层，被就冷启动速度负面对比）。
- **源文档没提到的同层工具**：vLLM、TensorRT-LLM（引擎层）；它们与 SGLang 可比，但**换引擎会连带影响路由层与弹性层**。
- **KServe 的批评只针对 Scale-to-Zero 的冷启动速度**，且"分钟级"并非其官方数字【R28】。
- **决策链的入口永远是"模型塞不塞得下单卡"**，不是"哪个引擎更快"。
- **三条最实质的落差**见 [5.7](#57-三条最实质的落差)：Snapshot 的环境要求、R-Fork 的缺失参数、路由层的名字与粒度。

**下一节**：[06 · 学习路径](06-learning-path.md) —— 把整条路线走一遍，每个阶段都有可观察的判据。
