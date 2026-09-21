"""
Presentation helpers for the Exercise 02 notebook.

The point of this module is the pairing between a theoretical quantity and the
measurement that should confirm it. :data:`MM1_QUANTITIES` states that pairing
once — symbol, formula, and the simulation output the number comes from — and
:func:`mm1_report` renders it as one row per symbol, so a student filling in a
formula can see which measurement it is supposed to reproduce.
"""

from typing import NamedTuple, Optional

import numpy as np
from IPython.display import HTML, display

from lib.core import BYTES_TO_BITS

CARD_STYLE = """
<style>
  .dashboard { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin: 16px 0; }
  .card { background: #F2F3F3; border-left: 4px solid #00A499; border-radius: 4px; padding: 12px 16px; }
  .card h3 { margin: 0 0 6px; font: bold 15px Carlito, Calibri, sans-serif; color: #292929; }
  .card p { margin: 0; color: #292929; font: bold 20px Carlito, Calibri, sans-serif;
            font-variant-numeric: tabular-nums; }
  .card small { display: block; margin: 8px 0 0; color: #292929; line-height: 1.4;
                font: 13.5px Carlito, Calibri, sans-serif; }
</style>
"""

TABLE_STYLE = """
<style>
  table.qos { border-collapse: collapse; margin: 16px 0; color: #292929;
              font-family: Carlito, Calibri, sans-serif; font-size: 15px; }
  table.qos th { background: #CCEDEB; border-bottom: 3px solid #00A499;
                 text-align: left; padding: 8px 16px; font-weight: bold; }
  table.qos td { padding: 8px 16px; border-bottom: 1px solid #E5E5E5; }
  table.qos tbody tr:nth-child(even) { background: #F2F3F3; }
  table.qos .num { text-align: right; font-variant-numeric: tabular-nums; }
  table.qos .src { color: #818386; }
  table.qos .off { color: #E4002B; }
</style>
"""

#: One entry per M/M/1 quantity: key, symbol, quantity with unit, formula, and
#: the simulation output whose value it should match. The key is what a student
#: writes in the ``theory`` dictionary, and what :func:`mm1_measurements`
#: returns, so theory and measurement are matched by name and never by the
#: order of the rows.
MM1_QUANTITIES = [
    (
        "lambda",
        "<em>λ</em>",
        "Arrival rate [1/s]",
        "1 / mean inter-arrival time",
        "packets delivered after warm-up / observed time",
    ),
    (
        "mu",
        "<em>μ</em>",
        "Service rate [1/s]",
        "<em>R</em> / (8 · mean packet size)",
        "1 / mean transmission time of the delivered packets",
    ),
    (
        "rho",
        "<em>ρ</em>",
        "Utilization [–]",
        "<em>λ</em> / <em>μ</em>",
        "tap: share of samples with a packet in service",
    ),
    (
        "L",
        "<em>L</em>",
        "Packets in system [–]",
        "<em>ρ</em> / (1 − <em>ρ</em>)",
        "tap.system_packets, mean after warm-up",
    ),
    (
        "L_q",
        "<em>L</em><sub>q</sub>",
        "Packets waiting [–]",
        "<em>ρ</em>² / (1 − <em>ρ</em>)",
        "tap.queue_packets, mean after warm-up",
    ),
    (
        "W",
        "<em>W</em>",
        "Time in system [s]",
        "1 / (<em>μ</em> − <em>λ</em>)",
        "sink.delays, mean after warm-up",
    ),
    (
        "W_q",
        "<em>W</em><sub>q</sub>",
        "Waiting time [s]",
        "<em>ρ</em> / (<em>μ</em> − <em>λ</em>)",
        "sink.delays mean − mean transmission time",
    ),
]

#: Labels for every key a measurement mapping can carry, including the two that
#: have no theoretical counterpart in the ideal infinite-buffer model.
QUANTITY_LABELS = {key: (symbol, name) for key, symbol, name, _, _ in MM1_QUANTITIES}
QUANTITY_LABELS["drops"] = ("–", "Packets dropped [–]")
QUANTITY_LABELS["loss"] = ("–", "Loss fraction [–]")


