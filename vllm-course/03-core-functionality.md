# 03 · 核心功能：能力与边界

> **学习目标**
> 完成本节后，你应该能够：
> 1. 说清 vLLM 的三种入口形态（服务器 / 离线 `LLM` 类 / 引擎参数）各自的输入与输出；
> 2. 列出 vLLM 明确**不具备**的能力，并解释每一条的成因；
> 3. 理解 Prefill 与 Decode 两个阶段，以及它们为什么会成为部署架构的分水岭；
> 4. 查到关键引擎参数的默认值，并判断改动它们会换来什么、失去什么。

### 证据标签约定

`【Source-derived · Sxx】` 来自根文档 `source.md`；`【Research-derived · Rxx】` 来自外部权威来源；`【Illustrative】` 为教学性构造，不主张 vLLM 的未经验证行为。完整定位码与出处见 [07 · 验证记录](07-verification-record.md)。

> **表格内简写约定**：下表单元格中的 `【Sxx】` 是 `【Source-derived · Sxx】` 的简写，`【Rxx】` 是 `【Research-derived · Rxx】` 的简写。

---

<a id="capabilities"></a>

## 3.1 三种入口形态

vLLM 对外暴露的东西可以归成三类。源文档覆盖了前两类，第三类（引擎参数）是本次研究补齐的。

| 形态 | 输入 | 输出 | 适用 | 定位 |
|---|---|---|---|---|
| **服务器** `vllm serve <model>` | HTTP 请求（OpenAI 格式） | HTTP 响应（OpenAI 格式） | 在线服务、多客户端 | 【Source-derived · S5b】；客户端调用形态见【S5c】 |
| **离线批处理** `LLM` 类 | Python 里的 prompt 列表 | 输出对象列表 | 离线批量推理、评测 | 【Source-derived · S5d】 |
| **引擎参数** | CLI flag / 配置 | 决定前两者的运行时行为 | 调优、资源约束 | 【Research-derived · R8】 |

### 服务器形态

源文档描述得直接：指定 Hugging Face 上的模型 ID，即可启动 API 服务器；这条命令会下载模型（如果本地没有）并在 `8000` 端口启动一个兼容 OpenAI `/v1/chat/completions` 等接口的服务【Source-derived · S5b】。

官方 quickstart 给出的形态一致，并补充了几个细节【Research-derived · R3】：

- 默认监听 `http://localhost:8000`，可用 `--host` / `--port` 改；
- 模型默认从 Hugging Face 下载（"By default, vLLM downloads models from Hugging Face."）；
- 可用 `curl http://localhost:8000/v1/models` 列出已托管的模型；
- 鉴权用 `--api-key` 或环境变量 `VLLM_API_KEY`，可给多个 key，任一匹配即放行。

### 离线形态

源文档：如果只想在 Python 脚本中进行**离线批量推理**，可以直接使用 `LLM` 类，无需启动服务器【Source-derived · S5d】。

官方 quickstart 补充了两个容易踩的坑【Research-derived · R3】：

- `llm.generate` **不会自动套用模型的 chat template**——直接喂聊天格式的多轮消息会得到错误结果。要么手动套模板，要么改用 `llm.chat(messages_list, sampling_params)`；
- 想让 vLLM 用自己的生成默认值、而不是模型仓库里的 `generation_config`，用 `generation_config="vllm"`（离线）或 `--generation-config vllm`（服务器）。

---

## 3.2 能力清单：vLLM 到底能做什么

