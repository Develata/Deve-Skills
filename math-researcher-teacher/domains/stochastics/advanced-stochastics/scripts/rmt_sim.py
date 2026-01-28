import numpy as np
from scipy import linalg


def generate_wigner_matrix(n, distribution="gaussian"):
    """
    Generates an n x n Wigner matrix (symmetric random matrix).

    Args:
        n (int): Dimension of the matrix.
        distribution (str): 'gaussian' (GOE) or 'rademacher' (+-1).

    Returns:
        np.ndarray: The generated Wigner matrix.
    """
    if distribution == "gaussian":
        # Generate random matrix with N(0, 1) entries
        A = np.random.randn(n, n)
    elif distribution == "rademacher":
        # Generate random matrix with entries +1 or -1
        A = 2 * np.random.randint(0, 2, (n, n)) - 1
    else:
        raise ValueError("Unknown distribution")

    # Symmetrize: M = (A + A.T) / sqrt(2n) to normalize eigenvalues to [-2, 2]
    # Standard normalization for Wigner Semicircle Law
    M = (A + A.T) / np.sqrt(4 * n)  # Proper normalization depends on definition.
    # Wigner Semicircle Law typically for entries var sigma^2/N.
    # Here we constructed (A+A^T)/sqrt(2). If entries of A are N(0,1), entries of (A+A^T) are N(0,2) on off-diagonal.
    # We want final eigenvalues in [-2, 2].
    # Standard Wigner: M = X / sqrt(N). X symmetric with var 1.

    # Let's use the explicit GOE construction:
    # Diagonal ~ N(0, 2/n), Off-diagonal ~ N(0, 1/n)

    # Simpler approach:
    X = np.random.randn(n, n)
    X_sym = (X + X.T) / np.sqrt(2)  # Symmetric, variance 1 off-diag
    W = X_sym / np.sqrt(n)  # Scale by 1/sqrt(n)

    return W


def get_eigenvalues(matrix):
    """Computes sorted eigenvalues of a symmetric matrix."""
    evals = linalg.eigvalsh(matrix)
    return np.sort(evals)


def wigner_semicircle_pdf(x, R=2):
    """
    Theoretical PDF of the Wigner Semicircle Law.
    f(x) = (2 / (pi * R^2)) * sqrt(R^2 - x^2) for |x| <= R
    """
    y = np.zeros_like(x)
    mask = np.abs(x) <= R
    y[mask] = (2 / (np.pi * R**2)) * np.sqrt(R**2 - x[mask] ** 2)
    return y


if __name__ == "__main__":
    import sys
    import os

    # Add project root to path to import common modules
    # Script is in domains/stochastics/advanced-stochastics/scripts/
    # Need to go up 4 levels to reach root
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
    )
    from common.plot_engine import plot_histogram_vs_theoretical
    from common.math_utils import setup_environment

    # Setup
    setup_environment(seed=42)

    # Parameters
    N = 1000  # Matrix size

    print(f"Generating {N}x{N} Wigner Matrix (GOE)...")
    W = generate_wigner_matrix(N)

    print("Computing eigenvalues...")
    evals = get_eigenvalues(W)

    print("Plotting results...")
    output_file = "wigner_semicircle.png"
    plot_histogram_vs_theoretical(
        evals,
        lambda x: wigner_semicircle_pdf(x, R=2),
        x_range=(-2.5, 2.5),
        title=f"Wigner Semicircle Law (N={N})",
        xlabel="Eigenvalues",
        filename=output_file,
    )
    print("Done.")
