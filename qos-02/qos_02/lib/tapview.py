"""
What a network tap sees: the state of one port over time.

The sink only records the packets that made it through. A tap samples the port
itself at a fixed interval, so it can show what the sink cannot: how full the
buffer was, whether the server was busy, and what was waiting. This module
draws those samples and summarises them.

:func:`tap_view` puts the bytes in the buffer next to its capacity and marks
each dropped packet at the level the buffer would have reached had it been
admitted, so every drop visibly overshoots the capacity line. Below it, the
packets at the port are stacked: those waiting in the buffer at the bottom and
the packet in service, at most one, on top. The lower area is what L_q counts,
the whole stack what L counts.

:func:`tap_card` turns the same samples into the estimates of ρ, L, and L_q
that Step 4 compares with the M/M/1 formulas.
"""

import numpy as np
import pandas as pd
import panel as pn
from bokeh.models import HoverTool

from lib.params import colors
from lib.plots import GREY, card, legend_below, new_plot

RED = "#E4002B"


def _busiest_window(times, queue_bytes, drop_times, length: float) -> tuple:
    """
    Pick the window of the given length with the most drops, then the fullest buffer.

    Parameters
    ----------
    times : numpy.ndarray
        Sample times of the tap [s].
    queue_bytes : numpy.ndarray
        Bytes in the buffer at each sample [B].
    drop_times : numpy.ndarray
        Times at which the port dropped a packet [s].
    length : float
        Length of the window [s].

    Returns
    -------
    tuple[float, float]
        Start and end of the chosen window [s].
    """
    if times[-1] - times[0] <= length:
        return float(times[0]), float(times[0] + length)
    starts = times[times <= times[-1] - length]
    best, best_score = float(starts[0]), (-1, -1.0)
    for start in starts[:: max(1, len(starts) // 400)]:  # at most ~400 candidates
        inside = (times >= start) & (times < start + length)
        drops = int(np.sum((drop_times >= start) & (drop_times < start + length)))
        score = (drops, float(queue_bytes[inside].sum()))
        if score > best_score:
            best, best_score = float(start), score
    return best, best + length


def tap_view(tap, port, t0: float | None = None, length: float = 30.0) -> pn.Column:
    """
    Draw the buffer occupancy, the drops, and the packet counts of one port.

    Parameters
    ----------
    tap : NetworkTap
        Tap attached to the port; a short sampling interval, such as 0.05 s,
        shows individual packets.
    port : SwitchPort
        The port the tap samples, for its buffer capacity and dropped packets.
    t0 : float, optional
        Start of the window shown [s]. Left out, the window of `length` seconds
        with the most drops is chosen. Pan or zoom to see the rest of the run.
    length : float, optional
        Length of the window shown [s], by default 30.0.

    Returns
    -------
    panel.Column
        Two charts sharing one time axis: bytes in the buffer above, packets in
        the system and waiting below.
    """
    times = np.asarray(tap.times, dtype=float)
    queue_bytes = np.asarray(tap.queue_bytes, dtype=float)
    system = np.asarray(tap.system_packets)
    queue = np.asarray(tap.queue_packets)

    # Each dropped packet is drawn at the level the buffer would have reached:
    # the bytes waiting at the instant of the drop, as the port recorded them,
    # plus its own size. This always exceeds the capacity, which is why it was
    # dropped; a tap sample could be up to one interval out of date.
    drops = pd.DataFrame(
        {
            "time": [p.drop_time for p in port.dropped_packets],
            "size": [p.size for p in port.dropped_packets],
            "packet": [p.id for p in port.dropped_packets],
            "waiting": [p.drop_queue_bytes for p in port.dropped_packets],
        }
    )
    drops["needed"] = drops["waiting"] + drops["size"]
    capacity = port.capacity or float(queue_bytes.max() or 1)
    drops["free"] = capacity - drops["waiting"]
    # One sentence per drop for the tooltip: a packet either did not fit into
    # the space left, or was larger than the whole buffer and never could.
    drops["reason"] = [
        f"larger than the whole {capacity:.0f} B buffer, so it can never be admitted"
        if size > capacity
        else f"only {free:.0f} B of the {capacity:.0f} B buffer was free"
        for size, free in zip(drops["size"], drops["free"])
    ]

    if t0 is None:
        t0, t1 = _busiest_window(times, queue_bytes, drops["time"].to_numpy(), length)
    else:
        t1 = t0 + length
    top = 1.15 * max(capacity, float(drops["needed"].max()) if len(drops) else 0)

    buffer_plot = new_plot(
        "Bytes in the buffer, and the packets that did not fit",
        "Time [s]",
        "Bytes waiting [B]",
        width=800,
        height=320,
        x_range=(t0, t1),
        y_range=(0, top),
    )
    buffer_plot.varea_step(
        x=times,
        y1=np.zeros_like(queue_bytes),
        y2=queue_bytes,
        step_mode="after",
        fill_color=colors[0],
        fill_alpha=0.35,
        legend_label="Bytes waiting",
    )
    buffer_plot.step(
        times, queue_bytes, mode="after", line_color=colors[0], line_width=2
    )
    buffer_plot.line(
        [times[0], times[-1]],
        [capacity, capacity],
        line_color=GREY,
        line_dash="dashed",
        line_width=2,
        legend_label=f"Buffer capacity {capacity:.0f} B",
    )
    if len(drops):
        crosses = buffer_plot.scatter(
            "time",
            "needed",
            source=drops,
            marker="x",
            size=12,
            line_width=3,
            color=RED,
            legend_label="Dropped packet, at bytes waiting + its size",
        )
        buffer_plot.add_tools(
            HoverTool(
                renderers=[crosses],
                tooltips=[
                    ("Packet", "@packet, @size B, arrived at t = @time{0.00} s"),
                    ("Buffer already held", "@waiting{0} B"),
                    ("Admitting it", "@waiting{0} B + @size B = @needed{0} B"),
                    ("Dropped because", "@reason"),
                ],
            )
        )
    legend_below(buffer_plot)

    count_plot = new_plot(
        "Packets at the port: waiting, and in service",
        "Time [s]",
        "Packets [–]",
        width=800,
        height=240,
        x_range=buffer_plot.x_range,  # zooming one chart zooms the other
        y_range=(0, max(2, int(system.max()) + 1)),
    )
    # Stacked areas: the waiting packets at the bottom, the packet in service
    # (at most one) on top. The top edge is the number in the system, L; the
    # lower area alone is L_q. The waiting count can never exceed the total.
    count_plot.varea_step(
        x=times,
        y1=np.zeros_like(queue),
        y2=queue,
        step_mode="after",
        fill_color=colors[0],
        fill_alpha=0.6,
        legend_label="Waiting in the buffer (counted in Lq)",
    )
    count_plot.varea_step(
        x=times,
        y1=queue,
        y2=system,
        step_mode="after",
        fill_color=colors[4],
        fill_alpha=0.45,
        legend_label="In service (added for L)",
    )
    count_plot.yaxis.ticker = list(range(max(2, int(system.max()) + 1) + 1))
    legend_below(count_plot)
    return pn.Column(buffer_plot, count_plot)


def tap_card(tap, port=None, window: float = 10.0) -> pn.pane.HTML:
    """
    Summarise the samples of one tap in a card.

    Parameters
    ----------
    tap : NetworkTap
        The tap to summarise.
    port : SwitchPort, optional
        The port the tap samples. Given, the card also counts how many of the
        drops at a full buffer the tap saw coming, i.e. its last sample before
        the drop already showed bytes waiting.
    window : float, optional
        Length of the windows whose peak occupancy is averaged [s], by default
        10.0.

    Returns
    -------
    panel.pane.HTML
        Busy share, mean occupancies, and what the tap saw of the buffer.
    """
    times = np.asarray(tap.times, dtype=float)
    system = np.asarray(tap.system_packets)
    queue = np.asarray(tap.queue_packets)
    queue_bytes = np.asarray(tap.queue_bytes)
    blocks = (times // window).astype(int)
    peaks = [queue_bytes[blocks == k].max() for k in np.unique(blocks)]
    rows = [
        ("Samples taken [–]", f"{system.size}"),
        ("Server busy, share of samples [–]", f"{np.mean(system >= 1):.3f}"),
        ("Mean packets in system [–]", f"{system.mean():.3f}"),
        ("Mean packets waiting [–]", f"{queue.mean():.3f}"),
        (
            f"Mean of the {window:g} s peaks of bytes waiting [B]",
            f"{np.mean(peaks):.1f}",
        ),
    ]
    if port is not None:
        # A drop at a full buffer, not one of a packet larger than the buffer.
        full = [p.drop_time for p in port.dropped_packets if p.size <= port.capacity]
        before = np.clip(np.searchsorted(times, full, side="right") - 1, 0, None)
        seen = int(np.sum(queue_bytes[before] > 0))
        rows.append(("Full-buffer drops seen coming [–]", f"{seen} of {len(full)}"))
    return card(
        f"Tap sampling every {tap.interval:g} s",
        rows,
        note="The busy share estimates the utilization <em>ρ</em>, the two means "
        "<em>L</em> and <em>L</em><sub>q</sub>. A sample only sees its own instant: "
        "a burst that fills the buffer and drains between two samples is missed, "
        "so a drop can occur while the last sample showed an empty buffer.",
    )