| 能力 | 说明 | 证据 |
|---|---|---|
| OpenAI 兼容 API | 迁移成本极低，只需更改 Base URL | 【S4d】 |
| 连续批处理 | 每步重组批，请求完成即腾位 | 【S2b / S3b】 |
| 分页注意力 | 固定块管理 KV Cache，消除碎片 | 【S3a】 |
| 前缀缓存 | 复用共享前缀；V1 默认开启 | 【S2b / S4c】+【R6】 |
| 离线批推理 | `LLM` 类，无需起服务 | 【S5d】 |
| `llm.chat` 接口 | 正确处理聊天模板 | 【R3】 |
| 显存预算控制 | `--gpu-memory-utilization` 默认 0.92 | 【R8】 |
| 数值精度自动选择 | `--dtype auto`（默认按模型配置） | 【R8】 |
| 上下文长度自动推导 | `--max-model-len` 未指定时由模型配置推导 | 【R8】 |

---

<a id="capability-boundary"></a>

## 3.3 边界清单：vLLM 明确不做什么

这一节是全课程最实用的一节。源文档在"使用场景"里给出了四条明确的否定【Source-derived · S4e / S4f / S4g / S4h】，研究补齐了平台与上下文两条。

| 不适合 | 根因 | 证据 |
|---|---|---|
| **训练或微调** | "vLLM **仅专注于推理**，不包含任何训练功能" | 【S4h】 |
| **多框架统一编排**（ONNX / TensorRT / PyTorch 混排流水线） | vLLM 更专注于 **Transformer 类 LLM** 的高效服务 | 【S4f】 |
| **70B+ 多节点 Prefill/Decode 分离式部署** | 该前沿领域成熟度不及专门方案 | 【S4g】 |
| **冷启动延迟敏感 + 流量极低 + 需快速扩缩容** | 设计目标是吞吐而非极致最小延迟 | 【S4e】 |
| **在非 Linux 平台上运行推理** | "vLLM can fully run only on Linux"（macOS 只能做开发；Windows 不在官方支持平台内） | 【R2】 |
| **超出模型原生上下文的超长输入** | 上下文长度由模型配置决定（如 Llama-2 为 4k） | 【R8 / R14】 |

> **关于"不适合"的常见误解**：源文档说 vLLM 在分离式推理上"成熟度可能不如其核心的单机/单副本场景"【S4g】——这是**成熟度**判断，不是"不能做"。研究也证实了这一点：NVIDIA Dynamo 官方文档明确列出它支持 **SGLang、TensorRT-LLM 和 vLLM** 作为推理后端【Research-derived · R11】。也就是说，**vLLM 可以被放进 Dynamo 的分离式架构里当后端**，只是不是那个架构的原生主角。
>
> 源文档没有给出这一层关系【证据缺口 · UQ5】，是本次研究补齐的。

---

## 3.4 Prefill 与 Decode：部署架构的分水岭

源文档在讨论超大规模部署时提到了这两个阶段，但没有解释它们是什么【Source-derived · S4g】。这一节补上。

一次推理请求天然分成两段：

| 阶段 | 做什么 | 资源瓶颈 | 缩放压力 |
|---|---|---|---|
| **Prefill**（预填充） | 处理整个输入提示词，产出初始 KV Cache【R11】 | **算力**密集（compute-bound）【R17】 | 输入长度、提示词复用、上下文大小【R11】 |
| **Decode**（解码） | 用 KV Cache 逐 token 生成输出【R11】 | **显存带宽**密集（memory-bound），每步需读取**该请求自身**已有的全部 KV Cache【R17】 | 并发数、输出长度、活跃 KV 显存【R11】 |

"做什么"与"缩放压力"两列来自 NVIDIA Dynamo 的官方文档【Research-derived · R11】；"资源瓶颈"一列来自 vLLM 官方调优文档【Research-derived · R17】——两者指向同一结论：Prefill 与 Decode 的资源画像相反。

**为什么这是分水岭**：在**聚合部署**（同一个 worker 既做 prefill 又做 decode）里，一个长提示词的 prefill 会阻塞同批次的 decode 步。而**分离式部署**把两者拆成独立的 worker 池，各自独立扩缩容与选型【Research-derived · R11】。

