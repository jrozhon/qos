#!/usr/bin/env python3
"""Generate the video samples and measured data for deck 06 (video quality assessment).

Sources: two uncompressed 720p50 4:2:0 test sequences of SVT Sveriges Television AB, as distributed by
Xiph.Org (https://media.xiph.org/video/derf/): ``old_town_cross`` (panning view over Stockholm; sky, spires,
roofs — moderate SI, low TI) and ``park_joy`` (people running past trees and water — high SI, high TI).
ReadMe_720p.txt: "Restrictions of use: No restrictions. Copyright: No copyright." Only the first 100 frames
(2 s) of each are downloaded, with an HTTP range request, into ``~/.cache/qos-slides/``.

Writes:

* ``public/images/06/artefact-*.png`` — one zoomed crop of old_town_cross: the reference and the three
  classic compression artefacts (blocking: MPEG-2; blurring: H.264; ringing: HEVC, all at very low bit rates)
* ``public/images/06/explorer.png`` — the grayscale crop used by ``components/QualityExplorer.vue``
* ``public/video/06/*.mp4`` (+ ``*.jpg`` posters for the PDF export) — park_joy clips: reference,
  low-bit-rate MPEG-2, a transmission error propagating through a GOP, and a stall
* ``scripts/data/06-video-metrics.json`` — measured rate–quality points (three codecs, two contents),
  per-resolution curves for the convex hull, and per-frame VMAF of the packet-loss clip; read by
  ``scripts/generate-figures.py``

Needs curl and ffmpeg built with libx264, libx265, libsvtav1, mpeg2video and libvmaf. Run from anywhere::

    python3 scripts/generate-video-samples.py
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / 'public' / 'images' / '06'
VIDEO = ROOT / 'public' / 'video' / '06'
DATA = ROOT / 'scripts' / 'data' / '06-video-metrics.json'
CACHE = Path.home() / '.cache' / 'qos-slides'

BASE_URL = 'https://media.xiph.org/video/derf/y4m/'
HEADER = 35               # 'YUV4MPEG2 W1280 H720 F50:1 Ip A1:1\n'
FRAME = 6 + 1280 * 720 * 3 // 2  # 'FRAME\n' + one 4:2:0 picture
FRAMES = 100              # 2 s at 50 frames/s
DURATION = FRAMES / 50
SOURCES = {'old_town_cross': 'old_town_cross_420_720p50.y4m', 'park_joy': 'park_joy_420_720p50.y4m'}

# Rate–quality sweeps: constant-quality settings chosen so the three codecs cover a similar bit-rate range.
CODECS = {
    'H.264': (['-c:v', 'libx264', '-preset', 'medium'], '-crf', [20, 24, 28, 32, 36, 40]),
    'HEVC': (['-c:v', 'libx265', '-preset', 'medium', '-x265-params', 'log-level=error'], '-crf', [22, 26, 30, 34, 38, 42]),
    'AV1': (['-c:v', 'libsvtav1', '-preset', '8'], '-crf', [38, 45, 51, 56, 60, 63]),
}
LADDER = [(1280, 720), (960, 540), (640, 360), (480, 270)]   # convex hull: H.264 at four resolutions
LADDER_CRF = [18, 22, 26, 30, 34, 38, 42]

# Crops: artefact stills (x, y, w, h in the 1280 x 720 frame, shown 2x enlarged) and the explorer image.
ARTEFACT_CROP = (592, 262, 120, 90)
ARTEFACTS = {  # name: encoder options (old_town_cross, 2 s)
    'blocking': ['-c:v', 'mpeg2video', '-b:v', '1500k', '-g', '12'],
    'blurring': ['-c:v', 'libx264', '-preset', 'medium', '-b:v', '250k'],
    'ringing': ['-c:v', 'libx265', '-b:v', '150k', '-x265-params', 'log-level=error'],
}
EXPLORER_CROP = (556, 190, 192, 192)
STILL_FRAME = 50

LOSS_FRAME = 12      # the transmission error hits the P-frame decoded around here (GOP 50: I-frames at 0, 50)
STALL_AT, STALL_S = 40, 1.2  # freeze after frame 40 for 1.2 s


def ffmpeg(*args: str) -> None:
    # SVT_LOG=1: SVT-AV1 prints its banner and memory report to stderr unless limited to errors
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *args], check=True,
                   env={**os.environ, 'SVT_LOG': '1'})


def source(name: str) -> Path:
    """First FRAMES frames of one SVT sequence, downloaded once with a range request."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / SOURCES[name]
    size = HEADER + FRAMES * FRAME
    if not path.exists() or path.stat().st_size != size:
        subprocess.run(['curl', '-sSf', '-r', f'0-{size - 1}', '-o', str(path), BASE_URL + SOURCES[name]], check=True)
    return path


