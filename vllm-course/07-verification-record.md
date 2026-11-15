# 07 · 验证记录

> **学习目标**
> 本节不是课程内容，而是**可追溯性档案**。任何人应当能够：
> 1. 拿到本课程中任意一条事实性陈述，反查到它来自源文档的哪一行，或外部的哪个 URL；
> 2. 看到本课程**没有**验证的部分，以及它为什么没有被验证；
> 3. 复现整条构建链路：源文件校验和 → 证据映射 → 审计 → 产出。

### 证据标签约定

`【Source-derived · Sxx】` 来自根文档 `source.md`；`【Research-derived · Rxx】` 来自外部权威来源；`【Illustrative】` 为教学性构造（含用于讲解的**定义性框架**），不主张 vLLM 的未经验证行为。

---

## 7.1 源文件信息

| 项 | 值 |
|---|---|
| **根源文件（只读，从未修改）** | `/Users/Admin/Desktop/vllm-play/source.md` |
| **SHA-256 校验和** | `6b1fd6c39c5f018b22097ef3f0553bc880329a00dc6742be0a3805ecad2a8365` |
| **字节数** | 6931 |
| **行数** | 91（末行无换行符，`wc -l` 报 90；按行读取为 91 行） |
| **语言** | 简体中文 |
| **结构** | **7 个标题**（5 个 `###` + 2 个 `####`）+ 1 段开篇；含 **4 个代码块** |
| **源内容分类** | **Public**（关于开源项目 vLLM 的通用技术介绍，无私有主机名、凭据、内部端点或专有信息） |
| **外部研究授权** | 因内容为 public，研究缺口**无需**逐条查询授权即可进行；所有外部请求均为公开文档/论文/官方仓库 |

