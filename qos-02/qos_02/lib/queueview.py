"""
An interactive view of packets passing through a single-server queue.

The averages of Step 4 say what the queue does on average; this module shows
the mechanism they average over. Dragging the time slider, or pressing play,
moves through the run one instant at a time, showing which packets are waiting
in the buffer, which one is being transmitted and how far it has got, and how
the two occupancy counters follow from that picture.

The picture is drawn with Bokeh and updated in place: moving the slider changes
the data of a few glyphs rather than redrawing an image, so playback stays
smooth even over a remote session.

Nothing extra has to be recorded during the simulation. For a single port
feeding a sink directly, the service interval of every delivered packet
follows from what the sink already logs::

    service        = 8 * size / rate
    service starts = sink_time - service
    waiting time   = service start - creation time

The reconstruction is exact for one port with no propagation delay. It does
not extend to a path over several ports, where only the creation time and the
final arrival time are known, and it omits dropped packets, which never reach
a sink.
"""

from typing import NamedTuple

import numpy as np
import panel as pn
from bokeh.core.properties import value
from bokeh.models import Arrow, ColumnDataSource, Span, VeeHead
from bokeh.plotting import figure

from lib.core import BYTES_TO_BITS
from lib.plots import FONT, card_html, new_plot

WAIT_FILL, WAIT_EDGE = "#E6F6F5", "#00A499"
CURSOR = "#0047BB"  # blue, so the time cursor is never read as teal data
SERVE_FILL, SERVE_EDGE = "#E6F9FC", "#05C3DE"
DONE_FILL = "#B2E4E0"
NEUTRAL, INK = "#818386", "#292929"
SLOTS = 6  # buffer positions drawn before the queue is summarized as "+ n more"
SLOT_X = [2.1 + slot * 0.62 for slot in range(SLOTS)]  # left edge of each slot
WIDTH = 700  # width of the picture and the strip [px]


class Timeline(NamedTuple):
    """
    Arrival, service, and departure of every packet that reached the sink.

    Attributes
    ----------
    ids : numpy.ndarray
        Packet identifier.
    arrival : numpy.ndarray
        Time the packet was created and offered to the port [s].
    start : numpy.ndarray
        Time transmission began [s].
    depart : numpy.ndarray
        Time transmission finished and the packet reached the sink [s].
    size : numpy.ndarray
        Packet size [B].
    """

    ids: np.ndarray
    arrival: np.ndarray
    start: np.ndarray
    depart: np.ndarray
    size: np.ndarray


def packet_timeline(sink, rate: float) -> Timeline:
    """
    Reconstruct the service interval of every packet the sink received.

    Parameters
    ----------
    sink : PacketSink
        Sink fed directly by the port of interest.
    rate : float
        Transmission rate of that port [bit/s].

    Returns
    -------
    Timeline
        One entry per delivered packet, in arrival order.
    """
    packets = sink.logged_packets
    size = np.array([p.size for p in packets], dtype=float)
    depart = np.array([p.sink_time for p in packets], dtype=float)
    service = BYTES_TO_BITS * size / rate
    return Timeline(
        ids=np.array([p.id for p in packets]),
        arrival=np.array([p.creation_time for p in packets], dtype=float),
        start=depart - service,
        depart=depart,
        size=size,
    )


def queue_state(timeline: Timeline, t: float) -> tuple:
    """
    Find which packets are waiting and which is in service at one instant.

    Parameters
    ----------
    timeline : Timeline
        Reconstructed packet timeline.
    t : float
        Instant to inspect [s].

    Returns
    -------
    tuple[numpy.ndarray, Optional[int]]
        Indices of the waiting packets, oldest first, and the index of the
        packet in service, or None when the server is idle.
    """
    waiting = np.flatnonzero((timeline.arrival <= t) & (t < timeline.start))
    serving = np.flatnonzero((timeline.start <= t) & (t < timeline.depart))
    return waiting, (int(serving[0]) if serving.size else None)


