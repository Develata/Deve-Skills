---
name: md-shorter
description: Markdown文档模块化工具。用于将超过130行的Markdown文档拆分为符合"130行铁律"的模块化结构。支持按章节、按主题、按内容类型三种重构策略。保持原有内容逻辑不变。自动更新内部链接和目录。
---

# MD Shorter (Markdown文档精简器)

自动化 Markdown 文档模块化重构工具。

## 触发时机

当 `code-shorters` 主 Skill 调用此 Skill 时触发。

## 重构策略

支持三种重构策略，按需选择。

### 用法

```bash
python scripts/md_modularizer.py <file_path> --strategy <strategy>
```

### 策略选项

- `chapter` - 按章节拆分（推荐）
- `topic` - 按主题拆分
- `content` - 按内容类型拆分

## 参考文档

详见 `references/` 目录。
