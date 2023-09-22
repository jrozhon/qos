from __future__ import annotations

from typing import Callable, Protocol, Self

import numpy as np
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure


# These are meant for the teacher to use in the lecture
def calc_channel_capacity(S: float, N: float, B: float) -> float:
    """
    Calculate the channel capacity.

    Parameters
    ----------
    S : float
        Signal power. [W]
    N : float
        Noise power. [W]
    B : float
        Bandwidth. [Hz]

    Returns
    -------
    float
        Channel capacity. [Bits/s]
    """
    C = B * np.log2(1 + S / N)
    return C


def calc_signal_power(signal: np.ndarray) -> float:
    """
    Calculate the power of a signal.

    Parameters
    ----------
    signal : np.ndarray
        Input signal. Discrete amplitudes of a signal.

    Returns
    -------
    float
        Signal power. [W]
    """
    return np.square(signal).mean()


# Protocol for the Signal class
class Signal(Protocol):
    x: np.ndarray
    y: np.ndarray
    linked_signal: Signal | None
    source: ColumnDataSource

    def generate(self, f: Callable, **kwargs) -> np.ndarray:
        ...

    def update(self, attrname, old, new) -> None:
        ...

    def _add_callbacks(self) -> None:
        ...

    def add_plot(
        self,
        x: np.ndarray,
        x_axis_label: str,
        y: np.ndarray,
        y_axis_label: str,
        title: str,
        source: ColumnDataSource,
    ) -> figure:
        plot = figure(
            height=400,
            width=600,
            title=title,
            x_axis_label=x_axis_label,
            y_axis_label=y_axis_label,
            tools="crosshair,pan,reset,save,wheel_zoom",
            x_range=[min(x), max(x)],
            y_range=[-12, 12],
        )

        plot.line("x", "y", source=source, line_width=3, line_alpha=0.6)
        return plot

    def __add__(self, other: Self) -> Signal:
        assert (self.x == other.x).all()
        y = self.y + other.y
        combined_signal = CombinedSignal(y=y, x=self.x)
        self.linked_signal = combined_signal
        other.linked_signal = combined_signal
        return combined_signal


class CombinedSignal(Signal):
    def __init__(self, y, x):
        self.y = y
        self.x = x
        self.linked_signal = None
        self.source = ColumnDataSource(data=dict(x=self.x, y=self.y))
        self.plot = self.add_plot(
            self.x, "time [s]", self.y, "amplitude [V]", "Combined signal", self.source
        )

    def generate(self, f: Callable, **kwargs):
        ...

    def update(self, attrname, old, new):
        ...

    def _add_callbacks(self):
        ...

