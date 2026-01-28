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
