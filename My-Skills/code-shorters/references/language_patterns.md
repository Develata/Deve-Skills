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
class Database:
    pass
```

```python
if __name__ == "__main__":
    print(main())
```

---

### C++

**文件后缀**: `.cpp`, `.h`, `.hpp`

**一级检测**：通过文件扩展名 `.cpp`, `.h`, `.hpp` 立即识别为 C++。

**二级检测**：至少匹配以下 1 个特征

```cpp
#include <vector>
```

```cpp
namespace MyLib {
    class Container {
    std::vector<int> items;
    };
}
```

```cpp
template <typename T>
class Template {
public:
    void process(T item);
};
```

---

### JavaScript / TypeScript

**文件后缀**: `.js`, `.ts`, `.jsx`, `.tsx`

**一级检测**：通过文件扩展名 `.js`, `.ts`, `.jsx`, `.tsx` 立即识别为 JavaScript/TypeScript。

**二级检测**：至少匹配以下 1 个特征

```javascript
function processData(data) {
    return data.map(item => item.value);
}
```

```javascript
const API_URL = 'https://api.example.com';
```

```javascript
export default function App() {
    return <div>App</div>;
}
```

```javascript
const reducer = (state, action) => {
    return { ...state, ...action };
};
```

---

### Markdown

**文件后缀**: `.md`

**一级检测**：通过文件扩展名 `.md` 立即识别为 Markdown。

**二级检测**：至少匹配以下 1 个特征

```markdown
# 标题 1

## 标题 2

内容...
```

```markdown
[链接文本](https://example.com)
```

```markdown
![图片描述](image.png)
```

```markdown
> 引用块

这是引用内容
```

---

## 不支持的语言

如果文件后缀不在支持列表中，或者文件内容特征不匹配任何已知模式，则返回 `unknown`。