> **回到 vLLM 的位置**：vLLM 的连续批处理是**聚合式**的调度——prefill 和 decode 共享同一个批。vLLM 用**分块 prefill（chunked prefill）**缓解长提示词的阻塞：官方文档写明 "In V1, chunked prefill is enabled by default whenever possible."，且启用后"the scheduling policy prioritizes decode requests"——它把大 prefill 切成小块，与 decode 请求放进同一批，从而"better balancing compute-bound (prefill) and memory-bound (decode) operations"【Research-derived · R17】。但分块 prefill **不是分离式架构**：两个阶段仍在同一个 worker、同一块 GPU 上。
>
> 所以源文档的判断是准确的【S4g】：vLLM 在**单机/单副本**场景是主角；在**多节点分离式**场景，最自然的是把 vLLM 放在 Dynamo 或 llm-d 这类编排框架的后面当执行后端。

---

<a id="engine-defaults"></a>

## 3.5 关键引擎参数默认值

这些是调优时最先要知道的数字，来自官方引擎参数文档【Research-derived · R8】（块大小来自缓存配置【R7】）。

| 参数 | 默认值 | 含义 | 改动的后果 |
|---|---|---|---|
| `--gpu-memory-utilization` | `0.92` | 允许 vLLM 使用的显存比例 | 调高 → 更大 KV Cache → 更高并发；调低 → 给同机其他进程留空间。**多进程共卡时的关键旋钮** |
| `--dtype` | `auto` | 按模型配置自动选精度 | 手动改低可省显存但影响质量 |
| `--max-model-len` | 未指定时**由模型配置自动推导** | 最大上下文长度 | 调大 → 每个请求预留的 KV Cache 上限变高 → 并发下降 |
| `--block-size` | `16`（token） | KV Cache 连续块大小 | 块越大 → 末块浪费越少但粒度越粗；块越小 → 浪费越少但管理开销越高 |
| `--enable-prefix-caching` / `--no-enable-prefix-caching` | V1 默认**开启**（对支持的模型）【R6 / R16】 | 前缀缓存开关 | 关闭可用 `--no-enable-prefix-caching` 显式关闭。**注意官方文档对该默认值表述不一致，见【证据缺口 · UQ2】** |
| `--host` / `--port` | `localhost` / `8000` | 监听地址 | 【R3】 |
| `--api-key` / `VLLM_API_KEY` | 无（不鉴权） | API 鉴权 | **默认不鉴权**，生产环境必须显式配置【R3】 |

> **`--max-model-len` 的连带效应值得单独记住**：它不是一个"我能塞多长"的上限那么简单。它同时决定了**每个请求为 KV Cache 预留的空间上界**【Research-derived · R8】。
>
> ⚠️ **本节的推断（非官方文档表述）**：若假设 KV Cache 是唯一瓶颈、且忽略碎片与调度开销，那么把上限从 4096 提到 32768（约 8 倍）**大约**会让并发请求数掉到 1/8。这个线性外推用于建立直觉，**具体比例必须以你机器上的实测为准**【Illustrative · 线性外推】。

---

## 3.6 具体例子

### 例子 1 · 决策表：什么场景该选 vLLM（Source-derived）

源文档的四条正面场景与四条否定场景可以直接翻译成一张选型表【Source-derived · S4a / S4b / S4c / S4d / S4e / S4f / S4g / S4h】：

