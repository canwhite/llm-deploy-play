#!/usr/bin/env python3
"""Rebuild sections 7.1 + 7.2 of 07-verification-record.md from the source.

Idempotent: the "影响的课程章节" column is left empty here and is
regenerated mechanically by check_course.py --fix-column.

Usage: python3 build_07_head.py <staging_dir> <source.md>
"""
import os
import subprocess
import sys

staging = sys.argv[1]
source = sys.argv[2]
rows = subprocess.run(
    ["python3", os.path.join(staging, "extract_s.py"), source,
     os.path.join(staging, "s_table.json")],
    capture_output=True, text=True, check=True,
).stdout.rstrip("\n")

HEAD = '''# 07 · 验证记录

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

摘录中的 `……` 表示省略了中间内容；`\\|` 表示原文表格中的竖线转义。

| 定位码 | 源标题 | 行范围 | 摘录（节选） | 影响的课程章节 |
|---|---|---|---|---|
'''

TAIL = '''
> **摘录可还原性**：上表全部摘录由脚本 `extract_s.py` 直接从 `source-sglang.md` 按「行范围」机械抽取生成，未经人工改写，因此可以逐条回源核对。
'''

out = os.path.join(staging, "07-verification-record.md")
open(out, "w", encoding="utf-8").write(HEAD + rows + TAIL)
print(f"07 head rebuilt: {out}")
