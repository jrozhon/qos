"""
Pictures of the packets crafted with Scapy and of the audio they carry.

Scapy prints a packet as text (``show``, ``show2``, ``hexdump``). The functions
here draw the same information so that the structure is visible at a glance:

- :func:`byte_map` – the bytes of a packet as a grid, colored by layer, with
  the field behind every byte on hover; the hexdump with its meaning attached.
- :func:`field_diff` – which header fields the program set and which Scapy
  filled in when the packet was finalized.
- :func:`header_diagram` – one header in the 32-bit-row layout of the RFCs,
  filled with the values of the packet.
- :func:`overhead_chart` – header bytes against payload bytes and the
  resulting bit rate for several packetization intervals.
- :func:`packetization_view` – a speech waveform cut into 20 ms blocks, each
  labelled with the RTP sequence number and timestamp it is sent with.
- :func:`companding_view` and :func:`roundtrip_view` – the G.711 characteristic
  and what encoding and decoding do to a block of speech.
"""

import numpy as np
import panel as pn
import scapy.all as sa
from bokeh.core.properties import value
from bokeh.models import (
    BoxAnnotation,
    ColumnDataSource,
    FactorRange,
    HoverTool,
    Range1d,
    Span,
)
from scapy.fields import _BitField
from scapy.packet import NoPayload

from lib.core import G711, SAMPLE_RATE
from lib.params import colors
from lib.plots import FONT, GREY, TEXT_COLOR, card, legend_below, new_plot

RED = "#E4002B"

# One solid palette color per protocol layer (STYLE.md §2.5), chosen so that
# neighbouring layers differ clearly in hue; anything else is drawn in grey.
LAYER_COLORS = {
    "Ethernet": GREY,
    "IP": colors[4],  # blue
    "ICMP": colors[6],  # purple
    "UDP": colors[6],  # purple
    "RTP": colors[0],  # teal
    "Raw": colors[3],  # yellow
}
TINT = "#E6F6F5"  # 10 % teal tint for background bands (STYLE.md §2.3)


def text_color_on(fill: str) -> str:
    """Label color readable on a fill: near-black on yellow, white otherwise."""
    return TEXT_COLOR if fill == colors[3] else "#ffffff"


# Short labels for fields too narrow for their Scapy name in a header diagram
SHORT_NAMES = {
    "version": "V",
    "padding": "P",
    "extension": "X",
    "numsync": "CC",
    "marker": "M",
    "payload_type": "PT",
    "ihl": "IHL",
    "flags": "flags",
    "sequence": "sequence number",
    "sourcesync": "SSRC",
}

# Fields read more easily in hexadecimal
HEX_FIELDS = {"sourcesync", "chksum"}

# Numeric fields whose symbolic name helps (protocol, ICMP type, payload type)
NAMED_FIELDS = {"proto", "type", "payload_type"}


# ---------------------------------------------------------------------------
# Packet structure
# ---------------------------------------------------------------------------


def finalize(packet: sa.Packet) -> sa.Packet:
    """
    Return the packet as it appears on the wire, with every field filled in.

    This is what ``show2`` prints: the packet is serialized, which computes
    lengths and checksums, and parsed back. The layers are parsed with the
    classes of the original packet, so an RTP layer stays RTP even when
    Scapy would not recognize it from the UDP port.

    Parameters
    ----------
    packet : scapy.packet.Packet
        A packet built with the ``/`` operator.

    Returns
    -------
    scapy.packet.Packet
        A new packet with the same layers and no unset (``None``) fields.
    """
    data = bytes(packet)
    result = None
    layer = packet
    while not isinstance(layer, NoPayload):
        parsed = layer.__class__(data)
        if isinstance(layer.payload, NoPayload):
            data = b""  # the innermost layer keeps the rest
        else:
            tail = bytes(parsed.payload)
            parsed.remove_payload()
            data = data[len(data) - len(tail) :]
        result = parsed if result is None else result / parsed
        layer = layer.payload
    return result


def _layer_name(layer: sa.Packet) -> str:
    """Name used for a layer in legends and color lookup."""
    return "Raw" if isinstance(layer, sa.Raw) else layer.__class__.__name__


