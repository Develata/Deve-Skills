## 配置选项

### 扫描配置

```bash
--path <directory>        # 指定扫描路径（默认当前目录）
--recursive              # 递归扫描子目录
--exclude <pattern>      # 排除文件/目录
--include-only <lang>    # 只扫描指定语言
```

### 复杂度配置

```bash
--no-complexity          # 跳过复杂度检测
--linter-path <path>     # 指定 lint 工具路径
```

### 输出配置

```bash
--output-dir <directory>  # 输出报告目录
--report-format <format>  # 报告格式：markdown 或 html
```

