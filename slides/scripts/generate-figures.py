#!/usr/bin/env python3
"""Generate the lecture figures as self-contained SVGs (standard library only).

Each deck has one section below; its figures land in ``public/figures/<deck>/``.
The SVGs embed Carlito so the built site and the PDF export render identically,
and they follow VSB-STYLE.md: brand green, FEI cyan as a small accent only,
hard-edged boxes, one CSS pixel per SVG unit on the 980 x 552 slide canvas.

Run from anywhere::

    python3 scripts/generate-figures.py          # both themes: name.svg and name.dark.svg
    python3 scripts/generate-figures.py dark     # one theme only
"""
from __future__ import annotations

import base64
import json
import math
import random
import subprocess
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / 'public' / 'figures'

# Palette — VSB-STYLE.md §1, §6 and §10. Cyan never carries text (R5).
# Every figure is written twice: light (name.svg, also used by the PDF export) and dark (name.dark.svg,
# shown by components/Figure.vue when the deck is in dark mode). Figures must take every colour from this
# table — a literal hex value in a figure would stay light-mode in the dark variant.
PALETTES = {
    'light': dict(
        G='#00A499', D='#00736B', C='#05C3DE', INK='#1A1A1A', MUT='#5A6664', TINT='#EBF8F7', LINE='#BCCFCD',
        GRID='#E6ECEB', FMT='#E4002B', EKF='#0047BB', FBI='#FF8200',
        PAPER='#FFFFFF', NEUTRAL='#F6F8F8', NEUTRAL2='#F3F6F5', CTINT='#E8F9FC',
        TINT2='#D6F0EE', TINT3='#BFE7E3', TINT4='#A6DDD8',
        YTINT='#FFF4D6', OTINT='#FFE6D0', RTINT='#FBD9DF', GREYTINT='#F3F3F3',
        IMG0='#000000', IMG1='#FFFFFF'),
    # dark: the deck's dark background (#0E1A19, style.css), R7's light green for green text, lightened
    # series colours that keep ≥ 3:1 on the background, and dark tints of the same hues for fills
    'dark': dict(
        G='#00A499', D='#4DD8CE', C='#05C3DE', INK='#E8ECEB', MUT='#9BA8A6', TINT='#143633', LINE='#3C5552',
        GRID='#223432', FMT='#FF4D6D', EKF='#6E9BFF', FBI='#FF8200',
        PAPER='#0E1A19', NEUTRAL='#16292A', NEUTRAL2='#1B2B2C', CTINT='#0C3239',
        TINT2='#1A4541', TINT3='#20564F', TINT4='#276A61',
        YTINT='#3A3218', OTINT='#3D2A1A', RTINT='#3E1E25', GREYTINT='#232626',
        # image pixels are content, not chrome: black and white stay the same in both themes
        IMG0='#000000', IMG1='#FFFFFF'),
}
if len(sys.argv) < 2:  # no theme given: run the script once per theme
    for theme in PALETTES:
        subprocess.run([sys.executable, __file__, theme], check=True)
    sys.exit(0)
THEME = sys.argv[1]
globals().update(PALETTES[THEME])
SUFFIX = '' if THEME == 'light' else f'.{THEME}'

FONTS = ''.join(
    '@font-face{font-family:Carlito;font-weight:%d;src:url(data:font/woff2;base64,%s) format("woff2");}'
    % (weight, base64.b64encode((ROOT / f'public/fonts/Carlito-{name}.woff2').read_bytes()).decode())
    for name, weight in [('Regular', 400), ('Bold', 700)])