class HarmSignal(Signal):
    """
    Class representing a harmonic signal.

    Attributes
    ----------
    MAX_AMPLITUDE : float
        Maximum amplitude of the signal.
    AMPLITUDE_STEP : float
        Step size for changing the amplitude.
    MAX_FREQ : float
        Maximum frequency of the signal.
    FREQ_STEP : float
        Step size for changing the frequency.
    """
    MAX_AMPLITUDE = 8
    AMPLITUDE_STEP = 0.5
    MAX_FREQ = 5
    FREQ_STEP = 0.1

    def __init__(
        self,
        amplitude: float = 1,
        freq: float = 1,
        phase: float = 0,
        f: Callable = np.sin,
        no_samples: int = 1000,
        max_range: float = 2 * np.pi,
        title: str = "Input signal",
        x_axis_label: str = "time [s]",
        y_axis_label: str = "amplitude [V]",
    ):
        """
        Initialize a harmonic signal.

        Parameters
        ----------
        amplitude : float, optional
            Amplitude of the signal, by default 1.
        freq : float, optional
            Frequency of the signal, by default 1.
        phase : float, optional
            Phase of the signal, by default 0.
        f : Callable, optional
            Function to generate the signal, by default np.sin.
        no_samples : int, optional
            Number of samples in the signal, by default 1000.
        max_range : float, optional
            Maximum range of the signal, by default 2 * np.pi.
        title : str, optional
            Title of the signal, by default "Input signal".
        x_axis_label : str, optional
            Label for the x-axis, by default "time [s]".
        y_axis_label : str, optional
            Label for the y-axis, by default "amplitude [V]".
        """
        self.x = np.linspace(0, max_range, no_samples)
        self.y = self.generate(f, amplitude, freq, phase)
        self.f = f
        self.linked_signal = None

        self.source = ColumnDataSource(data=dict(x=self.x, y=self.y))
        self.amplitude = Slider(
            title="amplitude [V]",
            value=amplitude,
            start=0.0,
            end=self.MAX_AMPLITUDE,
            step=self.AMPLITUDE_STEP,
        )
        self.freq = Slider(
            title="frequency [Hz]",
            value=freq,
            start=0,
            end=self.MAX_FREQ,
            step=self.FREQ_STEP,
        )
        self.phase = Slider(title="phase [rad]", value=phase, start=0.0, end=2 * np.pi)

        self.band = Slider(
            title="bandwidth [Hz]",
            value=0.1 * self.freq.value,
            start=0.1 * self.freq.value,
            end=1 * self.freq.value,
            step=0.1 * self.freq.value,
        )

        self._add_callbacks()
        self.plot = self.add_plot(
            self.x, x_axis_label, self.y, y_axis_label, title, source=self.source
        )

    def _add_callbacks(self) -> None:
        """
        Add callbacks to the sliders.
        """
        for w in [self.amplitude, self.freq, self.phase, self.band]:
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
            Amplitude of the signal.
        freq : float
            Frequency of the signal.
        phase : float
            Phase of the signal.

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
    Class representing a noise signal.

    Attributes
    ----------
    MAX_AMPLITUDE : float
        Maximum amplitude of the signal.
    AMPLITUDE_STEP : float
        Step size for changing the amplitude.
    """
    MAX_AMPLITUDE = 1
    AMPLITUDE_STEP = 0.1

    def __init__(
        self,
        amplitude: float = 0.1,
        f: Callable = np.random.default_rng().normal,
        no_samples: int = 1000,
        max_range: float = 2 * np.pi,
        title: str = "Noise signal",
        x_axis_label: str = "time [s]",
        y_axis_label: str = "amplitude [V]",
    ):
        """
        Initialize a noise signal.

        Parameters
        ----------
        amplitude : float, optional
            Amplitude of the signal, by default 0.1.
        f : Callable, optional
            Function to generate the signal, by default np.random.default_rng().normal.
        no_samples : int, optional
            Number of samples in the signal, by default 1000.
        max_range : float, optional
            Maximum range of the signal, by default 2 * np.pi.
        title : str, optional
            Title of the signal, by default "Noise signal".
        x_axis_label : str, optional
            Label for the x-axis, by default "time [s]".
        y_axis_label : str, optional
            Label for the y-axis, by default "amplitude [V]".
        """
        self.x = np.linspace(0, max_range, no_samples)
        self.y = self.generate(f, amplitude=amplitude)
        self.f = f
        self.linked_signal = None

        self.source = ColumnDataSource(data=dict(x=self.x, y=self.y))
        self.amplitude = Slider(
            title="amplitude [V]",
            value=amplitude,
            start=0.0,
            end=self.MAX_AMPLITUDE,
            step=self.AMPLITUDE_STEP,
        )

        self._add_callbacks()
        self.plot = self.add_plot(
            self.x, x_axis_label, self.y, y_axis_label, title, source=self.source
        )

    def _add_callbacks(self) -> None:
        """
        Add callbacks to the sliders.
        """
        for w in [self.amplitude]:
            w.on_change("value", self.update)

    def generate(self, f: Callable, amplitude: float) -> np.ndarray:
        """
        Generate the noise signal.

        Parameters
        ----------
        f : Callable
            Function to generate the signal.
        amplitude : float
            Amplitude of the signal.

        Returns
        -------
        np.ndarray
            Generated signal.
        """
        # Callable has no attributes here, as they are not defined in the
        # protocol and differ from harm signal
        return f(0, amplitude, len(self.x))

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
        y = self.generate(self.f, a)
        self.source.data = dict(x=self.x, y=y)
        if self.linked_signal:
            self.linked_signal.y -= self.y
            self.linked_signal.y += y
            self.linked_signal.source.data = dict(x=self.x, y=self.linked_signal.y)

        self.y = y

