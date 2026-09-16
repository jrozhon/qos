#!/usr/bin/env python3
"""Generate the lecture figures as self-contained SVGs (standard library only).

Each deck has one section below; its figures land in ``public/figures/<deck>/``.
The SVGs embed Carlito so the built site and the PDF export render identically,
and they follow VSB-STYLE.md: brand green, FEI cyan as a small accent only,
hard-edged boxes, one CSS pixel per SVG unit on the 980 x 552 slide canvas.

Run from anywhere::

    python3 scripts/generate-figures.py
"""
from __future__ import annotations

import base64
import math
import random
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / 'public' / 'figures'

# Palette — VSB-STYLE.md §1 and §6. Cyan never carries text (R5).
G, D, C, INK, MUT, TINT, LINE, GRID = (
    '#00A499', '#00736B', '#05C3DE', '#1A1A1A', '#5A6664', '#EBF8F7', '#BCCFCD', '#E6ECEB')
FMT, EKF, FBI = '#E4002B', '#0047BB', '#FF8200'  # other faculty colours, chart series only (R26)

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
        self.rect(0, 0, w, h, '#FFFFFF', 'none')

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
        (out / f'{self.name}.svg').write_text('\n'.join(self.parts + ['</svg>']) + '\n')


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
blocks = [('Source', 'message', '#F6F8F8'), ('Transmitter', 'encodes into a signal', TINT),
          ('Channel', 'bandwidth B', TINT), ('Receiver', 'decodes the signal', TINT), ('Destination', 'message', '#F6F8F8')]
x = 20
for i, (t, sub, fill) in enumerate(blocks):
    w = 130 if i in (0, 4) else 160
    s.box(x, 72, w, 64, t, sub, fill)
    if i < 4:
        s.line(x + w, 104, x + w + 20, 104, INK, 2, arrow='ink')
    x += w + 20
# Noise sits centred above the channel (x = 350, w = 160) and enters it from the top.
s.box(350, 6, 160, 34, 'Noise', '', '#FFFFFF')
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
    s.rect(x0, y0, w, 60, '#FFFFFF', LINE)
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
    s.rect(bx, by, bw, band_h, '#FFFFFF', chan[i], 2)
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
    s.rect(sx, slot_y, slot_w, slot_h, '#FFFFFF', chan[ch], 2)
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
    s.rect(lx, 262, 14, 14, '#FFFFFF', chan[i], 2)
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
s.box(x0, 68, 220, 64, 'Queue', 'waiting, Lq', '#F6F8F8')
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
s.rect(430, 12, 18, 18, '#E8F9FC', C, 2)
s.text(456, 26, 'Variable — traffic-dependent', 'small')
segments = [('Codec', 55, True), ('Serialization', 45, True), ('Propagation', 100, True),
            ('Queuing', 140, False), ('Forwarding', 35, False), ('Shaping', 85, False)]
total_w = sum(w for _, w, _ in segments)
cursor, bar_y, bar_h = (880 - total_w) // 2, 110, 60  # centre the bar itself in the 880-wide canvas
for i, (name, w, fixed) in enumerate(segments):
    fill, stroke = (TINT, G) if fixed else ('#E8F9FC', C)
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
s.rect(252, 40, 300, 170, '#FFFFFF', INK, 1.5)
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
s.rect(160, 30, 240, 210, '#FFFFFF', INK, 1.5)
s.text(280, 20, 'TOKEN BUCKET', 'label', 'middle')
s.rect(185, 70, 90, 140, '#FFFFFF', INK, 1.5)
token_cols = [192, 228]
token_rows = [185, 163, 141, 119]
for ri, ty in enumerate(token_rows):
    fill = TINT if ri < 3 else '#FFFFFF'
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
s.rect(470, 140, 330, 70, '#E8F9FC', C, 2)
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
cursor = timeline_block(cursor, 45, 100, 55, '#E8F9FC', C, 'Small', '200 B')
s.line(cursor + 10, 72, cursor + 50, 72, INK, 2, arrow='ink')
s.text(cursor + 58, 77, 'link', 'small')
span_bracket(80 + ox, 400 + ox, 120, 'the urgent packet waits for the whole 1500 B packet')

s.text(80 + ox, 165, 'WITH LFI (FRAGMENTATION + INTERLEAVING)', 'label')
cursor = timeline_block(80 + ox, 185, 100, 55, TINT, G, 'F1')
cursor = timeline_block(cursor, 185, 100, 55, '#E8F9FC', C, 'Small', '200 B')
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
cell_row(x0, 60, [(3 * cw, TINT), (4 * cw, '#F3F6F5'), (cw, '#FFFFFF')])
span_above(x0, x0 + 3 * cw, 60, 'IP Precedence (3 bits)')
span_above(x0 + 3 * cw, x0 + 7 * cw, 60, 'ToS bits (4 bits)')
span_above(x0 + 7 * cw, x0 + 8 * cw, 60, 'Unused')

s.text(440, 145, 'Same 8 bits, reinterpreted:', 'small', 'middle')

s.text(x0, 185, 'DS FIELD — DIFFSERV (RFC 2474)', 'label')
cell_row(x0, 220, [(6 * cw, TINT), (2 * cw, '#F3F6F5')])
span_above(x0, x0 + 6 * cw, 220, 'DSCP (6 bits)')
span_above(x0 + 6 * cw, x0 + 8 * cw, 220, 'ECN (2 bits)')

s.text(440, 290, 'Class-selector codepoints (000xxx) preserve IP Precedence’s ordering; DSCP adds finer-grained', 'small', 'middle')
s.text(440, 308, 'per-hop behaviors: EF = 101110 (voice, RFC 3246) · AF41 = 100010 (video, RFC 2597) · default = 000000.', 'small', 'middle')
s.save()

# =============================================================================
# 04 — Network traffic modelling: distributions and self-similarity
# =============================================================================
# The five Markov loss-model state diagrams for this deck (Bernoulli, Simple Gilbert, Gilbert,
# Gilbert-Elliott, four-state) are NOT generated here — hand-rolled SVG bezier math could not match
# matplotlib's FancyArrowPatch (auto node-edge clipping via patchA/patchB, properly weighted arc3
# curves). They live in generate-markov-figures.py instead; run both scripts to regenerate the deck.
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

print(f'Figures written to {FIGURES}')
