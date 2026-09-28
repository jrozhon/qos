"""
Packet-level views of a finished simulation: a table and a timeline.

A log line per packet is readable for a dozen packets and useless for a
thousand. After a run, :func:`packet_table` shows every packet once in a
sortable, filterable table with its time in the system already computed, and
:func:`packet_timeline` draws each packet as a bar from creation to arrival.
Pass the ports as well and the packets they dropped appear too, so a gap in
the packet numbers at the sink is explained rather than silently skipped.

Both read only what the simulation already keeps: ``sink.logged_packets`` and
``port.dropped_packets``.
"""

from collections.abc import Iterable

import numpy as np
import pandas as pd
import panel as pn
from bokeh.models import HoverTool, NumberFormatter, WheelZoomTool

from lib.params import colors
from lib.plots import FONT, GREY, card, legend_below, new_plot

RED = "#E4002B"
SOURCE_COLORS = [colors[0], colors[4], colors[7], colors[6], colors[3]]
COLUMNS = {
    "packet": "Packet",
    "source": "Source",
    "size": "Size [B]",
    "created": "Created [s]",
    "arrived": "Arrived [s]",
    "delay": "Time in system [s]",
    "status": "Status",
}


def _as_list(items) -> list:
    """Accept a single component or several, and return a list."""
    if items is None:
        return []
    if isinstance(items, Iterable) and not isinstance(items, str):
        return list(items)
    return [items]


def packet_frame(sinks, ports=None) -> pd.DataFrame:
    """
    Collect the packets of a finished run into one table.

    Parameters
    ----------
    sinks : PacketSink or Sequence[PacketSink]
        Sink or sinks whose received packets are listed.
    ports : SwitchPort or Sequence[SwitchPort], optional
        Port or ports whose dropped packets are listed as well, by default
        none.

    Returns
    -------
    pandas.DataFrame
        One row per packet, ordered by packet number, with the columns packet,
        source, size [B], created [s], arrived [s], delay [s] (time in system),
        status, and dropped [s]. A dropped packet has no arrival time and no
        delay but a drop time; a delivered one the other way round.
    """
    rows = [
        (
            p.id,
            p.source,
            p.size,
            p.creation_time,
            p.sink_time,
            p.sink_time - p.creation_time,
            f"delivered to {sink.sink_id}",
            np.nan,
        )
        for sink in _as_list(sinks)
        for p in sink.logged_packets
    ]
    rows += [
        (
            p.id,
            p.source,
            p.size,
            p.creation_time,
            np.nan,
            np.nan,
            f"dropped at port {port.port_no}, t = {p.drop_time:.2f} s",
            p.drop_time,
        )
        for port in _as_list(ports)
        for p in port.dropped_packets
    ]
    frame = pd.DataFrame(rows, columns=[*COLUMNS, "dropped"])
    return frame.sort_values("packet", ignore_index=True)


def packet_table(sinks, ports=None, page_size: int = 15) -> pn.Column:
    """
    Show every packet of a finished run in a sortable, filterable table.

    Click a column heading to sort by it; type into the box under a heading to
    filter, for example a source name, or a number in "Time in system" to keep
    only the packets that spent at least that long in the system.

    Parameters
    ----------
    sinks : PacketSink or Sequence[PacketSink]
        Sink or sinks whose received packets are listed.
    ports : SwitchPort or Sequence[SwitchPort], optional
        Port or ports whose dropped packets are listed as well, greyed out, by
        default none.
    page_size : int, optional
        Rows per page, by default 15.

    Returns
    -------
    panel.Column
        A summary card above the table.
    """
    frame = packet_frame(sinks, ports)
    delivered = frame[frame["arrived"].notna()]
    dropped = frame[frame["arrived"].isna()]

    summary = card(
        "Packets in this run",
        [
            ("Delivered [–]", f"{len(delivered)}"),
            ("Dropped [–]", f"{len(dropped)}" if ports is not None else "not tracked"),
            (
                "Created between [s]",
                f"{frame['created'].min():.2f} and {frame['created'].max():.2f}"
                if len(frame)
                else "–",
            ),
            ("Mean size, delivered [B]", f"{delivered['size'].mean():.1f}"),
            ("Mean time in system [s]", f"{delivered['delay'].mean():.3f}"),
        ],
        note="Time in system is arrival minus creation, waiting plus transmission. "
        + (
            "Dropped packets are listed in grey; they never reach a sink, so they "
            "explain the gaps in the packet numbers."
            if ports is not None
            else "Pass the ports as well, <code>packet_table(sink, ports=port)</code>, "
            "to list the packets they dropped."
        ),
        width=520,
    )

    two_decimals = NumberFormatter(format="0.00")
    table = pn.widgets.Tabulator(
        frame.drop(columns="dropped").rename(columns=COLUMNS),
        show_index=False,
        disabled=True,
        stylesheets=[f".tabulator {{ font-family: {FONT}; font-size: 14px; }}"],
        pagination="local",
        page_size=page_size,
        layout="fit_data_table",
        formatters={
            COLUMNS["created"]: two_decimals,
            COLUMNS["arrived"]: two_decimals,
            COLUMNS["delay"]: NumberFormatter(format="0.000"),
        },
        header_filters={
            COLUMNS["packet"]: {"type": "number", "func": "=", "placeholder": "="},
            COLUMNS["source"]: {"type": "input", "func": "like", "placeholder": "name"},
            COLUMNS["size"]: {"type": "number", "func": ">=", "placeholder": "≥"},
            COLUMNS["created"]: {"type": "number", "func": ">=", "placeholder": "≥"},
            COLUMNS["arrived"]: {"type": "number", "func": ">=", "placeholder": "≥"},
            COLUMNS["delay"]: {"type": "number", "func": ">=", "placeholder": "≥"},
            COLUMNS["status"]: {"type": "input", "func": "like", "placeholder": "text"},
        },
    )
    # Grey out the dropped packets, row by row.
    table.style.apply(
        lambda row: [
            f"color: {GREY}" if pd.isna(row[COLUMNS["arrived"]]) else "" for _ in row
        ],
        axis=1,
    )
    return pn.Column(summary, table)


