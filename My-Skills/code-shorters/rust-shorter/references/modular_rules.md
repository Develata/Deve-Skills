# Rust Modularization Rules

Use semantic boundaries before chunking:
- Split by `struct`, `enum`, `impl`, and top-level `fn` blocks.
- Keep public interfaces in a small `mod.rs` or `lib.rs` when possible.
- Prefer references over clones for low-memory environments.
