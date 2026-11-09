"""
Speech coding, RTP packetization, and objective quality scoring for Lab 03.

The G.711 functions convert between 16-bit linear PCM and the 8-bit A-law and
μ-law codes carried in RTP payload types 8 (PCMA) and 0 (PCMU). The reference
implementations of the RTP header and the packet stream are what the notebook
asks students to write themselves first. The Markov chain functions simulate
packet loss, independent or bursty as in the Gilbert–Elliott model of netem.
The scoring wrappers at the end call the external PESQ and ViSQOL executables.
"""

import re
import struct
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import scapy.all as sa
from scipy.io import wavfile
from scipy.signal import resample_poly

SAMPLE_RATE = 8000  # G.711 sampling frequency and RTP clock rate [Hz]

# ---------------------------------------------------------------------------
# G.711 companding (ITU-T G.711, segment-based approximation)
# ---------------------------------------------------------------------------
#
# Both laws split the magnitude axis into 8 segments (chords), each twice as
# wide as the one below it, and divide every segment into 16 equal steps. An
# 8-bit code word is then
#
#     bit 7     sign
#     bits 6–4  segment number, 0–7
#     bits 3–0  step within the segment (mantissa)
#
# so small amplitudes get fine steps and large amplitudes coarse ones: the
# quantization error grows with the signal and the signal-to-noise ratio stays
# roughly constant over a wide range of levels. A-law works on 13-bit
# magnitudes and inverts every other bit (XOR 0x55) to help line-clock
# recovery; μ-law works on 14-bit magnitudes with a bias of 33 that makes the
# segments start at a common origin, and inverts all bits.

# Upper end of each segment on the 13-bit (A-law) and 14-bit (μ-law) scale
ALAW_SEGMENT_END = np.array([0x1F, 0x3F, 0x7F, 0xFF, 0x1FF, 0x3FF, 0x7FF, 0xFFF])
ULAW_SEGMENT_END = np.array([0x3F, 0x7F, 0xFF, 0x1FF, 0x3FF, 0x7FF, 0xFFF, 0x1FFF])
ULAW_BIAS = 0x21  # 33 on the 14-bit scale, i.e. 0x84 = 132 on the 16-bit scale
ULAW_CLIP = 8159  # largest 14-bit magnitude μ-law represents


def linear_to_alaw(pcm_data) -> np.ndarray:
    """
    Encode 16-bit linear PCM samples as G.711 A-law code words.

    Parameters
    ----------
    pcm_data : array_like of int
        Samples in the range −32768 to 32767 [–].

    Returns
    -------
    numpy.ndarray of uint8
        One A-law byte per sample, as carried in an RTP PCMA payload.
    """
    pcm = np.asarray(pcm_data, dtype=np.int32) >> 3  # 13-bit resolution
    positive = pcm >= 0
    magnitude = np.where(positive, pcm, -pcm - 1)

    segment = np.searchsorted(ALAW_SEGMENT_END, magnitude)  # 0–7, or 8 if too loud
    # Segments 0 and 1 share the finest step (2 units); above that the step
    # doubles with each segment.
    shift = np.where(segment < 2, 1, segment)
    mantissa = (magnitude >> shift) & 0x0F
    code = np.where(segment >= 8, 0x7F, (np.minimum(segment, 7) << 4) | mantissa)

    # Sign bit 1 means positive in A-law; then every even bit is inverted.
    code = code ^ np.where(positive, 0xD5, 0x55)
    return code.astype(np.uint8)


def alaw_to_linear(codes) -> np.ndarray:
    """
    Decode G.711 A-law code words to 16-bit linear PCM.

    Each code is reconstructed at the middle of its quantization step.

    Parameters
    ----------
    codes : array_like of uint8
        A-law bytes, e.g. an RTP PCMA payload.

    Returns
    -------
    numpy.ndarray of int16
        Decoded samples [–].
    """
    code = np.asarray(codes, dtype=np.int32) ^ 0x55
    segment = (code & 0x70) >> 4
    magnitude = ((code & 0x0F) << 4) + 8  # middle of the step
    magnitude = np.where(
        segment > 0, (magnitude + 0x100) << np.maximum(segment - 1, 0), magnitude
    )
    return np.where(code & 0x80, magnitude, -magnitude).astype(np.int16)


