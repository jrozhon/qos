"""
Analysis of captured RTP streams: timing, loss, bursts, and jitter.

A receiver knows three things about every RTP packet: when it arrived, its
sequence number, and its timestamp. Everything Wireshark reports under
*Telephony → RTP → RTP Streams* follows from these, and so does everything
here:

- :func:`rtp_stream` reads the RTP packets of one stream from a capture file
  or from packets sniffed in the notebook into a table; :func:`list_streams`
  lists the streams of a capture to choose from.
- :func:`stream_stats` counts lost, duplicated, and reordered packets, the
  lengths of loss bursts, and the interarrival jitter of RFC 3550.
- :func:`interarrival_view`, :func:`interarrival_histogram`,
  :func:`jitter_view`, and :func:`burst_view` draw them, and
  :func:`analyze_capture` (or :func:`stream_view` for a stream already read)
  puts all of it on one dashboard.
- :func:`sniff_during` captures the packets sent by a function running in the
  same notebook, :func:`skip_loopback_copies` removes the second copy of each
  packet that Scapy sees on the loopback interface, and :func:`decode_rtp`
  turns a received stream back into audio, with silence where packets are
  missing.
"""

import struct
import threading
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd
import panel as pn
import scapy.all as sa
from bokeh.core.properties import value
from bokeh.models import ColumnDataSource, HoverTool, Span

from lib.core import G711, SAMPLE_RATE
from lib.params import colors
from lib.plots import FONT, GREY, card, histogram, legend_below, new_plot

RED = "#E4002B"
ORANGE = colors[7]


# ---------------------------------------------------------------------------
# Reading a stream
# ---------------------------------------------------------------------------


