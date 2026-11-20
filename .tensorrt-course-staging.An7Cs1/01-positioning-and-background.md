# 01 定位与背景

## 学习目标

能说明 TensorRT 所处生命周期阶段，以及它用什么代价换取什么目标。

## 定位

TensorRT 面向 NVIDIA GPU，可概括为“推理编译器 + 运行时”。它通常接收经 ONNX 转换的训练模型，生成针对目标 GPU 优化的引擎；以跨平台通用性换取该 GPU 上的推理效率。 [Source-derived: S1](07-verification-record.md#s1)

它位于模型部署而非训练阶段：训练框架优先灵活性，TensorRT 为一次前向推理生成高效执行计划。 [Source-derived: S2](07-verification-record.md#s2)

## 面向谁

适合硬件已锁定 NVIDIA GPU、模型进入部署、且愿意承担构建期开销的工程场景。该判断来自源文的选型逻辑与边界，非通用保证。 [Source-derived: S3](07-verification-record.md#s3)

## 结果预览

完成本课程后，应能区分 Build 与 Runtime，读懂 ONNX→Engine→Runtime 流程，并识别硬件绑定、动态 Shape、插件与迭代成本边界。 [Source-derived: S4](07-verification-record.md#s4)

**Illustrative 示例：** 把训练模型比作通用设计图，把 Engine 比作按目标机器加工后的零件；此比喻不主张额外兼容性或性能结论。

下一节：[核心概念](02-core-concepts.md)。证据索引见[验证记录](07-verification-record.md)。
