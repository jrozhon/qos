textcolor = "#292929"

rc_params = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Carlito", "Calibri", "Liberation Sans", "DejaVu Sans", "Arial", "sans-serif"],
    "text.color": textcolor,
    "axes.labelcolor": textcolor,
    "xtick.color": textcolor,
    "ytick.color": textcolor,
    "figure.facecolor": "#ffffff",
    "axes.facecolor": "#ffffff",
    "savefig.facecolor": "#ffffff",
    "axes.titlesize": 26,
    "axes.titlelocation": "left",
    "axes.titleweight": "bold",
    "axes.titlepad": 20,
    "axes.labelsize": 17,
    "axes.labelweight": "bold",
    "axes.labelpad": 8,
    "xaxis.labellocation": "right",
    "yaxis.labellocation": "top",
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "xtick.minor.size": 0,
    "ytick.minor.size": 0,
    "axes.linewidth": 0,
    "axes.axisbelow": True,
    "axes.grid": True,
    "grid.linestyle": "--",
    "grid.linewidth": 1.3,
    "grid.color": "#e5e5e5",
    "legend.frameon": False,
    "legend.numpoints": 1,
    "legend.scatterpoints": 1,
    "legend.loc": "center right",
    "legend.fontsize": 15,
    "legend.title_fontsize": 15,
    "legend.markerscale": 1.3,
    "lines.solid_capstyle": "round",
    "lines.linewidth": 3,
    "figure.dpi": 140,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
}

colors = [
    "#00A499", "#43B02A", "#E4002B", "#FFB81C",
    "#0047BB", "#05C3DE", "#8246AF", "#FF8200",
]


def add_logo(fig, path="logo.png", box=(0.83, 0.90, 0.10, 0.10)):
    """
    Place the university symbol in the top-right corner of a figure.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure to decorate.
    path : str, optional
        Image file, by default "logo.png" in the notebook directory.
    box : tuple[float, float, float, float], optional
        (x, y, width, height) of the logo axes in figure coordinates.
    """
    import matplotlib.image as image

    ax = fig.add_axes(box)
    ax.set_axis_off()
    ax.imshow(image.imread(path), aspect="equal")


def add_legend(ax, ncols=None, pad=0.16, **kwargs):
    """
    Place the legend in one row below the plot area, outside the axes.

    A legend drawn inside the axes covers the data, and with
    ``legend.frameon`` disabled its text sits directly on top of bars and
    lines. Keeping it outside avoids that for every figure, whatever the data
    happen to look like.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes whose legend is drawn.
    ncols : int, optional
        Number of legend columns, by default one per entry, giving a single
        row. Pass a smaller number when the labels are long.
    pad : float, optional
        Gap between the bottom of the axes and the legend, as a fraction of
        the height of the axes, by default 0.16. Raise it for a short panel in
        a stacked figure, where the same fraction is less absolute space and
        the legend can reach the axis label.
    **kwargs
        Further keyword arguments for ``matplotlib.axes.Axes.legend``.

    Returns
    -------
    matplotlib.legend.Legend
        The placed legend.
    """
    handles, _ = ax.get_legend_handles_labels()
    return ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -pad),
        ncols=max(1, len(handles)) if ncols is None else ncols,
        borderaxespad=0.0,
        **kwargs,
    )
