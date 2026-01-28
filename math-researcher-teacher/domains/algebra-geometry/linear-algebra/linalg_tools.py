import numpy as np
from scipy import linalg


def compute_spectral_decomposition(matrix):
    """
    Computes eigenvalues and eigenvectors of a matrix.
    Returns: (eigenvalues, eigenvectors)
    """
    return linalg.eig(matrix)


def compute_svd(matrix):
    """
    Computes Singular Value Decomposition.
    Returns: (U, s, Vh)
    """
    return linalg.svd(matrix)


def matrix_norm(matrix, ord=2):
    """
    Computes matrix norm. Default is spectral norm (2-norm).
    """
    return linalg.norm(matrix, ord=ord)


def is_positive_definite(matrix):
    """
    Checks if a symmetric matrix is positive definite via Cholesky decomposition.
    """
    try:
        linalg.cholesky(matrix)
        return True
    except linalg.LinAlgError:
        return False
