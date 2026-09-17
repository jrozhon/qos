from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar, Protocol, Self

import numpy as np
from bokeh.models import (
    ColumnDataSource,
    CustomJSTickFormatter,
    Div,
    Range1d,
    Select,
    Slider,
    Span,
)
from bokeh.plotting import figure
from scipy.signal import butter, lfilter

from lib.params import colors

FONT = "Carlito, Calibri, Liberation Sans, DejaVu Sans, Arial, sans-serif"
TEXT_COLOR = "#292929"
GRID_COLOR = "#e5e5e5"
GREY = "#818386"
RED = "#E4002B"
TOOLS = "crosshair,pan,reset,save,wheel_zoom"


# Reference implementations — students implement these first
def calc_channel_capacity(S: float, N: float, B: float) -> float:
    """
    Calculate the Shannon–Hartley channel capacity.

    Parameters
    ----------
    S : float
        Signal power. [W]
    N : float
        Noise power. [W]
    B : float
        Channel bandwidth. [Hz]

    Returns
    -------
    float
        Channel capacity. [bit/s]
    """
    C = B * np.log2(1 + S / N)
    return C


def calc_signal_power(signal: np.ndarray) -> float:
    """
    Calculate the mean power of a sampled signal.

    Parameters
    ----------
    signal : np.ndarray
        Discrete amplitudes of the signal. [V]

    Returns
    -------
    float
        Mean power, i.e. the mean of the squared samples. [W]
    """
    return np.square(signal).mean()


# Helpers shared by the dashboards
def si_format(value: float, unit: str, digits: int = 3) -> str:
    """
    Format a value with an SI prefix (k, M, G).

    Parameters
    ----------
    value : float
        Quantity to format.
    unit : str
        Unit symbol appended after the prefix, e.g. ``"bit/s"``.
    digits : int, optional
        Significant digits, by default 3.

    Returns
    -------
    str
        Formatted string such as ``"32.9 kbit/s"``.
    """
    if not np.isfinite(value):
        return f"{value} {unit}"
    for prefix, scale in (("G", 1e9), ("M", 1e6), ("k", 1e3)):
        if abs(value) >= scale:
            return f"{value / scale:.{digits}g} {prefix}{unit}"
    return f"{value:.{digits}g} {unit}"


