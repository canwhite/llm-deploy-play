# 04 · 使用方法：从零跑通一次推理

> **学习目标**
> 完成本节后，你应该能够：
> 1. 在一台合格的机器上完成 vLLM 安装，并判断自己的平台是否合格；
> 2. 用一条命令启动 OpenAI 兼容的服务器，并用 `curl` 和 OpenAI Python SDK 各验证一次；
> 3. 用离线 `LLM` 类跑一次批量推理，并正确处理 chat template；
> 4. 独立诊断最常见的三个卡点：gated 模型、鉴权没配、以及"装上了但跑不了"。

### 证据标签约定

`【Source-derived · Sxx】` 来自根文档 `source.md`；`【Research-derived · Rxx】` 来自外部权威来源；`【Illustrative】` 为教学性构造，不主张 vLLM 的未经验证行为。完整定位码与出处见 [07 · 验证记录](07-verification-record.md)。

---

<a id="platform-check"></a>

## 4.0 先确认你的平台（第一步，不是最后一步）

**这一步放在最前面，因为它决定后面所有命令是否有意义。**

官方安装文档写得很明确："vLLM can fully run only on Linux but for development purposes, you can still build it on other systems (for example, macOS) ... The binaries will not be compiled and won't work on non-Linux systems."【Research-derived · R2】

| 你的平台 | 能装吗 | 能跑推理吗 | 怎么办 |
|---|---|---|---|
| **Linux + NVIDIA GPU** | ✅ | ✅ | **推荐路径**，本节后续命令都按此写 |
| Linux + AMD GPU (ROCm) | ✅ | ✅ | 需 `--extra-index-url https://wheels.vllm.ai/rocm/`【R3】 |
| Linux + Intel XPU | ✅ | ✅ | XPU 后端【R3】 |
| **macOS (Apple Silicon)** | ⚠️ 只能开发/import | ❌ | 官方路径是 **vLLM-Metal**：改用 MLX 作为计算后端，模型取自 `mlx-community`【R3】；或改用 Linux 远程机 / 容器 |
| macOS (Intel) | ⚠️ | ❌ | 同上，或换 Linux |
| Windows | ❌ | ❌ | 不在官方支持的平台列表内（官方表述为 "can fully run only on Linux"）【R2】 |

> **典型误判**：在 macOS 上官方说明是"可以构建、可以 import，**但仅为开发目的**"——所以 `import vllm` 成功**不能**说明装好了。真正的问题会等到 `vllm serve` 时才暴露：官方文档明说了非 Linux 系统上"The binaries will not be compiled and won't work"【R2】。**判断标准是平台，不是 import 是否成功。**

---

## 4.1 安装

源文档给出的安装步骤【Source-derived · S5a】：

```bash
# 使用 uv (推荐)
uv venv myenv --python 3.12 --seed
source myenv/bin/activate
uv pip install vllm

# 或直接使用 pip
pip install vllm
```

这个流程是对的，但有两处需要按当前版本校准（源文档未标注版本【证据缺口 · UQ1】）：

**校准一：Python 版本范围。** vLLM 0.33.0 要求 Python `>=3.11, <3.15`【Research-derived · R1】。源文档用的 3.12 在范围内，安全。

**校准二：uv 的 torch 后端解析。** 当前官方 quickstart 推荐的形式是【Research-derived · R3】：

```bash
uv venv --python 3.12 --seed
source .venv/bin/activate
uv pip install vllm --torch-backend=auto
```

官方推荐在安装时带上 `--torch-backend=auto`，让 uv 自动选择 torch 后端【Research-derived · R3】。源文档里不带这个参数的 `uv pip install vllm` 在很多环境下仍能装上，但**官方推荐形式更可靠**——尤其是 CUDA 驱动版本不常见时。

> **验证安装是否成功**（Linux + GPU）：

```bash
python -c "import vllm; print(vllm.__version__)"
nvidia-smi   # 确认 GPU 可见
```

---

## 4.2 启动服务

源文档【Source-derived · S5b】：

```bash
vllm serve meta-llama/Llama-2-7b-hf --port 8000
```

官方 quickstart 的形态一致【Research-derived · R3】：