class SVG:
    """Minimal SVG writer with the deck's type scale: 18 px labels, 15 px notes, 24 px callouts."""

    def __init__(self, deck: str, name: str, h: int, title: str, desc: str, w: int = 880):
        self.deck, self.name, self.w, self.h = deck, name, w, h
        markers = ''.join(
            f'<marker id="{n}" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" '
            f'markerWidth="14" markerHeight="14" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{c}"/></marker>'
            for n, c in [('green', G), ('ink', INK), ('cyan', C), ('muted', MUT), ('red', FMT)])
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="title desc">',
            f'<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>',
            f'<defs><style>{FONTS} text{{font-family:Carlito,Calibri,sans-serif;fill:{INK};font-size:18px}} '
            f'.small{{font-size:15px;fill:{MUT}}} .label{{font-size:16px;font-weight:700;fill:{D};letter-spacing:1px}} '
            f'.bold{{font-weight:700}} .big{{font-size:24px;font-weight:700}} .green{{fill:{D}}} '
            f'.math{{font-style:italic}}</style>{markers}</defs>',
        ]
        self.rect(0, 0, w, h, PAPER, 'none')

    # --- primitives --------------------------------------------------------
    def rect(self, x, y, w, h, fill=TINT, stroke=LINE, sw=1):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def text(self, x, y, s, cls='', anchor='start'):
        self.parts.append(f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}">{escape(s)}</text>')

    def text_rot(self, x, y, s, cls='', anchor='middle', angle=-90):
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}" '
            f'transform="rotate({angle} {x:.1f} {y:.1f})">{escape(s)}</text>')

    def line(self, x1, y1, x2, y2, color=G, sw=2, dash=False, arrow=None):
        self.path(f'M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}', color, sw, dash, arrow)

    def path(self, d, color=G, sw=2, dash=False, arrow=None):
        self.parts.append(
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round"'
            + (' stroke-dasharray="6 5"' if dash else '') + (f' marker-end="url(#{arrow})"' if arrow else '') + '/>')

    def polyline(self, pts, color=G, sw=2.5, dash=False):
        self.path('M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts), color, sw, dash)

    def dot(self, x, y, r=4, fill=G):
        self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>')

    def box(self, x, y, w, h, title, sub='', fill=TINT):
        self.rect(x, y, w, h, fill)
        self.rect(x, y, 4, h, G, 'none')
        # Two-line boxes put the title on the upper line; a title-only box centres it.
        self.text(x + 14, y + 27 if sub else y + h / 2 + 6, title, 'bold')
        if sub:
            self.text(x + 14, y + 49, sub, 'small')

    def save(self):
        out = FIGURES / self.deck
        out.mkdir(parents=True, exist_ok=True)
        (out / f'{self.name}{SUFFIX}.svg').write_text('\n'.join(self.parts + ['</svg>']) + '\n')


class Axes:
    """Cartesian axes inside an SVG. Data coordinates map linearly onto a pixel box."""

    def __init__(self, svg: SVG, x0, y0, w, h, xr, yr, xlabel='', ylabel='', xticks=(), yticks=(), grid=True):
        self.s, self.x0, self.y0, self.w, self.h, self.xr, self.yr = svg, x0, y0, w, h, xr, yr
        for v, lab in xticks:
            px = self.px(v)
            if grid:
                svg.line(px, y0, px, y0 + h, GRID, 1)
            svg.text(px, y0 + h + 20, lab, 'small', 'middle')
        for v, lab in yticks:
            py = self.py(v)
            if grid:
                svg.line(x0, py, x0 + w, py, GRID, 1)
            svg.text(x0 - 8, py + 5, lab, 'small', 'end')
        svg.line(x0, y0 + h, x0 + w, y0 + h, INK, 1.5, arrow='ink')
        svg.line(x0, y0 + h, x0, y0, INK, 1.5, arrow='ink')
        if yr[0] < 0 < yr[1]:  # bipolar signal: draw the zero line the stems grow from
            svg.line(x0, self.py(0), x0 + w, self.py(0), MUT, 1)
        if xlabel:
            svg.text(x0 + w, y0 + h + 40, xlabel, 'small', 'end')
        if ylabel:
            svg.text_rot(x0 - 46, y0 + h / 2, ylabel, 'small')

    def px(self, x):
        return self.x0 + (x - self.xr[0]) / (self.xr[1] - self.xr[0]) * self.w

    def py(self, y):
        return self.y0 + self.h - (y - self.yr[0]) / (self.yr[1] - self.yr[0]) * self.h

    def curve(self, f, color=G, sw=2.5, n=200, dash=False, xr=None):
        a, b = xr or self.xr
        pts = [(self.px(x), self.py(f(x))) for x in (a + (b - a) * i / n for i in range(n + 1))]
        self.s.polyline(pts, color, sw, dash)

    def stem(self, x, y, color=G):
        self.s.line(self.px(x), self.py(0), self.px(x), self.py(y), color, 2)
        self.s.dot(self.px(x), self.py(y), 4, color)


# =============================================================================
# 01 — Channel capacity and introduction to information theory
# =============================================================================
DECK = '01'
sine = lambda f: (lambda t: math.sin(2 * math.pi * f * t))  # noqa: E731

# --- Communication system: the vocabulary every later slide reuses ----------
s = SVG(DECK, 'comm-system', 190, 'Block diagram of a communication system',
        'A source produces a message. The transmitter encodes it into a signal, the channel carries the signal '
        'while noise is added, and the receiver decodes the signal back into a message for the destination.')
blocks = [('Source', 'message', NEUTRAL), ('Transmitter', 'encodes into a signal', TINT),
          ('Channel', 'bandwidth B', TINT), ('Receiver', 'decodes the signal', TINT), ('Destination', 'message', NEUTRAL)]
x = 20
for i, (t, sub, fill) in enumerate(blocks):
    w = 130 if i in (0, 4) else 160
    s.box(x, 72, w, 64, t, sub, fill)
    if i < 4:
        s.line(x + w, 104, x + w + 20, 104, INK, 2, arrow='ink')
    x += w + 20
# Noise sits centred above the channel (x = 350, w = 160) and enters it from the top.
s.box(350, 6, 160, 34, 'Noise', '', PAPER)
s.line(430, 40, 430, 72, INK, 2, arrow='ink')
s.text(440, 172, 'Telephony: microphone → network → earpiece.   Information theory: message → channel symbols → message.',
       'small', 'middle')
s.save()

# --- Continuous vs discrete time --------------------------------------------
s = SVG(DECK, 'continuous-discrete', 240, 'Continuous-time and discrete-time signal',
        'Left: a continuous sine wave defined at every instant. Right: the same wave read only at sampling instants '
        'spaced by the sampling period, drawn as stems.')
for x0, title in [(60, 'CONTINUOUS TIME'), (500, 'DISCRETE TIME · SAMPLED')]:
    s.text(x0, 24, title, 'label')
    ax = Axes(s, x0, 40, 340, 150, (0, 2), (-1.3, 1.3), xticks=[(1, 'T'), (2, '2T t')], yticks=[(0, '0')])
    if x0 == 60:
        ax.curve(sine(1), G, 3)
    else:
        ax.curve(sine(1), LINE, 1.5, dash=True)
        for k in range(17):
            ax.stem(k / 8, math.sin(2 * math.pi * k / 8))
        s.text(x0, 232, 'sampling period Tₛ = 1 / fₛ', 'small')
s.text(60, 232, 'period T · frequency f = 1/T', 'small')
s.save()

# --- PCM: sampling → quantization → encoding ----------------------------------
s = SVG(DECK, 'pcm', 270, 'The three steps of pulse-code modulation',
        'Sampling reads the analog signal at regular instants. Quantization rounds each sample to one of four '
        'levels; the original sample is shown next to its rounded value. Encoding assigns each level a 2-bit code word.')
titles = ['1 · SAMPLING', '2 · QUANTIZATION · 4 levels', '3 · ENCODING · 2 bits']
# 1.15 periods across the panel so the samples do not happen to land on the levels.
pcm_sig = lambda t: math.sin(2 * math.pi * 1.15 * t + 3.12)  # noqa: E731
samples = [pcm_sig(k / 8) for k in range(9)]
levels = [round((v + 1) * 1.5) for v in samples]  # 0..3, step 2/3
for i, title in enumerate(titles):
    x0 = 45 + i * 285
    s.text(x0, 24, title, 'label')
    ax = Axes(s, x0, 38, 250, 160, (0, 1), (-1.15, 1.15), grid=False,
              yticks=[] if i == 2 else [(-1, '−1'), (0, '0'), (1, '1')])
    if i == 0:
        ax.curve(pcm_sig, LINE, 1.5, dash=True)
        for k, v in enumerate(samples):
            ax.stem(k / 8, v)
    if i == 1:
        for L in range(4):
            y = ax.py(L / 1.5 - 1)
            s.line(x0 + 12, y, x0 + 250, y, GRID, 1)  # start clear of the y-axis arrowhead
        # Original sample (grey) and the level it is rounded to (green stem); the
        # gap between them is the quantization error, discussed in person.
        for k, (v, L) in enumerate(zip(samples, levels)):
            ax.stem(k / 8, L / 1.5 - 1)
            s.dot(ax.px(k / 8), ax.py(v), 4, MUT)
        s.text(x0 + 250, 220, 'grey: original · green: quantized', 'small', 'end')
    if i == 2:
        for k, L in enumerate(levels):
            ax.stem(k / 8, L / 1.5 - 1, D)
            s.text(ax.px(k / 8), 215, format(L, '02b'), 'small', 'middle')
        s.text(x0 + 250, 240, 'stream ' + ''.join(format(L, '02b') for L in levels) + ' …', 'small', 'end')
s.text(440, 262, 'b bits per sample → 2ᵇ levels · G.711 telephony: 8 000 samples/s × 8 bits = 64 kbit/s', 'small', 'middle')
s.save()

# --- Aliasing: a 5 kHz tone sampled at 8 kHz -----------------------------------
s = SVG(DECK, 'aliasing', 270, 'Aliasing of a 5 kHz tone sampled at 8 kHz',
        'The samples of a 5 kHz sine taken every 125 microseconds lie exactly on a 3 kHz sine. After sampling the '
        'two tones cannot be told apart; the 5 kHz component folds back to 8 minus 5 equals 3 kHz.')
ax = Axes(s, 60, 36, 780, 160, (0, 1), (-1.3, 1.3),
          xticks=[(k / 8, f'{k * 0.125:g}' + (' ms' if k == 8 else '')) for k in range(0, 9, 2)], yticks=[(0, '0')])
ax.curve(lambda t: math.sin(2 * math.pi * 5 * t), LINE, 1.5, n=600)          # 5 kHz, t in ms
ax.curve(lambda t: -math.sin(2 * math.pi * 3 * t), FBI, 2.5, n=600)          # 3 kHz alias (phase-reversed)
for k in range(9):
    ax.stem(k / 8, math.sin(2 * math.pi * 5 * k / 8))
s.line(60, 250, 100, 250, LINE, 1.5); s.text(108, 255, '5 kHz tone', 'small')
s.line(210, 250, 250, 250, FBI, 2.5); s.text(258, 255, '3 kHz alias — same samples', 'small')
s.dot(470, 250, 4); s.text(482, 255, 'samples every 125 µs', 'small')
s.text(840, 256, 'f_alias = |fₛ − f| = 3 kHz', 'bold', 'end')
s.save()

# --- Gaussian probability density -------------------------------------------
s = SVG(DECK, 'gaussian', 270, 'Probability density function of Gaussian noise',
        'Two bell curves with zero mean: a narrow one with standard deviation 0.5 and a wide one with standard '
        'deviation 1. The wider curve is the stronger noise. Vertical guides mark plus and minus one sigma.')
ax = Axes(s, 70, 36, 560, 190, (-3.5, 3.5), (0, 0.85), xlabel='x  (noise amplitude)',
          xticks=[(v, str(v)) for v in (-3, -2, -1, 0, 1, 2, 3)], yticks=[(0.4, '0.4'), (0.8, '0.8')], ylabel='p(x)')
pdf = lambda sig: (lambda x: math.exp(-x * x / (2 * sig * sig)) / (sig * math.sqrt(2 * math.pi)))  # noqa: E731
ax.curve(pdf(1.0), G, 3, n=300)
ax.curve(pdf(0.5), EKF, 2.5, n=300)
for v in (-1, 1):
    s.line(ax.px(v), ax.py(0), ax.px(v), ax.py(pdf(1.0)(1)), MUT, 1, dash=True)
s.text(ax.px(0), ax.py(0.29), '−σ            +σ', 'small', 'middle')
s.line(660, 70, 700, 70, G, 3); s.text(708, 75, 'σ = 1   (stronger noise)')
s.line(660, 105, 700, 105, EKF, 2.5); s.text(708, 110, 'σ = 0.5')
s.text(660, 160, 'μ = 0 in this course', 'small')
s.text(660, 185, 'σ² = variance = noise power N', 'small')
s.text(660, 210, '68 % of samples within ±σ', 'small')
s.save()

# --- Sine plus additive Gaussian noise ---------------------------------------
s = SVG(DECK, 'signal-noise', 255, 'Harmonic signal with additive Gaussian noise',
        'A clean 1 Hz sine of amplitude 1 and the same sine after adding zero-mean Gaussian noise of variance 0.1. '
        'The noisy trace scatters around the clean one.')
rng = random.Random(1)
for x0, title in [(60, 'CLEAN SIGNAL  x(t) = sin 2πft'), (500, 'x(t) + n(t) · AWGN, σ² = 0.1')]:
    s.text(x0, 24, title, 'label')
    ax = Axes(s, x0, 40, 340, 160, (0, 2), (-1.7, 1.7), xticks=[(1, '1'), (2, '2 s')], yticks=[(-1, '−1'), (0, '0'), (1, '1')])
    if x0 == 60:
        ax.curve(sine(1), G, 3)
    else:
        ax.curve(sine(1), LINE, 1.5, dash=True)
        pts = [(ax.px(t), ax.py(math.sin(2 * math.pi * t) + rng.gauss(0, math.sqrt(0.1)))) for t in (i / 100 for i in range(201))]
        s.polyline(pts, G, 1.5)
s.text(440, 246, 'Theoretical powers: S = 0.5   ·   N = σ² = 0.1   ·   S/N = 5 ≈ 7 dB', 'bold', 'middle')
s.save()

# --- Symbols carry several bits ---------------------------------------------
s = SVG(DECK, 'symbols', 250, 'Symbol rate versus bit rate',
        'Top: a binary waveform with two levels sends one bit per symbol. Bottom: a four-level waveform sends two '
        'bits per symbol at half the symbol rate, so both waveforms carry ten bits per second.')
bits = '0110100011'
for row, (title, L) in enumerate([('M = 2 states · 1 bit per symbol', 2), ('M = 4 states · 2 bits per symbol', 4)]):
    y0 = 30 + row * 100
    s.text(50, y0 - 6, title, 'label')
    n = 10 if L == 2 else 5
    x0, w = 50, 560
    s.rect(x0, y0, w, 60, PAPER, LINE)
    for k in range(n + 1):
        s.line(x0 + k * w / n, y0, x0 + k * w / n, y0 + 60, GRID, 1)
    pts = []
    for k in range(n):
        val = int(bits[k]) if L == 2 else int(bits[2 * k:2 * k + 2], 2)
        y = y0 + 52 - val * (44 / (L - 1))
        pts += [(x0 + k * w / n, y), (x0 + (k + 1) * w / n, y)]
        s.text(x0 + (k + 0.5) * w / n, y0 + 78, bits[k] if L == 2 else bits[2 * k:2 * k + 2], 'small', 'middle')
    s.polyline(pts, G, 3)
    s.text(650, y0 + 25, f'{n} symbols / s', 'bold')
    s.text(650, y0 + 50, f'→ {len(bits)} bit/s' if L == 2 else '→ 10 bit/s = 5 Bd × 2', 'green')
s.text(440, 244, 'R_raw = Rₛ · log₂ M   →   raw bit rate = symbol rate × bits per symbol', 'big', 'middle')
s.save()

# --- Spectral efficiency vs SNR ---------------------------------------------
s = SVG(DECK, 'capacity-snr', 290, 'Shannon capacity per hertz as a function of SNR',
        'The curve C over B equals log base 2 of one plus S over N, plotted against SNR in decibels from minus 10 '
        'to 40. It is nearly flat at low SNR and grows by one bit per second per hertz for every 3 dB at high SNR.')
ax = Axes(s, 80, 30, 600, 200, (-10, 40), (0, 14), xlabel='S/N [dB]', ylabel='C / B  [bit/s/Hz]',
          xticks=[(v, str(v)) for v in range(-10, 41, 10)], yticks=[(v, str(v)) for v in (2, 4, 6, 8, 10, 12)])
ax.curve(lambda db: math.log2(1 + 10 ** (db / 10)), G, 3, n=300)
# The curve rises to the right, so labels go below-right of their point; the
# first point sits on the axis, so its label goes above-left on two lines.
for db, lab, dx, dy, anchor in [(12, 'S/N = 15.8 → 4.1 bit/s/Hz', 12, 20, 'start'),
                                (30, 'S/N = 1000 → 10 bit/s/Hz', -12, -10, 'end')]:
    c = math.log2(1 + 10 ** (db / 10))
    s.dot(ax.px(db), ax.py(c), 5, D)
    s.text(ax.px(db) + dx, ax.py(c) + dy, lab, 'small', anchor)
s.dot(ax.px(0), ax.py(1), 5, D)
s.text(ax.px(0) - 10, ax.py(1) - 24, 'S/N = 1', 'small', 'end')
s.text(ax.px(0) - 10, ax.py(1) - 6, '→ 1 bit/s/Hz', 'small', 'end')
s.text(700, 80, 'Every +3 dB of SNR', 'bold')
s.text(700, 104, 'adds ≈ 1 bit/s/Hz', 'bold')
s.text(700, 128, '(at high SNR)', 'small')
s.text(700, 170, 'Every +10 dB', 'bold')
s.text(700, 194, 'adds ≈ 3.3 bit/s/Hz', 'bold')
s.text(440, 282, 'Diminishing returns: SNR sits inside a logarithm', 'small', 'middle')
s.save()

# --- Capacity vs bandwidth for three SNRs ------------------------------------
s = SVG(DECK, 'capacity-bandwidth', 290, 'Shannon capacity as a function of bandwidth',
        'Three straight lines through the origin show capacity against bandwidth for SNR of 15, 100 and 1000. '
        'Doubling the bandwidth doubles the capacity at fixed SNR; a higher SNR only tilts the line.')
ax = Axes(s, 80, 30, 600, 200, (0, 40), (0, 420), xlabel='B [kHz]', ylabel='C [kbit/s]',
          xticks=[(v, str(v)) for v in (10, 20, 30, 40)], yticks=[(v, str(v)) for v in (100, 200, 300, 400)])
for snr, color, lab in [(1000, G, 'S/N = 1000 (30 dB) → 10.0 bit/s/Hz'), (100, EKF, 'S/N = 100 (20 dB) → 6.7 bit/s/Hz'),
                        (15, FBI, 'S/N = 15 (12 dB) → 4.0 bit/s/Hz')]:
    ax.curve(lambda b, k=math.log2(1 + snr): b * k, color, 3, n=2)
    s.line(700, 60 + [1000, 100, 15].index(snr) * 34, 730, 60 + [1000, 100, 15].index(snr) * 34, color, 3)
    s.text(738, 65 + [1000, 100, 15].index(snr) * 34, lab.split(' → ')[0], 'small')
    s.text(738, 82 + [1000, 100, 15].index(snr) * 34, '→ ' + lab.split(' → ')[1], 'small')
s.dot(ax.px(3), ax.py(12), 5, FBI)
s.text(700, 200, 'Worked example:', 'bold'); s.text(700, 222, '3 kHz · S/N = 15 → 12 kbit/s', 'small')
s.text(440, 282, 'Linear in bandwidth: doubling B doubles C — at fixed signal-to-noise ratio', 'small', 'middle')
s.save()

# --- Guessing game: yes/no questions locate one of 26 letters ----------------
s = SVG(DECK, 'guessing-tree', 220, 'Binary questions locating one of 26 letters',
        'A decision tree of yes-or-no questions halves the candidate set each time: 26, 13, 7, 4, 2, 1. '
        'Five questions always suffice. The best separate-letter tree averages 4.769 questions; '
        'the information is log base 2 of 26 equals 4.700 bits, approached by long-block coding.')
counts = [26, 13, 7, 4, 2, 1]
labels = ['A–Z', 'A–M ?', 'A–G ?', 'A–D ?', 'A–B ?', 'A ?']
for i, (n, lab) in enumerate(zip(counts, labels)):
    x = 8 + i * 148
    s.box(x, 30, 124, 60, f'{n} letter' + ('s' if n > 1 else ''), lab)
    if i < 5:
        s.line(x + 124, 60, x + 148, 60, INK, 2, arrow='ink')
        s.text(x + 136, 46, f'Q{i + 1}', 'small', 'middle')
s.text(8, 130, 'Each question halves the set: 26 → 13 → 7 → 4 → 2 → 1', 'bold')
s.text(8, 158, 'Five suffice in the worst case; an optimal separate-letter tree averages 4.769 questions', 'green')
s.text(8, 196, 'log₂ 26 = 4.700 bits of information', 'big')
s.text(872, 196, 'Information ≠ integer question count', 'small', 'end')
s.save()

# --- Binary entropy function ------------------------------------------------
s = SVG(DECK, 'binary-entropy', 275, 'Entropy of a binary source',
        'H of p equals minus p log p minus one minus p log of one minus p, plotted for p from zero to one. It is '
        'zero at both ends, where the outcome is certain, and reaches its maximum of one bit at p equals one half.')
ax = Axes(s, 80, 30, 560, 200, (0, 1), (0, 1.1), xlabel='p  (probability of "1")', ylabel='H [bit]',
          xticks=[(v, str(v)) for v in (0.25, 0.5, 0.75, 1)], yticks=[(0.5, '0.5'), (1, '1')])
h = lambda p: 0 if p <= 0 or p >= 1 else -(p * math.log2(p) + (1 - p) * math.log2(1 - p))  # noqa: E731
ax.curve(h, G, 3, n=400)
# The peak label sits above its point; the p = 0.1 label goes below-right,
# inside the curve, because the curve climbs steeply through that region.
for p, lab, dx, dy, anchor in [(0.5, 'fair coin: 1 bit', 0, -12, 'middle'), (0.1, 'p = 0.1: 0.47 bit', 12, 22, 'start'), (0.9, '', 0, 0, 'start')]:
    s.dot(ax.px(p), ax.py(h(p)), 5, D)
    if lab:
        s.text(ax.px(p) + dx, ax.py(h(p)) + dy, lab, 'small', anchor)
s.text(670, 70, 'Certain outcome', 'bold'); s.text(670, 92, 'p = 0 or 1  →  H = 0', 'small')
s.text(670, 132, 'Most uncertain', 'bold'); s.text(670, 154, 'p = 0.5  →  H = 1 bit', 'small')
s.text(670, 194, 'Uniform is the maximum:', 'bold'); s.text(670, 216, 'H ≤ log₂ N,  equal iff uniform', 'small')
s.save()

# --- Multiplexing: FDM splits the band, TDM splits the time -----------------
s = SVG(DECK, 'multiplexing', 300, 'Frequency-division and time-division multiplexing',
        'Left: frequency-division multiplexing gives three channels separate, permanent frequency bands, '
        'separated by guard bands, all transmitting at the same time. Right: time-division multiplexing gives '
        'each channel the full bandwidth in turn, in repeating time slots grouped into a frame.')
chan = [G, EKF, FBI]  # channel 1, 2, 3 — border + accent colour only, fill stays white (contrast)

# FDM panel — three frequency bands, each occupying the full width (all the time)
x0, y0, w, h = 50, 42, 340, 148
s.text(x0, 24, 'FDM · FREQUENCY-DIVISION', 'label')
band_h, band_gap = 40, 10
for i in range(3):  # i=0 lowest band (channel 1) … i=2 highest (channel 3)
    by = y0 + h - 4 - (i + 1) * band_h - i * band_gap
    bx, bw = x0 + 10, w - 20
    s.rect(bx, by, bw, band_h, PAPER, chan[i], 2)
    s.rect(bx, by, bw, 4, chan[i], 'none')  # accent bar, same language as box()
    s.text(bx + bw / 2, by + band_h / 2 + 8, f'Channel {i + 1}', 'bold', 'middle')
# Axes drawn last so their arrowheads sit on top of the band rectangles, not behind them.
s.line(x0, y0 + h, x0, y0, INK, 1.5, arrow='ink'); s.text(x0 - 6, y0 - 6, 'f', 'small', 'end')
s.line(x0, y0 + h, x0 + w, y0 + h, INK, 1.5, arrow='ink'); s.text(x0 + w + 8, y0 + h + 5, 't', 'small')
s.text(x0, y0 + h + 30, 'Every channel transmits all the time,', 'small')
s.text(x0, y0 + h + 48, 'in its own slice of bandwidth.', 'small')

# TDM panel — one full-bandwidth channel, sliced into a repeating frame of time slots
x0, y0, w, h = 490, 42, 340, 148
s.text(x0, 24, 'TDM · TIME-DIVISION', 'label')
n_slots = 9
slot_w = (w - 20) / n_slots
slot_y, slot_h = y0 + 4, h - 8
for k in range(n_slots):
    ch = k % 3
    sx = x0 + 10 + k * slot_w
    s.rect(sx, slot_y, slot_w, slot_h, PAPER, chan[ch], 2)
    s.rect(sx, slot_y, slot_w, 4, chan[ch], 'none')
    s.text(sx + slot_w / 2, slot_y + slot_h / 2 + 8, str(ch + 1), 'bold', 'middle')
# Axes drawn last so their arrowheads sit on top of the slot rectangles, not behind them.
s.line(x0, y0 + h, x0, y0, INK, 1.5, arrow='ink'); s.text(x0 - 6, y0 - 6, 'f', 'small', 'end')
s.line(x0, y0 + h, x0 + w, y0 + h, INK, 1.5, arrow='ink'); s.text(x0 + w + 8, y0 + h + 5, 't', 'small')
fx1, fx2, fy = x0 + 10, x0 + 10 + 3 * slot_w, y0 + h + 10
s.line(fx1, fy, fx2, fy, MUT, 1.5)
s.line(fx1, fy - 6, fx1, fy + 6, MUT, 1.5); s.line(fx2, fy - 6, fx2, fy + 6, MUT, 1.5)
s.text((fx1 + fx2) / 2, fy + 18, 'one frame', 'bold', 'middle')
s.text(x0, y0 + h + 48, 'Every channel gets the full bandwidth,', 'small')
s.text(x0, y0 + h + 66, 'once per frame.', 'small')

for i in range(3):  # shared legend
    lx = 300 + i * 130
    s.rect(lx, 262, 14, 14, PAPER, chan[i], 2)
    s.text(lx + 22, 273, f'Channel {i + 1}', 'small')
s.save()

# =============================================================================
# 02 — Kendall's notation and the M/M/1 queue
# =============================================================================
DECK = '02'

# --- Model of a queueing system ----------------------------------------------
s = SVG(DECK, 'queue-model', 210, 'Model of a queueing system',
        'Arrivals enter a buffer of waiting positions and are served by one or more servers before departing. '
        'The system is described by the arrival rate lambda, the service rate mu, the number of servers, the '
        'number of waiting positions, and the queueing discipline that orders waiting requests.')
# Row is vertically centred on y=100 (matches the boxes: top 68, height 64); "Arrivals" and
# "Departures" sit on that same row instead of floating above it, and all three arrows share one
# length so the chain reads as one evenly paced flow. The whole row is centred in the 880-wide
# canvas: left edge of "Arrivals" and right edge of "Departures" sit at roughly equal margins.
s.text(114, 106, 'Arrivals', 'bold', 'end')
s.line(128, 100, 188, 100, G, 2, arrow='green')
s.text(158, 90, 'λ', 'bold', 'middle')
s.box(188, 68, 230, 64, 'Waiting positions', 'buffer capacity D', TINT)
s.line(418, 100, 478, 100, INK, 2, arrow='ink')
s.box(478, 68, 200, 64, 'Server(s)', 'n channels, rate μ each', TINT)
s.line(678, 100, 738, 100, INK, 2, arrow='ink')
s.text(752, 106, 'Departures', 'bold')
s.text(440, 160, 'Queueing discipline orders the waiting positions: FIFO/FCFS, LIFO/LCFS, SIRO, priority, …', 'small', 'middle')
s.text(440, 190, 'Kendall notation A/B/C/D/E/F packages all of these choices into one string.', 'small', 'middle')
s.save()

# --- A realization of a Poisson arrival process ------------------------------
s = SVG(DECK, 'poisson-process', 230, 'A realization of a Poisson arrival process',
        'A realization of a Poisson arrival process on a time axis: dots mark arrival instants; the gaps between '
        'consecutive arrivals, T1, T2, T3, are the inter-arrival times. Each gap is drawn independently from an '
        'exponential distribution with the same rate; this description is what drives the simulation.')
s.text(40, 24, 'ARRIVALS ON THE TIME AXIS', 'label')
s.line(60, 110, 820, 110, INK, 1.5, arrow='ink')
s.text(832, 116, 't', 'small')
# Hand-picked gaps illustrate irregular, independent spacing (including a burst) while
# keeping the first three inter-arrival intervals wide enough to label without crowding.
gaps = [1.1, 0.8, 1.0, 0.3, 0.2, 0.6, 1.5, 0.4, 0.7, 0.9]
arrivals = [sum(gaps[:i + 1]) for i in range(len(gaps))]
X = lambda tt: 60 + tt / 7.6 * 740  # noqa: E731
for a in arrivals:
    s.line(X(a), 96, X(a), 110, G, 2.5)
    s.dot(X(a), 96, 4.5, G)
bounds = [0.0] + arrivals
for i in range(3):
    x1, x2, y = X(bounds[i]), X(bounds[i + 1]), 142
    s.line(x1, y, x2, y, MUT, 1.5)
    s.line(x1, y - 6, x1, y + 6, MUT, 1.5)
    s.line(x2, y - 6, x2, y + 6, MUT, 1.5)
    s.text((x1 + x2) / 2, y + 22, f'T{i + 1}', 'bold', 'middle')
s.text(440, 200, 'Inter-arrival times T₁, T₂, … are i.i.d. Exponential(λ) — the description used in simulation.', 'small', 'middle')
s.text(440, 222, 'Equivalently: the number of arrivals in any interval of length t is Poisson with mean λt.', 'small', 'middle')
s.save()

# --- Exponential probability density -----------------------------------------
s = SVG(DECK, 'exponential-pdf', 270, 'Probability density of the exponential distribution',
        'Probability density of the exponential distribution for two rates: lambda equals 2 has a short mean '
        'wait of 0.5 seconds; lambda equals 0.5 has a longer mean wait of 2 seconds. Both curves peak at x '
        'equals zero and decay monotonically. The distribution is memoryless.')
ax = Axes(s, 70, 36, 560, 190, (0, 6), (0, 2.1), xlabel='x  (waiting time) [s]', ylabel='f(x)',
          xticks=[(v, str(v)) for v in (1, 2, 3, 4, 5, 6)], yticks=[(1, '1'), (2, '2')])
epdf = lambda lam: (lambda x: lam * math.exp(-lam * x))  # noqa: E731
ax.curve(epdf(2.0), G, 3, n=300)
ax.curve(epdf(0.5), EKF, 2.5, n=300)
s.line(660, 70, 700, 70, G, 3); s.text(708, 75, 'λ = 2  (mean 1/λ = 0.5 s)')
s.line(660, 105, 700, 105, EKF, 2.5); s.text(708, 110, 'λ = 0.5  (mean 1/λ = 2 s)')
s.text(660, 160, 'Mean E(T) = 1/λ', 'small')
s.text(660, 185, 'Variance D(T) = 1/λ²', 'small')
s.text(660, 210, 'Memoryless:', 'small')
s.text(660, 230, 'P(T>s+t | T>s) = P(T>t)', 'small')
s.save()

# --- M/M/1 birth-death diagram ------------------------------------------------
s = SVG(DECK, 'mm1-birth-death', 210, 'Birth-death diagram of the M/M/1 queue',
        'Birth-death diagram of the M/M/1 queue: states are the number of customers in the system. Arrivals at '
        'rate lambda move the state up by one; service completions at rate mu move it down by one. Steady state '
        'requires rho equals lambda over mu, less than one.')
states = ['0', '1', '2', '3', '…']
x0, bw, bh, gap, y = 105, 70, 70, 150, 60  # x0 centres the chain in the 880-wide canvas
for i, st in enumerate(states):
    x = x0 + i * gap
    s.rect(x, y, bw, bh, TINT, G, 2)
    s.text(x + bw / 2, y + bh / 2 + 8, st, 'big', 'middle')
    if i < len(states) - 1:
        # The last transition leads into the literal "…" box, not a numbered state — draw it
        # dashed so it reads as "the chain continues", not as one more concrete step.
        last = i == len(states) - 2
        s.line(x + bw, y + bh * 0.35, x + gap, y + bh * 0.35, G, 2.5, dash=last, arrow='green')
        s.text(x + bw + (gap - bw) / 2, y + bh * 0.35 - 10, 'λ', 'bold', 'middle')
        s.line(x + gap, y + bh * 0.75, x + bw, y + bh * 0.75, MUT, 2.5, dash=last, arrow='muted')
        s.text(x + bw + (gap - bw) / 2, y + bh * 0.75 + 24, 'μ', 'bold', 'middle')
s.text(440, 190, 'State = number of customers in the system. Arrivals (λ) push it up; services (μ) pull it down.', 'small', 'middle')
s.save()

# --- Little's law: delay decomposition ---------------------------------------
s = SVG(DECK, 'littles-law', 230, "Delay decomposition in a queueing system",
        'Delay decomposition in a queueing system: an arriving request waits Wq in the queue, then receives one '
        'over mu of service; the total time in the system is W, the sum of the two. Occupancy L counts requests '
        'in service and waiting; Lq counts only those waiting.')
# x0 and the arrival arrow's start are both shifted right by the same amount from the original
# layout so the whole diagram (arrow to arrow) sits centred in the 880-wide canvas.
x0 = 206
s.line(126, 100, x0, 100, G, 2, arrow='green')
s.text(126, 85, 'λ', 'bold')
s.box(x0, 68, 220, 64, 'Queue', 'waiting, Lq', NEUTRAL)
s.box(x0 + 220, 68, 180, 64, 'Server', 'in service, rate μ', TINT)
s.line(x0 + 400, 100, x0 + 450, 100, INK, 2, arrow='ink')
s.text(x0 + 458, 105, 'Departures', 'bold')


def bracket(x1, x2, y, label):
    s.line(x1, y, x2, y, MUT, 1.5)
    s.line(x1, y - 6, x1, y + 6, MUT, 1.5)
    s.line(x2, y - 6, x2, y + 6, MUT, 1.5)
    s.text((x1 + x2) / 2, y + 22, label, 'bold', 'middle')


bracket(x0, x0 + 220, 155, 'Wq — queueing delay')
bracket(x0, x0 + 400, 195, 'W — total time in system')
s.text(440, 40, 'L (system occupancy) = Lq (queue occupancy) + ρ (the fraction in service)', 'small', 'middle')
s.save()


# =============================================================================
# 03 — QoS mechanisms: from packet handling to perceived quality
# =============================================================================
DECK = '03'

# --- QoS as one input to QoE --------------------------------------------------
s = SVG(DECK, 'qoe-qos-scope', 330, 'Quality of Service as one input to Quality of Experience',
        'Three stacked layers. At the bottom, the network layer provides Quality of Service: throughput, '
        'delay, jitter, and packet loss. An arrow leads up to the middle layer, the application and content, '
        'covering codec choice, encoding, and adaptive bitrate. A second arrow leads up to the top layer, the '
        'user, whose Quality of Experience depends on perception, expectations, context, and satisfaction.')
bx, bw = 160, 560
s.box(bx, 195, bw, 65, 'Network — Quality of Service (QoS)', 'throughput · delay · jitter · packet loss', TINT)
s.line(440, 195, 440, 163, G, 2, arrow='green')
s.text(452, 183, 'is encoded into', 'small')
s.box(bx, 100, bw, 65, 'Application / content', 'codec choice, encoding, adaptive bitrate', TINT)
s.line(440, 100, 440, 68, G, 2, arrow='green')
s.text(452, 88, 'is perceived by the user as', 'small')
s.box(bx, 5, bw, 65, 'User — Quality of Experience (QoE)', 'perception, expectations, context, satisfaction', TINT)
s.text(440, 295, 'QoS parameters are necessary inputs to QoE, but they are not sufficient on their own —', 'small', 'middle')
s.text(440, 313, 'expectations and context shape how the same measured QoS is experienced.', 'small', 'middle')
s.save()

# --- End-to-end one-way delay budget ------------------------------------------
s = SVG(DECK, 'delay-budget', 275, 'A one-way delay budget, fixed and variable components',
        'A horizontal timeline of six delay components that add up along a path: codec, serialization, and '
        'propagation delay are fixed by the codec and the link; queuing, forwarding, and shaping delay are '
        'variable and grow under load. ITU-T G.114 recommends keeping total one-way delay below about 150 '
        'milliseconds for good conversational quality.')
# Legend as one centered row (not a right-side float) so the bar itself can be centered below it.
s.rect(207, 12, 18, 18, TINT, G, 2)
s.text(233, 26, 'Fixed — codec & link', 'small')
s.rect(430, 12, 18, 18, CTINT, C, 2)
s.text(456, 26, 'Variable — traffic-dependent', 'small')
segments = [('Codec', 55, True), ('Serialization', 45, True), ('Propagation', 100, True),
            ('Queuing', 140, False), ('Forwarding', 35, False), ('Shaping', 85, False)]
total_w = sum(w for _, w, _ in segments)
cursor, bar_y, bar_h = (880 - total_w) // 2, 110, 60  # centre the bar itself in the 880-wide canvas
for i, (name, w, fixed) in enumerate(segments):
    fill, stroke = (TINT, G) if fixed else (CTINT, C)
    s.rect(cursor, bar_y, w, bar_h, fill, stroke, 2)
    mid = cursor + w / 2
    if i % 2 == 0:  # alternate labels above/below so narrow segments still get room for a leader line
        s.line(mid, bar_y, mid, bar_y - 22, MUT, 1.5)
        s.text(mid, bar_y - 32, name, 'small bold', 'middle')
    else:
        s.line(mid, bar_y + bar_h, mid, bar_y + bar_h + 22, MUT, 1.5)
        s.text(mid, bar_y + bar_h + 38, name, 'small bold', 'middle')
    cursor += w
s.text(440, 230, 'Fixed components are set once the codec and link are chosen; variable components grow under load.', 'small', 'middle')
s.text(440, 248, 'ITU-T G.114 recommends keeping total one-way delay below about 150 ms for good conversational quality.', 'small', 'middle')
s.save()

# --- Weighted scheduling across two queues ------------------------------------
s = SVG(DECK, 'weighted-queues', 260, 'Weighted scheduling across two output queues',
        'Packets arriving at router R1 are split between two output queues before leaving on one link. Queue '
        '1 is scheduled to use 25 percent of the link capacity, queue 2 the remaining 75 percent — '
        'proportional scheduling, not strict priority, so queue 1 is never starved.')
# +102 x-offset centres the whole assembly (Arrivals label to R2 box) in the 880-wide canvas.
s.text(402, 28, 'R1 — OUTPUT SCHEDULER', 'label', 'middle')
s.text(216, 130, 'Arrivals', 'bold', 'end')
s.line(230, 125, 252, 125, G, 2, arrow='green')
s.rect(252, 40, 300, 170, PAPER, INK, 1.5)
s.rect(277, 68, 62, 30, G, 'none')
s.rect(339, 68, 188, 30, EKF, 'none')
s.text(308, 58, '25%', 'bold', 'middle')
s.text(433, 58, '75%', 'bold', 'middle')
s.rect(277, 110, 16, 16, G, 'none')
s.text(301, 123, 'Queue 1 — priority traffic')
s.rect(277, 145, 16, 16, EKF, 'none')
s.text(301, 158, 'Queue 2 — best-effort traffic')
s.line(552, 125, 642, 125, INK, 2, arrow='ink')
s.rect(642, 95, 90, 60, TINT, G, 2)
s.text(687, 130, 'R2', 'big', 'middle')
s.text(440, 235, 'The scheduler serves queue 2 three times as often as queue 1 (75:25) — proportional sharing,', 'small', 'middle')
s.text(440, 253, 'not strict priority, so queue 1 is never starved of bandwidth.', 'small', 'middle')
s.save()

# --- Token bucket traffic enforcement -----------------------------------------
s = SVG(DECK, 'token-bucket', 300, 'The token bucket enforces a rate and a burst limit',
        'Tokens accumulate in a bucket at rate r, up to a maximum depth b. A packet needs one token per byte '
        'to be sent. If the bucket holds enough tokens the packet is sent immediately and the tokens are '
        'removed; otherwise it must wait for tokens to accumulate, or be dropped or marked as non-conformant.')
s.text(114, 148, 'Arrivals', 'bold', 'end')
s.line(128, 135, 160, 135, G, 2, arrow='green')
s.rect(160, 30, 240, 210, PAPER, INK, 1.5)
s.text(280, 20, 'TOKEN BUCKET', 'label', 'middle')
s.rect(185, 70, 90, 140, PAPER, INK, 1.5)
token_cols = [192, 228]
token_rows = [185, 163, 141, 119]
for ri, ty in enumerate(token_rows):
    fill = TINT if ri < 3 else PAPER
    stroke = G if ri < 3 else LINE
    for tx in token_cols:
        s.rect(tx, ty, 18, 18, fill, stroke, 1.5)
s.line(230, 30, 230, 70, G, 2, arrow='green')
s.text(238, 50, 'rate r', 'small')
s.line(295, 70, 305, 70, MUT, 1.5)
s.line(295, 210, 305, 210, MUT, 1.5)
s.line(300, 70, 300, 210, MUT, 1.5)
s.text(312, 135, 'depth b', 'bold')
s.text(312, 153, 'capacity', 'small')
s.line(400, 85, 470, 85, INK, 2, arrow='ink')
s.line(400, 175, 470, 175, INK, 2, arrow='ink')
s.rect(470, 50, 330, 70, TINT, G, 2)
s.text(485, 80, 'Enough tokens', 'bold')
s.text(485, 102, 'packet sent immediately, tokens removed', 'small')
s.rect(470, 140, 330, 70, CTINT, C, 2)
s.text(485, 170, 'Not enough tokens', 'bold')
s.text(485, 192, 'wait (shaping) or drop/mark (policing)', 'small')
s.text(440, 260, 'Traffic entering any interval of length T is bounded by b + rT: bursts up to b tokens pass', 'small', 'middle')
s.text(440, 278, 'immediately, but the long-run rate never exceeds r.', 'small', 'middle')
s.save()

# --- RED drop-probability profile ----------------------------------------------
s = SVG(DECK, 'red-drop-profile', 285, 'Random Early Detection drop-probability profile',
        'Drop probability as a function of average queue depth. Below the minimum threshold no packets are '
        'dropped. Between the minimum and maximum thresholds, drop probability rises linearly to a maximum '
        'value. At or above the maximum threshold every arriving packet is dropped, a tail drop.')
min_th, max_th, max_p = 30, 70, 0.1
red_prob = lambda x: 0.0 if x <= min_th else (max_p * (x - min_th) / (max_th - min_th) if x < max_th else 1.0)  # noqa: E731
ax = Axes(s, 90, 30, 560, 150, (0, 100), (0, 1.05), xlabel='Average queue depth [packets]', ylabel='Drop probability',
          xticks=[(min_th, 'min_th'), (max_th, 'max_th'), (100, '100')], yticks=[(max_p, 'max_p'), (1, '1.0')])
ax.curve(red_prob, G, 3, n=400)
s.text(660, 75, 'Below min_th:', 'small')
s.text(660, 95, 'no drops', 'small')
s.text(660, 125, 'min_th–max_th:', 'small')
s.text(660, 145, 'random early drops', 'small')
s.text(660, 175, '≥ max_th: tail drop', 'small')
s.text(440, 250, 'Early, random drops signal congestion before the buffer fills. A TCP sender backs off in', 'small', 'middle')
s.text(440, 268, 'response; a UDP/RTP voice stream does not — it keeps sending at the same rate regardless.', 'small', 'middle')
s.save()

# --- Link fragmentation and interleaving --------------------------------------
s = SVG(DECK, 'lfi-fragmentation', 300, 'Link fragmentation and interleaving reduces serialization wait',
        'Without link fragmentation and interleaving, a small delay-sensitive packet must wait behind an '
        'entire large packet already being sent. With fragmentation and interleaving, the large packet is '
        'split into fragments and the small packet is inserted after just the first fragment, cutting its '
        'wait roughly to a third.')


def timeline_block(x, y, w, h, fill, stroke, line1, line2=''):
    s.rect(x, y, w, h, fill, stroke, 2)
    if line2:
        s.text(x + w / 2, y + h / 2 - 2, line1, 'bold', 'middle')
        s.text(x + w / 2, y + h / 2 + 18, line2, 'small', 'middle')
    else:
        s.text(x + w / 2, y + h / 2 + 6, line1, 'bold', 'middle')
    return x + w


def span_bracket(x1, x2, y, label):
    s.line(x1, y, x2, y, MUT, 1.5)
    s.line(x1, y - 6, x1, y + 6, MUT, 1.5)
    s.line(x2, y - 6, x2, y + 6, MUT, 1.5)
    s.text((x1 + x2) / 2, y + 22, label, 'small', 'middle')


# +105 x-offset centres the assembly (both rows run narrower than the 880-wide canvas otherwise).
ox = 105
s.text(80 + ox, 25, 'WITHOUT LFI', 'label')
cursor = timeline_block(80 + ox, 45, 320, 55, TINT, G, 'Large packet', '1500 B')
cursor = timeline_block(cursor, 45, 100, 55, CTINT, C, 'Small', '200 B')
s.line(cursor + 10, 72, cursor + 50, 72, INK, 2, arrow='ink')
s.text(cursor + 58, 77, 'link', 'small')
span_bracket(80 + ox, 400 + ox, 120, 'the urgent packet waits for the whole 1500 B packet')

s.text(80 + ox, 165, 'WITH LFI (FRAGMENTATION + INTERLEAVING)', 'label')
cursor = timeline_block(80 + ox, 185, 100, 55, TINT, G, 'F1')
cursor = timeline_block(cursor, 185, 100, 55, CTINT, C, 'Small', '200 B')
cursor = timeline_block(cursor, 185, 100, 55, TINT, G, 'F2')
cursor = timeline_block(cursor, 185, 100, 55, TINT, G, 'F3')
s.line(cursor + 10, 212, cursor + 50, 212, INK, 2, arrow='ink')
s.text(cursor + 58, 217, 'link', 'small')
span_bracket(80 + ox, 280 + ox, 260, 'the urgent packet follows just one fragment')
s.save()

# --- IP Precedence and DSCP marking -------------------------------------------
s = SVG(DECK, 'dscp-header', 320, 'From IP Precedence to the Differentiated Services field',
        'Two 8-bit fields of the IP header. The pre-DiffServ Type of Service byte splits into 3 bits of IP '
        'Precedence, 4 ToS bits, and 1 unused bit. The Differentiated Services field defined by RFC 2474 '
        'reuses the same byte as 6 bits of Differentiated Services Code Point, DSCP, plus 2 bits for '
        'Explicit Congestion Notification. Class-selector codepoints keep the same ordering as IP Precedence.')


def cell_row(x0, y, groups):
    x = x0
    for w, fill in groups:
        s.rect(x, y, w, 50, fill, LINE, 1.5)
        x += w
    return x


def span_above(x1, x2, y, label):
    s.line(x1, y, x2, y, MUT, 1.5)
    s.line(x1, y, x1, y - 8, MUT, 1.5)
    s.line(x2, y, x2, y - 8, MUT, 1.5)
    s.text((x1 + x2) / 2, y - 14, label, 'bold', 'middle')


x0, cw = 240, 50
s.text(x0, 25, 'TOS BYTE — PRE-DIFFSERV (RFC 791/1349)', 'label')
cell_row(x0, 60, [(3 * cw, TINT), (4 * cw, NEUTRAL2), (cw, PAPER)])
span_above(x0, x0 + 3 * cw, 60, 'IP Precedence (3 bits)')
span_above(x0 + 3 * cw, x0 + 7 * cw, 60, 'ToS bits (4 bits)')
span_above(x0 + 7 * cw, x0 + 8 * cw, 60, 'Unused')

s.text(440, 145, 'Same 8 bits, reinterpreted:', 'small', 'middle')

s.text(x0, 185, 'DS FIELD — DIFFSERV (RFC 2474)', 'label')
cell_row(x0, 220, [(6 * cw, TINT), (2 * cw, NEUTRAL2)])
span_above(x0, x0 + 6 * cw, 220, 'DSCP (6 bits)')
span_above(x0 + 6 * cw, x0 + 8 * cw, 220, 'ECN (2 bits)')

s.text(440, 290, 'Class-selector codepoints (000xxx) preserve IP Precedence’s ordering; DSCP adds finer-grained', 'small', 'middle')
s.text(440, 308, 'per-hop behaviors: EF = 101110 (voice, RFC 3246) · AF41 = 100010 (video, RFC 2597) · default = 000000.', 'small', 'middle')
s.save()

# =============================================================================
# 04 — Network traffic modelling: distributions and self-similarity
# =============================================================================
# The Markov loss-model state diagrams for this deck (Bernoulli, Simple Gilbert, Gilbert,
# Gilbert-Elliott, four-state) are NOT generated here: they are drawn on the slides by the Vue components
# GilbertSim (diagram mode) and FourStateDiagram, so they match the live loss simulations.
DECK = '04'

# --- Exponential distribution: density and cumulative distribution -----------
s = SVG(DECK, 'exp-pdf-cdf', 270, 'Exponential distribution: density and cumulative distribution',
        'Probability density and cumulative distribution of the exponential distribution with rate 1. The '
        'density starts at 1 and decays monotonically; the cumulative distribution rises from 0 towards 1. '
        'This distribution models Poisson-process inter-arrival times.')
ax = Axes(s, 70, 30, 560, 200, (0, 5), (0, 1.05), xlabel='x', ylabel='f(x), F(x)',
          xticks=[(v, str(v)) for v in (0, 1, 2, 3, 4, 5)], yticks=[(0, '0'), (0.5, '0.5'), (1, '1.0')])
ax.curve(lambda x: math.exp(-x), G, 3, n=300)
ax.curve(lambda x: 1 - math.exp(-x), EKF, 2.5, n=300)
s.line(660, 60, 700, 60, G, 3); s.text(708, 65, 'pdf  f(x) = λe⁻λˣ')
s.line(660, 95, 700, 95, EKF, 2.5); s.text(708, 100, 'cdf  F(x) = 1 − e⁻λˣ')
s.text(660, 150, 'Models packet/call/session', 'small')
s.text(660, 170, 'inter-arrivals of a Poisson', 'small')
s.text(660, 190, 'process — Lecture 02.', 'small')
s.text(660, 222, 'Memoryless: most inter-', 'small')
s.text(660, 242, 'arrivals are short; the tail', 'small')
s.text(660, 262, 'relates to packet drop.', 'small')
s.save()

# --- Weibull distribution: shape family ---------------------------------------
s = SVG(DECK, 'weibull-pdf', 270, 'Weibull probability density for five shape parameters',
        'Probability density of the Weibull distribution with scale 1 and shape k from 1 to 5. Larger k '
        'concentrates the density more tightly around x = 1, moving away from the exponential shape at k = 1 '
        'towards an increasingly peaked, near-symmetric one.')
ax = Axes(s, 70, 30, 560, 200, (0, 3), (0, 2.0), xlabel='x', ylabel='f(x)',
          xticks=[(v, str(v)) for v in (0, 1, 2, 3)], yticks=[(0, '0'), (1, '1'), (2, '2')])
wpdf = lambda k: (lambda x: 0.0 if x < 0 else k * x ** (k - 1) * math.exp(-x ** k))  # noqa: E731
for k, col in zip(range(1, 6), (G, D, EKF, FBI, C)):
    ax.curve(wpdf(k), col, 2.5, n=300)
    s.line(660, 46 + (k - 1) * 30, 700, 46 + (k - 1) * 30, col, 2.5)
    s.text(708, 51 + (k - 1) * 30, f'k = {k}' + ('  (exponential)' if k == 1 else ''), 'small')
s.text(660, 220, 'k = 1 is the exponential;', 'small')
s.text(660, 240, 'better fit for access→core', 'small')
s.text(660, 260, 'and packet→session scaling [1]', 'small')
s.save()

# --- Normal distribution: jitter -----------------------------------------------
s = SVG(DECK, 'normal-jitter', 270, 'Normal distribution: density and cumulative distribution of jitter',
        'Probability density and cumulative distribution of a zero-mean, unit-variance Normal distribution, '
        'used to model packet delay variation, jitter, within one flow. The density is symmetric and '
        'bell-shaped; the cumulative distribution is its S-shaped integral.')
ax = Axes(s, 70, 30, 560, 200, (-5, 5), (0, 1.05), xlabel='x  (jitter)', ylabel='f(x), F(x)',
          xticks=[(v, str(v)) for v in (-4, -2, 0, 2, 4)], yticks=[(0, '0'), (0.5, '0.5'), (1, '1.0')])
npdf = lambda x: math.exp(-x * x / 2) / math.sqrt(2 * math.pi)  # noqa: E731
ncdf = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))  # noqa: E731
ax.curve(npdf, G, 3, n=300)
ax.curve(ncdf, EKF, 2.5, n=300)
s.line(660, 60, 700, 60, G, 3); s.text(708, 65, 'pdf f(x)')
s.line(660, 95, 700, 95, EKF, 2.5); s.text(708, 100, 'cdf F(x)')
s.text(660, 150, 'Models delay variation', 'small')
s.text(660, 170, '(jitter) between', 'small')
s.text(660, 190, 'consecutive packets of', 'small')
s.text(660, 210, 'the same flow.', 'small')
s.save()

