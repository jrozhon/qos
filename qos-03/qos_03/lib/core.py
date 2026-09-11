import numpy as np


def linear_to_ulaw(pcm_data):
  """
  Vectorized conversion of 16-bit linear PCM to μ-law
  """
  pcm_data = np.asarray(pcm_data)
  pcm_data = np.clip(pcm_data, -32768, 32767)
  
  # Get sign and magnitude
  sign = (pcm_data < 0).astype(np.uint8)
  abs_pcm = np.abs(pcm_data)
  
  # Add bias
  abs_pcm += 0x84
  
  # Find segment using log2
  seg = np.maximum(0, np.minimum(7, (np.log2(abs_pcm) - 6).astype(int)))
  
  # Calculate mantissa based on segment
  mantissa = (abs_pcm >> (seg + 3)) & 0x0F
  
  # Combine fields
  ulaw = ~((sign << 7) | (seg << 4) | mantissa) & 0xFF
  
  return ulaw.astype(np.uint8)

def linear_to_alaw(pcm_data):
  """
  Vectorized conversion of 16-bit linear PCM to A-law
  """
  pcm_data = np.asarray(pcm_data)
  pcm_data = np.clip(pcm_data, -32768, 32767)
  
  # Get sign and magnitude
  sign = (pcm_data < 0).astype(np.uint8)
  abs_pcm = np.abs(pcm_data)
  
  # Find segment using log2
  seg = np.maximum(0, np.minimum(7, (np.log2(abs_pcm) - 6).astype(int)))
  
  # Calculate mantissa based on segment
  mantissa = (abs_pcm >> (seg + 3)) & 0x0F
  
  # Combine fields and XOR with 0x55
  alaw = ((sign << 7) | (seg << 4) | mantissa) ^ 0x55
  
  return alaw.astype(np.uint8)

# ---------------------------------------------------------------------------
# Objective speech quality: wrappers around the PESQ and ViSQOL binaries
# ---------------------------------------------------------------------------

import re
import subprocess
import tempfile
from pathlib import Path

from scipy.io import wavfile
from scipy.signal import resample_poly

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
                "--reference_file", str(ref16),
                "--degraded_file", str(deg16),
                "--use_speech_mode",
                "--use_unscaled_speech_mos_mapping",
            ],
            capture_output=True,
            text=True,
            cwd=Path(visqol_bin).parents[1],  # model files are resolved relative to the repo
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
