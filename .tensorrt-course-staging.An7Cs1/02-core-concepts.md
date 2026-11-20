# 02 核心概念

## 学习目标

能区分两阶段模型与四个核心对象。

## 两阶段心智模型

Build 是离线、耗时阶段，产出 Engine；Runtime 是在线执行阶段，加载 Engine 做推理。 [Source-derived: S5](07-verification-record.md#s5)

| 对象 | 作用 |
|---|---|
| Builder | 解析模型、做图优化/精度校准/内核选择，并构建 Engine。 [Source-derived: S6](07-verification-record.md#s6) |
| Engine（plan） | 序列化、硬件绑定的优化模型，含目标 GPU 的内核与权重。 [Source-derived: S7](07-verification-record.md#s7) |
| ExecutionContext | 从 Engine 创建，管理推理中间状态与显存缓冲；每线程需要独立 Context。 [Source-derived: S8](07-verification-record.md#s8) |
| Plugin | 原生不支持算子时可注入的 C++ 自定义实现机制。 [Source-derived: S9](07-verification-record.md#s9) |

**Source-derived 示例：** `Conv → Bias → ReLU` 可在图优化中融合为一个内核，用于减少启动开销和显存往返。 [Source-derived: S10](07-verification-record.md#s10)

术语会在[核心功能](03-core-functionality.md)继续使用；流程见[使用](04-usage.md)。
