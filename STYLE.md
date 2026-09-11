# Style Guide — QoS & QoE Course

This document is the single source of truth for the visual and written style of this repository. It is written for AI agents and human contributors alike. Follow it when editing any README, notebook, figure, or library module. When this guide and existing content disagree, the guide wins and the content should be brought into line.

Source: *Manuál jednotného vizuálního stylu VŠB-TUO* (2023 edition, Czech; kept locally as `manual.pdf`, which is git-ignored — the tables below are self-sufficient). Section numbers below refer to that manual. Where the manual is silent (Markdown, notebooks, matplotlib), the rules here are derived from it and from the course's existing conventions.

---

## 1. Identity

| Item | Value |
|---|---|
| University (EN) | VSB – Technical University of Ostrava (spaced en dash) |
| University (CZ) | VŠB – Technická univerzita Ostrava |
| Short form | VSB-TUO (hyphen, no spaces) |
| Faculty | Faculty of Electrical Engineering and Computer Science (FEECS; Czech abbreviation FEI) |
| Course | Quality of Service and Quality of Experience (QoS & QoE) |
| Language of all material | English. Czech only in proper names. |
| Symbol | `logo.png` — five vertical bars in university teal (the "znak"), used as a figure watermark. Never recolour, stretch, or place on a background darker than a 30 % tint (manual §1.5). |

> Assumption: the course is delivered by a department of FEECS, so FEECS cyan is the faculty accent (manual §2.3: level III inherits level II). Change §2.2 below if that is wrong.

---

## 2. Colour (manual §2)

All values are the manual's HEX/RGB definitions for screen use. Do not introduce colours outside this table without a stated reason.

### 2.1 Core

| Role | Name | HEX | RGB | Pantone |
|---|---|---|---|---|
| **Primary** | University teal | `#00A499` | 0 164 153 | 3272 C |
| Ink | Black | `#000000` | 0 0 0 | Process Black C |
| Paper | White | `#FFFFFF` | 255 255 255 | — |
| Ceremonial (rarely used) | Silver | `#8A8D8F` | 138 141 143 | 877 C |

### 2.2 Faculty and institute colours (level II)

| Unit | HEX | RGB | Pantone |
|---|---|---|---|
| Mining and Geology (HGF) | `#43B02A` | 67 176 42 | 361 C |
| Materials Science and Technology (FMT) | `#E4002B` | 228 0 43 | 185 C |
| Mechanical Engineering (FS) | `#FFB81C` | 255 184 28 | 1235 C |
| Economics (EkF) | `#0047BB` | 0 71 187 | 2728 C |
| **Electrical Engineering and Computer Science (FEI/FEECS) — course accent** | `#05C3DE` | 5 195 222 | 311 C |
| Civil Engineering (FAST) | `#8246AF` | 130 70 175 | 2587 C |
| Safety Engineering (FBI) | `#FF8200` | 255 130 0 | 151 C |
| Energy and Environmental Technology Centre (CEET) | `#A28E2A` | 162 142 42 | 456 C |
| IT4Innovations | `#818386` | 129 131 134 | — |

### 2.3 Tints

The manual allows tints of the identity colours (§1.5). Use them for fills, backgrounds, and admonition boxes; never for text.

| Base | 10 % | 20 % | 30 % | 50 % |
|---|---|---|---|---|
| Teal `#00A499` | `#E6F6F5` | `#CCEDEB` | `#B2E4E0` | `#80D2CC` |
| FEECS cyan `#05C3DE` | `#E6F9FC` | `#CDF3F8` | `#B4EDF5` | `#82E1EE` |
| Grey `#818386` | `#F2F3F3` | `#E6E6E7` | `#D9DADB` | `#C0C1C2` |

### 2.4 Semantic roles in course material

| Purpose | Colour |
|---|---|
| Body text, axis labels, tick labels | `#292929` (near-black; softer on screen than pure black, established in `params.py`) |
| Headings in rendered HTML / figures titles | `#000000` or `#292929` — never coloured |
| Primary data series, highlight, links | Teal `#00A499` |
| Secondary highlight (course accent) | FEECS cyan `#05C3DE` |
| Gridlines, borders, disabled | `#E5E5E5` (existing) or grey tints above |
| Neutral card / box background | `#F2F3F3` |
| Warning / error emphasis | FMT red `#E4002B` — only when meaning "wrong/loss/error" |

### 2.5 Categorical series order for charts

