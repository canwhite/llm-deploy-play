# 04 使用

## 学习目标

能复述源文给出的最小流程，并知道哪些结果必须在本地验证。

## 三步流程

1. 从 PyTorch/TensorFlow 导出 ONNX；源文称 ONNX 是 TensorRT 最主流输入入口。 [Source-derived: S18](07-verification-record.md#s18)
2. 用 `trtexec` 或 Python/C++ Builder API 将 ONNX 构建为 Engine。 [Source-derived: S19](07-verification-record.md#s19)
3. 应用加载 `.engine`，创建 ExecutionContext，分配输入/输出显存并调用推理接口。 [Source-derived: S20](07-verification-record.md#s20)

**Source-derived 示例：**

```bash
trtexec --onnx=model.onnx --saveEngine=model.engine --fp16
```

该命令仅为源文示例；本课程未执行它，也不宣称其在任何版本/机器上的输出。 [Source-derived: S21](07-verification-record.md#s21) [Evidence gap: G2](07-verification-record.md#g2)

模型结构、精度或输入尺寸变化时，源文称 Engine 通常需要重新构建。 [Source-derived: S22](07-verification-record.md#s22)

## 完成检查

观察到：ONNX 输入、生成的 Engine、可创建的 Context、一次应用侧推理调用。具体命令、日志和性能阈值均未由来源给出，须另行验证。 [Evidence gap: G3](07-verification-record.md#g3)

相关取舍见[相关工具](05-related-tools.md)；证据见[验证记录](07-verification-record.md)。