# --- Simple Gilbert model: convergence to steady state --------------------------
s = SVG(DECK, 'gilbert-convergence', 330, 'Simple Gilbert model: convergence to steady state',
        'Two panels show the empirical probability of the Transmit and Loss states over time, averaged over '
        'many independent realizations of a simple Gilbert chain with p = 0.8 and q = 0.4, starting in '
        'Transmit (left) and in Loss (right). Both converge to the same steady-state probabilities.')
p, q = 0.8, 0.4
piL, piT = p / (p + q), q / (p + q)
N, M = 160, 600
rng = random.Random(7)


def simulate(start_loss):
    counts = [0] * (N + 1)
    for _ in range(M):
        st = start_loss
        counts[0] += st
        for t in range(1, N + 1):
            st = (rng.random() >= q) if st else (rng.random() < p)
            counts[t] += st
    return [c / M for c in counts]


for x0, start_loss, title in [(70, False, 'STARTING IN T'), (500, True, 'STARTING IN L')]:
    s.text(x0, 16, title, 'label')
    PL = simulate(start_loss)
    ax = Axes(s, x0, 46, 330, 170, (0, N), (0, 1.05), xlabel='step',
              xticks=[(v, str(v)) for v in (0, 40, 80, 120, 160)], yticks=[(0, '0'), (piT, '0.333'), (piL, '0.667'), (1, '1.0')])
    s.polyline([(ax.px(t), ax.py(1 - PL[t])) for t in range(N + 1)], G, 2)
    s.polyline([(ax.px(t), ax.py(PL[t])) for t in range(N + 1)], FMT, 2)
s.line(310, 288, 340, 288, G, 2.5); s.text(348, 293, 'P(T)', 'small')
s.line(430, 288, 460, 288, FMT, 2.5); s.text(468, 293, 'P(L)', 'small')
s.text(440, 318, 'p = 0.8, q = 0.4 — every realization converges to the same steady state, independent of the start.', 'small', 'middle')
s.save()

