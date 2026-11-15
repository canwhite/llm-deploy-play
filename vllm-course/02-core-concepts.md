# 02 · 核心概念：两个支柱

> **学习目标**
> 完成本节后，你应该能够：
> 1. 解释分页注意力（PagedAttention）如何消除显存碎片，说清"块表"的作用；
> 2. 解释连续批处理（Continuous Batching）与传统批处理的差别，说清"推理步"是什么；
> 3. 说清**为什么这两个机制必须搭配使用**，而不是各自独立地带来收益；
> 4. 描述前缀缓存（Prefix Caching）的工作方式，并说明它的默认开启状态与信任边界。

### 证据标签约定

`【Source-derived · Sxx】` 来自根文档 `source.md`；`【Research-derived · Rxx】` 来自外部权威来源；`【Illustrative】` 为教学性构造（含用于讲解的**定义性框架**），不主张 vLLM 的未经验证行为。完整定位码与出处见 [07 · 验证记录](07-verification-record.md)。

---

## 2.1 心智模型：把 KV Cache 当成"需要被管理的资源"

要理解后面所有内容，先换一个视角。

很多教程把 LLM 推理想成"模型一次算一个词"。在 vLLM 的世界里，更贴切的模型是：

> **GPU 显存里有一份共享的 KV Cache 池，vLLM 的工作是在每个推理步把这份池子切给当前活跃的请求集合。**【Illustrative】

这个视角一变，两件事就自然了：

- **KV Cache 是"资源"而不是"附属品"**——它要被分配、回收、复用、共享；
- **"调度"和"内存管理"是两件事，但必须协同**——这正是两个支柱的关系。

**KV Cache 是什么？** 每个请求在生成过程中，为已经处理过的每个 token 保存一份 Key 和一份 Value，供后续 token 的注意力计算使用。它是模型的"短期记忆"【Source-derived · S3a】，也是分页注意力要管理的核心对象【Research-derived · R5】。

它的两个麻烦属性决定了后面所有的设计【Research-derived · R4 / R5】：

| 属性 | 后果 |
|---|---|
| **长度动态变化、事先不可知** | 模型自己决定生成到哪儿停，显存需求无法预估 |
| **随 token 增长而变大** | 序列越长，KV Cache 越大；并发数一高，显存先崩 |

于是，"为每个请求预留一块连续的大显存"就成了必然——但这块预留又必须够大，否则请求生成到一半就 OOM。**预留过大 = 浪费，预留刚好 = 频繁 OOM**。分页注意力要跳出这个两难【Source-derived · S2a / Research-derived · R5】。

---

## 2.2 支柱一：分页注意力（PagedAttention）——内存管理术

### 它做什么

源文档的表述很精准：vLLM 借鉴了**操作系统的虚拟内存思想**，将 KV Cache 切分成固定大小的**"块"（Block）**，并允许这些块存储在显存中**不连续**的物理位置上。一个请求的逻辑序列，通过一个**"块表"**映射到物理块上，就像书的目录一样【Source-derived · S3a】。

官方论文与博客给出了更精确的定义：

- "PagedAttention partitions the KV cache of each sequence into blocks, each block containing the keys and values for a fixed number of tokens."【Research-derived · R5】
- "The contiguous logical blocks of a sequence are mapped to non-contiguous physical blocks via a block table."【Research-derived · R5】
- "The physical blocks are allocated on demand as new tokens are generated."【Research-derived · R5】

这就是"分页"的含义——**块 = 操作系统里的页，token = 字节，序列 = 进程**，逻辑地址空间与物理页帧分离。

### 为什么有效

传统系统的问题是双重的，官方博客给出的数字是：**"existing systems waste 60% – 80% of memory due to fragmentation and over-reservation"**【Research-derived · R5】。60–80% 的显存被浪费——这就是"为什么一张 80GB 的卡跑不满"。

