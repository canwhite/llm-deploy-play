# 04 · 使用方法

> **学习目标**
> 完成本节后，你应该能够：
> 1. 按顺序走完源文档的**五个步骤**，每一步都有**可观察的完成判据**；
> 2. 正确启动**情况 A（纯 DP）**与**情况 B（TP×PP）**两种形态；
> 3. 说出每条启动参数**为什么出现在这里**；
> 4. 识别常见启动故障，并知道先查哪一项。

### 证据标签约定

`【Source-derived · Sxx】` 来自根文档 `source-sglang.md`；`【Research-derived · Rxx】` 来自外部权威来源；`【Illustrative】` 为教学性构造，不主张 SGLang 的未经验证行为。完整定位码与出处见 [07 · 验证记录](07-verification-record.md)。

> **本节的命令以源文档为准，但有两处必须先核对**：(1) 源文档推荐的具体模型型号，见 [03 · 3.3.3](03-core-functionality.md#model-choice)；(2) 源文档给出的 Blackwell 参数是否与**你安装的 SGLang 版本**一致——命令会随版本演进，**参数拼写请以 `--help` 输出为准**。

---

<a id="40-preflight"></a>

## 4.0 开工前：确认五件事

在写任何参数之前，先确认这三项。缺任何一项，后面都会以"莫名其妙的方式"失败。

| # | 检查 | 命令 | 通过判据 |
|---|---|---|---|
| 1 | **卡在不在** | `nvidia-smi` | 列出你的 GPU；`nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv` 能看到型号、显存与计算能力 |
| 2 | **SGLang 在不在** | `python3 -m sglang.launch_server --help` | 能列出 `--tp-size` 等参数；有版本输出更好（`pip show sglang`） |
| 3 | **共享内存够不够**（容器环境） | `df -h /dev/shm` | 容器内 `/dev/shm` 不是默认的小值；SGLang 依赖它做进程间通信【S16】。官方 Docker 基准值是 `--shm-size 32g`【R31】 |
| 4 | **CUDA 版本对不对** | `nvcc --version` 或查镜像 tag | 当前 SGLang **要求 CUDA 13**；CUDA 12 镜像已不再发布【R31】 |
| 5 | **参数取值对不对** | `python3 -m sglang.launch_server --help \| grep -A3 quantization` | 确认你版本的 `--quantization` 合法取值里**没有 `nvfp4`**【R30】 |

> **第 3 项最容易被漏。** 源文档把它列为 Blackwell 必配项："Docker需设置 `--shm-size`，K8s需调整 `/dev/shm`"【Source-derived · S16】。默认的容器共享内存通常远小于需求。

---

<a id="step-1-topology"></a>

## 4.1 第一步：测量拓扑

```bash
nvidia-smi topo -m
```

源文档把这一步放在最前面，理由是"在写任何配置前，先用 `nvidia-smi topo -m` 确认20张卡的物理连接关系"【Source-derived · S2】。

### 怎么读这张表

- 找到每个 GPU 的**行**，看它下面的连接关系（`PIX` / `NODE` / `SYS`）；
- **同一个 Switch 下的一组 GPU**，才是 TP 的候选域；
- `SYS` 意味着要跨 NUMA 节点甚至跨 socket，走这类路径做 TP 代价很高。

### 完成判据

- [ ] 你能指着输出说出："**我的 TP 上限是 N**"，并说明理由（哪几个卡在同一个 Switch 域内）
- [ ] 你能说出："**我的节点数是 M**"，并确认节点间是 InfiniBand 还是普通以太网

> **不要跳过这步直接抄 `--tp-size 4`。** 源文档的 5×4 是**假设**【S7】；你的机器可能是 4×5、8×2.5（不整除）、或 2 个 8 卡域。**TP 规模必须来自这张表，不能来自抄来的数字。**

---

<a id="step-2-grading"></a>

## 4.2 第二步：判断走哪条分支

把模型规格和量化格式填进这个判断：

| 条件 | 走哪条 | 参数 |
|---|---|---|
| 权重 + KV Cache + 运行时开销 **≤ 32GB** | **情况 A：纯 DP** | `--tp-size 1`，20 个独立实例 |
| **> 32GB** | **情况 B：TP×PP** | `--tp-size <你的PCIe域内卡数>`，`--pp-size <节点数>` |

### 完成判据

- [ ] 你能说出所选模型**在所选量化格式下**的单卡显存估算值
- [ ] 你能指出自己的分支是 A 还是 B，以及**为什么**

---

<a id="step-3-blackwell"></a>

## 4.3 第三步：加上 Blackwell 必配项

不管走哪条分支，下面这些参数都要在：

| 参数 | 值 | 为什么 |
|---|---|---|
| `--attention-backend` | `flashinfer` | Blackwell 上部分默认后端的长提示 TTFT 可能极差【S12】。⚠️ SM120 上官方允许 `triton` 或 `flashinfer`【R32】——**不是强制项**（官方文档里“自动选 FlashInfer”那句话只适用于 SM100/SM103，不适用 SM120） |
| `--quantization` | 见下方说明 | BF16 显存不够；NVFP4 是 Blackwell 原生格式【S11】。⚠️ **合法取值里没有 `nvfp4`**【R30】 |
| `--mem-fraction-static` | `0.85` ~ `0.90`（源文档建议） | 为 KV Cache 留足空间【S15】。⚠️ 官方默认是**自动计算**，且官方建议在 OOM 时**调小**【R37】 |
| 容器 `--shm-size` | `32g` | 进程间通信依赖共享内存【S16】；官方 Docker 示例统一用 `32g`【R31】 |
| CUDA | **13.x（现为硬性要求）** | 源文档写的是"推荐版本"【S14】，但官方已改为 "SGLang requires CUDA 13"【R31】 |

> ### ⚠️ `--quantization` 的取值必须核对
>
> 源文档的命令块写的是 `--quantization nvfp4`【S8】。但 SGLang 的 `QUANTIZATION_CHOICES` 里**没有 `nvfp4` 这个取值**——它会被 argparse 直接拒绝【Research-derived · R30】。NVFP4 检查点对应的取值是 `modelopt_fp4` / `nvfp4_online` / `petit_nvfp4` / `mxfp4` 等，**具体用哪一个取决于你的检查点是怎么导出的**。
>
> **动手前先跑这一条**，照抄你那个版本的合法取值：
>
> ```bash
> python3 -m sglang.launch_server --help | grep -A3 -- "--quantization"
> ```
>
> **这个值只能由你现场确定**【UQ2】——它随 SGLang 版本与检查点的导出方式变化，课程不替你选定。
>
> 另外注意：**NVFP4 的 GEMM 路径需要装 FlashInfer**（"NVFP4 GEMM requires FlashInfer to be installed"）【R34】——所以上面那条 `--attention-backend flashinfer` 在用 NVFP4 时不是可选项。

### 完成判据

- [ ] 你的启动命令里能指出上面每一项对应的参数
- [ ] 容器场景下 `/dev/shm` 已经确认过

---

<a id="case-a-command"></a>

## 4.4 情况 A：启动 20 个纯 DP 副本

源文档给出的形态是：**20 个独立的 SGLang 实例**，每个实例占 1 张 GPU，运行完整模型副本，`--tp-size 1`【S5】，并用 SGLang Router 在副本间分发请求【S6】。

【Illustrative】 下面是**本课程按源文档参数拼装**的单实例命令形态（源文档只给了情况 B 的完整命令块【S8】，情况 A 的参数来自【S5】【S11】【S12】【S15】）。**它不是源文档的原文**，请按你实际的 SGLang 版本调整：

```bash
# 单个副本（本例为 node0 / GPU 0）
CUDA_VISIBLE_DEVICES=0 \
python3 -m sglang.launch_server \
  --model-path /path/to/model \
  --tp-size 1 \
  --attention-backend flashinfer \
  --quantization <你的版本里对应 NVFP4 的取值> \
  --mem-fraction-static 0.85 \
  --host 0.0.0.0 --port 30000
```

> **`--quantization` 的值留空了**：源文档写的 `nvfp4` **不是 SGLang 的合法取值**【R30】。候选是 `modelopt_fp4` / `nvfp4_online` / `petit_nvfp4` / `mxfp4`——**取决于你的检查点怎么导出**。请先用 `--help` 核对，再填。

**在 5 节点上铺开 20 个副本**，就是把这个命令在每张卡上跑一次（每节点 4 个，用不同的 `CUDA_VISIBLE_DEVICES` 与 `port`）：

```bash
# 节点内的 4 个副本（node0）——端口需互不冲突
# 【Illustrative】本循环是本课程按 S7 的 5 节点 × 4 卡假设构造的，源文档只给单实例命令
for i in 0 1 2 3; do
  CUDA_VISIBLE_DEVICES=$i nohup python3 -m sglang.launch_server \
    --model-path /path/to/model \
    --tp-size 1 \
    --attention-backend flashinfer \
    --quantization <你的版本里对应 NVFP4 的取值> \
    --mem-fraction-static 0.85 \
    --host 0.0.0.0 --port $((30000 + i)) \
    > /tmp/sglang-replica-$i.log 2>&1 &
done
```

### 完成判据

- [ ] 20 个副本全部起来了（每个节点的 `nvidia-smi` 显示对应显存被占用）
- [ ] 每个副本的日志里**没有**加载挂起（对照 FP8 MoE 的已知问题【S13】）
- [ ] 某一个副本的端口可以接受请求

---

<a id="case-b-command"></a>

## 4.5 情况 B：启动 TP × PP

这是**源文档给出的完整命令**【Source-derived · S8】：

```bash
python3 -m sglang.launch_server \
  --model-path /path/to/model \
  --tp-size 4 \
  --pp-size 5 \
  --dist-init-addr <MASTER_IP>:20000 \
  --nnodes 5 --node-rank <0-4> \
  --attention-backend flashinfer \
  --quantization nvfp4 \
  --mem-fraction-static 0.85 \
  --host 0.0.0.0 --port 30000
```

> ### ⚠️ 这段命令**逐字照抄会起不来**
>
> **`--quantization nvfp4` 不是合法取值**——SGLang 的 `QUANTIZATION_CHOICES` 里没有它，argparse 会直接拒绝【Research-derived · R30】。请换成你那个版本里对应 NVFP4 检查点的取值（候选：`modelopt_fp4` / `nvfp4_online` / `petit_nvfp4` / `mxfp4`），并先用 `--help` 核对。
>
> **其余参数逐字有效**：`--tp-size`、`--pp-size`、`--nnodes`、`--node-rank`、`--dist-init-addr`、`--attention-backend`、`--mem-fraction-static`、`--host`、`--port` 都已对照官方 server arguments 文档与源码逐一核实【R30】。`--attention-backend flashinfer` 也在合法取值表里【R30】。
>
> 另外两条与本命令相关的提醒：
> - **CUDA 13 是硬性要求**，不是推荐——CUDA 12 的 wheel 与镜像已停止发布【R31】。
> - **20 张无 NVLink 的卡做 TP 有已知的 P2P 挂起**：SGLang issue #15181 报告在两张 Blackwell 卡上做 TP 时，若不设 `NCCL_P2P_DISABLE=1`，"the process hangs indefinitely"（拓扑为 `NODE`，无 NVLink）【R33】。**做情况 B 前务必先在 2 卡上复现一次**。

### 每个参数在这里的原因

| 参数 | 作用 | 出处 |
|---|---|---|
| `--tp-size 4` | 单个 PCIe 域内的卡数 | 【S7】（**但请按你自己的拓扑改**【S2】） |
| `--pp-size 5` | 节点数 = 流水线 stage 数 | 【S7】 |
| `--dist-init-addr <MASTER_IP>:20000` | 多进程的 rendezvous 地址 | 【S9】 |
| `--nnodes 5` / `--node-rank <0-4>` | 告诉每个节点它的编号（rank） | 【S9】 |
| `--attention-backend flashinfer` | Blackwell 后端要求 | 【S12】 |
| `--quantization <NVFP4 取值>` | Blackwell 量化要求（**源文档首选**，不是硬性要求）；⚠️ `nvfp4` 不是合法取值 | 【S11】【R30】 |
| `--mem-fraction-static 0.85` | 给 KV Cache 留空间 | 【S15】 |

### 在多节点上执行的顺序

1. **先确定哪个节点是 master**（`--dist-init-addr` 里的 `<MASTER_IP>`）；
2. **5 个节点上都用同一条命令**，只有 `--node-rank` 不同（0–4）；
3. **等所有节点都起来**——`--dist-init-addr` 是 rendezvous，早到的节点会等后到的；
4. 全部就绪后，只有 **rank 0** 的那个进程会真正开始接受请求。

> **`--node-rank` 与 `--host/--port` 的常见误区**：源文档在每条命令末尾都给了 `--host 0.0.0.0 --port 30000`【S8】。在多节点 PP 部署里，**不要让 5 个节点都去抢 30000 端口**——`--host 0.0.0.0` 是"监听所有网卡"，但同一节点上多个进程会撞端口。**每个节点上只应有一个监听该端口的进程**（通常是 rank 0 所在节点对外提供服务），其余节点的端口可指向内部地址。

### 完成判据

- [ ] 5 个节点的进程都起来了，且**互相能解析 `<MASTER_IP>`**
- [ ] rank 0 的日志显示服务已就绪
- [ ] 你能解释：**为什么 `--tp-size` 是 4 而不是 20**（答：TP 不能跨 PCIe 域【S2】）

---

<a id="step-4-cold-start"></a>

## 4.6 第四步：接上冷启动

<a id="461-rfork从运行中的实例拉权重"></a>

### 4.6.1 R-Fork：从运行中的实例拉权重

**Seed 实例**——正常启动，不需要任何额外参数【S18】：

```bash
python -m sglang.launch_server [args]
```

**Client 实例**——增加以下参数，直接从 Seed 实例拉取权重【S19】：

```bash
python3 -m sglang.launch_server \
  ... \
  --load-format remote_instance \
  --remote-instance-weight-loader-seed-instance-ip <SEED_IP> \
  --remote-instance-weight-loader-seed-instance-service-port <SEED_PORT> \
  --remote-instance-weight-loader-backend nccl
```

若使用 `transfer_engine` 后端，**Seed 实例**需额外加【S20】：

```bash
--remote-instance-weight-loader-start-seed-via-transfer-engine
```

> ### ⚠️ 源文档的 NCCL 示例少了一个必需参数
>
> 上面这段是**源文档给的原文**【S19】。但官方文档写明，`nccl` 后端还需要 **`--remote-instance-weight-loader-send-weights-group-ports`**——它提供 "the list of available ports on the seed instance that will be used to build NCCL communication groups between seed and client instance. **Only needed by `nccl` backend**"【Research-derived · R25】。
>
> **照抄源文档的这段命令，NCCL 通信组建不起来。** 实际使用时应补上：
>
> ```bash
> --remote-instance-weight-loader-send-weights-group-ports <PORT1> <PORT2> ...
> ```
>
> 另外三点必须知道：
> - **Seed 与 Client 的并行策略必须一致**——"Only support loading weights from instance with same parallelism strategy"【R25】；
> - **NCCL 后端会打扰 Seed 的推理**——传输期间 Seed 侧会出现延迟尖峰【R25】；
> - **还有第三个后端** `modelexpress`，源文档没提【R23】。

> **参数拼写以 `--help` 为准**：这些 flag 在源码里是下划线字段名（`remote_instance_weight_loader_seed_instance_ip`），命令行形式由 argparse 生成【R22】。**不同 SGLang 版本的拼写可能不同**——请先跑 `python3 -m sglang.launch_server --help | grep remote-instance` 确认。

### 完成判据

- [ ] Client 实例的启动日志显示权重**从 Seed 拉取**，而不是从磁盘读取
- [ ] 你能说出这次省掉的是冷启动三段成本里的**哪一段**（答案：① 权重加载，见 [02 节](02-core-concepts.md#cold-start-costs)）

### 4.6.2 NVIDIA Snapshot：预先拍快照

源文档的运维要求是"**预先启动好服务、拍下快照**"【S22】。它不是一个启动参数，而是一套**运维流程**：

1. 正常启动服务，让它**完全初始化**（权重加载完、图编译完）；
2. 对这个已初始化的 GPU 工作负载做检查点；
3. 需要恢复时，用快照恢复，**跳过权重加载与图编译**【S21】。

> ### ⚠️ 三个必须先确认的适用前提
>
> 1. **它只在 Kubernetes 上可用**。官方定位是 "a Kubernetes-native checkpoint and restore system for NVIDIA GPU workloads"，要求使用 Kubernetes 自定义资源【Research-derived · R20】。**源文档设计的 5 节点裸机 SSH 部署方案，无法直接套用 Snapshot**——要么把编排层换成 K8s，要么放弃这一层。
> 2. **多 GPU 也只能单节点**。官方限制原文："Workloads, including multi-GPU workloads, must run on a single node. Multi-node is on the roadmap."【R20】——**PP 横跨 5 个节点的整体实例无法被快照**。
> 3. **官方自己说"暂不建议用于生产关键负载"**："Snapshot's APIs may still change, so it is **not yet recommended for production-critical workloads**"【R20】。
>    而源文档把它写成"层次二：生产级秒级弹性——NVIDIA Snapshot（必选）"【S21】——这个定性与 NVIDIA 自己的措辞不一致。
>
> **还有一条容易误读的数字口径**：3.6–42.7 秒是**恢复段**的耗时，不含镜像拉取、Pod 调度与运行时初始化——官方明确 "infrastructure provisioning and container image loading remain outside the measured restore path"【R19】。**端到端的"上线时间"更长**。

### 完成判据

- [ ] 你能区分"**恢复**一个副本"（快照能帮上）和"**扩容**一个新副本"（快照帮不上，要走正常启动路径）
- [ ] 你能说出快照的**三个适用前提**（K8s-only、单节点、官方标注非生产关键负载）

---

## 4.7 第五步：接上路由

源文档明确"不建议手动逐个SSH启动"【S23】，并把请求分发交给 SGLang Router【S23】。

> **名字先说清楚**：源文档写的是"SGLang Router（现称 Model Gateway）"【S23】。这个名字**改过两次**——2024 年是 `sglang-router`（SGLang DP Router），2025-10-23 改称 **SGLang Model Gateway (SMG)**，**SGLang 1.0 又改回 `sgl-router`**，并弃用 `sgl-model-gateway`【Research-derived · R9】【R10】【R11】。**当前应称 `sgl-router`**。另一个同名的 **Shepherd Model Gateway (SMG)** 是 LightSeek 基金会的独立项目，与 SGLang 无关【R9】。

**官方推荐的用法**是"用网关做 DP"，并且官方对 SGLang 自带的原生 DP 模式明确不推荐：

> "**We strongly recommend using the SGLang Model Gateway (SMG) for production-grade Data Parallelism.**" / "Native DP is **highly not recommended for use right now**."【Research-derived · R12】

【Research-derived】 源文档**没有给出** Router 的启动命令，以下是官方文档给出的实际调用形式【R12】【R15】：

```bash
# 方式一：把已有的独立副本挂到一个 router 上
python -m sglang_router.launch_router \
  --worker-urls http://worker1:8000 http://worker2:8000 \
  --policy cache_aware \
  --host 0.0.0.0 --port 30000
```

```bash
# 方式二：让 router 自己在单卡模型上拉起 DP 副本
python -m sglang_router.launch_server \
  --model-path meta-llama/Meta-Llama-3.1-8B-Instruct \
  --dp-size 8
```

**可选路由策略**：`random`、`round_robin`、`power_of_two`、`cache_aware`（0.x 默认）、`bucket`；1.0 之后的 `sgl-router` 还提供 `session_aware`，且**默认策略改为 `power_of_two`**【R12】【R15】。**两代的清单与默认值并不一致**——以你安装版本的 `--help` 为准【UQ11】。

> **一个必须知道的边界**：router 的工作单元是**完整的 SGLang 实例（engine）**，不是流水线 stage 组——源文档架构图里"大模型场景路由到 PP 组"的说法【S25】，**在官方文档里没有对应**。——官方自述 "A router serves one model and spreads its requests across that model's SGLang **engines**"【R15】。

### 完成判据

- [ ] Router 的**后端地址清单**能覆盖全部 20 个副本（DP）；情况 B 下，每个 PP 组需**对外暴露为一个可路由实例**，共 5 个 engine 端点——源文档的架构图正是这样区分的【S25】【R15】；
- [ ] Router 的**路由策略**对你是合适的（轮询 / 负载感知 / 缓存感知）；
- [ ] 副本**健康检查**的失败处理符合你的预期（副本挂了，Router 应该把流量挪走）；
- [ ] 你能说出**当前**它叫什么（`sgl-router`），以及它把请求分发到什么粒度（完整实例）

---

<a id="48-startup-faults"></a>

## 4.8 常见启动故障排查顺序

按"先查哪个"排序：

| # | 症状 | 先查这一项 | 依据 |
|---|---|---|---|
| **1** | 服务**卡住/无响应**，日志没有明显报错 | **容器 `/dev/shm` 大小** | SGLang 进程间通信依赖共享内存【S16】；这是"不报错但不动"的典型原因 |
| **2** | **加载模型时挂起** | **量化格式与模型类型** | 部分 FP8 MoE 路径在 SM_120 上加载时会挂起；改用 NVFP4 检查点【S13】 |
| **3** | **启动即显存不足** | **`--mem-fraction-static` 与模型实际占用** | 该值要为 KV Cache 留足空间；0.85~0.90 是源文档给的区间【S15】 |
| **4** | R-Fork Client **连不上 Seed / 传输卡住** | **① 并行策略是否一致；② `nccl` 后端是否给了 `--remote-instance-weight-loader-send-weights-group-ports`** | 两项都是硬约束【R25】；源文档的示例命令**缺第二个** |
| **5** | 快照恢复**起不来 / 恢复后 CUDA 调用挂死** | **是不是在 K8s 上；是不是跨节点；是不是装了拦截 `libcuda.so` 的监控工具** | 官方限制：K8s-only、单节点、"must not have tools that intercept `libcuda.so` calls"【R20】 |
| **6** | 启动**参数直接被拒**（argparse 报错） | **`--quantization` 的取值** | `nvfp4` 不在合法取值表里【R30】 |
| **7** | TP 起来后**进程无限挂起** | **`NCCL_P2P_DISABLE=1`** | 无 NVLink 的 Blackwell 卡上做 TP 的已知问题 #15181【R33】；官方另有针对无 NVLink 主机的 FlashInfer PCIe-IPC all-reduce 说明【R35】 |

### 一个通用的排查顺序

> **先看日志开头，再看报错，再看参数。** 源文档给出的是"必须显式处理"的项，**没列出的项不代表一定没问题**。第 3 类故障的常见根因是**模型比你想的大**——回到 [4.2 节](#step-2-grading) 重新核对。**第 4、5 类则要回到 [3.5](03-core-functionality.md#step-4-cold-start) 的边界表去核对前提条件。**

---

## 本节小结

- **顺序不能乱**：测拓扑 → 判分级 → 加 Blackwell 必配项 → 启动 → 接冷启动 → 接路由。
- **情况 A** 是 20 个 `--tp-size 1` 的独立副本【S5】；**情况 B** 是 `--tp-size 4 --pp-size 5` 的跨节点 PP 组【S7】【S8】。
- **源文档唯一给出的完整命令是情况 B 的**【S8】；情况 A 的命令形态是本课程按源文档参数拼装的【Illustrative】。
- **多节点时 `--node-rank` 要区分**，`--dist-init-addr` 是 rendezvous，早到的节点会等【S9】。
- **七类故障的排查顺序**：共享内存 → 量化格式 → 显存预算 → R-Fork 前提 → 快照前提 → **参数取值被拒** → **TP 无限挂起**。
- **两处源文档的命令不能照抄**：R-Fork 的 NCCL 示例少了一个必需参数【R25】；Snapshot 在裸机多节点上根本不适用【R20】。

**下一节**：[05 · 相关工具](05-related-tools.md) —— 把 Router、Ray Serve、Snapshot、KServe 这些工具放回各自的层次。
