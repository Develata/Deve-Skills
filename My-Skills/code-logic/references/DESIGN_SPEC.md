# Code-Logic Skill: The Perfect Logic Analyzer (Design Spec)

> "To see the code not as text, but as a manifold of logic flows."

## 1. 核心理念 (Core Philosophy)

本 Skill 旨在为代码逻辑提供**无懈可击 (Unassailable)** 的分析与可视化。
我们拒绝模糊的正则匹配，坚持使用 **AST (Abstract Syntax Tree)** 进行精确解析，并将代码映射为 **通用逻辑图 (Universal Logic Graph, ULG)**。

### 公理 (Axioms)
1.  **无损性 (Losslessness)**: 源码中所有的控制流变更（Branching, Jumping, Returning, Panicking）必须在图中有对应的边。
2.  **显式化 (Explicitness)**: 隐式控制流（如 Rust 的 `?` 操作符、`Deref` 转换、隐式 Drop）若影响逻辑路径，必须转译为显式节点。
3.  **同构性 (Isomorphism)**: 输出的 "AI Logic DSL" 与 "SVG Visualization" 必须是同一拓扑结构的不同投影。

---

## 2. 架构设计 (Architecture)

系统采用典型的编译器前端架构，分为三层：

```mermaid
graph TD
    Source[Source Code] -->|Tree-sitter| AST[Raw AST]
    AST -->|Transformer| ULG[Universal Logic Graph (IR)]
    ULG -->|Renderer A| DSL[Logic DSL (S-Expr)]
    ULG -->|Renderer B| DOT[Graphviz DOT]
    DOT -->|Graphviz| SVG[Visualization]
```

### 2.1 目录结构
遵循 130 行/文件模块化铁律。

```text
My-Skills/code-logic/
├── SKILL.md                 # 接口定义
├── scripts/
│   ├── main.py              # CLI 入口
│   ├── requirements.txt     # 依赖锁定
│   ├── ast_engine.py        # 语法层：Tree-sitter 封装
│   ├── ir_graph.py          # 语义层：ULG 节点与图结构定义
│   ├── cfg_rust_core.py     # 转换层：Rust 构建器入口与调度
│   ├── cfg_rust_stmt.py     # 转换层：语句处理 Mixin (let, ?, macro)
│   ├── cfg_rust_flow.py     # 转换层：控制流 Mixin (match, loop, if)
│   ├── cfg_python_core.py   # 转换层：Python 构建器入口与调度
│   ├── cfg_python_stmt.py   # 转换层：Python 语句 Mixin (try, with)
│   ├── cfg_python_flow.py   # 转换层：Python 控制流 Mixin (if, for)
│   ├── renderer_dsl.py      # 输出层：S-Expr 生成器
│   └── renderer_dot.py      # 输出层：DOT 生成器
└── references/
    ├── DESIGN_SPEC.md       # 本文档
    └── logic_dsl.md         # DSL 语法详述
```

---

## 3. 通用逻辑图 (ULG) 定义

ULG 是一个有向图 `G = (V, E)`。

### 3.1 节点类型 (Nodes)
在 Python (`ir_graph.py`) 中表现为 `dataclass`。

| 类型 | 描述 | 视觉表现 (Graphviz) |
| :--- | :--- | :--- |
| **Block** | 顺序执行的原子语句集 | 矩形 (Box) |
| **Fork** | 控制流分岔点 (`if`, `match`) | 菱形 (Diamond) |
| **Join** | 控制流汇合点 | 小圆点 (Point) |
| **Call** | 函数调用 (可能有副作用) | 椭圆 (Ellipse) |
| **Virtual** | 隐式逻辑节点 (如 `?` 拆解) | 虚线框或特定图标 |
| **Exit** | 终止节点 (`return`, `panic`) | 双圆 (DoubleCircle) |

### 3.2 边类型 (Edges)

| 类型 | 描述 | 视觉表现 (Graphviz) |
| :--- | :--- | :--- |
| **Seq** | 顺序流 (Sequential) | 黑色实线 |
| **Cond(True)** | 条件成立/Match Arm | 绿色实线 |
| **Cond(False)** | 条件失败/Default | 橙色实线 |
| **Err/Panic** | 错误传播/异常 | 红色虚线 |
| **Jump** | 循环回溯 (`continue`) | 灰色曲线 |

---

## 4. 语言特性映射策略 (Mapping Strategy)

### 4.1 Rust: `match` 表达式
```rust
match x {
    A => block_a,
    B => block_b,
}
```
*   **ULG 转换**:
    *   Node: `Fork(Label="match x")`
    *   Edge 1: `Cond(Label="A")` -> Node: `Block(block_a)`
    *   Edge 2: `Cond(Label="B")` -> Node: `Block(block_b)`
    *   Join: 所有 Block 汇聚到一个 `Join` 节点。

### 4.2 Rust: `?` 操作符 (Try Operator)
```rust
let y = func(x)?;
```
*   **ULG 转换**:
    *   Node: `Call(func)`
    *   Node: `Virtual(Label="?")` (作为 Call 的直接后继)
    *   Edge 1: `Seq(Ok)` -> 下一条语句
    *   Edge 2: `Err(Error)` -> 函数级 `Exit(Error)` 节点

### 4.3 Python: `try/except`
```python
try:
    do_something()
except ValueError:
    handle_error()
```
*   **ULG 转换**:
    *   Node: `Virtual(Label="try scope")`
    *   Edge 1: `Seq` -> Node: `Block(do_something)`
    *   Edge 2: `Err(Label="Ex")` -> Node: `Block(handle_error)`
    *   Join: 汇聚到 `end try` 节点。

---

## 5. 输出格式规范

### 5.1 Logic DSL (AI Readable)
采用 Lisp 风格 S-Expression。

```lisp
(def-flow "calculate_stuff"
  (args (a:i32) (b:i32))
  (flow
    (block :id 1
      (let x (+ a b)))
    (branch :cause "check_overflow"
      (cond (> x 100)
        (then (return (err "overflow")))
        (else (call "save_to_db" x))))
    (return (ok x))))
```

### 5.2 Graphviz DOT (Human Readable)
*   必须使用 `rankdir=TB` (Top to Bottom)。
*   必须使用 `splines=ortho` 或 `splines=curved` 保证连线美观。
*   Panic/Error 路径必须强制着色为 `red`。

---

## 6. 实施路线图 (Roadmap)

1.  **Infrastructure**: 配置 `tree-sitter` 环境。
2.  **Core Logic**: 实现 `ir_graph.py` 定义数据结构。
3.  **Parser**: 实现 `ast_engine.py` 加载 Rust 和 Python 语法。
4.  **Rust Mapper**: 开发 `cfg_rust_*.py` 模块。
5.  **Python Mapper**: 开发 `cfg_python_*.py` 模块。
6.  **Renderers**: 实现 `renderer_dot` 和 `renderer_dsl`。
7.  **Verification**: 自测复杂代码逻辑。

此计划为绝对准则，代码实现必须严格遵循上述定义。
