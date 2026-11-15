# 06 · 学习路径

> **学习目标**
> 完成本节后，你应该能够：
> 1. 判断自己是否具备开始学习的前置条件；
> 2. 按顺序走完七个阶段（阶段 0–6），每个阶段都有**可观察的完成判据**；
> 3. 针对自己的真实场景，选出下一步该深入的方向。

### 证据标签约定

`【Source-derived · Sxx】` 来自根文档 `source.md`；`【Research-derived · Rxx】` 来自外部权威来源；`【Illustrative】` 为教学性构造，不主张 vLLM 的未经验证行为。完整定位码与出处见 [07 · 验证记录](07-verification-record.md)。

---

## 6.1 前置知识清单

进入学习路径前，先自检。**不满足"必备"项就先补，别硬上**——vLLM 的很多困惑其实是前置知识的缺口。

### 必备（缺了会卡在第 4 阶段）

| 需要 | 为什么 | 自检问题 |
|---|---|---|
| **Linux + NVIDIA GPU 环境** | vLLM 只在 Linux 上完整运行【R2】 | 你能 SSH 到一台有 GPU 的 Linux 机器吗？`nvidia-smi` 有输出吗？ |
| **Python 与虚拟环境** | 安装与调用都用 Python【R1 / R3】 | 你能用 `uv` 或 `venv` 建隔离环境吗？ |
| **Hugging Face 账号** | 模型默认从 HF 下载【R3】；Llama-2 还要额外授权【R14】 | 你注册了 HF 账号吗？ |
| **HTTP / OpenAI API 基础** | vLLM 的价值之一就是 API 兼容【S4d】 | 你用过 `curl` 打 JSON 接口吗？ |

### 强烈建议（缺了会卡在第 5 阶段）

| 需要 | 为什么 |
|---|---|
| **Transformer 与自注意力机制** | 理解 KV Cache 为什么占显存【S3a】、prefill/decode 为什么特性相反【R17】 |
| **显存与并发的基本直觉** | 理解"碎片消除 → 并发上升 → 吞吐上升"这条因果链【S2a / S2c】 |
| **批处理与调度的概念** | 理解"推理步"粒度的组批【S3b】 |
| **GPU 监控**（`nvidia-smi` / DCGM） | 做性能判断时你需要读数据，而不是感觉 |

### 可选

| 需要 | 用于 |
|---|---|
| Kubernetes | 理解 KServe / llm-d 这一层【R9】 |
| 分布式训练背景 | 理解训练与服务分层的边界【S4h】 |

> **没有 GPU 也能学完阶段 0–2 的概念部分**。[01](01-positioning-and-background.md)、[02](02-core-concepts.md)、[03](03-core-functionality.md) 全部是概念性的；[05](05-related-tools.md) 的选型部分同样不需要动手。只有 [04](04-usage.md) 需要真实环境。（阶段 0 的环境自检本身需要 GPU 机器，但可以在阶段 4 之前补做。）

---

## 6.2 七阶段学习路径

每个阶段都遵循同一个结构：**读 → 练 → 判据**。"判据"必须是**可观察的**（能跑出一条命令、能说出一句话、能做出一个决定），不是"理解了"。

---

### 阶段 0 · 确认环境（前置）