def linear_to_ulaw(pcm_data) -> np.ndarray:
    """
    Encode 16-bit linear PCM samples as G.711 μ-law code words.

    Parameters
    ----------
    pcm_data : array_like of int
        Samples in the range −32768 to 32767 [–].

    Returns
    -------
    numpy.ndarray of uint8
        One μ-law byte per sample, as carried in an RTP PCMU payload.
    """
    pcm = np.asarray(pcm_data, dtype=np.int32) >> 2  # 14-bit resolution
    negative = pcm < 0
    magnitude = np.minimum(np.abs(pcm), ULAW_CLIP) + ULAW_BIAS

    segment = np.searchsorted(ULAW_SEGMENT_END, magnitude)
    mantissa = (magnitude >> (segment + 1)) & 0x0F
    code = np.where(segment >= 8, 0x7F, (np.minimum(segment, 7) << 4) | mantissa)

    # Sign bit 1 means positive in μ-law; then all bits are inverted.
    code = code ^ np.where(negative, 0x7F, 0xFF)
    return code.astype(np.uint8)


def ulaw_to_linear(codes) -> np.ndarray:
    """
    Decode G.711 μ-law code words to 16-bit linear PCM.

    Parameters
    ----------
    codes : array_like of uint8
        μ-law bytes, e.g. an RTP PCMU payload.

    Returns
    -------
    numpy.ndarray of int16
        Decoded samples [–].
    """
    code = ~np.asarray(codes, dtype=np.int32) & 0xFF
    segment = (code & 0x70) >> 4
    magnitude = (((code & 0x0F) << 3) + 0x84) << segment
    return np.where(code & 0x80, 0x84 - magnitude, magnitude - 0x84).astype(np.int16)


# Payload type, encoder, and decoder of each G.711 variant (RFC 3551, Table 4)
G711 = {
    "alaw": (8, linear_to_alaw, alaw_to_linear),
    "ulaw": (0, linear_to_ulaw, ulaw_to_linear),
}


# ---------------------------------------------------------------------------
# Reference implementations — students implement these first
# ---------------------------------------------------------------------------

RTP_VERSION = 2


def rtp_header(
    sequence: int, timestamp: int, ssrc: int, payload_type: int, marker: int = 0
) -> bytes:
    """
    Build the fixed 12-byte RTP header (RFC 3550, Section 5.1).

    The header has no padding, no extension, and no contributing sources, so
    the first byte is always ``0x80``::

         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |V=2|P|X|  CC   |M|     PT      |       sequence number         |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                           timestamp                           |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |           synchronization source (SSRC) identifier            |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

    Parameters
    ----------
    sequence : int
        Sequence number; taken modulo 2**16 [–].
    timestamp : int
        Sampling instant of the first sample in the payload, in units of the
        RTP clock (8 kHz for G.711); taken modulo 2**32 [–].
    ssrc : int
        Synchronization source identifier, a random 32-bit number [–].
    payload_type : int
        RTP payload type, 8 for PCMA and 0 for PCMU [–].
    marker : int, optional
        Marker bit, 1 on the first packet of a talkspurt, by default 0.

    Returns
    -------
    bytes
        The header in network byte order.
    """
    padding, extension, csrc_count = 0, 0, 0
    first = (RTP_VERSION << 6) | (padding << 5) | (extension << 4) | csrc_count
    second = (marker << 7) | payload_type
    # "!" = network (big-endian) byte order, B = 1 byte, H = 2 bytes, I = 4 bytes
    return struct.pack(
        "!BBHII", first, second, sequence % 2**16, timestamp % 2**32, ssrc
    )