# --- Self-similar synthetic traffic at four aggregation levels ------------------
s = SVG(DECK, 'self-similar-traffic', 320, 'Synthetic traffic at four levels of aggregation',
        'A synthetic trace built from the superposition of many ON/OFF sources with heavy-tailed, Pareto '
        'distributed period lengths, zoomed from 1 fine time bin per bar up to the whole trace aggregated into '
        'about 328 bins per bar. Unlike a Poisson process, which flattens toward a smooth average as bins are '
        'aggregated, this trace stays visibly bursty at every scale.')
NFINE, NSRC, ALPHA, SCALE = 65536, 40, 1.4, 4
rng = random.Random(11)


def onoff_source():
    trace = [0] * NFINE
    t, on = 0, rng.random() < 0.5
    while t < NFINE:
        dur = max(1, int(SCALE * rng.paretovariate(ALPHA)))
        if on:
            for i in range(t, min(NFINE, t + dur)):
                trace[i] = 1
        t += dur
        on = not on
    return trace


agg = [0] * NFINE
for _ in range(NSRC):
    src = onoff_source()
    for i in range(NFINE):
        agg[i] += src[i]


def bar_panel(x0, y0, w, h, vals, color, title):
    s.text(x0, y0 - 10, title, 'label')
    n = len(vals)
    bw = w / n
    vmax = max(vals) or 1
    for i, v in enumerate(vals):
        bh = v / vmax * h
        s.rect(x0 + i * bw, y0 + h - bh, max(bw - 0.3, 0.4), bh, color, 'none')
    s.line(x0, y0 + h, x0 + w, y0 + h, INK, 1)