def _format(field, layer: sa.Packet, raw=None) -> str:
    """Human-readable value of a field, with the name behind some numbers."""
    if raw is None:
        raw = layer.getfieldval(field.name)
    if raw is None:
        return "None"
    if isinstance(raw, sa.FlagValue):
        raw = int(raw)
    if field.name in HEX_FIELDS and isinstance(raw, int):
        return f"0x{raw:0{2 * max(1, int(field.sz))}x}"
    if field.name in NAMED_FIELDS:
        return f"{raw} ({field.i2repr(layer, raw)})"
    if isinstance(raw, int):
        return str(raw)
    return field.i2repr(layer, raw)


def packet_fields(packet: sa.Packet) -> list[dict]:
    """
    List the fields of a finalized packet with their position in bits.

    Parameters
    ----------
    packet : scapy.packet.Packet
        A packet built with the ``/`` operator; it is finalized first.

    Returns
    -------
    list of dict
        One entry per field, in wire order, with the keys ``layer`` (layer
        name), ``index`` (position of the layer, 0 for the outermost),
        ``name``, ``value`` (formatted for display), ``offset`` (first bit,
        counted from the start of the packet), and ``bits`` (width).
    """
    built = finalize(packet)
    _, layers = built.build_ps()
    entries, offset = [], 0
    # build_ps lists the innermost layer first.
    for index, (layer, fields) in enumerate(reversed(layers)):
        for field, _, chunk in fields:
            while hasattr(field, "fld"):  # unwrap Emph, ConditionalField
                field = field.fld
            # Bit fields of one byte group share a single chunk, which is
            # attached to the last of them; use their declared widths instead.
            bits = field.size if isinstance(field, _BitField) else 8 * len(chunk)
            if bits == 0:
                continue
            entries.append(
                dict(
                    layer=_layer_name(layer),
                    index=index,
                    name="payload" if isinstance(layer, sa.Raw) else field.name,
                    value=_format(field, layer),
                    offset=offset,
                    bits=bits,
                )
            )
            offset += bits
    if offset != 8 * len(bytes(built)):
        raise ValueError("could not map every bit of the packet to a field")
    return entries


