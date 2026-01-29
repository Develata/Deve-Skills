# Logic DSL Specification

The Logic DSL is a Lisp-inspired S-Expression format designed for high-density, low-ambiguity representation of control flow graphs. It is optimized for LLM consumption.

## Syntax

```lisp
(flow-graph :name "string"
  (nodes
    (node_type :id node_id :label "string" ...props)
    ...
  )
  (edges
    (edge_type source_id -> target_id :label "string")
    ...
  )
)
```

## Node Types

| Type | Description |
| :--- | :--- |
| `block` | A sequence of non-branching statements. |
| `fork` | A branching point (if, match, switch). |
| `join` | A convergence point where branches merge. |
| `call` | A function call or context entry. |
| `virtual` | A logical construct not present in source (e.g., implicit scopes). |
| `exit` | Terminal point (return, panic, throw). |

## Edge Types

| Type | Description |
| :--- | :--- |
| `seq` | Sequential flow (normal execution). |
| `cond_true` | True branch of a condition. |
| `cond_false` | False branch of a condition. |
| `err` | Exception or error path. |
| `jump` | Loop back edge or goto. |
| `link` | Cross-file symbolic reference. |

## Example

```lisp
(flow-graph :name "check_user"
  (nodes
    (block :id b1 :label "user = get_user()")
    (fork  :id f1 :label "if user.is_active")
    (virtual :id v1 :label "True")
    (exit  :id e1 :label "return True")
  )
  (edges
    (seq b1 -> f1)
    (cond_true f1 -> v1 :label "True")
    (seq v1 -> e1)
  )
)
```