```bash
vllm serve Qwen/Qwen2.5-1.5B-Instruct
```

**共同点**：官方 quickstart 用的是**位置参数**形式（模型 ID 直接跟在 `serve` 后面），本节统一沿用该形式；默认监听 `http://localhost:8000`；模型默认从 Hugging Face 下载（本地没有就下载）【R3】。

> **`--port 8000` 是冗余的**——8000 本来就是默认值【R3】。保留它没有坏处，但要知道你也可以省略。

---

<a id="common-blockers"></a>

## 4.3 三个最常卡住的地方

### 卡点 1：gated 模型下不下来（最常见）

源文档用的 `meta-llama/Llama-2-7b-hf` 是一个 **gated** 模型。官方模型页写明："You need to share contact information with Meta to access this model."，并且要求先在 Meta 官网接受 Llama 2 Community License，才能在 Hugging Face 上申请访问【Research-derived · R14】。

**症状**：启动时卡在下载，或报 401 / 403。

**解法（三选一）**：

1. **换用非 gated 模型**——最省事。官方 quickstart 用的 `Qwen/Qwen2.5-1.5B-Instruct` 就不是 gated【R3】：
   ```bash
   vllm serve Qwen/Qwen2.5-1.5B-Instruct
   ```
2. **申请并配置 HF token**——先在 Hugging Face 上接受许可、拿到 access token，再把 token 通过环境变量传给 vLLM：
   ```bash
   export HF_TOKEN="hf_..."
   ```
   Hugging Face 官方文档建议用环境变量传递 token 以避免写进 shell 历史【Research-derived · R18】。

   > ⚠️ **token 只解决"你是谁"，不解决"你被授权了吗"**：账号必须**已被 Meta 授予该模型的访问权**，否则即使 token 有效也仍会被拒（403）【Research-derived · R14】。token 不是绕过授权的钥匙。
3. **用本地已下载的模型路径**——把位置参数换成磁盘上的目录，例如 `vllm serve /path/to/local/model`【Illustrative · 操作建议】。