def byte_map(packet: sa.Packet, columns: int = 16, title: str | None = None):
    """
    Draw the bytes of a packet as a grid colored by protocol layer.

    The layout is that of ``hexdump`` and of the bytes pane in Wireshark:
    ``columns`` bytes per row, offsets on the left. Hovering over a byte shows
    its offset, its value, and the field or fields it belongs to.

    Parameters
    ----------
    packet : scapy.packet.Packet
        A packet built with the ``/`` operator; it is finalized first.
    columns : int, optional
        Bytes per row, by default 16.
    title : str, optional
        Plot title, by default the layer names joined by " / ".

    Returns
    -------
    panel.pane.Bokeh
        The byte map.
    """
    data = bytes(finalize(packet))
    fields = packet_fields(packet)
    rows = (len(data) + columns - 1) // columns

    # For every byte: the layer of its first bit and every field it overlaps.
    layer_of = [""] * len(data)
    described = [[] for _ in data]
    for f in fields:
        first, last = f["offset"] // 8, (f["offset"] + f["bits"] - 1) // 8
        for i in range(first, last + 1):
            if not layer_of[i]:
                layer_of[i] = f["layer"]
            if f["name"] == "payload":
                described[i].append(
                    f"payload byte {i - first + 1} of {last - first + 1}"
                )
            else:
                described[i].append(f"{f['name']} = {f['value']}")

    layer_order = list(dict.fromkeys(f["layer"] for f in fields))
    plot = new_plot(
        title or " / ".join(layer_order),
        "Byte within the row [–]",
        "Offset [B]",
        width=36 * columns + 120,
        height=28 * rows + 110,
        x_range=Range1d(-0.5, columns - 0.5),
        y_range=Range1d(rows - 0.5, -0.5),  # first row on top
    )
    plot.grid.visible = False
    plot.xaxis.ticker = list(range(columns))
    plot.yaxis.ticker = list(range(rows))
    plot.yaxis.major_label_overrides = {r: f"{r * columns:04x}" for r in range(rows)}

    for name in layer_order:
        idx = [i for i in range(len(data)) if layer_of[i] == name]
        source = ColumnDataSource(
            dict(
                x=[i % columns for i in idx],
                y=[i // columns for i in idx],
                hex=[f"{data[i]:02x}" for i in idx],
                offset=[f"{i} (0x{i:04x})" for i in idx],
                layer=[name] * len(idx),
                fields=[", ".join(described[i]) for i in idx],
            )
        )
        plot.rect(
            "x",
            "y",
            0.92,
            0.86,
            source=source,
            fill_color=LAYER_COLORS.get(name, GREY),
            line_color=None,
            legend_label="payload" if name == "Raw" else name,
        )
        plot.text(
            "x",
            "y",
            text="hex",
            source=source,
            text_align="center",
            text_baseline="middle",
            text_font=value("DejaVu Sans Mono, monospace"),
            text_font_size="12px",
            text_color=text_color_on(LAYER_COLORS.get(name, GREY)),
        )
    plot.add_tools(
        HoverTool(
            tooltips=[
                ("offset", "@offset"),
                ("value", "0x@hex"),
                ("layer", "@layer"),
                ("field", "@fields"),
            ]
        )
    )
    return pn.pane.Bokeh(legend_below(plot))


def field_diff(packet: sa.Packet) -> pn.pane.HTML:
    """
    Tabulate the header fields as set by the program and as sent on the wire.

    Fields left unset (``None``) are computed by Scapy when the packet is
    finalized: lengths, checksums, the header length of IP. They are
    highlighted, because these are the fields a program would otherwise have
    to compute by hand.

    Parameters
    ----------
    packet : scapy.packet.Packet
        A packet built with the ``/`` operator.

    Returns
    -------
    panel.pane.HTML
        Table with one row per header field (payloads are left out).
    """
    built = finalize(packet)
    rows = []
    original, final = packet, built
    while not isinstance(original, NoPayload):
        if not isinstance(original, sa.Raw):
            for field in original.fields_desc:
                if not final.getfieldval(field.name) and field.name in (
                    "options",
                    "sync",
                ):
                    continue  # empty lists carry nothing
                before = original.getfieldval(field.name)
                user_set = field.name in original.fields
                after = final.getfieldval(field.name)
                rows.append(
                    (
                        _layer_name(original),
                        field.name,
                        "set"
                        if user_set
                        else ("default" if before is not None else "unset"),
                        _format(field, original, before),
                        _format(field, final, after),
                        before is None,
                    )
                )
        original, final = original.payload, final.payload

    head = "".join(
        f"<th style='text-align:left;padding:4px 12px 4px 0;border-bottom:2px solid "
        f"{colors[0]}'>{h}</th>"
        for h in ("Layer", "Field", "Origin", "Before finalization", "On the wire")
    )
    body = ""
    for layer, name, origin, before, after, filled in rows:
        style = "background:#E6F6F5;font-weight:bold;" if filled else ""
        cells = (layer, name, origin, before, after)
        body += "<tr style='{}'>{}</tr>".format(
            style,
            "".join(
                f"<td style='padding:2px 12px 2px 0;border-bottom:1px solid #E5E5E5'>"
                f"{c}</td>"
                for c in cells
            ),
        )
    note = (
        "Highlighted: fields left as None and computed by Scapy when the packet "
        "is serialized. <i>set</i>: given by the program; <i>default</i>: the "
        "value Scapy uses when nothing is given."
    )
    return pn.pane.HTML(
        f"<div style='font-family:{FONT};font-size:14px;color:{TEXT_COLOR}'>"
        f"<table style='border-collapse:collapse'><tr>{head}</tr>{body}</table>"
        f"<p style='margin:8px 0 0;font-size:13px;color:{GREY}'>{note}</p></div>"
    )


def header_diagram(packet: sa.Packet, layer: str = "RTP", bit_width: int = 22):
    """
    Draw one header in the 32-bit-row layout used by the RFCs.

    Every row is one 32-bit word; a field is a box as wide as its number of
    bits, labelled with its name and its value in this packet.

    Parameters
    ----------
    packet : scapy.packet.Packet
        A packet containing the layer; it is finalized first.
    layer : str, optional
        Class name of the layer to draw, e.g. ``"IP"``, ``"UDP"``, ``"RTP"``,
        by default ``"RTP"``.
    bit_width : int, optional
        Width of one bit in the drawing [px], by default 22.

    Returns
    -------
    panel.pane.Bokeh
        The header diagram.
    """
    fields = [f for f in packet_fields(packet) if f["layer"] == layer]
    if not fields:
        raise ValueError(f"the packet has no {layer} layer")
    start = fields[0]["offset"]
    total = sum(f["bits"] for f in fields)
    rows = (total + 31) // 32

    # Split fields that cross a 32-bit boundary into one box per row.
    boxes = []
    for f in fields:
        bit, remaining = f["offset"] - start, f["bits"]
        while remaining:
            row, col = divmod(bit, 32)
            width = min(remaining, 32 - col)
            boxes.append((f, row, col, width))
            bit += width
            remaining -= width

    color = LAYER_COLORS.get(layer, GREY)
    plot = new_plot(
        f"{layer} header, {total // 8} bytes",
        "Bit [–]",
        "Byte offset [B]",
        width=32 * bit_width + 110,
        height=60 * rows + 120,
        x_range=Range1d(0, 32),
        y_range=Range1d(rows, 0),
    )
    plot.grid.visible = False
    plot.xaxis.ticker = [i + 0.5 for i in range(32)]
    plot.xaxis.major_label_overrides = {i + 0.5: str(i) for i in range(32)}
    plot.xaxis.major_label_text_font_size = "10px"
    plot.yaxis.ticker = [r + 0.5 for r in range(rows)]
    plot.yaxis.major_label_overrides = {r + 0.5: str(4 * r) for r in range(rows)}

    source = ColumnDataSource(
        dict(
            left=[col for _, _, col, _ in boxes],
            right=[col + w for _, _, col, w in boxes],
            top=[row for _, row, _, _ in boxes],
            bottom=[row + 1 for _, row, _, _ in boxes],
            cx=[col + w / 2 for _, _, col, w in boxes],
            name_y=[row + 0.35 for _, row, _, _ in boxes],
            value_y=[row + 0.7 for _, row, _, _ in boxes],
            label=[
                SHORT_NAMES.get(f["name"], f["name"]) if w < 12 else f["name"]
                for f, _, _, w in boxes
            ],
            shown=[
                f["value"] if w >= 4 or len(f["value"]) <= 2 else "…"
                for f, _, _, w in boxes
            ],
            name=[f["name"] for f, _, _, _ in boxes],
            value=[f["value"] for f, _, _, _ in boxes],
            bits=[f["bits"] for f, _, _, _ in boxes],
            size=["10px" if w < 3 else "13px" for _, _, _, w in boxes],
        )
    )
    plot.quad(
        "left",
        "right",
        "top",
        "bottom",
        source=source,
        fill_color=color,
        line_color="#ffffff",
        line_width=3,
    )
    for y, text, style in (("name_y", "label", "bold"), ("value_y", "shown", "normal")):
        plot.text(
            "cx",
            y,
            text=text,
            source=source,
            text_align="center",
            text_baseline="middle",
            text_font=value(FONT),
            text_font_style=style,
            text_font_size="size",
            text_color=text_color_on(color),
        )
    plot.add_tools(
        HoverTool(
            tooltips=[("field", "@name"), ("value", "@value"), ("width", "@bits bit")]
        )
    )
    return pn.pane.Bokeh(plot)


# ---------------------------------------------------------------------------
# Packetization
# ---------------------------------------------------------------------------

HEADERS = (
    ("IPv4", 20, LAYER_COLORS["IP"]),
    ("UDP", 8, LAYER_COLORS["UDP"]),
    ("RTP", 12, LAYER_COLORS["RTP"]),
)


def overhead_chart(intervals_ms=(10, 20, 30, 40, 60), bits_per_sample: int = 8):
    """
    Compare header and payload sizes of G.711 packets for several intervals.

    The headers stay 40 B whatever the payload, so a short packetization
    interval spends a large share of the bit rate on headers.

    Parameters
    ----------
    intervals_ms : sequence of int, optional
        Packetization intervals [ms], by default 10, 20, 30, 40, and 60.
    bits_per_sample : int, optional
        Bits per sample of the codec, by default 8 (G.711).

    Returns
    -------
    panel.Row
        Stacked bars of bytes per packet, and a card with the bit rates.
    """
    factors = [f"{t} ms" for t in intervals_ms]
    payload = [SAMPLE_RATE * t / 1000 * bits_per_sample / 8 for t in intervals_ms]
    header = sum(size for _, size, _ in HEADERS)
    plot = new_plot(
        "Packet size by packetization interval",
        "Packetization interval [ms]",
        "Packet size [B]",
        x_range=FactorRange(*factors),
    )
    data = {"interval": factors, "payload": payload}
    for name, size, _ in HEADERS:
        data[name] = [size] * len(factors)
    stack = [name for name, _, _ in HEADERS] + ["payload"]
    plot.vbar_stack(
        stack,
        x="interval",
        width=0.6,
        source=ColumnDataSource(data),
        color=[c for _, _, c in HEADERS] + [LAYER_COLORS["Raw"]],
        line_color=None,
        legend_label=[f"{n} header" for n, _, _ in HEADERS] + ["G.711 payload"],
    )
    plot.y_range.start = 0
    plot.add_tools(
        HoverTool(tooltips=[("interval", "@interval"), ("payload", "@payload B")])
    )

    rows = []
    for t, p in zip(intervals_ms, payload):
        rate = (p + header) * 8 / (t / 1000)
        rows.append(
            (
                f"{t} ms",
                f"{rate / 1000:.1f} kbit/s &nbsp;({p / (p + header):.0%} payload)",
            )
        )
    info = card(
        "IP bit rate of one direction",
        rows,
        note=f"Packet = {header} B of IPv4, UDP, and RTP headers + payload. "
        "Rate = packet size × 8 / interval. Ethernet adds a further 38 B per "
        "frame on the wire.",
    )
    return pn.Row(legend_below(plot, columns=2), info, align="start")


def loudest_start(samples, block: int, count: int = 1) -> int:
    """
    Find the loudest stretch of a recording, aligned to packet boundaries.

    Parameters
    ----------
    samples : array_like of int16
        The recording [–].
    block : int
        Samples per packet, e.g. 160.
    count : int, optional
        Number of consecutive blocks in the stretch, by default 1.

    Returns
    -------
    int
        Index of the first sample of the `count` consecutive blocks with the
        highest energy; a multiple of `block`.
    """
    samples = np.asarray(samples)
    n = len(samples) // block
    if n <= count:
        return 0
    energy = (samples[: n * block].astype(float) ** 2).reshape(n, block).sum(axis=1)
    window = np.convolve(energy, np.ones(count), mode="valid")
    return int(np.argmax(window)) * block


def packetization_view(
    samples,
    packets: int = 6,
    first: int | None = None,
    samples_per_packet: int = 160,
):
    """
    Show how consecutive blocks of speech become consecutive RTP packets.

    The upper plot is the waveform with every block of `samples_per_packet`
    samples shaded and labelled with the sequence number and timestamp its
    packet carries; the lower strip shows the packets on the same time axis,
    drawn to scale in bytes.

    Parameters
    ----------
    samples : array_like of int16
        Speech sampled at 8 kHz [–].
    packets : int, optional
        Number of blocks shown, by default 6.
    first : int, optional
        Index of the first block shown. Left out, the loudest stretch of the
        recording is chosen, so that the blocks contain speech.
    samples_per_packet : int, optional
        Samples per packet, by default 160 (20 ms).

    Returns
    -------
    panel.Column
        The waveform above the packet strip.
    """
    samples = np.asarray(samples)
    if first is None:
        first = (
            loudest_start(samples, samples_per_packet, packets) // samples_per_packet
        )
    start = first * samples_per_packet
    stop = start + packets * samples_per_packet
    t_ms = np.arange(start, stop) / SAMPLE_RATE * 1000
    block_ms = samples_per_packet / SAMPLE_RATE * 1000
    x_range = Range1d(t_ms[0], t_ms[0] + packets * block_ms)

    wave = new_plot(
        "Speech cut into packets",
        "Time [ms]",
        "Amplitude [–]",
        width=800,
        height=320,
        x_range=x_range,
    )
    peak = max(1, int(np.abs(samples[start:stop]).max()))
    wave.y_range = Range1d(-1.35 * peak, 1.35 * peak)
    for k in range(packets):
        if k % 2 == 0:
            wave.add_layout(
                BoxAnnotation(
                    left=t_ms[0] + k * block_ms,
                    right=t_ms[0] + (k + 1) * block_ms,
                    fill_color=TINT,
                    fill_alpha=1,
                    level="underlay",  # behind the grid and the waveform
                )
            )
    wave.line(t_ms, samples[start:stop], line_width=2, line_alpha=0.8, color=colors[0])
    labels = ColumnDataSource(
        dict(
            x=[t_ms[0] + (k + 0.5) * block_ms for k in range(packets)],
            y=[1.18 * peak] * packets,
            text=[
                f"seq {first + k}  ·  ts {(first + k) * samples_per_packet}"
                for k in range(packets)
            ],
        )
    )
    wave.text(
        "x",
        "y",
        text="text",
        source=labels,
        text_align="center",
        text_baseline="middle",
        text_font=value(FONT),
        text_font_size="13px",
        text_color=TEXT_COLOR,
    )

    strip = new_plot(
        "",
        "Time [ms]",
        "",
        width=800,
        height=150,
        x_range=x_range,
        y_range=Range1d(0, 1),
    )
    strip.yaxis.visible = False
    strip.grid.visible = False
    payload = samples_per_packet  # G.711: one byte per sample
    total = payload + sum(size for _, size, _ in HEADERS)
    scale = 0.9 * block_ms / total  # [ms of axis per byte]
    # Every packet starts at the beginning of its block; the parts follow in
    # wire order, one renderer per part so that each gets a legend entry.
    left = t_ms[0] + (np.arange(packets) + 0.05) * block_ms
    for name, size, color in (*HEADERS, ("payload", payload, LAYER_COLORS["Raw"])):
        strip.quad(
            left=left,
            right=left + size * scale,
            bottom=0.25,
            top=0.75,
            fill_color=color,
            line_color="#ffffff",
            legend_label=f"{name}, {size} B",
        )
        left = left + size * scale
    return pn.Column(wave, legend_below(strip))


# ---------------------------------------------------------------------------
# Companding
# ---------------------------------------------------------------------------

# Test tone [Hz]; not a divisor of 8 kHz, so its samples hit every phase and
# the quantization error averages out (a 1 kHz tone repeats every 8 samples).
TONE = 1019


def _snr_db(x: np.ndarray, y: np.ndarray) -> float:
    """Signal-to-quantization-noise ratio of a decoded signal [dB]."""
    x = x.astype(float)
    noise = np.sum((x - y.astype(float)) ** 2)
    return float("inf") if noise == 0 else 10 * np.log10(np.sum(x**2) / noise)


def uniform_8bit(samples) -> np.ndarray:
    """
    Quantize 16-bit samples uniformly to 8 bits and back, for comparison.

    Parameters
    ----------
    samples : array_like of int
        Samples in the range −32768 to 32767 [–].

    Returns
    -------
    numpy.ndarray of int16
        The samples rounded to the middle of one of 256 equal steps.
    """
    x = np.asarray(samples, dtype=np.int32)
    return (((x >> 8) << 8) + 128).astype(np.int16)


def companding_view():
    """
    Draw the G.711 characteristics and their SNR over the input level.

    The left plot maps input amplitude to the 7-bit magnitude part of the
    code: steep (fine steps) for quiet signals, flat (coarse steps) for loud
    ones. The right plot shows the signal-to-quantization-noise ratio of a
    sine wave as its level falls: G.711 keeps it roughly constant over a wide
    range, while uniform 8-bit quantization loses 6 dB per halving of the
    amplitude.

    Returns
    -------
    panel.Row
        The characteristic and the SNR curves side by side.
    """
    x = np.arange(0, 32768, 16)
    curve = new_plot(
        "G.711 characteristic",
        "Input amplitude [–]",
        "Code magnitude [–]",
        width=480,
        height=400,
    )
    for name, label, color, dash in (
        ("alaw", "A-law", colors[0], "solid"),
        ("ulaw", "μ-law", colors[4], "dashed"),
    ):
        _, encode, _ = G711[name]
        code = encode(x).astype(int)
        # Undo the bit inversions to get the plain segment/step index 0–127.
        index = (code ^ 0xD5) & 0x7F if name == "alaw" else (~code) & 0x7F
        curve.line(
            x,
            index,
            line_width=3,
            line_alpha=0.6,
            color=color,
            line_dash=dash,
            legend_label=label,
        )
    curve.line(
        x,
        x // 256,
        line_width=2,
        color=GREY,
        line_dash="dashed",
        legend_label="uniform",
    )

    levels = np.arange(-60, 1, 2)  # [dBov]
    n = np.arange(SAMPLE_RATE)  # one second of a sine
    snr = new_plot(
        "Quantization SNR against level",
        "Sine level [dBov]",
        "SNR [dB]",
        width=480,
        height=400,
    )
    results = {"alaw": [], "ulaw": [], "uniform": []}
    for level in levels:
        sine = np.round(
            32767
            * 10 ** (level / 20)
            * np.sin(2 * np.pi * TONE / SAMPLE_RATE * n + 0.1)
        )
        sine = sine.astype(np.int16)
        for name in ("alaw", "ulaw"):
            _, encode, decode = G711[name]
            results[name].append(_snr_db(sine, decode(encode(sine))))
        results["uniform"].append(_snr_db(sine, uniform_8bit(sine)))
    snr.line(
        levels,
        results["alaw"],
        line_width=3,
        line_alpha=0.6,
        color=colors[0],
        legend_label="A-law",
    )
    snr.line(
        levels,
        results["ulaw"],
        line_width=3,
        line_alpha=0.6,
        color=colors[4],
        line_dash="dashed",
        legend_label="μ-law",
    )
    snr.line(
        levels,
        results["uniform"],
        line_width=2,
        color=GREY,
        line_dash="dashed",
        legend_label="uniform 8 bit",
    )
    return pn.Row(legend_below(curve), legend_below(snr))


def roundtrip_view(block, encoding: str = "alaw"):
    """
    Encode a block of speech with G.711, decode it, and show the error.

    Parameters
    ----------
    block : array_like of int16
        Samples of one packet, e.g. 160 samples [–].
    encoding : {"alaw", "ulaw"}, optional
        G.711 variant, by default A-law.

    Returns
    -------
    panel.Row
        Original and decoded samples with their difference, and a card with
        the sizes and the signal-to-quantization-noise ratio.
    """
    block = np.asarray(block, dtype=np.int16)
    _, encode, decode = G711[encoding]
    codes = encode(block)
    decoded = decode(codes)
    t_ms = np.arange(len(block)) / SAMPLE_RATE * 1000

    plot = new_plot("One block before and after G.711", "Time [ms]", "Amplitude [–]")
    plot.line(
        t_ms,
        block,
        line_width=3,
        line_alpha=0.6,
        color=colors[0],
        legend_label="original",
    )
    plot.scatter(t_ms, decoded, size=4, color=colors[4], legend_label="decoded")
    plot.vbar(
        x=t_ms,
        top=block.astype(int) - decoded,
        width=0.6 / SAMPLE_RATE * 1000,
        color=RED,
        alpha=0.7,
        legend_label="error",
    )
    plot.add_layout(Span(location=0, dimension="width", line_color=GREY, line_width=1))
    error = np.abs(block.astype(int) - decoded)
    info = card(
        f"G.711 {'A-law' if encoding == 'alaw' else 'μ-law'}",
        [
            ("Samples [–]", f"{len(block)}"),
            ("Linear PCM [B]", f"{block.nbytes}"),
            ("G.711 payload [B]", f"{codes.nbytes}"),
            ("SNR [dB]", f"{_snr_db(block, decoded):.1f}"),
            ("SNR of uniform 8 bit [dB]", f"{_snr_db(block, uniform_8bit(block)):.1f}"),
            (
                "Largest error [–]",
                f"{error.max()} at amplitude {abs(int(block[error.argmax()]))}",
            ),
            ("First code bytes", " ".join(f"{c:02x}" for c in codes[:6]) + " …"),
        ],
        note="The error grows with the amplitude: each segment's step is twice "
        "that of the segment below.",
    )
    return pn.Row(legend_below(plot), info, align="start")