> **源字节保全声明**：本课程构建过程**从未写入** `source.md`。构建前与推广前均重新校验 SHA-256，两次一致（见 [7.5.4](#final-result)）。

---

<a id="s-locators"></a>

## 7.2 S 源定位表

每一行是一个**源定位码**。课程中每条 `【Source-derived · Sxx】` 陈述都对应下表一行。"影响的课程章节"一列由脚本从 01–06 的**实际引用**机械统计得出，非人工填写。

| 定位码 | 源标题 | 行范围 | 摘录（节选） | 影响的课程章节 |
|---|---|---|---|---|
| **S1** | （开篇段，无标题） | L1 | "它的首要目标不是让单个请求跑得最快，而是让**整个 GPU 在单位时间内服务尽可能多的用户**" | 01, 05, 06 
| **S2a** | 🎯 一个类比：从"包场餐厅"到"拼桌高手" | L5–L9 | "他必须凑齐一桌客人（一个 Batch），等这桌所有人**全部吃完**（所有请求生成完毕），才肯放下一桌人进来"；"为每位客人预留一张巨大的、固定的桌子（预分配连续显存）……**显存碎片**" | 01, 02, 06 |
| **S2b** | 🎯 一个类比：从"包场餐厅"到"拼桌高手" | L11–L13 | "**连续批处理 (Continuous Batching)**：它的规则是'随吃随走，有空就拼'"；"**分页注意力 (PagedAttention)**……把餐厅改造成无数个**标准化的小格子**（固定大小的内存块）……**前缀缓存**" | 01, 02, 03, 05, 06 |
| **S2c** | 🎯 一个类比：从"包场餐厅"到"拼桌高手" | L15 | "虽然单个客人（请求）的等待时间不一定最短，但**整个餐厅的翻台率（吞吐量）实现了飞跃**" | 01, 02, 06 |
| **S3a** | 💎 核心概念：两个支柱 | L21 | "借鉴了操作系统的虚拟内存思想，将 KV Cache……切分成固定大小的 **'块'（Block）**，并允许这些块存储在显存中**不连续**的物理位置上。一个请求的逻辑序列，通过一个'块表'映射到物理块上" | 01, 02, 03, 05, 06 |
| **S3b** | 💎 核心概念：两个支柱 | L23 | "它在**每个推理步（step）** 都会重新组批，而非等待整个批次结束。一旦有请求完成，调度器会立刻将队列中的新请求插入"；"这需要 PagedAttention 提供的灵活内存管理作为基础，因为新请求随时需要新的内存块" | 01, 02, 03, 05, 06 |
| **S4a** | 🗺️ 使用场景：它适合谁，不适合谁 | L31 | "**高并发、多租户的生产服务**……vLLM 能让单张 GPU 服务更多用户，显著降低单位请求的成本" | 01, 03 |
| **S4b** | 🗺️ 使用场景：它适合谁，不适合谁 | L32 | "**大规模离线批量处理**……在这种情况下，**总完成时间**比单个任务的延迟更重要" | 01, 03 |
| **S4c** | 🗺️ 使用场景：它适合谁，不适合谁 | L33 | "**长文本与 RAG 应用**：PagedAttention 对长序列的内存管理优势明显，且其**前缀缓存**能力可以在多轮对话或 RAG 场景中，复用重复的系统提示词或文档上下文" | 01, 02, 03, 05 |
| **S4d** | 🗺️ 使用场景：它适合谁，不适合谁 | L34 | "**追求'开箱即用'的 OpenAI API 兼容性**：vLLM 原生提供 OpenAI 风格的 API 服务器，迁移成本极低，只需更改 Base URL 即可" | 01, 03, 04, 05, 06 |
| **S4e** | 🗺️ 使用场景：它适合谁，不适合谁 | L38 | "对'冷启动延迟'极度敏感的交互式场景……其冷启动时间可能不如一些为 Serverless 设计的方案（如 KServe）" | 01, 03, 05, 06 |
| **S4f** | 🗺️ 使用场景：它适合谁，不适合谁 | L39 | "需要多框架统一服务的复杂流水线……**NVIDIA Triton** 这类多框架服务器可能更合适，vLLM 则更专注于 Transformer 类 LLM 的高效服务" | 01, 03, 05, 06 |
| **S4g** | 🗺️ 使用场景：它适合谁，不适合谁 | L40 | "**超大规模（70B+）的多节点分离式推理**……**NVIDIA Dynamo** 等方案可能提供了更原生的支持。vLLM 虽然也在发展相关能力，但在这一特定前沿领域，其成熟度可能不如其核心的单机/单副本场景" | 01, 03, 05 |
| **S4h** | 🗺️ 使用场景：它适合谁，不适合谁 | L41 | "**需要训练或微调**：vLLM **仅专注于推理**，不包含任何训练功能。如果需要微调模型，你需要回到 PyTorch、DeepSpeed 等训练框架" | 01, 03, 05, 06 |
| **S5a** | 🛠️ 使用方法：一条命令启动服务 | L47–L57 | "uv venv myenv --python 3.12 --seed …… source myenv/bin/activate …… uv pip install vllm"；"pip install vllm" | 04 |
| **S5b** | 🛠️ 使用方法：一条命令启动服务 | L60–L65 | "vllm serve meta-llama/Llama-2-7b-hf --port 8000"；"在 `8000` 端口启动一个兼容 OpenAI `/v1/chat/completions` 等接口的服务" | 03, 04 |
| **S5c** | 🛠️ 使用方法：一条命令启动服务 | L67–L79 | "client = OpenAI(base_url='http://localhost:8000/v1', api_key='token-abc123')"；"client.chat.completions.create……" | 03, 04, 06 |
| **S5d** | 🛠️ 使用方法：一条命令启动服务 | L81–L87 | "llm = LLM(model='meta-llama/Llama-2-7b-hf')"；"outputs = llm.generate(……, SamplingParams(temperature=0.8))" | 03, 04, 06 |
| **S6** | 💎 总结 | L89–L91 | "vLLM 的核心价值在于**用系统工程的手段，极致地压榨 GPU 的并发服务能力**"；"如果你的目标是在给定硬件上，以尽可能低的成本服务尽可能多的用户或处理尽可能多的数据，并且主要使用 Transformer 架构的开源模型，那么 vLLM 通常是那个最优先、最稳妥的默认选择" | 01, 05, 06 |

---

<a id="r-locators"></a>

## 7.3 R 研究记录表

每一行是一次**外部研究**。所有检索日期均为 **2026-11-15**（统一声明于本节前言，未逐行重复）。优先级：官方文档 / 标准 / 原始论文 / 官方仓库；社区 issue 仅用于标注尚未被官方确认的行为，并明确标注置信度。

| 定位码 | 主题 | 来源 URL | 关键原文 / 摘录 | 影响的课程章节 | 置信度 |
|---|---|---|---|---|---|
| **R1** | vLLM 版本与 Python 要求 | https://pypi.org/project/vllm/ | 最新版本 `0.33.0`，发布于 `November 2, 2026`；`Requires: Python >=3.11, <3.15`；摘要 "A high-throughput and memory-efficient inference and serving engine for LLMs" | 01, 04, 06 | 高 |
| **R2** | 平台支持边界 | https://docs.vllm.ai/en/stable/getting_started/installation/gpu | "vLLM can fully run only on Linux but for development purposes, you can still build it on other systems (for example, macOS) ... The binaries will not be compiled and won't work on non-Linux systems." | 01, 03, 04, 06 | 高 |
| **R3** | 快速上手、端口、鉴权、chat template、平台后端 | https://docs.vllm.ai/en/stable/getting_started/quickstart | `vllm serve Qwen/Qwen2.5-1.5B-Instruct`；默认地址 `http://localhost:8000`，可用 `--host`/`--port` 更改；鉴权用 `--api-key` 或 `VLLM_API_KEY`（支持多密钥，匹配任一即可）；`curl http://localhost:8000/v1/models`；"By default, vLLM downloads models from Hugging Face."；"llm.generate method does not automatically apply the model's chat template"；`llm.chat(messages_list, sampling_params)`；`generation_config="vllm"` / `--generation-config vllm`；Apple Silicon 用 vLLM-Metal（MLX 后端，模型取自 `mlx-community`）；ROCm 需 `--extra-index-url https://wheels.vllm.ai/rocm/` | 01, 03, 04, 06 | 高 |
| **R4** | PagedAttention 原始论文 | https://arxiv.org/abs/2309.06180 ・ https://dl.acm.org/doi/10.1145/3600006.3613165 (SOSP '23) | "vLLM, an LLM serving system that achieves (1) near-zero waste in KV cache memory and (2) flexible sharing of KV cache within and across requests"；KV Cache "grows and shrinks dynamically"；"vLLM improves the throughput of popular LLMs by 2--4× with the same level of latency compared to the state-of-the-art systems, such as FasterTransformer and Orca" | 01, 02, 06 | 高 |
| **R5** | 分页机制与量化指标 | https://vllm.ai/blog/2023-06-20-vllm | "existing systems waste 60% – 80% of memory due to fragmentation and over-reservation"；"PagedAttention partitions the KV cache of each sequence into blocks, each block containing the keys and values for a fixed number of tokens"；"The contiguous logical blocks of a sequence are mapped to non-contiguous physical blocks via a block table"；"The physical blocks are allocated on demand as new tokens are generated."；"In PagedAttention, memory waste only happens in the last block of a sequence. In practice, this results in near-optimal memory usage, with a mere waste of under 4%."；"PagedAttention keeps track of the reference counts of the physical blocks"；"implements the Copy-on-Write mechanism"；并行采样/beam search "cutting their memory usage by up to 55%"、"up to 2.2x improvement in throughput"；"vLLM achieves up to 24x higher throughput compared to HF and up to 3.5x higher throughput than TGI" | 01, 02, 05, 06 | 高 |
| **R6** | V1 默认开启前缀缓存 | https://vllm.ai/blog/2025-01-27-v1-alpha-release | "In V0, enabling prefix caching sometimes causes significant CPU overhead ... As a result, it is disabled by default."；"we observed that V1's prefix caching causes less than 1% decrease in throughput even when the cache hit rate is 0%"；"Thanks to the near-zero overhead, we now enable prefix caching by default in V1." | 02, 03, 04, 05, 06 | 高 |
| **R7** | KV Cache 块大小默认值 | https://docs.vllm.ai/en/stable/api/vllm/config/cache | `DEFAULT_BLOCK_SIZE: ClassVar[int] = 16`；`block_size` 文档："Size of a contiguous cache block in number of tokens. Accepts None (meaning 'use default'). After construction, always int." | 02, 03, 05, 06 | 高 |
| **R8** | 引擎参数默认值 | https://docs.vllm.ai/en/stable/configuration/engine_args.html | `--gpu-memory-utilization` → `Default: 0.92`；`--dtype` → `Default: auto`；`--max-model-len` → "will be automatically derived from the model config"；`--block-size` → "Accepts None (meaning 'use default')" | 03, 05, 06 | 高 |
| **R9** | KServe 定位、与 vLLM 的集成路径、scale-to-zero 前提 | https://github.com/kserve/kserve ・ https://docs.vllm.ai/en/stable/deployment/integrations/kserve ・ https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-overview | "Standardized Distributed Generative and Predictive AI Inference Platform for Scalable, Multi-Framework Deployment on Kubernetes"；"Optimized Backends: Support for vLLM and llm-d for optimized performance for serving LLMs"；"Cost Efficient: Scale-to-zero on expensive resources when not in use"；**Standard 安装方式** "does not support canary deployment and request based autoscaling with scale-to-zero"；"vLLM can be deployed with KServe on Kubernetes for highly scalable distributed model serving"；两条路径："KServe's Hugging Face serving runtime" 或 "LLMInferenceService that uses llm-d"；llm-d "combining vLLM's inference engine with Kubernetes orchestration and intelligent routing capabilities"，含 "KV-cache aware scheduling, disaggregated prefill-decode serving, and distributed inference" | 05, 06 | 高 |
| **R10** | NVIDIA Triton 定位与后端 | https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/index.html | "an open source inference serving software that streamlines AI inferencing"；"enables teams to deploy any AI model from multiple deep learning and machine learning frameworks"；后端含 "TensorRT, PyTorch, ONNX, OpenVINO, Python, RAPIDS FIL, and more" | 05, 06 | 高 |
| **R11** | NVIDIA Dynamo 定位与分离式部署 | https://docs.nvidia.com/dynamo/kubernetes/disaggregated-serving/overview ・ https://developer.nvidia.com/dynamo | "Disaggregated serving separates the two phases of LLM inference into their own worker pools so you can scale, size, and place them independently"；Prefill = "Processes the prompt and produces the initial KV cache"（缩放压力：输入长度、提示词复用、上下文大小）；Decode = "Generates output tokens using the KV cache"（缩放压力：并发数、输出长度、活跃 KV 显存）；"supports open source inference engines—including SGLang, NVIDIA TensorRT™ LLM, and vLLM" | 03, 05, 06 | 高 |
| **R12** | SGLang 定位与特性 | https://docs.sglang.ai/ | "High-performance serving framework for large language and multimodal models"；"an inference framework meant for production level serving"；"low-latency, high-throughput inference with RadixAttention, prefix caching, and multi-GPU parallelism"；"from a single GPU to large distributed clusters"；"Compatible with Hugging Face and OpenAI APIs"；"powering 400k+ GPUs" | 05, 06 | 高 |
| **R13** | Hugging Face TGI 现状 | https://huggingface.co/docs/text-generation-inference/index | "Text Generation Inference (TGI) is a toolkit for deploying and serving Large Language Models (LLMs)"；**"text-generation-inference is now in maintenance mode. Going forward, we will accept pull requests for minor bug fixes, documentation improvements and lightweight maintenance tasks."**；"TGI has initiated the movement for optimized inference engines to rely on a `transformers` model architectures. This approach is now adopted by downstream inference engines, which we contribute to and recommend using going forward: [vllm], [SGLang]" | 01, 05, 06 | 高 |
| **R14** | Llama-2-7b-hf 的授权状态与上下文长度 | https://huggingface.co/meta-llama/Llama-2-7b-hf | "You need to share contact information with Meta to access this model."；"Use of this model is governed by the Meta license. In order to download the model weights and tokenizer, please visit the website and accept our License before requesting access here."；模型表：Llama 2 7B → Content Length **4k** | 03, 04, 06 | 高 |
| **R15** | 前缀缓存实现细节、哈希算法、信任组隔离 | https://docs.vllm.ai/en/stable/design/prefix_caching | APC "caches the KV cache of existing queries, so that a new query can directly reuse the KV cache if it shares the same prefix with one of the existing queries, allowing the new query to skip the computation of the shared part"；v1 块表 append-only，"changing the block table from `[0, 3]` to `[0, 1]` is not allowed ... we will have duplicated blocks for the hash key E-H"；`--prefix-caching-hash-algo`：`sha256`（默认）/`sha256_cbor`（可复现、跨语言兼容）/`xxhash`（更快，非密码学）；"cache sharing is limited to users or requests that explicitly agree on a common salt, enabling cache reuse within a trust group while isolating others" | 02, 06 | 高 |
| **R16** | 前缀缓存在 `temperature=0` 下的确定性差异（社区报告） | https://github.com/vllm-project/vllm/issues/40896 | "in vLLM v1, `enable_prefix_caching` defaults to `model_config.is_prefix_caching_supported` ... Removing `--enable-prefix-caching` from the cmdline does NOT disable it; only `--no-enable-prefix-caching` does"；报告：同一请求在 `temperature=0` 下首次与后续输出不同，"Disabling prefix caching with `--no-enable-prefix-caching` makes the output deterministic across all runs" | 03, 04, 06 | **中**（社区 issue；`--no-enable-prefix-caching` 这一开关本身见于官方旧版 engine args 文档，但该确定性差异尚未见官方文档确认或修复状态说明） |
| **R17** | 官方调优文档：分块 prefill、compute-bound / memory-bound 画像、TTFT / ITL | https://docs.vllm.ai/en/stable/configuration/optimization | "In V1, chunked prefill is enabled by default whenever possible."；"With chunked prefill enabled, the scheduling policy prioritizes decode requests."；"It batches all pending decode requests before scheduling any prefill operations."；"This feature helps improve both throughput and latency by better balancing compute-bound (prefill) and memory-bound (decode) operations."；"It helps achieve better GPU utilization by locating compute-bound (prefill) and memory-bound (decode) requests to the same batch."；"If a pending prefill request cannot fit into `max_num_batched_tokens`, it automatically chunks it."；"Smaller values (e.g., 2048) achieve better ITL because there are fewer prefills slowing down decodes."；"Higher values achieve better time to first token (TTFT) as you can process more prefill tokens in a batch." | 03, 05, 06 | 高 |
| **R18** | Hugging Face token 的传递方式（`HF_TOKEN` 环境变量） | https://huggingface.co/docs/huggingface_hub/guides/cli ・ https://huggingface.co/docs/hub/security-tokens | "To be more secure, we recommend passing your token as an environment variable to avoid pasting it in your command history."；"This command will not log you out if you are logged in using the `HF_TOKEN` environment variable"；"Use `--secrets HF_TOKEN` to pass your local Hugging Face token implicitly."；"User Access Tokens are the preferred way to authenticate an application or notebook to Hugging Face services." | 04 | 高 |

---

<a id="unresolved-questions"></a>

## 7.4 证据缺口与未决问题

以下条目是**本课程没能消除的不确定性**。它们要么是源文档未提供，要么是外部证据不足或相互冲突。按 HITL 保留，不由构建方自行裁定。

| 编号 | 缺口 / 冲突 | 需要的证据 | 受影响章节 | 当前处理 |
|---|---|---|---|---|
| **UQ1** | 源文档未标注 vLLM 版本 | 源文档写作时的版本号 | 01, 04 | 课程基于 **0.33.0（2026-11-02）**【R1】构建；源文档的 `uv pip install vllm`（不带 `--torch-backend=auto`）在当前版本下是否仍稳定解析 torch 依赖，官方文档未直接说明。课程按官方推荐形式给出，并标注了差异 |
| **UQ2** | 官方文档对 `enable_prefix_caching` 默认值的表述不一致：feature 页写 "Set `enable_prefix_caching=True` in vLLM engine to enable APC"，而 V1 官方博客写 "we now enable prefix caching by default in V1"；engine args 页未列出该参数默认值 | 官方对 V1 默认值的明确声明 | 02, 03 | 以 **V1 官方博客**（R6）为准，同时在 [02 节](02-core-concepts.md) 与 [03 节](03-core-functionality.md#engine-defaults) 显式标出这一不一致，不掩盖 |
| **UQ3** | 源文档客户端示例传了 `api_key="token-abc123"`，但服务端命令未配置 `--api-key`；源文档未说明这是占位符还是配置遗漏 | 源文档作者意图 | 04 | 课程按官方文档解释为"客户端 key 不会被校验"，并在 [04 节](04-usage.md#common-blockers) 显式提示生产环境必须配置服务端鉴权 |
| **UQ4** | 源文档示例使用 gated 模型 `meta-llama/Llama-2-7b-hf`；本次构建环境无 Meta 授权，无法实际执行该下载与启动流程 | 授权环境下的完整执行记录 | 04 | 课程据【R14】说明 gated 前提，并给出官方 quickstart 的非 gated 路径作为可验证的替代；在 [04 节 gated 讨论处](04-usage.md#common-blockers) 明确标注**未实跑 gated 路径** |
| **UQ5** | 源文档称 vLLM 在分离式推理上"成熟度可能不如" Dynamo，但未给出任何对比数据 | 同硬件同负载下的公开对比基准 | 03, 05 | 课程补上了"Dynamo 支持 vLLM 作后端"这一事实【R11】，但**未找到**公开的同条件对比数据，故不断言孰优孰劣 |
| **UQ6** | 源文档提到前缀缓存，但完全未提及信任组 / salt 隔离机制；多租户下的隔离行为在源文档中无描述 | 源文档对多租户隔离的意图 | 02 | 课程据【R15】补齐机制说明，并标注为"源文档未提及" |
| **UQ7** | 源文档未说明 `vllm serve` 是前台常驻进程，也未说明客户端调用需等服务器就绪 | 源文档的时序意图 | 04 | 课程据【R3】补齐时序说明 |
| **UQ8** | 前缀缓存在 `temperature=0` 下导致首次与后续请求输出不一致：社区 issue 报告了，但未见官方文档确认或修复状态说明 | 上游官方确认 | 04 | 课程以【R16】标注为"社区报告"，置信度标为**中**，并给出 `--no-enable-prefix-caching` 的规避方式【R16 / R6】 |
| **UQ9** | 源文档**完全未提及** llm-d、SGLang、TGI 三个工具——它们与 vLLM 的关系、同层还是异层，均不在源文档覆盖范围内 | 源文档作者对这些工具的定位意图 | 05 | 课程据【R9 / R12 / R13】研究补齐三者的定位与关系，并在 [05 节](05-related-tools.md) 逐处标注"源文档未提及" |

### 研究缺口处理原则

- **研究失败不阻塞安全的源文档章节**。上表任何一条未解决，都不影响其余章节的准确性。
- **不发明引用**。若某项能力找不到可靠证据，保留为未决问题，而不是补一个看起来合理的说法。
- **冲突记录而非静默取舍**。UQ2 即为典型：两处官方表述不一致，课程同时呈现并说明取舍依据。

---

## 7.5 审计与推广记录

<a id="promotion-gate"></a>

### 7.5.1 构建链路

| 阶段 | 产物 | 校验方式 |
|---|---|---|
| 1. 读源、抽取结构 | S 源定位表（[7.2](#s-locators)，19 条） | 每条含标题 + 行范围 + 摘录；已逐条回源核对 |
| 2. 缺口识别与研究 | R 研究记录表（[7.3](#r-locators)，18 条） | 每条含 URL + 检索日期 + 原文 + 置信度；全部经直接打开页面取证，未使用搜索摘要 |
| 3. 起草（staging） | 7 个章节文件 | 证据标签逐条标注 |
| 4. 清单（manifest） | `MANIFEST.json` | 每文件 SHA-256 + 源文件只读声明 + 禁区路径 |
| 5. 逐节审计 | 审计发现表（[7.5.2](#audit-findings)） | 每节独立 review-only 评审，边界为 manifest |
| 6. 跨节一致性 | 一致性发现与修正（[7.5.3](#consistency-pass)） | 术语、标签、链接、矛盾、引用完整性（脚本核验） |
| 7. 推广 | 最终结果（[7.5.4](#final-result)） | 源校验和 + 目标路径 + 清单校验和 + 逐文件授权 |

### <a id="audit-findings"></a>

### 7.5.2 逐节审计发现

> 由 `post-mortem` 技能以 **review-only** 模式执行，目标边界为暂存清单（`MANIFEST.json`）所列的 7 个暂存文件；源文件与暂存目录之外的文件一律只读。**七次评审均未发生任何写入**——逐一体检了评审 agent 的工具调用记录：仅有读取与 grep，无 Write/Edit/MultiEdit。

| 章节 | 结论 | Critical | High | Medium | Low | 关键发现 | 处理 |
|---|---|---|---|---|---|---|---|
| **01** · 定位与背景 | PASS-WITH-FINDINGS | 0 | 2 | 3 | 4 | ① 例 1 的"**前 480 步**"方向写反——A 在第 20 步就结束，占着批位的是**后** 480 步；② 同一处的"有效工作占比不到 4%"混淆了两个口径，且与官方博客的 "under 4%"（**显存**浪费率）撞名；③ 1.2 节多处未标注断言（"静态批处理""算力闲置""尾延迟""按最大可能长度预留"——后者源文档与 R5 均无支撑）；④ 对照表引用的 S 码不全（"每个推理步重新组批"实为 S3b）；⑤ Windows 一句被并入【R3】标签 | 全部已修；"按最大可能长度预留"改写为官方博客的 "over-reservation"（【R5】） |
| **02** · 核心概念 | PASS-WITH-FINDINGS | 0 | 1 | 4 | 1 | ①「Key 和 **Vector**」术语错误（应为 Value），且"最主要显存消耗来源"超出 S3a 支撑；② KV Cache 属性表、推理步定义、"接近 100%" 等 5 处未标注断言；③ "接近 100%" 是无界量化 | 全部已修 |
| **03** · 核心功能 | PASS-WITH-FINDINGS | 0 | 2 | 4 | 3 | ① prefill/decode 的"算力密集 / 显存带宽密集"被归因到 R11，但 R11 只定义阶段与缩放压力；② 分块 prefill 无标签、无来源；③ `--max-model-len` 线性外推未标注；④ `--dtype auto` 被误标为"推理模式" | ①②经补 **R17**（官方调优文档）解决；③④⑤⑥按评审建议修正 |
| **04** · 使用方法 | PASS-WITH-FINDINGS | 0 | 2 | 6 | 4 | ① `export HF_TOKEN` 未标注且**无任何 R 记录支撑**；② 文本暗示"拿到 token 即可下载"，未说明**token ≠ 授权**（未获 Meta 授权仍会 403）；③ "模型 ID 不是 `--model`"超出 R3 引文——`vllm serve --model X` 实际可用；④ 例子 3 的"预期观察"列把未验证的日志内容/JSON 行为写成了断言 | ①②经新增 **R18**（Hugging Face 官方 CLI 文档）并补写"token 不等于授权"后解决；③④已按建议改写为"检查什么"与位置参数表述 |
| **05** · 相关工具 | **FAIL** | 1 | 2 | 6 | 5 | ① **【证据缺口 · UQ9】被引用 3 次但 07 中不存在该条目**（悬空指针）；② `#tool-comparison` 锚点实际落在 5.3 而非 5.4，链接标错小节；③ RadixAttention 的中文注解与"块表哈希链"（本课程未使用的术语）超出 R12 支撑；④ 各工具"与 vLLM 的重叠"单元格普遍未标注 | 全部已修（新增 UQ9 条目、新增 `#selection-chain` 与 `#deployment-topology` 锚点、逐条补标签） |
| **06** · 学习路径 | PASS-WITH-FINDINGS | 0 | 3 | 4 | 3 | ① 标题写"六阶段"但实际是**七个**阶段（0–6）；② "论文的 under 4%" 归因错误——该数字出自**官方博客**（R5）而非论文（R4）；③ R8 只支撑"默认值"，不支撑"调大 `--max-model-len` 压低并发"的推论；④ "TTFT" 未出现在任何 R 记录中 | 全部已修 |
| **07** · 验证记录 | PASS-WITH-FINDINGS | 0 | 1 | 4 | 3 | ① 源结构计数错误（实际 **7 个标题**、**4 个代码块**）；② **S6 是死证据**——定义了却从未被引用；③ "影响的课程章节"列与实际引用**31/43 行不匹配**；④ UQ4 从未被引用 | 全部已修：受影响章节列已由脚本从 01–06 实际引用**机械重算**；S6 已接入 01 节；UQ4 已接入 04 节 |

#### 审计发现的共同根因（预防规则）

七次评审中有六次独立地指向**同一个失效模式**：

> **引用相邻不等于引用支撑。** 一段话里先放一个有据可查的引文，紧接着放一个自己的推论——读者（和评审）容易把后者当成前者的一部分。02 的"接近 100%"、03 的"并发减半"、05 的"层内重叠"、06 的"调大 `--max-model-len` 压低并发"，全都是这个形态。

**已采纳的预防规则**（本次修正的判定依据）：

1. 凡含**数量词、倍数、因果连接词**（"等于…""大约…""会导致…""密集"）的句子，必须自带标签，不得靠段落里的邻近引文"继承"。
2. 教学用的线性外推、启发式分类、术语框架，一律显式标为 `【Illustrative · …】` 并写出其成立假设。
3. 证据表里出现、却从未被任何章节引用的条目（死证据）与被引用、却不在证据表里的条目（悬空指针），都用脚本双向核验——本轮发现并修复了 **1 个悬空指针（UQ9）** 与 **1 条死证据（S6）**。

### <a id="consistency-pass"></a>

### 7.5.3 跨节一致性检查

在七次逐节审计与全部修正**之后**，另行执行了一次**只读**的跨节一致性扫描（脚本 + 人工复核）。

| # | 检查项 | 方法 | 结果 |
|---|---|---|---|
| 1 | **本地链接与锚点** | 脚本遍历全部 Markdown 链接，逐个解析目标文件与 `#锚点` | **77 条全部通过**（终稿计数：脚本遍历 7 个文件的全部本地链接，逐个解析目标文件与 `#锚点`）；所有跨节锚点均为显式 `<a id="…">`，不依赖 Markdown 自动锚点 |
| 2 | **证据表双向完整性** | 脚本抽取 01–06 的全部 S/R/UQ 引用，与 07 的定义表双向比对 | **19 S + 18 R + 9 UQ：悬空指针 0、死证据 0** |
| 3 | **「影响的课程章节」列** | 脚本从 01–06 的实际引用重算，与三张表（[7.2](#s-locators) 19 行 + [7.3](#r-locators) 18 行 + [7.4](#unresolved-questions) 9 行）共 **46 行**逐行比对 | **46/46 行完全一致**（此前 31/43 行不匹配） |
| 4 | **术语一致性** | 扫描核心术语在 7 个文件中的分布 | 连续批处理 / 分页注意力 / 块表 / 前缀缓存 / 推理步 / Prefill / Decode 用法统一，无同义异名 |
| 5 | **数值一致性** | 扫描 13 个关键数字在全文的出现位置 | `0.92`、`16 token`、`0.33.0`、`>=3.11,<3.15`、`2–4×`、`24×`、`3.5×`、`60–80%`、`under 4%`、`55%`、`2.2×`、`400k+`、`4k` —— 每个数字在各处取值一致 |
| 6 | **证据标签语法** | 正则校验全部 `【…】` 是否属于三类标签之一（允许带限定后缀） | 全部合规；表中简写 `【Sxx】`/`【Rxx】` 已在各表头显式声明 |
| 7 | **锚点消歧** | 人工核对同名语义目标 | 已拆分：`#capabilities`(03 §3.1) / `#capability-boundary`(03 §3.3) / `#engine-defaults`(03 §3.5) / `#example-2`；`#tool-comparison`(05 §5.3) / `#selection-chain`(05 §5.4) / `#deployment-topology`(05 例子 2) |

#### 一致性扫描中发现并已修正的问题

| 问题 | 处理 |
|---|---|
| 06 阶段 5 的两个链接指向 `#tool-comparison`（实际落在 5.3 工具对比表），而文字说的是 **5.4 决策链** | 05 新增 `<a id="selection-chain">` 与 `<a id="deployment-topology">`，06 与 05 小结的链接一并重指 |
| 06 阶段 3 的链接指向 `#capabilities`（实际落在 3.1），文字说的是 **3.3 边界清单** | 03 新增 `<a id="capability-boundary">`，链接重指；06 阶段 6 的 `#capabilities` 同样改为 `#engine-defaults` |
| 04 指向"03 节例子 2"的链接落在 `#capabilities` | 03 新增 `<a id="example-2">`，链接重指 |
| 06 标题写"六阶段"，但实际是 **七个**阶段（阶段 0–6） | 全部改为"七阶段（阶段 0–6）" |
| 06 把 "under 4%" 归因给**论文** | 改为归因**官方博客**（R5）——该数字出自博客，论文给的是 2–4× 吞吐提升 |
| 06 的"前 3 阶段"含义不明 | 改为"阶段 0–2" |
| 01 例子 1 的"4%"与官方博客的 "under 4%"（显存浪费率）撞名 | 01 改写指标口径并加显式区分提示 |
| 07 的 UQ9 被 05 引用三次却未定义（悬空指针） | 07 新增 UQ9 条目 |
| S6 在证据表中定义却从未被任何章节引用（死证据） | 01 §1.1 接入 S6 |
| UQ4 在证据表中定义却从未被引用 | 04 的 gated 模型讨论处接入 UQ4 |

> **未解决而保留的**：UQ1–UQ9 全部为**内容层面**的不确定性（源文档未提供 / 外部证据冲突 / 未实跑），不是结构缺陷。它们在正文中就地标注并回指本表，不影响课程的链接完整性与引用自洽。

### <a id="final-result"></a>

### 7.5.4 最终结果

| 检查项 | 结果 |
|---|---|
| **源文件校验和** | `6b1fd6c39c5f018b22097ef3f0553bc880329a00dc6742be0a3805ecad2a8365` —— 与构建前一致，**源文件未被修改** |
| **章节文件数与顺序** | **7 个**，命名与顺序符合 `01`–`07` 约定，无缺项、无 `Not applicable` 占位 |
| **本地链接** | **77 条**全部解析成功（含跨文件锚点） |
| **源派生声明** | 全部可回查至 [7.2](#s-locators) 的 S 行（含源标题 + 行范围 + 摘录） |
| **研究派生声明** | 全部可回查至 [7.3](#r-locators) 的 R 行（含 URL + 检索日期 + 原文 + 置信度） |
| **证据表自洽性** | 悬空指针 0、死证据 0、章节列不匹配 0 |
| **未决问题** | 9 条，全部显式保留并在正文就地标注（UQ1–UQ9） |
| **审计** | 7 次逐节 review-only；合计 **1 Critical / 13 High / 31 Medium / 23 Low** 条发现，**全部已修并回写暂存区** |
| **审计边界** | 评审全程只读——逐一体检了 7 个评审 agent 的工具调用记录，**无任何 Write / Edit / MultiEdit** |
| **符号链接** | 暂存目录与目标目录树内**无符号链接**；所有目标均为常规文件 |
| **作用域** | 全部写入均在暂存目录内；`source.md` 与目录树外文件零写入 |

**推广结论：作用域、来源、链接、一致性四道闸门全部通过，课程可以推广。**

#### 推广执行记录（promotion executed）

| 项 | 值 |
|---|---|
| **执行时间** | 2026-11-15 |
| **目标目录** | `/Users/Admin/Desktop/vllm-play/course/`（新建；6 个文件为 `create`，`07-verification-record.md` 终稿订正后为 `replace`） |
| **推广前源校验和** | `6b1fd6c3…2a8365`（与构建前一致） |
| **推广后源校验和** | `6b1fd6c3…2a8365`（**未变**） |
| **推广后逐文件校验** | 目标目录 7 个文件的 SHA-256 与暂存文件**逐个相等** |
| **符号链接** | 目标目录内**无符号链接**，全部为常规文件 |
| **目录外影响** | 无——`source.md` 与 `.git` 均未被写入 |

> **终稿订正记录（2026-11-15，推广后）**：终稿复核时发现本节两处「本地链接 71 条」与实际终稿（**77 条**）不符——原因是审计收尾阶段为 `03` 新增了 `#engine-defaults` 与 `#example-2` 两个锚点、并在 `04`/`06` 增加了指向它们的链接，链接总数随之增加，但本节的计数未同步。**订正方式**：仅在暂存区修改本节这两处计数并重新跑通链接校验与一致性核验，随后以 **replace** 方式把 `07-verification-record.md` 重新推广一次；其余 6 个文件字节未变，未重新复制。
>
> **同批订正的另一处**：[7.2](#s-locators) 中 `S1` 的「影响的课程章节」原为 `01, 06`，而终稿的 `05` 也引用了 `S1`（§5.4 决策链与 §5.6 分层图），实际应为 `01, 05, 06`——同样因收尾期对 `05` 的编辑而变陈旧。该列已由脚本按 `01`–`06` 的**实际引用**重新统计，复核后确认**仅 `S1` 一行需要改动**，S/R 两表其余 36 行与 UQ 表 9 行均已一致。
>
> **同批订正的第三、四处**：① §7.5.2 逐节审计表中，**`02` 行被完整重复了一次**（两行逐字节相同），已删除重复行——现为 7 行、7 个章节各一行，Critical/High/Medium/Low 合计仍为 **1 / 13 / 31 / 23**，与 §7.5.4 最终结果表的口径一致；② 「影响的课程章节」列的核对行数原写作 **37 行**（仅 S + R 两表），但该列同样存在于未决问题表，实际应核对 **46 行**（S 19 + R 18 + UQ 9），已按 46 行重新逐行核对并全部一致；③ §7.2 S 源定位表中 `S5a` / `S5c` / `S5d` 三条摘录用的是 `/` 连接与 ASCII `...` 省略，与其余 16 条统一使用的 `……` 省略法不一致，已改写为 `……`——改写后 **19 条摘录全部可由脚本按「行范围」机械还原为 `source.md` 的原文**。
>
> 该订正不新增、不删除任何证据码（S/R/UQ 数量与内容均未变动），仅使记录数字与终稿一致。

> **07 节自身的校验和**：本节写入了推广记录，因此其内容在最后一次复制后即为最终态；其 SHA-256 由推广脚本在复制完成后现场计算并与暂存副本比对（结果见脚本输出）。

#### 推广授权记录（post-audit approval）

| 项 | 值 |
|---|---|
| **目标目录（规范化绝对路径）** | `/Users/Admin/Desktop/vllm-play/course`（新建；推广前不存在，无同名文件被覆盖） |
| **文件名白名单（7 个）** | `01-positioning-and-background.md` · `02-core-concepts.md` · `03-core-functionality.md` · `04-usage.md` · `05-related-tools.md` · `06-learning-path.md` · `07-verification-record.md` |
| **操作类型** | `01`–`06` 为 **create**（无内容变更）；`07-verification-record.md` 为 **replace**（终稿订正链接计数后重新推广）。无 delete、无 rename |
| **源文件** | `/Users/Admin/Desktop/vllm-play/source.md` — SHA-256 `6b1fd6c3…2a8365` — **mode: read-only** |
| **清单** | `MANIFEST.json`（与 7 个暂存文件同目录），记录每个暂存文件的 SHA-256 与 `op` |
| **禁区** | `source.md`、`.git`、暂存目录之外的任何路径 |
| **授权失效条件** | 暂存内容一旦变更，本次授权即失效，须重新核验后再推广 |

> **校验与自引用**：清单按内容重新生成；由于清单记录 07 节自身的校验和、而 07 节又要写入授权记录，二者不能互嵌哈希。因此**推广前的实际闸门是逐文件校验**：复制后立即比对目标文件与暂存文件的 SHA-256 必须逐个相等，源文件校验和必须保持 `6b1fd6c3…2a8365`。清单自身的 SHA-256 在该步骤现场计算并核验。

> **关于 `MANIFEST.json` 的校验和**：它按内容重新生成，并记录每个暂存文件的 SHA-256。由于它包含 07 节自身的校验和，而 07 节又要写入推广结果，**把清单校验和写回 07 会形成自引用**。因此清单的 SHA-256 在推广时**现场计算并核验**，而不是嵌在本文件中；本表中的其余数值均为可直接复核的稳定量。

---

## 7.6 如何复核本课程

1. **核对源未被改动**：`shasum -a 256 /Users/Admin/Desktop/vllm-play/source.md` 应得到 `6b1fd6c39c5f018b22097ef3f0553bc880329a00dc6742be0a3805ecad2a8365`。
2. **抽查任意一条事实**：取课程中任一 `【Source-derived · Sxx】`，到 [7.2](#s-locators) 查行号与摘录，回到 `source.md` 对应行核对。
3. **抽查任意一条研究引用**：取任一 `【Research-derived · Rxx】`，到 [7.3](#r-locators) 取 URL 与原文摘录，打开页面确认该句仍在。
4. **检查未验证部分**：到 [7.4](#unresolved-questions) 确认课程在哪些地方保持了克制。
5. **复现构建**：按 [7.5.1](#promotion-gate) 的七步重跑，校验每步的产物。

---

## 本节小结

- 源文件 `source.md`（SHA-256 `6b1fd6c3…2a8365`）**全程只读**，构建前后校验一致。
- **19 条**源定位（S）与 **18 条**研究记录（R）构成完整证据链，每条含可复核的定位信息。
- **9 条**证据缺口保留为未决问题（UQ1–UQ9），未由构建方擅自裁定。
- **7 次**逐节 review-only 审计，共记录 **1 Critical / 13 High / 31 Medium / 23 Low** 条发现，**全部已修并回写暂存区**。
- 交叉引用完整性经**脚本双向核验**：S / R / UQ 三类代码**零悬空指针、零死证据**；三张表的 **46 行**「影响的课程章节」列（S 19 + R 18 + UQ 9）与实际引用**逐行一致**。
