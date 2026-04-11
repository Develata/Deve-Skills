import sympy as sp


def calculate_limit(expr_str, var_str, point, direction="+"):
    """
    Computes the limit of an expression.
    """
    x = sp.Symbol(var_str)
    expr = sp.sympify(expr_str)
    limit_val = sp.limit(expr, x, point, dir=direction)
    return limit_val


def calculate_derivative(expr_str, var_str, order=1):
    """
    Computes the n-th derivative.
    """
    x = sp.Symbol(var_str)
    expr = sp.sympify(expr_str)
    deriv = sp.diff(expr, x, order)
    return deriv


def calculate_integral(expr_str, var_str, lower=None, upper=None):
    """
    Computes definite or indefinite integral.
    """
    x = sp.Symbol(var_str)
    expr = sp.sympify(expr_str)
    if lower is not None and upper is not None:
        integral = sp.integrate(expr, (x, lower, upper))
    else:
        integral = sp.integrate(expr, x)
    return integral


if __name__ == "__main__":
    import sys

    # Example Usage
    expr = "sin(x)/x"
    print(f"Limit of {expr} as x->0: {calculate_limit(expr, 'x', 0)}")

    expr2 = "exp(-x**2)"
    print(
        f"Integral of {expr2} from -inf to inf: {calculate_integral(expr2, 'x', -sp.oo, sp.oo)}"
    )
