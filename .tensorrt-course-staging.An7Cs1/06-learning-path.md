# 06 学习路径

## 学习目标

形成从概念到可观察检查的短路径，且不把未验证能力当作完成标准。

1. 阅读[定位与背景](01-positioning-and-background.md)：说出部署阶段与硬件取舍。 [Source-derived: S1](07-verification-record.md#s1)
2. 阅读[核心概念](02-core-concepts.md)：画出 Builder→Engine→ExecutionContext，并标注 Plugin 的扩展位置。 [Source-derived: S5](07-verification-record.md#s5)
3. 阅读[核心功能](03-core-functionality.md)：将优化项与边界成对记录。 [Source-derived: S11](07-verification-record.md#s11)
4. 阅读[使用](04-usage.md)：按 ONNX→Engine→Runtime 复述输入与产物。 [Source-derived: S18](07-verification-record.md#s18)
5. 阅读[相关工具](05-related-tools.md)：写下硬件、模型稳定性、构建预算三个待核验约束；后两项来自源文的选型描述。 [Source-derived: S3](07-verification-record.md#s3)

**Illustrative 练习：** 选一个假想部署需求，填“目标 GPU、输入尺寸、精度、是否有不支持算子”；将每项标为“已知”或“待验证”。不执行命令、不推断兼容性。

完成标准：能链接每个课程事实到[验证记录](07-verification-record.md)，并明确 G1–G5 仍未解决。 [Evidence gap: G1](07-verification-record.md#g1)