**读** → [04 · 4.0 先确认你的平台](04-usage.md#platform-check) + [4.1 安装](04-usage.md)

**练**

```bash
# 在目标机器上执行
nvidia-smi
python --version
```

**完成判据**
- [ ] `nvidia-smi` 列出了你的 GPU 且显存可用
- [ ] `python --version` 在 `>=3.11, <3.15` 区间内【R1】
- [ ] 你能明确回答："这台机器是不是 Linux？"（**如果不是，本课程的第 4 阶段需要换环境或改走 vLLM-Metal**【R2 / R3】）

---

### 阶段 1 · 建立定位（为什么是它）

**读** → [01 · 定位与背景](01-positioning-and-background.md)

**练**（不写代码，纯口头/书面）
1. 用一句话回答："vLLM 用什么换了什么？"（目标：说出"用单请求延迟换整体吞吐"）
2. 说出传统推理框架的两个浪费源头。
3. 说出两个 vLLM 不适合的场景，并解释原因。

**完成判据**
- [ ] 你能不看资料说出："vLLM 的首要目标不是让单个请求跑得最快，而是让整个 GPU 在单位时间内服务尽可能多的用户"【S1】
- [ ] 你能解释"包场领班"和"拼桌高手"的差别，并指出差别落在**组批时机**和**显存分配方式**两处【S2a / S2b】
- [ ] 你至少能举出"冷启动延迟敏感"和"需要训练"两个不适合的场景【S4e / S4h】

---

### 阶段 2 · 吃透两个支柱（本课程的技术核心）

**读** → [02 · 核心概念](02-core-concepts.md)

**练**
1. 画出你自己版本的"块表"：一个 40 token 的请求，逻辑块 0/1/2 分别映射到哪些物理块。
2. 算一笔账：末块浪费了多少？如果负载里全是 40 token 的请求，浪费率是多少？（对照官方博客给出的 "under 4%"【R5】，解释为什么会有差距）
3. 回答：如果只上连续批处理、不上分页注意力，会发生什么？反过来呢？

**完成判据**
- [ ] 你能说出块默认是 **16 token**【R7】，并解释末块浪费为什么是分页下**唯一**的浪费来源【R5】
- [ ] 你能说出"**分页负责腾得出空间，连续批处理负责空间不闲置**"这个双向依赖【S3b】
- [ ] 你能解释 <4% 是**系统级均值**，而不是单条请求的保证【R5】，并说明官方博客未给出其统计口径【证据缺口 · 见 07】
- [ ] 你能说出前缀缓存在 vLLM V1 中**默认开启**【R6】，并提及其信任组 / salt 隔离机制【R15】

---

### 阶段 3 · 划清能力边界

**读** → [03 · 核心功能](03-core-functionality.md)

**练**
1. 用 [3.3 的边界清单](03-core-functionality.md#capability-boundary) 对照你自己的项目，写下"能用"还是"不能用"，并给理由。
2. 查一个你打算用的模型的上下文长度和授权状态。

**完成判据**
- [ ] 你能说出 vLLM **只做推理**，训练要回 PyTorch / DeepSpeed【S4h】
- [ ] 你能说清 vLLM 与 Triton 的分工（LLM vs 多框架）【S4f / R10】
- [ ] 你能说清 prefill 与 decode 的资源画像差异（compute-bound vs memory-bound）【R17】，以及它为什么导致分离式架构的出现【R11】
- [ ] 你查到了目标模型的 context length 与是否 gated【R14】

---

### 阶段 4 · 动手跑通（第一次端到端）

**读** → [04 · 使用方法](04-usage.md)（重点看 [4.3 三个最常卡住的地方](04-usage.md#common-blockers)）

**练**（按顺序，别跳步）

```bash
# 1. 安装
uv venv myenv --python 3.12 --seed
source myenv/bin/activate
uv pip install vllm --torch-backend=auto

# 2. 启动（非 gated 模型，先打通链路）
vllm serve Qwen/Qwen2.5-1.5B-Instruct

# 3. 另开终端：验活
curl http://localhost:8000/v1/models

# 4. 发一个请求
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-1.5B-Instruct","prompt":"San Francisco is a","max_tokens":7,"temperature":0}'
```

然后用 Python SDK 再跑一遍（`base_url` 指到本地即可）【S5c / S4d】。

再跑一次**离线**批量推理（不需要服务器）：

```python
from vllm import LLM, SamplingParams

llm = LLM(model="Qwen/Qwen2.5-1.5B-Instruct")
outputs = llm.generate(
    ["Hello, my name is", "The capital of France is"],
    SamplingParams(temperature=0.8),
)
for out in outputs:
    print(repr(out.prompt), "->", repr(out.outputs[0].text))

# 聊天模型请改用 llm.chat(messages_list, sampling_params)，它会自动套用 chat template
```

**完成判据**
- [ ] `curl /v1/models` 返回了包含你模型 ID 的 JSON
- [ ] `/v1/completions` 返回了续写文本
- [ ] OpenAI SDK 调用成功，**只改了 `base_url`**【S4d】
- [ ] 离线 `LLM` 类跑通一次批量生成；如果你用的是聊天模型，你用的是 `llm.chat` 而不是 `llm.generate`【R3 / S5d】

> **如果你想直接用 Llama-2-7b**：先走完上面的非 gated 路径，再换模型。gated 授权是**独立问题**，混在一起排查会浪费时间【R14】。

---

### 阶段 5 · 选型与架构

**读** → [05 · 相关工具](05-related-tools.md)

**练**
1. 拿 [5.4 的决策链](05-related-tools.md#selection-chain) 跑一遍你的项目，逐层排除。
2. 画一张你自己的部署拓扑图（参考 [例子 2 · 一个真实世界的组装](05-related-tools.md#deployment-topology)）。
3. 列出你的三个候选方案，每个写一条"它解决什么、代价是什么"。

**完成判据**
- [ ] 你能说出 vLLM 在**引擎层**，而 llm-d / Dynamo / KServe 在它**上面**【R9 / R11】；以及源文档把 vLLM 定位为"最优先、最稳妥的默认选择"【S6】
- [ ] 你的决策链走到了唯一终点，没有停在"要不要换引擎"这一步
- [ ] 你能说出同层竞品是 SGLang，且 TGI 已进入 maintenance mode【R12 / R13】

---

### 阶段 6 · 调优与度量（进阶）

**读** → 回到 [03 · 3.5 关键引擎参数默认值](03-core-functionality.md#engine-defaults) + [04 · 例子 3](04-usage.md)

**练**
1. 记录基线：GPU 利用率、平均 TTFT、平均 ITL、吞吐（req/s）。
2. 一次只改一个参数（`--gpu-memory-utilization` / `--max-model-len` / `--block-size`），重测。
3. 如果你的负载有共享前缀（比如固定 system prompt），验证前缀缓存是否生效——重复请求同一 prompt，观察首 token 延迟是否下降。前缀缓存会让新请求**跳过共享部分的计算**【R15】；TTFT / ITL 是 vLLM 官方调优文档中用于衡量这两个阶段的指标【R17】。

**完成判据**
- [ ] 你有一份**改动前**的基线数据
- [ ] 你能说出你改了哪个参数、指标怎么变了、以及**为什么**会这样变
- [ ] 你能解释为什么调大 `--max-model-len` 会压低并发（KV Cache 预留上界随之上调）【R8 + 本节推断】
- [ ] 如果你做严格可复现评测，你已显式加上 `--no-enable-prefix-caching` 或记录了它的影响【R6 / R16】

> **纪律**：**一次只改一个变量**。同时改三个参数然后看指标变化，等于什么都没学到。

---

## 6.3 练习清单（可勾选）

### 必做

- [ ] 判断自己的平台是否满足"Linux + GPU"【R2】
- [ ] 安装 vLLM 并打印版本号
- [ ] 启动一个服务器并用 `curl /v1/models` 验活
- [ ] 用 OpenAI SDK 调用成功（只改 `base_url`）【S4d】
- [ ] 用 `LLM` 类跑一次离线批量生成【S5d】
- [ ] 用自己的话解释"分页 + 连续批处理"的耦合关系【S3b】
- [ ] 对照 [3.3 边界清单](03-core-functionality.md#capabilities) 判断自己的项目适不适合 vLLM

### 选做

- [ ] 手算一个 40 token 请求的块分配与末块浪费
- [ ] 查自己目标模型的 context length、授权状态、推荐精度
- [ ] 画出自己的部署拓扑图
- [ ] 记录一组性能基线，并做一次单参数对比实验
- [ ] 验证前缀缓存在你的共享前缀负载上是否生效

---

## 6.4 完成之后：往哪走

| 你的下一步 | 去哪学 |
|---|---|
| 想读原始论文 | PagedAttention 论文（SOSP '23）【R4】——本课程 [02 节](02-core-concepts.md) 的每个机制在论文里都有对应章节 |
| 想上生产 | [05 节](05-related-tools.md) 的编排层 + [04 节](04-usage.md) 的鉴权与可复现性注意事项 |
| 想做多模型 / 弹性 | KServe 的 Serverless 安装方式（scale-to-zero 依赖它）【R9】 |
| 想做超大规模 | Dynamo 的分离式部署文档【R11】 + llm-d【R9】 |
| 想深入调度 | vLLM V1 架构博客（前缀缓存的设计动机与默认开启的由来）【R6】；vLLM 官方调优文档（分块 prefill、TTFT / ITL 与调度策略）【R17】；连续批处理的机制见 [02 节](02-core-concepts.md)【S3b】 |

---

## 本节小结

- **前置**：一台 Linux + GPU 的机器 + HF 账号，是硬门槛；前 3 阶段不需要 GPU【R2】。
- **路径**：环境 → 定位 → 支柱 → 边界 → 动手 → 选型 → 调优（阶段 0–6，共七阶段），每阶段一个**可观察的判据**。
- **纪律**：调优阶段**一次只改一个参数**；动手阶段**先打通非 gated 链路再换生产模型**。
- **每阶段都指向可验证的产出**：一条命令的输出、一句能复述的定义、一个能做出的选型决定。

**回到起点** → [01 · 定位与背景](01-positioning-and-background.md) ｜ **查证据** → [07 · 验证记录](07-verification-record.md)
