# Advanced Stochastics

**Path**: `math-researcher-teacher/domains/stochastics/advanced-stochastics/`

## 🔬 Core Topics

### 1. Random Matrix Theory (RMT)
*   **Concepts**: Wigner Matrices, Semicircle Law, Marchenko-Pastur Law, Universality.
*   **Script**: `scripts/rmt_sim.py`
    *   **Usage**: Simulates eigenvalues of large symmetric random matrices.
    *   **Output**: Comparison plot of empirical eigenvalues vs Wigner's Semicircle.

### 2. Large Deviations Principle (LDP)
*   **Concepts**: Rate functions, Cramér's Theorem, Sanov's Theorem, Varadhan's Lemma.
*   **Script**: `scripts/ldp_sim.py`
    *   **Usage**: Simulates sample means of i.i.d. variables.
    *   **Output**: Visualization of probability concentration and empirical rate function approximation.

## 💻 How to use Scripts

**Simulate Random Matrix Eigenvalues:**
```bash
python scripts/rmt_sim.py
```
*Check `wigner_semicircle.png` for the result.*

**Simulate Large Deviations:**
```bash
python scripts/ldp_sim.py
```
*Check `ldp_simulation.png` for the result.*