def busiest_window(timeline: Timeline, length: float = 60.0, after: float = 0.0):
    """
    Find the window of the given length holding the most packet-seconds.

    At a utilization of 0.4 the server is idle most of the time, so a window
    picked at random is usually empty and shows nothing happening. This picks
    one that contains a busy period, which is what there is to look at. The
    run as a whole is emptier than the window it returns.

    Parameters
    ----------
    timeline : Timeline
        Reconstructed packet timeline.
    length : float, optional
        Length of the window [s], by default 60.0.
    after : float, optional
        Ignore packets arriving before this time [s], by default 0.0.

    Returns
    -------
    tuple[float, float]
        Start and end of the chosen window [s].
    """
    candidates = timeline.arrival[timeline.arrival >= after]
    if candidates.size == 0:
        return after, after + length
    # Time each packet spends in the system, summed over the packets whose
    # stay begins inside the window starting at each candidate arrival.
    stay = timeline.depart - timeline.arrival
    best_start, best_load = float(candidates[0]), -1.0
    for start in candidates:
        inside = (timeline.arrival >= start) & (timeline.arrival < start + length)
        load = float(stay[inside].sum())
        if load > best_load:
            best_start, best_load = float(start), load
    return best_start, best_start + length


def _occupancy_series(timeline: Timeline, t0: float, t1: float, points: int = 400):
    """
    Sample the number of packets in the system across a window.

    The series is the same for every frame of a given window, so it is computed
    once and reused rather than per frame.

    Parameters
    ----------
    timeline : Timeline
        Reconstructed packet timeline.
    t0, t1 : float
        Bounds of the window [s].
    points : int, optional
        Number of samples across the window, by default 400.

    Returns
    -------
    tuple[numpy.ndarray, numpy.ndarray]
        Sample times [s] and packets in the system at each [–].
    """
    grid = np.linspace(t0, t1, points)
    occupancy = np.empty(points, dtype=int)
    for i, u in enumerate(grid):
        waiting, serving = queue_state(timeline, float(u))
        occupancy[i] = len(waiting) + (serving is not None)
    return grid, occupancy


def _text(plot: figure, source, color=INK, size="14px", style="normal", **kwargs):
    """Draw centred labels from a data source in the course font."""
    plot.text(
        "x",
        "y",
        text="text",
        source=source,
        text_font=value(FONT),
        text_font_size=size,
        text_font_style=style,
        text_color=color,
        text_align="center",
        text_baseline="middle",
        **kwargs,
    )


