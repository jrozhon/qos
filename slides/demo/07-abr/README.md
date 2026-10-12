# Lecture 07 live demo — ABR on an emulated link

The teacher runs this on their own laptop during Lecture 07; students predict, watch and discuss. It plays one
DASH video in [dash.js](https://github.com/Dash-Industry-Forum/dash.js) over an emulated link whose throughput
follows the trace from the lecture figures, so the stalls and switches of Parts 2 and 3 happen live. Every finished
run is scored with the reference implementation of ITU-T P.1203 next to the linear QoE of the slides.

## Requirements

- Linux with `sudo` (network namespaces and `tc`), `ffmpeg` with libx264, `uv`, a browser with H.264 (Chrome,
  Chromium, Firefox).
- Internet access for `prepare` only: it downloads dash.js and the P.1203 model. The lecture itself runs offline.

## Before the lecture (once)

```bash
cd slides/demo/07-abr
uv run demo.py prepare                    # ~15 s encoding + downloads; content/ is about 200 MB
uv run demo.py prepare --source film.mp4  # optional: real 16:9 footage instead of the test pattern
```

`prepare` encodes 120 s of video into the lecture ladder (240p 0.375 → 1080p 5.8 Mbit/s, strict CBR, 4 s
segments starting with an IDR frame), plus a 64 kbit/s AAC track. Each rendition carries its rung as a caption,
so the audience sees every switch on the picture itself.

## In the lecture

```bash
sudo python3 demo.py run                  # RTT 40 ms, no loss
sudo python3 demo.py run --rtt 100 --loss 0.5
```

Open the printed address (`http://10.77.0.2:8000/`) in a browser on the same machine, pick a rule and a trace, and
press **Start run**. The link starts replaying the trace at that moment, so runs are comparable. Ctrl-C in the
terminal removes the namespace; `sudo python3 demo.py down` cleans up after a crash.

| ABR rule | What runs |
|---|---|
| throughput rule only | dash.js `abrThroughput`, all safeguards off — the textbook rule of the slides |
| buffer rule only (BOLA) | dash.js `abrBola`, all safeguards off |
| dash.js default | `abrDynamic` with the safeguards on: abandon a download that will not finish in time, insufficient-buffer guard, switch history, dropped frames |

| Trace | Shape |
|---|---|
| `lecture` | the trace of the buffer-dynamics and ABR-comparison figures: 6.5 → 1.4 (at 20 s) → 4.6 → 2.2 (at 80 s) → 6 Mbit/s |
| `wifi-to-cell` | the "which algorithm, when?" checkpoint: 20 Mbit/s, then 1.5 Mbit/s from 30 s |
| `steady-3` | a constant 3 Mbit/s link, just above the 720p rung |

Every run takes about two minutes. The results table on the page collects the runs; the sessions are saved to
`sessions/` as P.1203 input files.

## Reference run (12 Oct 2026, `lecture` trace, RTT 40 ms)

| Rule | Stalls | Stall time | Switches | Mean bit rate | Linear QoE | P.1203 |
|---|---|---|---|---|---|---|
| throughput only | 2 | 9.2 s | 5 | 3.15 Mbit/s | 28.0 | 3.37 |
| BOLA only | 0 | 0 s | 5 | 2.21 Mbit/s | 51.5 | 3.23 |
| dash.js default | 0 | 0 s | 7 | 2.12 Mbit/s | 46.9 | 3.38 |

The throughput rule keeps requesting 4.3 Mbit/s into the drop at 20 s, because its estimate only updates when a
12 s download finishes. The dash.js safeguards abandon that download instead and step down. Live numbers vary by
a few tenths; the pattern does not.

## After the lecture

```bash
uv run demo.py score                      # one row per saved session, P.1203 recomputed
```

## How the link is built

`run` does what Mininet does underneath (Lecture 09), without Mininet: a namespace `qos07` holds the web server
and is joined to the host by the veth pair `qos07-h` (10.77.0.1) ↔ `qos07-s` (10.77.0.2). Each side delays its
egress by half the RTT with netem. On the server side, netem also drops packets (`--loss`), and a tbf child qdisc
limits the rate; a thread rewrites the tbf rate once per second from the trace:

```bash
tc qdisc replace dev qos07-s root handle 1: netem delay 20ms
tc qdisc add     dev qos07-s parent 1:1 handle 10: tbf rate 6500kbit burst 4000 latency 200ms
tc qdisc change  dev qos07-s parent 1:1 handle 10: tbf rate 1400kbit burst 4000 latency 200ms   # every second
```

The P.1203 implementation ([itu-p1203/itu-p1203](https://github.com/itu-p1203/itu-p1203)) is not an official
ITU-T publication. Its licence permits use "for non-commercial research purposes" only, and the repository does not
ship it: `prepare` installs it from GitHub on the teacher's machine. `demo.py` passes `--accept-notice` to it, so
running the demo means accepting those terms. Without the model the demo still works; the P.1203 column shows n/a.