class MM1Samples(NamedTuple):
    """
    The arrays behind the measured M/M/1 quantities, kept for plotting.

    Attributes
    ----------
    times : numpy.ndarray
        Time of every tap sample, the warm-up included [s].
    system : numpy.ndarray
        Packets in the system at every sample, the warm-up included [–]. The
        whole run is kept so that the transient can be plotted; the averages in
        the values mapping are taken after the warm-up only.
    queue : numpy.ndarray
        Packets waiting at every sample, the warm-up included [–].
    delays : numpy.ndarray
        Time in system of each packet created after the warm-up [s].
    service : numpy.ndarray
        Transmission time of those same packets [s].
    """

    times: np.ndarray
    system: np.ndarray
    queue: np.ndarray
    delays: np.ndarray
    service: np.ndarray


def dashboard(cards: dict) -> None:
    """
    Render a mapping of titles to values as a grid of cards.

    A card states three things: what the quantity is, its value, and what the
    number actually counts. The third is the one a reader cannot reconstruct
    from the notebook, so a card should normally carry it.

    Parameters
    ----------
    cards : dict
        Card title, including the unit in square brackets, mapped either to the
        value alone or to a ``(value, explanation)`` pair. The explanation says
        what the number counts and which attribute it was read from, and is
        printed under the value in smaller type.
    """
    blocks = []
    for title, entry in cards.items():
        value, explanation = entry if isinstance(entry, tuple) else (entry, None)
        note = f"<small>{explanation}</small>" if explanation else ""
        blocks.append(f'<div class="card"><h3>{title}</h3><p>{value}</p>{note}</div>')
    display(HTML(f'{CARD_STYLE}<div class="dashboard">{"".join(blocks)}</div>'))


def table(headers: list, rows: list) -> None:
    """
    Render a table in the course style.

    Parameters
    ----------
    headers : list[str]
        Column headings. A heading may contain HTML markup.
    rows : list[list]
        Cell contents, one list per row. A cell may contain HTML markup.
    """
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows
    )
    display(
        HTML(
            f"{TABLE_STYLE}<table class='qos'><thead><tr>{head}</tr></thead>"
            f"<tbody>{body}</tbody></table>"
        )
    )


def sample_summary(x: np.ndarray, mean: float, std: float) -> None:
    """
    Compare the moments of a sample with their theoretical values.

    Parameters
    ----------
    x : numpy.ndarray
        The sample.
    mean : float
        Theoretical mean of the distribution.
    std : float
        Theoretical standard deviation of the distribution.
    """
    table(
        ["Quantity", "Sample", "Theory"],
        [
            ["Count", f"{x.size}", "–"],
            ["Minimum", f"{x.min():.3f}", "–"],
            ["Mean", f"{x.mean():.3f}", f"{mean:.3f}"],
            ["Standard deviation", f"{x.std():.3f}", f"{std:.3f}"],
            ["Maximum", f"{x.max():.3f}", "–"],
        ],
    )


def last(values, n: int = 10, fmt: str = "{:.3f}") -> str:
    """
    Format the last n values of a sequence for a dashboard card.

    Parameters
    ----------
    values : Sequence
        The values to format.
    n : int, optional
        How many trailing values to show, by default 10.
    fmt : str, optional
        Format string applied to each value, by default "{:.3f}".

    Returns
    -------
    str
        The formatted values, separated by commas.
    """
    return ", ".join(fmt.format(v) for v in values[-n:])