class QueueView:
    """
    Bokeh picture of the queue at one instant, above an occupancy strip.

    The glyphs are built once; :meth:`show` only replaces the data of their
    sources, so changing the instant is cheap.

    Parameters
    ----------
    timeline : Timeline
        Reconstructed packet timeline.
    t0, t1 : float
        Bounds of the window being inspected [s].
    """

    def __init__(self, timeline: Timeline, t0: float, t1: float):
        self.timeline, self.t0, self.t1 = timeline, t0, t1
        self.state = self._state_figure()
        self.strip = self._strip_figure()
        self.card = pn.pane.HTML("", width=250)

    def _state_figure(self) -> figure:
        """Build the buffer and server diagram, with empty packet glyphs."""
        plot = figure(
            width=WIDTH,
            height=230,
            x_range=(0, 10),
            y_range=(0.7, 2.45),
            toolbar_location=None,
            tools="",
        )
        plot.axis.visible = False
        plot.grid.visible = False
        plot.outline_line_color = None

        # Component names in bold, the two areas captioned in grey above them.
        names = dict(x=[0.5, 9.5], y=[1.3, 1.3], text=["Source", "Sink"])
        captions = dict(x=[3.7, 7.0], y=[2.15, 2.15], text=["Waiting queue", "Server"])
        _text(plot, ColumnDataSource(names), style="bold")
        _text(plot, ColumnDataSource(captions), color=NEUTRAL, size="13px")
        for x_start, x_end in ((1.1, 2.0), (8.1, 9.0)):
            plot.add_layout(
                Arrow(
                    end=VeeHead(size=12, fill_color=INK, line_color=INK),
                    x_start=x_start,
                    y_start=1.3,
                    x_end=x_end,
                    y_end=1.3,
                    line_color=INK,
                    line_width=2,
                )
            )

        # Buffer: the packet nearest the server is the next one to be sent, so
        # the oldest waiting packet is drawn rightmost and later arrivals extend
        # to the left; any overflow is at the back of the queue, on the far left.
        self.empty_slots = ColumnDataSource(dict(left=[], right=[]))
        plot.quad(
            left="left",
            right="right",
            bottom=1.0,
            top=1.62,
            source=self.empty_slots,
            fill_color="#FFFFFF",
            line_color=NEUTRAL,
            line_width=1.5,
            line_dash=[4, 3],
        )
        self.waiting = ColumnDataSource(dict(left=[], right=[], x=[], y=[], text=[]))
        plot.quad(
            left="left",
            right="right",
            bottom=1.0,
            top=1.62,
            source=self.waiting,
            fill_color=WAIT_FILL,
            line_color=WAIT_EDGE,
            line_width=2,
        )
        _text(plot, self.waiting, size="13px")
        self.overflow = ColumnDataSource(dict(x=[2.05], y=[1.8], text=[""]))
        plot.text(
            "x",
            "y",
            text="text",
            source=self.overflow,
            text_font=value(FONT),
            text_font_size="12px",
            text_color=NEUTRAL,
            text_baseline="middle",
        )

        # Server, with a bar showing how much of the packet has been sent. The
        # background, the progress bar, and the outline are separate glyphs so
        # the bar never covers the outline.
        plot.quad(
            left=6.0,
            right=8.0,
            bottom=0.95,
            top=1.67,
            fill_color=SERVE_FILL,
            line_color=None,
        )
        self.progress = ColumnDataSource(dict(right=[6.0]))
        plot.quad(
            left=6.0,
            right="right",
            bottom=0.95,
            top=1.67,
            source=self.progress,
            fill_color=DONE_FILL,
            line_color=None,
        )
        plot.quad(
            left=6.0,
            right=8.0,
            bottom=0.95,
            top=1.67,
            fill_color=None,
            line_color=SERVE_EDGE,
            line_width=2,
        )
        self.server = ColumnDataSource(
            dict(x=[7.0], y=[1.31], text=["idle"], color=[NEUTRAL])
        )
        plot.text(
            "x",
            "y",
            text="text",
            source=self.server,
            text_font=value(FONT),
            text_font_size="13px",
            text_color="color",
            text_align="center",
            text_baseline="middle",
        )
        return plot

    def _strip_figure(self) -> figure:
        """Build the occupancy strip with a cursor at the current instant."""
        grid, occupancy = _occupancy_series(self.timeline, self.t0, self.t1)
        plot = new_plot(
            "Packets in the system across the window",
            "Time [s]",
            "In system [–]",
            width=WIDTH,
            height=220,
            x_range=(self.t0, self.t1),
            y_range=(0, max(3, int(occupancy.max()) + 1)),
        )
        plot.step(grid, occupancy, mode="after", line_color=WAIT_EDGE, line_width=2)
        self.cursor = Span(
            location=self.t0,
            dimension="height",
            line_color=CURSOR,
            line_width=2,
            line_dash="dashed",
        )
        plot.add_layout(self.cursor)
        return plot

    def show(self, t: float) -> None:
        """
        Redraw the picture, the cursor, and the counters for instant t.

        Parameters
        ----------
        t : float
            Instant to show [s].
        """
        timeline = self.timeline
        waiting, serving = queue_state(timeline, t)
        shown = waiting[:SLOTS]
        # Slot SLOTS - 1 (rightmost) holds position 0, the next packet to send.
        occupied = [SLOTS - 1 - position for position in range(len(shown))]
        self.waiting.data = dict(
            left=[SLOT_X[slot] for slot in occupied],
            right=[SLOT_X[slot] + 0.52 for slot in occupied],
            x=[SLOT_X[slot] + 0.26 for slot in occupied],
            y=[1.31] * len(occupied),
            text=[f"{int(timeline.size[packet])}" for packet in shown],
        )
        free = [slot for slot in range(SLOTS) if slot not in occupied]
        self.empty_slots.data = dict(
            left=[SLOT_X[slot] for slot in free],
            right=[SLOT_X[slot] + 0.52 for slot in free],
        )
        extra = len(waiting) - SLOTS
        self.overflow.data = dict(
            x=[2.05], y=[1.8], text=[f"+ {extra} further back" if extra > 0 else ""]
        )

        if serving is None:
            done = 0.0
            self.server.data = dict(x=[7.0], y=[1.31], text=["idle"], color=[NEUTRAL])
        else:
            span = timeline.depart[serving] - timeline.start[serving]
            done = 0.0 if span <= 0 else (t - timeline.start[serving]) / span
            self.server.data = dict(
                x=[7.0],
                y=[1.31],
                text=[f"{int(timeline.size[serving])} B, {done:.0%} sent"],
                color=[INK],
            )
        self.progress.data = dict(right=[6.0 + 2.0 * done])
        self.cursor.location = t

        in_system = len(waiting) + (serving is not None)
        self.card.object = card_html(
            f"At t = {t:.2f} s",
            [
                ("Waiting, <em>L</em><sub>q</sub> [–]", f"{len(waiting)}"),
                ("In system, <em>L</em> [–]", f"{in_system}"),
            ],
            note="A packet leaving the buffer for the server lowers "
            "<em>L</em><sub>q</sub> by one and leaves <em>L</em> unchanged.",
        )


