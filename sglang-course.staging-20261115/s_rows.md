| **S1** | （开篇段，无标题） | L1 | 基于你 20张RTX 5090 的硬件规模和对 SGLang 的选型，以下是整合了并行策略、Blackwell专属调优与极致冷启动的最终部署方案。 |
| **S2** | 第一步：确定硬件拓扑与并行总原则 | L7 | 在写任何配置前，先用 nvidia-smi topo -m 确认20张卡的物理连接关系。核心铁律只有一条：张量并行（TP）绝对不能跨节点或跨PCIe Switch边界。RTX 5090无NVLink，跨边界TP的All-Reduce通信会成为严重瓶颈。 |
| **S3** | 第一步：确定硬件拓扑与并行总原则 | L9 | 节点内：只做TP，将模型层内权重切分在同一个PCIe域内完成。 |
| **S4** | 第一步：确定硬件拓扑与并行总原则 | L10 | 跨节点：只做PP（流水线并行）或DP（数据并行）。PP仅在流水线阶段边界通信，对跨节点网络要求远低于TP。 |
| **S5** | 情况A：模型可完整放入单张RTX 5090（32GB显存） | L18 | 策略：纯数据并行（DP），吞吐量最大化。 启动20个独立的SGLang实例，每个实例占1张GPU，运行完整模型副本（--tp-size 1）。GPU之间零通信开销，这是吞吐量的理论最优形态。 |
| **S6** | 情况A：模型可完整放入单张RTX 5090（32GB显存） | L20 | 推荐搭配 Qwen3.8-27B的NVFP4 W4A4检查点。该模型官方验证可在单张RTX 5090上以NVFP4精度运行，GSM8K得分93.18–95.15%。建议配合 SGLang Router 在20个副本之间做请求分发。 |
| **S7** | 情况B：模型需要跨卡拆分（如百B级模型） | L24 | 策略：TP = 单节点GPU数，PP = 节点数。假设拓扑为 5节点 × 4卡/节点，则设 --tp-size 4，--pp-size 5，tp × pp = 20，刚好用满全部GPU。 |
| **S8** | 情况B：模型需要跨卡拆分（如百B级模型） | L27–L38 | `bash……--host 0.0.0.0 --port 30000 |
| **S9** | 情况B：模型需要跨卡拆分（如百B级模型） | L39 | 跨节点启动需配合 --dist-init-addr、--nnodes 和 --node-rank 协调各节点。 |
| **S10** | 第三步：Blackwell（RTX 5090）强制配置项 | L45 | RTX 5090（SM_120）在SGLang上有几个必须显式处理的坑： |
| **S11** | 第三步：Blackwell（RTX 5090）强制配置项 | L49 | \| 量化 \| NVFP4（首选）或 FP8 \| BF16显存不够；NVFP4是Blackwell原生格式，SGLang官方已验证RTX 5090单卡可跑 \| |
| **S12** | 第三步：Blackwell（RTX 5090）强制配置项 | L50 | \| 注意力后端 \| --attention-backend flashinfer \| 在Blackwell上部分默认后端的长提示TTFT可能极差，FlashInfer是必需项 \| |
| **S13** | 第三步：Blackwell（RTX 5090）强制配置项 | L51 | \| FP8 MoE注意 \| 部分FP8 MoE路径在SM_120上加载时会挂起 \| 优先选用NVFP4检查点，避开FP8 MoE的已知问题 \| |
| **S14** | 第三步：Blackwell（RTX 5090）强制配置项 | L52 | \| CUDA版本 \| CUDA 13.x \| 推荐版本，可获得最佳的FlashInfer线性注意力预填充性能 \| |
| **S15** | 第三步：Blackwell（RTX 5090）强制配置项 | L53 | \| --mem-fraction-static \| 0.85 ~ 0.90 \| 为KV Cache留足空间，NVFP4权重更小，可适当提高并发 \| |
| **S16** | 第三步：Blackwell（RTX 5090）强制配置项 | L54 | \| 共享内存 \| Docker需设置 --shm-size，K8s需调整 /dev/shm \| SGLang进程间通信依赖共享内存 \| |
| **S17** | 层次一：从零冷启动的最快路径——SGLang R-Fork（权重复用） | L62 | 这是SGLang原生的“热启动”方案。R-Fork（Tensor Remote Fork） 允许一个新实例通过高速GPU-to-GPU通道，从已运行的实例零拷贝加载模型权重，将权重加载时间从数分钟压缩到数秒。 |
| **S18** | 层次一：从零冷启动的最快路径——SGLang R-Fork（权重复用） | L64 | Seed实例：正常启动 python -m sglang.launch_server [args] |
| **S19** | 层次一：从零冷启动的最快路径——SGLang R-Fork（权重复用） | L66–L71 | `bash……--remote-instance-weight-loader-backend nccl |
| **S20** | 层次一：从零冷启动的最快路径——SGLang R-Fork（权重复用） | L72 | 若使用 transfer_engine 后端，Seed实例需额外加 --remote-instance-weight-loader-start-seed-via-transfer-engine。 |
| **S21** | 层次二：生产级秒级弹性——NVIDIA Snapshot（必选） | L76 | 这是目前冷启动速度的天花板。NVIDIA Snapshot 对已完全初始化的GPU工作负载（含CPU和GPU内存状态）做检查点，恢复时跳过权重加载、图编译等全部初始化步骤，将推理副本上线时间压缩到 3.6 ~ 42.7秒，相比分钟级冷启动加速 8~36倍。它支持SGLang作为后端。 |
| **S22** | 层次二：生产级秒级弹性——NVIDIA Snapshot（必选） | L78 | 对你的20卡集群的意义：预先启动好服务、拍下快照。之后无论是故障恢复还是闲置缩容后的唤醒，都能在秒级到数十秒内完成，彻底告别“KServe Scale-to-Zero那种分钟级冷启动”的陷阱。 |
| **S23** | 第五步：跨节点编排与路由 | L84 | 20卡多节点场景下，不建议手动逐个SSH启动。SGLang Router（现称Model Gateway） 是官方推荐的多实例路由方案，支持DP场景下的请求分发。 |
| **S24** | 第五步：跨节点编排与路由 | L86 | 如果节点间网络是InfiniBand或高速RoCE，Ray Serve可以作为上层编排，将SGLang实例作为部署单元管理，实现统一的扩缩容和故障恢复。但冷启动弹性不应依赖Ray/K8s的默认调度，而应通过NVIDIA Snapshot实现秒级恢复。 |
| **S25** | 最终部署架构总览 | L92–L115 | ┌─────────────────────────────────────────────────────────┐……└───────────────────────────┘ |
| **S26** | 最终部署架构总览 | L117 | 一句话总结：模型能塞进单卡就开20个DP副本用Router分发；塞不进就 TP=节点内卡数, PP=节点数。Blackwell上量化锁NVFP4、后端锁FlashInfer。冷启动用 R-Fork做权重复用，生产弹性用 NVIDIA Snapshot做秒级恢复，避开KServe Scale-to-Zero的分钟级冷启动。 |
