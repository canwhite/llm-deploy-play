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
| **结构** | **10 个标题**（6 个 `###` + 4 个 `####`）+ 1 段开篇；含 **3 个代码块**（2 个 bash + 1 个 ASCII 架构图） |
| **源内容分类** | **Public**（关于 SGLang 在 RTX 5090 集群上部署的通用技术方案；无私有主机名、凭据、内部端点。`<MASTER_IP>`、`<SEED_IP>`、`<SEED_PORT>` 均为占位符） |
| **外部研究授权** | 因内容为 public，研究缺口**无需**逐条查询授权即可进行；所有外部请求均为公开文档/官方仓库 |

> **源字节保全声明**：本课程构建过程**从未写入** `source-sglang.md`。构建前与推广前均重新校验 SHA-256，两次一致（见 [7.5.4](#final-result)）。

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
> **摘录可还原性**：上表全部摘录由脚本 `extract_s.py` 直接从 `source-sglang.md` 按「行范围」机械抽取生成，未经人工改写，因此可以逐条回源核对。

---

<a id="r-locators"></a>

## 7.3 R 研究记录表

下表记录本课程为核对源文档主张而做的**外部研究**。每条含：来源标题、URL、支撑原文、影响的课程章节。

**检索日期**：全部为 2026-11-15。**研究方式**：打开并阅读一手来源（官方文档、官方仓库源码、官方 issue、模型卡），不以搜索摘要作为证据。

**分类**：源文档判定为 **Public**（内容全部是公开的 SGLang / NVIDIA / Ray / KServe 产品与技术信息，无私有信息），因此外部研究按公开信息处理。**未向任何外部服务发送源文档原文、私有主机名或私有摘录**；发出的检索词全部是产品名、参数名与公开术语。

| 码 | 来源标题 | URL | 支撑原文 / 事实 | 影响的课程章节 |
|---|---|---|---|---|
| **R1** | SGLang 官方 Cookbook — Qwen3.8-27B | https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B | "That is 202 cells, each one served and scored on the full 1319-question GSM8K (93.18-95.15%)." / "FP8 weights ~28.5GB (not serviceable beyond bs≤2 on 32GB cards); NVFP4 weights ~16.5GB (recommended for RTX 5090-class GPUs)." / RTX 5090 单卡区间 93.93-94.92% |  01, 02, 03, 06  |
| **R2** | Hugging Face — Qwen/Qwen3.8-27B（官方模型卡） | https://huggingface.co/Qwen/Qwen3.8-27B | 模型卡存在（created 2026-08-05）；卡上基准为 GPQA Diamond 89.2 / HLE 30.8 / LiveCodeBench v6 90.3 / Terminal Bench 2.1 73.0，**不含 GSM8K** |  01, 03  |
| **R3** | Hugging Face — nvidia/Qwen3.8-27B-NVFP4（NVIDIA 官方导出） | https://huggingface.co/nvidia/Qwen3.8-27B-NVFP4 | "NVFP4 quantization was applied to the MLP layers and language model head (lm_head), while FP8 quantization was applied to the self-attention and linear-attention layers." / "Test Hardware: NVIDIA Grace Blackwell GB300" |  01, 03  |
| **R4** | QwenLM/Qwen3.8（GitHub 官方仓库） | https://github.com/QwenLM/Qwen3.8 | "2026-08-14: Qwen3.8-27B is now available on Hugging Face Hub and ModelScope." |  03  |
| **R5** | NVIDIA 技术博客 — Introducing NVFP4 | https://developer.nvidia.com/blog/introducing-nvfp4-for-efficient-and-accurate-low-precision-inference | "one 4-bit value plus minor overhead of one FP8 scale per 16 values (4.5 bits per value)" / "reduces the model memory footprint by approximately 3.5x relative to FP16, and approximately 1.8x compared to FP8" |  02, 03  |
| **R6** | NVIDIA — GeForce RTX 5090 官方产品页 | https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/#specifications | "Standard Memory Config | 32 GB GDDR7" / "Memory Interface Width | 512-bit" / "NVIDIA CUDA® Cores | 21760" / "NVIDIA NVLink™ (SLI-Ready) | No" |  01, 03, 06  |
| **R7** | NVIDIA — RTX Blackwell GPU 架构白皮书（PDF） | https://images.nvidia.com/aem-dam/Solutions/geforce/blackwell/nvidia-rtx-blackwell-gpu-architecture.pdf | "The RTX Blackwell Tensor Cores support FP16, BF16, TF32, INT8, and Hopper's FP8 Transformer Engine." / "RTX Blackwell adds new support for FP4 and FP6 Tensor Core operations" |  02, 03  |
| **R8** | NVIDIA — TensorRT-LLM 量化支持矩阵 | https://nvidia.github.io/TensorRT-LLM/latest/features/quantization.html | sm120 行：" | Blackwell(sm120) | Y | Y | Y | . | . | Y | . | . | . | . | . | "（NVFP4 / MXFP4 / FP8(per-tensor) / FP8 KV Cache 为支持；FP8 block scaling、FP8 rowwise、NVFP4 KV Cache、AWQ、GPTQ 为不支持） |  02, 03, 05  |
| **R9** | SGLang Model Gateway 官方文档 + LMSYS v0.4 博客 + SMG 独立项目 | https://docs.sglang.ai/advanced_features/sgl_model_gateway.html | "Starting from September 2024, SGLang Model Gateway, i.e., SMG, formerly named as SGLang DP Router, was built especially as a production-ready DP routing system with Rust." / v0.4 博客："pip install sglang-router" |  02, 03, 04, 05  |
| **R10** | LMSYS 官方公告（X，2025-10-23） | https://x.com/lmsysorg/status/1981458341579886718 | "SGLang Model Gateway v0.2 ... Now, it is fully rebuilt and renamed as \'SGLang Model Gateway\'" |  03, 04, 05  |
| **R11** | sgl-project/sglang #50045（SGLang 1.0 跟踪 issue） | https://github.com/sgl-project/sglang/issues/50045 | "It replaces sgl-model-gateway." / "sgl-model-gateway is deprecated in 1.0 and removed in a later release." / "The SGLang Docker images ship sgl-router instead of sgl-model-gateway." |  02, 03, 04, 05, 06  |
| **R12** | SGLang 官方 DP / DPA / SMG 指南 | https://docs.sglang.ai/advanced_features/dp_dpa_smg_guide.html | "We strongly recommend using the SGLang Model Gateway (SMG) for production-grade Data Parallelism." / "Native DP is highly not recommended for use right now." / 路由策略表：random / round_robin / power_of_two / cache_aware（默认）/ bucket |  01, 02, 03, 04, 05  |
| **R13** | SGLang 官方流水线并行文档 | https://docs.sglang.ai/advanced_features/pipeline_parallelism.html | "Although Tensor Parallelism (TP) remains the conventional approach for intra-node scaling, it frequently encounters communication bottlenecks during multi-node deployments. On the other hand, pipeline parallelism only requires cross-node communication at the boundaries of each pipeline stage ..." |  02, 03  |
| **R14** | SGLang 官方多节点部署文档 | https://docs.sglang.ai/references/multi_node_deployment/multi_node.html | 官方示例："--tp 16 --dist-init-addr 172.16.4.52:20000 --nnodes 2 --node-rank 0"（8 卡 × 2 节点，TP 跨节点）；PP 官方示例均为 4 节点 |  02, 03  |
| **R15** | sgl-router 官方 README（main 分支） | https://github.com/sgl-project/sglang/blob/main/sgl-router/README.md | "A router serves one model and spreads its requests across that model's SGLang engines. It picks an engine per request from live engine load, global KV-cache prefix matches, or session affinity" |  03, 04, 05, 06  |
| **R16** | Ray Serve 官方 SGLang 文档 | https://docs.ray.io/en/latest/serve/llm/user-guides/sglang.html | "Community SGLang support is in early development." + 官方缺口清单：同一 deployment 内多 engine 副本、engine 遥测、独立 prefill/decode worker 组、宽专家并行、弹性容错 EP |  03, 05  |
| **R17** | Ray Serve 自动扩缩容与容错文档 | https://docs.ray.io/en/latest/serve/autoscaling-guide.html | "target_ongoing_requests is the average number of ongoing requests per replica that the Serve autoscaler tries to ensure." / "the Serve controller logs the exception, kills the unhealthy replica(s), and restarts them." |  05  |
| **R18** | Ray Serve LLM 基准 + 部署初始化文档 | https://docs.ray.io/en/latest/serve/llm/benchmarks.html | "Replica startup times involving large models can be slow, leading to slow autoscaling and poor response to changing workloads." / 启动阶段拆解：Provisioning Nodes → Image Download → Model Loading → Torch Compile → Memory Profiling → CUDA Graph Capture → Warmup |  03, 05, 06  |
| **R19** | NVIDIA 官方博客 — Start and Restore GPU Workloads in Seconds with NVIDIA Snapshot（2026-11-10） | https://developer.nvidia.com/blog/start-and-restore-gpu-workloads-in-seconds-with-nvidia-snapshot | "Restoring from a Snapshot artifact brings inference replicas online in 3.6 to 42.7 seconds across tested configurations, delivering 8x to 36x speedups over cold starts that take minutes." / "NVIDIA provides ready-made examples for vLLM, SGLang, and NVIDIA TensorRT LLM" |  02, 03, 04, 05  |
| **R20** | ai-dynamo/snapshot 官方仓库（README / limitations / prerequisites / SGLang 指南） | https://github.com/ai-dynamo/snapshot | "Snapshot is a Kubernetes-native checkpoint and restore system for NVIDIA GPU workloads." / "Snapshot's APIs may still change, so it is not yet recommended for production-critical workloads." / "Workloads, including multi-GPU workloads, must run on a single node. Multi-node is on the roadmap." / "infrastructure provisioning and container image loading remain outside the measured restore path." |  02, 03, 04, 05, 06  |
| **R21** | KServe 官方控制面文档 | https://kserve.github.io/website/docs/concepts/architecture/control-plane | Mode Comparison：" | Scale-to-Zero | ❌ Not supported | ✅ Native support | "、" | Cold Start | ✅ No cold start | ⚠️ Cold start latency | "；Knative 限制清单含 "⚠️ Cold Start Latency" |  05  |
| **R22** | SGLang 源码 arg_groups/fields/model.py | https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/arg_groups/fields/model.py | remote_instance_weight_loader_backend: A[Literal["transfer_engine", "nccl", "modelexpress"], ...] = "nccl"；同族参数 send_weights_group_ports / seed_instance_ip / seed_instance_service_port / start_seed_via_transfer_engine |  02, 03, 04  |
| **R23** | SGLang 官方 R-Fork 文档（rfork.mdx） | https://docs.sglang.ai/advanced_features/rfork.html | "R-Fork (Tensor Remote Fork) is a novel weight loading methodology that leverages efficient inter-node GPU-to-GPU data transfer path to load tensors from a running SGLang instance to a new instance with zero-copy." / 后端表："nccl, transfer_engine, or modelexpress. Default is nccl." |  03, 04, 06  |
| **R24** | LMSYS 官方博客《Let Tensors Fly — Accelerating Large Model Weight Loading with R-Fork》（2025-12-10） | https://www.lmsys.org/blog/2025-12-10-rfork | "We introduce Tensor R-Fork (stands for Tensor Remote Fork) ... to load tensors from a running SGLang instance to a new instance with zero-copy."（评测环境：8×H20 + DeepSeek-R1；**官方未发布任何加速倍数**） |  02, 03  |
| **R25** | R-Fork 官方限制与已知问题（文档 + 源码 + issue） | https://docs.sglang.ai/advanced_features/rfork.html | "Only support loading weights from instance with same parallelism strategy." / send-weights-group-ports："Only needed by nccl backend" / "weight transfer disrupts the source instance's inference service" / issue #17629：TransferEngine 后端与 HiCache 不兼容 |  03, 04, 05, 06  |
| **R26** | ai-dynamo/snapshot 官方性能文档 | https://github.com/ai-dynamo/snapshot/blob/main/docs/overview/performance.md | "We tested 22 configurations of vLLM, SGLang and TensorRT-LLM on one to eight B200 GPUs. Restore was 8.1-35.9 times faster than cold start."（B200；driver 615.71.09；Snapshot v0.2.0-rc.2；SGLang 0.5.21；VAST NFSv3 over TCP；区间两端均为 SGLang 行） |  03, 05  |
| **R27** | NVIDIA Dynamo Snapshot 官方博客（前身，实验性） | https://developer.nvidia.com/blog/nvidia-dynamo-snapshot-fast-startup-for-inference-workloads-on-kubernetes | "for larger models, the restore time actually exceeds that of a cold start"（实验性；与当前的 ai-dynamo/snapshot 是两个不同产品） |  03, 05  |
| **R28** | KServe 官方 KPA 自动扩缩容文档 | https://kserve.github.io/website/docs/model-serving/predictive-inference/autoscaling/kpa-autoscaler | "that's the cold start time cost to initially spawn the pods and download the model to be ready to serve"（全站唯一的冷启动具体数字，约 10 秒，且出自 **sklearn/iris 预测模型**示例；KServe 未发布任何 LLM 冷启动数字） |  05  |
| **R29** | KServe 官方 llmisvc 自动扩缩容文档 | https://github.com/kserve/website/blob/main/docs/model-serving/generative-inference/llmisvc/autoscaling/llmisvc-autoscaling.md | "idleReplicaCount allows scaling below minReplicas when no triggers are active." / "initialCooldownPeriod is particularly useful for LLM deployments where the model takes time to load before it can serve traffic" |  05  |
| **R30** | SGLang 官方 Server Arguments 文档 + 源码 arg_groups/choices.py | https://docs.sglang.ai/advanced_features/server_arguments.html | QUANTIZATION_CHOICES（31 项）中**不含 nvfp4**（含 modelopt_fp4 / nvfp4_online / petit_nvfp4 / mxfp4）；ATTENTION_BACKEND_CHOICES 含 flashinfer；LOAD_FORMAT_CHOICES 含 remote_instance；--tp-size/--pp-size/--nnodes/--node-rank/--dist-init-addr/--mem-fraction-static/--host/--port 均存在 |  02, 03, 04, 05, 06  |
| **R31** | SGLang 官方安装文档 | https://docs.sglang.ai/get_started/install.html | "SGLang requires CUDA 13. CUDA 12 (cu129) wheels and images were retired with the upgrade to PyTorch 2.14" / "CUDA 12 images (-cu12 / -cu129) are no longer published" / Docker 示例统一用 "--shm-size 32g"；K8s 示例用 "emptyDir: medium: Memory"（**未设 sizeLimit**，另有 hostIPC: true 方案） |  02, 03, 04, 06  |
| **R32** | SGLang 官方注意力后端文档 | https://docs.sglang.ai/advanced_features/attention_backend.html | "Blackwell SM120 (e.g., RTX PRO 6000 Blackwell): triton or flashinfer for prefill/full attention" / "On SM100/SM103 with CUDA 13+, SGLang automatically selects FlashInfer for GDN prefill ..."（**SM100/SM103 ≠ SM120**） |  03, 04, 06  |
| **R33** | SGLang issue #40558 / #9233 / #15181 | https://github.com/sgl-project/sglang/issues/40558 | #40558："the server hangs or abruptly terminates during the FlashInfer autotune phase"（RTX PRO 6000 Blackwell，cc 12.0，日志含 "Detected fp8 checkpoint."） / #9233："the FP8 blockwise on blackwell sm120 is not supported by the sglang yet" / #15181："If I do not set NCCL_P2P_DISABLE=1, the process hangs indefinitely." |  02, 03, 04, 06  |
| **R34** | SGLang 官方量化文档 | https://docs.sglang.ai/advanced_features/quantization.html | "NVFP4 GEMM requires FlashInfer to be installed." / --fp4-gemm-backend auto："Auto-selects: flashinfer_cutedsl on SM100; marlin on SM80-SM90; flashinfer_cutlass otherwise (including SM120)" |  03, 04, 05  |
| **R35** | SGLang 官方环境变量文档 | https://docs.sglang.ai/references/environment_variables.html | "Use FlashInfer's PCIe-IPC all-reduce on switch-free intra-node hosts (no NVLink, no multicast), where the other custom all-reduce backends do not apply." |  04  |
| **R36** | NVIDIA 官方 nvidia-smi 拓扑工具文档 | https://developer.nvidia.com/system-management-nvidia-smi-topology | `nvidia-smi topo -m` 为 NVIDIA 官方拓扑工具；**SGLang 官方文档中没有针对 LLM 服务的 topo 指引**（全库仅 diffusion cookbook 一处附带提及） |  01  |
| **R37** | SGLang 官方 FAQ + 源码 arg_groups/memory_hook.py | https://docs.sglang.io/references/faq.html | "You can also decrease --mem-fraction-static to a smaller value, such as 0.8 or 0.7." / "When unset, it is computed as (GPU memory - reserved memory) / GPU memory, defaulting to 0.88" / 源码定义："mem_fraction_static = (model weights + KV cache pool) / GPU memory capacity" |  02, 03, 04  |

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
|---|---|---|---|---|
| **UQ1** | 是否存在官方的 20× RTX 5090 部署指南？ |  03  | **未决**。NVIDIA、Qwen、SGLang 均无任何 20 卡 5090 的部署文档；SGLang cookbook 对该模型的部署面板只覆盖单卡（Nodes 维度仅 single） | 课程中明确标注「无官方来源，本课程为合理推演」 |
| **UQ2** | 在你安装的 SGLang 版本里，`--quantization` 对应 NVFP4 的确切取值是什么？ |  04  | **可当场解决**。取值随版本与检查点导出方式变化；`nvfp4` 不是合法取值 | 课程给出候选清单与 `--help` 核对命令，不替读者选定 |
| **UQ3** | R-Fork 在 RTX 5090 上的实际权重加载耗时是多少？ |  02  | **未决**。官方仅在 8×H20 + DeepSeek-R1 上做过评测，且未发布加速倍数 | 课程把「数分钟→数秒」标为源文档主张 + 待实测假设 |
| **UQ4** | 「FP8 MoE 在 SM_120 上加载时挂起」对应的是哪条 issue？ |  02  | **已改述**。未找到完全匹配的 issue；最接近的是 #40558（autotune 阶段挂起，非加载期间）与 #9233（block-scaled FP8 特性请求） | 课程改用可查证的表述，并保留 issue 编号 |
| **UQ5** | KServe Scale-to-Zero 在 LLM 上的真实冷启动时长是多少？ |  05  | **未决**。KServe 全站唯一的冷启动数字约 10 秒，且出自 sklearn/iris 预测模型示例；从未发布 LLM 冷启动数字 | 课程改述为「KServe 自认冷启动有延迟 + LLM 路径需 initialCooldownPeriod」，不再引用「分钟级」 |
| **UQ6** | 「5 节点 × TP4 / PP5」这一布局是否有官方依据？ |  03  | **未决**。SGLang 官方 PP 示例均为 4 节点（`--nnodes 4 --tp 8 --pp-size 4` / `--tp 4 --pp-size 8`） | 课程标为「合理工程选择，非官方指导」 |
| **UQ7** | 「冷启动弹性不应依赖 Ray/K8s 的默认调度」是官方建议吗？ |  03  | **已定性**。Ray 官方文档承认冷启动慢并给出缓解手段，但**没有任何官方文档如此建议** | 课程标为源文档作者的主观主张 |
| **UQ8** | 「跨 PCIe Switch 边界」这条具体规则的官方出处是什么？ |  01, 02  | **已定性**。官方 PP 文档支持「TP 节点内、PP 跨节点」的方向，但无「PCIe Switch 边界」这一措辞；官方多节点文档甚至有 TP 跨节点示例 | 课程标为源文档主张；「绝对不能」降级为「强烈不推荐」 |
| **UQ9** | NVIDIA Snapshot 能否用于跨节点的 PP 实例？ |  03  | **已确认为不支持**。官方限制原文：「Workloads, including multi-GPU workloads, must run on a single node. Multi-node is on the roadmap.」 | 课程在 03/04/05 三处加显著限定 |
| **UQ10** | 「20 个独立副本」这种部署形态的官方依据是什么？ |  03  | **未决**。与 UQ1 同源；无任何官方 20 卡 5090 文档 | 课程标为推演，并把它列为 [06 · 6.3](06-learning-path.md#63-实践清单) 的实践目标 |
| **UQ11** | sgl-router 1.0 之后的路由策略集合与默认值是什么？ |  05  | **可当场解决**。0.x 文档列 5 种策略，1.0 README 列 `power_of_two`（默认）/ `cache_aware` / `session_aware` | 课程并列给出两代清单，要求以实际版本 `--help` 为准 |
| **UQ12** | RTX 5090 上 `--mem-fraction-static` 的实际回退值是多少？ |  02  | **未决**。官方文档写 0.88，源码 `memory_hook.py` 写 0.95，两者不一致（正常情况下能探测到显存，不走回退分支） | 课程指出文档与源码不一致，并说明正常路径不受影响 |

---

## 7.5 审计与推广记录

> 本节的审计结果在逐节 review-only 评审与跨节一致性检查完成后填写。

---

## 7.6 如何复核本课程

本课程的可追溯性依赖于四类可独立复现的动作。任何人都可以在自己的机器上重跑它们。

### 7.6.1 复核源文档未被改动

```bash
shasum -a 256 /Users/Admin/Desktop/llm-deploy-play/source-sglang.md
# 期望：24fba92410eac39bdd182f8cb0648b5a64c8d5c0f24589f2e20c52ce8d5f3a9b
```

### 7.6.2 复核 S 表摘录可还原

S 表的每一行摘录都由脚本按行范围机械抽取，可逐字节还原：

```bash
cd sglang-course.staging-20261115
python3 extract_s.py ../source-sglang.md s_table.json   # 重新生成 26 行
```

### 7.6.3 复核跨节一致性

```bash
python3 check_course.py <本课程目录>     # 链接、证据指针、影响章节列、标签语法
python3 check_quotes.py <本课程目录> ../source-sglang.md   # 源文引述逐字核对
```

### 7.6.4 复核 R 表

R 表每条都带 URL 与支撑原文。**复核方式**：打开 URL，找到摘录那句话，确认它仍然存在于该页面。

---

## 本节小结

- **§7.1** 记录了源文件的路径、SHA-256、字节数与结构统计，并声明源文件为只读。
- **§7.2** 是 **26 条 S 源定位表**，覆盖源文档的每一处事实主张；摘录由脚本机械抽取，字节级可还原。
- **§7.3** 是 **37 条 R 研究记录表**，每条含 URL、支撑原文与影响章节；全部检索日期为 2026-11-15。
- **§7.4** 是 **12 条证据缺口**，分「未决」「可当场解决」「已定性」三类，每条都写明了课程的处理方式。
- **§7.5** 记录逐节审计、跨节一致性检查与推广授权。
- **§7.6** 给出四条可独立复现的复核命令。

> **本课程相对源文档最大的增值不在于「讲了什么」，而在于「哪些能信、哪些不能信，以及不能信的时候该怎么做」。** 三条最影响可执行性的落差见 [05 · 5.7](05-related-tools.md#57-三条最实质的落差)；十二条未决问题见 [7.4](#unresolved-questions)。