def mm1_measurements(sink, tap, port, warmup: float, duration: float, rate: float):
    """
    Extract the seven M/M/1 quantities from one completed simulation.

    Only packets created after the warm-up and tap samples taken after it enter
    the averages, so the transient of an initially empty system is excluded.

    Parameters
    ----------
    sink : PacketSink
        Sink that received the packets.
    tap : NetworkTap
        Tap attached to the port.
    port : SwitchPort
        The port being measured.
    warmup : float
        Initial time excluded from the measurement [s].
    duration : float
        Total simulated time [s].
    rate : float
        Transmission rate of the port [bit/s].

    Returns
    -------
    tuple[dict, MM1Samples]
        The measured values, keyed exactly like the theory dictionary, and the
        arrays they were computed from.
    """
    delays = np.asarray(sink.delays)
    arrivals = np.asarray(sink.arrivals)
    sizes = np.asarray([p.size for p in sink.logged_packets], dtype=float)

    created_after_warmup = (arrivals - delays) >= warmup
    delays = delays[created_after_warmup]
    service = BYTES_TO_BITS * sizes[created_after_warmup] / rate

    times = np.asarray(tap.times, dtype=float)
    system = np.asarray(tap.system_packets)
    queue = np.asarray(tap.queue_packets)
    # The full series is returned for plotting; only samples taken after the
    # warm-up enter the averages below.
    steady = times > warmup

    observed = duration - warmup
    values = {
        "lambda": delays.size / observed,
        "mu": 1.0 / service.mean(),
        "rho": float(np.mean(system[steady] >= 1)),
        "L": float(system[steady].mean()),
        "L_q": float(queue[steady].mean()),
        "W": float(delays.mean()),
        "W_q": float(delays.mean() - service.mean()),
        "drops": port.cum_drop_count,
        "loss": port.cum_drop_count / port.cum_packet_count,
    }
    return values, MM1Samples(times, system, queue, delays, service)


def _agreement(theory: Optional[float], measured: float, tolerance: float) -> tuple:
    """
    Describe how close a measurement is to its theoretical value.

    Parameters
    ----------
    theory : Optional[float]
        Theoretical value, or None or NaN when it has not been filled in yet.
    measured : float
        Measured value.
    tolerance : float
        Relative difference still counted as agreement [–].

    Returns
    -------
    tuple[str, str]
        The formatted theoretical value and the verdict, both as HTML.
    """
    if theory is None or not np.isfinite(theory) or theory == 0:
        return "–", '<span class="src">not filled in</span>'
    difference = (measured - theory) / abs(theory)
    verdict = f"{difference:+.1%}"
    if abs(difference) > tolerance:
        return (
            f"{theory:.4f}",
            f'<span class="off">{verdict}, outside {tolerance:.0%}</span>',
        )
    return f"{theory:.4f}", f"{verdict}, within {tolerance:.0%}"


def mm1_report(theory: dict, measured: dict, tolerance: float = 0.10) -> None:
    """
    Show each M/M/1 symbol beside the measurement that should confirm it.

    Each row carries the formula the theoretical value comes from and the
    simulation output the measured value comes from, so the correspondence is
    visible without tracing variable names through the notebook. A theoretical
    value left as NaN is reported as not filled in rather than compared.

    Parameters
    ----------
    theory : dict
        Theoretical values, keyed as in :data:`MM1_QUANTITIES`.
    measured : dict
        Measured values from :func:`mm1_measurements`.
    tolerance : float, optional
        Relative difference still counted as agreement, by default 0.10. The
        default is loose on purpose: over a run of a few thousand seconds the
        run-to-run spread of the second-order quantities is itself several per
        cent, as :func:`seed_table` shows, so a tighter bound would flag a
        correct answer.
    """
    rows = []
    for key, symbol, name, formula, source in MM1_QUANTITIES:
        theory_text, verdict = _agreement(theory.get(key), measured[key], tolerance)
        rows.append(
            [
                symbol,
                name,
                formula,
                f'<span class="num">{theory_text}</span>',
                f'<span class="num">{measured[key]:.4f}</span>',
                verdict,
                f'<span class="src">{source}</span>',
            ]
        )
    table(
        [
            "Symbol",
            "Quantity",
            "Formula",
            "Theory",
            "Measured",
            "Agreement",
            "Measured from",
        ],
        rows,
    )