def rtp_packets(
    samples,
    dst_ip: str,
    dst_port: int,
    src_port: int,
    encoding: str = "alaw",
    ssrc: int = 0x12345678,
    samples_per_packet: int = 160,
    first_sequence: int = 0,
    first_timestamp: int = 0,
) -> list:
    """
    Cut a PCM signal into blocks and wrap each one in IP, UDP, and RTP.

    Parameters
    ----------
    samples : array_like of int16
        Speech sampled at 8 kHz [–].
    dst_ip : str
        Destination IP address.
    dst_port, src_port : int
        UDP destination and source ports.
    encoding : {"alaw", "ulaw"}, optional
        G.711 variant, by default A-law (payload type 8).
    ssrc : int, optional
        Synchronization source identifier, by default 0x12345678. RFC 3550
        asks for a random value, e.g. ``int(rng.integers(2**32))``.
    samples_per_packet : int, optional
        Samples per packet, by default 160, i.e. 20 ms at 8 kHz.
    first_sequence, first_timestamp : int, optional
        Initial sequence number and timestamp, by default 0. RFC 3550 asks for
        random initial values, so that a stream cannot be predicted; zero makes
        the first packets easier to read.

    Returns
    -------
    list of scapy.packet.Packet
        One ``IP / UDP / RTP / Raw`` packet per block, ready for ``send``. The
        last block is padded with zeros to the full length.
    """
    payload_type, encoder, _ = G711[encoding]
    samples = np.asarray(samples, dtype=np.int16)
    packets = []
    for index, start in enumerate(range(0, len(samples), samples_per_packet)):
        block = samples[start : start + samples_per_packet]
        block = np.pad(block, (0, samples_per_packet - len(block)))
        rtp = sa.RTP(
            version=RTP_VERSION,
            marker=int(index == 0),  # the stream starts with a talkspurt
            payload_type=payload_type,
            sequence=(first_sequence + index) % 2**16,
            # The timestamp counts samples, not milliseconds.
            timestamp=(first_timestamp + index * samples_per_packet) % 2**32,
            sourcesync=ssrc,
        )
        packets.append(
            sa.IP(dst=dst_ip)
            / sa.UDP(sport=src_port, dport=dst_port)
            / rtp
            / sa.Raw(load=encoder(block).tobytes())
        )
    return packets


# ---------------------------------------------------------------------------
# Packet loss models: Markov chains
# ---------------------------------------------------------------------------
#
# A discrete-time Markov chain moves between a finite set of states once per
# step, here once per packet. The next state depends only on the current one.
# The chain is described by a state dictionary: for every state, the states
# it can move to and the probabilities of doing so, which sum to one,
#
#     {"good": (["good", "bad"], [1 - P, P]),
#      "bad":  (["good", "bad"], [R, 1 - R])}
#
# This is the Gilbert–Elliott model of bursty loss: a packet is lost with one
# probability in the good state and with another in the bad state. netem's
# `loss gemodel P R 1-h 1-k` is this chain, and `loss state p13 p31 p32 p23
# p14` is the four-state chain built by netem_state_dict().