def still(video: Path, crop: tuple[int, int, int, int], dst: Path, scale: int = 2, gray: bool = False) -> None:
    x, y, w, h = crop
    vf = f'select=eq(n\\,{STILL_FRAME}),crop={w}:{h}:{x}:{y}'
    if scale > 1:
        vf += f',scale={w * scale}:{h * scale}:flags=neighbor'
    if gray:
        vf += ',format=gray'
    ffmpeg('-i', str(video), '-vf', vf, '-frames:v', '1', str(dst))


def metrics(distorted: Path, reference: Path, tmp: Path, upscale: tuple[int, int] | None = None) -> dict:
    """VMAF (default model) and PSNR-Y of distorted against reference: pooled means and per-frame VMAF."""
    log = tmp / 'vmaf.json'
    pre = f'scale={upscale[0]}:{upscale[1]}:flags=bicubic,' if upscale else ''
    ffmpeg('-i', str(distorted), '-i', str(reference), '-lavfi',
           f'[0:v]{pre}setpts=PTS-STARTPTS[d];[1:v]setpts=PTS-STARTPTS[r];'
           f'[d][r]libvmaf=log_fmt=json:log_path={log}:feature=name=psnr:n_threads=8', '-f', 'null', '-')
    data = json.loads(log.read_text())
    return {'vmaf': data['pooled_metrics']['vmaf']['mean'], 'psnr': data['pooled_metrics']['psnr_y']['mean'],
            'frames': [f['metrics']['vmaf'] for f in data['frames']]}


def kbps(path: Path) -> float:
    return path.stat().st_size * 8 / DURATION / 1000


def web(src: Path, name: str, vf: str = '', poster: int = STILL_FRAME) -> None:
    """Browser copy (H.264, 854 x 480, visually near-transparent) and a poster frame for the PDF export."""
    scale = 'scale=854:480:flags=bicubic'
    ffmpeg('-i', str(src), '-vf', f'{vf},{scale}' if vf else scale, '-c:v', 'libx264', '-preset', 'slow', '-crf', '20',
           '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', str(VIDEO / f'{name}.mp4'))
    ffmpeg('-i', str(VIDEO / f'{name}.mp4'), '-vf', f'select=eq(n\\,{poster})', '-frames:v', '1', '-q:v', '3',
           str(VIDEO / f'{name}.jpg'))


def drop_ts_packets(src: Path, dst: Path, frame: int) -> None:
    """Delete a burst of video TS packets inside the given frame's access unit (a lost IP datagram carries 7)."""
    data = bytearray(src.read_bytes())
    packets = [data[i:i + 188] for i in range(0, len(data), 188)]
    starts = [i for i, p in enumerate(packets) if p[1] & 0x40 and (p[1] & 0x1F) << 8 | p[2] == 0x100]
    first, last = starts[frame], starts[frame + 1]
    rng = random.Random(6)
    hole = rng.randrange(first + 2, max(first + 3, last - 21))
    kept = packets[:hole] + packets[hole + 21:]  # three datagrams of 7 x 188 bytes
    dst.write_bytes(b''.join(kept))


