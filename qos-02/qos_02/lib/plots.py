"""
Bokeh figures and result cards for the Lab 02 notebook.

The styling is the one used in Lab 01 (STYLE.md §5.2 and §5.3): Carlito
typography, a dashed light grid, lines 3 px wide at 60 % opacity, and result
cards with a grey background and a green edge. Every chart in the notebook is
built with :func:`new_plot`, so a student plotting their own results in Task 5
starts from the same look with one call.

A Bokeh figure is shown by returning it from a cell inside a Panel layout,
``pn.Row(plot, card)``, or on its own as ``pn.pane.Bokeh(plot)``; the notebook
calls ``pn.extension("tabulator")`` once in its imports cell (the argument loads
the table widget used by :mod:`lib.packets`).
"""

import numpy as np
import panel as pn
from bokeh.models import Legend
from bokeh.plotting import figure

from lib.params import colors

FONT = "Carlito, Calibri, Liberation Sans, DejaVu Sans, Arial, sans-serif"
TEXT_COLOR = "#292929"
GRID_COLOR = "#e5e5e5"
GREY = "#818386"  # neutral colour of theory curves and bounds
TOOLS = "crosshair,pan,reset,save,wheel_zoom"
WIDTH, HEIGHT = 600, 400  # plot size [px], as in Lab 01
CARD_WIDTH = 380  # width of a result card beside a plot [px]


def style_plot(plot: figure) -> figure:
    """
    Apply the course typography to a Bokeh figure.

    Parameters
    ----------
    plot : bokeh.plotting.figure
        Figure to style in place.

    Returns
    -------
    bokeh.plotting.figure
        The same figure, for chaining.
    """
    plot.title.text_font = FONT
    plot.title.text_font_style = "bold"
    plot.title.text_color = TEXT_COLOR
    plot.axis.axis_label_text_font = FONT
    plot.axis.axis_label_text_font_style = "bold"
    plot.axis.axis_label_text_color = TEXT_COLOR
    plot.axis.major_label_text_font = FONT
    plot.axis.major_label_text_color = TEXT_COLOR
    plot.grid.grid_line_color = GRID_COLOR
    plot.grid.grid_line_dash = "dashed"
    plot.toolbar.logo = None
    return plot


def new_plot(
    title: str,
    x_axis_label: str,
    y_axis_label: str,
    width: int = WIDTH,
    height: int = HEIGHT,
    **kwargs,
) -> figure:
    """
    Create an empty figure in the course style.

    Parameters
    ----------
    title : str
        Short noun phrase in sentence case.
    x_axis_label, y_axis_label : str
        Axis labels with the unit in square brackets, e.g. ``"Time [s]"``.
    width, height : int, optional
        Size of the figure [px], by default 600 × 400.
    **kwargs
        Further keyword arguments for :func:`bokeh.plotting.figure`, such as
        ``x_range`` or ``y_axis_type``.

    Returns
    -------
    bokeh.plotting.figure
        The styled figure, ready for glyphs.
    """
    plot = figure(
        title=title,
        x_axis_label=x_axis_label,
        y_axis_label=y_axis_label,
        width=width,
        height=height,
        tools=TOOLS,
        **kwargs,
    )
    return style_plot(plot)