class MarkovChain:
    """
    General discrete-time Markov chain over named states.

    `next_state` takes one random step; `run` takes many, one per packet, and
    `stationary_distribution` gives the long-run share of each state.

    Parameters
    ----------
    state_dict : dict
        For every state, a pair ``(next_states, probabilities)``: the states
        reachable in one step and the probability of moving to each [–]. The
        two-row arrays
        ``np.array([["1", "3"], [p11, p13]])``, are accepted as well.
    state : hashable
        Initial state. A state not in `state_dict` falls back to the first
        one, with a warning.
    rng : numpy.random.Generator, optional
        Random number generator, by default a new unseeded one.
    """

    def __init__(self, state_dict: dict, state, rng=None):
        self.state_dict = state_dict
        self.rng = rng if rng is not None else np.random.default_rng()
        # For each state, the next states and their cumulative probabilities:
        # a uniform random number u then selects the first state whose
        # cumulative probability exceeds u, i.e. state j with probability p_j.
        self._next = {}
        for name, (targets, probabilities) in state_dict.items():
            probabilities = np.asarray(probabilities, dtype=float)
            if np.any(probabilities < 0) or not np.isclose(probabilities.sum(), 1):
                raise ValueError(
                    f"probabilities out of state {name!r} must be non-negative "
                    f"and sum to 1, not {probabilities.sum()}"
                )
            missing = set(targets) - set(state_dict)
            if missing:
                raise ValueError(f"state {name!r} leads to unknown {missing}")
            cumulative = np.cumsum(probabilities)
            cumulative[-1] = 1.0  # guard against rounding just below 1
            # Plain Python values, also for the NumPy strings of a 2-row array
            targets = [t.item() if isinstance(t, np.generic) else t for t in targets]
            self._next[name] = (targets, cumulative)
        if state not in state_dict:
            print("Warning: the state is not in the state dictionary; using the first.")
            state = next(iter(state_dict))
        self.state = state

    def check_state(self, display: bool = True):
        """Return the current state, and print it unless `display` is False."""
        if display:
            print(f"Current state: {self.state}")
        return self.state

    def set_state(self, state) -> None:
        """Move the chain to `state` without a random step."""
        if state not in self.state_dict:
            raise ValueError(f"unknown state {state!r}")
        self.state = state

    def next_state(self):
        """Take one random step and return the new state."""
        targets, cumulative = self._next[self.state]
        u = self.rng.random()
        self.state = targets[int(np.searchsorted(cumulative, u, side="right"))]
        return self.state

    def run(self, steps: int) -> np.ndarray:
        """
        Take `steps` steps and return the state after each of them.

        Parameters
        ----------
        steps : int
            Number of steps, e.g. one per packet [–].

        Returns
        -------
        numpy.ndarray
            The states entered, in order; the initial state is not included.
        """
        return np.array([self.next_state() for _ in range(steps)])

    def transition_matrix(self) -> tuple[list, np.ndarray]:
        """
        The state dictionary as a transition matrix.

        Returns
        -------
        tuple
            ``(states, T)``: the states in the order of `state_dict`, and the
            matrix whose element ``T[i, j]`` is the probability of moving from
            ``states[i]`` to ``states[j]`` [–]. Every row sums to 1.
        """
        states = list(self.state_dict)
        index = {s: i for i, s in enumerate(states)}
        matrix = np.zeros((len(states), len(states)))
        for name, (targets, probabilities) in self.state_dict.items():
            for target, p in zip(targets, np.asarray(probabilities, dtype=float)):
                matrix[index[name], index[target]] += p
        return states, matrix

    def stationary_distribution(self) -> dict:
        """
        Long-run share of steps the chain spends in each state.

        The stationary distribution π solves π · T = π with the elements of π
        summing to 1. It is computed over the states reachable from the current
        one; the others, e.g. state 2 of the four-state model when p23 = p32 =
        0, are never visited and get 0. It is unique when every reachable
        state can also be reached from every other.

        Returns
        -------
        dict
            Probability of each state [–].

        Raises
        ------
        ValueError
            If the long-run behaviour depends on the random steps taken, i.e.
            the chain can end up in more than one closed group of states.
        """
        states, matrix = self.transition_matrix()
        # States reachable from the current one through non-zero transitions
        keep = {states.index(self.state)}
        frontier = list(keep)
        while frontier:
            for j in np.flatnonzero(matrix[frontier.pop()] > 0):
                if j not in keep:
                    keep.add(int(j))
                    frontier.append(int(j))
        keep = sorted(keep)
        sub = matrix[np.ix_(keep, keep)]
        n = len(keep)
        # (T^T − I) · π = 0 has a one-dimensional solution space when π is
        # unique; the extra row of ones fixes the scale (probabilities sum to 1).
        a = np.vstack([sub.T - np.eye(n), np.ones(n)])
        if np.linalg.matrix_rank(a[:-1]) < n - 1:
            raise ValueError("the stationary distribution is not unique")
        b = np.concatenate([np.zeros(n), [1.0]])
        pi = np.zeros(len(states))
        pi[keep] = np.linalg.lstsq(a, b, rcond=None)[0]
        return {name: float(x) for name, x in zip(states, pi)}


def gilbert_elliott_dict(p: float, r: float) -> dict:
    """
    State dictionary of the two-state Gilbert–Elliott chain.

    Parameters
    ----------
    p : float
        Probability of moving from the good to the bad state after a packet [–].
    r : float
        Probability of moving from the bad to the good state after a packet [–].

    Returns
    -------
    dict
        States ``"good"`` and ``"bad"``, for :class:`MarkovChain`.
    """
    return {
        "good": (["good", "bad"], [1 - p, p]),
        "bad": (["good", "bad"], [r, 1 - r]),
    }


def netem_state_dict(
    p13: float, p31: float, p32: float = 0.0, p23: float = 0.0, p14: float = 0.0
) -> dict:
    """
    State dictionary of netem's four-state loss model (`loss state`).

    The states are numbered as in netem: 1 packet received in a gap
    (a good period), 2 packet received within a burst, 3 packet lost within
    a burst, and 4 isolated loss within a gap. A packet is lost when the
    chain enters state 3 or 4. With only p13 and p31 non-zero, the model is
    the Gilbert–Elliott chain with P = p13 and R = p31.

    Parameters
    ----------
    p13 : float
        Gap to burst: probability that a burst of losses starts [–].
    p31 : float
        Burst to gap: probability that a burst ends [–].
    p32 : float, optional
        Lost to received within a burst [–], by default 0.
    p23 : float, optional
        Received to lost within a burst [–], by default 0.
    p14 : float, optional
        Probability of an isolated loss in a gap [–], by default 0.

    Returns
    -------
    dict
        States ``"1"`` to ``"4"``, for :class:`MarkovChain`.
    """
    return {
        "1": (["1", "3", "4"], [1 - p13 - p14, p13, p14]),
        "2": (["2", "3"], [1 - p23, p23]),
        "3": (["1", "2", "3"], [p31, p32, 1 - p31 - p32]),
        "4": (["1"], [1.0]),
    }