Keep this order; it is already in `lib/params.py` and existing figures depend on it.

```python
colors = [
    "#00A499",  # 0 teal      – primary
    "#43B02A",  # 1 green
    "#E4002B",  # 2 red
    "#FFB81C",  # 3 yellow
    "#0047BB",  # 4 blue
    "#05C3DE",  # 5 cyan      – FEECS
    "#8246AF",  # 6 purple
    "#FF8200",  # 7 orange
]
```

Rules:
- One series → `colors[0]`. Two series → `colors[0]` and `colors[4]` (teal/blue — safe for red–green colour-vision deficiency). Avoid pairing `colors[1]` with `colors[2]` as the *only* distinction.
- Yellow `#FFB81C` fails contrast on white; use it for filled areas or markers, never for lines thinner than 3 pt or for text.
- Do not use colour as the only encoding: vary line style or markers as well when there are more than three series.
- Neutral references (theory curves, bounds) in grey `#818386`, dashed.

---

## 3. Typography (manual §3)

| Manual role | Official font | Substitute (licensed) | Open substitute used here |
|---|---|---|---|
| Body text | Drive (humanist sans) | Calibri | **Carlito** (metric-compatible with Calibri) |
| Headings, short labels | Drive Mono (monospace) | Calibri Bold | **Carlito Bold**; monospace `DejaVu Sans Mono` only for code |
| Code | — | — | Default monospace of the renderer |

Never set running text in a monospace face (manual §3.4). Never mix in other sans-serif families for effect.

Reference size/leading pairs from the manual (pt): body 14/18, 10/14, 8/12; headings 30/33, 24/29, 18/24, 14/21, all bold. In figures this maps to: title 26 pt bold left-aligned, axis labels 17 pt bold, tick and legend text 15 pt (values already in `rc_params`).

Font stack for anything that renders on a machine we do not control:

```
"Carlito", "Calibri", "Liberation Sans", "DejaVu Sans", "Arial", sans-serif
```

Carlito is packaged as `fonts-crosextra-carlito` (Debian/Ubuntu), `ttf-carlito` (Arch), `google-crosextra-carlito-fonts` (Fedora). If it is absent, matplotlib falls back silently — check `fc-list | grep -i carlito` before regenerating committed figures.

---

## 4. Written material

Applies to every `README.md` and every Markdown cell in notebooks.

### 4.1 Voice and register

- Academic, third person or impersonal ("The signal is sampled…", "Consider a channel…"). Second person is acceptable in task instructions ("Implement…", "Compare…").
- Precise and economical. Prefer a short sentence with a defined term over a long explanatory one. Define every abbreviation on first use: "Quality of Service (QoS)".
- No emoji, no exclamation marks, no marketing tone ("lightning-fast", "a breeze"). The root `README.md` currently violates this and should be rewritten.
- British or American spelling is acceptable but must be consistent within a file; existing files are predominantly American — use American.
- Numbers with units use a non-breaking space and SI symbols: `8 kHz`, `20 ms`, `64 kbit/s`. Bits per second is `bit/s`, never `bps` in prose; `Mb/s` and `MB/s` must not be confused.
- Terminology is fixed: *QoS*, *QoE*, *M/M/1*, *PCM*, *RTP*, *inter-arrival time*, *packet loss* (not "packet drop" unless describing a queue action), *delay* (not "latency" unless it is the one-way network latency specifically), *jitter*.

### 4.2 Lesson README structure

Every `qos-NN/README.md` follows this skeleton. Headings are sentence case. Do not skip levels.

```markdown
# Exercise NN – Topic Title

One-paragraph abstract: what the exercise covers and what the student will be able to do afterwards.

## Learning objectives
- …

## Theory
### Subtopic
Prose, equations, figures.

## Exercise
### Preparation
Environment, commands, credentials pointer (never the credentials themselves).
### Step 1 – …
### Step 2 – …

## Questions
1. …

## References
1. Author, *Title*, Publisher, Year. / URL
```

- The H1 uses a spaced en dash: `# Exercise 03 – Network traffic and QoE`.
- Two-digit exercise numbers everywhere: `Exercise 01`, directory `qos-01`, notebook `exercise_01.ipynb`.
- Wikipedia may be cited as a reference but must not be pasted as an excerpt; paraphrase and cite.
- Shell commands go in fenced `bash` blocks with a one-line explanation before, not after. Placeholders in capitals: `DEVICE`, `X.X`. Do not embed terminal prompts (`$`) inside the block.
- Callouts use GitHub alerts, one per idea:

  ```markdown
  > [!NOTE]
  > Superuser privileges are required for `tc`.
  ```
  Use `[!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`. Do not use `:information_source:` or other shortcode icons.

