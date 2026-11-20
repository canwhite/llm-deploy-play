# 03 核心功能

## 学习目标

能列出 Build 阶段优化及其已知限制，不把它们当成无条件承诺。

## Build 优化

源文将 Build 阶段的优化描述为“不可逆、面向目标 GPU”；这表示 Engine 是针对当次构建配置产出的专用结果，不表示模型或部署配置不能通过重新构建来调整。 [Source-derived: S11](07-verification-record.md#s11) [Source-derived: S22](07-verification-record.md#s22)

- 图优化与层融合：合并冗余算子、消除无用层、融合细碎操作。 [Source-derived: S10](07-verification-record.md#s10)
- 精度量化：源文列出 FP32、FP16、BF16、FP8、INT8；INT8 需要校准数据。 [Source-derived: S12](07-verification-record.md#s12)
- 内核自动调优：针对目标 GPU 型号和输入尺寸实测多种 CUDA 内核实现，选最快者固化到 Engine。 [Source-derived: S13](07-verification-record.md#s13)
- 动态张量内存管理：分析生命周期，按需分配并复用显存。 [Source-derived: S14](07-verification-record.md#s14)

## 已知边界

Engine 针对构建时 GPU 架构优化，换卡通常需要重建。 [Source-derived: S15](07-verification-record.md#s15)

源文称 Optimization Profile 支持有限范围动态维度；完全动态 Shape 或依赖 Shape 的算子仍可能不支持，或需显式指定范围。版本、具体 API 与适用条件未获外部证据确认。 [Source-derived: S16](07-verification-record.md#s16) [Evidence gap: G1](07-verification-record.md#g1)

不支持的 ONNX 算子需要 C++ Plugin；TensorRT 不用于训练。 [Source-derived: S17](07-verification-record.md#s17)

**Illustrative 示例：** 若输入尺寸从已构建配置改为另一关键尺寸，应把“是否重建”作为待验证问题，而非假定旧 Engine 可用。

下一节：[使用流程](04-usage.md)。