def gilbert_elliott(
    count: int,
    p: float,
    r: float,
    rng=None,
    loss_bad: float = 1.0,
    loss_good: float = 0.0,
) -> np.ndarray:
    """
    Draw a packet loss pattern from the Gilbert–Elliott model.

    The chain starts in the good state, as in netem, and takes one step per
    packet; ``gilbert_elliott(n, P, R)`` with P and R as fractions has the
    statistics of ``tc qdisc add dev DEVICE root netem loss gemodel P% R% 100% 0%``.
    Independent loss with probability q is the special case p = q, r = 1 − q:
    then the next state no longer depends on the current one.

    Parameters
    ----------
    count : int
        Number of packets [–].
    p : float
        Probability of moving from the good to the bad state after a packet [–].
    r : float
        Probability of moving from the bad to the good state after a packet [–].
    rng : numpy.random.Generator, optional
        Random number generator, by default a new unseeded one.
    loss_bad : float, optional
        Loss probability in the bad state, netem's 1 − h, by default 1 [–].
    loss_good : float, optional
        Loss probability in the good state, netem's 1 − k, by default 0 [–].

    Returns
    -------
    numpy.ndarray of bool
        True for every lost packet.
    """
    rng = rng if rng is not None else np.random.default_rng()
    states = MarkovChain(gilbert_elliott_dict(p, r), "good", rng).run(count)
    return rng.random(count) < np.where(states == "bad", loss_bad, loss_good)


def netem_state_loss(
    count: int,
    p13: float,
    p31: float,
    p32: float = 0.0,
    p23: float = 0.0,
    p14: float = 0.0,
    rng=None,
) -> np.ndarray:
    """
    Draw a packet loss pattern from netem's four-state model.

    Parameters
    ----------
    count : int
        Number of packets [–].
    p13, p31, p32, p23, p14 : float
        Transition probabilities, as for :func:`netem_state_dict` [–].
    rng : numpy.random.Generator, optional
        Random number generator, by default a new unseeded one.

    Returns
    -------
    numpy.ndarray of bool
        True for every lost packet, i.e. every step into state 3 or 4.
    """
    chain = MarkovChain(netem_state_dict(p13, p31, p32, p23, p14), "1", rng)
    return np.isin(chain.run(count), ["3", "4"])


def gilbert_elliott_params(loss: float, burst: float) -> tuple[float, float]:
    """
    Transition probabilities for a given mean loss and mean burst length.

    With all packets lost in the bad state and none in the good state, the
    bad state lasts 1/r packets on average, and the chain spends the share
    p / (p + r) of the packets in it.

    Parameters
    ----------
    loss : float
        Long-run loss fraction, 0 < loss < 1 [–].
    burst : float
        Mean length of a loss burst, at least 1 [packets].

    Returns
    -------
    tuple of float
        ``(p, r)``, the good-to-bad and bad-to-good probabilities [–]; multiply
        by 100 for netem's P and R in percent.
    """
    r = 1 / burst
    return r * loss / (1 - loss), r


def loss_bursts(lost) -> np.ndarray:
    """
    Lengths of the runs of consecutive lost packets.

    Parameters
    ----------
    lost : array_like of bool
        True for every lost packet, in sending order.

    Returns
    -------
    numpy.ndarray of int
        One length per burst, in order of occurrence [packets].
    """
    padded = np.concatenate([[0], np.asarray(lost, dtype=int), [0]])
    edges = np.diff(padded)  # +1 where a burst starts, −1 after it ends
    return np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)


# ---------------------------------------------------------------------------
# Objective speech quality: wrappers around the PESQ and ViSQOL binaries
# ---------------------------------------------------------------------------

# Default locations of the two command-line tools. Override them in the
# notebook or pass explicit paths to score_pair().
PESQ_BIN = Path.home() / "PESQ" / "PESQ"
VISQOL_BIN = Path.home() / "visqol" / "bazel-bin" / "visqol"

