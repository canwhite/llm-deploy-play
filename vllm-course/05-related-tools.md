# 05 · 相关工具：vLLM 在工具链里的位置

> **学习目标**
> 完成本节后，你应该能够：
> 1. 把 vLLM 放到正确的**层次**上——它是引擎，不是平台、不是编排器、不是训练框架；
> 2. 对每个相关工具说清它的**目的**、与 vLLM 的**重叠**、以及**关键差异**；
> 3. 面对一个具体需求，用一条**选型规则**决定该用哪一层。

### 证据标签约定

`【Source-derived · Sxx】` 来自根文档 `source.md`；`【Research-derived · Rxx】` 来自外部权威来源；`【Illustrative】` 为教学性构造，不主张 vLLM 的未经验证行为。完整定位码与出处见 [07 · 验证记录](07-verification-record.md)。

---

## 5.1 先分层：它们根本不在同一层

源文档提到的工具看起来像一组竞品，实际上**分属不同层次**。把层次理清，选型就变成一道填空题而不是一道纠结题。

> **说明**：下面这张层次图是**本课程自建的分类框架**【Illustrative】，不是任何一方文档的原文表述。各工具自身的定位均来自其官方文档（见各小节引用的 R 码）。

```
┌─ 平台层 ────────────────────────────────────────────────┐
│  KServe（K8s 上的推理平台：自动扩缩、灰度、scale-to-zero） │
├─ 编排 / 路由层 ─────────────────────────────────────────┤
│  llm-d（KV 感知调度、分离式 prefill/decode）              │
│  NVIDIA Dynamo（数据中心级分布式推理编排）                │
├─ 引擎层 ─────────────────────────────────────────────────┤
│  ★ vLLM        —— 本课程的主角                            │
│    SGLang      —— 同层邻居，定位高度相似                   │
│    TGI         —— 同层邻居，已进入 maintenance mode       │
│  NVIDIA Triton —— 多框架通用服务器（可跑非 LLM）           │
├─ 训练层 ─────────────────────────────────────────────────┤
│  PyTorch / DeepSpeed —— 训练与微调，vLLM 完全不覆盖        │
└──────────────────────────────────────────────────────────┘
```

**最关键的一句话**：vLLM 是**引擎层**的工具。编排层的东西（llm-d、Dynamo、KServe）**通常把 vLLM 当作后端来调用**，而不是取代它。

---

## 5.2 逐个工具

### KServe —— K8s 上的推理平台（源文档的"冷启动延迟"替代方案）

| | |
|---|---|
| **目的** | "Standardized Distributed Generative and Predictive AI Inference Platform for Scalable, Multi-Framework Deployment on Kubernetes"【R9】 |
| **与 vLLM 的重叠** | 都能提供 OpenAI 兼容的推理服务【R9】 |
| **关键差异** | KServe 管的是**部署拓扑与生命周期**（自动扩缩、灰度发布、scale-to-zero）【R9】；vLLM 管的是**单个进程内的调度与显存效率**【S3a / S3b】 |
| **源文档的定位** | 适合"冷启动延迟极度敏感、流量极低、需快速扩缩容"的场景【S4e】 |

**细节要点（研究补齐）**：

- KServe 的官方仓库列出 "Optimized Backends: Support for vLLM and llm-d for optimized performance for serving LLMs"【R9】——**vLLM 是它的优化后端之一**。
- vLLM 官方文档也确认了这条集成路径："vLLM can be deployed with KServe on Kubernetes for highly scalable distributed model serving."，并给出两条路：走 KServe 的 Hugging Face serving runtime，或走基于 llm-d 的 `LLMInferenceService`【R9】。
- ⚠️ **一个容易踩的坑**：KServe 的 **scale-to-zero 依赖 Serverless（Knative）安装方式**。官方仓库明确说明 Standard 安装方式"does not support canary deployment and request based autoscaling with scale-to-zero"【R9】。想用 scale-to-zero 省成本，就必须装 Serverless 那一套。

### NVIDIA Triton —— 多框架通用推理服务器

| | |
|---|---|
| **目的** | "an open source inference serving software that streamlines AI inferencing"，"enables teams to deploy any AI model from multiple deep learning and machine learning frameworks"【R10】 |
| **与 vLLM 的重叠** | 都能做 GPU 上的高性能推理【R10】 |
| **关键差异** | Triton 的后端包括 "TensorRT, PyTorch, ONNX, OpenVINO, Python, RAPIDS FIL, and more"【R10】；vLLM 则**专注 Transformer 类 LLM** 的高效服务【S4f】 |
| **源文档的定位** | 适合"需要 ONNX / TensorRT / PyTorch 多框架统一编排的复杂流水线"【S4f】 |