| 你的情况 | 选 vLLM？ | 理由 | 更合适的替代 |
|---|---|---|---|
| 面向大量终端用户的聊天产品 | ✅ | 高并发多租户正是它的主场【S4a】 | — |
| 夜间跑一批文档摘要任务 | ✅ | 总完成时间优先于单任务延迟【S4b】 | — |
| RAG / 长文档问答 | ✅ | 前缀缓存可复用重复的文档上下文【S4c】 | — |
| 已有代码调用 OpenAI SDK | ✅ | 改 Base URL 即可【S4d】 | — |
| 内部低频工具，等一秒就要结果 | ❌ | 吞吐优先牺牲了单请求延迟【S4e】 | Serverless 路线（如 KServe）【S4e】 |
| 服务里要混跑 ONNX 与 TensorRT 模型 | ❌ | 专注 Transformer 类 LLM【S4f】 | NVIDIA Triton【S4f】 |
| 70B+ 模型跨节点分离 Prefill/Decode | ⚠️ | 成熟度不如专用方案【S4g】 | NVIDIA Dynamo / llm-d【S4g + R11】 |
| 想微调模型 | ❌ | 只做推理，无训练功能【S4h】 | PyTorch / DeepSpeed【S4h】 |

<a id="example-2"></a>

### 例子 2 · 一个会直接卡住你的参数（Research-derived）

> 场景：你想用 `meta-llama/Llama-2-7b-hf` 跑一段 6000 token 的长文档。

**先看模型本身**：Llama-2 7B 的内容长度上限是 **4k**【Research-derived · R14】。而 `--max-model-len` 未指定时**由模型配置自动推导**【Research-derived · R8】。

所以你的 6000 token 输入**根本进不去**——这与 vLLM 配得对不对无关，是模型本身的能力边界。

**再看第二道门**：这个模型是 **gated** 的。官方模型页写明 "You need to share contact information with Meta to access this model."，并且需要先在 Meta 官网接受 Llama 2 Community License 才能申请访问【Research-derived · R14】。

**第三道门（如果你硬要调大）**：即使你换成一个支持长上下文的模型，把 `--max-model-len` 从 4096 调到 8192，KV Cache 的预留上界也随之翻倍，**并发能力大约减半**【Illustrative · 线性外推，同 [3.5](#engine-defaults) 的假设】。

> **三个结论**：
> 1. **上下文长度是模型属性，不是 vLLM 属性**——先查模型的 context length，再谈 vLLM 的配置；
> 2. **gated 模型需要账号 + 许可 + token**，新手最容易在这里卡住（见 [04 · 使用方法](04-usage.md#common-blockers)）；
> 3. **加大 `--max-model-len` 是有并发代价的**，不是免费的。

### 例子 3 · 输入输出对照（Illustrative）

> **教学性构造，不主张 vLLM 的未经验证行为。**

| 你给出的 | 你得到的 | 说明 |
|---|---|---|
| `vllm serve <model-id>` | 一个常驻的 HTTP 服务 | 进程不退出，直到被停止 |
| 一个 prompt 字符串 | 一段生成的文本 | 单次生成 |
| 一个 prompt **列表** | **同样长度的输出列表**（顺序对应） | 离线批量的核心特性 |
| `SamplingParams(temperature=0.8)` | 采样行为的配置 | 每次 `generate` / `chat` 调用可各配各的 |
| 一个 chat messages 列表（用 `llm.chat`） | 正确套用了模板的生成结果 | 用 `llm.generate` 则不会套模板【R3】 |
| `messages=[{"role":"user","content":"你好！"}]`（走 HTTP） | OpenAI 格式的响应 | 客户端只需改 `base_url`【S4d】 |

---

## 本节小结

- 三种入口：**服务器 / 离线 `LLM` 类 / 引擎参数**【S5b / S5d / R8】。
- 能力：OpenAI 兼容、连续批处理、分页注意力、前缀缓存（V1 默认开）【S2b / S4c / S4d + R6】。
- 边界：**不训练**【S4h】、**不混跑多框架**【S4f】、**不是分离式部署的原生主角**【S4g】、**只在 Linux 完整运行**【R2】。
- Prefill 算力密集 / Decode 带宽密集——这是分离式架构存在的理由，也是 vLLM 的边界所在【S4g + R11】。
- 调参第一课：`--gpu-memory-utilization`（0.92）与 `--max-model-len`（由模型推导）是一对牵制关系【R8】。

**下一步** → [04 · 使用方法](04-usage.md)