分页注意力把浪费压缩到了**只剩每条序列的最后一个块**："In PagedAttention, memory waste only happens in the last block of a sequence. In practice, this results in near-optimal memory usage, with a mere waste of under 4%."【Research-derived · R5】

> ⚠️ **一个必须说清的精度问题**：那个 "under 4%" 是**系统级平均**——官方博客未说明其统计口径。**本节的推断**是：它来自大量长度各异的序列，末块浪费被摊薄了。**单条短序列的末块浪费比例可以很高**（见例子 2）。不要把 4% 套到任何单条请求上。

### 关键机制：块表、引用计数与 Copy-on-Write

块表不只是索引，它还是**共享**的基础："PagedAttention naturally enables memory sharing through its block table ... different sequences in PagedAttention can share the blocks by mapping their logical blocks to the same physical block."【Research-derived · R5】

共享要安全，就要有引用计数："PagedAttention keeps track of the reference counts of the physical blocks" 并 "implements the Copy-on-Write mechanism"【Research-derived · R5】——即当一个共享块需要被写入时，先复制再写，不影响其他引用者。

这套机制带来的收益是可量化的：官方博客在并行采样与 beam search 场景下报告，最多**节省 55% 的显存**，并可转化为**最高 2.2 倍的吞吐提升**【Research-derived · R5】。

### 块有多大

vLLM 的缓存配置中，`DEFAULT_BLOCK_SIZE = 16`，即默认每个块装 **16 个 token**【Research-derived · R7】。块是"固定大小"的核心参数——固定才能像页一样被池化管理。

---

## 2.3 支柱二：连续批处理（Continuous Batching）——动态调度策略

### 它做什么

源文档：vLLM 的规则是"**随吃随走，有空就拼**"。一旦这桌有客人吃完离开，立刻就让外面排队的新客人坐上他的位置，确保厨师**一刻不停**地在工作【Source-derived · S2b】。

技术上，源文档说得更精确：**"它在每个推理步（step）都会重新组批，而非等待整个批次结束"**。一旦有请求完成，调度器会立刻将队列中的新请求插入，让 GPU 的算力尽可能不被闲置【Source-derived · S3b】。

**"推理步"是什么**：一次前向传播。解码阶段每个请求每步产出一个 token，因此一个请求生成 500 个 token 大致要走 500 步【Illustrative · 定义性框架】。

### 关键差别：组批发生在"步"的粒度，不是"批"的粒度

| | 传统批级别批处理 | 连续批处理 |
|---|---|---|
| 批次何时确定 | 服务开始前，一次定死 | **每个推理步重新确定** |
| 短请求完成后 | 仍占据批位直到整批结束 | **立刻退出**，位置被新请求接管 |
| 新请求入场 | 等整批跑完 | **下一个 step 就能进** |
| 有效步数占比 | 取决于最慢请求 | **显著高于批级别批处理**（具体比例取决于请求长度分布）【Illustrative】 |

---

## 2.4 为什么两个支柱必须搭配（关键洞察）

源文档点出了这层依赖：**"这需要 PagedAttention 提供的灵活内存管理作为基础，因为新请求随时需要新的内存块"**【Source-derived · S3b】。

这个依赖是**双向的**，很多人只看到单向：

**连续批处理 → 需要分页注意力：**
每个 step 都有新请求插入，新请求需要新的 KV 块。如果显存是"每请求预留一大块连续空间"，那么新请求进来就得预留一整块大空间，即使它最终只生成 20 个 token。GPU 很快就因为预留而饱和。分页注意力让"再塞一个请求进来"的边际显存成本降到**按需的一个块（默认 16 token）**【Research-derived · R7】。

**分页注意力 → 需要连续批处理：**
分页把显存碎片消除了，但如果调度策略仍是"等整批结束"，那些刚刚释放的物理块会**闲置到整批结束**才被复用。内存效率提升拿不到吞吐收益——腾出来的空间得有人用。连续批处理保证**每一块空闲显存几乎立刻被新请求占用**。

