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


if __name__ == "__main__":
    import argparse
    import json
    import sys

    def parse_matrix(matrix_str):
        try:
            return np.array(json.loads(matrix_str))
        except Exception as e:
            print(f"Error parsing matrix: {e}", file=sys.stderr)
            sys.exit(1)

    parser = argparse.ArgumentParser(description="Linear Algebra Tools")
    parser.add_argument(
        "--matrix",
        type=str,
        required=True,
        help="Matrix in JSON format e.g. [[1,2],[3,4]]",
    )
    parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=["eigen", "svd", "norm", "posdef"],
        help="Action to perform",
    )

    args = parser.parse_args()
    matrix = parse_matrix(args.matrix)

    if args.action == "eigen":
        vals, vecs = compute_spectral_decomposition(matrix)
        print("Eigenvalues:", vals)
        print("Eigenvectors:", vecs)
    elif args.action == "svd":
        U, s, Vh = compute_svd(matrix)
        print("U:", U)
        print("Singular Values:", s)
        print("Vh:", Vh)
    elif args.action == "norm":
        print("Spectral Norm:", matrix_norm(matrix))
    elif args.action == "posdef":
        print("Is Positive Definite:", is_positive_definite(matrix))