VISQOL_RATE = 16000  # sample rate expected by the ViSQOL speech model [Hz]


def resample_wav(src: Path, dst: Path, rate: int) -> Path:
    """
    Resample a mono 16-bit WAV file to a new sample rate.

    Parameters
    ----------
    src : Path
        Input WAV file (mono, int16).
    dst : Path
        Output WAV file; overwritten if it exists.
    rate : int
        Target sample rate [Hz].

    Returns
    -------
    Path
        The output path, for chaining.
    """
    fs, x = wavfile.read(src)
    if x.ndim > 1:
        x = x[:, 0]
    if fs != rate:
        g = np.gcd(fs, rate)
        x = resample_poly(x.astype(np.float64), rate // g, fs // g)
        x = np.clip(np.round(x), -32768, 32767).astype(np.int16)
    wavfile.write(dst, rate, x)
    return dst


def run_pesq(reference: Path, degraded: Path, pesq_bin: Path = PESQ_BIN) -> float:
    """
    Score a degraded file against its reference with the ITU-T P.862 binary.

    Parameters
    ----------
    reference : Path
        Clean reference WAV (8 kHz, mono, int16).
    degraded : Path
        Degraded WAV with the same format.
    pesq_bin : Path, optional
        Path to the compiled PESQ executable.

    Returns
    -------
    float
        MOS-LQO [-], or NaN if the binary is missing or produced no score.
    """
    if not Path(pesq_bin).is_file():
        return float("nan")
    fs, _ = wavfile.read(reference)
    out = subprocess.run(
        [str(pesq_bin), f"+{fs}", str(reference), str(degraded)],
        capture_output=True,
        text=True,
        cwd=tempfile.gettempdir(),  # PESQ writes _pesq_results.txt into cwd
    )
    # e.g. "P.862 Prediction (Raw MOS, MOS-LQO):  = 3.868   3.976"
    m = re.search(r"Prediction[^=]*=\s*([\d.]+)(?:\s+([\d.]+))?", out.stdout)
    if not m:
        return float("nan")
    return float(m.group(2) or m.group(1))


def run_visqol(reference: Path, degraded: Path, visqol_bin: Path = VISQOL_BIN) -> float:
    """
    Score a degraded file against its reference with ViSQOL in speech mode.

    Both files are resampled to 16 kHz in a temporary directory first.

    Parameters
    ----------
    reference : Path
        Clean reference WAV (mono, int16).
    degraded : Path
        Degraded WAV with the same format.
    visqol_bin : Path, optional
        Path to the ViSQOL executable built with Bazel.

    Returns
    -------
    float
        MOS-LQO [-], or NaN if the binary is missing or produced no score.
    """
    if not Path(visqol_bin).is_file():
        return float("nan")
    with tempfile.TemporaryDirectory() as tmp:
        ref16 = resample_wav(Path(reference), Path(tmp) / "ref16.wav", VISQOL_RATE)
        deg16 = resample_wav(Path(degraded), Path(tmp) / "deg16.wav", VISQOL_RATE)
        out = subprocess.run(
            [
                str(visqol_bin),
                "--reference_file",
                str(ref16),
                "--degraded_file",
                str(deg16),
                "--use_speech_mode",
                "--use_unscaled_speech_mos_mapping",
            ],
            capture_output=True,
            text=True,
            cwd=Path(visqol_bin).parents[
                1
            ],  # model files are resolved relative to the repo
        )
    m = re.search(r"MOS-LQO:\s*([\d.]+)", out.stdout)
    return float(m.group(1)) if m else float("nan")


def score_pair(
    reference: Path,
    degraded: Path,
    pesq_bin: Path = PESQ_BIN,
    visqol_bin: Path = VISQOL_BIN,
) -> dict[str, float]:
    """
    Compute the objective quality scores of one degraded recording.

    Parameters
    ----------
    reference : Path
        Clean reference WAV (8 kHz, mono, int16).
    degraded : Path
        Degraded WAV with the same format.
    pesq_bin, visqol_bin : Path, optional
        Locations of the PESQ and ViSQOL executables.

    Returns
    -------
    dict[str, float]
        ``{"pesq": MOS-LQO, "visqol": MOS-LQO}``; a missing tool yields NaN.
    """
    reference, degraded = Path(reference), Path(degraded)
    return {
        "pesq": run_pesq(reference, degraded, pesq_bin),
        "visqol": run_visqol(reference, degraded, visqol_bin),
    }