def legend_below(plot: figure, columns: int | None = None) -> figure:
    """
    Move the legend of a figure below the plot area.

    A legend inside the plot area covers the data it describes, for a histogram
    most of all (STYLE.md §5.1). Call this after every glyph with a
    ``legend_label`` has been added.

    Parameters
    ----------
    plot : bokeh.plotting.figure
        Figure whose legend is moved.
    columns : int, optional
        Number of legend columns, by default one per entry, i.e. a single row.

    Returns
    -------
    bokeh.plotting.figure
        The same figure, for chaining.
    """
    if not plot.legend:
        return plot
    items = plot.legend[0].items
    # Drop the default legend from the plot area and re-create it underneath.
    plot.center = [r for r in plot.center if not isinstance(r, Legend)]
    legend = Legend(
        items=items,
        orientation="horizontal",
        ncols=columns or len(items),
        label_text_font=FONT,
        label_text_color=TEXT_COLOR,
        border_line_color=None,
        click_policy="hide",
        spacing=24,
        label_standoff=6,
    )
    plot.add_layout(legend, "below")
    plot.height += 30 * ((len(items) - 1) // (columns or len(items)) + 1)
    return plot


def histogram(
    plot: figure,
    values,
    bins,
    density: bool = True,
    color: str = colors[0],
    alpha: float = 0.8,
    label: str | None = None,
):
    """
    Add a histogram of the values to a figure, bars 80 % of the bin width.

    Parameters
    ----------
    plot : bokeh.plotting.figure
        Figure to draw on.
    values : array_like
        The sample.
    bins : int or array_like
        Number of bins, or their edges, as for :func:`numpy.histogram`.
    density : bool, optional
        Normalise to a probability density, by default True; otherwise the bars
        are counts.
    color : str, optional
        Bar colour, by default the university green.
    alpha : float, optional
        Bar opacity, by default 0.8; use 0.5 when histograms overlap.
    label : str, optional
        Legend entry, by default none.

    Returns
    -------
    tuple[numpy.ndarray, numpy.ndarray]
        Heights of the bars and the bin edges.
    """
    heights, edges = np.histogram(values, bins=bins, density=density)
    gap = 0.1 * np.diff(edges)
    extra = {"legend_label": label} if label else {}
    plot.quad(
        left=edges[:-1] + gap,
        right=edges[1:] - gap,
        bottom=0,
        top=heights,
        fill_color=color,
        fill_alpha=alpha,
        line_color=None,
        **extra,
    )
    return heights, edges


def card_html(title: str, rows: list[tuple[str, str]], note: str = "") -> str:
    """
    Build the HTML of a result card in the course style (STYLE.md §5.3).

    Identical to the card of Lab 01: a heading, a two-column table of labelled
    values, and an optional note saying what the numbers count and where they
    were read from.

    Parameters
    ----------
    title : str
        Card heading.
    rows : list[tuple[str, str]]
        ``(label, value)`` pairs rendered as a two-column table. A label carries
        its unit in square brackets; both may contain HTML markup.
    note : str, optional
        Small print rendered below the table, by default none.

    Returns
    -------
    str
        HTML fragment with inline styles.
    """
    table = "".join(
        f"<tr><td style='padding:2px 12px 2px 0;color:{TEXT_COLOR}'>{label}</td>"
        f"<td style='padding:2px 0;font-weight:bold;color:{TEXT_COLOR};"
        f"font-variant-numeric:tabular-nums'>{value}</td></tr>"
        for label, value in rows
    )
    note_html = (
        f"<p style='margin:8px 0 0;font-size:13px;line-height:1.4;color:{GREY}'>"
        f"{note}</p>"
        if note
        else ""
    )
    return (
        f"<div style='background:#F2F3F3;border-left:4px solid {colors[0]};"
        f"border-radius:4px;padding:12px 16px;font-family:{FONT};font-size:15px'>"
        f"<h3 style='margin:0 0 6px;font:bold 15px {FONT};color:{TEXT_COLOR}'>"
        f"{title}</h3>"
        f"<table style='border-collapse:collapse'>{table}</table>{note_html}</div>"
    )


def card(
    title: str, rows: list[tuple[str, str]], note: str = "", width: int = CARD_WIDTH
) -> pn.pane.HTML:
    """
    Wrap :func:`card_html` in a Panel pane that can sit in a layout.

    Parameters
    ----------
    title, rows, note
        As for :func:`card_html`.
    width : int, optional
        Width of the card [px], by default 380.

    Returns
    -------
    panel.pane.HTML
        The card, to be placed in ``pn.Row`` or ``pn.Column``.
    """
    return pn.pane.HTML(card_html(title, rows, note), width=width)


def cards(*items: pn.pane.HTML) -> pn.Row:
    """
    Lay result cards out side by side, aligned at the top.

    Parameters
    ----------
    *items : panel.pane.HTML
        Cards from :func:`card`.

    Returns
    -------
    panel.Row
        The row of cards.
    """
    return pn.Row(*items, align="start")


def sample_card(x: np.ndarray, mean: float, std: float) -> pn.pane.HTML:
    """
    Compare the moments of a sample with their theoretical values in a card.

    Parameters
    ----------
    x : numpy.ndarray
        The sample.
    mean : float
        Theoretical mean of the distribution.
    std : float
        Theoretical standard deviation of the distribution.

    Returns
    -------
    panel.pane.HTML
        Card with the count, extremes, mean, and standard deviation.
    """
    return card(
        "Sample against theory",
        [
            ("Count [–]", f"{x.size}"),
            ("Minimum", f"{x.min():.3f}"),
            ("Mean", f"{x.mean():.3f} &nbsp;(theory {mean:.3f})"),
            ("Standard deviation", f"{x.std():.3f} &nbsp;(theory {std:.3f})"),
            ("Maximum", f"{x.max():.3f}"),
        ],
        note="Record these with the seed and the parameters. A finite-sample "
        "minimum or maximum is not a bound of an unbounded distribution.",
    )
