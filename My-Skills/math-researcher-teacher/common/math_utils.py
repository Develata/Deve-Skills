import numpy as np
import sympy as sp


def setup_environment(seed=None):
    """
    Sets up the mathematical environment.
    - Seeds NumPy random number generator for reproducibility.
    - Configures SymPy printing.
    """
    if seed is not None:
        np.random.seed(seed)

    sp.init_printing(use_unicode=True)


def to_latex(expr):
    """Converts a SymPy expression to a LaTeX string."""
    return sp.latex(expr)
