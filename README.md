# qlib-code-notes

这个仓库用于整理阅读和使用 [Microsoft Qlib](https://github.com/microsoft/qlib) 时遇到的问题、代码入口和可复用配置片段。

目前它更像是一个轻量笔记库，不是完整教程。每篇笔记应该尽量做到：问题明确、结论先行、代码片段可直接复制、关键判断有源码链接。

## Notes

| File | Topic |
| --- | --- |
| [QA.md](QA.md) | Qlib workflow 使用 MLflow filesystem tracking backend 时出现 deprecation warning 的原因和处理方式 |

## Writing Rules

- 一篇笔记只解决一个具体问题。
- 先写结论，再写原因和可选方案。
- 代码片段优先给最小可运行配置。
- 涉及 Qlib 内部行为时，补上对应源码文件链接。
- 如果只是临时规避 warning，要明确说明它不会修复底层配置。

## Suggested Structure

```text
# Qlib: short problem title

## Problem
## Short Answer
## Recommended Fix
## Alternatives
## Code References
```
