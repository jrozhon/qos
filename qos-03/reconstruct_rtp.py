"""Reconstruct one short G.711 RTP stream using a clean capture's timeline.

Inputs are headerless TSV files containing rtp.seq, rtp.timestamp, and
rtp.payload, exported for one SSRC and direction. Missing packets become
16-bit PCM silence. This offline model does not emulate a jitter buffer.
"""

import argparse
import csv
import subprocess
import wave
from pathlib import Path


def read_packets(path: Path) -> dict[tuple[int, int], bytes]:
    """Read packet payloads indexed by sequence number and timestamp.

    Parameters
    ----------
    path : Path
        Headerless TSV file for one G.711 stream; timestamps use an 8 kHz clock.

    Returns
    -------
    dict
        Packet keys and payload bytes; identical duplicates are ignored.
    """
    packets = {}
    with path.open(newline="") as stream:
        for line, row in enumerate(csv.reader(stream, delimiter="\t"), 1):
            if not row:
                continue
            try:
                seq, timestamp, payload = row
                key = (int(seq), int(timestamp))
                data = bytes.fromhex(payload.replace(":", ""))
                if not (0 <= key[0] < 2**16 and 0 <= key[1] < 2**32 and data):
                    raise ValueError("invalid sequence, timestamp, or payload")
                if key in packets and packets[key] != data:
                    raise ValueError("conflicting duplicate packet")
                packets[key] = data
            except ValueError as error:
                raise ValueError(f"{path}:{line}: {error}") from error
    return packets


def reconstruct(reference: Path, received: Path, output: Path, codec: str) -> None:
    """Write a WAV file with the clean stream's duration and packet positions.

    Parameters
    ----------
    reference, received : Path
        TSV exports of the clean source stream and its replayed reception.
        Reference packets must start with the earliest packet and be complete.
    output : Path
        Destination WAV file (8 kHz, mono, signed 16-bit PCM).
    codec : str
        FFmpeg G.711 format: ``alaw`` or ``mulaw``.
    """
    clean = read_packets(reference)
    packets = read_packets(received)
    if not clean:
        raise ValueError("the clean reference contains no packets")
    if codec not in {"alaw", "mulaw"}:
        raise ValueError("codec must be alaw or mulaw")
    origin = next(iter(clean))[1]
    offsets = {key: (key[1] - origin) % 2**32 for key in clean}
    ordered = sorted(clean, key=offsets.get)
    end = 0
    previous = None
    for key in ordered:
        if offsets[key] != end:
            raise ValueError("reference must have contiguous, nonoverlapping audio")
        if previous is not None and key[0] != (previous + 1) % 2**16:
            raise ValueError("reference has a sequence gap or multiple streams")
        end += len(clean[key])  # G.711 encodes one sample per byte.
        previous = key[0]
    if end > 8000 * 3600:
        raise ValueError("use a reference shorter than one hour")
    for key, payload in packets.items():
        if key not in clean or len(payload) != len(clean[key]):
            raise ValueError("received packet does not match the reference timeline")

    pcm = bytearray(2 * end)  # Missing samples remain digital silence.
    present = [key for key in ordered if key in packets]
    if present:
        decoded = subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-f",
                codec,
                "-ar",
                "8000",
                "-ac",
                "1",
                "-i",
                "pipe:0",
                "-f",
                "s16le",
                "-acodec",
                "pcm_s16le",
                "pipe:1",
            ],
            input=b"".join(packets[key] for key in present),
            capture_output=True,
            check=True,
        ).stdout
        expected = 2 * sum(len(packets[key]) for key in present)
        if len(decoded) != expected:
            raise ValueError("decoded audio length does not match G.711 payloads")
        cursor = 0
        for key in present:
            size = 2 * len(packets[key])
            offset = 2 * offsets[key]
            pcm[offset : offset + size] = decoded[cursor : cursor + size]
            cursor += size
    with wave.open(str(output), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8000)
        stream.writeframes(pcm)
    print(
        f"Saved {end / 8000:.3f} s; missing {len(clean) - len(packets)} / {len(clean)} packets"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("received", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--codec", choices=("alaw", "mulaw"), required=True)
    args = parser.parse_args()
    try:
        reconstruct(args.reference, args.received, args.output, args.codec)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Reconstruction failed: {error}\n")
