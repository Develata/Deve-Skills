# Rust Error Fix Strategies

This reference guide provides strategies for fixing common Rust compiler errors, particularly those related to ownership, borrowing, and types.

## Borrow Checker Errors

### E0382: Use of Moved Value

**Error**: `borrow of moved value: x`
**Cause**: You tried to use a value after it was moved to another variable or function.
**Strategies**:
1.  **Clone**: If the type implements `Clone`, call `.clone()` before moving.
    ```rust
    let s2 = s1.clone(); // Fix
    ```
2.  **Reference**: If ownership isn't needed, pass a reference.
    ```rust
    fn foo(s: &String) { ... }
    foo(&s1); // Fix
    ```
3.  **Scope**: Ensure the move happens last, or reorder code.

### E0502: Cannot Borrow Mutable and Immutable

**Error**: `cannot borrow x as mutable because it is also borrowed as immutable`
**Cause**: You have an active immutable reference while trying to create a mutable one.
**Strategies**:
1.  **Scope**: End the immutable borrow's scope before the mutable borrow starts.
    ```rust
    {
        let r1 = &x;
        println!("{}", r1);
    } // r1 scope ends
    let r2 = &mut x; // Fix
    ```
2.  **Refactor**: Sometimes you need to split the struct or use interior mutability (`RefCell`, `Mutex`).

### E0597: `x` does not live long enough

**Error**: `x does not live long enough`
**Cause**: You are returning a reference to a value that will be dropped at the end of the scope.
**Strategies**:
1.  **Return Owned**: Return `String` instead of `&str`, or `Vec<T>` instead of `&[T]`.
2.  **Lifetime Parameters**: If the input has a lifetime, ensure the output lifetime matches correctly.
3.  **'static**: If using a string literal, ensure it's truly static or use `String`.

## Type Errors

### E0308: Mismatched Types

**Error**: `expected type X, found type Y`
**Strategies**:
1.  **Conversion**: Use `.into()`, `.as_ref()`, `format!()` etc.
2.  **References**: Check if you need `&` or `*` (dereference).
    - `expected &String, found String` -> `&s`
    - `expected String, found &String` -> `s.clone()` or `s.to_string()`
3.  **Result/Option**: Did you forget to unwrap or handle an error?
    - `expected T, found Result<T, E>` -> `?` operator or `unwrap()`.

## Dependency Errors

### E0432: Unresolved Import

**Error**: `unresolved import` or `use of undeclared crate or module`
**Strategies**:
1.  **Check Cargo.toml**: Ensure the dependency is listed. (Note: The `rust-auto-fixer` tool attempts to auto-detect this based on `use` statements, but may fail for complex macros or qualified paths).
2.  **Correct Name**: Check for typos in crate names.

## General Debugging

- **Read the Note**: The compiler often provides a `help` or `note` section. Pay close attention to these.
- **Minimal Repro**: If stuck, try to isolate the error in a smaller function.
