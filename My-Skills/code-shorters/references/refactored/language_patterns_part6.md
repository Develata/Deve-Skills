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
