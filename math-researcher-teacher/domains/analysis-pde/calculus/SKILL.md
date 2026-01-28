# Calculus & Mathematical Analysis

**Path**: `math-researcher-teacher/domains/analysis-pde/calculus/`

## 🔬 Core Capabilities

Provides rigorous symbolic computation for mathematical analysis using SymPy.

### 1. Limits & Continuity
*   Rigorous limit calculation ($\epsilon-\delta$ verification support via SymPy logic).
*   Asymptotic expansion (Taylor/Laurent series).

### 2. Differentiation & Integration
*   Symbolic derivatives (including partials).
*   Definite and improper integrals.

## 💻 Python Tools

**`symbolic_calc.py`**:
*   `calculate_limit(expr, var, point)`
*   `calculate_derivative(expr, var)`
*   `calculate_integral(expr, var, [lower, upper])`

## 🔗 Related Domains
*   **Differential Equations**: See `domains/analysis-pde/differential-equations` for ODE/PDE solvers.
*   **Complex Analysis**: See `domains/analysis-pde/real-complex` for contour integrals.
