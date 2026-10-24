"""
Speech coding, RTP packetization, and objective quality scoring for Lab 03.

The G.711 functions convert between 16-bit linear PCM and the 8-bit A-law and
μ-law codes carried in RTP payload types 8 (PCMA) and 0 (PCMU). The reference
implementations of the RTP header and the packet stream are what the notebook
asks students to write themselves first. The scoring wrappers at the end call
the external PESQ and ViSQOL executables.
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
