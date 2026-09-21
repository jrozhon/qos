"""
Regenerate the figures embedded in the Exercise 02 README.

Run from the notebook directory so that the university symbol is found::

    cd qos-02/qos_02
    uv run python -m lib.figures

Every figure follows the course style guide: the palette and rc parameters come
from :mod:`lib.params`, titles and axis labels are sentence case, axis labels
carry a unit in square brackets, and the symbol is placed by
:func:`lib.params.add_logo`.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from lib.params import add_legend, add_logo, colors, rc_params

HERE = Path(__file__).resolve().parent
NOTEBOOK_DIR = HERE.parent
LOGO = NOTEBOOK_DIR / "logo.png"
FIG_DIR = NOTEBOOK_DIR.parent / "fig"

SEED = 1
SIZE = 10_000
GREY = "#818386"


def _finish(fig, ax, name: str) -> None:
    """
    Add the symbol, save the figure under `name`, and close it.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure to save.
    ax : matplotlib.axes.Axes or numpy.ndarray
        Axes of the figure; a legend is drawn where one is warranted.
    name : str
        File name inside the figure directory.
    """
    add_logo(fig, path=str(LOGO))
    stacked = np.atleast_1d(ax).size > 1
    for axis in np.atleast_1d(ax).ravel():
        if axis.get_legend_handles_labels()[0]:
            # A short panel in a stacked figure needs a bigger relative gap.
            add_legend(axis, pad=0.28 if stacked else 0.16)
    fig.savefig(FIG_DIR / name)
    plt.close(fig)
    print(f"wrote {FIG_DIR / name}")


def uniform_pdf(rng) -> None:
    """
    Plot samples of the uniform distribution on [0, 1) against its density.

    Parameters
    ----------
    rng : numpy.random.Generator
        Source of the samples.
    """
    x = rng.random(size=SIZE)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(x, bins=50, density=True, color=colors[0], rwidth=0.8, label="Samples")
    ax.plot([0, 1], [1, 1], "--", color=GREY, linewidth=2, label="Density $f(x)$")
    ax.set_ylim(0, 1.4)
    ax.set_xlabel("Value [–]")
    ax.set_ylabel("Probability density [–]")
    ax.set_title("Uniform distribution on [0, 1)")
    _finish(fig, ax, "uniform_pdf.png")


def exponential_pdf(rng) -> None:
    """
    Plot samples of the exponential distribution against its density.

    Parameters
    ----------
    rng : numpy.random.Generator
        Source of the samples.
    """
    scale = 1.0  # mean waiting time 1/lambda [s]
    x = rng.exponential(scale=scale, size=SIZE)
    t = np.linspace(0, 6 * scale, 300)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(x, bins=60, density=True, color=colors[0], rwidth=0.8, label="Samples")
    ax.plot(
        t,
        np.exp(-t / scale) / scale,
        "--",
        color=GREY,
        linewidth=2,
        label=r"Density $\lambda e^{-\lambda x}$",
    )
    ax.set_xlim(0, 6 * scale)
    ax.set_xlabel("Inter-arrival time [s]")
    ax.set_ylabel("Probability density [s⁻¹]")
    ax.set_title("Exponential distribution with λ = 1 s⁻¹")
    _finish(fig, ax, "exponential_pdf.png")


def normal_pdf(rng) -> None:
    """
    Plot samples of the standard normal distribution against its density.

    Parameters
    ----------
    rng : numpy.random.Generator
        Source of the samples.
    """
    mu, sigma = 0.0, 1.0
    x = rng.normal(loc=mu, scale=sigma, size=SIZE)
    t = np.linspace(-4 * sigma, 4 * sigma, 300)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(x, bins=60, density=True, color=colors[0], rwidth=0.8, label="Samples")
    ax.plot(
        t,
        np.exp(-((t - mu) ** 2) / (2 * sigma**2)) / (sigma * np.sqrt(2 * np.pi)),
        "--",
        color=GREY,
        linewidth=2,
        label="Density $f(x)$",
    )
    ax.axvspan(-sigma, sigma, color=colors[0], alpha=0.12, label="μ ± σ")
    ax.set_xlabel("Value [–]")
    ax.set_ylabel("Probability density [–]")
    ax.set_title("Normal distribution with μ = 0, σ = 1")
    _finish(fig, ax, "normal_pdf.png")


def poisson_process(rng) -> None:
    """
    Show the two equivalent descriptions of a homogeneous Poisson process.

    The upper panel draws the arrival instants produced by exponential gaps;
    the lower panel counts the arrivals per unit interval and compares the
    histogram with the Poisson probability mass function.

    Parameters
    ----------
    rng : numpy.random.Generator
        Source of the samples.
    """
    lam = 2.0  # arrival rate [s^-1]
    window = 10.0  # length of the illustrated timeline [s]
    horizon = 20_000.0  # length of the counted run [s]

    gaps = rng.exponential(1 / lam, size=int(2 * lam * horizon))
    arrivals = np.cumsum(gaps)
    arrivals = arrivals[arrivals < horizon]
    shown = arrivals[arrivals < window]
    counts = np.bincount(arrivals.astype(int), minlength=int(horizon))

    fig, (ax_top, ax_bottom) = plt.subplots(
        2, 1, figsize=(10, 8), gridspec_kw={"height_ratios": [1, 2]}
    )

    ax_top.eventplot(
        shown, colors=colors[0], lineoffsets=0.45, linelengths=0.5, linewidths=3
    )
    # Mark a single gap rather than all of them, so the label stays readable.
    first, second = shown[0], shown[1]
    ax_top.annotate(
        "",
        xy=(first, 0.28),
        xytext=(second, 0.28),
        arrowprops={"arrowstyle": "<->", "color": GREY, "linewidth": 1.5},
    )
    ax_top.text(
        (first + second) / 2,
        0.18,
        "gap ~ exponential",
        ha="center",
        va="top",
        color=GREY,
        fontsize=15,
    )
    ax_top.set_xlim(0, window)
    ax_top.set_ylim(0, 1.3)
    ax_top.set_yticks([])
    ax_top.grid(False)
    ax_top.set_xlabel("Time [s]")
    ax_top.set_title("Exponential gaps between arrivals")

    k = np.arange(0, counts.max() + 1)
    pmf = np.exp(k * np.log(lam) - lam - np.cumsum(np.log(np.maximum(k, 1))))
    ax_bottom.hist(
        counts,
        bins=np.arange(-0.5, counts.max() + 1.5),
        density=True,
        color=colors[0],
        rwidth=0.8,
        label="Simulated counts",
    )
    ax_bottom.plot(
        k, pmf, "--o", color=GREY, linewidth=2, markersize=7, label="Poisson PMF"
    )
    ax_bottom.set_xticks(k)
    ax_bottom.set_xlabel("Arrivals per interval [–]")
    ax_bottom.set_ylabel("Probability [–]")
    ax_bottom.set_title("Poisson counts over a one-second interval")

    fig.tight_layout(h_pad=3.0)
    _finish(fig, (ax_top, ax_bottom), "poisson_process.png")


def mm1_delay_vs_utilization() -> None:
    """
    Plot the normalized M/M/1 delays against utilization.

    Dividing by the mean service time makes both curves independent of the link
    rate, so the figure applies to any M/M/1 system.
    """
    rho = np.linspace(0.0, 0.95, 400)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(rho, 1 / (1 - rho), color=colors[0], label="Time in system $W/S$")
    ax.plot(
        rho,
        rho / (1 - rho),
        color=colors[4],
        linestyle="--",
        label="Waiting time $W_q/S$",
    )
    ax.annotate(
        "ρ = 0.8:  W = 5S",
        xy=(0.8, 5.0),
        xytext=(0.5, 12.0),
        color="#292929",
        fontsize=15,
        arrowprops={"arrowstyle": "->", "color": GREY, "linewidth": 1.5},
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 20)
    ax.set_xlabel("Utilization ρ [–]")
    ax.set_ylabel("Mean time, in units of $S$ [–]")
    ax.set_title("M/M/1 delay grows without bound as ρ → 1")
    _finish(fig, ax, "mm1_delay_vs_utilization.png")


def main() -> None:
    """Regenerate every README figure."""
    plt.rcParams.update(rc_params)
    FIG_DIR.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)

    uniform_pdf(rng)
    exponential_pdf(rng)
    normal_pdf(rng)
    poisson_process(rng)
    mm1_delay_vs_utilization()


if __name__ == "__main__":
    main()
