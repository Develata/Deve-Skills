# C++ Modularization Rules

Split by declarations:
- Split along `class`, `struct`, `namespace`, and `template` declarations.
- Keep headers under 130 lines; move implementations to `.cpp` files.
- Avoid cyclic includes by forward declarations where possible.
