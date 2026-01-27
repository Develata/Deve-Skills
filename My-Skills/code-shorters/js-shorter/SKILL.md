---
name: js-shorter
description: JavaScript/TypeScript代码模块化工具。用于将超过130行的JS/TS代码文件拆分为符合"130行铁律"的模块化结构。支持按组件、按路由、按状态管理三种重构策略。保持原有代码逻辑不变。
---

# JS Shorter (JavaScript/TypeScript代码精简器)

自动化 JavaScript/TypeScript 代码模块化重构工具。

## 触发时机

当 `code-shorters` 主 Skill 调用此 Skill 时触发。

## 重构策略

支持三种重构策略，按需选择。

### 用法

```bash
python scripts/js_modularizer.py <file_path> --strategy <strategy>
```

### 策略选项

- `components` - 按组件拆分（推荐）
- `routes` - 按路由拆分
- `state` - 按状态管理拆分

## 参考文档

详见 `references/` 目录。
