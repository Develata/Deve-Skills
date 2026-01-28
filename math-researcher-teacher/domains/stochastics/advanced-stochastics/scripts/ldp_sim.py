import numpy as np


def simulate_sample_means(n_samples, batch_size, distribution="exponential", param=1.0):
    """
    Simulates sample means for Large Deviation Principle demonstration.

    Args:
        n_samples (int): Number of independent experiments (e.g., 10000).
        batch_size (int): Size of each sample batch (N) over which mean is taken.
        distribution (str): 'exponential' or 'bernoulli'.
        param (float): Parameter for distribution (lambda for exp, p for bernoulli).

    Returns:
        np.ndarray: Array of sample means.
    """
    if distribution == "exponential":
        # Sum of N exponential variables with rate lambda
        # Mean should concentrate around 1/lambda
        data = np.random.exponential(scale=1.0 / param, size=(n_samples, batch_size))
    elif distribution == "bernoulli":
        # Mean should concentrate around p
        data = np.random.binomial(1, param, size=(n_samples, batch_size))
    else:
        raise ValueError("Unknown distribution")

    sample_means = np.mean(data, axis=1)
    return sample_means


def cramer_rate_function_exp(x, lam=1.0):
    """
    Rate function I(x) for Exponential(lambda).
    I(x) = lambda * x - 1 - log(lambda * x)  for x > 0
    (Derived from Fenchel-Legendre transform of cumulant generating function)
    """
    # Theoretical mean is 1/lam. I(1/lam) should be 0.
    # Let's verify standard form: I(x) = lambda*x - 1 - ln(lambda*x)
    # Note: Returns infinity for x <= 0
    y = np.full_like(x, np.inf)
    mask = x > 0
    # Formula: lambda * x - 1 - ln(lambda * x)
    # Let's double check relative entropy (KL divergence)
    # It relates to KL(P_x || P_true)
    y[mask] = lam * x[mask] - 1 - np.log(lam * x[mask])
    return y


if __name__ == "__main__":
    import sys
    import os

    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    )
    from common.plot_engine import configure_plotting, save_plot
    import matplotlib.pyplot as plt

    # LDP Visualization is tricky because probability decays exponentially.
    # Histogram isn't enough; we want to see P(Mean \approx x) ~ exp(-N * I(x))
    # => -1/N * log(P) \approx I(x)

    N_BATCH = 50
    N_SAMPLES = 100000
    LAM = 1.0

    print(f"Simulating LDP for Exponential({LAM})... N={N_BATCH}, Samples={N_SAMPLES}")
    means = simulate_sample_means(N_SAMPLES, N_BATCH, "exponential", LAM)

    # Calculate empirical probability density
    hist, bin_edges = np.histogram(means, bins=50, density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # Calculate empirical rate function: I_emp(x) = -1/N * log(P(x))
    # Note: density isn't probability, need to account for bin width, but for shape comparison it's okay-ish
    # Or strictly: P(x in bin) ~ exp(-N * I(x)) * dx
    # Let's just plot the histogram vs theoretical concentration to show the "shape" narrowing

    configure_plotting()
    plt.figure()

    # 1. Plot Empirical Distribution
    plt.hist(
        means, bins=50, density=True, alpha=0.6, label=f"Empirical Means (N={N_BATCH})"
    )

    # 2. Plot Theoretical Rate Function (Scaled for visualization context)
    # This is qualitative comparison. I(x) is convex with min at mean.
    x_grid = np.linspace(0.1, 3.0, 100)
    I_x = cramer_rate_function_exp(x_grid, LAM)

    # To compare on same graph, maybe plot exp(-N * I(x)) * NormalizingConstant
    # This approximates the PDF using saddle-point approximation
    pdf_approx = np.exp(-N_BATCH * I_x)
    # Normalize approx pdf
    pdf_approx /= np.sum(pdf_approx) * (x_grid[1] - x_grid[0])

    plt.plot(
        x_grid, pdf_approx, "r--", linewidth=2, label="LDP Approximation exp(-N*I(x))"
    )

    plt.title(f"Large Deviation Principle: Cramér's Theorem")
    plt.xlabel("Sample Mean")
    plt.legend()
    plt.grid(True)

    save_plot("ldp_simulation.png")
