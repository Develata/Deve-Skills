import numpy as np
import matplotlib.pyplot as plt
import matplotlib.style as style


def configure_plotting():
    """
    Configures Matplotlib for research-quality plots.
    Attempts to use LaTeX rendering if available, otherwise falls back to standard high-DPI settings.
    """
    # Use a clean, professional style
    try:
        style.use("seaborn-v0_8-paper")
    except:
        style.use("ggplot")

    # General Settings
    plt.rcParams.update(
        {
            "figure.figsize": (10, 6),
            "figure.dpi": 150,
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "lines.linewidth": 2,
            "grid.alpha": 0.5,
            "savefig.bbox": "tight",
        }
    )

    # Font settings - trying to mimic academic paper look
    # We avoid forcing text.usetex=True to prevent crashes on systems without TeX installed
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["mathtext.fontset"] = "cm"  # Computer Modern (TeX-like)


def save_plot(filename):
    """Saves the current plot to the specified filename."""
    plt.savefig(filename)
    print(f"Plot saved to: {filename}")
    plt.close()


def plot_histogram_vs_theoretical(
    data,
    theoretical_func,
    x_range,
    bins=50,
    title="Simulated vs Theoretical",
    xlabel="Value",
    filename="plot.png",
):
    """
    Generic function to plot a normalized histogram of data against a theoretical PDF.
    """
    configure_plotting()

    plt.figure()

    # Histogram of data
    plt.hist(
        data,
        bins=bins,
        density=True,
        alpha=0.6,
        color="#3498db",
        edgecolor="black",
        label="Empirical",
    )

    # Theoretical curve
    x = np.linspace(x_range[0], x_range[1], 1000)
    y = theoretical_func(x)
    plt.plot(x, y, "r-", linewidth=2.5, label="Theoretical")

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Density")
    plt.legend()
    plt.grid(True)

    save_plot(filename)