def seed_table(
    results: dict, theory: dict, keys=("rho", "L", "W", "W_q", "drops")
) -> None:
    """
    Summarize repeated runs of the same system under different seeds.

    Parameters
    ----------
    results : dict
        Seed to the measured values of that run.
    theory : dict
        Theoretical values, shown once because they do not depend on the seed.
    keys : Sequence[str], optional
        Which quantities to tabulate.
    """
    seeds = sorted(results)
    headers = (
        ["Symbol", "Quantity", "Theory"]
        + [f"Seed {seed}" for seed in seeds]
        + ["Mean", "Spread"]
    )
    rows = []
    for key in keys:
        symbol, name = QUANTITY_LABELS[key]
        values = np.array([float(results[seed][key]) for seed in seeds])
        number = "{:.0f}" if np.all(values == np.round(values)) else "{:.4f}"
        candidate = theory.get(key)
        theory_text = (
            f"{candidate:.4f}"
            if candidate is not None and np.isfinite(candidate)
            else "–"
        )
        rows.append(
            [symbol, name, f'<span class="num">{theory_text}</span>']
            + [f'<span class="num">{number.format(v)}</span>' for v in values]
            + [
                f'<span class="num">{values.mean():.4f}</span>',
                f'<span class="num">{values.max() - values.min():.4f}</span>',
            ]
        )
    table(headers, rows)


def port_measurements(ports, taps, duration: float, mean_size: float) -> dict:
    """
    Measure the arrival rate and offered traffic of each port.

    Parameters
    ----------
    ports : Sequence[SwitchPort]
        The ports to measure.
    taps : Sequence[NetworkTap]
        A tap attached to each of those ports, in the same order.
    duration : float
        Total simulated time [s].
    mean_size : float
        Mean packet size used by the sources [B], needed to turn an arrival
        rate into offered traffic.

    Returns
    -------
    dict
        Port number to its measured arrival rate, offered traffic, and the
        share of time it was busy.
    """
    measured = {}
    for port, tap in zip(ports, taps):
        service_time = BYTES_TO_BITS * mean_size / port.transmission_rate
        arrival_rate = port.cum_packet_count / duration
        system = np.asarray(tap.system_packets)
        measured[port.port_no] = {
            "lambda": arrival_rate,
            "A": arrival_rate * service_time,
            "rho": float(np.mean(system >= 1)),
        }
    return measured


def port_report(theory: dict, measured: dict, tolerance: float = 0.10) -> None:
    """
    Compare the traffic computed for each port with the simulated traffic.

    Parameters
    ----------
    theory : dict
        Port number to a mapping with the keys "lambda" and "A".
    measured : dict
        Port number to the mapping returned by :func:`port_measurements`.
    tolerance : float, optional
        Relative difference still counted as agreement, by default 0.10.
    """
    spec = [
        ("lambda", "<em>λ</em>", "Arrival rate [1/s]", "sum of the feeding rates"),
        ("A", "<em>A</em>", "Offered traffic [erl]", "<em>λ</em> · <em>S</em>"),
    ]
    rows = []
    for port_no in sorted(measured):
        for key, symbol, name, formula in spec:
            expected = theory.get(port_no, {}).get(key)
            theory_text, verdict = _agreement(
                expected, measured[port_no][key], tolerance
            )
            rows.append(
                [
                    f"Port {port_no}",
                    symbol,
                    name,
                    formula,
                    f'<span class="num">{theory_text}</span>',
                    f'<span class="num">{measured[port_no][key]:.4f}</span>',
                    verdict,
                ]
            )
        rows.append(
            [
                f"Port {port_no}",
                "<em>ρ</em>",
                "Busy share of time [–]",
                '<span class="src">no formula, measured only</span>',
                "–",
                f'<span class="num">{measured[port_no]["rho"]:.4f}</span>',
                '<span class="src">tap: share of samples with a packet in service</span>',
            ]
        )
    table(
        ["Port", "Symbol", "Quantity", "Formula", "Theory", "Measured", "Agreement"],
        rows,
    )