> **一句话总结耦合关系**：
> **分页注意力负责"腾得出空间"，连续批处理负责"空间不闲置"。**
> 只有前者 → 显存省了但用不满；只有后者 → 批是满了但每块都预留过大。
> 两者叠加，才形成 [01 节](01-positioning-and-background.md) 说的"翻台率飞跃"【Source-derived · S2c】。

---

## 2.5 第三个机制：前缀缓存（Prefix Caching）

源文档把前缀缓存作为分页注意力的**衍生收益**提到："让点相同菜品的客人**共享**一部分格子（**前缀缓存**）"【Source-derived · S2b】，并在场景部分强调它能"复用重复的系统提示词或文档上下文，节省显存和计算"【Source-derived · S4c】。

官方设计文档给出了工作方式：

- **基于哈希的块匹配**——APC（Automatic Prefix Caching）缓存已有请求的 KV Cache，新请求若与已有请求共享前缀，就直接复用这部分 KV Cache，跳过对共享部分的计算【Research-derived · R15】；
- **块表是 append-only 的**——在 vLLM v1 中，块表只允许追加，不允许把 `[0, 3]` 改成 `[0, 1]`；结果是相同哈希键下**可能存在重复的块**【Research-derived · R15】；
- **哈希算法可选**：`--prefix-caching-hash-algo` 支持 `sha256`（默认）、`sha256_cbor`（可跨环境复现、跨语言兼容）、`xxhash`（更快，非密码学用途）【Research-derived · R15】。

**默认开启吗？** 源文档没有说明【证据缺口 · UQ2】。答案是：**vLLM V1 默认开启**。官方 V1 发布博客写得非常明确——V0 因为开启后有显著 CPU 开销（命中率低时会掉性能）而默认关闭；V1 优化了数据结构，做到"命中率 0% 时吞吐下降不到 1%"，因此 "Thanks to the near-zero overhead, we now enable prefix caching by default in V1"【Research-derived · R6】。

> **一个安全边界值得单独记住**：官方设计文档提到，缓存共享可以通过让不同用户**约定一个共同的 salt** 来限制在信任组内，从而把不同租户隔离开【Research-derived · R15】。源文档完全没有提到这一层【证据缺口 · UQ6】。在多租户场景里，"谁能看到谁的 KV Cache"是一个安全设计问题，不只是性能问题。

---

## 2.6 术语对照表

| 中文 | 英文 | 首次出现 | 一句话解释 |
|---|---|---|---|
| 键值缓存 | KV Cache | [01](01-positioning-and-background.md) | 模型对已处理 token 的"短期记忆"，分页注意力管理的对象 |
| 分页注意力 | PagedAttention | 本节 | 用固定大小的块管理 KV Cache，块可散布于显存，消除碎片 |
| 块表 | Block Table | 本节 | 逻辑块 → 物理块的映射表，兼作共享的基础 |
| 连续批处理 | Continuous Batching | 本节 | 每个推理步重新组批，请求完成即腾位 |
| 推理步 | Step | 本节 | 一次前向传播；解码阶段每个请求每步产出一个 token |
| 前缀缓存 | Prefix Caching / APC | 本节 | 复用共享前缀已算好的 KV Cache，V1 默认开启 |
| 预填充 | Prefill | [03](03-core-functionality.md) | 处理输入提示词、产出首个 KV Cache 的阶段 |
| 解码 | Decode | [03](03-core-functionality.md) | 用 KV Cache 逐 token 生成输出的阶段 |

---

## 2.7 具体例子

### 例子 1 · 从餐厅格子到块表（Source-derived）

源文档的类比是：把餐厅改造成无数个**标准化的小格子**（固定大小的内存块）。客人来了按需分配格子，吃完立刻回收；点相同菜品的客人还能**共享**一部分格子【Source-derived · S2b】。

把它翻译成 vLLM 的实际结构：

