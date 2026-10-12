#!/usr/bin/env python3
"""Live demo for Lecture 07: dash.js over an emulated link whose throughput follows a trace.

The teacher runs this on their own laptop during the lecture; students predict, watch and discuss. Three steps:

    uv run demo.py prepare            # once: encode the DASH ladder, fetch dash.js, install the P.1203 model
    sudo python3 demo.py run          # each lecture: emulated link + web server, then open the printed URL
    uv run demo.py score              # optional: re-score every saved session with ITU-T P.1203

``run`` builds the link the way Mininet does (Lecture 09) but without Mininet: a network namespace ``qos07``
holds the web server and is joined to the host by a veth pair. On the server side, a netem qdisc adds half the
RTT (and optional random loss) and a tbf child qdisc limits the rate; a thread rewrites the tbf rate every second
from the throughput trace, starting the moment the player page starts a run. The browser stays on the host and
reaches the server at 10.77.0.2, so all its traffic crosses the shaped link.

``run`` uses only the standard library, because it runs as root; ``prepare`` and ``score`` use the uv project
next to this file (the P.1203 reference implementation, https://github.com/itu-p1203/itu-p1203).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from urllib.parse import urlsplit
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTENT = HERE / 'content'      # generated: DASH manifest, segments, dash.js (git-ignored)
SESSIONS = HERE / 'sessions'    # generated: one JSON per finished run (git-ignored)
P1203 = HERE / '.venv' / 'bin' / 'p1203-standalone'

NS, DEV_HOST, DEV_NS = 'qos07', 'qos07-h', 'qos07-s'
IP_HOST, IP_NS, PORT = '10.77.0.1', '10.77.0.2', 8000

DASHJS = 'https://cdn.jsdelivr.net/npm/dashjs@4.7.4/dist/dash.all.min.js'
SEG, DURATION, FPS, AUDIO_KBPS = 4, 120, 25, 64
# The ladder of the lecture figures (a subset of Netflix's former fixed ladder): width, height, kbit/s
LADDER = [(426, 240, 375), (640, 360, 750), (854, 480, 1750), (1280, 720, 3000), (1920, 1080, 4300), (1920, 1080, 5800)]
UNLIMITED = 1000.0  # Mbit/s — the link between runs


def lecture_trace() -> list[float]:
    """The throughput trace of the lecture figures (same levels and seed as make_trace in generate-figures.py)."""
    rnd = random.Random(7)
    levels = [(0, 6.5), (20, 1.4), (48, 4.6), (80, 2.2), (100, 6.0)]
    return [round(max(0.3, [v for t0, v in levels if sec >= t0][-1] * (1 + rnd.uniform(-0.18, 0.18))), 3)
            for sec in range(400)]


TRACES = {
    'lecture': lecture_trace(),                  # Part 2 and Part 3 figures: drops to 1.4 and 2.2 Mbit/s
    'wifi-to-cell': [20.0] * 30 + [1.5] * 370,   # the "which algorithm, when?" checkpoint
    'steady-3': [3.0] * 400,                     # a constant link just above the 720p rung
}


# --- prepare --------------------------------------------------------------------------------------------------
def prepare(args: argparse.Namespace) -> None:
    """Encode the ladder into one DASH presentation, download dash.js, and install the P.1203 model."""
    CONTENT.mkdir(exist_ok=True)
    for old in CONTENT.glob('*.m4s'):
        old.unlink()
    branches = ''.join(f'[s{i}]' for i in range(len(LADDER)))
    filters = [f'[0:v]fps={FPS},split={len(LADDER)}{branches}']
    for i, (w, h, kbps) in enumerate(LADDER):
        mbps = f'{kbps / 1000:g}'
        label = f'{h}p · {mbps if "." in mbps else mbps + ".0"} Mbit/s'
        filters.append(f'[s{i}]scale={w}:{h},setdar=16/9,drawtext=text=\'{label}\':fontsize=h/12:fontcolor=white:'
                       f'box=1:boxcolor=black@0.6:boxborderw=12:x=24:y=h-th-36[v{i}]')
    source = (['-stream_loop', '-1', '-i', str(args.source)] if args.source
              else ['-f', 'lavfi', '-i', f'testsrc2=size=1920x1080:rate={FPS}'])
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-stats', '-y', *source,
           '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-t', str(DURATION),
           '-filter_complex', ';'.join(filters)]
    for i in range(len(LADDER)):
        cmd += ['-map', f'[v{i}]']
    cmd += ['-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
            # one IDR frame every 4 s in every rendition, so the player can switch at each segment boundary
            '-force_key_frames', f'expr:gte(t,n_forced*{SEG})', '-sc_threshold', '0']
    # strict CBR (x264 pads with filler data): every segment is as large as its rung says, even for easy content
    cmd += ['-x264-params', 'nal-hrd=cbr']
    for i, (_, _, kbps) in enumerate(LADDER):
        cmd += [f'-b:v:{i}', f'{kbps}k', f'-minrate:v:{i}', f'{kbps}k', f'-maxrate:v:{i}', f'{kbps}k',
                f'-bufsize:v:{i}', f'{kbps}k']
    cmd += ['-c:a', 'aac', '-b:a', f'{AUDIO_KBPS}k', '-f', 'dash', '-seg_duration', str(SEG),
            '-use_template', '1', '-use_timeline', '0', '-adaptation_sets', 'id=0,streams=v id=1,streams=a',
            str(CONTENT / 'manifest.mpd')]
    print('encoding', len(LADDER), 'renditions of', DURATION, 's ...')
    subprocess.run(cmd, check=True)
    print('downloading', DASHJS)
    urllib.request.urlretrieve(DASHJS, CONTENT / 'dash.all.min.js')
    if shutil.which('uv'):
        subprocess.run(['uv', 'sync', '--project', str(HERE)], check=True)
    print(f'ready — now: sudo python3 {Path(__file__).name} run')


# --- run (root) -----------------------------------------------------------------------------------------------
def sh(*cmd: str, check: bool = True) -> None:
    subprocess.run(cmd, check=check, stdout=subprocess.DEVNULL, stderr=None if check else subprocess.DEVNULL)


def link_down() -> None:
    sh('ip', 'netns', 'del', NS, check=False)  # deleting the namespace also deletes the veth pair


def run(args: argparse.Namespace) -> None:
    """Create the namespace and the shaped veth link, start the server inside it, and tear it all down on exit."""
    if os.geteuid() != 0:
        sys.exit('run needs root for the network namespace and tc: sudo python3 demo.py run')
    if not (CONTENT / 'manifest.mpd').exists():
        sys.exit('no content yet — run "uv run demo.py prepare" first (as your own user)')
    link_down()
    sh('ip', 'netns', 'add', NS)
    sh('ip', 'link', 'add', DEV_HOST, 'type', 'veth', 'peer', 'name', DEV_NS, 'netns', NS)
    sh('ip', 'addr', 'add', f'{IP_HOST}/24', 'dev', DEV_HOST)
    sh('ip', 'link', 'set', DEV_HOST, 'up')
    for cmd in (['ip', 'addr', 'add', f'{IP_NS}/24', 'dev', DEV_NS], ['ip', 'link', 'set', DEV_NS, 'up'],
                ['ip', 'link', 'set', 'lo', 'up']):
        sh('ip', 'netns', 'exec', NS, *cmd)
    # requests (and TCP ACKs) get the other half of the RTT on the host side of the pair
    sh('tc', 'qdisc', 'replace', 'dev', DEV_HOST, 'root', 'netem', 'delay', f'{args.rtt / 2:g}ms')
    server = [sys.executable, str(Path(__file__).resolve()), 'serve', '--rtt', str(args.rtt), '--loss', str(args.loss)]
    print(f'\n  emulated link up: RTT {args.rtt:g} ms, loss {args.loss:g} %\n'
          f'  open  http://{IP_NS}:{PORT}/  in a browser on this machine (Ctrl-C here to stop)\n')
    try:
        subprocess.run(['ip', 'netns', 'exec', NS, *server])
    except KeyboardInterrupt:
        pass
    finally:
        link_down()
        print('emulated link removed')


# --- serve (root, inside the namespace) -----------------------------------------------------------------------
class Link:
    """The server side of the veth pair: netem (half the RTT, loss) with a tbf child that follows the trace."""

    def __init__(self, rtt: float, loss: float):
        netem = ['delay', f'{rtt / 2:g}ms'] + (['loss', f'{loss:g}%'] if loss else [])
        sh('tc', 'qdisc', 'replace', 'dev', DEV_NS, 'root', 'handle', '1:', 'netem', *netem)
        self.mbps, self.stop_event, self.thread = 0.0, threading.Event(), None
        self.set_rate(UNLIMITED, op='add')

    def set_rate(self, mbps: float, op: str = 'change') -> None:
        burst = max(4000, int(mbps * 1e6 / 8 / 250))  # bytes: at least 4 ms of traffic at this rate
        sh('tc', 'qdisc', op, 'dev', DEV_NS, 'parent', '1:1', 'handle', '10:', 'tbf',
           'rate', f'{int(mbps * 1000)}kbit', 'burst', str(burst), 'latency', '200ms')
        self.mbps = mbps

    def play(self, trace: list[float]) -> None:
        self.stop()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._replay, args=(trace, self.stop_event), daemon=True)
        self.thread.start()

    def _replay(self, trace: list[float], stop: threading.Event) -> None:
        t0 = time.monotonic()
        for k, mbps in enumerate(trace):
            self.set_rate(mbps)
            if stop.wait(max(0.0, t0 + k + 1 - time.monotonic())):
                return

    def stop(self) -> None:
        if self.thread:
            self.stop_event.set()
            self.thread.join()
            self.thread = None
        self.set_rate(UNLIMITED)


def p1203(session_file: Path) -> dict:
    """Score one saved session with the P.1203 reference implementation (mode 0: metadata only)."""
    if not P1203.exists():
        return {'error': 'P.1203 not installed — run "uv run demo.py prepare"'}
    out = subprocess.run([str(P1203), '--accept-notice', str(session_file)], capture_output=True, text=True)
    try:
        result = next(iter(json.loads(out.stdout).values()))
        return {'O46': result['O46'], 'O35': result['O35']}
    except (ValueError, StopIteration, KeyError):
        return {'error': (out.stderr.strip().splitlines() or ['P.1203 failed'])[-1]}


def owner_chown(path: Path) -> None:
    """Files written as root under sudo go back to the user who called sudo."""
    if 'SUDO_UID' in os.environ:
        os.chown(path, int(os.environ['SUDO_UID']), int(os.environ['SUDO_GID']))


def serve(args: argparse.Namespace) -> None:
    link = Link(args.rtt, args.loss)
    config = {'traces': TRACES, 'rtt': args.rtt, 'loss': args.loss, 'segment': SEG, 'audioKbps': AUDIO_KBPS}

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(HERE), **kw)

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')  # every run must download its segments again
            super().end_headers()

        def log_message(self, *_):  # keep the terminal quiet during the lecture
            pass

        def reply(self, obj: dict, code: int = 200) -> None:
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlsplit(self.path).path  # the player page takes ?abr=…&trace=…&autostart=1
            if path == '/':
                path = self.path = '/player.html'
            if path == '/api/config':
                return self.reply(config)
            if path == '/player.html' or path.startswith('/content/'):
                return super().do_GET()
            self.send_error(404)

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
            if self.path == '/api/start':
                link.play(TRACES[body.get('trace', 'lecture')])
                return self.reply({'ok': True})
            if self.path == '/api/stop':
                link.stop()
                return self.reply({'ok': True})
            if self.path == '/api/session':
                SESSIONS.mkdir(exist_ok=True)
                owner_chown(SESSIONS)
                name = f'{time.strftime("%Y%m%d-%H%M%S")}-{body["meta"]["abr"]}-{body["meta"]["trace"]}.json'
                path = SESSIONS / name
                path.write_text(json.dumps(body, indent=1))
                owner_chown(path)
                return self.reply({'file': name, **p1203(path)})
            self.send_error(404)

    httpd = ThreadingHTTPServer((IP_NS, PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        link.stop()


# --- score ----------------------------------------------------------------------------------------------------
def score(args: argparse.Namespace) -> None:
    """Print one row per saved session: what the player saw and what P.1203 makes of it."""
    files = sorted(SESSIONS.glob('*.json'))
    if not files:
        sys.exit('no sessions yet')
    print(f'{"session":42} {"start s":>7} {"stalls":>6} {"stall s":>7} {"switch":>6} {"mean Mb/s":>9} '
          f'{"lin. QoE":>8} {"P.1203":>6}')
    for f in files:
        m = json.loads(f.read_text())['metrics']
        q = p1203(f)
        print(f'{f.stem:42} {m["startup"]:7.2f} {m["stalls"]:6d} {m["stallTime"]:7.1f} {m["switches"]:6d} '
              f'{m["meanBitrate"]:9.2f} {m["linearQoE"]:8.1f} {q.get("O46", float("nan")):6.2f}')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('prepare', help='encode the DASH content, fetch dash.js, install P.1203')
    p.add_argument('--source', type=Path, help='a 16:9 video to use instead of the test pattern (looped to 120 s)')
    for name in ('run', 'serve'):  # serve is run's internal half, started inside the namespace
        p = sub.add_parser(name, **({'help': 'start the emulated link and the server (needs root)'}
                                    if name == 'run' else {}))
        p.add_argument('--rtt', type=float, default=40, help='round-trip time in ms (default 40)')
        p.add_argument('--loss', type=float, default=0, help='random loss on the server-to-player direction, %%')
    sub.add_parser('score', help='score every saved session with ITU-T P.1203')
    sub.add_parser('down', help='remove a left-over namespace (needs root)')
    args = ap.parse_args()
    {'prepare': prepare, 'run': run, 'serve': serve, 'score': score, 'down': lambda _: link_down()}[args.cmd](args)


if __name__ == '__main__':
    main()
