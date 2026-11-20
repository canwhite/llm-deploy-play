# 05 相关工具

## 学习目标

按源文的两个比较层面说出选择条件，并识别未核验比较。

## 通用推理框架层面

源文把 TensorRT、ONNX Runtime、OpenVINO 放在“在哪种硬件运行推理”的层面比较：TensorRT 对 NVIDIA GPU；ONNX Runtime 强调跨平台 Execution Provider；OpenVINO 对 Intel 硬件。 [Source-derived: S23](07-verification-record.md#s23)

源文选型规则：锁定 NVIDIA GPU 且追求极限推理性能时选 TensorRT；多硬件场景考虑 ONNX Runtime；Intel CPU/iGPU 场景考虑 OpenVINO。 [Source-derived: S24](07-verification-record.md#s24)

这些是源文观点，未接受外部研究来确认版本、性能或兼容性细节。 [Evidence gap: G4](07-verification-record.md#g4)

## LLM 推理层面

源文把 TensorRT-LLM 描述为 TensorRT 的 LLM 专用延伸，并与 vLLM、SGLang 比较；其中 30%—50% 吞吐与 1—2 周搭建周期等数字未获外部证据确认，课程不将其作为事实教学。 [Source-derived: S25](07-verification-record.md#s25) [Evidence gap: G5](07-verification-record.md#g5)

**Illustrative 示例：** 若团队必须同时服务不同硬件，先把硬件覆盖列为约束，再按已验证的兼容性资料做选型；本例不推荐特定工具。

下一节：[学习路径](06-learning-path.md)，所有定位依据见[验证记录](07-verification-record.md)。
