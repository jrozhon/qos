"""
An interactive view of packets passing through a single-server queue.

The averages of Step 4 say what the queue does on average; this module shows
the mechanism they average over. Dragging the time slider moves through the
run one instant at a time, showing which packets are waiting in the buffer,
which one is being transmitted and how far it has got, and how the two
occupancy counters follow from that picture.

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

import matplotlib.pyplot as plt
import numpy as np

from lib.core import BYTES_TO_BITS

WAIT_FILL, WAIT_EDGE = "#E6F6F5", "#00A499"
CURSOR = "#0047BB"  # blue, so the time cursor is never read as teal data
SERVE_FILL, SERVE_EDGE = "#E6F9FC", "#05C3DE"
DONE_FILL = "#B2E4E0"
NEUTRAL, INK = "#818386", "#292929"
SLOTS = 6  # buffer positions drawn before the queue is summarized as "+ n more"
WIDTH_IN, HEIGHT_IN = 10, 5  # frame size [in]; fixed so playback does not jump


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


def _draw_packet(ax, x, y, width, height, fill, edge, label):
    """Draw one packet box with its size written inside."""
    ax.add_patch(
        plt.Rectangle(
            (x, y), width, height, facecolor=fill, edgecolor=edge, linewidth=2
        )
    )
    ax.text(x + width / 2, y + height / 2, label, ha="center", va="center", fontsize=13)


def _draw_state(ax, timeline: Timeline, t: float) -> tuple:
    """
    Draw the buffer and the server as they stand at time t.

    Returns
    -------
    tuple[int, int]
        Packets waiting and packets in the system at that instant.
    """
    waiting, serving = queue_state(timeline, t)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2.6)
    ax.axis("off")

    ax.text(0.5, 1.3, "Source", ha="center", va="center", fontsize=14, weight="bold")
    ax.annotate(
        "",
        xy=(2.0, 1.3),
        xytext=(1.1, 1.3),
        arrowprops={"arrowstyle": "->", "color": INK, "linewidth": 2},
    )

    # Buffer: the packet nearest the server is the next one to be transmitted,
    # so waiting[0], the oldest, is drawn rightmost and later arrivals extend
    # to the left. Any overflow is at the back of the queue, on the far left.
    ax.text(3.7, 2.15, "Waiting queue", ha="center", fontsize=13, color=NEUTRAL)
    shown = waiting[:SLOTS]
    for slot in range(SLOTS):
        x = 2.1 + slot * 0.62
        position = SLOTS - 1 - slot  # 0 is nearest the server
        if position < len(shown):
            packet = shown[position]
            _draw_packet(
                ax,
                x,
                1.0,
                0.52,
                0.62,
                WAIT_FILL,
                WAIT_EDGE,
                f"{int(timeline.size[packet])}",
            )
        else:
            ax.add_patch(
                plt.Rectangle(
                    (x, 1.0),
                    0.52,
                    0.62,
                    facecolor="#FFFFFF",
                    edgecolor=NEUTRAL,
                    linewidth=1.5,
                    linestyle=(0, (4, 3)),
                )
            )
    if len(waiting) > SLOTS:
        ax.text(
            2.05,
            1.78,
            f"+ {len(waiting) - SLOTS} further back",
            ha="left",
            fontsize=12,
            color=NEUTRAL,
        )

    # Server, with a bar showing how much of the packet has been sent.
    ax.text(7.0, 2.15, "Server", ha="center", fontsize=13, color=NEUTRAL)
    ax.add_patch(
        plt.Rectangle(
            (6.0, 0.95),
            2.0,
            0.72,
            facecolor=SERVE_FILL,
            edgecolor=SERVE_EDGE,
            linewidth=2,
        )
    )
    if serving is None:
        ax.text(7.0, 1.31, "idle", ha="center", va="center", fontsize=14, color=NEUTRAL)
    else:
        span = timeline.depart[serving] - timeline.start[serving]
        done = 0.0 if span <= 0 else (t - timeline.start[serving]) / span
        ax.add_patch(
            plt.Rectangle(
                (6.0, 0.95), 2.0 * done, 0.72, facecolor=DONE_FILL, edgecolor="none"
            )
        )
        ax.text(
            7.0,
            1.31,
            f"{int(timeline.size[serving])} B, {done:.0%} sent",
            ha="center",
            va="center",
            fontsize=13,
        )

    ax.annotate(
        "",
        xy=(9.0, 1.3),
        xytext=(8.1, 1.3),
        arrowprops={"arrowstyle": "->", "color": INK, "linewidth": 2},
    )
    ax.text(9.5, 1.3, "Sink", ha="center", va="center", fontsize=14, weight="bold")

    in_system = len(waiting) + (0 if serving is None else 1)
    for x, text in (
        (0.0, f"t = {t:.2f} s"),
        (3.1, f"waiting  $L_q$ = {len(waiting)}"),
        (6.6, f"in system  $L$ = {in_system}"),
    ):
        ax.text(x, 0.25, text, fontsize=15, color=INK)
    return len(waiting), in_system


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


def _build_figure(timeline: Timeline, t: float, t0: float, t1: float, series):
    """
    Build the figure for one instant without displaying it.

    Parameters
    ----------
    timeline : Timeline
        Reconstructed packet timeline.
    t : float
        Instant to draw [s].
    t0, t1 : float
        Bounds of the window being inspected [s].
    series : tuple
        Occupancy series from :func:`_occupancy_series`.

    Returns
    -------
    matplotlib.figure.Figure
        The finished figure, still open.
    """
    grid, occupancy = series
    fig, (ax_state, ax_strip) = plt.subplots(
        2, 1, figsize=(WIDTH_IN, HEIGHT_IN), gridspec_kw={"height_ratios": [2, 1]}
    )
    _draw_state(ax_state, timeline, t)
    ax_strip.step(grid, occupancy, where="post", color=WAIT_EDGE, linewidth=2)
    ax_strip.axvline(t, color=CURSOR, linewidth=2, linestyle="--")
    ax_strip.set_xlim(t0, t1)
    ax_strip.set_ylim(0, max(3, int(occupancy.max()) + 1))
    ax_strip.set_xlabel("Time [s]")
    ax_strip.set_ylabel("In system [–]")
    fig.tight_layout(h_pad=2.0)
    return fig


def draw_frame(timeline: Timeline, t: float, t0: float, t1: float):
    """
    Draw the queue at time t above a strip locating t within the window.

    Parameters
    ----------
    timeline : Timeline
        Reconstructed packet timeline.
    t : float
        Instant to draw [s].
    t0, t1 : float
        Bounds of the window being inspected [s].
    """
    _build_figure(timeline, t, t0, t1, _occupancy_series(timeline, t0, t1))
    plt.show()


def queue_view(
    sink,
    rate: float,
    t0: float = None,
    t1: float = None,
    length: float = 60.0,
    after: float = 0.0,
    step: float = 0.2,
    dpi: int = 110,
    interval: int = 150,
):
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
        filling up gradually while keeping the number of frames modest.
    dpi : int, optional
        Resolution of each frame, by default 110. Every frame is sent to the
        browser as a picture, so a higher value costs bandwidth on a remote
        session without adding much at this size.
    interval : int, optional
        Milliseconds between frames while playing, by default 150. Rendering a
        frame takes roughly 65 ms, so this leaves room on a loaded machine.

    Notes
    -----
    The view is displayed as a side effect and nothing is returned, so that a
    notebook cell ending in this call does not render the controls twice.
    """
    import io

    import ipywidgets as widgets
    from IPython.display import display

    timeline = packet_timeline(sink, rate)
    if t0 is None:
        t0, t1 = busiest_window(timeline, length, after)
    elif t1 is None:
        t1 = t0 + length
    frames = max(1, int(round((t1 - t0) / step)))
    series = _occupancy_series(timeline, t0, t1)

    # Frames are kept once drawn. Drawing one costs about 65 ms, which is
    # close to the playback interval, so the first pass through the window can
    # stutter; afterwards every frame is already in hand and both playback and
    # dragging the slider are immediate. At the default step a window holds a
    # few hundred frames, on the order of ten megabytes.
    drawn: dict[int, bytes] = {}

    def render(frame):
        """Return one frame as PNG bytes, at a size that never varies."""
        if frame not in drawn:
            figure = _build_figure(timeline, t0 + frame * step, t0, t1, series)
            buffer = io.BytesIO()
            # bbox_inches=None overrides the "tight" default of rc_params: a
            # frame cropped to its own content would change size as the labels
            # change, and the picture would jump about during playback.
            figure.savefig(buffer, format="png", dpi=dpi, bbox_inches=None)
            plt.close(figure)
            drawn[frame] = buffer.getvalue()
        return drawn[frame]

    # The frame is swapped into an Image widget rather than written to an
    # Output widget. An Output is cleared and refilled for every frame, which
    # blanks the picture between frames and reads as flicker; assigning to
    # Image.value replaces the picture in place, and fixing the widget size
    # keeps the surrounding layout still.
    picture = widgets.Image(
        value=render(0), format="png", width=WIDTH_IN * 100, height=HEIGHT_IN * 100
    )
    play = widgets.Play(min=0, max=frames, step=1, value=0, interval=interval)
    cursor = widgets.IntSlider(min=0, max=frames, step=1, value=0, readout=False)
    widgets.jslink((play, "value"), (cursor, "value"))
    cursor.observe(
        lambda change: setattr(picture, "value", render(change["new"])),
        names="value",
    )
    display(widgets.VBox([widgets.HBox([play, cursor]), picture]))
