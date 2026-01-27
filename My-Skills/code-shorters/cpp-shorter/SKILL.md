---
name: cpp-shorter
description: C++代码模块化工具。用于将超过130行的C++代码文件拆分为符合"130行铁律"的模块化结构。支持按头文件分离、按命名空间、按模板类三种重构策略。保持原有代码逻辑不变。
---

# C++ Shorter (C++代码精简器)

自动化 C++ 代码模块化重构工具。

## 触发时机

当 `code-shorters` 主 Skill 调用此 Skill 时触发。

## 重构策略

支持三种重构策略，按需选择。

### 用法

```bash
python scripts/cpp_modularizer.py <file_path> --strategy <strategy>
```

### 策略选项

- `headers` - 按头文件分离（推荐）
- `namespace` - 按命名空间拆分
- `templates` - 按模板类拆分

## 参考文档

详见 `references/` 目录。