def _unwrap(values, modulus: int) -> np.ndarray:
    """
    Undo the wrap-around of a counter, e.g. a 16-bit sequence number.

    Consecutive values are assumed to differ by less than half the modulus,
    which holds for any realistic loss or reordering.
    """
    v = np.asarray(values, dtype=np.int64)
    if v.size == 0:
        return v
    step = (np.diff(v) + modulus // 2) % modulus - modulus // 2
    return np.concatenate([[v[0]], v[0] + np.cumsum(step)])


def _rtp_table(source, dport: int | None = None) -> pd.DataFrame:
    """Parse every RTP packet of a capture, of all streams, into a table."""
    packets = sa.rdpcap(str(source)) if isinstance(source, str | Path) else source
    rows = []
    for pkt in packets:
        if sa.UDP not in pkt or (dport is not None and pkt[sa.UDP].dport != dport):
            continue
        data = bytes(pkt[sa.UDP].payload)
        if len(data) < 12 or data[0] >> 6 != 2:  # too short, or not RTP version 2
            continue
        first, second, seq, timestamp, source_id = struct.unpack("!BBHII", data[:12])
        header = 12 + 4 * (first & 0x0F)  # fixed header + contributing sources
        if first & 0x10 and len(data) >= header + 4:  # header extension
            header += 4 + 4 * struct.unpack("!H", data[header + 2 : header + 4])[0]
        rows.append(
            dict(
                time=float(pkt.time),
                seq=seq,
                timestamp=timestamp,
                ssrc=source_id,
                marker=second >> 7,
                payload_type=second & 0x7F,
                payload=data[header:],
                rtp=data,
                src=pkt[sa.IP].src if sa.IP in pkt else None,
                dst=pkt[sa.IP].dst if sa.IP in pkt else None,
                dport=pkt[sa.UDP].dport,
                dscp=pkt[sa.IP].tos >> 2 if sa.IP in pkt else None,
                ttl=pkt[sa.IP].ttl if sa.IP in pkt else None,
            )
        )
    return pd.DataFrame(rows)


def list_streams(source, dport: int | None = None) -> pd.DataFrame:
    """
    List the RTP streams of a capture, like Wireshark's RTP Streams window.

    Parameters
    ----------
    source : str, pathlib.Path, or list of scapy.packet.Packet
        A pcap or pcapng file, or captured packets.
    dport : int, optional
        Keep only packets to this UDP destination port.

    Returns
    -------
    pandas.DataFrame
        One row per SSRC, largest first, with the addresses, the destination
        port, the payload type, and the number of packets. Pass the ``ssrc``
        of the chosen row to :func:`rtp_stream`.
    """
    table = _rtp_table(source, dport)
    if table.empty:
        raise ValueError("no RTP packets found; check the port and the capture")
    streams = table.groupby("ssrc").agg(
        src=("src", "first"),
        dst=("dst", "first"),
        dport=("dport", "first"),
        payload_type=("payload_type", "first"),
        packets=("seq", "size"),
    )
    streams = streams.sort_values("packets", ascending=False).reset_index()
    streams.insert(1, "ssrc_hex", streams["ssrc"].map(lambda v: f"0x{v:08x}"))
    return streams


def rtp_stream(source, dport: int | None = None, ssrc: int | None = None):
    """
    Read the RTP packets of one stream into a table, in order of arrival.

    The RTP header is parsed from the UDP payload directly, so the packets do
    not need to be decoded as RTP by Scapy or Wireshark first.

    Parameters
    ----------
    source : str, pathlib.Path, or list of scapy.packet.Packet
        A pcap or pcapng file, or packets returned by :func:`sniff_during`
        or ``sniff``.
    dport : int, optional
        Keep only packets to this UDP destination port.
    ssrc : int, optional
        Keep only this synchronization source. Left out, the SSRC with the
        most packets is taken.

    Returns
    -------
    pandas.DataFrame
        One row per packet with the columns ``time`` (arrival time relative
        to the first packet [s]), ``seq``, ``timestamp``, ``ssrc``,
        ``marker``, ``payload_type``, ``payload`` (the codec bytes), ``rtp``
        (the whole UDP payload: RTP header and codec bytes), ``src``, ``dst``,
        ``dport``, ``dscp`` (the Differentiated Services code point of the IP
        header), ``ttl``, and ``ext_seq`` and ``ext_ts``, the sequence number
        and timestamp with their wrap-around undone.
    """
    table = _rtp_table(source, dport)
    if table.empty:
        raise ValueError("no RTP packets found; check the port and the capture")
    if ssrc is None:
        ssrc = int(table["ssrc"].mode()[0])
    table = table[table["ssrc"] == ssrc].reset_index(drop=True)
    if table.empty:
        raise ValueError(f"no packets with SSRC 0x{ssrc:08x}")
    table["time"] -= table["time"].iloc[0]
    table["ext_seq"] = _unwrap(table["seq"], 2**16)
    table["ext_ts"] = _unwrap(table["timestamp"], 2**32)
    return table


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def rfc3550_jitter(arrival, timestamp, rate: int = SAMPLE_RATE) -> np.ndarray:
    """
    Compute the interarrival jitter estimate of RFC 3550, Section 6.4.1.

    For consecutive packets i−1 and i, the difference between their spacing
    at the receiver and their spacing at the sender is

        D = (R_i − R_{i−1}) − (S_i − S_{i−1})

    where R is the arrival time and S the RTP timestamp, both in timestamp
    units. The estimate is a running mean of |D| with gain 1/16,
    ``J += (|D| − J) / 16``, which is what RTCP receiver reports and
    Wireshark show.

    Parameters
    ----------
    arrival : array_like of float
        Arrival times in order of arrival [s].
    timestamp : array_like of int
        RTP timestamps with wrap-around undone, same order [–].
    rate : int, optional
        RTP clock rate, by default 8000 Hz.

    Returns
    -------
    numpy.ndarray
        The estimate after every packet [ms]; 0 for the first packet.
    """
    r = np.asarray(arrival, dtype=float) * rate
    s = np.asarray(timestamp, dtype=float)
    d = np.abs(np.diff(r) - np.diff(s))
    jitter = np.zeros(len(r))
    for i, step in enumerate(d, start=1):
        jitter[i] = jitter[i - 1] + (step - jitter[i - 1]) / 16
    return jitter / rate * 1000


def _runs(values: np.ndarray) -> np.ndarray:
    """Lengths of the runs of consecutive integers in a sorted array."""
    if values.size == 0:
        return np.array([], dtype=int)
    breaks = np.nonzero(np.diff(values) != 1)[0]
    edges = np.concatenate([[-1], breaks, [values.size - 1]])
    return np.diff(edges)


def stream_stats(
    stream: pd.DataFrame,
    expected: int | None = None,
    first_sequence: int | None = None,
    rate: int = SAMPLE_RATE,
) -> dict:
    """
    Count losses, bursts, reordering, and jitter of a received stream.

    Parameters
    ----------
    stream : pandas.DataFrame
        Table from :func:`rtp_stream`.
    expected : int, optional
        Number of packets sent. Left out, it is inferred from the lowest and
        highest sequence number received, which misses losses at the start
        and at the end of the stream.
    first_sequence : int, optional
        Sequence number of the first packet sent, by default the lowest one
        received. Give it together with `expected` to count losses at the
        start.
    rate : int, optional
        RTP clock rate, by default 8000 Hz.

    Returns
    -------
    dict
        ``received``, ``expected``, ``lost``, ``loss`` [%], ``duplicates``,
        ``reordered``, ``lost_seq`` (the missing extended sequence numbers),
        ``bursts`` (lengths of the runs of consecutive losses), ``interarrival``
        [ms], ``jitter`` (the RFC 3550 estimate after every packet [ms]), and
        ``duration`` of the capture [s].
    """
    seq = stream["ext_seq"].to_numpy()
    received = np.unique(seq)
    first = int(received[0])
    if first_sequence is not None:
        # The extended number of the first packet sent: at most the lowest
        # one received, and equal to first_sequence modulo 2**16.
        first -= (first - first_sequence) % 2**16
    if expected is None:
        expected = int(received[-1] - first + 1)
    sent = np.arange(first, first + expected)
    lost = np.setdiff1d(sent, received)
    running_max = np.maximum.accumulate(seq)
    times = stream["time"].to_numpy()
    return dict(
        received=int(received.size),
        expected=int(expected),
        lost=int(lost.size),
        loss=100 * lost.size / expected,
        duplicates=int(seq.size - received.size),
        reordered=int(np.sum(seq[1:] < running_max[:-1])),
        lost_seq=lost,
        bursts=_runs(lost),
        interarrival=np.diff(times) * 1000,
        jitter=rfc3550_jitter(times, stream["ext_ts"].to_numpy(), rate),
        duration=float(times[-1] - times[0]),
    )


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


def stream_card(stats: dict, title: str = "Received stream", nominal_ms: float = 20):
    """
    Summarize :func:`stream_stats` in a result card.

    Parameters
    ----------
    stats : dict
        Output of :func:`stream_stats`.
    title : str, optional
        Card heading, by default "Received stream".
    nominal_ms : float, optional
        Packetization interval of the sender [ms], by default 20.

    Returns
    -------
    panel.pane.HTML
        The card.
    """
    ia = stats["interarrival"]
    bursts = stats["bursts"]
    return card(
        title,
        [
            (
                "Packets received / sent [–]",
                f"{stats['received']} / {stats['expected']}",
            ),
            ("Packet loss [%]", f"{stats['loss']:.2f} &nbsp;({stats['lost']} packets)"),
            (
                "Loss bursts [–]",
                f"{bursts.size}, mean length {bursts.mean():.2f}"
                if bursts.size
                else "0",
            ),
            (
                "Reordered / duplicated [–]",
                f"{stats['reordered']} / {stats['duplicates']}",
            ),
            (
                "Interarrival mean ± std [ms]",
                f"{ia.mean():.2f} ± {ia.std():.2f} &nbsp;(nominal {nominal_ms:g})"
                if ia.size
                else "–",
            ),
            (
                "Interarrival min / max [ms]",
                f"{ia.min():.2f} / {ia.max():.2f}" if ia.size else "–",
            ),
            (
                "Jitter mean / max [ms]",
                f"{stats['jitter'][1:].mean():.2f} / {stats['jitter'].max():.2f}"
                if stats["jitter"].size > 1
                else "–",
            ),
        ],
        note="Loss counts sequence numbers never received. Reordered: arrived "
        "after a packet with a higher sequence number. Compare the jitter with "
        "Wireshark, Telephony → RTP → RTP Streams.",
    )


def interarrival_view(stream: pd.DataFrame, stats: dict, nominal_ms: float = 20):
    """
    Plot the time since the previous packet against the sequence number.

    Lost packets are marked on the horizontal axis; reordered packets, which
    arrive after a packet with a higher sequence number, are highlighted.

    Parameters
    ----------
    stream : pandas.DataFrame
        Table from :func:`rtp_stream`.
    stats : dict
        Output of :func:`stream_stats` for the same stream.
    nominal_ms : float, optional
        Packetization interval of the sender [ms], by default 20.

    Returns
    -------
    panel.pane.Bokeh
        The plot.
    """
    seq = stream["ext_seq"].to_numpy()[1:]
    ia = stats["interarrival"]
    late = seq < np.maximum.accumulate(stream["ext_seq"].to_numpy())[:-1]
    plot = new_plot(
        "Interarrival time of each packet",
        "Sequence number [–]",
        "Time since previous packet [ms]",
        width=700,
    )
    for mask, color, label in (
        (~late, colors[0], "in order"),
        (late, ORANGE, "reordered"),
    ):
        if mask.any():
            source = ColumnDataSource(dict(seq=seq[mask], ia=ia[mask]))
            plot.scatter(
                "seq",
                "ia",
                source=source,
                size=5,
                color=color,
                alpha=0.7,
                legend_label=label,
            )
    if stats["lost"]:
        plot.scatter(
            stats["lost_seq"],
            np.zeros(stats["lost"]),
            marker="triangle",
            size=9,
            color=RED,
            legend_label="lost",
        )
    plot.add_layout(
        Span(
            location=nominal_ms,
            dimension="width",
            line_color=GREY,
            line_dash="dashed",
            line_width=2,
        )
    )
    plot.add_tools(
        HoverTool(tooltips=[("sequence", "@seq"), ("interarrival", "@ia{0.00} ms")])
    )
    return pn.pane.Bokeh(legend_below(plot))


def interarrival_histogram(
    streams: dict[str, dict],
    nominal_ms: float = 20,
    title: str = "Histogram of interarrival times",
):
    """
    Overlay the interarrival-time histograms of several streams.

    Parameters
    ----------
    streams : dict[str, dict]
        Legend label → output of :func:`stream_stats`.
    nominal_ms : float, optional
        Packetization interval of the sender [ms], by default 20.
    title : str, optional
        Plot title.

    Returns
    -------
    panel.pane.Bokeh
        The histograms, normalized to a probability density.
    """
    values = np.concatenate([s["interarrival"] for s in streams.values()])
    top = max(2 * nominal_ms, float(np.percentile(values, 99.5)))
    bins = np.linspace(0, top, 80)
    plot = new_plot(
        title,
        "Time since previous packet [ms]",
        "Probability density [1/ms]",
        width=700,
    )
    palette = [colors[0], colors[4], colors[5], colors[6]]
    for (label, s), color in zip(streams.items(), palette):
        histogram(
            plot,
            np.clip(s["interarrival"], 0, top),
            bins,
            color=color,
            alpha=0.5,
            label=label,
        )
    plot.add_layout(
        Span(
            location=nominal_ms,
            dimension="height",
            line_color=GREY,
            line_dash="dashed",
            line_width=2,
        )
    )
    plot.y_range.start = 0
    return pn.pane.Bokeh(legend_below(plot))


def jitter_view(stream: pd.DataFrame, stats: dict):
    """
    Plot the RFC 3550 jitter estimate as the stream progresses.

    Parameters
    ----------
    stream : pandas.DataFrame
        Table from :func:`rtp_stream`.
    stats : dict
        Output of :func:`stream_stats` for the same stream.

    Returns
    -------
    panel.pane.Bokeh
        The plot.
    """
    plot = new_plot(
        "Interarrival jitter (RFC 3550)",
        "Arrival time [s]",
        "Jitter [ms]",
        width=700,
        height=300,
    )
    plot.line(
        stream["time"], stats["jitter"], line_width=3, line_alpha=0.6, color=colors[0]
    )
    plot.y_range.start = 0
    return pn.pane.Bokeh(plot)


def burst_view(stats: dict, R: float | None = None):
    """
    Compare the lengths of loss bursts with the geometric distribution.

    In the Gilbert–Elliott model with 100 % loss in the bad state, the chain
    leaves the bad state after each packet with probability R, so a burst has
    length k with probability (1 − R)^(k−1) · R and mean 1/R. Independent
    loss with probability p is the special case R = 1 − p: almost all bursts
    are a single packet.

    Parameters
    ----------
    stats : dict
        Output of :func:`stream_stats`.
    R : float, optional
        Bad-to-good transition probability configured in netem [%]. Left out,
        the geometric distribution with the measured mean is drawn instead.

    Returns
    -------
    panel.pane.Bokeh
        Relative frequency of each burst length with the model overlaid.
    """
    bursts = stats["bursts"]
    plot = new_plot(
        "Lengths of loss bursts",
        "Burst length [packets]",
        "Relative frequency [–]",
        width=500,
        height=400,
    )
    if bursts.size == 0:
        plot.title.text = "Lengths of loss bursts: no losses"
        plot.text(
            [0],
            [0],
            text=["no packet was lost"],
            text_align="center",
            text_font=value(FONT),
        )
        return pn.pane.Bokeh(plot)
    k = np.arange(1, max(int(bursts.max()), 5) + 1)
    freq = np.array([(bursts == n).mean() for n in k])
    plot.vbar(
        x=k, top=freq, width=0.8, color=colors[0], alpha=0.8, legend_label="measured"
    )
    r = R / 100 if R is not None else 1 / bursts.mean()
    label = f"geometric, R = {100 * r:.1f} %" + (
        "" if R is not None else " (same mean)"
    )
    plot.line(
        k,
        (1 - r) ** (k - 1) * r,
        line_width=2,
        color=GREY,
        line_dash="dashed",
        legend_label=label,
    )
    plot.scatter(k, (1 - r) ** (k - 1) * r, size=6, color=GREY)
    plot.xaxis.ticker = list(k)
    plot.y_range.start = 0
    return pn.pane.Bokeh(legend_below(plot))


def analyze_capture(
    source,
    dport: int | None = None,
    ssrc: int | None = None,
    expected: int | None = None,
    first_sequence: int | None = None,
    R: float | None = None,
    title: str = "Received stream",
    nominal_ms: float = 20,
):
    """
    Read one RTP stream and show its timing, loss, and jitter on one dashboard.

    Parameters
    ----------
    source : str, pathlib.Path, or list of scapy.packet.Packet
        Capture file or sniffed packets, as for :func:`rtp_stream`.
    dport, ssrc : int, optional
        Stream selection, as for :func:`rtp_stream`.
    expected, first_sequence : int, optional
        Packets sent and the first sequence number, as for
        :func:`stream_stats`.
    R : float, optional
        Gilbert–Elliott R [%] for the burst plot, as for :func:`burst_view`.
    title : str, optional
        Heading of the result card.
    nominal_ms : float, optional
        Packetization interval of the sender [ms], by default 20.

    Returns
    -------
    panel.Column
        The dashboard.
    """
    stream = rtp_stream(source, dport=dport, ssrc=ssrc)
    stats = stream_stats(stream, expected=expected, first_sequence=first_sequence)
    return stream_view(stream, stats, R=R, title=title, nominal_ms=nominal_ms)


def stream_view(
    stream: pd.DataFrame,
    stats: dict,
    R: float | None = None,
    title: str = "Received stream",
    nominal_ms: float = 20,
):
    """
    Lay out the plots and the card of one stream already read and counted.

    Parameters
    ----------
    stream : pandas.DataFrame
        Table from :func:`rtp_stream`.
    stats : dict
        Output of :func:`stream_stats` for the same stream.
    R, title, nominal_ms
        As for :func:`analyze_capture`.

    Returns
    -------
    panel.Column
        The dashboard.
    """
    return pn.Column(
        pn.Row(
            interarrival_view(stream, stats, nominal_ms),
            stream_card(stats, title, nominal_ms),
            align="start",
        ),
        pn.Row(jitter_view(stream, stats), burst_view(stats, R), align="start"),
    )


# ---------------------------------------------------------------------------
# Capturing and decoding in the notebook
# ---------------------------------------------------------------------------


def skip_loopback_copies(window: float = 0.001) -> Callable[[sa.Packet], bool]:
    """
    Make a ``sniff`` filter that passes each loopback packet only once.

    On the loopback interface Scapy's sniffer receives every packet twice:
    once as it leaves and once as it arrives. (``tcpdump -i lo`` hides the
    outgoing copy; Scapy does not.) The two copies are byte-identical and a few
    microseconds apart, so a packet that repeats the previous one within
    `window` seconds is dropped. On other interfaces such repeats do not
    occur, except for duplicates created on purpose, e.g. by netem.

    A capture filter cannot do this: Scapy 2.7 compiles filters without
    opening the interface, and libpcap then rejects ``inbound``/``outbound``.

    Parameters
    ----------
    window : float, optional
        Longest time between the two copies [s], by default 1 ms.

    Returns
    -------
    callable
        Use as ``sa.sniff(..., lfilter=skip_loopback_copies())``; create a new
        one for every capture, since it remembers the previous packet.
    """
    last = [b"", float("-inf")]

    def first_copy(pkt: sa.Packet) -> bool:
        data, t = bytes(pkt), float(pkt.time)
        repeat = data == last[0] and t - last[1] < window
        last[0], last[1] = data, t
        return not repeat

    return first_copy


def sniff_during(
    action: Callable[[], object],
    iface: str,
    bpf: str = "udp",
    settle: float = 0.5,
) -> list:
    """
    Capture packets on an interface while a function runs.

    ``sniff`` blocks the notebook until it is stopped; an asynchronous
    sniffer runs in the background instead, so one notebook can send and
    capture at the same time. Packets leaving the interface are captured
    after the queueing discipline, so a ``tc netem`` delay or loss on that
    interface is visible in the capture.

    Parameters
    ----------
    action : callable
        Function without arguments that sends the packets, e.g.
        ``lambda: send_paced(packets)``.
    iface : str
        Interface to capture on.
    bpf : str, optional
        Capture filter in BPF syntax, by default ``"udp"``.
    settle : float, optional
        Time to keep capturing after the function returns [s], so that delayed
        packets are not cut off, by default 0.5. Raise it above the netem
        delay.

    Returns
    -------
    list of scapy.packet.Packet
        The captured packets with their arrival times in ``pkt.time``, each
        packet once also on the loopback interface.
    """
    started = threading.Event()
    sniffer = sa.AsyncSniffer(
        iface=iface,
        filter=bpf,
        lfilter=skip_loopback_copies(),  # see skip_loopback_copies
        started_callback=started.set,
    )
    sniffer.start()
    started.wait(timeout=5)
    try:
        action()
        time.sleep(settle)
    finally:
        sniffer.stop()
    return list(sniffer.results)


def decode_rtp(stream: pd.DataFrame, encoding: str = "alaw") -> np.ndarray:
    """
    Turn a received G.711 stream back into audio on the sender's timeline.

    Every payload is decoded and placed at the sample its RTP timestamp
    names, so missing packets leave gaps of silence and reordered packets
    land in the right place. Like ``reconstruct_rtp.py`` this is an offline
    receiver: it has no jitter buffer and no packet-loss concealment.

    Parameters
    ----------
    stream : pandas.DataFrame
        Table from :func:`rtp_stream`.
    encoding : {"alaw", "ulaw"}, optional
        G.711 variant of the payload, by default A-law.

    Returns
    -------
    numpy.ndarray of int16
        The audio at 8 kHz [–].
    """
    _, _, decode = G711[encoding]
    offsets = stream["ext_ts"] - stream["ext_ts"].min()
    length = int((offsets + stream["payload"].map(len)).max())
    if length > SAMPLE_RATE * 3600:
        raise ValueError(
            "the timestamps span more than an hour: the stream has a timestamp "
            "discontinuity; decode the parts before and after it separately"
        )
    audio = np.zeros(length, dtype=np.int16)  # silence where nothing arrived
    for offset, payload in zip(offsets, stream["payload"]):
        samples = decode(np.frombuffer(payload, dtype=np.uint8))
        audio[offset : offset + len(samples)] = samples
    return audio


# ---------------------------------------------------------------------------
# Recorded against created streams
# ---------------------------------------------------------------------------
#
# stream_summary and compare_streams put a recorded call next to the stream
# created in the notebook; sdp_view shows how the call's codec was negotiated.


def stream_summary(stream: pd.DataFrame, rate: int = SAMPLE_RATE) -> dict[str, str]:
    """
    Describe a stream by the properties in which senders differ.

    Parameters
    ----------
    stream : pandas.DataFrame
        Table from :func:`rtp_stream`.
    rate : int, optional
        RTP clock rate, by default 8000 Hz.

    Returns
    -------
    dict[str, str]
        Property name → formatted value: addresses, SSRC, payload type, first
        sequence number and timestamp, marker bits, payload sizes, timestamp
        steps, DSCP, TTL, packet spacing, and jitter.
    """
    stats = stream_stats(stream, rate=rate)
    ia = stats["interarrival"]
    steps = np.diff(stream.sort_values("ext_seq")["ext_ts"].to_numpy())
    usual = int(pd.Series(steps).mode()[0]) if steps.size else 0
    odd = steps[steps != usual]
    first = stream.iloc[0]
    sizes = sorted(set(stream["payload"].map(len)))
    return {
        "From → to": f"{first['src']} → {first['dst']}:{first['dport']}",
        "SSRC": f"0x{first['ssrc']:08x}",
        "Payload type": ", ".join(str(v) for v in sorted(set(stream["payload_type"]))),
        "Packets": f"{len(stream)}",
        "First sequence number": f"{first['seq']}",
        "First timestamp": f"{first['timestamp']}",
        "Packets with marker bit": f"{int(stream['marker'].sum())}",
        "Payload sizes [B]": ", ".join(str(v) for v in sizes[:4])
        + (" …" if len(sizes) > 4 else ""),
        "Timestamp step": f"{usual}"
        + (f"; {odd.size} other, largest {int(np.abs(odd).max())}" if odd.size else ""),
        "DSCP": f"{first['dscp']}" + (" (EF)" if first["dscp"] == 46 else ""),
        "TTL": f"{first['ttl']}",
        "Spacing mean ± std [ms]": f"{ia.mean():.3f} ± {ia.std():.2f}"
        if ia.size
        else "–",
        "Spacing min / max [ms]": f"{ia.min():.2f} / {ia.max():.2f}"
        if ia.size
        else "–",
        "Jitter mean [ms]": f"{stats['jitter'][1:].mean():.2f}"
        if stats["jitter"].size > 1
        else "–",
    }


def compare_streams(streams: dict[str, pd.DataFrame], nominal_ms: float = 20):
    """
    Put several RTP streams side by side: header fields, timing, first header.

    Parameters
    ----------
    streams : dict[str, pandas.DataFrame]
        Label → table from :func:`rtp_stream`, e.g. a recorded call and the
        stream created in the notebook.
    nominal_ms : float, optional
        Packetization interval [ms] marked in the histogram, by default 20.

    Returns
    -------
    panel.Column
        A table with one column per stream, the overlaid histograms of the
        packet spacing, and tabs with the RTP header of each stream's first
        packet.
    """
    from lib.packetviz import header_diagram  # avoids a circular import

    summaries = {label: stream_summary(t) for label, t in streams.items()}
    keys = list(next(iter(summaries.values())))
    cell = "padding:3px 14px 3px 0;border-bottom:1px solid #E5E5E5"
    head = "".join(
        f"<th style='text-align:left;padding:4px 14px 4px 0;"
        f"border-bottom:2px solid {colors[0]}'>{h}</th>"
        for h in ["Property", *summaries]
    )
    body = "".join(
        f"<tr><td style='{cell}'>{k}</td>"
        + "".join(
            f"<td style='{cell}'>{summary[k]}</td>" for summary in summaries.values()
        )
        + "</tr>"
        for k in keys
    )
    table = pn.pane.HTML(
        f"<div style='font-family:{FONT};font-size:14px;color:#292929'>"
        f"<table style='border-collapse:collapse'><tr>{head}</tr>{body}</table></div>"
    )
    histogram_view = interarrival_histogram(
        {label: stream_stats(t) for label, t in streams.items()},
        nominal_ms=nominal_ms,
        title="Packet spacing by stream",
    )
    headers = pn.Tabs(
        *[
            (label, header_diagram(sa.RTP(t.sort_values("ext_seq")["rtp"].iloc[0])))
            for label, t in streams.items()
        ]
    )
    return pn.Column(table, histogram_view, headers)


# Static RTP payload types for audio that appear in SIP offers (RFC 3551, Table 4)
STATIC_PAYLOAD_TYPES = {
    "0": "PCMU/8000",
    "3": "GSM/8000",
    "8": "PCMA/8000",
    "9": "G722/8000",
    "18": "G729/8000",
}


def sdp_view(source) -> pn.Row:
    """
    Show the codec negotiation of a call: the SDP offer and answer in SIP.

    Parameters
    ----------
    source : str, pathlib.Path, or list of scapy.packet.Packet
        A capture that includes the SIP signaling of the call.

    Returns
    -------
    panel.Row
        One card per distinct SDP body: the SIP start line, the media line
        (port, transport, offered payload types), the payload-type mappings,
        and the packetization time.
    """
    packets = sa.rdpcap(str(source)) if isinstance(source, str | Path) else source
    # An INVITE with a long offer can exceed the MTU and arrive IP-fragmented.
    packets = sa.defragment(list(packets))
    bodies = {}
    for pkt in packets:
        if sa.UDP not in pkt:
            continue
        text = bytes(pkt[sa.UDP].payload).decode("utf-8", errors="replace")
        if "\r\n\r\n" not in text or "m=audio" not in text:
            continue
        start, _, body = text.partition("\r\n")[0], None, text.split("\r\n\r\n", 1)[1]
        lines = [line.strip() for line in body.splitlines()]
        media = next(line[2:] for line in lines if line.startswith("m=audio"))
        rtpmap = [line[9:] for line in lines if line.startswith("a=rtpmap:")]
        mapped = {entry.split()[0] for entry in rtpmap}
        # Static payload types need no rtpmap line (RFC 3551, Table 4).
        rtpmap = [
            f"{pt} {STATIC_PAYLOAD_TYPES[pt]} (static)"
            if pt in STATIC_PAYLOAD_TYPES and pt not in mapped
            else next((e for e in rtpmap if e.split()[0] == pt), f"{pt} (no rtpmap)")
            for pt in media.split()[3:]
        ]
        ptime = [line[2:] for line in lines if line.startswith("a=ptime")]
        bodies[(start.split()[0], media)] = (start, media, rtpmap, ptime)
    if not bodies:
        return pn.Row(
            card(
                "No SDP found",
                [],
                note="The capture holds no SIP message with an SDP body.",
            )
        )
    cards = []
    for start, media, rtpmap, ptime in bodies.values():
        cards.append(
            card(
                start.replace("SIP/2.0 ", "Answer: ")
                if start.startswith("SIP/2.0")
                else "Offer: " + start.split()[0],
                [
                    ("Media line", media),
                    ("Payload types", "<br>".join(rtpmap) or "static types only"),
                    ("Packetization", ", ".join(ptime) or "not stated (default 20 ms)"),
                ],
                width=460,
            )
        )
    return pn.Row(*cards, align="start")
