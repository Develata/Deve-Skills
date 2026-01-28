---
name: math-researcher-teacher
description: "Advanced, research-oriented mathematics expert system. Provides rigorous symbolic computation, numerical simulation, and proof assistance across four major pillars: Analysis & PDE, Algebra & Geometry, Stochastics, and Discrete Math."
---

# Math Researcher Teacher

A comprehensive, research-oriented AI assistant for advanced mathematics. It acts as a meta-skill, routing queries to specialized sub-domains for rigorous analysis and simulation.

**Target Audience**: Undergraduate/Graduate Mathematics Students, Researchers.

## 🏛️ Domain Architecture (The Four Pillars)

This skill is organized into four major departments. The Agent should determine the user's mathematical field and route to the appropriate subdirectory.

### 1. Analysis & Differential Equations (`domains/analysis-pde/`)
*   **Calculus & Analysis**: Limits, series, integrals, metric spaces.
*   **Real & Complex Analysis**: Measure theory, residues, conformal mappings.
*   **Differential Equations**: ODEs (stability, phase portraits), PDEs (heat, wave, laplace).
*   **Functional Analysis**: Banach/Hilbert spaces, operators.

### 2. Algebra & Geometry (`domains/algebra-geometry/`)
*   **Linear Algebra**: Vector spaces, eigenvalues, matrix decompositions, spectral theory.
*   **Abstract Algebra**: Groups, rings, fields, Galois theory.
*   **Geometry & Topology**: Differential geometry, manifolds, curvature, homotopy/homology.
*   **Number Theory**: Primes, congruences, elliptic curves.

### 3. Stochastics (`domains/stochastics/`)
*   **Basic Probability**: Distributions, expectations, limit theorems.
*   **Stochastic Processes**: Markov chains, Brownian motion, martingales.
*   **Advanced Stochastics**: Random matrices, large deviations, random graphs (Erdős-Rényi).

### 4. Discrete & Combinatorial (`domains/discrete/`)
*   **Combinatorics**: Counting, generating functions, partitions.
*   **Graph Theory**: Connectivity, coloring, flows, spectral graph theory.

## 🚀 How to Use

**Step 1: Identify the Domain**
Read the user's request and map it to one of the four domains above.

**Step 2: Navigate & Load**
Navigate to the domain's folder and read its `SKILL.md` for specific instructions on using its specialized agents and Python scripts.

**Example Routing:**
*   "Simulate the eigenvalue distribution of a Wigner matrix" -> **Go to `domains/stochastics/`** (Advanced Stochastics).
*   "Calculate the curvature of a surface" -> **Go to `domains/algebra-geometry/`** (Geometry).
*   "Solve this Heat Equation numerically" -> **Go to `domains/analysis-pde/`** (Differential Equations).

## 🛠️ Common Tools

All domains share access to the `common/` library for standard operations:
*   `symbolic_engine.py` (SymPy wrappers)
*   `numeric_engine.py` (NumPy/SciPy wrappers)
*   `plot_engine.py` (Visualization tools)