| 餐厅类比 | vLLM 实体 |
|---|---|
| 标准化小格子 | 物理块（默认 16 token） |
| 客人（一条对话） | 一个请求 / 一条序列 |
| 客人手写的"目录"，记录自己在哪些格子 | **块表**（block table） |
| 点相同菜品共享格子 | 前缀缓存 / 块共享 |
| 领班随时换人拼桌 | 调度器每个推理步重新组批 |

> 关键理解：**块表是这个类比里最容易被忽略、但最关键的一环**。没有块表，"格子在哪儿"就无从记录；有了块表，格子在哪儿**根本不重要**——这正是分页能消除"必须连续"约束的原因。

### 例子 2 · 一条请求的真实显存账（Research-derived）

> 基础事实：块大小默认 16 token【Research-derived · R7】；末块浪费是分页注意力下**唯一**的浪费来源【Research-derived · R5】。

假设一条请求最终有 **40 个 token**：

```
块 0: [token 0  .. 15 ]   满
块 1: [token 16 .. 31 ]   满
块 2: [token 32 .. 39 ]   只用了 8 / 16   ← 末块
```

- 实际需要的 KV 容量 = 40 token；
- 实际分配到的容量 = 3 × 16 = 48 token；
- **这条序列的浪费率 = 8 / 48 ≈ 16.7%**。

> **对照 [R5] 的 "under 4%"**：那个数字是**系统级**的——官方博客未说明其统计口径。**本节的推断**是：当序列长度分布足够分散、且同时有大量序列在跑时，末块浪费被摊薄。而单看一条 40 token 的短请求，浪费率高达 16.7%。
>
> **这解释了一个实践现象**：**短请求为主的负载，末块浪费相对更明显**；请求越长、长度分布越分散，分页带来的实际收益越接近官方博客里的数字。这也解释了为什么块大小是一个需要按负载调优的参数。

### 例子 3 · 多租户共享系统提示词（Illustrative）

> **教学性构造，不主张 vLLM 的未经验证行为。**

一个 SaaS 产品的真实负载长这样：100 个用户，每个用户的请求都是

```
[系统提示词：固定的 800 token 公司规章]  +  [用户问题：50 token]
```

**没有前缀缓存时**：每个请求都要为那 800 token 的系统提示词**重算一遍 KV Cache**。100 个请求 = 100 次相同的 prefill 计算。

**有前缀缓存时**（V1 默认开启【Research-derived · R6】）：第 1 个请求算完这 800 token，后续 99 个请求的共享前缀**直接命中缓存**，跳过 prefill。

这个例子的教学价值在于揭示一件事：

> **前缀缓存的价值随"共享前缀的长度 × 请求数"增长，而随"请求之间的差异性"衰减。**
>
> - 系统提示词固定、用户问题短 → 命中率高，收益大；
> - 每个请求都是一段不同的长文档 → 几乎没有可共享的前缀，收益接近 0。
>
> 这也解释了源文档为什么把前缀缓存列为**长文本与 RAG 场景**的加分项【Source-derived · S4c】——RAG 里被反复检索命中的那段文档上下文，正是可以共享的前缀。

---

## 本节小结

- **PagedAttention**：用固定大小的块管理 KV Cache，靠块表把逻辑序列映射到散布的物理块上，消除碎片【S3a / R5】。
- **Continuous Batching**：每个推理步重新组批，请求完成即腾位给新请求【S3b】。
- **两者是耦合的**：分页负责"腾得出空间"，连续批处理负责"空间不闲置"【S3b】。
- **前缀缓存**是分页的衍生能力，基于哈希的块匹配，**V1 默认开启**，并支持用 salt 做信任组隔离【R6 / R15】。
- 末块浪费是分页下唯一的浪费来源；<4% 是系统级均值，单条短请求可高得多【R5 / R7】。

**下一步** → [03 · 核心功能：能力与边界](03-core-functionality.md)