> **一句话区分**【Illustrative · 教学启发式】：**模型是 LLM 吗？** 是 → vLLM；不是（传统 CV、推荐、任意 ONNX 模型）→ Triton。混合流水线 → Triton。依据见【S4f】与【R10】。

### NVIDIA Dynamo —— 数据中心级分布式推理编排

| | |
|---|---|
| **目的** | 分布式推理服务框架，"separates the two phases of LLM inference into their own worker pools so you can scale, size, and place them independently"【R11】 |
| **与 vLLM 的重叠** | 都服务于大模型高吞吐推理【R11】 |
| **关键差异** | Dynamo 是**编排层**，vLLM 是**执行后端**。官方文档明确列出 Dynamo 支持 "SGLang, NVIDIA TensorRT™ LLM, and vLLM" 作为推理引擎【R11】 |
| **源文档的定位** | 适合"超大规模（70B+）的多节点分离式推理"【S4g】 |

**细节要点**：

- Dynamo 的核心是**分离式部署**：prefill 池与 decode 池独立，路由请求先过 prefill，再把 KV Cache 传给 decode worker 继续流式输出【R11】。原理见 [03 节 3.4](03-core-functionality.md#capabilities)。
- **对 vLLM 用户的实际含义**：源文档说 vLLM 在这个方向"成熟度可能不如"【S4g】——研究证实了这一点，但也补上了另一半：**vLLM 可以作为 Dynamo 的后端被使用**【R11】。所以不是二选一，而是"Dynamo 编排 + vLLM 执行"。

### llm-d —— 面向 LLM 的 Kubernetes 原生编排

| | |
|---|---|
| **目的** | 生产级 LLM 服务架构框架，KServe 的 `LLMInferenceService` CRD 建立在它之上【R9】 |
| **与 vLLM 的重叠** | 都提供高吞吐 LLM 服务【R9】 |
| **关键差异** | llm-d 在 K8s 之上提供 **KV-cache 感知调度**、**分离式 prefill/decode**、**分布式推理**【R9】 |
| **源文档的定位** | 源文档未提及【证据缺口 · UQ9】，研究补齐 |

> **llm-d 与 vLLM 的关系不是竞争，是叠加**：官方描述是 llm-d "combining vLLM's inference engine with Kubernetes orchestration and intelligent routing capabilities"【R9】——**vLLM 是引擎，llm-d 是它上面那层调度与路由**。

### SGLang —— 同层的直接邻居

| | |
|---|---|
| **目的** | "High-performance serving framework for large language and multimodal models"，"an inference framework meant for production level serving"【R12】 |
| **与 vLLM 的重叠** | **高度重叠**——SGLang 侧：做高吞吐 LLM 服务、有前缀缓存、OpenAI API 兼容【R12】；vLLM 侧：连续批处理【S2b / S3b】、前缀缓存【S4c】、OpenAI API 兼容【S4d】 |
| **关键差异** | SGLang 的标志性机制是 **RadixAttention**【R12】；SGLang 官方报告 "powering 400k+ GPUs"【R12】。（两种前缀复用机制的具体差异不在本课程已记录的证据范围内，故不作断言） |
| **源文档的定位** | 源文档未提及【证据缺口 · UQ9】 |

> **选 vLLM 还是 SGLang？** 两者是真正的**同层竞品**，也是最难选的一对。可用的区分维度：
> 1. **多模态**：SGLang 自我定位含 "large language and **multimodal** models"【R12】；
> 2. **既有生态**：TGI 的官方文档点名 **vllm 与 SGLang** 为其架构思路的下游引擎【R13】——两者在社区里是同一阵营；
> 3. **编排层兼容性**：Dynamo 同时支持 SGLang、TensorRT-LLM 和 vLLM【R11】，所以这一点不构成区分。
>
> 剩下真正决定性的，是**你自己的模型 + 你的负载在你的硬件上的实测数据**。这一条无法从文档推出，本课程不给结论。

### Hugging Face TGI —— 同层，但已退役为主力

| | |
|---|---|
| **目的** | "Text Generation Inference (TGI) is a toolkit for deploying and serving Large Language Models (LLMs)"【R13】 |
| **与 vLLM 的重叠** | 早期是 vLLM 最主要的对比对象【R5】 |
| **关键差异** | **"text-generation-inference is now in maintenance mode"**【R13】——只接受 bug 修复、文档改进和轻量维护 |
| **源文档的定位** | 源文档未提及【证据缺口 · UQ9】，研究补齐 |

> **TGI 的一个反向证据很有意思**：它的官方文档主动把 **vllm** 和 **SGLang** 列为推荐的下游引擎，并说 TGI 推动的"依赖 `transformers` 模型架构"的做法"This approach is now adopted by downstream inference engines, which we contribute to and recommend using going forward"【R13】。也就是说，**连它的继任者都指向了 vLLM**。

### PyTorch / DeepSpeed —— 训练层，vLLM 完全不覆盖

源文档说得很干脆：**"vLLM 仅专注于推理，不包含任何训练功能。如果需要微调模型，你需要回到 PyTorch、DeepSpeed 等训练框架"**【Source-derived · S4h】。

| | |
|---|---|
| **与 vLLM 的重叠** | 无 |
| **差异** | 完全不同的阶段：训练产出权重，vLLM 消费权重 |
| **实践含义** | 微调流程是 `DeepSpeed/PyTorch 训练 → 导出权重 → vLLM 部署`。vLLM 出现在流水线的**最后一环** |

---

<a id="tool-comparison"></a>

## 5.3 工具对比表

| 工具 | 层次 | 核心目的 | 与 vLLM 的关系 | 何时选它 |
|---|---|---|---|---|
| **vLLM** | 引擎 | 高吞吐 LLM 推理 | —— | 默认起点【S6】 |
| **SGLang** | 引擎 | 高吞吐 LLM / 多模态推理 | 同层竞品 | 需要多模态【R12】；否则以你自己的实测为准【Illustrative · 建议】 |
| **TGI** | 引擎 | LLM 部署 | 同层，maintenance mode | 仅维护既有部署【R13】 |
| **Triton** | 引擎 | 多框架通用推理 | 邻层 | 服务对象不只有 LLM【S4f / R10】 |
| **llm-d** | 编排 | KV 感知调度、分离式部署 | vLLM 是其引擎 | K8s 上跑多模型集群【R9】 |
| **Dynamo** | 编排 | 数据中心级分布式推理 | vLLM 是其支持后端之一 | 70B+ 多节点分离式【S4g / R11】 |
| **KServe** | 平台 | K8s 推理平台、scale-to-zero | vLLM 是其优化后端 | 需自动扩缩、灰度、scale-to-zero【S4e / R9】 |
| **PyTorch / DeepSpeed** | 训练 | 训练与微调 | 流水线上下游 | 要微调模型【S4h】 |

---

<a id="selection-chain"></a>

## 5.4 选型规则

给一条可执行的决策链，按顺序问下去：

```
需要训练或微调模型吗？
  ├─ 是 → PyTorch / DeepSpeed（vLLM 不参与）           【S4h】
  └─ 否 ↓
要同时服务非 LLM 模型（ONNX / TensorRT 混排）吗？
  ├─ 是 → NVIDIA Triton                                【S4f / R10】
  └─ 否 ↓
是单模型 / 单副本 / 单机部署吗？
  ├─ 是 → vLLM（或 SGLang，按实测选）                  【S1 / R12】
  └─ 否 ↓
需要跨节点分离 Prefill / Decode，或 70B+ 多副本吗？
  ├─ 是 → 编排层：Dynamo 或 llm-d（vLLM 作后端）        【S4g / R9 / R11】
  └─ 否 ↓
需要 K8s 自动扩缩 / 灰度 / scale-to-zero 吗？
  ├─ 是 → KServe（Serverless 安装方式）                 【S4e / R9】
  └─ 否 → vLLM【S6】
```

> **规则的形状**：**先排除，后选择**。每一步排除的都是"层次不匹配"的情况——vLLM 解决不了训练问题，KServe 解决不了显存碎片问题，编排层解决不了引擎内的调度效率。**层次选错了，后面所有优化都是白费。**
>
> 其中"碎片由分页注意力在引擎内解决"依据【S3a】；"KServe 面向平台级弹性"依据【S4e / R9】。

---

## 5.5 具体例子

### 例子 1 · 源文档给出的四条替代建议（Source-derived）

源文档在"不适合"清单里顺带给出了四条替代方案【Source-derived · S4e / S4f / S4g / S4h】：

| 源文档的判断 | 源文档给的替代 | 层次关系 |
|---|---|---|
| 冷启动延迟敏感、流量极低、需快速扩缩容 | KServe 等 Serverless 方案【S4e】 | 平台层叠加在引擎之上 |
| 需 ONNX / TensorRT / PyTorch 多框架统一服务 | NVIDIA Triton【S4f】 | 同层但覆盖面更广 |
| 70B+ 多节点分离式推理 | NVIDIA Dynamo 等【S4g】 | 编排层，vLLM 可作后端 |
| 需要训练或微调 | PyTorch、DeepSpeed【S4h】 | 完全不同的阶段 |

> **注意这四条的结构**：没有一条是"另一个更快的推理引擎"。**源文档在否定 vLLM 的时候，指向的都是不同层次或不同阶段的工具**——这本身就是"vLLM 的边界由层次决定"的最好证明。研究补齐的是：Dynamo 与 llm-d 实际上**可以把 vLLM 包含进来**（【R9 / R11】），源文档没有点明这层协作关系【证据缺口 · UQ5】。

<a id="deployment-topology"></a>

### 例子 2 · 一个真实世界的组装（Research-derived）

> **教学性构造**，说明工具如何组合，**不主张任何未经验证的组合行为**。

一个多租户的 LLM API 平台，典型形态是：

```
        用户流量
           ↓
   ┌───────────────────┐
   │  KServe            │  平台层：自动扩缩、灰度、按需 scale-to-zero
   │  LLMInferenceService│  （Serverless 安装方式才有 scale-to-zero）【R9】
   └─────────┬─────────┘
             ↓
   ┌───────────────────┐
   │  llm-d             │  编排层：KV-cache 感知调度、分离式 prefill/decode【R9】
   └─────────┬─────────┘
             ↓
   ┌───────────────────┐
   │  ★ vLLM            │  引擎层：连续批处理 + 分页注意力【S1】
   │  多个副本, 每个一张 GPU│
   └─────────┬─────────┘
             ↓
   ┌───────────────────┐
   │  NVIDIA GPU        │
   └───────────────────┘
```

**读这张图的关键**：

1. **每一层只解决自己那一层的问题**。KServe 不会让单个 vLLM 进程更快，但它让"没人用的时候不花钱"成为可能；vLLM 不会帮你做灰度发布。
2. **vLLM 在最底下**——它是这个栈里唯一真正碰到 GPU 的组件。上层做得再好，如果 vLLM 的显存效率不行，整条链路的成本都上不去。
3. **训练不在图里**。要微调，就是另一条流水线：DeepSpeed/PyTorch 训练 → 权重 → 上面这张图【S4h】。

### 例子 3 · 为什么"换个引擎"往往不是答案（Illustrative）

> **教学性构造，不主张任何未经验证的行为。**

一个团队发现推理太慢，做了三件事：

**做法 A：换引擎。** 从 vLLM 换到 SGLang。→ 可能在某些负载上有提升（SGLang 与 vLLM 是同层竞品【R12】），但如果瓶颈其实是**层次不对**（比如多模型服务却用单模型部署方式，或每个副本都在重复加载同一份 800 token 的系统提示词），换引擎不会解决。

**做法 B：调参数。** 在同一个引擎上调 `--gpu-memory-utilization`、`--max-model-len`、批大小。→ 常常是**性价比最高的一步**，因为默认值（0.92 / 由模型推导 / 16 token 块）不一定适合你的负载【R7 / R8】。

**做法 C：先量再动。** 先量清楚三件事：**(1) GPU 实际利用率**（低 = 调度或负载问题）；**(2) TTFT 与 ITL 的分布**（区分是 prefill 慢还是 decode 慢）【R17】；**(3) 命中率**（前缀缓存有没有在起作用）【R6】。

> **推荐顺序是 C → B → A。** 先测量，再调参数，最后才考虑换引擎。换引擎是成本最高、收益最不确定的一步——它把"你可能有的配置问题"变成"你可能有的迁移问题"。
>
> 而**层次问题要用层次解决**：如果测出来是"多模型 + 需要弹性"，那正确答案是上 KServe【S4e / R9】，不是换引擎。

---

## 本节小结

- vLLM 是**引擎层**工具；llm-d / Dynamo / KServe 是它**上面**的编排与平台层，vLLM 通常是它们的后端【R9 / R11】。
- 源文档提到的替代方案没有一个是"更快的引擎"——**否定来自层次不匹配**【S4e / S4f / S4g / S4h】。
- 同层竞品：SGLang（定位相近、覆盖多模态）【R12】；TGI 已进入 maintenance mode 且官方推荐迁移到 vLLM / SGLang【R13】。
- 选型用**排除法**：训练 → 多框架 → 规模 → 平台，逐层排除，详见 [5.4](#selection-chain)。
- 实践顺序：**先测量 → 再调参 → 最后换引擎**。

**下一步** → [06 · 学习路径](06-learning-path.md)
