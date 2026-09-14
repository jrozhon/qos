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
            for n, c in [('green', G), ('ink', INK), ('cyan', C), ('muted', MUT)])
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
            svg.text(x0 - 8, y0 - 12, ylabel, 'small', 'start')

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
s.text(440, 244, 'R_raw = Rₛ · log₂ M   —   raw bit rate = symbol rate × bits per symbol', 'big', 'middle')
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

print(f'Figures written to {FIGURES}')