def card_html(title: str, rows: list[tuple[str, str]], note: str = "") -> str:
    """
    Build the HTML of a result card in the course style (STYLE.md §5.3).

    Parameters
    ----------
    title : str
        Card heading.
    rows : list[tuple[str, str]]
        ``(label, value)`` pairs rendered as a two-column table.
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
        f"<p style='margin:8px 0 0;font-size:13px;color:{GREY}'>{note}</p>"
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
    if plot.legend:
        plot.legend.label_text_font = FONT
        plot.legend.label_text_color = TEXT_COLOR
        plot.legend.border_line_color = None
        plot.legend.background_fill_alpha = 0.6
    return plot


# Protocol for the Signal class
class Signal(Protocol):
    x: np.ndarray
    y: np.ndarray
    linked_signal: Signal | None
    source: ColumnDataSource

    def generate(self, f: Callable, **kwargs) -> np.ndarray: ...

    def update(self, attrname, old, new) -> None: ...

    def _add_callbacks(self) -> None: ...

    def add_plot(
        self,
        x: np.ndarray,
        x_axis_label: str,
        y: np.ndarray,
        y_axis_label: str,
        title: str,
        source: ColumnDataSource,
        color: str = colors[0],
        y_range: tuple[float, float] = (-12, 12),
    ) -> figure:
        plot = figure(
            height=400,
            width=600,
            title=title,
            x_axis_label=x_axis_label,
            y_axis_label=y_axis_label,
            tools=TOOLS,
            x_range=[min(x), max(x)],
            y_range=list(y_range),
        )
        plot.line("x", "y", source=source, line_width=3, line_alpha=0.6, color=color)
        return style_plot(plot)

    def __add__(self, other: Self) -> Signal:
        assert (self.x == other.x).all()
        y = self.y + other.y
        combined_signal = CombinedSignal(y=y, x=self.x)
        self.linked_signal = combined_signal
        other.linked_signal = combined_signal
        return combined_signal


class CombinedSignal(Signal):
    """
    Sum of two linked signals; it is updated by them and has no sliders.
    """

    def __init__(self, y, x):
        self.y = y
        self.x = x
        self.linked_signal = None
        self.source = ColumnDataSource(data=dict(x=self.x, y=self.y))
        self.plot = self.add_plot(
            self.x,
            "Time [s]",
            self.y,
            "Amplitude [V]",
            "Signal with noise",
            self.source,
            color=colors[5],
        )

    def generate(self, f: Callable, **kwargs): ...

    def update(self, attrname, old, new): ...

    def _add_callbacks(self): ...


class HarmSignal(Signal):
    """
    Class representing a harmonic signal.

    Attributes
    ----------
    MAX_AMPLITUDE : float
        Maximum amplitude of the signal. [V]
    AMPLITUDE_STEP : float
        Step size for changing the amplitude. [V]
    MAX_FREQ : float
        Maximum frequency of the signal. [Hz]
    FREQ_STEP : float
        Step size for changing the frequency. [Hz]
    MAX_BAND : float
        Maximum channel bandwidth offered by the slider. [Hz]
    """

    MAX_AMPLITUDE = 8
    AMPLITUDE_STEP = 0.5
    MAX_FREQ = 5
    FREQ_STEP = 0.1
    MAX_BAND = 100

    def __init__(
        self,
        amplitude: float = 1,
        freq: float = 1,
        phase: float = 0,
        band: float = 10,
        f: Callable = np.sin,
        no_samples: int = 1000,
        max_range: float = 2 * np.pi,
        title: str = "Harmonic signal",
        x_axis_label: str = "Time [s]",
        y_axis_label: str = "Amplitude [V]",
    ):
        """
        Initialize a harmonic signal.

        Parameters
        ----------
        amplitude : float, optional
            Amplitude of the signal [V], by default 1.
        freq : float, optional
            Frequency of the signal [Hz], by default 1.
        phase : float, optional
            Phase of the signal [rad], by default 0.
        band : float, optional
            Initial channel bandwidth of the *Bandwidth* slider [Hz], by
            default 10. It is only the factor B of the capacity formula; the
            tone itself is not filtered.
        f : Callable, optional
            Function to generate the signal, by default np.sin.
        no_samples : int, optional
            Number of samples in the signal, by default 1000.
        max_range : float, optional
            Duration of the time axis [s], by default 2π.
        title : str, optional
            Title of the plot, by default "Harmonic signal".
        x_axis_label : str, optional
            Label for the x-axis, by default "Time [s]".
        y_axis_label : str, optional
            Label for the y-axis, by default "Amplitude [V]".
        """
        self.x = np.linspace(0, max_range, no_samples)
        self.y = self.generate(f, amplitude, freq, phase)
        self.f = f
        self.linked_signal = None

        self.source = ColumnDataSource(data=dict(x=self.x, y=self.y))
        self.amplitude = Slider(
            title="Amplitude [V]",
            value=amplitude,
            start=0.0,
            end=self.MAX_AMPLITUDE,
            step=self.AMPLITUDE_STEP,
        )
        self.freq = Slider(
            title="Frequency [Hz]",
            value=freq,
            start=0,
            end=self.MAX_FREQ,
            step=self.FREQ_STEP,
        )
        self.phase = Slider(
            title="Phase [rad]", value=phase, start=0.0, end=2 * np.pi, step=0.1
        )
        self.band = Slider(
            title="Channel bandwidth B [Hz]",
            value=band,
            start=1,
            end=self.MAX_BAND,
            step=1,
        )

        self._add_callbacks()
        self.plot = self.add_plot(
            self.x, x_axis_label, self.y, y_axis_label, title, source=self.source
        )

    def _add_callbacks(self) -> None:
        """
        Add callbacks to the sliders.
        """
        for w in [self.amplitude, self.freq, self.phase]:
            w.on_change("value", self.update)

    def generate(
        self,
        f: Callable[[np.ndarray], np.ndarray],
        amplitude: float,
        freq: float,
        phase: float,
    ) -> np.ndarray:
        """
        Generate the harmonic signal.

        Parameters
        ----------
        f : Callable[[np.ndarray], np.ndarray]
            Function to generate the signal.
        amplitude : float
            Amplitude of the signal. [V]
        freq : float
            Frequency of the signal. [Hz]
        phase : float
            Phase of the signal. [rad]

        Returns
        -------
        np.ndarray
            Generated signal.
        """
        return amplitude * f(2 * np.pi * freq * self.x + phase)

    def update(self, attrname, old, new) -> None:
        """
        Update the signal based on the current slider values.

        Parameters
        ----------
        attrname : str
            Name of the attribute that changed.
        old : Any
            Old value of the attribute.
        new : Any
            New value of the attribute.
        """
        # Get the current slider values
        a = self.amplitude.value
        w = self.phase.value
        k = self.freq.value

        # Generate the new curve
        y = self.generate(self.f, a, k, w)

        self.source.data = dict(x=self.x, y=y)

        if self.linked_signal:
            self.linked_signal.y -= self.y
            self.linked_signal.y += y
            self.linked_signal.source.data = dict(x=self.x, y=self.linked_signal.y)

        self.y = y


class NoiseSignal(Signal):
    """
    Class representing Gaussian white noise.

    Attributes
    ----------
    MAX_SIGMA : float
        Maximum standard deviation offered by the slider. [V]
    SIGMA_STEP : float
        Step size for changing the standard deviation. [V]
    """

    MAX_SIGMA = 1
    SIGMA_STEP = 0.1

    def __init__(
        self,
        sigma: float = 0.1,
        f: Callable = np.random.default_rng().normal,
        no_samples: int = 1000,
        max_range: float = 2 * np.pi,
        title: str = "Noise signal",
        x_axis_label: str = "Time [s]",
        y_axis_label: str = "Amplitude [V]",
    ):
        """
        Initialize a noise signal.

        Parameters
        ----------
        sigma : float, optional
            Standard deviation of the noise [V], by default 0.1. The noise
            power equals σ².
        f : Callable, optional
            Generator called as ``f(mean, sigma, size)``, by default
            ``np.random.default_rng().normal``.
        no_samples : int, optional
            Number of samples in the signal, by default 1000.
        max_range : float, optional
            Duration of the time axis [s], by default 2π.
        title : str, optional
            Title of the plot, by default "Noise signal".
        x_axis_label : str, optional
            Label for the x-axis, by default "Time [s]".
        y_axis_label : str, optional
            Label for the y-axis, by default "Amplitude [V]".
        """
        self.x = np.linspace(0, max_range, no_samples)
        self.y = self.generate(f, sigma=sigma)
        self.f = f
        self.linked_signal = None

        self.source = ColumnDataSource(data=dict(x=self.x, y=self.y))
        self.sigma = Slider(
            title="Standard deviation σ [V]",
            value=sigma,
            start=0.0,
            end=self.MAX_SIGMA,
            step=self.SIGMA_STEP,
        )

        self._add_callbacks()
        self.plot = self.add_plot(
            self.x,
            x_axis_label,
            self.y,
            y_axis_label,
            title,
            source=self.source,
            color=colors[4],
            y_range=(-4, 4),
        )

    def _add_callbacks(self) -> None:
        """
        Add callbacks to the sliders.
        """
        for w in [self.sigma]:
            w.on_change("value", self.update)

    def generate(self, f: Callable, sigma: float) -> np.ndarray:
        """
        Generate the noise signal.

        Parameters
        ----------
        f : Callable
            Generator called as ``f(mean, sigma, size)``.
        sigma : float
            Standard deviation of the noise. [V]

        Returns
        -------
        np.ndarray
            Generated signal.
        """
        return f(0, sigma, len(self.x))

    def update(self, attrname, old, new) -> None:
        """
        Update the signal based on the current slider values.

        Parameters
        ----------
        attrname : str
            Name of the attribute that changed.
        old : Any
            Old value of the attribute.
        new : Any
            New value of the attribute.
        """
        y = self.generate(self.f, self.sigma.value)
        self.source.data = dict(x=self.x, y=y)
        if self.linked_signal:
            self.linked_signal.y -= self.y
            self.linked_signal.y += y
            self.linked_signal.source.data = dict(x=self.x, y=self.linked_signal.y)

        self.y = y


class CapacityExplorer:
    """
    Interactive Shannon–Hartley explorer.

    Two plots share one operating point set by the *Bandwidth* and *SNR*
    sliders or by a technology preset: the capacity as a function of
    bandwidth at the chosen SNR, and the spectral efficiency C/B as a
    function of SNR, which does not depend on the bandwidth at all.

    Attributes
    ----------
    PRESETS : dict[str, tuple[float, float] | None]
        Name → (bandwidth [Hz], linear SNR [–]) from the README table.
    LOG_B_RANGE : tuple[float, float]
        Range of log10(B) covered by the bandwidth slider.
    """

    PRESETS: ClassVar[dict[str, tuple[float, float] | None]] = {
        "Custom": None,
        "Telephone channel": (3.1e3, 1585),
        "ADSL, one channel": (4.3125e3, 1000),
        "VDSL, 30 MHz profile": (30e6, 1000),
        "Wi-Fi 802.11n, 20 MHz": (20e6, 316),
        "Wi-Fi 802.11n, 40 MHz": (40e6, 631),
        "5G, 100 MHz": (100e6, 100),
        "5G mmWave, 1 GHz": (1e9, 6.3),
    }
    LOG_B_RANGE = (3.0, 9.3)
    SNR_DB_RANGE = (-10.0, 40.0)

    def __init__(self, band: float = 3.1e3, snr_db: float = 32.0):
        """
        Build the widgets and plots.

        Parameters
        ----------
        band : float, optional
            Initial bandwidth [Hz], by default 3.1 kHz.
        snr_db : float, optional
            Initial signal-to-noise ratio [dB], by default 32 dB.
        """
        self._syncing = False

        # Widgets. The bandwidth slider works in log10(B) and displays B.
        self.preset = Select(
            title="Technology preset", value="Custom", options=list(self.PRESETS)
        )
        self.log_band = Slider(
            title="Bandwidth B",
            value=np.log10(band),
            start=self.LOG_B_RANGE[0],
            end=self.LOG_B_RANGE[1],
            step=0.05,
            format=CustomJSTickFormatter(
                code="""
                const b = Math.pow(10, tick);
                if (b >= 1e9) return (b / 1e9).toPrecision(3) + " GHz";
                if (b >= 1e6) return (b / 1e6).toPrecision(3) + " MHz";
                return (b / 1e3).toPrecision(3) + " kHz";
                """
            ),
        )
        self.snr_db = Slider(
            title="Signal-to-noise ratio [dB]",
            value=snr_db,
            start=self.SNR_DB_RANGE[0],
            end=self.SNR_DB_RANGE[1],
            step=0.5,
        )

        # Plot 1: capacity versus bandwidth at the chosen SNR.
        self.b_axis = np.logspace(*self.LOG_B_RANGE, 200)
        self.cap_source = ColumnDataSource(data=dict(x=self.b_axis, y=self.b_axis))
        self.point_source = ColumnDataSource(data=dict(x=[band], y=[0.0]))
        self.plot_band = figure(
            height=400,
            width=600,
            title="Capacity versus bandwidth at the chosen SNR",
            x_axis_label="Bandwidth B [Hz]",
            y_axis_label="Capacity C [bit/s]",
            x_axis_type="log",
            y_axis_type="log",
            tools=TOOLS,
            x_range=[10 ** self.LOG_B_RANGE[0], 10 ** self.LOG_B_RANGE[1]],
            y_range=[1e2, 1e11],
        )
        for ref_db, dash in ((0, "dashed"), (30, "dotted")):
            self.plot_band.line(
                self.b_axis,
                calc_channel_capacity(10 ** (ref_db / 10), 1.0, self.b_axis),
                line_color=GREY,
                line_dash=dash,
                line_width=2,
                legend_label=f"SNR = {ref_db} dB",
            )
        self.plot_band.line(
            "x",
            "y",
            source=self.cap_source,
            line_width=3,
            line_alpha=0.6,
            color=colors[0],
            legend_label="chosen SNR",
        )
        self.plot_band.scatter(
            "x", "y", source=self.point_source, size=12, color=colors[4]
        )
        self.plot_band.legend.location = "top_left"
        style_plot(self.plot_band)

        # Plot 2: spectral efficiency versus SNR; the curve is fixed.
        snr_axis = np.linspace(*self.SNR_DB_RANGE, 200)
        eff = np.log2(1 + 10 ** (snr_axis / 10))
        self.eff_point_source = ColumnDataSource(data=dict(x=[snr_db], y=[0.0]))
        self.plot_snr = figure(
            height=400,
            width=600,
            title="Spectral efficiency versus SNR",
            x_axis_label="Signal-to-noise ratio [dB]",
            y_axis_label="Spectral efficiency C/B [bit/s/Hz]",
            tools=TOOLS,
            x_range=list(self.SNR_DB_RANGE),
            y_range=[0, 14],
        )
        self.plot_snr.line(
            snr_axis,
            snr_axis * np.log2(10) / 10,
            line_color=GREY,
            line_dash="dashed",
            line_width=2,
            legend_label="log₂(S/N), high-SNR approximation",
        )
        self.plot_snr.line(
            snr_axis,
            eff,
            line_width=3,
            line_alpha=0.6,
            color=colors[0],
            legend_label="log₂(1 + S/N)",
        )
        self.plot_snr.scatter(
            "x", "y", source=self.eff_point_source, size=12, color=colors[4]
        )
        self.plot_snr.legend.location = "top_left"
        style_plot(self.plot_snr)

        self.card = Div(text="", width=600)

        self.preset.on_change("value", self._on_preset)
        self.log_band.on_change("value", self._on_slider)
        self.snr_db.on_change("value", self._on_slider)
        self.update()

    @property
    def band(self) -> float:
        """Current bandwidth [Hz]."""
        return 10**self.log_band.value

    @property
    def snr(self) -> float:
        """Current linear signal-to-noise ratio [–]."""
        return 10 ** (self.snr_db.value / 10)

    def _on_preset(self, attrname, old, new) -> None:
        values = self.PRESETS[new]
        if values is None:
            return
        band, snr = values
        self._syncing = True
        self.log_band.value = float(np.log10(band))
        self.snr_db.value = float(10 * np.log10(snr))
        self._syncing = False
        self.update()

    def _on_slider(self, attrname, old, new) -> None:
        if self._syncing:
            return
        self.preset.value = "Custom"
        self.update()

    def update(self) -> None:
        """
        Recompute the curves, the operating point, and the result card.
        """
        B, snr = self.band, self.snr
        C = calc_channel_capacity(snr, 1.0, B)
        self.cap_source.data = dict(
            x=self.b_axis, y=calc_channel_capacity(snr, 1.0, self.b_axis)
        )
        self.point_source.data = dict(x=[B], y=[C])
        self.eff_point_source.data = dict(x=[self.snr_db.value], y=[np.log2(1 + snr)])
        self.card.text = card_html(
            "Operating point",
            [
                ("Bandwidth B", si_format(B, "Hz")),
                ("SNR", f"{self.snr_db.value:.1f} dB = {snr:.4g} [–]"),
                ("Capacity C", si_format(C, "bit/s")),
                ("Spectral efficiency C/B", f"{np.log2(1 + snr):.2f} bit/s/Hz"),
            ],
            note="The SNR is assumed fixed while B changes; with thermal noise "
            "N = kTB and constant signal power it would fall.",
        )


class Telegraph:
    """
    Interactive simulation of a binary telegraph link.

    A bit sequence — seeded random, alternating, or isolated ones — is sent
    as rectangular on–off pulses (non-return-to-zero, 0 → 0 V, 1 → 1 V) at a
    symbol rate R_s. The channel
    limits the bandwidth to B with either an ideal (brick-wall) low-pass
    filter or a first-order RC low-pass, then adds Gaussian noise. The
    receiver samples the middle of every symbol interval and compares the
    sample with a 0.5 V threshold.

    Attributes
    ----------
    FS : float
        Simulation sampling frequency. [Hz]
    N_BITS : int
        Number of transmitted bits.
    GUARD : int
        Silent symbol intervals added before and after the message.
    """

    FS = 2000.0
    N_BITS = 32
    GUARD = 1
    FILTERS = ("Ideal low-pass", "RC line")
    PATTERNS = ("Random", "Alternating 0101…", "Isolated ones 0001…")

    def __init__(
        self,
        symbol_rate: float = 20.0,
        band: float = 20.0,
        sigma: float = 0.0,
        seed: int = 1,
    ):
        """
        Build the widgets and plots.

        Parameters
        ----------
        symbol_rate : float, optional
            Initial symbol rate [Bd], by default 20 Bd.
        band : float, optional
            Initial channel bandwidth [Hz], by default 20 Hz.
        sigma : float, optional
            Initial noise standard deviation [V], by default 0.
        seed : int, optional
            Seed of the bit and noise generator, by default 1. The same
            slider settings therefore always give the same picture.
        """
        self.seed = seed
        self.pattern = Select(
            title="Bit pattern", value=self.PATTERNS[0], options=list(self.PATTERNS)
        )

        self.symbol_rate = Slider(
            title="Symbol rate R_s [Bd]", value=symbol_rate, start=5, end=100, step=1
        )
        self.band = Slider(
            title="Channel bandwidth B [Hz]", value=band, start=1, end=100, step=1
        )
        self.sigma = Slider(
            title="Noise standard deviation σ [V]",
            value=sigma,
            start=0.0,
            end=0.5,
            step=0.02,
        )
        self.filter = Select(
            title="Channel model", value=self.FILTERS[0], options=list(self.FILTERS)
        )

        self.tx_source = ColumnDataSource(data=dict(x=[], y=[]))
        self.rx_source = ColumnDataSource(data=dict(x=[], y=[]))
        self.ok_source = ColumnDataSource(data=dict(x=[], y=[]))
        self.err_source = ColumnDataSource(data=dict(x=[], y=[]))

        # Both plots share one explicit time range that update() rescales, so
        # the waveform always fills the plot and only the tick labels change.
        self.time_range = Range1d(0, 1)
        self.plot_tx = figure(
            height=400,
            width=600,
            title="Transmitted signal",
            x_axis_label="Time [s]",
            y_axis_label="Amplitude [V]",
            tools=TOOLS,
            x_range=self.time_range,
            y_range=[-1, 2],
        )
        self.plot_tx.line(
            "x",
            "y",
            source=self.tx_source,
            line_width=3,
            line_alpha=0.6,
            color=colors[0],
        )
        style_plot(self.plot_tx)

        self.plot_rx = figure(
            height=400,
            width=600,
            title="Received signal and decisions",
            x_axis_label="Time [s]",
            y_axis_label="Amplitude [V]",
            tools=TOOLS,
            x_range=self.time_range,
            y_range=[-1, 2],
        )
        self.plot_rx.line(
            "x",
            "y",
            source=self.rx_source,
            line_width=3,
            line_alpha=0.6,
            color=colors[4],
        )
        self.plot_rx.add_layout(
            Span(
                location=0.5,
                dimension="width",
                line_color=GREY,
                line_dash="dashed",
                line_width=2,
            )
        )
        self.plot_rx.scatter(
            "x",
            "y",
            source=self.ok_source,
            size=9,
            color=colors[0],
            legend_label="correct",
        )
        self.plot_rx.scatter(
            "x",
            "y",
            source=self.err_source,
            size=12,
            marker="x",
            line_width=3,
            color=RED,
            legend_label="error",
        )
        self.plot_rx.legend.location = "top_left"
        style_plot(self.plot_rx)

        self.card = Div(text="", width=600)

        for w in (self.symbol_rate, self.band, self.sigma, self.filter, self.pattern):
            w.on_change("value", self._on_change)
        self.update()

    def _on_change(self, attrname, old, new) -> None:
        self.update()

    @property
    def bits(self) -> np.ndarray:
        """Transmitted bit sequence according to the *Bit pattern* selector."""
        if self.pattern.value == "Alternating 0101…":
            return np.arange(self.N_BITS) % 2
        if self.pattern.value == "Isolated ones 0001…":
            return (np.arange(self.N_BITS) % 4 == 3).astype(int)
        return np.random.default_rng(self.seed).integers(0, 2, self.N_BITS)

    def transmit(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Generate the NRZ waveform of the bit sequence with guard intervals.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            Time axis [s] and transmitted amplitude [V].
        """
        sps = round(self.FS / self.symbol_rate.value)  # samples per symbol
        guard = np.zeros(self.GUARD * sps)
        tx = np.concatenate([guard, np.repeat(self.bits, sps), guard])
        t = np.arange(len(tx)) / self.FS
        return t, tx

    def channel(self, tx: np.ndarray) -> np.ndarray:
        """
        Apply the band limitation and the noise to the transmitted waveform.

        Parameters
        ----------
        tx : np.ndarray
            Transmitted amplitude. [V]

        Returns
        -------
        np.ndarray
            Received amplitude. [V]
        """
        B = self.band.value
        if self.filter.value == "Ideal low-pass":
            spectrum = np.fft.rfft(tx)
            freqs = np.fft.rfftfreq(len(tx), 1 / self.FS)
            spectrum[freqs > B] = 0
            rx = np.fft.irfft(spectrum, n=len(tx))
        else:
            b, a = butter(1, B, fs=self.FS)
            rx = lfilter(b, a, tx)
        noise = np.random.default_rng(self.seed).normal(0, self.sigma.value, len(tx))
        return rx + noise

    def receive(self, rx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Sample the received waveform in the middle of each symbol and decide.

        Parameters
        ----------
        rx : np.ndarray
            Received amplitude. [V]

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            Indices of the decision samples and the decoded bits.
        """
        sps = round(self.FS / self.symbol_rate.value)
        idx = self.GUARD * sps + np.arange(self.N_BITS) * sps + sps // 2
        decoded = (rx[idx] > 0.5).astype(int)
        return idx, decoded

    def update(self) -> None:
        """
        Run the simulation and refresh the plots and the result card.
        """
        t, tx = self.transmit()
        rx = self.channel(tx)
        idx, decoded = self.receive(rx)
        errors = decoded != self.bits

        self.tx_source.data = dict(x=t, y=tx)
        self.rx_source.data = dict(x=t, y=rx)
        self.ok_source.data = dict(x=t[idx][~errors], y=rx[idx][~errors])
        self.err_source.data = dict(x=t[idx][errors], y=rx[idx][errors])
        self.time_range.end = float(t[-1])

        rs, B = self.symbol_rate.value, self.band.value
        n_err = int(errors.sum())
        mono = "font-family:DejaVu Sans Mono,monospace"
        tx_bits = f"<span style='{mono}'>{''.join(map(str, self.bits))}</span>"
        rx_bits = (
            f"<span style='{mono}'>"
            + "".join(
                f"<span style='color:{RED}'>{b}</span>" if e else str(b)
                for b, e in zip(decoded, errors)
            )
            + "</span>"
        )
        verdict = (
            "R_s ≤ 2B: the alternating pattern still passes"
            if rs <= 2 * B
            else "R_s > 2B: the alternating pattern is filtered out"
        )
        self.card.text = card_html(
            "Link report",
            [
                ("Symbol rate R_s", f"{rs:g} Bd"),
                ("Nyquist rate 2B", f"{2 * B:g} Bd — {verdict}"),
                ("Sent", tx_bits),
                ("Received", rx_bits),
                (
                    "Bit errors",
                    f"{n_err} of {self.N_BITS} (BER = {n_err / self.N_BITS:.3f})",
                ),
            ],
            note="Decisions are taken in the middle of each symbol interval against "
            "a 0.5 V threshold (dashed line).",
        )
