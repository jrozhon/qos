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
    "savefig.dpi": 150,
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