### 4.3 Mathematics

- Display equations as a block with each `$$` delimiter on its own line and a blank line before and after — Typora ignores single-line `$$ … $$`; GitHub accepts both. Inline math in `$ … $` (Typora needs *Inline Math* enabled in its preferences). GitHub's renderer is fragile: no `\begin{align}` without `$$` around it, no `\text{}` with special characters, escape underscores outside math.
- Every display equation is followed by a "where" list defining each symbol with its unit in square brackets:

  ```markdown
  $$
  C = B \log_2 \left(1 + \frac{S}{N}\right)
  $$

  where $C$ is the channel capacity [bit/s], $B$ the bandwidth [Hz], and $S/N$ the linear signal-to-noise ratio [–].
  ```
- Units in square brackets, dimensionless as `[–]` (en dash), matching axis labels in figures.
- Use the same symbol for the same quantity across all lessons: $\lambda$ arrival rate, $\mu$ service rate, $S = 1/\mu$ mean service time, $A$ offered traffic [erl], $\rho$ utilization, $L$ / $L_q$ mean number in system / in queue, $W$ / $W_q$ mean time in system / in queue, $B$ bandwidth, $C$ channel capacity, $S/N$ signal-to-noise ratio, $f_s$ sampling frequency, $\sigma$ standard deviation.

### 4.4 Images in READMEs

- Stored in `qos-NN/fig/`, PNG, lowercase snake_case names describing content (`exponential_pdf.png`, not `fig1.png`).
- Referenced with a relative path and a meaningful alt text: `![Exponential distribution PDF](fig/exponential_pdf.png)`.
- Generated figures are produced by code that lives in the lesson (notebook or `lib/`), following §5, so they can be regenerated.
- Diagrams (topologies, block schemes) are hand-written SVG, not raster exports, so they can be edited in place. Conventions, as in `qos-05/fig/`: hosts `fill #E6F6F5 / stroke #00A499`, switches `fill #E6F9FC / stroke #05C3DE` with `rx 8`, controllers and other infrastructure `fill #F2F3F3 / stroke #818386`; data links solid `#292929` 2.5 px, control links dashed `#818386`; node names 18 px bold centred, secondary text 14 px, annotations 14 px in `#818386`; the §3 font stack on the root element; a `<title>` describing the diagram. No drop shadows, gradients, or icons.

---

## 5. Figures

### 5.1 matplotlib

Every lesson's `lib/params.py` must be byte-identical. Target content (the current files differ only in the font stack and the three `lines.linewidth`/`savefig.*` keys):

```python
textcolor = "#292929"

rc_params = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Carlito", "Calibri", "Liberation Sans", "DejaVu Sans", "Arial", "sans-serif"],
    "text.color": textcolor,
    "axes.labelcolor": textcolor,
    "xtick.color": textcolor,
    "ytick.color": textcolor,
    "figure.facecolor": "#ffffff",
    "axes.facecolor": "#ffffff",
    "savefig.facecolor": "#ffffff",
    "axes.titlesize": 26,
    "axes.titlelocation": "left",
    "axes.titleweight": "bold",
    "axes.titlepad": 20,
    "axes.labelsize": 17,
    "axes.labelweight": "bold",
    "axes.labelpad": 8,
    "xaxis.labellocation": "right",
    "yaxis.labellocation": "top",
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "xtick.minor.size": 0,
    "ytick.minor.size": 0,
    "axes.linewidth": 0,
    "axes.axisbelow": True,
    "axes.grid": True,
    "grid.linestyle": "--",
    "grid.linewidth": 1.3,
    "grid.color": "#e5e5e5",
    "legend.frameon": False,
    "legend.numpoints": 1,
    "legend.scatterpoints": 1,
    "legend.loc": "center right",
    "legend.fontsize": 15,
    "legend.title_fontsize": 15,
    "legend.markerscale": 1.3,
    "lines.solid_capstyle": "round",
    "lines.linewidth": 3,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
}

colors = [
    "#00A499", "#43B02A", "#E4002B", "#FFB81C",
    "#0047BB", "#05C3DE", "#8246AF", "#FF8200",
]


def add_logo(fig, path="logo.png", box=(0.83, 0.90, 0.10, 0.10)):
    """
    Place the university symbol in the top-right corner of a figure.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure to decorate.
    path : str, optional
        Image file, by default "logo.png" in the notebook directory.
    box : tuple[float, float, float, float], optional
        (x, y, width, height) of the logo axes in figure coordinates.
    """
    import matplotlib.image as image

    ax = fig.add_axes(box)
    ax.set_axis_off()
    ax.imshow(image.imread(path), aspect="equal")
```

