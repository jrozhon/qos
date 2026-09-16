#!/usr/bin/env python3
"""Generate deck 04's five Markov packet-loss state diagrams with matplotlib.

generate-figures.py is standard-library-only by design, but hand-rolled SVG bezier math could not
produce clean curved transitions that land exactly on a node's edge. matplotlib's FancyArrowPatch
solves both: connectionstyle="arc3,rad=..." gives a properly weighted curve, and passing the node's
own Circle patch as patchA/patchB auto-clips the arrow to the circle boundary — no manual trig.

Carlito is loaded from the same woff2 files as generate-figures.py (decompressed to TTF on the fly
via the system `woff2_decompress` binary) and baked into the SVG as vector outlines
(``svg.fonttype = 'path'``), so the output is self-contained exactly like the stdlib figures — no
runtime font dependency, safe inside an <img>-embedded SVG.

Needs matplotlib, which is NOT a project dependency — run with:

    uv run --with matplotlib scripts/generate-markov-figures.py

Output lands in the same public/figures/04/*.svg paths generate-figures.py used to write, so the
deck's <img> references do not change.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use('svg')
matplotlib.rcParams['svg.fonttype'] = 'path'  # bake glyph outlines — no runtime font dependency
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / 'public' / 'figures' / '04'

# Palette — VSB-STYLE.md §1 and §6, matching generate-figures.py.
G, D, C, INK, MUT, TINT, LINE, GRID = (
    '#00A499', '#00736B', '#05C3DE', '#1A1A1A', '#5A6664', '#EBF8F7', '#BCCFCD', '#E6ECEB')
FMT = '#E4002B'  # FMT faculty red — the "Loss" state's brand colour (R26: chart series / error marks)
LTINT = '#FCE9EB'  # light tint of FMT, same treatment as TINT for the "Transmit" state


def load_carlito() -> tuple[fm.FontProperties, fm.FontProperties]:
    tmp = Path(tempfile.mkdtemp())
    props = {}
    for weight in ('Regular', 'Bold'):
        src = ROOT / f'public/fonts/Carlito-{weight}.woff2'
        dst = tmp / src.name
        shutil.copy(src, dst)
        subprocess.run(['woff2_decompress', dst.name], cwd=tmp, check=True, capture_output=True)
        ttf = dst.with_suffix('.ttf')
        fm.fontManager.addfont(str(ttf))
        props[weight] = fm.FontProperties(fname=str(ttf))
    return props['Regular'], props['Bold']


REG, BOLD = load_carlito()


def circ_pt(cx, cy, r, deg):
    rad = math.radians(deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def new_fig(w, h):
    fig, ax = plt.subplots(figsize=(w / 100, h / 100), dpi=100)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)  # y grows downward, matching generate-figures.py's SVG coordinate convention
    ax.set_aspect('equal')
    ax.axis('off')
    fig.patch.set_facecolor('white')
    return fig, ax


def node(ax, cx, cy, r, label, fill, stroke) -> Circle:
    c = Circle((cx, cy), r, facecolor=fill, edgecolor=stroke, linewidth=2.5, zorder=3)
    ax.add_patch(c)
    ax.text(cx, cy, label, fontproperties=BOLD, fontsize=24, color=INK, ha='center', va='center', zorder=4)
    return c


def edge(ax, circle_a: Circle, circle_b: Circle, rad, color, label, label_pos):
    """A transition arrow between two node boundaries — auto-clipped to each circle's edge."""
    arrow = FancyArrowPatch(circle_a.center, circle_b.center, connectionstyle=f'arc3,rad={rad}',
                             arrowstyle='-|>', mutation_scale=18, patchA=circle_a, patchB=circle_b,
                             shrinkA=0, shrinkB=0, color=color, linewidth=2.5, zorder=2)
    ax.add_patch(arrow)
    ax.text(*label_pos, label, fontproperties=BOLD, fontsize=16, color=color, ha='center', va='center', zorder=4)


def self_loop(ax, cx, cy, r, deg, color, label, spread=50, rad=-2.8, label_gap=95, fontsize=16):
    p1, p2 = circ_pt(cx, cy, r, deg - spread / 2), circ_pt(cx, cy, r, deg + spread / 2)
    loop = FancyArrowPatch(p1, p2, connectionstyle=f'arc3,rad={rad}', arrowstyle='-|>',
                            mutation_scale=16, shrinkA=0, shrinkB=0, color=color, linewidth=2.5, zorder=2)
    ax.add_patch(loop)
    lx, ly = circ_pt(cx, cy, r + label_gap, deg)
    ax.text(lx, ly, label, fontproperties=BOLD, fontsize=fontsize, color=color, ha='center', va='center', zorder=4)


