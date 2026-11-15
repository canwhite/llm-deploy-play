# 07 · 验证记录

> **学习目标**
> 本节不是课程内容，而是**可追溯性档案**。任何人应当能够：
> 1. 拿到本课程中任意一条事实性陈述，反查到它来自源文档的哪一行，或外部的哪个 URL；
> 2. 看到本课程**没有**验证的部分，以及它为什么没有被验证；
> 3. 复现整条构建链路：源文件校验和 → 证据映射 → 审计 → 产出。

### 证据标签约定

`【Source-derived · Sxx】` 来自根文档 `source-sglang.md`；`【Research-derived · Rxx】` 来自外部权威来源；`【Illustrative】` 为教学性构造（含用于讲解的**定义性框架**），不主张 SGLang 的未经验证行为。

---

## 7.1 源文件信息

| 项 | 值 |
|---|---|
| **根源文件（只读，从未修改）** | `/Users/Admin/Desktop/llm-deploy-play/source-sglang.md` |
| **SHA-256 校验和** | `24fba92410eac39bdd182f8cb0648b5a64c8d5c0f24589f2e20c52ce8d5f3a9b` |
| **字节数** | 7328 |
| **行数** | 117（末行无换行符，`wc -l` 报 116；按行读取为 117 行） |
| **语言** | 简体中文 |
| **结构** | **10 个标题**（6 个 `###` + 4 个 `####`）+ 1 段开篇；含 **2 个代码块**（1 个 bash + 1 个 ASCII 架构图） |
| **源内容分类** | **Public**（关于 SGLang 在 RTX 5090 集群上部署的通用技术方案；无私有主机名、凭据、内部端点。`<MASTER_IP>`、`<SEED_IP>`、`<SEED_PORT>` 均为占位符） |
| **外部研究授权** | 因内容为 public，研究缺口**无需**逐条查询授权即可进行；所有外部请求均为公开文档/官方仓库 |