Conventions:
- `plt.rcParams.update(rc_params)` once at the top of the notebook, not before every figure.
- Default figure size `figsize=(10, 6)`; two-panel `(10, 4)` per row.
- Axis labels always carry a unit in square brackets: `"Time [ms]"`, `"Frequency of occurrence [–]"`. Sentence case.
- Titles are short noun phrases in sentence case: `"Histogram of inter-arrival times"`.
- Logo watermark: `add_logo(fig)` from `lib/params.py` places `logo.png` at `fig.add_axes([0.83, 0.90, 0.10, 0.10])`, axis off, `aspect="equal"`. Every committed figure carries it. Do not enlarge it or redefine the helper in a notebook.
- Histograms: `rwidth=0.8`, `colors[0]`, `alpha=0.5` when overlapping.
- Theory overlays (analytic PDF, M/M/1 formula): `colors[4]` or grey `#818386`, dashed, `linewidth=2`.

### 5.2 Bokeh / Panel (qos-01)

- `line_width=3`, `line_alpha=0.6`, line colour `colors[0]`; second signal `colors[4]`; combined/result `colors[5]`.
- Tools `"crosshair,pan,reset,save,wheel_zoom"`; plot 600 × 400.
- Titles and axis labels follow §5.1 wording rules. Set `p.title.text_font = "Carlito"`, `p.axis.axis_label_text_font = "Carlito"`, `p.axis.axis_label_text_font_style = "bold"`.

### 5.3 HTML dashboards in notebooks

Cards use the neutral tints, not ad-hoc greys:

```css
.card  { background: #F2F3F3; border-left: 4px solid #00A499; border-radius: 4px; padding: 12px 16px; }
.card h3 { margin: 0 0 6px; font: bold 15px Carlito, Calibri, sans-serif; color: #292929; }
.card p  { margin: 0; color: #292929; }
```

---

## 6. Notebooks

- One notebook per lesson at `qos-NN/qos_NN/exercise_NN.ipynb`, kernel `python3`.
- Cell 1 is a Markdown H1 identical to the README H1. Section headings mirror the README (`## Theory`, `## Exercise`, …) so the two documents can be read side by side.
- Cell order: title → imports (single cell) → constants → theory demonstrations → tasks → questions.
- Task cells are Markdown with an H3 `### Task N – short name`, a numbered list of what to do, and an empty code cell beneath.
- Reference implementations that students are meant to write themselves are kept in `lib/core.py` under a `# Reference implementations — students implement these first` banner, and imported only after the task cell.
- Commit notebooks with outputs cleared (`jupyter nbconvert --clear-output --inplace`) except where a figure is the deliverable of the lesson; then the figure is also saved to `fig/`.
- No `%autoreload` or `!pip install` in committed notebooks; dependencies belong in `pyproject.toml`.

---

## 7. Code

- Python ≥ 3.12, formatted with `ruff format` defaults (88 columns, double quotes). Imports sorted with `ruff check --select I`.
- NumPy-style docstrings on every public function and class; parameters carry units in the description: `S : float — Signal power [W]`.
- Public interfaces declared as `typing.Protocol` classes above the implementations, as in `qos-02/lib/core.py`.
- Every lesson's `pyproject.toml` uses the PEP 621 `[project]` table and is managed with `uv`; Poetry sections are legacy and must be migrated.

---

## 8. Checklist before committing

1. Colours come from §2 only; series order unchanged.
2. Fonts: Carlito stack in any rc/CSS you touched.
3. README follows the §4.2 skeleton; H1 is `# Exercise NN – Title`.
4. Every equation has a "where" list with units; renders on GitHub.
5. Every figure has unit-bearing axis labels, a sentence-case title, and the logo.
6. `lib/params.py` still identical across lessons (`md5sum qos-0*/qos_0*/lib/params.py`).
7. No emoji, no shortcode icons, no exclamation marks in prose.
