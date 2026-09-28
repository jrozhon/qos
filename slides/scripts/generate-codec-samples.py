#!/usr/bin/env python3
"""Generate the codec listening samples for deck 05 (slide "Equipment impairment Ie — the codec").

One sentence of clean narrowband speech is encoded and decoded again with each codec, and the decoded
signal is written as 16-bit 8 kHz WAV to ``public/audio/05/`` so any browser can play it.

Source speech: Open Speech Repository, OSR_us_000_0010_8k.wav (Harvard sentences, female talker),
https://www.voiptroubleshooter.com/open_speech/ — "freely available for use in VoIP testing, research,
development … We do require that you identify the source of the speech materials as 'Open Speech
Repository'." The trimmed reference is kept in ``public/audio/05/reference.wav``; it is downloaded and cut
only if missing.

Needs curl, ffmpeg (G.711, G.726, G.723.1) and a C compiler with the bcg729 library (G.729 Annex A/B).
G.728 and G.723.1 at 5.3 kbit/s have no freely available encoder, so they are not generated.

Run from anywhere::

    python3 scripts/generate-codec-samples.py
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public' / 'audio' / '05'
SOURCE_URL = 'https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav'
CUT = ('0', '7.3')  # two sentences: "The birch canoe slid on the smooth planks. Glue the sheet to the dark blue background."

# (output name, ffmpeg encoder options) — each is encoded into a Matroska container and decoded back
FFMPEG_CODECS = [
    ('g711-alaw', ['-c:a', 'pcm_alaw']),
    ('g726-40k', ['-c:a', 'g726', '-b:a', '40k']),
    ('g726-32k', ['-c:a', 'g726', '-b:a', '32k']),
    ('g726-24k', ['-c:a', 'g726', '-b:a', '24k']),
    ('g726-16k', ['-c:a', 'g726', '-b:a', '16k']),
    ('g723-1-6k3', ['-c:a', 'g723_1', '-b:a', '6300']),
]


def ffmpeg(*args: str) -> None:
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *args], check=True)


def to_wav(src: Path, dst: Path) -> None:
    """Decode anything ffmpeg reads into 16-bit mono 8 kHz WAV."""
    ffmpeg('-i', str(src), '-ac', '1', '-ar', '8000', '-c:a', 'pcm_s16le', str(dst))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    reference = OUT / 'reference.wav'
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        if not reference.exists():
            full = tmp / 'osr.wav'
            # curl rather than urllib: the server answers urllib's default request with HTTP 406
            subprocess.run(['curl', '-sSfL', '-m', '60', '-o', str(full), SOURCE_URL], check=True)
            ffmpeg('-i', str(full), '-ss', CUT[0], '-to', CUT[1], '-af', 'afade=t=out:st=7.2:d=0.1',
                   '-ac', '1', '-ar', '8000', '-c:a', 'pcm_s16le', str(reference))

        for name, opts in FFMPEG_CODECS:
            coded = tmp / f'{name}.mka'
            ffmpeg('-i', str(reference), *opts, str(coded))
            to_wav(coded, OUT / f'{name}.wav')

        # G.729A (and Annex B VAD/DTX) through bcg729: raw PCM in, decoded raw PCM out.
        helper = tmp / 'g729-roundtrip'
        subprocess.run(['cc', '-O2', '-o', str(helper), str(ROOT / 'scripts' / 'g729-roundtrip.c'), '-lbcg729'],
                       check=True)
        raw = tmp / 'reference.raw'
        ffmpeg('-i', str(reference), '-f', 's16le', '-ac', '1', '-ar', '8000', str(raw))
        for name, args in [('g729a', []), ('g729a-vad', ['vad']), ('g729a-vad-nocng', ['vad-nocng'])]:
            decoded = tmp / f'{name}.raw'
            with raw.open('rb') as src, decoded.open('wb') as dst:
                subprocess.run([str(helper), *args], stdin=src, stdout=dst, check=True)
            ffmpeg('-f', 's16le', '-ar', '8000', '-ac', '1', '-i', str(decoded), '-c:a', 'pcm_s16le',
                   str(OUT / f'{name}.wav'))

    print(f'Codec samples written to {OUT}')


if __name__ == '__main__':
    main()
