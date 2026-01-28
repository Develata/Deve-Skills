# 语言检测模式

本文档定义各编程语言的检测规则和特征模式。

## 检测机制

code-shorters 使用**多层级语言检测**机制：

### 一级检测：文件后缀名（快速过滤）
### 二级检测：文件内容特征（准确分类）

---

## 支持的语言

### Rust

**文件后缀**: `.rs`

**一级检测**：通过文件扩展名 `.rs` 立即识别为 Rust。

**二级检测**：至少匹配以下 1 个特征

```rust
use std::collections::HashMap;
```

```rust
fn main() {
    let data = HashMap::new();
}
```

```rust
pub struct Config {
    debug: bool,
}
```

```rust
impl Config {
    fn new() -> Self { Config { debug: false } }
}
```

---

### Python

**文件后缀**: `.py`

**一级检测**：通过文件扩展名 `.py` 立即识别为 Python。

**二级检测**：至少匹配以下 1 个特征

```python
import sys
from typing import List
```

```python
def main() -> int:
    return 0
```

```python
