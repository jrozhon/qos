# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Style guide

`STYLE.md` is the authoritative style guide (university colours, Carlito font stack, README skeleton, equation and figure conventions, notebook layout). Read it before editing any README, notebook, figure, or `lib/params.py`, and run its §8 checklist before committing. It is derived from the VSB-TUO visual identity manual (`manual.pdf`, Czech).

## What this repo is

Teaching material for a university course on Quality of Service / Quality of Experience (VSB-TUO, FEECS). Students work on laboratory servers over SSH for every lesson; Jupyter is served with `--ip 0.0.0.0` for that reason. Each `qos-NN/` directory is one lesson: a `README.md` with theory, a Jupyter notebook with tasks for students, and (for lessons 01–04) a small Python library the notebook imports. There is no application, no test suite, and no CI. `support/` holds scratch notebooks and media used while authoring lessons — not student-facing.

Lesson map:

| Dir | Topic | Notable deps / tools |
|---|---|---|
| `qos-01` | Signals, PCM, Gaussian noise, Shannon capacity — interactive Bokeh/Panel sliders | bokeh, panel, jupyter-bokeh |
| `qos-02` | Probability distributions, Poisson process, M/M/1 queues — discrete-event simulation | simpy, loguru, networkx |
| `qos-03` | Packet crafting, VoIP/RTP, `tc netem`, audio extraction from pcap, PESQ/ViSQOL scoring | scapy, scipy; needs Wireshark/tshark, tcpreplay, root/capabilities; PESQ and ViSQOL binaries are external (paths set in the notebook, `score_pair` returns NaN without them) |
| `qos-04` | PSNR / SSIM image quality metrics | pillow, scipy |
| `qos-05`–`qos-07` | Mininet SDN emulation, QoS queuing (PQ/CQ/WFQ/LLQ) | notebook-only; tasks run in the Mininet CLI, not in Python |

## Commands

Each lesson with a `pyproject.toml` is its own isolated `uv` project — there is no root-level environment. Always `cd` into the lesson first.

```bash
cd qos-01                          # or qos-02, qos-03
uv sync                            # create .venv and install pinned deps
uv run jupyter lab --ip 0.0.0.0    # --ip 0.0.0.0 because students run on remote lab machines
uv add <package>                   # add a dependency to that lesson's pyproject.toml
```


Notebooks are the only "runnable" thing. To execute one headlessly for a sanity check:

```bash
cd qos-02 && uv run jupyter nbconvert --to notebook --execute qos_02/exercise_02.ipynb --output /tmp/out.ipynb
```

(qos-03 and qos-05+ notebooks require network capabilities / external hosts and will not execute cleanly unattended.)

## Structure conventions

- Package layout inside a lesson: `qos-NN/qos_NN/exercise_NN.ipynb` next to `qos_NN/lib/core.py` (and optionally `lib/params.py`). Notebooks import with `from lib.core import ...` — a bare relative import that only works because Jupyter sets the kernel cwd to the notebook's directory. The `qos_NN` package is *not* installed; don't change imports to `qos_NN.lib.core` without also changing how the notebook is launched.
- `lib/params.py` (identical in 01–04) holds the shared matplotlib `rc_params` dict and `colors` palette; the target content is in `STYLE.md` §5.1. If you touch one, mirror it in the other.
- `lib/core.py` in each lesson uses `typing.Protocol` classes as the public interface (`Signal`, `PacketSourceProto`, `SwitchProto`, …) with concrete implementations below them. Code is heavily docstringed in NumPy style because students read it; keep that style.
- `qos-02/lib/core.py` is a simpy pipeline: `PacketSource → Switch(SwitchPort…) → PacketSink`, with `NetworkTap` attaching to a `SwitchPort` for statistics and `PacketFork` splitting traffic probabilistically. Components are wired by passing a `destination` and each exposes `start()` returning a `simpy.Process`. Inter-arrival/size arguments accept either a number or a zero-arg callable (use `functools.partial` with a numpy RNG).
- Some `core.py` functions are marked "meant for the teacher" (e.g. `calc_channel_capacity`, `calc_signal_power` in qos-01): the notebook asks students to reimplement them before importing the reference version. Don't remove the reference implementations or the "implement first" prompts.
- Lesson READMEs contain LaTeX equations rendered by GitHub; several past commits are "equation rendering fix", so verify `$$…$$` blocks render on GitHub after editing.

## Branches

Work happens on year branches (`2026` currently); `main` is what students clone. Other remote branches (`filip`, `honza`, `test`) belong to co-authors.