def main() -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    VIDEO.mkdir(parents=True, exist_ok=True)
    DATA.parent.mkdir(parents=True, exist_ok=True)
    otc, pj = source('old_town_cross'), source('park_joy')
    result: dict = {'source': 'SVT test sequences (Xiph.Org derf), first 100 frames, 1280x720, 50 fps',
                    'rd': {}, 'ladder': {}, 'loss': {}}
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        # --- artefact stills and the explorer crop -------------------------------------------------
        still(otc, ARTEFACT_CROP, IMAGES / 'artefact-reference.png')
        for name, opts in ARTEFACTS.items():
            coded = tmp / f'{name}.mkv'
            ffmpeg('-i', str(otc), *opts, str(coded))
            still(coded, ARTEFACT_CROP, IMAGES / f'artefact-{name}.png')
        still(otc, EXPLORER_CROP, IMAGES / 'explorer.png', scale=1, gray=True)

        # --- clips ------------------------------------------------------------------------------------
        web(pj, 'reference')
        mpeg2 = tmp / 'mpeg2.mkv'
        ffmpeg('-i', str(pj), '-c:v', 'mpeg2video', '-b:v', '3000k', '-g', '12', str(mpeg2))
        web(mpeg2, 'mpeg2-3mbit')

        clean = tmp / 'clean.ts'   # constant-quality H.264, one I-frame per second, no B-frames: decode order = display order
        ffmpeg('-i', str(pj), '-c:v', 'libx264', '-preset', 'medium', '-crf', '26', '-g', '50', '-keyint_min', '50',
               '-sc_threshold', '0', '-bf', '0', '-f', 'mpegts', str(clean))
        lossy = tmp / 'lossy.ts'
        drop_ts_packets(clean, lossy, LOSS_FRAME)
        decoded = tmp / 'lossy.y4m'  # the decoder conceals what it can; keep every frame so it stays aligned
        ffmpeg('-err_detect', 'ignore_err', '-i', str(lossy), '-fps_mode', 'passthrough', '-frames:v', str(FRAMES),
               str(decoded))
        web(decoded, 'packet-loss', poster=30)
        loss = metrics(decoded, pj, tmp)
        clean_m = metrics(clean, pj, tmp)
        result['loss'] = {'frame': LOSS_FRAME, 'gop': 50, 'kbps': kbps(clean), 'vmaf': loss['frames'],
                          'vmaf_clean': clean_m['frames']}

        web(pj, 'stall', f'split[a][b];[a]trim=end_frame={STALL_AT},tpad=stop_mode=clone:stop_duration={STALL_S}'
                         f'[a2];[b]trim=start_frame={STALL_AT},setpts=PTS-STARTPTS[b2];[a2][b2]concat=n=2:v=1')

        # --- rate–quality curves: three codecs, two contents ------------------------------------------
        for content, src in [('park_joy', pj), ('old_town_cross', otc)]:
            result['rd'][content] = {}
            for codec, (opts, flag, values) in CODECS.items():
                points = []
                for v in values:
                    coded = tmp / 'rd.mkv'
                    ffmpeg('-i', str(src), *opts, flag, str(v), str(coded))
                    m = metrics(coded, src, tmp)
                    points.append({'crf': v, 'kbps': kbps(coded), 'psnr': m['psnr'], 'vmaf': m['vmaf']})
                    print(f'{content:15} {codec:5} crf {v:3}  {points[-1]["kbps"]:8.0f} kbit/s  '
                          f'PSNR {m["psnr"]:5.2f}  VMAF {m["vmaf"]:5.1f}')
                result['rd'][content][codec] = points

        # --- encoding ladder: H.264 at four resolutions, upscaled back to 720p for VMAF ------------------
        for w, h in LADDER:
            points = []
            for crf in LADDER_CRF:
                coded = tmp / 'ladder.mkv'
                ffmpeg('-i', str(pj), '-vf', f'scale={w}:{h}:flags=bicubic', '-c:v', 'libx264', '-preset', 'medium',
                       '-crf', str(crf), str(coded))
                m = metrics(coded, pj, tmp, upscale=(1280, 720))
                points.append({'crf': crf, 'kbps': kbps(coded), 'vmaf': m['vmaf']})
                print(f'ladder {h:4}p crf {crf:3}  {points[-1]["kbps"]:8.0f} kbit/s  VMAF {m["vmaf"]:5.1f}')
            result['ladder'][f'{h}p'] = points

    DATA.write_text(json.dumps(result, indent=1) + '\n')
    print(f'samples written to {IMAGES}, {VIDEO}; data to {DATA}')


if __name__ == '__main__':
    main()
