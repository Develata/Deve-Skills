---
name: code-logic
description: A rigorous code logic analyzer that converts source code (currently Rust) into a Universal Logic Graph (ULG). It outputs both an AI-optimized Logic DSL (S-Expression) and a human-readable Graphviz SVG visualization. Use this when you need "unassailable" understanding of control flow, including implicit paths like Rust's `?` operator or `match` exhaustiveness.
---

# Code Logic Analyzer

此 Skill 用于生成代码的深度逻辑可视化与结构化文本。
它不依赖正则，而是基于 AST 进行完整的控制流分析 (CFG)。

## Use Cases

*   **Deep Audit**: 当需要通过视觉确认代码是否存在逻辑漏洞（如未处理的 Error 分支）时。
*   **Documentation**: 为复杂的算法生成永久性的逻辑架构图。
*   **AI Context**: 为 LLM 提供不含噪音的纯逻辑 DSL，提升代码理解准确度。

## Usage

```bash
# 基本用法：分析单个文件
python scripts/main.py --file /path/to/source.rs

# 指定输出格式 (默认为 both)
python scripts/main.py --file /path/to/source.rs --format svg
python scripts/main.py --file /path/to/source.rs --format dsl

# 仅解析函数名为 foo 的逻辑
python scripts/main.py --file /path/to/source.rs --focus foo
```

## Outputs

运行后，将在源文件同级目录下生成：
*   `filename.logic.svg`: 高精度矢量逻辑图。
*   `filename.logic.lisp`: 供 AI 阅读的 S-Expression 逻辑描述。

## Dependencies

*   Python 3.8+
*   GCC (for compiling tree-sitter languages)
*   Graphviz (must be installed in system PATH for SVG generation)
