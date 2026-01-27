# Python Modularization Rules

Split by semantic units:
- Prefer splitting by `class` and then by top-level `def` functions.
- Keep shared utilities in a `utils.py` module.
- Avoid circular imports by using `__init__.py` exports.