def emit_pair(ax, cx, node_bottom, top_y, label_ok, label_lost):
    bw, bh, gap = 56, 42, 12
    bx1, bx2 = cx - bw - gap / 2, cx + gap / 2
    for bx, fill, stroke, label in ((bx1, TINT, G, label_ok), (bx2, LTINT, FMT, label_lost)):
        ax.add_patch(Rectangle((bx, top_y), bw, bh, facecolor=fill, edgecolor=stroke, linewidth=1.5, zorder=3))
        ax.text(bx + bw / 2, top_y + bh / 2, label, fontproperties=BOLD, fontsize=16, color=INK,
                ha='center', va='center', zorder=4)
        ax.annotate('', xy=(bx + bw / 2, top_y), xytext=(cx + (12 if bx > cx else -12), node_bottom),
                     arrowprops=dict(arrowstyle='-|>', color=MUT, lw=1.5, shrinkA=0, shrinkB=0, mutation_scale=12), zorder=2)


def caption(ax, w, y, *lines):
    for i, line in enumerate(lines):
        ax.text(w / 2, y + i * 20, line, fontproperties=REG, fontsize=13.5, color=MUT, ha='center', va='center', zorder=4)


def save(fig, name):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f'{name}.svg', format='svg', bbox_inches='tight', pad_inches=0.15, facecolor='white')
    plt.close(fig)


# Shared geometry for the four 2-state loss models.
CY, R, CXT, CXL = 140, 60, 230, 650
TOP_LABEL, BOT_LABEL = (440, 58), (440, 222)  # cross-arc label positions, matched to rad=-0.32


def two_state(name, w, h, self_t, self_l, top_label, bot_label, extra=None, cap=()):
    fig, ax = new_fig(w, h)
    cT = node(ax, CXT, CY, R, 'T', TINT, G)
    cL = node(ax, CXL, CY, R, 'L', LTINT, FMT)
    self_loop(ax, CXT, CY, R, 180, G, self_t)
    self_loop(ax, CXL, CY, R, 0, FMT, self_l)
    edge(ax, cT, cL, -0.32, G, top_label, TOP_LABEL)
    edge(ax, cL, cT, -0.32, FMT, bot_label, BOT_LABEL)
    if extra:
        extra(ax, cT, cL)
    caption(ax, w, h - 20 if len(cap) == 1 else h - 34, *cap)
    save(fig, name)


two_state('bernoulli-model', 880, 300, '1−p', 'p', 'p', '1−p',
           cap=('The simplest loss model — a single independent variable p; losses are completely independent.',))

two_state('gilbert-simple-model', 880, 300, '1−p', '1−q', 'p', 'q',
           cap=('A more elaborate Bernoulli model with a second independent variable q — can produce loss bursts.',))

two_state('gilbert-model', 880, 340, '1−p', '1−q', 'p', 'q',
           extra=lambda ax, cT, cL: emit_pair(ax, CXL, CY + R, CY + R + 34, 'h', '1−h'),
           cap=('Even in the "bad" state, the system can still transmit individual packets correctly.',))

two_state('gilbert-elliott-model', 880, 340, '1−p', '1−q', 'p', 'q',
           extra=lambda ax, cT, cL: (emit_pair(ax, CXT, CY + R, CY + R + 34, 'k', '1−k'),
                                      emit_pair(ax, CXL, CY + R, CY + R + 34, 'h', '1−h')),
           cap=('Even in the "good" state, the system can still lose a packet correctly modelled by chance.',))

# --- Four-state packet-loss model -----------------------------------------------
fig, ax = new_fig(880, 340)
cy4, r4 = 150, 46
xs = [110, 330, 550, 770]
nodes = {}
for x, num, kind, fill, stroke in zip(xs, ('4', '1', '3', '2'), ('L', 'T', 'L', 'T'),
                                       (LTINT, TINT, LTINT, TINT), (FMT, G, FMT, G)):
    nodes[num] = node(ax, x, cy4, r4, num, fill, stroke)
    ax.text(x, cy4 + r4 + 24, kind, fontproperties=REG, fontsize=13.5, color=MUT, ha='center', va='center', zorder=4)
edge(ax, nodes['4'], nodes['1'], -0.4, FMT, 'p₄₁ = 1', (220, 92))
edge(ax, nodes['1'], nodes['4'], -0.4, G, 'p₁₄', (220, 208))
edge(ax, nodes['1'], nodes['3'], -0.4, G, 'p₁₃', (440, 92))
edge(ax, nodes['3'], nodes['1'], -0.4, FMT, 'p₃₁', (440, 208))
edge(ax, nodes['3'], nodes['2'], -0.4, FMT, 'p₃₂', (660, 92))
edge(ax, nodes['2'], nodes['3'], -0.4, G, 'p₂₃', (660, 208))
self_loop(ax, xs[2], cy4, r4, 270, FMT, 'p₃₃', spread=44, rad=-2.6, label_gap=66, fontsize=15)
self_loop(ax, xs[3], cy4, r4, 270, G, 'p₂₂', spread=44, rad=-2.6, label_gap=66, fontsize=15)
caption(ax, 880, 300,
        'State 4 (isolated loss) always returns to T (p₄₁ = 1) and never repeats (p₄₄ = 0);',
        'state 3 can repeat itself (p₃₃) to model a burst of consecutive losses.')
save(fig, 'four-state-model')

print(f'Markov figures written to {FIGURES}')