> **注意 Llama-2 的上下文只有 4k**【Research-derived · R14】。用它做长文档实验会撞上长度上限——这是模型属性，不是 vLLM 的问题，详见 [03 节例子 2](03-core-functionality.md#example-2)。
>
> **本课程没有实跑过 gated 路径**【证据缺口 · UQ4】——构建环境无 Meta 授权，因此以上是依据官方模型页给出的操作指引，不是已验证的执行记录。

### 卡点 2：客户端传了 api_key，但服务端根本没鉴权

源文档的客户端示例【Source-derived · S5c】：

```python
client = OpenAI(base_url="http://localhost:8000/v1", api_key="token-abc123")
```

**这里有一个容易误读的点**：客户端传了 `api_key`，但**服务端启动时并没有加 `--api-key`**。官方文档说明鉴权要靠服务端的 `--api-key` flag 或 `VLLM_API_KEY` 环境变量，且未配置时**默认不鉴权**【Research-derived · R3】。

也就是说：

| 服务端 | 客户端 | 实际效果 |
|---|---|---|
| 不带 `--api-key` | 随便传什么 `api_key` | **不校验**——`"token-abc123"` 只是个占位符，不会被验证【R3】 |
| 带 `--api-key sk-xxx` | 传 `sk-xxx` | 校验通过【R3】 |
| 带 `--api-key sk-xxx` | 传别的 | 请求被拒绝（401）【Illustrative · 预期行为】 |

> **多密钥**：官方文档说明 `--api-key` 支持配置多个 key，**只要匹配其中任意一个即可**通过【R3】——所以上面第 2 行是"匹配任意一个已配置 key"，而不是"必须等于唯一那个 key"。
>
> **客户端侧还有一个小约束**：OpenAI SDK 要求 `api_key` 构造参数非空，所以写个占位符（如 `"EMPTY"`）是**必须的**——但服务端没配 `--api-key` 时，这个占位符**不会**被拿去校验。

> **生产环境务必显式配置服务端 `--api-key`**，否则任何人都能调用你的模型——那行客户端里的 `api_key` 给不了你任何保护。源文档没有点明这一层【证据缺口 · UQ3】。

### 卡点 3：装上了，但在 macOS 上跑不了

见 [4.0](#platform-check)。这一条排在最后，是因为它的排查成本最高（会一路走到启动才炸）。

---

## 4.4 调用服务

### 用 curl 验证服务器活着

官方 quickstart 提供了两个直接的验证动作【Research-derived · R3】：

```bash
# 1. 列出已托管的模型
curl http://localhost:8000/v1/models

# 2. 发一个补全请求
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "prompt": "San Francisco is a",
    "max_tokens": 7,
    "temperature": 0
}'
```

源文档点明服务兼容 OpenAI 的 `/v1/chat/completions` 等接口【Source-derived · S5b】。

### 用 OpenAI Python SDK

源文档的写法【Source-derived · S5c】：

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="token-abc123")

completion = client.chat.completions.create(
    model="meta-llama/Llama-2-7b-hf",
    messages=[{"role": "user", "content": "你好！"}]
)
print(completion.choices[0].message.content)
```

**这段代码唯一的必要改动是把 `base_url` 指到本地**——这正是源文档所说"迁移成本极低，只需更改 Base URL"【Source-derived · S4d】的含金量所在。

官方 quickstart 的等价写法用 `"EMPTY"` 作为 key【Research-derived · R3】：

```python
from openai import OpenAI

openai_api_key = "EMPTY"
openai_api_base = "http://localhost:8000/v1"
client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

completion = client.completions.create(
    model="Qwen/Qwen2.5-1.5B-Instruct",
    prompt="San Francisco is a",
)
print("Completion result:", completion)
```

> `"EMPTY"` 这个写法直接把"我没有鉴权"这件事写在了代码里——比 `"token-abc123"` 更诚实地表达了当前状态（见 [卡点 2](#common-blockers)）。

---

## 4.5 离线批量推理

源文档【Source-derived · S5d】：

```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-2-7b-hf")
outputs = llm.generate(["Hello, my name is", "The capital of France is"], SamplingParams(temperature=0.8))
```

官方 quickstart 展开了输出结构【Research-derived · R3】：

```python
from vllm import LLM, SamplingParams

sampling_params = SamplingParams(temperature=0.8, top_p=0.95)
llm = LLM(model="facebook/opt-125m")
outputs = llm.generate(prompts, sampling_params)

for output in outputs:
    prompt = output.prompt
    generated_text = output.outputs[0].text
    print(f"Prompt: {prompt!r}, Generated text: {generated_text!r}")
```

**最容易踩的一个坑**：官方文档明确指出 "llm.generate method does not automatically apply the model's chat template to the input prompt."【Research-derived · R3】

也就是说，如果你要跑的是**聊天模型**并且输入是 messages 列表，**不要用 `llm.generate`**，用【Research-derived · R3】：

```python
outputs = llm.chat(messages_list, sampling_params)
```

> **选哪个？**
> - 纯文本续写（few-shot 补全、批量评测）→ `llm.generate`
> - 多轮对话 / 指令跟随 → `llm.chat`（自动套 chat template）

---

## 4.6 具体例子

### 例子 1 · 源文档的完整三步序列（Source-derived）

把 [S5a / S5b / S5c] 串起来，就是源文档承诺的"一条命令启动服务"的完整体验：

```bash
# 步骤 1：安装
uv venv myenv --python 3.12 --seed
source myenv/bin/activate
uv pip install vllm

# 步骤 2：启动（前台运行，Ctrl-C 停止）
vllm serve meta-llama/Llama-2-7b-hf --port 8000

# 步骤 3：另开一个终端调用
python call.py
```

其中 `call.py`：

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="token-abc123")
completion = client.chat.completions.create(
    model="meta-llama/Llama-2-7b-hf",
    messages=[{"role": "user", "content": "你好！"}]
)
print(completion.choices[0].message.content)
```

> **执行顺序上有个前提**：`vllm serve` **不会自己返回**——它的终端会一直被占着，这就是你判断"服务还在跑"的方式【Illustrative · 检查点】。启动过程会经历下载模型、加载权重、初始化显存等阶段，这段时间客户端连不上。所以步骤 3 必须**等终端出现就绪标志后**在**另一个终端**执行。源文档没有点明这个时序【证据缺口 · UQ7】。

### 例子 2 · 官方 quickstart 的"无需授权"路径（Research-derived）

如果你的目的是**先跑通**再谈生产，推荐这条不涉及 gated 模型、也不涉及鉴权的最短路径：

```bash
# 1. 启动（非 gated 模型，官方 quickstart 同款）
vllm serve Qwen/Qwen2.5-1.5B-Instruct

# 2. 另开终端，确认服务活着
curl http://localhost:8000/v1/models

# 3. 发一个请求
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-1.5B-Instruct","prompt":"San Francisco is a","max_tokens":7,"temperature":0}'
```

**为什么这条路径更适合入门**：

| 维度 | gated 路径（Llama-2-7b） | 非 gated 路径（Qwen2.5-1.5B） |
|---|---|---|
| 需要账号 / 接受许可 | 需要【R14】 | 不需要【R3】 |
| 模型体积 | 7B | 1.5B（官方 quickstart 用的入门模型）【R3】 |
| 上下文 | 4k【R14】 | 以模型页为准 |
| 适合 | 贴近生产模型 | 打通链路、验证部署流程 |

> **选型建议**：先用小非 gated 模型把"装 → 起 → 调"三步打通，再换成生产模型。这样能把"环境问题"和"模型授权问题"彻底分开——这是排查效率最高的做法。

### 例子 3 · 一次完整的可观测走查（Illustrative）

> **教学性构造。** 下表列的是**你要检查什么**，不是对输出内容的断言——具体的日志行与 JSON 字段取决于模型与版本。

| 步骤 | 执行 | 检查什么 |
|---|---|---|
| 0 | `nvidia-smi` | 能否看到你的 GPU，显存有没有被别的进程占满 |
| 1 | `python -c "import vllm; print(vllm.__version__)"` | 有没有打印出版本号、有没有抛异常 |
| 2 | `vllm serve <model>` | 终端有没有开始下载模型；下载完成后有没有出现与 KV cache / 并发相关的日志行 |
| 3 | 等终端出现就绪标志 | **此时再**去调客户端——过早调用会连接失败 |
| 4 | `curl http://localhost:8000/v1/models` | 返回的 JSON 里有没有你用的那个模型 ID |
| 5 | 发一个 `/v1/completions` 请求 | 有没有返回续写文本；改变 `max_tokens` 时输出长度有没有跟着变 |
| 6 | 再发一次**完全相同**的请求 | 两次输出是否高度相似——但注意前缀缓存启用时，重复请求可能命中缓存；已知存在 `temperature=0` 下首次与后续输出不一致的问题被报告为 bug【Research-derived · R16】 |

> **第 6 步的提醒**：它不是"必须完全一致"的断言。vLLM v1 的前缀缓存**默认开启**【R6】，而社区已报告在 `temperature=0` 下首个请求与后续请求输出不同、且可通过 `--no-enable-prefix-caching` 恢复确定性【R16 / 证据缺口 · UQ8】。如果你在做**严格可复现性评测**，建议显式加上 `--no-enable-prefix-caching`，或记录该影响。

---

## 本节小结

- **先查平台**：vLLM 只在 Linux 上完整运行；macOS 上装得上 ≠ 跑得了【R2】。
- **安装**：源文档流程正确；当前推荐 `uv pip install vllm --torch-backend=auto`，Python 需 `>=3.11,<3.15`【S5a / R1 / R3】。
- **启动**：`vllm serve <model-id>`，模型是位置参数，默认 8000 端口，默认从 HF 下载【S5b / R3】。
- **三个卡点**：gated 模型要授权【R14】、客户端 `api_key` 不等于服务端鉴权【R3】、平台不对装上也白装【R2】。
- **调用**：`curl /v1/models` 验活，`/v1/completions` 或 SDK 调用；离线用 `LLM`，**聊天用 `llm.chat` 不是 `llm.generate`**【S5c / S5d / R3】。
- **严格可复现评测**要显式 `--no-enable-prefix-caching`【R6 / R16】。

**下一步** → [05 · 相关工具](05-related-tools.md)