def queue_view(
    sink,
    rate: float,
    t0: float | None = None,
    t1: float | None = None,
    length: float = 60.0,
    after: float = 0.0,
    step: float = 0.2,
    interval: int = 150,
) -> pn.Column:
    """
    Show the queue as an interactive, playable view over a time window.

    Parameters
    ----------
    sink : PacketSink
        Sink fed directly by the port of interest.
    rate : float
        Transmission rate of that port [bit/s].
    t0, t1 : float, optional
        Window to inspect [s]. Left out, the busiest window of `length`
        seconds starting no earlier than `after` is chosen, because at a low
        utilization a window picked at random is usually empty.
    length : float, optional
        Length of the automatically chosen window [s], by default 60.0.
    after : float, optional
        Earliest time that window may start [s], by default 0.0. Pass the
        warm-up to keep the view inside the steady state.
    step : float, optional
        Time between two positions of the slider [s], by default 0.2. A mean
        packet takes 0.8 s to transmit here, so this still shows the server
        filling up gradually.
    interval : int, optional
        Milliseconds between two positions while playing, by default 150.

    Returns
    -------
    panel.Column
        The player, the picture with its counters, and the occupancy strip.
        Returned as the last value of a cell, it is displayed there.
    """
    timeline = packet_timeline(sink, rate)
    if t0 is None:
        t0, t1 = busiest_window(timeline, length, after)
    elif t1 is None:
        t1 = t0 + length
    frames = max(1, round((t1 - t0) / step))

    view = QueueView(timeline, t0, t1)
    view.show(t0)
    player = pn.widgets.Player(
        name="Time",
        start=0,
        end=frames,
        value=0,
        step=1,
        interval=interval,
        loop_policy="once",
        show_value=False,
        show_loop_controls=False,
        width=WIDTH,
    )
    player.param.watch(lambda event: view.show(t0 + event.new * step), "value")
    return pn.Column(
        player,
        pn.Row(view.state, pn.Column(pn.Spacer(height=20), view.card)),
        view.strip,
    )