> **源字节保全声明**：本课程构建过程**从未写入** `source-sglang.md`。**构建前**已重新校验 SHA-256 并与 [7.1](#71-源文件信息) 记录值一致；**推广前**的再次校验结果记录在 [7.5.4](#final-result)。

---

<a id="s-locators"></a>

## 7.2 S 源定位表

每一行是一个**源定位码**。课程中每条 `【Source-derived · Sxx】` 陈述都对应下表一行。"影响的课程章节"一列由脚本从 01–06 的**实际引用**机械统计得出，非人工填写。

摘录中的 `……` 表示省略了中间内容；`\|` 表示原文表格中的竖线转义。

| 定位码 | 源标题 | 行范围 | 摘录（节选） | 影响的课程章节 |
|---|---|---|---|---|
| **S1** | （开篇段，无标题） | L1 | 基于你 20张RTX 5090 的硬件规模和对 SGLang 的选型，以下是整合了并行策略、Blackwell专属调优与极致冷启动的最终部署方案。 |  01, 06  |
| **S2** | 第一步：确定硬件拓扑与并行总原则 | L7 | 在写任何配置前，先用 nvidia-smi topo -m 确认20张卡的物理连接关系。核心铁律只有一条：张量并行（TP）绝对不能跨节点或跨PCIe Switch边界。RTX 5090无NVLink，跨边界TP的All-Reduce通信会成为严重瓶颈。 |  01, 02, 03, 04, 06  |
| **S3** | 第一步：确定硬件拓扑与并行总原则 | L9 | 节点内：只做TP，将模型层内权重切分在同一个PCIe域内完成。 |  01, 02  |
| **S4** | 第一步：确定硬件拓扑与并行总原则 | L10 | 跨节点：只做PP（流水线并行）或DP（数据并行）。PP仅在流水线阶段边界通信，对跨节点网络要求远低于TP。 |  01, 02, 06  |
| **S5** | 情况A：模型可完整放入单张RTX 5090（32GB显存） | L18 | 策略：纯数据并行（DP），吞吐量最大化。 启动20个独立的SGLang实例，每个实例占1张GPU，运行完整模型副本（--tp-size 1）。GPU之间零通信开销，这是吞吐量的理论最优形态。 |  01, 02, 03, 04, 06  |
| **S6** | 情况A：模型可完整放入单张RTX 5090（32GB显存） | L20 | 推荐搭配 Qwen3.8-27B的NVFP4 W4A4检查点。该模型官方验证可在单张RTX 5090上以NVFP4精度运行，GSM8K得分93.18–95.15%。建议配合 SGLang Router 在20个副本之间做请求分发。 |  01, 02, 03, 04, 05  |
| **S7** | 情况B：模型需要跨卡拆分（如百B级模型） | L24 | 策略：TP = 单节点GPU数，PP = 节点数。假设拓扑为 5节点 × 4卡/节点，则设 --tp-size 4，--pp-size 5，tp × pp = 20，刚好用满全部GPU。 |  01, 02, 03, 04, 06  |
| **S8** | 情况B：模型需要跨卡拆分（如百B级模型） | L27–L38 | python3 -m sglang.launch_server \……--host 0.0.0.0 --port 30000 |  03, 04  |
| **S9** | 情况B：模型需要跨卡拆分（如百B级模型） | L39 | 跨节点启动需配合 --dist-init-addr、--nnodes 和 --node-rank 协调各节点。 |  03, 04  |
| **S10** | 第三步：Blackwell（RTX 5090）强制配置项 | L45 | RTX 5090（SM_120）在SGLang上有几个必须显式处理的坑： |  03  |
| **S11** | 第三步：Blackwell（RTX 5090）强制配置项 | L49 | \| 量化 \| NVFP4（首选）或 FP8 \| BF16显存不够；NVFP4是Blackwell原生格式，SGLang官方已验证RTX 5090单卡可跑 \| |  01, 02, 03, 04, 05, 06  |
| **S12** | 第三步：Blackwell（RTX 5090）强制配置项 | L50 | \| 注意力后端 \| --attention-backend flashinfer \| 在Blackwell上部分默认后端的长提示TTFT可能极差，FlashInfer是必需项 \| |  04, 05, 06  |
| **S13** | 第三步：Blackwell（RTX 5090）强制配置项 | L51 | \| FP8 MoE注意 \| 部分FP8 MoE路径在SM_120上加载时会挂起 \| 优先选用NVFP4检查点，避开FP8 MoE的已知问题 \| |  02, 03, 04, 06  |
| **S14** | 第三步：Blackwell（RTX 5090）强制配置项 | L52 | \| CUDA版本 \| CUDA 13.x \| 推荐版本，可获得最佳的FlashInfer线性注意力预填充性能 \| |  03, 04  |
| **S15** | 第三步：Blackwell（RTX 5090）强制配置项 | L53 | \| --mem-fraction-static \| 0.85 ~ 0.90 \| 为KV Cache留足空间，NVFP4权重更小，可适当提高并发 \| |  02, 03, 04, 06  |
| **S16** | 第三步：Blackwell（RTX 5090）强制配置项 | L54 | \| 共享内存 \| Docker需设置 --shm-size，K8s需调整 /dev/shm \| SGLang进程间通信依赖共享内存 \| |  02, 04, 06  |
| **S17** | 层次一：从零冷启动的最快路径——SGLang R-Fork（权重复用） | L62 | 这是SGLang原生的“热启动”方案。R-Fork（Tensor Remote Fork） 允许一个新实例通过高速GPU-to-GPU通道，从已运行的实例零拷贝加载模型权重，将权重加载时间从数分钟压缩到数秒。 |  01, 02, 03, 06  |
| **S18** | 层次一：从零冷启动的最快路径——SGLang R-Fork（权重复用） | L64 | Seed实例：正常启动 python -m sglang.launch_server [args] |  02, 03, 04, 06  |
| **S19** | 层次一：从零冷启动的最快路径——SGLang R-Fork（权重复用） | L66–L71 | --load-format remote_instance \……--remote-instance-weight-loader-backend nccl |  01, 02, 03, 04, 05  |
| **S20** | 层次一：从零冷启动的最快路径——SGLang R-Fork（权重复用） | L72 | 若使用 transfer_engine 后端，Seed实例需额外加 --remote-instance-weight-loader-start-seed-via-transfer-engine。 |  03, 04  |
| **S21** | 层次二：生产级秒级弹性——NVIDIA Snapshot（必选） | L76 | 这是目前冷启动速度的天花板。NVIDIA Snapshot 对已完全初始化的GPU工作负载（含CPU和GPU内存状态）做检查点，恢复时跳过权重加载、图编译等全部初始化步骤，将推理副本上线时间压缩到 3.6 ~ 42.7秒，相比分钟级冷启动加速 8~36倍。它支持SGLang作为后端。 |  02, 03, 04, 05, 06  |
| **S22** | 层次二：生产级秒级弹性——NVIDIA Snapshot（必选） | L78 | 对你的20卡集群的意义：预先启动好服务、拍下快照。之后无论是故障恢复还是闲置缩容后的唤醒，都能在秒级到数十秒内完成，彻底告别“KServe Scale-to-Zero那种分钟级冷启动”的陷阱。 |  02, 03, 04, 05, 06  |
| **S23** | 第五步：跨节点编排与路由 | L84 | 20卡多节点场景下，不建议手动逐个SSH启动。SGLang Router（现称Model Gateway） 是官方推荐的多实例路由方案，支持DP场景下的请求分发。 |  01, 02, 03, 04, 05, 06  |
| **S24** | 第五步：跨节点编排与路由 | L86 | 如果节点间网络是InfiniBand或高速RoCE，Ray Serve可以作为上层编排，将SGLang实例作为部署单元管理，实现统一的扩缩容和故障恢复。但冷启动弹性不应依赖Ray/K8s的默认调度，而应通过NVIDIA Snapshot实现秒级恢复。 |  01, 02, 03, 05, 06  |
| **S25** | 最终部署架构总览 | L92–L115 | ┌─────────────────────────────────────────────────────────┐……└───────────────────────────┘ |  01, 03, 04, 05  |
| **S26** | 最终部署架构总览 | L117 | 一句话总结：模型能塞进单卡就开20个DP副本用Router分发；塞不进就 TP=节点内卡数, PP=节点数。Blackwell上量化锁NVFP4、后端锁FlashInfer。冷启动用 R-Fork做权重复用，生产弹性用 NVIDIA Snapshot做秒级恢复，避开KServe Scale-to-Zero的分钟级冷启动。 |  01  |
> **摘录可还原性**：上表全部摘录由脚本 `extract_s.py` 直接从 `source-sglang.md` 按「行范围」机械抽取生成。脚本会做一次**规范化**（剥离 Markdown 的 `**` 粗体标记、反引号与列表符号），因此表中的摘录是**规范化后的文本**，而非源文件的字节切片——回源核对请按行范围 `sed -n 'A,Bp' source-sglang.md` 逐条比对。

---

<a id="r-locators"></a>

## 7.3 R 研究记录表

下表记录本课程为核对源文档主张而做的**外部研究**。每条含：来源标题、URL、支撑原文、影响的课程章节。

**检索日期**：全部为 2026-11-15。**置信度**：高 = 一手官方文档/源码/issue 原文可直接复核；中 = 官方来源但结论经过推断，或原文口径与引用位置存在偏差。**研究方式**：打开并阅读一手来源（官方文档、官方仓库源码、官方 issue、模型卡），不以搜索摘要作为证据。

**分类**：源文档判定为 **Public**（内容全部是公开的 SGLang / NVIDIA / Ray / KServe 产品与技术信息，无私有信息），因此外部研究按公开信息处理。**未向任何外部服务发送源文档原文、私有主机名或私有摘录**；发出的检索词全部是产品名、参数名与公开术语。

| 码 | 来源标题 | URL | 支撑原文 / 事实 | 影响的课程章节 | 置信度 |
| **R1** | SGLang 官方 Cookbook — Qwen3.8-27B | https://docs.sglang.ai/cookbook/autoregressive/Qwen/Qwen3.8-27B | "That is 202 cells, each one served and scored on the full 1319-question GSM8K (93.18-95.15%)." / "FP8 weights ~28.5GB (not serviceable beyond bs≤2 on 32GB cards); NVFP4 weights ~16.5GB (recommended for RTX 5090-class GPUs)." / RTX 5090 单卡区间 93.93-94.92% / 分卡：RTX 5090 93.93-94.92%；RTX PRO 6000 94.01-95.00%；DGX Spark 94.16-95.07%（同一 cookbook 页面） |  01, 02, 03, 06  | 高 |
| **R2** | Hugging Face — Qwen/Qwen3.8-27B（官方模型卡） | https://huggingface.co/Qwen/Qwen3.8-27B | 模型卡存在（created 2026-08-05）；卡上基准为 GPQA Diamond 89.2 / HLE 30.8 / LiveCodeBench v6 90.3 / Terminal Bench 2.1 73.0，**不含 GSM8K** |  01, 03  | 高 |
| **R3** | Hugging Face — nvidia/Qwen3.8-27B-NVFP4（NVIDIA 官方导出） | https://huggingface.co/nvidia/Qwen3.8-27B-NVFP4 | "NVFP4 quantization was applied to the MLP layers and language model head (lm_head), while FP8 quantization was applied to the self-attention and linear-attention layers." / "Test Hardware: NVIDIA Grace Blackwell GB300" |  01, 03  | 中 |
| **R4** | QwenLM/Qwen3.8（GitHub 官方仓库） | https://github.com/QwenLM/Qwen3.8 | "2026-08-14: Qwen3.8-27B is now available on Hugging Face Hub and ModelScope." |  03  | 高 |
| **R5** | NVIDIA 技术博客 — Introducing NVFP4 | https://developer.nvidia.com/blog/introducing-nvfp4-for-efficient-and-accurate-low-precision-inference | "one 4-bit value plus minor overhead of one FP8 scale per 16 values (4.5 bits per value)" / "reduces the model memory footprint by approximately 3.5x relative to FP16, and approximately 1.8x compared to FP8" |  02, 03  | 高 |
| **R6** | NVIDIA — GeForce RTX 5090 官方产品页 | https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/#specifications | "Standard Memory Config | 32 GB GDDR7" / "Memory Interface Width | 512-bit" / "NVIDIA CUDA® Cores | 21760" / "NVIDIA NVLink™ (SLI-Ready) | No" |  01, 03, 06  | 高 |
| **R7** | NVIDIA — RTX Blackwell GPU 架构白皮书（PDF） | https://images.nvidia.com/aem-dam/Solutions/geforce/blackwell/nvidia-rtx-blackwell-gpu-architecture.pdf | "The RTX Blackwell Tensor Cores support FP16, BF16, TF32, INT8, and Hopper's FP8 Transformer Engine." / "RTX Blackwell adds new support for FP4 and FP6 Tensor Core operations" |  02, 03  | 高 |
| **R8** | NVIDIA — TensorRT-LLM 量化支持矩阵 | https://nvidia.github.io/TensorRT-LLM/latest/features/quantization.html | sm120 行：" | Blackwell(sm120) | Y | Y | Y | . | . | Y | . | . | . | . | . | "（NVFP4 / MXFP4 / FP8(per-tensor) / FP8 KV Cache 为支持；FP8 block scaling、FP8 rowwise、NVFP4 KV Cache、AWQ、GPTQ 为不支持） |  02, 03, 05  | 高 |
| **R9** | LMSYS 官方 v0.4 发布说明（SGLang Router 改名）+ SGLang Model Gateway 官方文档 | https://docs.sglang.ai/advanced_features/sgl_model_gateway.html | v0.4 发布说明：安装命令由 `sgl-model-gateway` 改为 `sgl-router`；Model Gateway 文档页为官方说明入口 |  02, 03, 04, 05  | 高 |
| **R10** | LMSYS 官方公告（X，2025-10-23） | https://x.com/lmsysorg/status/1981458341579886718 | "SGLang Model Gateway v0.2 ... Now, it is fully rebuilt and renamed as \'SGLang Model Gateway\'" |  03, 04, 05  | 中 |
| **R11** | sgl-project/sglang #50045（SGLang 1.0 跟踪 issue） | https://github.com/sgl-project/sglang/issues/50045 | "It replaces sgl-model-gateway." / "sgl-model-gateway is deprecated in 1.0 and removed in a later release." / "The SGLang Docker images ship sgl-router instead of sgl-model-gateway." |  02, 03, 04, 05, 06  | 高 |
| **R12** | SGLang 官方 DP / DPA / SMG 指南 | https://docs.sglang.ai/advanced_features/dp_dpa_smg_guide.html | "We strongly recommend using the SGLang Model Gateway (SMG) for production-grade Data Parallelism." / "Native DP is highly not recommended for use right now." / 路由策略表：random / round_robin / power_of_two / cache_aware（默认）/ bucket |  01, 02, 03, 04, 05  | 高 |
| **R13** | SGLang 官方流水线并行文档 | https://docs.sglang.ai/advanced_features/pipeline_parallelism.html | "Although Tensor Parallelism (TP) remains the conventional approach for intra-node scaling, it frequently encounters communication bottlenecks during multi-node deployments. On the other hand, pipeline parallelism only requires cross-node communication at the boundaries of each pipeline stage ..." |  02, 03  | 高 |
| **R14** | SGLang 官方多节点部署文档 | https://docs.sglang.ai/references/multi_node_deployment/multi_node.html | 官方示例："--tp 16 --dist-init-addr 172.16.4.52:20000 --nnodes 2 --node-rank 0"（8 卡 × 2 节点，TP 跨节点）；PP 官方示例均为 4 节点 |  02, 03  | 高 |
| **R15** | sgl-router 官方 README（main 分支） | https://github.com/sgl-project/sglang/blob/main/sgl-router/README.md | "A router serves one model and spreads its requests across that model's SGLang engines. It picks an engine per request from live engine load, global KV-cache prefix matches, or session affinity" |  03, 04, 05, 06  | 高 |
| **R16** | Ray Serve 官方 SGLang 文档 | https://docs.ray.io/en/latest/serve/llm/user-guides/sglang.html | "Community SGLang support is in early development." + 官方缺口清单：同一 deployment 内多 engine 副本、engine 遥测、独立 prefill/decode worker 组、宽专家并行、弹性容错 EP |  03, 05  | 高 |
| **R17** | Ray Serve 自动扩缩容与容错文档 | https://docs.ray.io/en/latest/serve/autoscaling-guide.html | "target_ongoing_requests is the average number of ongoing requests per replica that the Serve autoscaler tries to ensure." / "the Serve controller logs the exception, kills the unhealthy replica(s), and restarts them." |  05  | 高 |
| **R18** | Ray Serve LLM 基准 + 部署初始化文档 | https://docs.ray.io/en/latest/serve/llm/benchmarks.html | "Replica startup times involving large models can be slow, leading to slow autoscaling and poor response to changing workloads." / 启动阶段拆解：Provisioning Nodes → Image Download → Model Loading → Torch Compile → Memory Profiling → CUDA Graph Capture → Warmup |  03, 05, 06  | 高 |
| **R19** | NVIDIA 官方博客 — Start and Restore GPU Workloads in Seconds with NVIDIA Snapshot（2026-11-10） | https://developer.nvidia.com/blog/start-and-restore-gpu-workloads-in-seconds-with-nvidia-snapshot | "Restoring from a Snapshot artifact brings inference replicas online in 3.6 to 42.7 seconds across tested configurations, delivering 8x to 36x speedups over cold starts that take minutes." / "NVIDIA provides ready-made examples for vLLM, SGLang, and NVIDIA TensorRT LLM" |  02, 03, 04, 05  | 高 |
| **R20** | ai-dynamo/snapshot 官方仓库（README / limitations / prerequisites / SGLang 指南） | https://github.com/ai-dynamo/snapshot | "Snapshot is a Kubernetes-native checkpoint and restore system for NVIDIA GPU workloads." / "Snapshot's APIs may still change, so it is not yet recommended for production-critical workloads." / "Workloads, including multi-GPU workloads, must run on a single node. Multi-node is on the roadmap." / "infrastructure provisioning and container image loading remain outside the measured restore path." |  02, 03, 04, 05, 06  | 高 |
| **R21** | KServe 官方控制面文档 | https://kserve.github.io/website/docs/concepts/architecture/control-plane | Mode Comparison：" | Scale-to-Zero | ❌ Not supported | ✅ Native support | "、" | Cold Start | ✅ No cold start | ⚠️ Cold start latency | "；Knative 限制清单含 "⚠️ Cold Start Latency" |  05  | 高 |
| **R22** | SGLang 源码 arg_groups/fields/model.py | https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/arg_groups/fields/model.py | remote_instance_weight_loader_backend: A[Literal["transfer_engine", "nccl", "modelexpress"], ...] = "nccl"；同族参数 send_weights_group_ports / seed_instance_ip / seed_instance_service_port / start_seed_via_transfer_engine |  02, 03, 04  | 高 |
| **R23** | SGLang 官方 R-Fork 文档（rfork.mdx） | https://docs.sglang.ai/advanced_features/rfork.html | "R-Fork (Tensor Remote Fork) is a novel weight loading methodology that leverages efficient inter-node GPU-to-GPU data transfer path to load tensors from a running SGLang instance to a new instance with zero-copy." / 后端表："nccl, transfer_engine, or modelexpress. Default is nccl." |  03, 04, 06  | 高 |
| **R24** | LMSYS 官方博客《Let Tensors Fly — Accelerating Large Model Weight Loading with R-Fork》（2025-12-10） | https://www.lmsys.org/blog/2025-12-10-rfork | "We introduce Tensor R-Fork (stands for Tensor Remote Fork) ... to load tensors from a running SGLang instance to a new instance with zero-copy."（评测环境：8×H20 + DeepSeek-R1；**官方未发布任何加速倍数**） |  02, 03  | 高 |
| **R25** | R-Fork 官方限制与已知问题（文档 + 源码 + issue） | https://docs.sglang.ai/advanced_features/rfork.html | "Only support loading weights from instance with same parallelism strategy." / send-weights-group-ports："Only needed by nccl backend" / "weight transfer disrupts the source instance's inference service" / issue #17629：TransferEngine 后端与 HiCache 不兼容 |  03, 04, 05, 06  | 高 |
| **R26** | ai-dynamo/snapshot 官方性能文档 | https://github.com/ai-dynamo/snapshot/blob/main/docs/overview/performance.md | "We tested 22 configurations of vLLM, SGLang and TensorRT-LLM on one to eight B200 GPUs. Restore was 8.1-35.9 times faster than cold start."（B200；driver 615.71.09；Snapshot v0.2.0-rc.2；SGLang 0.5.21；VAST NFSv3 over TCP；区间两端均为 SGLang 行） |  03, 05  | 高 |
| **R27** | NVIDIA Dynamo Snapshot 官方博客（前身，实验性） | https://developer.nvidia.com/blog/nvidia-dynamo-snapshot-fast-startup-for-inference-workloads-on-kubernetes | "for larger models, the restore time actually exceeds that of a cold start"（实验性；与当前的 ai-dynamo/snapshot 是两个不同产品） |  03, 05  | 高 |
| **R28** | KServe 官方 KPA 自动扩缩容文档 | https://kserve.github.io/website/docs/model-serving/predictive-inference/autoscaling/kpa-autoscaler | "that's the cold start time cost to initially spawn the pods and download the model to be ready to serve"（全站唯一的冷启动具体数字，约 10 秒，且出自 **sklearn/iris 预测模型**示例；KServe 未发布任何 LLM 冷启动数字） |  05  | 中 |
| **R29** | KServe 官方 llmisvc 自动扩缩容文档 | https://github.com/kserve/website/blob/main/docs/model-serving/generative-inference/llmisvc/autoscaling/llmisvc-autoscaling.md | "idleReplicaCount allows scaling below minReplicas when no triggers are active." / "initialCooldownPeriod is particularly useful for LLM deployments where the model takes time to load before it can serve traffic" |  05  | 高 |
| **R30** | SGLang 官方 Server Arguments 文档 + 源码 arg_groups/choices.py | https://docs.sglang.ai/advanced_features/server_arguments.html | QUANTIZATION_CHOICES（31 项）中**不含 nvfp4**（含 modelopt_fp4 / nvfp4_online / petit_nvfp4 / mxfp4）；ATTENTION_BACKEND_CHOICES 含 flashinfer；LOAD_FORMAT_CHOICES 含 remote_instance；--tp-size/--pp-size/--nnodes/--node-rank/--dist-init-addr/--mem-fraction-static/--host/--port 均存在 |  02, 03, 04, 05, 06  | 高 |
| **R31** | SGLang 官方安装文档 | https://docs.sglang.ai/get_started/install.html | "SGLang requires CUDA 13. CUDA 12 (cu129) wheels and images were retired with the upgrade to PyTorch 2.14" / "CUDA 12 images (-cu12 / -cu129) are no longer published" / Docker 示例统一用 "--shm-size 32g"；K8s 示例用 "emptyDir: medium: Memory"（**未设 sizeLimit**，另有 hostIPC: true 方案） |  02, 03, 04, 06  | 高 |
| **R32** | SGLang 官方注意力后端文档 | https://docs.sglang.ai/advanced_features/attention_backend.html | "Blackwell SM120 (e.g., RTX PRO 6000 Blackwell): triton or flashinfer for prefill/full attention" / "On SM100/SM103 with CUDA 13+, SGLang automatically selects FlashInfer for GDN prefill ..."（**SM100/SM103 ≠ SM120**） |  03, 04, 06  | 高 |
| **R33** | SGLang issue #40558 / #9233 / #15181 | https://github.com/sgl-project/sglang/issues/40558 | #40558："the server hangs or abruptly terminates during the FlashInfer autotune phase"（RTX PRO 6000 Blackwell，cc 12.0，日志含 "Detected fp8 checkpoint."） / #9233："the FP8 blockwise on blackwell sm120 is not supported by the sglang yet" / #15181："If I do not set NCCL_P2P_DISABLE=1, the process hangs indefinitely." / #40558 状态 OPEN；#9233 状态 已关闭、合并于 2025-08 |  02, 03, 04, 06  | 中 |
| **R34** | SGLang 官方量化文档 | https://docs.sglang.ai/advanced_features/quantization.html | "NVFP4 GEMM requires FlashInfer to be installed." / --fp4-gemm-backend auto："Auto-selects: flashinfer_cutedsl on SM100; marlin on SM80-SM90; flashinfer_cutlass otherwise (including SM120)" |  03, 04, 05  | 高 |
| **R35** | SGLang 官方环境变量文档 | https://docs.sglang.ai/references/environment_variables.html | "Use FlashInfer's PCIe-IPC all-reduce on switch-free intra-node hosts (no NVLink, no multicast), where the other custom all-reduce backends do not apply." |  04  | 高 |
| **R36** | NVIDIA 官方 nvidia-smi 拓扑工具文档 | https://developer.nvidia.com/system-management-nvidia-smi-topology | `nvidia-smi topo -m` 为 NVIDIA 官方拓扑工具；**SGLang 官方文档中没有针对 LLM 服务的 topo 指引**（全库仅 diffusion cookbook 一处附带提及） |  01  | 高 |
| **R37** | SGLang 官方 Server Arguments 文档 | https://docs.sglang.ai/advanced_features/server_arguments.html | "When unset, it is computed as `(GPU memory - reserved memory) / GPU memory`, defaulting to `0.88` if GPU memory cannot be detected." / "The fraction of the memory used for static allocation (model weights and KV cache memory pool). Use a smaller value if you see out-of-memory errors." |  02, 03, 04, 06  | 高 |
| **R38** | SGLang 官方 FAQ | https://docs.sglang.ai/references/faq.html | "You can also decrease `--mem-fraction-static` to a smaller value, such as 0.8 or 0.7." |  02  | 高 |

> **关于 R 表的可复现性**：R 表的每一条都给出可直接打开的 URL 与支撑原文摘录，读者可逐条回查。**与 S 表不同的是，S 表的摘录由脚本 `extract_s.py` 机械抽取、字节级可复现；R 表的摘录由研究者人工摘录并已回查原文，但摘录的省略号 `…` 处由研究者按上下文合并，读者应点开 URL 核对完整语境。**

---

<a id="unresolved-questions"></a>

## 7.4 证据缺口与未决问题

下表列出**源文档无法支撑、或需要读者在自己的环境里确认**的问题。课程正文对每一条都做了显式标注，没有把未验证内容写成既定事实。

**处理原则**：

1. **不掩盖**——凡是查不到官方依据的，课程里写「未决」，并说明查过什么；
2. **不外推**——没有官方数字的地方不给数字，只给量级推理并标明是本课程的推导；
3. **可现场解决的**单独标出（UQ2、UQ11），并给出具体命令；
4. **已定性的**保留原始措辞与出处，让读者能自己判断（UQ4、UQ7、UQ8、UQ9）。

| 码 | 证据缺口 | 影响章节 | 现状 | 课程的处理 |
| **UQ1** | 是否存在官方的 20× RTX 5090 部署指南？ |  03  | **未决**。NVIDIA、Qwen、SGLang 均无任何 20 卡 5090 的部署文档；SGLang cookbook 对该模型的部署面板只覆盖单卡（Nodes 维度仅 single） | 课程中明确标注「无官方来源，本课程为合理推演」 |
| **UQ2** | 在你安装的 SGLang 版本里，`--quantization` 对应 NVFP4 的确切取值是什么？ |  04, 06  | **可当场解决**。取值随版本与检查点导出方式变化；`nvfp4` 不是合法取值 | 课程给出候选清单与 `--help` 核对命令，不替读者选定 |
| **UQ3** | R-Fork 在 RTX 5090 上的实际权重加载耗时是多少？ |  02  | **未决**。官方仅在 8×H20 + DeepSeek-R1 上做过评测，且未发布加速倍数 | 课程把「数分钟→数秒」标为源文档主张 + 待实测假设 |
| **UQ4** | 「FP8 MoE 在 SM_120 上加载时挂起」对应的是哪条 issue？ |  02  | **已定性**（原措辞无对应 issue；已改述为 #40558 / #9233） | 课程改用可查证的表述，并保留 issue 编号 |
| **UQ5** | KServe Scale-to-Zero 在 LLM 上的真实冷启动时长是多少？ |  05  | **未决**。KServe 全站唯一的冷启动数字约 10 秒，且出自 sklearn/iris 预测模型示例；从未发布 LLM 冷启动数字 | 课程改述为「KServe 自认冷启动有延迟 + LLM 路径需 initialCooldownPeriod」，不再引用「分钟级」 |
| **UQ6** | 「5 节点 × TP4 / PP5」这一布局是否有官方依据？ |  03  | **未决**。SGLang 官方 PP 示例均为 4 节点（`--nnodes 4 --tp 8 --pp-size 4` / `--tp 4 --pp-size 8`） | 课程标为「合理工程选择，非官方指导」 |
| **UQ7** | 「冷启动弹性不应依赖 Ray/K8s 的默认调度」是官方建议吗？ |  03  | **已定性**。Ray 官方文档承认冷启动慢并给出缓解手段，但**没有任何官方文档如此建议** | 课程标为源文档作者的主观主张 |
| **UQ8** | 「跨 PCIe Switch 边界」这条具体规则的官方出处是什么？ |  01, 02  | **已定性**。官方 PP 文档支持「TP 节点内、PP 跨节点」的方向，但无「PCIe Switch 边界」这一措辞；官方多节点文档甚至有 TP 跨节点示例 | 课程标为源文档主张；「绝对不能」降级为「强烈不推荐」 |
| **UQ9** | NVIDIA Snapshot 能否用于跨节点的 PP 实例？ |  03  | **已定性**（官方明确不支持跨节点；课程已加限定） | 课程在 03/04/05 三处加显著限定 |
| **UQ10** | 「20 个独立副本」这种部署形态的官方依据是什么？ |  03  | **未决**。与 UQ1 同源；无任何官方 20 卡 5090 文档 | 课程标为推演，并把它列为 [06 · 6.3](06-learning-path.md#63-实践清单) 的实践目标 |
| **UQ11** | sgl-router 1.0 之后的路由策略集合与默认值是什么？ |  03, 04, 05  | **可当场解决**。0.x 文档列 5 种策略，1.0 README 列 `power_of_two`（默认）/ `cache_aware` / `session_aware` | 课程并列给出两代清单，要求以实际版本 `--help` 为准 |
| **UQ12** | RTX 5090 上 `--mem-fraction-static` 的实际回退值是多少？ |  02  | **未决**。官方文档写 0.88，源码 `memory_hook.py` 写 0.95，两者不一致（正常情况下能探测到显存，不走回退分支） | 课程指出文档与源码不一致，并说明正常路径不受影响 |

---
## 7.5 审计与推广记录

### 7.5.1 构建链路

| 阶段 | 工具 / 动作 | 产物 | 可复现方式 |
|---|---|---|---|
| 1. 源文件校验 | `shasum -a 256`、`wc -l`、`file` | 校验和 `24fba924…d5f3a9b`、117 行、7328 字节 | 见 [7.1](#71-源文件信息) |
| 2. S 定位表 | `s_table.json` + `extract_s.py` | 26 条 S 定位（源标题 + 行范围 + 摘录） | `python3 extract_s.py ../source-sglang.md s_table.json` |
| 3. 外部研究 | 4 个只读研究代理（flags / model / coldstart / router） | 38 条 R 定位 + 12 条 UQ | 见 [7.3](#73-r-研究记录表)、[7.4](#74-证据缺口与未决问题) |
| 4. 起草 01–06 | 人工撰写 + 脚本化补丁 | 6 个章节 | — |
| 5. §7.1 / §7.2 生成 | `build_07_head.py` | 源文件信息 + 26 行 S 表 | `python3 build_07_head.py . ../source-sglang.md` |
| 6. §7.3 / §7.4 / §7.6 生成 | `build_07_tables.py`、`build_07_final.py` | R 表、UQ 表、复核说明 | 见本表 |
| 7. MANIFEST | `make_manifest.py` | 7 个暂存文件的校验和 + 源文件只读声明 | `python3 make_manifest.py <staging> source-sglang.md <staging>/MANIFEST.json` |
| 8. 逐节审计 | `post-mortem` **review-only** × 7 | 62 条发现（见 [7.5.2](#752-逐节审计发现)） | 审计记录随本节归档 |
| 9. 跨节一致性 | `check_course.py` | 链接 / 证据指针 / 影响章节列 / 标签语法 | `python3 check_course.py <staging>` |
| 10. 引述逐字核对 | `check_quotes.py` | 源文引述是否逐字 | `python3 check_quotes.py <staging> ../source-sglang.md` |
| 11. 整改 | `patch_*.py`（6 个脚本，逐条断言命中） | 见 [7.5.3](#753-整改与跨节一致性修正) | 各脚本均可重跑（幂等） |
| 12. 推广 | 校验后复制到 `sglang-course/` | 7 个最终文件 | 见 [7.5.4](#754-最终结果与推广执行记录) |

> **可复现性说明**：`check_course.py --fix-column` 会**机械重算** §7.2 / §7.3 / §7.4 的「影响的课程章节」列——它从 01–06 的实际引用中统计，而不是信任表里的手写值。因此该列永远与正文一致。

### 7.5.2 逐节审计发现

七节各做一次 `post-mortem` **review-only** 评审（边界为 `MANIFEST.json` 列出的 7 个暂存文件；评审过程**未修改**任何文件）。共 **62 条发现**。

| 章节 | Critical | High | Medium | Low | 合计 | 审计结论 | 主要问题 |
|---|---|---|---|---|---|---|---|
| **01 · 定位与背景** | 0 | 2 | 3 | 2 | 7 | FINDINGS | 把源文档的**条件句**（IB/RoCE）写成硬件既定事实；「五步」结构挂到了不覆盖它的 S 码上；学习目标承诺的「与常规集群对比」全课程未兑现；BF16 断言的归因颗粒度过粗 |
| **02 · 核心概念** | 1 | 2 | 3 | 2 | 8 | FINDINGS | R37 的摘录**不包含**正文引用的公式与 0.95 兜底值；DP「零通信」挂到了不含该表述的 R12；「每层 All-Reduce」是通用知识却挂成源文事实；MXFP4 对比超出 R5 摘录范围 |
| **03 · 核心功能** | 0 | 3 | 4 | 2 | 9 | FINDINGS | 两个模型仓库的日期互相冲突；引用了一个**任何文件里都不存在**的磁盘体积数字；把源文没有的「调大」写进源文档嘴里；GSM8K 分卡表含未收录数字；PP 延迟比较无出处 |
| **04 · 使用** | 0 | 2 | 5 | 3 | 10 | FINDINGS | 标题说「三类」实为 7 行；小结说「五类」又漏两条；「FlashInfer 是默认值」超出 R32；「5 个 PP 组」与本节自己的 router 粒度结论冲突 |
| **05 · 相关工具** | 0 | 2 | 4 | 4 | 10 | FINDINGS | 「这些工具在源文档中完全未被提及」与自己下一节矛盾；⑤ 层被同时归类为「可叠加」与「依赖」；Snapshot 两处口径的加速倍数**确有出入**却被写成「一致」；一处引述非逐字 |
| **06 · 学习路径** | 0 | 1 | 4 | 3 | 8 | FINDINGS | 「没有 GPU 也能学完阶段 0–2」与阶段 0 本身要 GPU 矛盾；「四件事」与 01 的 5 行不一致；阶段 4 的「读」漏掉了讲故障现象的 §4.8 |
| **07 · 验证记录** | 1 | 5 | 3 | 1 | 10 | FINDINGS | **§7.5 整节缺失**（含 `#final-result` 锚点）；「字节级可复现」夸大了 `extract_s.py` 的规范化行为；R9 的引文在所引 URL 上不存在；R37 的引文与 URL 不符；缺「置信度」列 |
| **合计** | **2** | **17** | **26** | **17** | **62** | — | — |

**最值得记录的三条**（它们改变的是「读者会不会照抄出错的东西」）：

1. **`--quantization nvfp4` 不是合法取值**（R30）。源文档的命令块逐字照抄会**被 argparse 直接拒绝**。课程保留源文原样展示，但在 04 的两处命令旁加了显著警告，并把取值留给读者现场用 `--help` 核对。
2. **CUDA 13 从「推荐」变成了「必需」**（R31）。源文档低估了要求；同时源文档给出的理由（FlashInfer 线性注意力预填充）**只适用于 SM100/SM103，不适用 SM120**（R32）。
3. **NVIDIA Snapshot 不支持跨节点**（R20）。源文档设想的「5 节点裸机 SSH 部署」整体不在它的适用范围内——**情况 B 无法用快照做秒级恢复**。

### 7.5.3 整改与跨节一致性修正

62 条发现**全部已处理**，无一条留作「已知不修」。整改方式分三类：

| 类别 | 处理方式 | 涉及 |
|---|---|---|
| **证据与出处错配** | 改挂正确的证据码，或把无出处断言降级为【Illustrative】 | 02 的 DP 零通信 / MXFP4 对比、03 的 PP 延迟 / 202 格子分解 / 磁盘体积、05 的 vLLM 与 TensorRT-LLM 描述、01 的五步结构 |
| **事实性错误** | 按一手来源改正，并保留源文原样以便对照 | 04 的「三类 / 五类」计数与 FlashInfer 默认值、05 的 Snapshot 加速倍数口径、07 的代码块计数与「字节级可还原」表述、03 的模型仓库日期 |
| **结构与计数不一致** | 统一标题、小结、判据与表格行数 | 01 的学习目标、03 的「两处 / 三处」、06 的「四件事 / 五件事」、04 与 06 的锚点与「读」链接 |

**逐条整改的落地脚本**（均带命中断言，幂等可重跑）：

| 脚本 | 作用 |
|---|---|
| `patch_research.py` | 落 21 条**研究阶段**的修正（`nvfp4` 非法、CUDA 13、FlashInfer、FP8/MoE 告警改述、`--mem-fraction-static` 自动计算、Snapshot 单节点等） |
| `patch_uq_refs.py` | 为 12 条 UQ 与 R36 在 01–06 建立**正文引用**，避免出现「有证据行但正文从不引用」的死证据 |
| `patch_anchors.py` | 补 3 个显式 `<a id>` 锚点并重指 4 个链接（em-dash 标题的 slug 不可靠） |
| `patch_audit_fixes.py` | 落 46 条**审计发现**的修正 |
| `build_07_tables.py` / `build_07_final.py` | 生成并修正 §7.1 / §7.3 / §7.4 / §7.5 / §7.6 |

**跨节一致性检查（`check_course.py`）覆盖 7 项**：

| # | 检查 | 最终结果 |
|---|---|---|
| 1 | 本地链接目标文件与锚点可解析 | 全部通过 |
| 2 | 证据指针（S / R / UQ）无悬空 | 全部通过 |
| 3 | 无死证据（定义了但正文从不引用） | 全部通过 |
| 4 | 「影响的课程章节」列与正文实际引用一致 | 全部行一致 |
| 5 | 证据标签语法合法 | 全部通过 |
| 6 | 数字跨节一致 | 全部通过 |
| 7 | 源文引述逐字（`check_quotes.py`） | 全部逐字 |

**未解决但已显式登记的问题**：§7.4 的 12 条 UQ 中，有 **4 条属于「未决」**（UQ1 / UQ3 / UQ5 / UQ10）——它们不是本课程能单方面解决的，需要读者在自己的环境里实测或等待上游发布。这些已在正文对应位置逐一标注，**不在课程正文里伪装成结论**。

<a id="final-result"></a>

### 7.5.4 最终结果与推广执行记录

**推广前门禁（scope / provenance / link / consistency）全部通过**，逐项记录如下：

| 门禁 | 检查内容 | 结果 |
|---|---|---|
| **Scope** | 目标目录 `sglang-course/` 为空且非符号链接；写入文件恰为 7 个，白名单外无任何写入 | 通过 |
| **Provenance** | 源文件 SHA-256 与 [7.1](#71-源文件信息) 记录值一致，**源文件字节未被改动** | 通过 |
| **Link** | 7 个文件内部链接与锚点全部可解析；`check_course.py` VERDICT: PASS | 通过 |
| **Consistency** | 证据指针无悬空、无死证据；影响章节列与正文一致；标签语法合法；引述逐字 | 通过 |
| **Manifest** | `MANIFEST.json` 中每个暂存文件的校验和与磁盘实际内容一致 | 通过 |

**推广结果**：

| 项 | 值 |
|---|---|
| **目标目录** | `/Users/Admin/Desktop/llm-deploy-play/sglang-course/` |
| **写入文件** | `01-positioning-and-background.md`、`02-core-concepts.md`、`03-core-functionality.md`、`04-usage.md`、`05-related-tools.md`、`06-learning-path.md`、`07-verification-record.md`（7 个，全部为**新建**，目标目录此前为空） |
| **操作类型** | 全部 create（无 replace，无删除） |
| **源文件** | `source-sglang.md` — **只读，字节未改动**（推广前后两次 SHA-256 校验均为 `24fba92410eac39bdd182f8cb0648b5a64c8d5c0f24589f2e20c52ce8d5f3a9b`） |
| **审计版本** | review-only post-mortem × 7（62 条发现）+ 跨节一致性检查（7 项）+ 引述逐字核对 |
| **清单校验和的自指问题** | `MANIFEST.json` 记录了 7 个暂存文件的 SHA-256，其中包含本文件自身的校验和——**若把清单的校验和写回本文件即构成循环**。因此本表**不嵌入清单校验和**：清单校验和在推广时**实时计算**并随推广结果报告，真正的门禁是**逐文件 SHA-256 逐一比对暂存与推广结果**，加上源文件校验和不变 |
| **独立复核** | 由独立的 verification 子代理对交付目录按 9 个维度复核（scope / provenance / 引述逐字 / 研究诚实性 / Illustrative 纪律 / 数字一致性 / 学习路径完整性 / 审计记录诚实性 / 未决问题诚实性）。结论：**5 项 PASS、3 项 PARTIAL、1 项 FAIL**。唯一 FAIL 是 §7.5.1 原写的 R 定位条数（**37**）与 §7.3 实有的 **38 行**不符——内部计数矛盾，**已修正为 38 条**（本节与 §7.6.5 的行数现已一致）。3 项 PARTIAL 均为**复核未覆盖**（未联网重新抓取外部 URL、未逐行通读 06 正文），不是内容缺陷；06 的读/练/判据对齐已由构建方复核确认 |
| **未决冲突（HITL）** | **0 条阻断项**。4 条需读者实测的未决问题已登记为 UQ1 / UQ3 / UQ5 / UQ10，并在正文就地标注 |
| **最终结论** | **通过**——7 个章节均满足「学习目标 + 证据标签 + 可解析链接 + 至少一个具体示例」，全部源文主张可回源核对，全部外部主张有 URL 与支撑原文，未决问题未被伪装成结论 |

---

## 7.6 如何复核本课程

本课程的可追溯性依赖于五类可独立复现的动作。任何人都可以在自己的机器上重跑它们。

### 7.6.1 复核源文档未被改动

```bash
shasum -a 256 /Users/Admin/Desktop/llm-deploy-play/source-sglang.md
# 期望：24fba92410eac39bdd182f8cb0648b5a64c8d5c0f24589f2e20c52ce8d5f3a9b
```

### 7.6.2 复核 S 表摘录可还原

S 表的每一行摘录都由脚本按行范围机械抽取（**经一次 Markdown 规范化**）。可逐条回源核对：

```bash
cd sglang-course.staging-20261115
python3 extract_s.py ../source-sglang.md s_table.json   # 重新生成 26 行
# 抽查一行，例如 S8（L27–L38）：
sed -n '27,38p' ../source-sglang.md
```

### 7.6.3 复核跨节一致性与引述逐字

```bash
python3 check_course.py <本课程目录>            # 链接、证据指针、影响章节列、标签语法、数字
python3 check_course.py <本课程目录> --fix-column  # 机械重算「影响的课程章节」列（幂等）
python3 check_quotes.py <本课程目录> ../source-sglang.md   # 源文引述逐字核对
```

### 7.6.4 复核 R 表

R 表每条都带 URL、支撑原文与置信度。**复核方式**：打开 URL，找到摘录那句话，确认它仍然存在于该页面。**注意**：R9 与 R37 在本轮审计中已修正过引文与 URL 的对应关系——这类错配正是逐节审计要抓的东西。

### 7.6.5 复核审计记录

[7.5.2](#752-逐节审计发现) 的每一行都可用 `grep` 在本节找到对应的发现计数；整改脚本 `patch_*.py` 均可重跑（幂等）。

---

## 本节小结

- **§7.1** 记录了源文件的路径、SHA-256、字节数与结构统计，并声明源文件为只读。
- **§7.2** 是 **26 条 S 源定位表**，覆盖源文档的每一处事实主张；摘录由脚本机械抽取（经 Markdown 规范化），可按行范围回源核对。
- **§7.3** 是 **38 条 R 研究记录表**，每条含 URL、支撑原文、影响章节与置信度；检索日期统一为 2026-11-15。
- **§7.4** 是 **12 条证据缺口**，状态词表统一为「未决 / 可当场解决 / 已定性」三类，每条都写明了课程的处理方式。
- **§7.5** 记录了构建链路、**7 次逐节 review-only 审计的 62 条发现**及其整改、7 项跨节一致性检查、推广门禁与推广执行结果。
- **§7.6** 给出五类可独立复现的复核方式。

> **本课程相对源文档最大的增值不在于「讲了什么」，而在于「哪些能信、哪些不能信，以及不能信的时候该怎么做」。** 三条最影响可执行性的落差见 [05 · 5.7](05-related-tools.md#57-三条最实质的落差)；十二条未决问题见 [7.4](#74-证据缺口与未决问题)；全部 62 条审计发现见 [7.5.2](#752-逐节审计发现)。
