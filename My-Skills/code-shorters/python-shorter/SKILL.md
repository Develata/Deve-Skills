---
name: python-shorter
description: Python 代码模块化工具。用于将超过130行的 Python 代码文件拆分为符合"130行铁律"的模块化结构。支持按类模块、按功能分组、按数据流三种重构策略。保持原有代码逻辑不变。
---

# Python Shorter (Python 代码精简器)

自动化 Python 代码模块化重构工具。

## 触发时机

当 `code-shorters` 主 Skill 调用此 Skill 时触发。

## 重构策略

支持三种重构策略，按需选择。

### 用法

```bash
python scripts/python_modularizer.py <file_path> --strategy <strategy>
```

### 策略选项

- `class` - 按类模块拆分（推荐）
- `functional` - 按功能分组
- `dataflow` - 按数据流拆分

## 参考文档

详见 `references/` 目录。