def packet_timeline(
    sinks, ports=None, first: int = 20, width: int = 800, height: int = 400
):
    """
    Draw every packet as a bar from its creation to its arrival.

    Packets are stacked by number, so time runs to the right and packet
    numbers upwards. A packet that waited is a long bar; a burst of arrivals
    is a staircase of overlapping bars. Dropped packets are red crosses at the
    time they were dropped. Hover over a bar for the details of that packet.

    A packet spends well under a second in the system while a run lasts
    minutes, so over the whole run every bar would shrink to a dot. The view
    therefore opens on the first few packets; scroll to zoom and drag to move
    along the run, and press the reset tool to return to this view.

    Parameters
    ----------
    sinks : PacketSink or Sequence[PacketSink]
        Sink or sinks whose received packets are drawn.
    ports : SwitchPort or Sequence[SwitchPort], optional
        Port or ports whose dropped packets are drawn as well, by default none.
    first : int, optional
        Number of packets the initial view shows, by default 20.
    width, height : int, optional
        Size of the figure [px], by default 800 × 400.

    Returns
    -------
    bokeh.plotting.figure
        The timeline.
    """
    frame = packet_frame(sinks, ports)
    shown = frame.head(first)
    end = np.nanmax(shown[["created", "arrived", "dropped"]].to_numpy())
    margin = 0.02 * (end - shown["created"].min())
    plot = new_plot(
        f"Packets from creation to arrival, first {len(shown)} of {len(frame)}",
        "Time [s]",
        "Packet number [–]",
        width=width,
        height=height,
        x_range=(shown["created"].min() - margin, end + margin),
        y_range=(shown["packet"].min() - 1, shown["packet"].max() + 1),
    )
    plot.toolbar.active_scroll = plot.select_one({"type": WheelZoomTool})
    delivered = frame[frame["arrived"].notna()]
    for k, source in enumerate(sorted(delivered["source"].unique())):
        rows = delivered[delivered["source"] == source]
        color = SOURCE_COLORS[k % len(SOURCE_COLORS)]
        # Round caps make both ends of a bar alike, and draw a packet that spent
        # no time in the system (Step 1, no switch) as a dot rather than nothing.
        bars = plot.segment(
            "created",
            "packet",
            "arrived",
            "packet",
            source=rows,
            line_color=color,
            line_width=8,
            line_cap="round",
            legend_label=source,
        )
        plot.add_tools(
            HoverTool(
                renderers=[bars],
                tooltips=[
                    ("packet", "@packet (@size B, @source)"),
                    ("created → arrived", "@created{0.00} → @arrived{0.00} s"),
                    ("time in system", "@delay{0.000} s"),
                ],
            )
        )
    lost = frame[frame["dropped"].notna()]
    if len(lost):
        plot.scatter(
            "dropped",
            "packet",
            source=lost,
            marker="x",
            size=11,
            line_width=2.5,
            color=RED,
            legend_label="Dropped",
        )
    legend_below(plot)
    return plot
