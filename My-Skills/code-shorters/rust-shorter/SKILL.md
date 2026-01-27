---
name: rust-shorter
description: Rust 代码模块化工具。用于将超过130行的 Rust 代码文件拆分为符合"130行铁律"的模块化结构。支持按功能模块、按数据流、按依赖层级三种重构策略。保持原有代码逻辑不变。
---

# Rust Shorter (Rust 代码精简器)

自动化 Rust 代码模块化重构工具。

## 触发时机

当 `code-shorters` 主 Skill 调用此 Skill 时触发。

## 重构策略

支持三种重构策略，按需选择。

### 用法

```bash
python scripts/rust_modularizer.py <file_path> --strategy <strategy>
```

### 策略选项

- `functional` - 按功能模块拆分（推荐）
- `dataflow` - 按数据流拆分
- `hierarchical` - 按依赖层级拆分

## 参考文档

详见 `references/` 目录。