BARS = 200  # cap per panel — the whole-trace panel would otherwise draw 65536 individual rects
factors = [1, 8, 64, NFINE // BARS]
titles = ['FINE — 1 bin/bar', '×8 aggregation', '×64 aggregation', f'×{factors[3]} aggregation (whole trace)']
colors = [G, D, EKF, FBI]
for i, (factor, title) in enumerate(zip(factors, titles)):
    n_bars = min(BARS, NFINE // factor)  # panels 1-3 zoom into the trace's first n_bars*factor bins
    vals = [sum(agg[b * factor:(b + 1) * factor]) / factor for b in range(n_bars)]
    col, row = i % 2, i // 2
    bar_panel(60 + col * 440, 48 + row * 130, 380, 90, vals, colors[i], title)
s.text(440, 300, 'A Poisson-based model would flatten towards a smooth average as aggregation grows — this one does not.', 'small', 'middle')
s.save()

# --- Extras: Pareto tail vs exponential tail (log–log CCDF) -------------------
# Same mean period (12 slots) as the deck's live ON/OFF animations. Axes are in log10 units, because
# Axes maps linearly; on log–log axes a Pareto tail is a straight line of slope −α.
PARETO_MEAN = 12
s = SVG(DECK, 'pareto-ccdf', 250, 'Pareto versus exponential tails',
        'Complementary cumulative distribution P(X > x) on log-log axes for Pareto periods with shape alpha '
        '1.2, 1.5 and 1.9 and for an exponential period, all with mean 12 slots. Each Pareto tail is a straight '
        'line of slope minus alpha; the exponential tail falls away steeply, so very long periods are practically '
        'impossible for it but routine for the Pareto distribution.')
ax = Axes(s, 80, 16, 500, 190, (0, 4), (-6, 0.2), xlabel='period length x [slots]', ylabel='P(X > x)',
          xticks=[(0, '1'), (1, '10'), (2, '100'), (3, '1 000'), (4, '10 000')],
          yticks=[(0, '1'), (-2, '10⁻²'), (-4, '10⁻⁴'), (-6, '10⁻⁶')])
for alpha, color in ((1.2, G), (1.5, EKF), (1.9, FBI)):
    xm = PARETO_MEAN * (alpha - 1) / alpha
    top = min(4, math.log10(xm) + 6 / alpha)  # where the tail leaves the plot at 10⁻⁶
    ax.curve(lambda lx, a=alpha, m=xm: 0 if 10 ** lx < m else a * (math.log10(m) - lx), color, 3, n=300, xr=(0, top))
ax.curve(lambda lx: -(10 ** lx) / PARETO_MEAN / math.log(10), MUT, 2.5, n=300, dash=True,
         xr=(0, math.log10(6 * math.log(10) * PARETO_MEAN)))
for i, (label, color, dash) in enumerate((('Pareto α = 1.2 (H = 0.90)', G, False), ('Pareto α = 1.5 (H = 0.75)', EKF, False),
                                          ('Pareto α = 1.9 (H = 0.55)', FBI, False), ('exponential', MUT, True))):
    s.line(620, 34 + i * 30, 660, 34 + i * 30, color, 3, dash)
    s.text(668, 39 + i * 30, label, 'small')
s.text(620, 170, 'all four: mean period 12 slots', 'small')
s.text(620, 192, 'Pareto: straight line, slope −α', 'small')
s.text(620, 214, 'exponential: below 10⁻⁶ by ~170 slots', 'small')
s.save()

# =============================================================================
# 05 — Speech quality measurement: MOS, intrusive models and the E-model
# =============================================================================
DECK = '05'

# --- P.800 rating scales -----------------------------------------------------
s = SVG(DECK, 'rating-scales', 330, 'The three ITU-T P.800 listening-test rating scales',
        'Absolute Category Rating asks for the quality of one sample on a five-point scale from Excellent (5) to '
        'Bad (1). Degradation Category Rating plays the reference first and asks how annoying the degradation is, '
        'from inaudible (5) to very annoying (1). Comparison Category Rating compares two samples on a seven-point '
        'scale from much better (+3) to much worse (−3).')
scales = [
    ('ACR → MOS', 'one sample, no reference',
     [('5', 'Excellent'), ('4', 'Good'), ('3', 'Fair'), ('2', 'Poor'), ('1', 'Bad')]),
    ('DCR → DMOS', 'reference first, then degraded',
     [('5', 'Inaudible'), ('4', 'Audible, not annoying'), ('3', 'Slightly annoying'), ('2', 'Annoying'),
      ('1', 'Very annoying')]),
    ('CCR → CMOS', 'pair in random order',
     [('+3', 'Much better'), ('+2', 'Better'), ('+1', 'Slightly better'), ('0', 'About the same'),
      ('−1', 'Slightly worse'), ('−2', 'Worse'), ('−3', 'Much worse')]),
]
for i, (title, sub, rows) in enumerate(scales):
    x0 = 20 + i * 290
    s.text(x0, 20, title, 'label')
    s.text(x0, 42, sub, 'small')
    for k, (score, lab) in enumerate(rows):
        y = 56 + k * 36
        s.rect(x0, y, 260, 32, TINT if k % 2 == 0 else PAPER, LINE)
        s.rect(x0, y, 44, 32, PAPER, G, 1.5)
        s.text(x0 + 22, y + 22, score, 'bold green', 'middle')
        s.text(x0 + 56, y + 22, lab)
s.text(440, 322, 'MOS = arithmetic mean of all listeners’ scores for one condition · always report it with its confidence interval',
       'small', 'middle')
s.save()

# --- Three families of objective models --------------------------------------
s = SVG(DECK, 'model-families', 300, 'Intrusive, non-intrusive and parametric speech quality models',
        'A reference speech signal passes through the system under test, a codec and a network, and comes out as '
        'degraded speech. An intrusive model compares the reference with the degraded signal. A non-intrusive '
        'signal-based model listens to the degraded signal only. A parametric model uses no audio at all, only '
        'network and terminal parameters such as delay, loss and codec type.')
s.box(20, 30, 200, 60, 'Reference speech', 'clean, known in advance', NEUTRAL)
s.line(220, 60, 330, 60, INK, 2, arrow='ink')
s.box(330, 30, 220, 60, 'System under test', 'codec · network · terminal')
s.line(550, 60, 660, 60, INK, 2, arrow='ink')
s.box(660, 30, 200, 60, 'Degraded speech', 'what the listener hears', NEUTRAL)
# Reference drops straight into the intrusive model; the degraded signal runs along one bus at
# y = 130 to both signal-based models, so no two connectors cross.
s.line(90, 90, 90, 190, G, 2, arrow='green')
s.path('M760,90 L760,130 L230,130', G, 2)
s.line(230, 130, 230, 190, G, 2, arrow='green')
s.line(440, 130, 440, 190, G, 2, arrow='green')
s.box(20, 190, 270, 64, 'Intrusive · full reference', 'PESQ P.862 · POLQA P.863 · ViSQOL')
s.box(305, 190, 270, 64, 'Non-intrusive · signal', 'P.563 · DNSMOS (degraded only)')
s.box(590, 190, 270, 64, 'Parametric · no audio', 'E-model G.107 · RTCP probes', PAPER)
s.text(725, 152, 'delay, loss, codec, echo …', 'small', 'middle')
s.line(725, 158, 725, 190, MUT, 2, dash=True, arrow='muted')
s.text(440, 290, 'More information in → more accurate, but harder to deploy: a reference signal exists only in a test call.',
       'small', 'middle')
s.save()

# --- PESQ processing chain ---------------------------------------------------
s = SVG(DECK, 'pesq-pipeline', 265, 'Processing chain of the PESQ model',
        'Both reference and degraded signals are level-aligned and filtered like a telephone handset, then '
        'time-aligned utterance by utterance. An auditory transform maps each to a loudness representation over '
        'time and Bark frequency bands. The difference between the two gives the disturbance, which a cognitive '
        'model weights asymmetrically and aggregates over time into a raw score, finally mapped to MOS-LQO.')
steps = [('1 · Level & filter', 'IRS handset response'), ('2 · Time alignment', 'delay per utterance'),
         ('3 · Auditory transform', 'Bark bands, loudness'), ('4 · Disturbance', 'loudness difference'),
         ('5 · Cognitive model', 'asymmetry, Lp aggregation'), ('6 · Mapping', 'raw → MOS-LQO (P.862.1)')]
s.text(20, 22, 'INPUT: REFERENCE + DEGRADED SIGNAL', 'label')
for k, (t, sub) in enumerate(steps):
    col, row = k % 3, k // 3
    x, y = 20 + col * 295, 40 + row * 110
    s.box(x, y, 250, 60, t, sub, TINT if k < 5 else PAPER)
    if col < 2:
        s.line(x + 250, y + 30, x + 295, y + 30, INK, 2, arrow='ink')
s.path('M735,100 L735,125 L145,125', INK, 2)
s.line(145, 125, 145, 150, INK, 2, arrow='ink')
s.text(440, 240, 'Raw PESQ score −0.5 … 4.5 · the mapping fits it to subjective ACR results from many listening tests',
       'small', 'middle')
s.save()

# --- Audio bandwidth classes and the standards for each -------------------------
s = SVG(DECK, 'bandwidths', 285, 'Audio bandwidth classes and the matching quality standards',
        'On a logarithmic frequency axis from 20 hertz to 20 kilohertz: narrowband telephony covers 300 to 3400 '
        'hertz, wideband 50 to 7000, super-wideband 50 to 14000 and fullband 20 to 20000. PESQ, now withdrawn, '
        'covered narrowband and, with P.862.2, wideband. POLQA covers narrowband to fullband. The E-model has '
        'narrowband, wideband and super-wideband/fullband versions.')
LX = lambda f: 290 + (math.log10(f) - 1) / (math.log10(20000) - 1) * 560  # noqa: E731  log axis, 10 Hz … 20 kHz
bands = [('Narrowband', 300, 3400, 'G.711, G.729 · P.862 (withdrawn) · P.863 · G.107'),
         ('Wideband', 50, 7000, 'G.722, AMR-WB · P.862.2 (withdrawn) · G.107.1'),
         ('Super-wideband', 50, 14000, 'EVS, Opus · P.863 · G.107.2'),
         ('Fullband', 20, 20000, 'EVS, Opus · POLQA P.863 · G.107.2')]
fmt = lambda f: f'{f / 1000:g} kHz' if f >= 1000 else f'{f} Hz'  # noqa: E731
for k, (name, lo, hi, std) in enumerate(bands):
    y = 20 + k * 50
    s.text(20, y + 20, name, 'bold')
    s.text(20, y + 38, std, 'small')
    s.rect(LX(lo), y + 4, LX(hi) - LX(lo), 30, [TINT, TINT2, TINT3, TINT4][k], G, 1.5)
    s.text(LX(lo) + 6, y + 24, fmt(lo), 'small green', 'start')
    s.text(LX(hi) - 6, y + 24, fmt(hi), 'small green', 'end')
s.line(290, 218, 850, 218, INK, 1.5)
for dec in (10, 100, 1000, 10000):
    for m in range(1, 10):
        f = dec * m
        if f <= 20000:
            s.line(LX(f), 218, LX(f), 226 if m == 1 else 222, INK, 1.5 if m == 1 else 1)
s.line(LX(20000), 218, LX(20000), 226, INK, 1.5)
for f, lab in [(10, '10 Hz'), (100, '100 Hz'), (1000, '1 kHz'), (10000, '10 kHz')]:
    s.text(LX(f), 244, lab, 'small', 'middle')
s.text(440, 277, 'A model is valid only for the bandwidth it was trained on — never score wideband audio with narrowband PESQ.',
       'small', 'middle')
s.save()

# --- E-model reference connection --------------------------------------------
s = SVG(DECK, 'emodel-connection', 330, 'Reference connection of the E-model',
        'The E-model describes a call as a send side, a network, and a receive side. The send side carries the '
        'send loudness rating, room noise and sidetone. The network carries codec impairment, packet loss and '
        'robustness, delays, echo and circuit noise. The receive side carries the receive loudness rating, room '
        'noise and listener sidetone. All of them feed the single rating R.')
panels = [(20, 230, 'SEND SIDE · talker', 78, [('SLR', 'send loudness'), ('Ps', 'room noise'),
                                                 ('STMR', 'sidetone masking'), ('Ds', 'handset D-factor')]),
          (300, 280, 'NETWORK · IP path', 128, [('Ie, Bpl', 'codec & PLC'), ('Ppl, BurstR', 'packet loss'),
                                                ('T, Ta, Tr', 'delays'), ('TELR, WEPL', 'echo'),
                                                ('Nc, qdu', 'noise, quantizing')]),
          (630, 230, 'RECEIVE SIDE · listener', 78, [('RLR', 'receive loudness'), ('Pr', 'room noise'),
                                                     ('LSTR', 'listener sidetone'), ('Dr', 'handset D-factor')])]
for x, w, title, indent, rows in panels:
    s.rect(x, 60, w, 180, PAPER, LINE)
    s.rect(x, 60, w, 4, G, 'none')
    s.text(x + 14, 90, title, 'label')
    for k, (sym, desc) in enumerate(rows):
        s.text(x + 14, 122 + k * 25, sym, 'bold green')
        s.text(x + 14 + indent, 122 + k * 25, desc, 'small')
s.line(250, 150, 300, 150, INK, 2, arrow='ink')
s.line(580, 150, 630, 150, INK, 2, arrow='ink')
s.line(20, 32, 860, 32, MUT, 1.5)
s.line(20, 24, 20, 40, MUT, 1.5); s.line(860, 24, 860, 40, MUT, 1.5)
s.text(440, 22, 'OLR = SLR + RLR   (overall loudness, mouth to ear)', 'small', 'middle')
s.text(440, 272, 'A — advantage (expectation) factor: set by the user’s situation, not by the equipment', 'small', 'middle')
s.text(440, 310, 'R = Ro − Is − Id − Ie-eff + A', 'big', 'middle')
s.save()

# --- E-model: the formulas shared by the next three figures ---------------------
RO, IS = 94.77, 1.41  # G.107 default basic signal-to-noise ratio and simultaneous impairment


def mos_from_r(r):
    """ITU-T G.107 Annex B: rating R → estimated conversational MOS (MOS-CQE)."""
    if r <= 0:
        return 1.0
    if r >= 100:
        return 4.5
    return 1 + 0.035 * r + r * (r - 60) * (100 - r) * 7e-6


def id_delay(t, telr=65.0, wepl=110.0):
    """ITU-T G.107 delay impairment Id = Idte + Idle + Idd for one-way delay t [ms], Ta = T, Tr = 2T."""
    roe = RO  # −1.5 (No − 2) with the default noise floor No = −61.18 dBm0p
    terv = telr - 40 * math.log10((1 + t / 10) / (1 + t / 150)) + 6 * math.exp(-0.3 * t * t)
    re = 80 + 2.5 * (terv - 14)
    idte = ((roe - re) / 2 + math.sqrt((roe - re) ** 2 / 4 + 100) - 1) * (1 - math.exp(-t))
    rle = 10.5 * (wepl + 7) * (2 * t + 1) ** -0.25
    idle = (RO - rle) / 2 + math.sqrt((RO - rle) ** 2 / 4 + 169)
    x = math.log10(t / 100) / math.log10(2) if t > 100 else 0
    idd = 25 * ((1 + x ** 6) ** (1 / 6) - 3 * (1 + (x / 3) ** 6) ** (1 / 6) + 2) if t > 100 else 0
    return idte + idle + idd


def ie_eff(ie, bpl, ppl, burst=1.0):
    """ITU-T G.107 effective equipment impairment for packet-loss percentage ppl."""
    return ie + (95 - ie) * ppl / (ppl / burst + bpl)


# --- R-factor → MOS with the G.109 user-satisfaction bands ---------------------
s = SVG(DECK, 'r-to-mos', 310, 'Mapping the E-model rating R to MOS, with user-satisfaction categories',
        'MOS as a function of R from 0 to 100, following ITU-T G.107: an S-shaped curve from 1 at R = 0 to 4.5 at '
        'R = 100. Background bands mark the G.109 categories: 90 to 100 very satisfied, 80 to 90 satisfied, 70 to '
        '80 some users dissatisfied, 60 to 70 many users dissatisfied, 50 to 60 nearly all users dissatisfied, '
        'below 50 not recommended. The default narrowband connection has R = 93.2, MOS 4.41, the best a '
        'narrowband connection can reach; the curve beyond it is dashed. Below R = 6.5 the formula dips '
        'slightly under MOS 1, drawn as a red dashed segment.')
axes_at = len(s.parts)  # the bands are inserted here so the axes and arrowheads stay on top
ax = Axes(s, 70, 20, 520, 220, (0, 104), (1, 4.7), xlabel='R', ylabel='MOS-CQE',
          xticks=[(v, str(v)) for v in (0, 20, 40, 50, 60, 70, 80, 90, 100)],
          yticks=[(v, str(v)) for v in (1, 2, 3, 4, 4.5)], grid=False)
cats = [(90, 100, TINT3, 'Very satisfied'), (80, 90, TINT, 'Satisfied'), (70, 80, YTINT, 'Some users dissatisfied'),
        (60, 70, OTINT, 'Many users dissatisfied'), (50, 60, RTINT, 'Nearly all dissatisfied'),
        (0, 50, GREYTINT, 'Not recommended')]
for k, (lo, hi, fill, lab) in enumerate(cats):
    s.parts.insert(axes_at, f'<rect x="{ax.px(lo):.1f}" y="{ax.py(4.7):.1f}" width="{ax.px(hi) - ax.px(lo):.1f}" '
                            f'height="{ax.py(1) - ax.py(4.7):.1f}" fill="{fill}" stroke="none"/>')
    ly = 36 + k * 34
    s.rect(620, ly - 14, 18, 18, fill, LINE)
    s.text(646, ly, lab, 'small')
    s.text(870, ly, f'R ≥ {lo}' if lo else 'R < 50', 'small', 'end')
# Solid up to the narrowband maximum R = 93.2 (all G.107 defaults); dashed beyond it, where the mapping is
# defined but no narrowband connection can reach. The axis runs past 100 only for its arrowhead.
# Below R ≈ 6.5 the G.107 polynomial dips under MOS 1 (min ≈ 0.99), which is why G.107 Appendix I
# inverts it only for 6.5 ≤ R ≤ 100. Mark that stretch as a red dashed line instead of hiding it.
R_LOW = 6.5
ax.curve(mos_from_r, FMT, 2, n=40, xr=(0, R_LOW), dash=True)
ax.curve(mos_from_r, G, 3, n=280, xr=(R_LOW, 93.2))
ax.curve(mos_from_r, G, 2, n=20, xr=(93.2, 100), dash=True)
for r in (50, 60, 70, 80, 90):
    s.text(ax.px(r) - 4, ax.py(mos_from_r(r)) - 10, f'{mos_from_r(r):.2f}', 'small', 'end')
s.dot(ax.px(93.2), ax.py(mos_from_r(93.2)), 6, D)
s.line(ax.px(93.2), ax.py(mos_from_r(93.2)), ax.px(93.2), ax.py(2.2), D, 1.5)
s.text(ax.px(93.2) - 6, ax.py(2.1), 'G.107 default', 'small bold', 'end')
s.text(ax.px(93.2) - 6, ax.py(2.1) + 18, 'R = 93.2 → 4.41', 'small bold', 'end')
s.text(440, 302, 'MOS = 1 + 0.035 R + R (R − 60)(100 − R) · 7 · 10⁻⁶   for 0 < R < 100', 'small', 'middle')
s.save()

# --- R versus one-way delay for five echo loudness ratings -----------------------
# Same axes as the course's original figure (R 50–100). The original was
# drawn with the 1998 E-model (default R = 94.2); these curves use G.107 (06/2015), whose default is 93.2,
# so they sit one R point lower at every delay — the only difference.
s = SVG(DECK, 'r-vs-delay', 322, 'E-model rating R against one-way delay for five talker echo loudness ratings',
        'R computed with the ITU-T G.107 delay impairment for one-way delays from 0 to 500 milliseconds and TELR '
        'of 65, 60, 55, 50 and 45 dB, all other parameters at default. With good echo control, TELR 65 dB, R stays '
        'near 90 until about 150 ms. Weaker echo '
        'loss makes R fall much earlier: at TELR 45 dB it drops to 70 already around 100 ms.')
ax = Axes(s, 70, 20, 560, 230, (0, 500), (50, 100), xlabel='one-way delay T [ms]', ylabel='R',
          xticks=[(v, str(v)) for v in range(0, 501, 100)], yticks=[(v, str(v)) for v in (50, 60, 70, 80, 90, 100)])
s.line(ax.px(150), ax.py(50), ax.px(150), ax.py(100), MUT, 1.5, dash=True)
s.text(ax.px(150) + 6, ax.py(97), 'G.114: 150 ms', 'small')
for k, (telr, col) in enumerate([(65, G), (60, D), (55, EKF), (50, FBI), (45, FMT)]):
    pts = [(t, RO - IS - id_delay(t, telr)) for t in (i * 2 for i in range(251))]
    s.polyline([(ax.px(t), ax.py(r)) for t, r in pts if r >= 50], col, 2.5)
    s.line(670, 44 + k * 30, 710, 44 + k * 30, col, 2.5)
    s.text(718, 49 + k * 30, f'TELR = {telr} dB', 'small')
s.text(670, 215, 'Ie = 0, A = 0, no loss,', 'small')
s.text(670, 235, 'other inputs at default', 'small')
s.text(440, 316, 'Delay alone is tolerable; delay combined with audible echo is what destroys a conversation.', 'small', 'middle')
s.save()

# --- Ie against packet loss: the tabulated values of G.113 Appendix I -------------
# Exactly the data behind the course's original figure: Tables I.2 and I.3 of G.113 Appendix I (09/1999).
# The G.711-without-PLC column was withdrawn in the 10/2001 edition as too pessimistic; the other columns
# are identical in both editions. From 05/2002 the tables were replaced by the Ie-eff/Bpl formula of G.107.
s = SVG(DECK, 'ie-vs-loss', 322, 'Equipment impairment against packet loss, tabulated values of ITU-T G.113',
        'Provisional planning values of Ie against packet loss from ITU-T G.113 Appendix I (1999). G.711 without '
        'packet-loss concealment rises steeply to 55 at 5 percent loss. G.711 with concealment rises slowly to 45 at '
        '20 percent under random loss, but jumps to 30 at 5 percent under bursty loss. G.729A and G.723.1 with VAD '
        'start at 11 and 15 and reach 49 and 55 at 16 percent; GSM EFR starts at 5 and reaches 33 at 5 percent.')
G113_IE = [  # (label, colour, dashed, [(loss %, Ie), ...])
    ('G.711 without PLC', FMT, False, [(0, 0), (1, 25), (2, 35), (3, 45), (5, 55)]),
    ('G.711 + PLC, random loss', G, False, [(0, 0), (1, 5), (2, 7), (3, 10), (5, 15), (7, 20), (10, 25), (15, 35), (20, 45)]),
    ('G.711 + PLC, bursty loss', G, True, [(0, 0), (1, 5), (2, 7), (3, 10), (5, 30), (7, 35), (10, 40), (15, 45), (20, 50)]),
    ('G.729A + VAD', EKF, False, [(0, 11), (0.5, 13), (1, 15), (1.5, 17), (2, 19), (3, 23), (4, 26), (8, 36), (16, 49)]),
    ('G.723.1 + VAD (6.3 kbit/s)', FBI, False, [(0, 15), (0.5, 17), (1, 19), (1.5, 22), (2, 24), (3, 27), (4, 32), (8, 41), (16, 55)]),
    ('GSM 06.60 EFR', D, False, [(0, 5), (1, 16), (2, 21), (3, 26), (5, 33)]),
]
ax = Axes(s, 70, 20, 500, 230, (0, 21), (0, 60), xlabel='packet loss [%]', ylabel='Ie',
          xticks=[(v, str(v)) for v in (0, 5, 10, 15, 20)], yticks=[(v, str(v)) for v in range(10, 61, 10)])
for k, (name, col, dash, pts) in enumerate(G113_IE):
    s.polyline([(ax.px(x), ax.py(y)) for x, y in pts], col, 2.5, dash=dash)
    for x, y in pts:
        s.dot(ax.px(x), ax.py(y), 3.5, col)
    s.line(600, 44 + k * 30, 640, 44 + k * 30, col, 2.5, dash=dash)
    s.dot(620, 44 + k * 30, 3.5, col)
    s.text(648, 49 + k * 30, name, 'small')
s.text(600, 240, 'Dots: tabulated values', 'small')
s.text(440, 316, 'Provisional planning values of ITU-T G.113 Appendix I (1999) — the data the Bpl formula was later fitted to.',
       'small', 'middle')
s.save()

# =============================================================================
# 06 — Video quality assessment: subjective methods, PSNR, SSIM and VMAF
# =============================================================================
DECK = '06'

# --- The video delivery chain and where quality is lost ------------------------
s = SVG(DECK, 'video-chain', 300, 'The video delivery chain and the impairments each stage adds',
        'Five stages from left to right: capture, pre-processing, encoding, transmission, and decoding with '
        'display. Under each stage the impairments it typically introduces: sensor resolution, noise and motion '
        'blur at capture; scaling, colour conversion and chroma subsampling in pre-processing; blocking, blurring, '
        'ringing and mosquito noise in the encoder; packet loss, delay and stalling during transmission; error '
        'concealment, display size and viewing distance at the receiver.')
stages = [('Capture', 'camera, sensor'), ('Pre-processing', 'scaling, 4:2:0'), ('Encoding', 'H.264 … AV1'),
          ('Transmission', 'IP network, CDN'), ('Playback', 'decoder, screen')]
impairments = [['resolution', 'sensor noise', 'motion blur'], ['down-scaling', 'colour conversion', 'chroma loss'],
               ['blocking, blurring', 'ringing', 'mosquito noise'], ['packet loss', 'delay, jitter', 'stalling'],
               ['error concealment', 'screen size', 'viewing distance']]
for k, ((t, sub), imps) in enumerate(zip(stages, impairments)):
    x = 20 + k * 172
    s.box(x, 40, 150, 60, t, sub, TINT if k != 2 else TINT3)
    if k < 4:
        s.line(x + 150, 70, x + 172, 70, INK, 2, arrow='ink')
    s.line(x + 75, 100, x + 75, 128, FMT, 1.5, dash=True, arrow='red')
    s.rect(x, 130, 150, 92, PAPER, LINE)
    for j, imp in enumerate(imps):
        s.text(x + 12, 156 + j * 26, imp, 'small')
s.text(20, 22, 'SOURCE → VIEWER', 'label')
s.text(20, 252, 'Signal quality is lost at every stage; what the viewer finally judges also depends on the display and on',
       'small')
s.text(20, 274, 'the viewing context — the QoS/QoE distinction of Lecture 03 applies to video as it did to speech.', 'small')
s.save()

# --- Group of pictures: prediction structure and error propagation ------------
s = SVG(DECK, 'gop', 300, 'A group of pictures and the propagation of a transmission error',
        'Thirteen frames in display order: an I-frame, then B, B, P repeated, and the next I-frame. P-frames are '
        'predicted from the previous I- or P-frame, B-frames from the reference frames on both sides. A packet '
        'lost in the first P-frame corrupts that frame, the two B-frames before it that use it as a backward '
        'reference, and every later frame predicted from it, until the next I-frame refreshes the picture.')
frames = ['I', 'B', 'B', 'P', 'B', 'B', 'P', 'B', 'B', 'P', 'B', 'B', 'I']
W, X0, Y0 = 56, 40, 70
hit = 3  # the P-frame that loses a packet
for k, f in enumerate(frames):
    x = X0 + k * (W + 7)
    damaged = 1 <= k < 12  # B1, B2 use P3 as their backward reference, so they are hit too
    fill = RTINT if damaged else (TINT3 if f == 'I' else TINT if f == 'P' else PAPER)
    s.rect(x, Y0, W, 60, fill, FMT if k == hit else LINE, 2.5 if k == hit else 1)
    s.text(x + W / 2, Y0 + 38, f, 'big', 'middle')
refs = [k for k, f in enumerate(frames) if f in 'IP']
for a, b in zip(refs, refs[1:]):  # forward prediction arcs above the frames
    xa, xb = X0 + a * (W + 7) + W / 2, X0 + b * (W + 7) + W / 2
    if frames[b] == 'P':
        s.path(f'M{xa:.1f},{Y0} Q{(xa + xb) / 2:.1f},{Y0 - 44} {xb:.1f},{Y0 - 2}', G, 2, arrow='green')
s.text(X0, 20, 'I — intra-coded (self-contained)   P — predicted from the past   B — bi-directionally predicted',
       'small')
# B-frame references, shown once for frames 4 and 5
for bk in (4, 5):
    xb = X0 + bk * (W + 7) + W / 2
    for rk in (3, 6):
        xr = X0 + rk * (W + 7) + W / 2
        s.path(f'M{xr:.1f},{Y0 + 60} Q{(xr + xb) / 2:.1f},{Y0 + 60 + 40 + 12 * abs(rk - bk)} {xb:.1f},{Y0 + 62}', MUT, 1.2, arrow='muted')
s.text(X0 + hit * (W + 7) - 8, Y0 + 90, 'packet lost', 'small bold', 'end')
x1, x2 = X0 + 1 * (W + 7), X0 + 11 * (W + 7) + W
s.line(x1, 218, x2, 218, FMT, 2)
s.line(x1, 210, x1, 226, FMT, 2); s.line(x2, 210, x2, 226, FMT, 2)
s.text((x1 + x2) / 2, 246, 'error propagates through every frame that references the damaged one', 'small', 'middle')
s.text(X0 + 12 * (W + 7) + W / 2, 246, 'refresh', 'small green', 'middle')
s.text(440, 284, 'Longer GOPs save bits (fewer I-frames) but let a single loss stay visible longer.', 'small', 'middle')
s.save()

# --- Equal MSE, different perceived quality -----------------------------------------
# A 32 x 32 synthetic reference and four distortions scaled to exactly the same MSE, in the spirit of
# Wang & Bovik (2009), Fig. 2. PSNR is therefore identical; SSIM is computed here with the lab's defaults
# (L = 255, k1 = 0.01, k2 = 0.03) over uniform 8 x 8 windows, so the values match what lab 04's code would give
# for a uniform window.
N = 32


def ref_pixel(i, j):
    v = 118 + 48 * math.sin(2 * math.pi * (i + 0.6 * j) / 13) * math.cos(2 * math.pi * j / 21)
    v += 40 if (i - 20) ** 2 + (j - 11) ** 2 < 36 else 0   # a bright disc: a sharp edge for the eye to find
    v += 30 if j > 22 else 0                                # a vertical step
    return v


REF = [[ref_pixel(i, j) for j in range(N)] for i in range(N)]


def mse_of(a, b):
    return sum((a[i][j] - b[i][j]) ** 2 for i in range(N) for j in range(N)) / N ** 2


def mix(a, b, alpha):  # a + alpha (b - a): scales a distortion without changing its shape
    return [[a[i][j] + alpha * (b[i][j] - a[i][j]) for j in range(N)] for i in range(N)]


def ssim_uniform(a, b, win=8, L=255):
    c1, c2, vals = (0.01 * L) ** 2, (0.03 * L) ** 2, []
    for i in range(N - win + 1):
        for j in range(N - win + 1):
            xs = [a[i + u][j + v] for u in range(win) for v in range(win)]
            ys = [b[i + u][j + v] for u in range(win) for v in range(win)]
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            vx = sum((x - mx) ** 2 for x in xs) / len(xs)
            vy = sum((y - my) ** 2 for y in ys) / len(ys)
            cxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / len(xs)
            vals.append((2 * mx * my + c1) * (2 * cxy + c2) / ((mx * mx + my * my + c1) * (vx + vy + c2)))
    return sum(vals) / len(vals)


rng = random.Random(6)
blocks = [[sum(REF[8 * (i // 8) + u][8 * (j // 8) + v] for u in range(8) for v in range(8)) / 64
           for j in range(N)] for i in range(N)]
blur = [[sum(REF[min(N - 1, max(0, i + u))][min(N - 1, max(0, j + v))] for u in (-2, -1, 0, 1, 2) for v in (-2, -1, 0, 1, 2)) / 25
         for j in range(N)] for i in range(N)]
noise = [[REF[i][j] + rng.gauss(0, 1) for j in range(N)] for i in range(N)]
TARGET = 225.0  # MSE 225 → 15 grey levels RMS → PSNR 24.6 dB
shift = [[REF[i][j] + math.sqrt(TARGET) for j in range(N)] for i in range(N)]
variants = [('Reference', REF)]
for name, d in [('Mean shift', shift), ('Gaussian noise', noise), ('Blur', blur), ('Blocking 8 × 8', blocks)]:
    variants.append((name, mix(REF, d, math.sqrt(TARGET / mse_of(REF, d)))))
psnr_db = 10 * math.log10(255 ** 2 / TARGET)
s = SVG(DECK, 'equal-mse', 300, 'Four distortions with the same MSE and PSNR but very different SSIM',
        'A synthetic 32 by 32 pixel reference image and four distorted versions: a uniform brightness shift, '
        'additive Gaussian noise, blur, and 8 by 8 blocking. Each distortion is scaled so that the mean squared '
        f'error is exactly {TARGET:.0f}, giving the same PSNR of {psnr_db:.1f} dB for all four. SSIM, computed with 8 by 8 '
        'windows, ranks them very differently: ' + ', '.join(
            f'{n} {ssim_uniform(REF, v):.2f}' for n, v in variants[1:]) + '.')
P = 5  # screen pixels per image pixel → 160 x 160 panels
for k, (name, img) in enumerate(variants):
    x0, y0 = 20 + k * 172, 30
    s.text(x0, 20, name, 'bold')
    s.rect(x0, y0, N * P, N * P, IMG0, 'none')
    for i in range(N):
        for j in range(N):
            v = min(255, max(0, img[i][j])) / 255
            s.parts.append(f'<rect x="{x0 + j * P}" y="{y0 + i * P}" width="{P}" height="{P}" fill="{IMG1}" '
                           f'fill-opacity="{v:.3f}"/>')
    s.rect(x0, y0, N * P, N * P, 'none', LINE)
    if k:
        s.text(x0, 214, f'MSE {mse_of(REF, img):.0f} · PSNR {psnr_db:.1f} dB', 'small')
        s.text(x0, 238, f'SSIM {ssim_uniform(REF, img):.2f}', 'bold green')
    else:
        s.text(x0, 214, 'MSE 0 · PSNR ∞', 'small')
        s.text(x0, 238, 'SSIM 1.00', 'bold green')
s.text(440, 284, 'PSNR cannot tell these apart; SSIM, which compares local structure, can.', 'small', 'middle')
s.save()

# --- Structure of a subjective test session ------------------------------------
s = SVG(DECK, 'session', 250, 'Structure of a subjective video test session',
        'A session starts with a short training sequence of representative conditions, followed by a break for '
        'questions. The session proper opens with a few stabilising sequences whose ratings are discarded, '
        'followed by the main part in randomised order. The whole session should not exceed about 30 minutes.')
s.text(20, 22, 'TRAINING', 'label')
for k in range(4):
    s.rect(20 + k * 30, 70, 30, 44, NEUTRAL, LINE)
s.text(80, 140, 'representative', 'small', 'middle')
s.text(80, 158, 'conditions', 'small', 'middle')
s.text(215, 96, 'break', 'bold', 'middle')
s.text(215, 116, 'questions', 'small', 'middle')
s.line(150, 92, 180, 92, MUT, 1.5, arrow='muted')
s.line(250, 92, 280, 92, MUT, 1.5, arrow='muted')
s.text(290, 22, 'STABILISING', 'label')
for k in range(4):
    s.rect(290 + k * 30, 70, 30, 44, GREYTINT, LINE)
s.text(350, 140, 'not processed', 'small', 'middle')
s.text(430, 22, 'MAIN PART — RANDOMISED ORDER', 'label')
for k in range(14):
    s.rect(430 + k * 30, 70, 30, 44, TINT if k % 2 else TINT2, LINE)
s.line(290, 50, 850, 50, G, 1.5)
s.line(290, 44, 290, 56, G, 1.5); s.line(850, 44, 850, 56, G, 1.5)
s.text(640, 40, '≤ 30 min per session', 'small green', 'middle')
s.text(640, 140, 'each cell: one sequence + vote', 'small', 'middle')
s.text(640, 158, 'replicated conditions check each viewer’s consistency', 'small', 'middle')
s.text(440, 220, 'Randomisation cancels order and fatigue effects; the stabilising items absorb the “first impressions”.',
       'small', 'middle')
s.save()

# --- Presentation timing of the main test methods -----------------------------------
s = SVG(DECK, 'methods-timing', 300, 'Presentation patterns of ACR, ACR-HR, DCR, PC and DSCQS',
        'Timelines of the five methods. ACR shows one test sequence of about 10 seconds followed by a vote. ACR-HR '
        'is the same, but the unprocessed reference is hidden among the test sequences. DCR, called DSIS in ITU-R '
        'BT.500, shows the reference, a 2 second grey pause, the test sequence, then a vote on the impairment. PC '
        'shows the same content through two systems and asks for a preference. DSCQS alternates A and B twice, the '
        'viewer not knowing which is the reference, and rates both.')
rows = [('ACR', [('Test sequence', 170, PAPER), ('Vote ≤ 10 s', 110, GREYTINT)], 'no reference, absolute scale'),
        ('ACR-HR', [('Test or hidden ref.', 170, PAPER), ('Vote', 110, GREYTINT)], 'reference hidden → DMOS'),
        ('DCR / DSIS', [('Reference', 150, TINT), ('', 16, NEUTRAL), ('Test', 150, PAPER), ('Vote', 90, GREYTINT)],
         'impairment vs. known ref.'),
        ('PC', [('System A', 150, PAPER), ('', 16, NEUTRAL), ('System B', 150, PAPER), ('Vote', 90, GREYTINT)],
         'preference within a pair'),
        ('DSCQS', [('A', 90, PAPER), ('B', 90, PAPER), ('A', 90, PAPER), ('B', 90, PAPER), ('Vote A, B', 90, GREYTINT)],
         'ref. is A or B, unknown')]
for k, (name, segs, note) in enumerate(rows):
    y = 16 + k * 50
    s.text(20, y + 26, name, 'bold')
    x = 130
    for lab, w, fill in segs:
        s.rect(x, y, w, 38, fill, LINE)
        if lab:
            s.text(x + w / 2, y + 25, lab, '', 'middle')
        x += w
    s.text(x + 14, y + 25, note, 'small')
s.text(440, 290, '~10 s per sequence · grey pause ≈ 2 s between the two stimuli of a pair (ITU-T P.910)', 'small', 'middle')
s.save()

# --- Rating scales for video ----------------------------------------------------
s = SVG(DECK, 'video-scales', 320, 'Rating scales used in subjective video tests',
        'Four scales side by side. The five-grade ACR scale from Excellent to Bad. The nine-grade scale with the '
        'same five labels on every second grade, 9 to 1. The eleven-grade scale from 0 to 10, where 10 means a '
        'reproduction perfectly faithful to the original and 0 no similarity to it, both endpoints used only as '
        'anchors. The continuous scale from 0 to 100 with the five labels as guides, used by DSCQS and SAMVIQ.')
labels = ['Excellent', 'Good', 'Fair', 'Poor', 'Bad']
cols = [('5-grade · ACR', [(str(5 - k), labels[k]) for k in range(5)]),
        ('9-grade', [(str(9 - k), labels[k // 2] if k % 2 == 0 else '') for k in range(9)]),
        ('11-grade', [('10', 'faithful to original')] + [(str(9 - k), labels[k // 2] if k % 2 == 0 else '')
                                                         for k in range(9)] + [('0', 'no similarity')])]
H = 256
for c, (title, grades) in enumerate(cols):
    x0 = 20 + c * 215
    s.text(x0, 20, title, 'label')
    step = H / len(grades)
    for k, (g, lab) in enumerate(grades):
        y = 34 + k * step
        anchor = title == '11-grade' and g in ('10', '0')
        s.rect(x0, y, 40, step - 2, PAPER if anchor else TINT, LINE)
        s.text(x0 + 20, y + step / 2 + 4, g, 'small bold green' if step < 26 else 'bold green', 'middle')
        if lab:
            s.text(x0 + 50, y + step / 2 + 5, lab, 'small' if anchor else '')
x0 = 665
s.text(x0, 20, 'Continuous · DSCQS', 'label')
s.rect(x0 + 10, 34, 26, H - 2, TINT, G, 1.5)
for k, lab in enumerate(labels):
    y = 34 + k * H / 5
    s.line(x0 + 10, y, x0 + 36, y, G, 1)
    s.text(x0 + 46, y + H / 10 + 5, lab)
s.line(x0 + 4, 34 + 0.37 * H, x0 + 42, 34 + 0.37 * H, FMT, 3)
s.text(x0 + 124, 34 + 0.37 * H + 5, '← 63', 'small')
s.text(440, 312, 'More grades add resolution only if viewers can use it; verbal labels anchor the meaning of the numbers.',
       'small', 'middle')
s.save()

# --- Spatial and temporal information plane (schematic) ------------------------------
s = SVG(DECK, 'siti-plane', 300, 'The spatial–temporal information plane used to select test content',
        'Schematic plane with spatial information SI on the horizontal axis and temporal information TI on the '
        'vertical axis. Low SI and low TI: a news presenter or video call. High SI, low TI: a slow pan over a '
        'detailed landscape or text. Low SI, high TI: fast camera motion over smooth surfaces. High SI and high '
        'TI: sport or a crowd scene, the hardest content to compress. A test set should cover all four quadrants.', w=470)
ax = Axes(s, 60, 20, 390, 210, (0, 1), (0, 1), xlabel='SI — spatial detail', ylabel='TI — motion', grid=False)
s.line(ax.px(0.5), ax.py(0), ax.px(0.5), ax.py(1), LINE, 1.5, dash=True)
s.line(ax.px(0), ax.py(0.5), ax.px(1), ax.py(0.5), LINE, 1.5, dash=True)
quad = [(0.25, 0.25, 'news presenter', 'video call'), (0.75, 0.25, 'landscape pan', 'text, fine texture'),
        (0.25, 0.75, 'fast pan over', 'smooth surfaces'), (0.75, 0.75, 'sport, crowd', 'hardest to compress')]
for x, y, a, b in quad:
    s.dot(ax.px(x), ax.py(y) - 26, 6, FMT if x > 0.5 and y > 0.5 else G)
    s.text(ax.px(x), ax.py(y) + 2, a, 'bold' if x > 0.5 and y > 0.5 else '', 'middle')
    s.text(ax.px(x), ax.py(y) + 22, b, 'small', 'middle')
s.text(235, 292, 'Schematic · difficulty grows towards the top right', 'small', 'middle')
s.save()

# --- Families of objective video quality models -------------------------------------
s = SVG(DECK, 'vqa-families', 300, 'Full-reference, reduced-reference, no-reference and parametric video models',
        'The source video passes through the system under test and comes out as the received video. A '
        'full-reference model compares every pixel of both. A reduced-reference model compares a few features '
        'extracted from the source and sent alongside. A no-reference model sees the received video only. A '
        'bitstream or parametric model reads no pixels at all, only packet headers or stream metadata such as '
        'bit rate, resolution and stalling events.')
s.box(20, 30, 200, 60, 'Source video', 'pristine, known', NEUTRAL)
s.line(220, 60, 330, 60, INK, 2, arrow='ink')
s.box(330, 30, 220, 60, 'System under test', 'encoder · network · player')
s.line(550, 60, 660, 60, INK, 2, arrow='ink')
s.box(660, 30, 200, 60, 'Received video', 'what the viewer sees', NEUTRAL)
s.line(60, 90, 60, 190, G, 2, arrow='green')
s.line(150, 90, 150, 140, G, 1.5, dash=True)
s.path('M150,140 L260,140', G, 1.5, dash=True)
s.line(260, 140, 260, 190, G, 1.5, dash=True, arrow='green')
s.text(160, 132, 'features', 'small')
s.path('M790,90 L790,115 L110,115', G, 2)
s.line(110, 115, 110, 190, G, 2, arrow='green')
s.line(300, 115, 300, 190, G, 2, arrow='green')
s.line(520, 115, 520, 190, G, 2, arrow='green')
s.box(20, 190, 190, 64, 'Full reference', 'PSNR · SSIM · VMAF')
s.box(225, 190, 190, 64, 'Reduced reference', 'ITU-T J.249 · J.342')
s.box(430, 190, 200, 64, 'No reference', 'BRISQUE · deep models')
s.box(645, 190, 215, 64, 'Bitstream, parametric', 'ITU-T P.1203 · P.1204', PAPER)
s.text(752, 152, 'headers, bit rate, stalls', 'small', 'middle')
s.line(752, 158, 752, 190, MUT, 2, dash=True, arrow='muted')
s.text(440, 290, 'The same trade-off as for speech: less input → easier deployment → usually lower accuracy.',
       'small', 'middle')
s.save()

# --- SSIM block diagram (after Wang et al. 2004, Fig. 3) ---------------------------
# The three comparisons sit between the two signal rows and multiply, as in the SSIM formula with
# alpha = beta = gamma = 1, instead of the original figure's crossing connectors.
s = SVG(DECK, 'ssim-diagram', 340, 'Block diagram of the structural similarity index',
        'Two signals x and y, one window of the reference and of the test image. For each, the mean is measured '
        'and subtracted, and the standard deviation is measured and divided out. Luminance comparison uses the '
        'two means, contrast comparison the two standard deviations, structure comparison the two normalised '
        'signals. The product of the three comparisons is the similarity index. After Wang et al., 2004, Fig. 3.')
cols6 = [(150, 'Luminance', 'mean μ', 'l(x, y)'), (340, 'Contrast', 'std. dev. σ', 'c(x, y)'),
         (530, 'Normalise', '(· − μ) / σ', 's(x, y)')]
for sig, y in [('x', 14), ('y', 216)]:
    s.text(12, y + 36, f'Signal {sig}', 'bold math')
    for k, (x, t, sub, _) in enumerate(cols6):
        s.box(x, y, 160, 60, t, ' ')  # blank sub keeps the title on the upper line; the sub is written below
        sub_ = escape(sub.replace('·', sig))  # μ and σ get a subscripted signal name
        for sym in ('μ', 'σ'):
            sub_ = sub_.replace(sym, f'{sym}<tspan baseline-shift="sub" font-size="11">{sig}</tspan>')
        s.parts.append(f'<text x="{x + 14}" y="{y + 49}" class="small">{sub_}</text>')
        s.line(x - (60 if k == 0 else 30), y + 30, x, y + 30, INK, 1.5, arrow='ink')
# comparison row centred between the two signal rows (74 … 216): boxes 44 high around y = 145
for k, (x, _, _, cmp_lab) in enumerate(cols6):
    s.rect(x + 25, 123, 110, 44, TINT3, LINE)
    s.text(x + 80, 151, cmp_lab, 'bold math', 'middle')
    s.line(x + 80, 74, x + 80, 123, G, 1.5, arrow='green')
    s.line(x + 80, 216, x + 80, 167, G, 1.5, arrow='green')
    if k < 2:
        s.text(x + 175, 153, '×', 'big', 'middle')
s.line(665, 145, 720, 145, INK, 2, arrow='ink')
s.rect(720, 119, 145, 52, PAPER, G, 1.5)
s.text(792, 151, 'SSIM(x, y)', 'bold', 'middle')
s.text(440, 308, 'Each comparison uses one statistic of both signals; their product is SSIM.', 'small', 'middle')
s.text(440, 330, 'After Z. Wang et al., IEEE Trans. Image Processing 13(4), 2004, Fig. 3.', 'small', 'middle')
s.save()

# --- VMAF processing pipeline ------------------------------------------------------
s = SVG(DECK, 'vmaf-pipeline', 300, 'Processing pipeline of Netflix VMAF',
        'The reference and the distorted video are both scaled to the resolution of the model. Three elementary '
        'features are computed per frame: visual information fidelity at four spatial scales, the additive '
        'detail-loss metric, and a motion feature from the reference, the mean co-located pixel difference of '
        'consecutive frames. A support vector regressor trained on subjective scores fuses them into a per-frame '
        'score from 0 to 100, which is pooled over time, by default as the arithmetic mean.')
# Orthogonal routing with one end point per arrow, so no two arrowheads meet at the same spot. The one
# unavoidable crossing (reference → ADM over the distorted bus) is drawn with a gap in the crossing line.
s.box(20, 20, 170, 56, 'Reference', 'scaled to model res.', NEUTRAL)       # centre y = 48
s.box(20, 168, 170, 56, 'Distorted', 'scaled to model res.', NEUTRAL)      # centre y = 196
for t, sub, yc in [('Motion', 'reference only', 48), ('VIF × 4 scales', 'information fidelity', 118),
                   ('ADM (DLM)', 'detail loss', 188)]:
    s.box(290, yc - 28, 200, 56, t, sub)
s.line(190, 48, 290, 48, INK, 1.5, arrow='ink')                             # reference → motion
s.path('M215,48 L215,180', INK, 1.5)                                        # reference bus
s.line(215, 108, 290, 108, INK, 1.5, arrow='ink')                           # reference → VIF
s.line(215, 180, 244, 180, INK, 1.5)                                        # reference → ADM, gap at the bus
s.line(256, 180, 290, 180, INK, 1.5, arrow='ink')
s.dot(215, 48, 3.5, INK); s.dot(215, 108, 3.5, INK)
s.line(190, 196, 290, 196, INK, 1.5, arrow='ink')                           # distorted → ADM
s.path('M250,196 L250,128 L290,128', INK, 1.5, arrow='ink')                 # distorted → VIF
s.dot(250, 196, 3.5, INK)
s.path('M490,48 L515,48 L515,100 L545,100', INK, 1.5, arrow='ink')         # motion → SVR
s.line(490, 118, 545, 118, INK, 1.5, arrow='ink')                           # VIF → SVR
s.path('M490,188 L515,188 L515,136 L545,136', INK, 1.5, arrow='ink')       # ADM → SVR
s.box(545, 90, 145, 56, 'SVR fusion', 'trained on MOS', TINT3)
s.line(690, 118, 720, 118, INK, 2, arrow='ink')
s.box(720, 90, 150, 56, 'Score 0 … 100', 'per frame → mean', PAPER)
s.text(20, 258, 'Models: vmaf_v0.6.1 (1080p TV at 3H) · 4K model (1.5H) · phone model · NEG variant (no enhancement gain).',
       'small')
s.text(20, 282, 'The features are per-frame; temporal behaviour enters only through the motion feature and the pooling.',
       'small')
s.save()

# --- Correlation of objective metrics with subjective scores -------------------------
# Spearman rank-order correlation (SROCC) over all codecs, read from the MSU Video Quality Metrics Benchmark
# chart (videoprocessing.ai) used in the original 2023 course slides. Each bar spans the variants of one
# metric family (colour spaces, model versions, weightings) from the lowest to the highest SROCC.
SROCC = [('VMAF (v0.6.1 – v0.6.3, NEG)', 0.9130, 0.9449, G), ('MS-SSIM', 0.8353, 0.9090, EKF),
         ('SSIM', 0.8428, 0.9059, EKF), ('PSNR', 0.8650, 0.8833, FBI), ('Other full-reference metrics', 0.5367, 0.9372, MUT)]
s = SVG(DECK, 'metric-srocc', 300, 'Rank correlation of objective video metrics with subjective scores',
        'Spearman rank-order correlation with subjective scores over all codecs of the MSU video quality metrics '
        'benchmark. VMAF variants range from 0.913 to 0.945, MS-SSIM variants from 0.835 to 0.909, SSIM from '
        '0.843 to 0.906, PSNR from 0.865 to 0.883, and other full-reference metrics from 0.537 to 0.937. '
        'A perfect predictor would reach 1.')
ax = Axes(s, 250, 20, 520, 200, (0.5, 1.0), (0, len(SROCC)), xlabel='SROCC with subjective score',
          xticks=[(v / 100, f'{v / 100:.2f}') for v in range(50, 101, 5)], grid=True)
for k, (name, lo, hi, col) in enumerate(SROCC):
    yc = ax.py(len(SROCC) - k - 0.5)
    s.text(238, yc + 6, name, 'bold' if k == 0 else '', 'end')
    s.rect(ax.px(lo), yc - 10, ax.px(hi) - ax.px(lo), 20, col, 'none')
    s.text(ax.px(hi) + 8, yc + 5, f'{hi:.3f}', 'small')
s.line(ax.px(1.0), ax.py(0), ax.px(1.0), ax.py(len(SROCC)), FMT, 1.5, dash=True)
s.text(ax.px(1.0) - 4, 14, 'ideal', 'small', 'end')
s.text(440, 292, 'Bars span all variants of a metric (colour planes, versions). Data: MSU Video Quality Metrics Benchmark.',
       'small', 'middle')
s.save()

# --- Measured data: scripts/data/06-video-metrics.json (written by generate-video-samples.py) --------------
# Two 2 s SVT test clips (1280 x 720, 50 fps), encoded with ffmpeg; VMAF (default model v0.6.1) and PSNR-Y
# from libvmaf. The figures below only plot these numbers; regenerate the data to change them.
VIDEO_DATA = json.loads((ROOT / 'scripts' / 'data' / '06-video-metrics.json').read_text())
CODEC_COLOURS = {'H.264': EKF, 'HEVC': FBI, 'AV1': G}


def polyfit3(xs, ys):
    """Least-squares cubic, coefficients c0..c3 (normal equations, Gauss-Jordan)."""
    n = 4
    a = [[sum(x ** (i + j) for x in xs) for j in range(n)] for i in range(n)]
    b = [sum(y * x ** i for x, y in zip(xs, ys)) for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(a[r][c]))
        a[c], a[p], b[c], b[p] = a[p], a[c], b[p], b[c]
        for r in range(n):
            if r != c:
                f = a[r][c] / a[c][c]
                a[r] = [u - f * v for u, v in zip(a[r], a[c])]
                b[r] -= f * b[c]
    return [b[i] / a[i][i] for i in range(n)]


def bd_rate(ref, test, key):
    """Bjøntegaard delta rate [%]: average bit-rate difference at equal quality over the common quality range."""
    def fit(pts):
        return polyfit3([p[key] for p in pts], [math.log10(p['kbps']) for p in pts])

    lo = max(min(p[key] for p in ref), min(p[key] for p in test))
    hi = min(max(p[key] for p in ref), max(p[key] for p in test))
    integral = lambda c: sum(ci * (hi ** (i + 1) - lo ** (i + 1)) / (i + 1) for i, ci in enumerate(c))  # noqa: E731
    return (10 ** ((integral(fit(test)) - integral(fit(ref))) / (hi - lo)) - 1) * 100


# --- Rate–quality curves: three codecs, two contents -----------------------------------------------
s = SVG(DECK, 'rd-curves', 330, 'Measured rate–quality curves of H.264, HEVC and AV1 on two contents',
        'VMAF against bit rate on a logarithmic axis for H.264, HEVC and AV1, measured on two 2-second 720p50 '
        'SVT test clips. Left, park_joy, a demanding scene with trees, water and motion: all codecs need several '
        'megabits per second for good quality. Right, old_town_cross, a slow pan over a city: the same quality '
        'costs about a tenth of the bit rate. The Bjøntegaard delta rates against H.264 are printed under each panel.')
panels06 = [('park_joy', 'park_joy — high SI, high TI', 70, (2.4, 4.7)), ('old_town_cross', 'old_town_cross — low TI', 500, (2.0, 3.9))]
for content, title, x0, (lx0, lx1) in panels06:
    decades = [v for v in (100, 300, 1000, 3000, 10000, 30000) if lx0 <= math.log10(v) <= lx1]
    ax = Axes(s, x0, 32, 340, 210, (lx0, lx1), (20, 100), xlabel='bit rate [kbit/s]', ylabel='VMAF' if x0 < 100 else '',
              xticks=[(math.log10(v), f'{v:g}' if v < 1000 else f'{v // 1000:g}k') for v in decades],
              yticks=[(v, str(v)) for v in (20, 40, 60, 80, 100)])
    s.text(x0, 20, title, 'label')
    rd = VIDEO_DATA['rd'][content]
    for codec, pts in rd.items():
        xy = [(ax.px(math.log10(p['kbps'])), ax.py(p['vmaf'])) for p in pts
              if lx0 <= math.log10(p['kbps']) <= lx1 and p['vmaf'] >= 20]
        s.polyline(xy, CODEC_COLOURS[codec], 2.5)
        for x, y in xy:
            s.dot(x, y, 3.5, CODEC_COLOURS[codec])
    bd = ' · '.join(f'{c} {bd_rate(rd["H.264"], rd[c], "vmaf"):+.0f} %'.replace('-', '−') for c in ('HEVC', 'AV1'))
    s.text(x0 + 170, 300, f'BD-rate vs H.264 (VMAF): {bd}', 'small bold', 'middle')
for k, codec in enumerate(CODEC_COLOURS):
    s.line(290 + k * 110, 322, 320 + k * 110, 322, CODEC_COLOURS[codec], 2.5)
    s.text(326 + k * 110, 327, codec, 'small')
s.save()

# --- Encoding ladder and its convex hull ---------------------------------------------------------------
s = SVG(DECK, 'convex-hull', 330, 'Rate–quality curves of one clip at four resolutions and their convex hull',
        'VMAF against bit rate for park_joy encoded with H.264 at 270p, 360p, 540p and 720p and upscaled to 720p. '
        'At low bit rates a lower resolution gives the higher VMAF; as the bit rate grows the best resolution '
        'moves up. The upper envelope of all points, the convex hull, is the ideal encoding ladder for this clip.')
LADDER_COLOURS = {'270p': MUT, '360p': EKF, '540p': FBI, '720p': G}
lx0, lx1 = 2.0, 4.6
ax = Axes(s, 70, 20, 520, 230, (lx0, lx1), (0, 100), xlabel='bit rate [kbit/s]', ylabel='VMAF',
          xticks=[(math.log10(v), f'{v:g}' if v < 1000 else f'{v // 1000:g}k') for v in (100, 300, 1000, 3000, 10000, 30000)],
          yticks=[(v, str(v)) for v in (20, 40, 60, 80, 100)])
allpts = []
for res, pts in VIDEO_DATA['ladder'].items():
    xy = [(math.log10(p['kbps']), p['vmaf']) for p in pts if lx0 <= math.log10(p['kbps']) <= lx1]
    allpts += [(x, y, res) for x, y in xy]
    s.polyline([(ax.px(x), ax.py(y)) for x, y in xy], LADDER_COLOURS[res], 2)
    for x, y in xy:
        s.dot(ax.px(x), ax.py(y), 3, LADDER_COLOURS[res])
hull = []  # upper convex hull in linear bit rate (the rate–quality trade-off an encoder can interpolate)
for x, y, res in sorted(allpts, key=lambda t: 10 ** t[0]):
    while len(hull) >= 2:
        (x1, y1, _), (x2, y2, _) = hull[-2], hull[-1]
        r1, r2, r3 = 10 ** x1, 10 ** x2, 10 ** x
        if (y2 - y1) * (r3 - r1) <= (y - y1) * (r2 - r1):  # middle point on or below the chord
            hull.pop()
        else:
            break
    hull.append((x, y, res))
s.polyline([(ax.px(x), ax.py(y)) for x, y, _ in hull], INK, 1.5, dash=True)
for k, res in enumerate(reversed(list(LADDER_COLOURS))):
    s.line(620, 44 + k * 28, 650, 44 + k * 28, LADDER_COLOURS[res], 2.5)
    s.text(658, 49 + k * 28, res, 'small')
s.line(620, 44 + 4 * 28, 650, 44 + 4 * 28, INK, 1.5, dash=True)
s.text(658, 49 + 4 * 28, 'convex hull (best of all)', 'small')
# where each resolution first reaches the hull; above ~5 Mbit/s 540p and 720p are practically equal and alternate
starts = []
for x, _, res in hull:
    if res not in [r for _, r in starts]:
        starts.append((x, res))
s.text(620, 196, 'FIRST ON THE HULL', 'label')
for k, (x, res) in enumerate(starts):
    s.text(620, 222 + k * 20, f'{res}', 'small bold')
    s.text(870, 222 + k * 20, f'from {10 ** x:,.0f} kbit/s'.replace(',', ' '), 'small', 'end')
s.text(440, 322, 'park_joy, H.264 medium, CRF 18–42. Lower resolutions are upscaled (bicubic) to 1280 × 720 before VMAF.',
       'small', 'middle')
s.save()

# --- Temporal pooling of a per-frame score ---------------------------------------------------------------
loss = VIDEO_DATA['loss']
lossy, clean = loss['vmaf'], loss['vmaf_clean']
pool = {'arithmetic mean': sum(lossy) / len(lossy),
        'harmonic mean': len(lossy) / sum(1 / (1 + v) for v in lossy) - 1,
        '5th percentile': sorted(lossy)[int(0.05 * len(lossy))],
        'minimum': min(lossy)}
s = SVG(DECK, 'temporal-pooling', 320, 'Per-frame VMAF of a clip with one transmission error, and four ways to pool it',
        'Per-frame VMAF of park_joy encoded with H.264, one I-frame per second, without errors and with a burst of '
        f'lost transport-stream packets in frame {loss["frame"]}. From that frame until the next I-frame at frame 50 '
        'the damaged clip scores clearly lower, then recovers. Pooled into one number the lossy clip gets: '
        + ', '.join(f'{k} {v:.1f}' for k, v in pool.items()) + f'; the error-free clip averages {sum(clean) / len(clean):.1f}.')
ax = Axes(s, 70, 20, 500, 230, (0, 100), (40, 100), xlabel='frame (50 frames/s)', ylabel='VMAF',
          xticks=[(v, str(v)) for v in range(0, 101, 10)], yticks=[(v, str(v)) for v in (40, 60, 80, 100)])
s.line(ax.px(loss['frame']), ax.py(40), ax.px(loss['frame']), ax.py(100), FMT, 1.5, dash=True)
s.text(ax.px(loss['frame']) + 4, ax.py(44), 'packets lost', 'small')
s.line(ax.px(50), ax.py(40), ax.px(50), ax.py(100), G, 1.5, dash=True)
s.text(ax.px(50) + 4, ax.py(44), 'next I-frame', 'small')
s.polyline([(ax.px(i), ax.py(v)) for i, v in enumerate(clean)], MUT, 2)
s.polyline([(ax.px(i), ax.py(v)) for i, v in enumerate(lossy)], FMT, 2.5)
s.line(610, 34, 640, 34, MUT, 2)
s.text(648, 39, f'error-free · mean {sum(clean) / len(clean):.1f}', 'small')
s.line(610, 62, 640, 62, FMT, 2.5)
s.text(648, 67, 'one loss burst', 'small')
s.text(610, 104, 'LOSSY CLIP, POOLED', 'label')
for k, (name, v) in enumerate(pool.items()):
    y = 132 + k * 28
    s.text(610, y, name, '')
    s.text(870, y, f'{v:.1f}', 'bold green', 'end')
s.text(440, 312, f'The same frames give a score between {min(pool.values()):.0f} and {max(pool.values()):.0f} — '
       'the pooling rule is part of the metric.', 'small', 'middle')
s.save()

# =============================================================================
# 07 — Streaming and adaptive bit rate: the QoE of HTTP adaptive streaming
# =============================================================================
DECK = '07'


def cell(x, y, w, h, label, sub='', fill=TINT, stroke=LINE, sw=1.5):
    """A box with one centred bold label, or a label and a small second line."""
    s.rect(x, y, w, h, fill, stroke, sw)
    if sub:
        s.text(x + w / 2, y + h / 2 - 3, label, 'bold', 'middle')
        s.text(x + w / 2, y + h / 2 + 17, sub, 'small', 'middle')
    else:
        s.text(x + w / 2, y + h / 2 + 6, label, 'bold', 'middle')


# --- A small HTTP-adaptive-streaming player simulator -----------------------------------------
# Shared by the buffer and ABR-comparison figures, so the slides quote numbers this code actually produced.
# One client downloads 30 segments of 4 s over a seeded, piecewise-constant throughput trace; playback starts
# after the first segment, the buffer is capped at 30 s, and the player stalls whenever the buffer is empty.
LADDER = [0.375, 0.75, 1.75, 3.0, 4.3, 5.8]  # Mbit/s — a subset of Netflix's former fixed ladder
SEG, NSEG, MAXBUF = 4.0, 30, 30.0


def make_trace():
    rnd = random.Random(7)
    levels = [(0, 6.5), (20, 1.4), (48, 4.6), (80, 2.2), (100, 6.0)]
    return [max(0.3, [v for t0, v in levels if sec >= t0][-1] * (1 + rnd.uniform(-0.18, 0.18))) for sec in range(400)]


TRACE = make_trace()


def simulate(policy, dt=0.02):
    t = buf = stall = 0.0
    k, dl, rem, rate, t0 = 0, False, 0.0, 0.0, 0.0
    started, startup, samples, rates, bufs, stalls, in_stall = False, None, [], [], [], [], None
    while t < 300:
        if not dl and k < NSEG and buf + SEG <= MAXBUF:
            rate = policy(buf, samples)
            rem, dl, t0 = rate * SEG, True, t
        if dl:
            rem -= TRACE[int(t)] * dt
            if rem <= 0:
                dl, buf, k = False, buf + SEG, k + 1
                samples.append(rate * SEG / (t + dt - t0))
                rates.append((t0, t + dt, rate))
                if not started:
                    started, startup = True, t + dt
        if started:
            if buf > 0:
                if in_stall is not None:
                    stalls.append((in_stall, t))
                    in_stall = None
                buf -= min(dt, buf)
            elif k < NSEG or dl:
                stall += dt
                in_stall = t if in_stall is None else in_stall
            else:
                break
        bufs.append((t, buf))
        t += dt
    return dict(rates=rates, buf=bufs[::5], stall=stall, startup=startup, stalls=stalls)


def fixed(r):
    return lambda buf, samples: r


def rate_based(buf, samples):  # harmonic mean of the last five segment throughputs, 15 % safety margin
    if not samples:
        return LADDER[0]
    last = samples[-5:]
    est = len(last) / sum(1 / x for x in last)
    return max([r for r in LADDER if r <= 0.85 * est] or [LADDER[0]])


RESERVOIR, CUSHION = 8.0, 18.0


def bba_rate(buf):  # BBA-0 rate map (Huang et al., SIGCOMM 2014)
    if buf <= RESERVOIR:
        return LADDER[0]
    if buf >= RESERVOIR + CUSHION:
        return LADDER[-1]
    return LADDER[0] + (LADDER[-1] - LADDER[0]) * (buf - RESERVOIR) / CUSHION


def bba(buf, samples):
    return max([r for r in LADDER if r <= bba_rate(buf)] or [LADDER[0]])


def summary(res):
    rs = [r for _, _, r in res['rates']]
    sw = sum(abs(b - a) for a, b in zip(rs, rs[1:]))
    return dict(avg=sum(rs) / len(rs), nsw=sum(1 for a, b in zip(rs, rs[1:]) if a != b), stall=res['stall'],
                nstall=len(res['stalls']), startup=res['startup'],
                # linear QoE of Yin et al. (SIGCOMM 2015): quality − switching − rebuffering, per segment, mu = Rmax
                qoe=sum(rs) - sw - LADDER[-1] * (res['stall'] + res['startup']))


def trace_line(ax, color=MUT, sw=1.5):
    s.polyline([(ax.px(x), ax.py(TRACE[x])) for x in range(0, 131)], color, sw)


def rate_steps(ax, res, color, sw=2.5, dash=False):
    pts = []
    for t0, t1, r in res['rates']:
        pts += [(ax.px(t0), ax.py(r)), (ax.px(min(t1, 130)), ax.py(r))]
    s.polyline(pts, color, sw, dash)


# --- HAS architecture ---------------------------------------------------------------------
s = SVG(DECK, 'has-architecture', 300, 'HTTP adaptive streaming: encoding ladder, segments, CDN and a client-driven player',
        'The encoder produces the same content at several bit rates, the ladder, and cuts each version into segments of a few '
        'seconds. The segments and a manifest describing them are stored on an origin server and cached by a CDN. The player '
        'first downloads the manifest, then requests one segment at a time over plain HTTP, choosing the bit rate of each '
        'request with its adaptive bit rate logic from the measured throughput and its buffer level.')
cell(10, 115, 110, 60, 'Encoder', 'packager', TINT3)
s.line(120, 145, 148, 145, INK, 2, arrow='ink')
s.text(150, 40, 'LADDER × SEGMENTS', 'label')
for j, (res, br) in enumerate([('1080p', '5.8'), ('720p', '3.0'), ('480p', '1.75'), ('240p', '0.375')]):
    y = 60 + j * 42
    s.text(150, y + 21, f'{res} · {br}', 'small')
    for i in range(5):
        s.rect(250 + i * 30, y, 26, 30, TINT3 if j == 0 else TINT2 if j == 1 else TINT, LINE)
s.text(325, 240, 'segments of 2–6 s', 'small', 'middle')
s.line(405, 145, 433, 145, INK, 2, arrow='ink')
cell(435, 105, 120, 80, 'Origin', 'and CDN', NEUTRAL)
s.rect(680, 30, 190, 230, PAPER, INK, 1.5)
s.text(692, 52, 'PLAYER', 'label')
cell(695, 65, 160, 50, 'ABR logic', fill=TINT3)
s.rect(695, 130, 160, 50, TINT, LINE)
for i in range(3):
    s.rect(700 + i * 30, 138, 26, 34, G, 'none')
s.text(848, 161, 'buffer', 'bold', 'end')
cell(695, 195, 160, 50, 'Decoder, screen', fill=NEUTRAL)
s.line(775, 115, 775, 128, MUT, 1.5, arrow='muted')
s.line(775, 180, 775, 193, MUT, 1.5, arrow='muted')
s.line(678, 90, 557, 90, EKF, 2, arrow='ink')
s.text(618, 83, 'GET manifest', 'small', 'middle')
s.line(678, 128, 557, 128, EKF, 2, arrow='ink')
s.text(618, 121, 'GET seg k @ R', 'small', 'middle')
s.line(557, 160, 678, 160, G, 2.5, arrow='green')
s.text(618, 180, 'segment k', 'small', 'middle')
s.text(440, 285, 'The server is a plain web server; every adaptation decision is made by the client, one segment at a time.',
       'small', 'middle')
s.save()

# --- Buffer dynamics of a fixed-bit-rate player ---------------------------------------------
fx = simulate(fixed(4.3))
fs = summary(fx)
s = SVG(DECK, 'buffer-dynamics', 392, 'Buffer level of a player that always requests 4.3 Mbit/s over a varying link',
        'Top: the available throughput over 130 seconds, about 6.5 Mbit/s at first, dropping to about 1.4 Mbit/s at 20 s, '
        'recovering to 4.6, dropping to 2.2 at 80 s and recovering to 6 at 100 s, against the constant requested bit rate '
        f'of 4.3 Mbit/s. Bottom: the playout buffer grows while throughput exceeds the bit rate and drains otherwise; it '
        f'empties {fs["nstall"]} times, giving {fs["stall"]:.0f} seconds of stalling in total, marked in red.')
ax = Axes(s, 70, 15, 780, 120, (0, 130), (0, 8), ylabel='Mbit/s',
          xticks=[(v, '') for v in range(0, 131, 10)], yticks=[(v, str(v)) for v in (0, 2, 4, 6, 8)])
trace_line(ax, MUT, 2)
s.line(ax.px(0), ax.py(4.3), ax.px(130), ax.py(4.3), G, 2.5, dash=True)
s.text(ax.px(33), ax.py(4.3) + 20, 'requested bit rate 4.3 Mbit/s', 'small green', 'middle')
s.text(ax.px(22), ax.py(7.2), 'available throughput', 'small')
bx = Axes(s, 70, 180, 780, 130, (0, 130), (0, 16), xlabel='time (s)', ylabel='buffer (s)',
          xticks=[(v, str(v)) for v in range(0, 131, 10)], yticks=[(v, str(v)) for v in (0, 4, 8, 12, 16)])
for a, b in fx['stalls']:
    s.rect(bx.px(a), bx.py(16), bx.px(b) - bx.px(a), bx.py(0) - bx.py(16), RTINT, 'none')
s.polyline([(bx.px(t), bx.py(v)) for t, v in fx['buf'] if t <= 130], G, 2.5)
s.text(bx.px(fx['stalls'][0][0]) + 4, bx.py(14.5), 'stall', 'small bold')
s.text(440, 382, f'Each 4 s segment takes 4.3/C × 4 s to download: whenever C < 4.3 Mbit/s the buffer drains — here '
       f'{fs["nstall"]} stalls, {fs["stall"]:.0f} s in total.', 'small', 'middle')
s.save()

# --- BBA rate map ------------------------------------------------------------------------------
s = SVG(DECK, 'bba-map', 312, 'The rate map of a buffer-based ABR algorithm',
        f'Horizontal axis: buffer level from 0 to 30 seconds. Below a reservoir of {RESERVOIR:.0f} seconds the player '
        f'always requests the lowest rate; across a cushion of {CUSHION:.0f} seconds the target rate rises linearly to the '
        'highest rate; above it the highest rate is requested. The chosen ladder rung is the highest one below the line, '
        'so the request rate is a staircase.')
ax = Axes(s, 80, 20, 740, 210, (0, 30), (0, 6.5), xlabel='buffer level (s)', ylabel='requested rate (Mbit/s)',
          xticks=[(v, str(v)) for v in range(0, 31, 5)], yticks=[(r, f'{r:g}') for r in LADDER if r != 0.75])
s.rect(ax.px(0), ax.py(6.5), ax.px(RESERVOIR) - ax.px(0), ax.py(0) - ax.py(6.5), RTINT, 'none')
s.rect(ax.px(RESERVOIR + CUSHION), ax.py(6.5), ax.px(30) - ax.px(RESERVOIR + CUSHION), ax.py(0) - ax.py(6.5), TINT, 'none')
ax.curve(bba_rate, MUT, 1.5, n=300, dash=True)
pts, prev = [], None
for i in range(301):
    b = 30 * i / 300
    r = bba(b, [])
    if prev is not None and r != prev:
        pts.append((ax.px(b), ax.py(prev)))
    pts.append((ax.px(b), ax.py(r)))
    prev = r
s.polyline(pts, G, 3)
s.text(ax.px(RESERVOIR / 2), ax.py(5.9), 'reservoir', 'small bold', 'middle')
s.text(ax.px(RESERVOIR + CUSHION / 2), ax.py(5.9), 'cushion', 'small bold', 'middle')
s.text(ax.px(28), ax.py(5.9) + 30, 'upper', 'small bold', 'middle')
s.text(ax.px(RESERVOIR + CUSHION / 2) + 40, ax.py(2.2), 'rate map f(B)', 'small')
s.text(440, 302, 'The buffer level alone chooses the rate: no throughput estimate is needed while the buffer is in the cushion.',
       'small', 'middle')
s.save()

# --- Throughput-based vs buffer-based ABR on the same trace ---------------------------------
rb, bb = simulate(rate_based), simulate(bba)
rs, bs = summary(rb), summary(bb)
s = SVG(DECK, 'abr-compare', 392, 'A throughput-based and a buffer-based ABR algorithm on the same throughput trace',
        'Top: requested bit rate of a throughput-based algorithm, harmonic mean of the last five segments with a 15 percent '
        'margin, and of the buffer-based BBA-0 algorithm, over the same trace. Bottom: their buffer levels. The '
        f'throughput-based player starts at a high rate, is caught by the drop at 20 seconds and stalls {rs["nstall"]} times '
        f'for {rs["stall"]:.1f} seconds in total; the buffer-based player ramps up slowly, keeps its buffer, and never stalls, '
        f'at the cost of {bs["nsw"]} switches against {rs["nsw"]}.')
ax = Axes(s, 60, 15, 520, 130, (0, 130), (0, 8), ylabel='Mbit/s',
          xticks=[(v, '') for v in range(0, 131, 20)], yticks=[(v, str(v)) for v in (0, 2, 4, 6, 8)])
trace_line(ax, LINE, 1.5)
rate_steps(ax, rb, EKF, 2.5)
rate_steps(ax, bb, G, 2.5)
bx = Axes(s, 60, 185, 520, 130, (0, 130), (0, 32), xlabel='time (s)', ylabel='buffer (s)',
          xticks=[(v, str(v)) for v in range(0, 131, 20)], yticks=[(v, str(v)) for v in (0, 10, 20, 30)])
for a, b in rb['stalls']:
    s.rect(bx.px(a), bx.py(32), bx.px(b) - bx.px(a), bx.py(0) - bx.py(32), RTINT, 'none')
s.polyline([(bx.px(t), bx.py(v)) for t, v in rb['buf'] if t <= 130], EKF, 2)
s.polyline([(bx.px(t), bx.py(v)) for t, v in bb['buf'] if t <= 130], G, 2.5)
s.line(610, 30, 640, 30, EKF, 2.5)
s.text(648, 35, 'throughput-based', 'small')
s.line(610, 55, 640, 55, G, 2.5)
s.text(648, 60, 'buffer-based (BBA-0)', 'small')
s.line(610, 80, 640, 80, LINE, 1.5)
s.text(648, 85, 'available throughput', 'small')
s.text(610, 125, 'SESSION METRICS', 'label')
s.text(815, 150, 'rate', 'small bold', 'end')
s.text(870, 150, 'buffer', 'small bold', 'end')
rows = [('mean bit rate, Mbit/s', f'{rs["avg"]:.2f}', f'{bs["avg"]:.2f}'),
        ('bit-rate switches', f'{rs["nsw"]}', f'{bs["nsw"]}'),
        ('stalls', f'{rs["nstall"]}', f'{bs["nstall"]}'),
        ('stall time, s', f'{rs["stall"]:.1f}', f'{bs["stall"]:.1f}'),
        ('linear QoE', f'{rs["qoe"]:.0f}', f'{bs["qoe"]:.0f}')]
for k, (name, a, b) in enumerate(rows):
    y = 178 + k * 28
    s.text(610, y, name, 'small')
    s.text(815, y, a, 'bold', 'end')
    s.text(870, y, b, 'bold green', 'end')
s.text(440, 382, 'Same link, same ladder: the rule that picks the next segment decides whether the viewer ever sees a stall.',
       'small', 'middle')
s.save()

# --- Stalling and MOS: the exponential model of Hossfeld et al. --------------------------------
s = SVG(DECK, 'stall-mos', 312, 'Mean opinion score of a short video clip against the number of stalls',
        'The exponential model of Hossfeld et al. (2011) for 30-second clips, MOS = 3.5 exp(−(0.15 L + 0.19) N) + 1.5, where '
        'N is the number of stalls and L their length in seconds. Curves for L = 1, 3 and 5 seconds all fall steeply: already '
        'one or two stalls push the MOS from 5 towards 3, and the score saturates near 1.5.')
ax = Axes(s, 80, 15, 520, 220, (0, 6), (1, 5), xlabel='number of stalls N', ylabel='MOS',
          xticks=[(v, str(v)) for v in range(7)], yticks=[(v, str(v)) for v in range(1, 6)])
for L, color in [(1, G), (3, EKF), (5, FMT)]:
    ax.curve(lambda n, L=L: 3.5 * math.exp(-(0.15 * L + 0.19) * n) + 1.5, color, 2.5)
    s.line(640, 40 + [1, 3, 5].index(L) * 28, 670, 40 + [1, 3, 5].index(L) * 28, color, 2.5)
    s.text(678, 45 + [1, 3, 5].index(L) * 28, f'stall length L = {L} s', 'small')
s.text(640, 150, 'MOS = 3.5·exp(−(0.15 L + 0.19) N)', 'small bold')
s.text(640, 170, '        + 1.5', 'small bold')
s.text(640, 196, '30 s clips, crowdsourced', 'small')
s.text(640, 216, '(Hoßfeld et al., QoMEX 2011)', 'small')
s.text(440, 302, 'Number of stalls matters more than their length: a single 1 s stall already costs about one MOS point.',
       'small', 'middle')
s.save()

# =============================================================================
# 09 — Software-defined networking with OpenFlow, and VXLAN-EVPN for comparison
# =============================================================================
DECK = '09'


# --- Traditional (distributed) control vs SDN (logically centralized) --------------------
s = SVG(DECK, 'planes', 300, 'Distributed control in a traditional network and logically centralized control in SDN',
        'Left: three traditional devices, each containing its own control plane and data plane; the control planes '
        'talk to each other through distributed routing protocols such as OSPF, BGP or spanning tree. Right: three '
        'SDN switches that keep only the data plane; one logically centralized controller above them computes the '
        'forwarding state and installs it into every switch over OpenFlow.')
s.text(210, 22, 'TRADITIONAL — DISTRIBUTED CONTROL', 'label', 'middle')
s.text(670, 22, 'SDN — LOGICALLY CENTRALIZED CONTROL', 'label', 'middle')
s.line(440, 10, 440, 230, GRID, 1.5)
for k in range(3):
    x = 25 + k * 130
    cell(x, 110, 110, 50, 'control', fill=TINT3)
    cell(x, 160, 110, 50, 'data', fill=TINT)
    if k < 2:
        s.line(x + 110, 185, x + 130, 185, INK, 2)
        s.path(f'M{x + 55},110 Q{x + 120},62 {x + 185},110', MUT, 1.5, dash=True)
s.text(210, 66, 'routing protocols (OSPF, BGP, STP)', 'small', 'middle')
cell(560, 40, 220, 55, 'Controller', 'network OS + applications', TINT3)
for k in range(3):
    x = 485 + k * 130
    cell(x, 160, 110, 50, 'data', fill=TINT)
    s.line(670, 95, x + 55, 158, G, 2, arrow='green')
    if k < 2:
        s.line(x + 110, 185, x + 130, 185, INK, 2)
s.text(700, 135, 'OpenFlow', 'small green')
s.text(440, 262, 'Traditional: every box decides for itself and the network state is the sum of many local views.',
       'small', 'middle')
s.text(440, 282, 'SDN: switches only forward; one program with a global view decides for all of them.', 'small', 'middle')
s.save()

# --- The layered SDN architecture and its interfaces --------------------------------------
s = SVG(DECK, 'architecture', 340, 'The three planes of an SDN architecture and the interfaces between them',
        'Top: the application plane with routing, traffic engineering and security or QoS policy applications. '
        'They talk to the control plane through the northbound API, typically REST or gRPC, which is not '
        'standardized. The control plane consists of two controller instances synchronized over an east-west '
        'interface. It programs the data plane, five interconnected switches, through the southbound API such as '
        'OpenFlow, P4Runtime, NETCONF or OVSDB.')
for y, h in [(10, 70), (120, 70), (230, 70)]:
    s.rect(190, y, 670, h, NEUTRAL, LINE)
for k, name in enumerate(['Routing', 'Traffic engineering', 'Security / QoS policy']):
    cell(210 + k * 215, 22, 200, 46, name, fill=PAPER)
for x in (310, 525, 740):
    s.line(x, 80, x, 118, G, 2, arrow='green')
cell(230, 130, 220, 50, 'Controller instance 1', fill=TINT3)
cell(590, 130, 220, 50, 'Controller instance 2', fill=TINT3)
s.line(450, 155, 590, 155, MUT, 1.5, dash=True)
s.text(520, 148, 'east–west', 'small', 'middle')
for k in range(5):
    x = 215 + k * 130
    cell(x, 245, 90, 40, f's{k + 1}', fill=TINT)
    s.line(x + 45, 190, x + 45, 243, G, 2, arrow='green')
    if k < 4:
        s.line(x + 90, 265, x + 130, 265, INK, 2)
for y, lines, cls in [(40, ['APPLICATION', 'PLANE'], 'label'), (150, ['CONTROL', 'PLANE'], 'label'),
                      (260, ['DATA', 'PLANE'], 'label'), (96, ['northbound API', 'REST, gRPC'], 'small'),
                      (206, ['southbound API', 'OpenFlow, P4Runtime'], 'small')]:
    for j, t in enumerate(lines):
        s.text(20, y + j * 19, t, cls)
s.text(440, 328, 'Only the southbound side has a widely adopted standard; each controller defines its own northbound API.',
       'small', 'middle')
s.save()

# --- Components of an OpenFlow switch -------------------------------------------------------
s = SVG(DECK, 'openflow-switch', 345, 'Main components of an OpenFlow logical switch',
        'An external controller connects to the switch over the OpenFlow channel, a TCP connection optionally '
        'secured with TLS. Inside the switch, the OpenFlow channel agent installs entries into a pipeline of flow '
        'tables numbered 0 to n. A packet enters on an ingress port, passes through the tables, and leaves on an '
        'egress port. Flow entries can refer to a group table, for multicast, load sharing and fast failover, and '
        'to a meter table, for per-flow rate limiting.')
cell(340, 10, 200, 50, 'Controller', fill=TINT3)
s.line(440, 60, 440, 103, G, 2.5)
s.text(452, 88, 'OpenFlow protocol · TCP 6653, optional TLS', 'small')
s.rect(60, 103, 760, 200, PAPER, INK, 1.5)
s.text(75, 126, 'OPENFLOW SWITCH', 'label')
cell(340, 113, 200, 40, 'OpenFlow channel', fill=NEUTRAL)
tables = [(110, 'Flow table 0'), (260, 'Flow table 1'), (450, 'Flow table n')]
for x, name in tables:
    cell(x, 175, 120, 50, name, fill=TINT)
    s.line(440, 153, x + 60, 173, MUT, 1.2, dash=True)
s.line(230, 200, 258, 200, G, 2, arrow='green')
s.line(380, 200, 400, 200, G, 2)
s.text(415, 206, '…', 'bold', 'middle')
s.line(428, 200, 448, 200, G, 2, arrow='green')
cell(260, 250, 150, 40, 'Group table', fill=CTINT)
cell(450, 250, 150, 40, 'Meter table', fill=CTINT)
s.line(335, 225, 335, 248, MUT, 1.5, arrow='muted')
s.line(525, 225, 525, 248, MUT, 1.5, arrow='muted')
s.line(15, 200, 108, 200, INK, 2, arrow='ink')
s.text(20, 190, 'ingress port', 'small')
s.line(570, 200, 865, 200, INK, 2, arrow='ink')
s.text(860, 190, 'egress port', 'small', 'end')
s.text(715, 240, 'filled by the', 'small', 'middle')
s.text(715, 259, 'controller via Flow-Mod,', 'small', 'middle')
s.text(715, 278, 'Group-Mod, Meter-Mod', 'small', 'middle')
s.text(440, 333, 'The switch hardware stays closed; only the tables and the channel that fills them are standardized.',
       'small', 'middle')
s.save()

# --- Anatomy of one flow entry --------------------------------------------------------------
s = SVG(DECK, 'flow-entry', 210, 'The fields of one OpenFlow 1.3 flow entry, with an example',
        'A flow entry has seven parts: match fields, priority, counters, instructions, timeouts, cookie and flags. '
        'The example matches IPv4 packets from port 1 to 10.0.0.2 marked DSCP 46, has priority 100, counts packets, '
        'bytes and duration, applies output to port 2 through meter 1, expires after 10 seconds without a match, '
        'carries a controller cookie and asks the switch to report its removal.')
fields = [(215, 'Match fields', TINT3, ['in_port=1, eth_type=0x0800,', 'ip_dst=10.0.0.2, ip_dscp=46']),
          (85, 'Priority', TINT, ['100', 'highest wins']),
          (105, 'Counters', TINT, ['packets, bytes,', 'duration']),
          (140, 'Instructions', TINT3, ['meter:1,', 'apply: output:2']),
          (115, 'Timeouts', TINT, ['idle 10 s,', 'hard 0 (none)']),
          (100, 'Cookie', TINT, ['opaque tag', 'of controller']),
          (80, 'Flags', TINT, ['notify on', 'removal'])]
s.text(20, 25, 'ONE FLOW ENTRY — OPENFLOW 1.3', 'label')
x = 20
for w, name, fill, ex in fields:
    cell(x, 40, w, 50, name, fill=fill)
    for j, t in enumerate(ex):
        s.text(x + w / 2, 115 + j * 20, t, 'small', 'middle')
    x += w
s.text(440, 180, 'Match fields and priority identify the entry; a packet is handled by the highest-priority entry it matches.',
       'small', 'middle')
s.text(440, 200, 'The table-miss entry wildcards every field at priority 0: send to controller, drop, or go to a later table.',
       'small', 'middle')
s.save()

# --- Multi-table pipeline processing -----------------------------------------------------
s = SVG(DECK, 'pipeline', 285, 'Pipeline processing across several flow tables',
        'A packet enters table 0. Each matching entry executes instructions: Apply-Actions changes the packet at '
        'once, Write-Actions adds actions to an action set that travels with the packet, and Goto-Table sends it '
        'to a later table, never an earlier one, for example directly from table 0 to table n. When an entry has no '
        'Goto-Table instruction, processing stops and the accumulated action set is executed, typically ending in '
        'output to an egress port.')
s.text(20, 121, 'packet in', 'small')
s.line(20, 130, 98, 130, INK, 2, arrow='ink')
for x, name in [(100, 'Table 0'), (250, 'Table 1'), (430, 'Table n')]:
    s.box(x, 95, 120, 70, name, 'match → instr.')
s.line(220, 130, 248, 130, G, 2, arrow='green')
s.line(370, 130, 388, 130, G, 2)
s.text(405, 136, '…', 'bold', 'middle')
s.line(412, 130, 428, 130, G, 2, arrow='green')
cell(600, 95, 160, 70, 'Execute', 'action set', TINT3)
s.line(550, 130, 598, 130, G, 2, arrow='green')
s.line(760, 130, 862, 130, INK, 2, arrow='ink')
s.text(860, 121, 'packet out', 'small', 'end')
s.path('M160,95 Q325,20 490,93', G, 2, dash=True, arrow='green')
s.text(325, 42, 'Goto-Table: forward only, tables may be skipped', 'small', 'middle')
s.rect(100, 190, 660, 36, NEUTRAL, LINE)
s.text(430, 213, 'action set + metadata travel with the packet from table to table', 'small', 'middle')
for x in (160, 310, 490, 680):
    s.line(x, 165, x, 190, MUT, 1.2, dash=True)
s.text(440, 255, 'Apply-Actions modifies the packet immediately; Write-Actions and Clear-Actions edit the action set,',
       'small', 'middle')
s.text(440, 275, 'which is executed once, when an entry without Goto-Table ends the pipeline.', 'small', 'middle')
s.save()

# --- Reactive flow set-up: the first packet visits the controller ----------------------------
s = SVG(DECK, 'reactive-setup', 330, 'Reactive flow installation: the first packet of a flow visits the controller',
        'A sequence diagram with four participants: host h1, switch s1, the controller and host h2. Packet 1 from h1 '
        'misses in the flow table, so s1 sends a Packet-In to the controller. The controller answers with a Flow-Mod '
        'that installs a forwarding entry and a Packet-Out that releases packet 1, which s1 forwards to h2. Packet 2 '
        'matches the new entry and is forwarded directly by the switch without involving the controller.')
cols = {'h1': 110, 's1': 340, 'ctl': 570, 'h2': 790}
for key, name in [('h1', 'Host h1'), ('s1', 'Switch s1'), ('ctl', 'Controller'), ('h2', 'Host h2')]:
    cell(cols[key] - 70, 8, 140, 36, name, fill=TINT3 if key in ('s1', 'ctl') else NEUTRAL)
    s.line(cols[key], 44, cols[key], 300, LINE, 1.5, dash=True)


def msg(a, b, y, label, color=G, marker='green'):
    s.line(cols[a], y, cols[b] + (-2 if cols[b] > cols[a] else 2), y, color, 2, arrow=marker)
    s.text((cols[a] + cols[b]) / 2, y - 7, label, 'small', 'middle')


msg('h1', 's1', 80, 'packet 1', INK, 'ink')
s.text(352, 102, 'table miss', 'small bold')
msg('s1', 'ctl', 128, 'Packet-In (headers, buffer id)')
msg('ctl', 's1', 165, 'Flow-Mod (match → output:2)')
msg('ctl', 's1', 200, 'Packet-Out (packet 1)')
msg('s1', 'h2', 235, 'packet 1', INK, 'ink')
msg('h1', 's1', 275, 'packet 2', INK, 'ink')
s.line(340, 285, 788, 285, INK, 2, arrow='ink')
s.text(565, 280, 'packet 2 — matches the new entry', 'small', 'middle')
s.line(600, 128, 600, 200, FMT, 1.5)
s.line(594, 128, 606, 128, FMT, 1.5)
s.line(594, 200, 606, 200, FMT, 1.5)
s.text(612, 169, 'flow set-up delay', 'small')
s.text(440, 322, 'Only the first packet of a flow pays for the controller round trip; the rest stay in the data plane.',
       'small', 'middle')
s.save()

# --- VXLAN encapsulation ----------------------------------------------------------------------
s = SVG(DECK, 'vxlan-frame', 255, 'VXLAN encapsulation of an Ethernet frame',
        'The ingress VTEP prepends 50 bytes to the tenant Ethernet frame: an outer Ethernet header of 14 bytes, an '
        'outer IPv4 header of 20 bytes, an outer UDP header of 8 bytes with destination port 4789, and an 8-byte '
        'VXLAN header. The VXLAN header holds 8 bits of flags, 24 reserved bits, a 24-bit VXLAN network identifier '
        'and 8 reserved bits.')
row = [(105, 'Outer Eth', '14 B', TINT), (110, 'Outer IPv4', '20 B', TINT), (105, 'Outer UDP', '8 B', TINT),
       (90, 'VXLAN', '8 B', TINT3), (330, 'Inner Ethernet frame', 'tenant MAC, VLAN, IP, payload', PAPER),
       (50, 'FCS', '', NEUTRAL)]
x = 45
for w, name, sub, fill in row:
    cell(x, 50, w, 50, name, sub, fill)
    x += w
s.line(45, 38, 455, 38, MUT, 1.5)
s.line(45, 38, 45, 30, MUT, 1.5)
s.line(455, 38, 455, 30, MUT, 1.5)
s.text(250, 24, 'added by the ingress VTEP — 50 B for IPv4', 'bold', 'middle')
s.line(365, 100, 240, 140, MUT, 1.2, dash=True)
s.line(455, 100, 640, 140, MUT, 1.2, dash=True)
x = 240
for w, name in [(50, 'Flags'), (150, 'Reserved (24)'), (150, 'VNI (24 bit)'), (50, 'Rsvd')]:
    cell(x, 140, w, 40, name, fill=TINT3 if 'VNI' in name else PAPER)
    x += w
s.text(440, 218, 'Outer UDP destination port 4789; the source port is a hash of the inner headers, so underlay ECMP',
       'small', 'middle')
s.text(440, 238, 'spreads tenant flows. A 24-bit VNI gives about 16.7 million segments, against 4094 usable VLAN IDs.',
       'small', 'middle')
s.save()

# --- Where the control plane lives: OpenFlow vs VXLAN-EVPN ----------------------------------
s = SVG(DECK, 'control-placement', 355, 'Centralized control with OpenFlow and distributed control with BGP EVPN',
        'Left: one logically centralized controller cluster pushes flow entries into four switches. Right: a '
        'leaf-spine fabric; two spine switches act as BGP route reflectors and four leaf switches act as VXLAN '
        'tunnel endpoints. Every leaf runs BGP and learns MAC and IP routes from the others through the route '
        'reflectors; tenant traffic between two leaves is carried in a VXLAN tunnel across the IP underlay.')
s.text(220, 22, 'OPENFLOW — CENTRAL CONTROLLER', 'label', 'middle')
s.text(660, 22, 'VXLAN-EVPN — DISTRIBUTED BGP', 'label', 'middle')
s.line(440, 10, 440, 290, GRID, 1.5)
cell(110, 45, 220, 55, 'SDN controller', 'cluster, global view', TINT3)
for k in range(4):
    x = 30 + k * 100
    cell(x, 200, 80, 40, f's{k + 1}', fill=TINT)
    s.line(220, 100, x + 40, 198, G, 2, arrow='green')
    if k < 3:
        s.line(x + 80, 220, x + 100, 220, INK, 2)
s.text(220, 270, 'flow entries pushed into each switch', 'small', 'middle')
spines = [(545, 'Spine 1'), (675, 'Spine 2')]
leaves = [470 + k * 100 for k in range(4)]
for lx in leaves:
    for sx, _ in spines:
        s.line(lx + 40, 200, sx + 60, 100, LINE, 1.5)
for sx, name in spines:
    cell(sx, 55, 120, 45, name, 'BGP route refl.', TINT3)
for k, lx in enumerate(leaves):
    cell(lx, 200, 80, 40, f'Leaf {k + 1}', fill=TINT)
s.path(f'M{leaves[0] + 40},240 Q{(leaves[0] + leaves[3]) / 2 + 40},305 {leaves[3] + 40},240', C, 3, dash=True)
s.text(660, 292, 'VXLAN tunnel between VTEPs', 'small', 'middle')
s.rect(582, 136, 156, 22, PAPER, 'none')
s.text(660, 152, 'EVPN routes over iBGP', 'small', 'middle')
s.text(440, 322, 'OpenFlow: one program computes state for every switch. EVPN: every leaf computes its own state from',
       'small', 'middle')
s.text(440, 340, 'routes its peers advertise — the control plane is standardized and distributed, as in any IP network.',
       'small', 'middle')
s.save()

print(f'{THEME} figures written to {FIGURES}')
