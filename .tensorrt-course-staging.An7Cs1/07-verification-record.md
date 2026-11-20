# 07 验证记录

## 范围与来源

- 只读来源：`/Users/doing/Desktop/llm-deploy-play/source-tensorRT.md`
- 来源 SHA-256：`9cf9784aa95729c30042cba560cc2ee720f7cf812e539511057a6be856e6db7c`
- 外部研究：未接受。以下 NVIDIA 文档检索尝试均于 2026-11-19 返回 HTTP 404，因而没有可接受外部引文：
  - 动态 Shape：`https://docs.nvidia.com/deeplearning/tensorrt/latest/inference-library/work-dynamic-shapes.html`
  - `trtexec`：`https://docs.nvidia.com/deeplearning/tensorrt/latest/reference/command-line-programs.html`
  - capabilities：`https://docs.nvidia.com/deeplearning/tensorrt/latest/architecture/capabilities.html`
  - plugins：`https://docs.nvidia.com/deeplearning/tensorrt/latest/inference-library/extending.html`
  这些 URL 仅记录检索失败，不构成技术事实证据。
- 课程文件：仅本 staging 内 `01` 至 `07`；见 `manifest.sha256`。

## 证据映射

| ID | 来源标题与行 | 影响章节 |
|---|---|---|
| <a id="s1"></a>S1 | “定位” L3–7 | [01](01-positioning-and-background.md), [06](06-learning-path.md) |
| <a id="s2"></a>S2 | “定位” L3–7 | [01](01-positioning-and-background.md) |
| <a id="s3"></a>S3 | “同类比较” L60–84 | [01](01-positioning-and-background.md), [06](06-learning-path.md) |
| <a id="s4"></a>S4 | “核心概念” L9–20；“边界” L50–58 | [01](01-positioning-and-background.md) |
| <a id="s5"></a>S5 | “核心概念” L9–13 | [02](02-core-concepts.md), [06](06-learning-path.md) |
| <a id="s6"></a>S6 | “核心概念” L15–20 | [02](02-core-concepts.md) |
| <a id="s7"></a>S7 | “核心概念” L15–20 | [02](02-core-concepts.md) |
| <a id="s8"></a>S8 | “核心概念” L15–20 | [02](02-core-concepts.md) |
| <a id="s9"></a>S9 | “核心概念” L15–20 | [02](02-core-concepts.md) |
| <a id="s10"></a>S10 | “核心功能” L22–29 | [02](02-core-concepts.md), [03](03-core-functionality.md) |
| <a id="s11"></a>S11 | “核心功能” L22–24 | [03](03-core-functionality.md), [06](06-learning-path.md) |
| <a id="s12"></a>S12 | “核心功能” L26–27 | [03](03-core-functionality.md) |
| <a id="s13"></a>S13 | “核心功能” L28 | [03](03-core-functionality.md) |
| <a id="s14"></a>S14 | “核心功能” L29 | [03](03-core-functionality.md) |
| <a id="s15"></a>S15 | “边界” L50–57 | [03](03-core-functionality.md) |
| <a id="s16"></a>S16 | “边界” L54–55 | [03](03-core-functionality.md) |
| <a id="s17"></a>S17 | “边界” L56–58 | [03](03-core-functionality.md) |
| <a id="s18"></a>S18 | “使用方法” L31–36 | [04](04-usage.md), [06](06-learning-path.md) |
| <a id="s19"></a>S19 | “使用方法” L38–45 | [04](04-usage.md) |
| <a id="s20"></a>S20 | “使用方法” L47–48 | [04](04-usage.md) |
| <a id="s21"></a>S21 | “使用方法” L38–43 | [04](04-usage.md) |
| <a id="s22"></a>S22 | “使用方法” L45 | [04](04-usage.md) |
| <a id="s23"></a>S23 | “同类比较” L64–74 | [05](05-related-tools.md) |
| <a id="s24"></a>S24 | “同类比较” L74 | [05](05-related-tools.md) |
| <a id="s25"></a>S25 | “LLM 推理引擎” L76–84 | [05](05-related-tools.md) |

## 证据缺口与未决问题

| ID | 缺口 | 影响章节 | 未决问题 |
|---|---|---|---|
| <a id="g1"></a>G1 | NVIDIA 动态 Shape 文档 404 | [03](03-core-functionality.md) | Optimization Profile 的版本/API/支持范围？ |
| <a id="g2"></a>G2 | NVIDIA `trtexec` 文档 404 | [04](04-usage.md) | 示例参数、产物、错误行为是否适用于目标版本？ |
| <a id="g3"></a>G3 | 源未给出可重复运行验收数据 | [04](04-usage.md) | 应使用何种模型、设备、日志和阈值？ |
| <a id="g4"></a>G4 | capabilities 官方资料 404 | [05](05-related-tools.md) | 各框架当前硬件/Execution Provider 支持矩阵？ |
| <a id="g5"></a>G5 | plugins/LLM 性能资料未获接受 | [05](05-related-tools.md) | 性能数字与周期的测试条件、版本、负载？ |

## 链接检查入口

验证映射所列每个章节链接：
[01](01-positioning-and-background.md) · [02](02-core-concepts.md) · [03](03-core-functionality.md) · [04](04-usage.md) · [05](05-related-tools.md) · [06](06-learning-path.md) · [07](07-verification-record.md)

## 审计记录

- 审计范围：本 staging 内 01–07 与 `manifest.sha256`；模式为 review-only，未修改来源或目标目录。
- 每节审计：01、02、03 与全套审计已完成；其余分节审计被运行环境取消，未将取消视为通过。全套审计覆盖了全部七节，用于补齐该检查。
- 跨节一致性：已检查术语、来源标签、S1–S25 / G1–G5 锚点与本地链接；未发现不一致。
- 有效发现与编辑：将“不可逆”改写为不排除重新构建的表述；补入四个返回 404 的检索 URL；原先两项关于 S8/S16 行范围不足的发现，经对来源实际 1-based 行号复核后不成立（S8 为 L15–20，S16 为 L54–55）。
- 清单：审计后重算 `manifest.sha256`；发布前已再次验证。
- 发布/晋升：已将本次清单中获授权创建的 `01-positioning-and-background.md` 至 `07-verification-record.md` 发布至 `/Users/doing/Desktop/llm-deploy-play/course/`。暂存目录 `/Users/doing/Desktop/llm-deploy-play/.tensorrt-course-staging.An7Cs1` 保留为可追溯审计材料。
