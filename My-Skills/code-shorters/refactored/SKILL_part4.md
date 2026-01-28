## 工作流程

### 步骤 1：Git 环境检查

首先验证 Git 仓库状态，确保版本安全：

```bash
# 执行 Git 检查
python scripts/git_checker.py
```

**检查规则**：
1. 当前目录必须是 Git 仓库（检测 `.git` 目录）
2. 不能有未提交的修改（`git status --porcelain` 检测）
3. 未通过检查则**立即退出**，不执行任何修改

### 步骤 2：递归扫描目录

扫描指定目录（默认当前目录），识别所有代码文件：

```bash
# 执行扫描
python scripts/main_analyzer.py --path . --recursive
```

**扫描支持的语言后缀**：
- Rust: `.rs`
- Python: `.py`
- C++: `.cpp`, `.h`, `.hpp`
- JavaScript/TypeScript: `.js`, `.ts`, `.jsx`, `.tsx`
- Markdown: `.md`

### 步骤 3：行数统计（包含注释）

计算每个文件的总行数，**包含注释行和代码行**：

**语言特定注释规则**：
- Rust: `//`, `/* */`
- Python: `#`, `"""""`
- C++: `//`, `/* */`
- JS: `//`, `/* */`
- MD: `<!-- -->`

### 步骤 4：复杂度检测与优先级排序

集成多语言 lint 工具计算复杂度：

| 语言 | Lint 工具 | 命令 |
|------|-----------|-------|
| Rust | cargo clippy | `cargo clippy --message-format=json` |
| Python | pylint | `pylint --output-format=json` |
| C++ | cpplint | `cpplint --output-format=json5` |
| JavaScript | eslint | `eslint --format=json` |

**优先级评分公式**：
```
Priority Score = (行数 × 0.4) + (复杂度 × 0.3) + (嵌套深度 × 0.2) + (函数数量 × 0.1)
```

### 步骤 5：生成分类报告

生成 JSON 格式的分类报告：

```json
{
  "warning_files": [
    {"path": "src/parser.rs", "language": "rust", "lines": 145, "priority": 58.0},
    {"path": "lib/database.rs", "language": "rust", "lines": 189, "priority": 75.6}
  ],
  "critical_files": [
    {"path": "src/main.rs", "language": "rust", "lines": 320, "priority": 128.0},
    {"path": "server/handler.rs", "language": "rust", "lines": 412, "priority": 164.8}
  ],
  "statistics": {
    "total_files": 5,
    "warning_count": 2,
    "critical_count": 2
  }
}
```

### 步骤 6：自动串行调用子 Skill

按照优先级顺序，自动调用对应的语言专项子skill：

```bash
# 批处理模式（方案 B）
python scripts/batch_refactor.py
```

