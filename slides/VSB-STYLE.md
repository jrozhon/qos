# VŠB-TUO visual style — rules for the Slidev deck

Condensed from *Manuál jednotného vizuálního stylu VŠB-TUO, verze 1.1* (2023). Section numbers below
point back at the manual. Source of truth for assets: **vizual.vsb.cz**; approvals: **vizual@vsb.cz** (§ intro).

---

## 1. Colours

### University (I. level) — § 2.1

| Role | HEX | Pantone | Note |
|---|---|---|---|
| **University green** | `#00A499` | 3272 C | The primary brand colour. Everything defaults to this. |
| Black | `#000000` | Process Black C | Achromatic variant, body text |
| White | `#FFFFFF` | — | Default logo background |

### Faculty / institute (II. level) — § 2.2

Each unit has one fixed colour. Departments (III. level) **inherit** their faculty's colour — they get no colour
of their own (§ 2.3).

| Unit | HEX | Pantone |
|---|---|---|
| HGF — Hornicko-geologická fakulta | `#43B02A` | 361 C |
| FMT — Fakulta materiálově-technologická | `#E4002B` | 185 C |
| FS — Fakulta strojní | `#FFB81C` | 1235 C |
| EKF — Ekonomická fakulta | `#0047BB` | 2728 C |
| **FEI — Fakulta elektrotechniky a informatiky** | `#05C3DE` | 311 C |
| FAST — Fakulta stavební | `#8246AF` | 2587 C |
| FBI — Fakulta bezpečnostního inženýrství | `#FF8200` | 151 C |
| CEET | `#A28E2A` | 456 C |
| IT4Innovations | `#818386` | 50 % black |

**This deck is FEI** → accent `#05C3DE`.

### Reserved

`#8A8D8F` (Pantone 877 C) is the **ceremonial silver**, reserved for rector-level materials (§ 2.4). Do not use it
as a generic grey — pick a neutral outside the palette instead.

### Rules

- **R1** — Faculty materials must always also carry an element in the **university green** `#00A499`
  (§ 4.7, § 4.9). A purely FEI-cyan deck is non-conformant: keep green on the title slide, section dividers, or rules/accents.
- **R2** — Green is the primary; the faculty colour is the accent, not a replacement.
- **R3** — No colours outside this palette for chrome. Syntax highlighting in code blocks is exempt (it's content, not identity).
- **R4** — No gradients, no re-saturation, and never any of this on the **logo** (§ 1.13). Flat *tints* of the brand
  green as a background field are fine and explicitly sanctioned — § 1.5 shows the 10–100 % scale — provided the logo
  then follows the ≤30 % / ≥80 % rule (R12). `#EBF8F7`, the 8 % tint used for mermaid nodes, is in-style.

### Contrast (not in the manual — WCAG, measured)

The palette is print-first and several colours fail on screen. Measured ratios:

| Pair | Ratio | Verdict |
|---|---|---|
| `#00A499` on white | 3.10 | Large text / ≥24px headings only |
| White on `#00A499` | 3.10 | Large text only — fine for the full-bleed green slide's big title |
| `#05C3DE` on white | 2.13 | **Never for text.** Fills, rules, chart marks only |
| Black on `#00A499` | 6.77 | Safe |
| `#FFB81C`, `#FF8200`, `#43B02A` on white | 1.73 / 2.49 / 2.81 | Fills only |

- **R5** — Never set body text in a brand colour on white. Body text is `#000000` (or `#1A1A1A`).
- **R6** — For green *text* at body size, use a darkened tone `#00736B` (5.73:1) or `#005F58` (7.56:1). Keep `#00A499`
  itself for fills, rules, and large headings so the brand colour is still what the eye reads as "green".
- **R7** — Slidev dark mode (`d`) isn't covered by the manual. Use `#4DD8CE` as the green on dark backgrounds
  (9.8:1 on `#0B1F1D`) and keep `#00A499` for fills.

---

## 2. Typography — § 3.1–3.5

- **Drive** — body/text face (humanist sans).
- **Drive Mono** — display/heading face, monospaced. Also used for the logotype itself.
- **Calibri** — the manual's *sanctioned substitute* when Drive is unavailable (§ 3.3), and what the official
  PowerPoint template ships with (§ 5.4).

### Rules

- **R8** — Never set long body copy in Drive Mono, and never set headings in Drive when Drive Mono is available —
  respect each face's purpose (§ 3.4). Permitted combinations: Mono headings + Drive body, Drive headings + Drive body,
  Drive headings + Mono body (short text only).
- **R9** — Type scale steps of **≥1.33×** between levels (text → perex → title), minimum 1.2× in dense layouts (§ 3.5).
  E.g. 16 / 21 / 28 px, or 18 / 24 / 32 px.
- **R10** — The logotype's own type (Drive Mono Medium for "VŠB", Book for the rest) is part of the logo file. Never
  re-typeset it (§ 1.2, § 1.13).

### Free substitutes — what the manual does and doesn't give you

**The manual names no free font.** It names exactly three faces, and all three are commercial:

| Face | Status |
|---|---|
| Drive, Drive Mono | Commercial. Black[Foundry] (Elliott Amblard, Jérémie Hornus). Licence via the university. |
| Calibri | Microsoft proprietary. Bundled with Windows/Office; **not** redistributable as a webfont. |

So there is no licence-clean route to a literally conformant deck without buying in. But there is a defensible one:

- **R8a** — Substitute **Carlito** (SIL OFL, by Łukasz Dziedzic) for Calibri. Carlito is *metrically compatible* with
  Calibri — same advance widths, same line breaks — so it renders as Calibri's stand-in rather than as a different
  typeface. Since Calibri is itself the manual's sanctioned Drive substitute (§ 3.3), Carlito is one documented step
  further down a chain the manual opened.
- **R8b** — The official VŠB-TUO PowerPoint template ships with **Calibri throughout — headings included** (§ 5.4).
  That is the precedent to follow: when Drive is unavailable, do *not* invent a mono heading face. Set the whole deck
  in Carlito and get hierarchy from size and weight instead. A non-brand mono in the heading slot looks more
  off-brand than Calibri does, because Drive Mono's monospacing is a recognisable identity cue that a substitute
  mono gets visibly wrong.
- **R8c** — Code blocks are exempt. They are content, not identity, and Drive Mono is explicitly called out as
  ill-suited to dense text (§ 3.2). Use any coding mono — IBM Plex Mono is already installed on this machine.

```css
--vsb-font-text:    "Drive", "Carlito", "Calibri", system-ui, sans-serif;
--vsb-font-display: "Drive Mono", "Drive", "Carlito", "Calibri", sans-serif;
--vsb-font-code:    "IBM Plex Mono", "JetBrains Mono", ui-monospace, monospace;
```

Carlito is not currently installed here. Get it with `sudo pacman -S ttf-carlito`, or self-host it in
`slides/public/fonts/` so exports and the built site don't depend on the presenter's machine. If you do obtain the
Drive licence, drop the webfonts in the same folder — the cascade above picks them up with no other change.

---

## 3. Logo — § 1.2–1.13

- **R11** — Clear zone on all four sides = the height of the symbol (the "A" measure, § 1.3). Nothing but background inside it.
- **R12** — Positive (colour) logo on backgrounds up to **30 %** tint of the brand colour; **negative/white** logo on
  backgrounds darker than **80 %** (§ 1.5). On the full-green slide → white logo. Mid-tones: put the logo on a solid
  white or black patch sized to at least the clear zone (§ 1.8).
- **R13** — Minimum height 9 mm (CZ) / 8 mm (EN). Slidev exports this deck at **735 × 414 pt = 259 × 146 mm** for a
  980 × 552 px canvas, i.e. **3.78 px/mm**. So the EN minimum is **30.2 px** and the CZ minimum is **34.0 px**.
  `VsbLogo` clamps to 31 px. Re-derive this if you change the export page size — a larger printed page makes the
  minimum *smaller* in px, never larger.
- **R14** — Abbreviated form is always **VŠB-TUO**. `VŠB` alone is forbidden (§ 1.12).
- **R15** — Levels are separated by a vertical rule of the same weight as the symbol's strokes. A III. level (department)
  lockup must always carry the II. level too (§ 1.11).
- **R16** — Forbidden (§ 1.13): recolouring, restretching, swapping the font, shadows/outlines, changing symbol position,
  reordering levels, any custom modification. Use the original files from vizual.vsb.cz — never redraw.
- **R17** — Combining with partner logos: minimum gap **2A** horizontally and vertically; equal heights (§ 1.2b).

### Logo assets in this repo

Converted from `logo.eps` (Illustrator EPS, `440 FEI-02.eps`, 2019) into `public/`:

| File | Use |
|---|---|
| `public/logo-lvl1.svg` | **Level I, colour — the deck's mark.** Aspect **2.73:1** |
| `public/logo-lvl1-white.svg` | Level I, negative (§ 1.5) |
| `public/logo-lvl1-black.svg` | Level I, achromatic (§ 1.6) |
| `public/logo.svg` | Full I+II+III lockup, colour. Aspect 5.97:1. Not currently used |
| `public/logo-white.svg` | Full lockup, negative (§ 1.5) |
| `public/logo-black.svg` | Full lockup, achromatic (§ 1.6) |

All six are pure paths — no live text, so no font dependency — and carry no fixed aspect lock beyond the viewBox,
so set a height and let the width follow.

The source `logo.eps` is the **English, III. level** lockup: *VSB - Technical University of Ostrava | Faculty of
Electrical Engineering and Computer Science | Department of Telecommunications*. Level I is `#00A499`, levels II
and III are `#05C3DE` — the inheritance rule (§ 2.3). Ghostscript's CMYK→RGB gave `#3bae9a`/`#50c5d9`; both were
remapped to the manual's exact RGB values.

**How the Level I files were made.** The III. level lockup was 5.97:1 — unreadable at the § 1.9 minimum and
overbearing at a legible one. The Level I files isolate the 36 paths filled `#3bae9a` (the symbol plus *VSB
TECHNICAL UNIVERSITY OF OSTRAVA*) and crop to their bounding box. This is not a modified logotype — the result is
the standalone Level I mark, path-for-path, which § 1.11 defines as a valid level in its own right. Still, see the
open items: verifying it against the official Level I file is worthwhile.

Two things that will bite you if you regenerate these:

- **Get the bounding box from rendered pixels, not `inkscape --query-*`.** Inkscape reports in 96 dpi px while the
  viewBox here is in pt-like units — a 1.3333× error that silently crops the mark. The measured box is
  `x=29.00 y=68.50 w=130.01 h=47.75` in viewBox units, +0.25 u padding for antialiased edges.
- **Normalise the viewBox to a 0,0 origin** (wrap the paths in a `translate`) and set explicit `width`/`height`.
  A non-zero origin plus CSS `width:auto` made the browser clip the mark.
- **Validate the output as XML.** A raw `<` inside `<desc>` is a hard parse error in browsers — the image silently
  fails to load — while Inkscape's lenient parser renders it fine, so a local render is not proof.

- **R13a** — Level I is **2.73:1**, so the 31 px minimum is ~85 px wide, under 9 % of the canvas. The cover uses
  76 px (~207 px wide), comfortably legible.
- **R13b** — No Czech version is in the repo. A Czech-language deck needs the CZ lockup from vizual.vsb.cz, and its
  minimum is 9 mm = 34 px, not 31 (§ 1.9).

### Naming in slide text — § 1.1

- Full name: `Vysoká škola báňská – Technická univerzita Ostrava`
- Permitted: `VŠB – Technická univerzita Ostrava` (en dash, spaces both sides) and `VŠB-TUO` (hyphen, no spaces)
- English: `VSB - Technical University of Ostrava`
- **R18** — Only the shortest form uses a hyphen; every longer form uses a spaced en dash.

---

## 4. Layout patterns (from the official PowerPoint and poster templates — § 5.4, § 4.6)

- **R19** — **This deck carries the logo on the cover only.** The official PowerPoint template (§ 5.4) puts it on
  every slide, so this is a deliberate deviation: at the sanctioned minimum size the mark was too small to read, and
  at a readable size it competed with the content on the remaining content slides. The cover carries it at 76 px, well
  clear of legibility. If you restore per-slide logos, use `<VsbLogo :height="31" />` top-left.
- **R20** — Title slide: logo lockup centred, `www.vsb.cz` at the foot, generous white space.
- **R21** — Content slide: green heading, black body, a thin green rule or a bordered content box. White background is
  the default (§ 1.8).
- **R22** — Section dividers: **full-bleed green**, white heading, faculty-cyan accent bar. This is the deck's main
  rhythm device — use it between the deck's parts. No logo, per R19.
- **R23** — Photo slides: full-bleed image, text in white directly on it, white logo. Keep the image dark enough for the type.
- **R24** — Everything sits on a **grid**; blocks are hard-edged rectangles, flush-aligned, no rounded corners, no
  drop shadows, no bevels (§ 4.6 shows the construction grid).
- **R25** — Closing slide: *"Děkuji za pozornost"* + presenter name, phone, e-mail, and `www.vsb.cz`.
- **R26** — Charts: one brand colour per series, drawn from the faculty palette in the order used by the official
  template (green first, then HGF green, FMT red, FS yellow, EKF blue, FEI cyan, FAST purple, FBI orange).

---

## 5. Photography — § 8.1–8.4

- **R27** — Level horizon, parallel building walls, minimal perspective distortion, correct exposure, lively colour.
- **R28** — Prefer authentic campus/student/research images; retouch out distracting objects (bins, cameras, red signs).
- **R29** — Avoid staged, artificial-looking scenes and cluttered, over-detailed frames. GDPR applies to student photos.

---

## 6. Suggested CSS variables

```css
:root {
  /* identity */
  --vsb-green:        #00A499;  /* Pantone 3272 C — primary */
  --vsb-green-text:   #00736B;  /* darkened, AA for body text on white */
  --vsb-green-dark:   #005F58;  /* AAA on white */
  --vsb-green-light:  #4DD8CE;  /* dark-mode accent only */
  --vsb-black:        #000000;
  --vsb-white:        #FFFFFF;

  /* faculty — FEI */
  --vsb-faculty:      #05C3DE;  /* Pantone 311 C — fills/rules, never text on white */

  /* other faculties, for charts */
  --vsb-hgf:  #43B02A;
  --vsb-fmt:  #E4002B;
  --vsb-fs:   #FFB81C;
  --vsb-ekf:  #0047BB;
  --vsb-fast: #8246AF;
  --vsb-fbi:  #FF8200;
  --vsb-ceet: #A28E2A;
  --vsb-it4i: #818386;

  /* type */
  --vsb-font-text:    "Drive", "Carlito", "Calibri", system-ui, sans-serif;
  --vsb-font-display: "Drive Mono", "Drive", "Carlito", "Calibri", sans-serif;
  --vsb-font-code:    "JetBrains Mono", ui-monospace, monospace;

  /* 1.33× scale */
  --vsb-text:  16px;
  --vsb-perex: 21px;
  --vsb-h2:    28px;
  --vsb-h1:    38px;
}
```

---

## 7. How this is wired into the deck

| File | What it does |
|---|---|
| `style.css` | Palette, self-hosted `@font-face`, type scale, headings, tables, code, dark mode. Auto-loaded by Slidev. |
| `layouts/cover.vue` | Title slide (R20) |
| `layouts/default.vue` | Content slide — green title + rule (R21) |
| `layouts/center.vue` | Centred content slide, same chrome |
| `layouts/section.vue` | Full-bleed green divider, cyan accent (R22) |
| `layouts/statement.vue` | Thesis slide — white ground, oversized green type |
| `layouts/end.vue` | Closing slide (R25) |
| `components/VsbLogo.vue` | Logo with `variant` and `height`, clamped to the § 1.9 minimum |
| `setup/mermaid.ts` | Mermaid theme — **all** diagram styling lives here (see below) |
| `public/logo-lvl1*.svg`, `public/fonts/` | Assets |
| `scripts/generate-figures.py` | SVG lecture figures for every deck, `public/figures/<deck>/` (see §9) |

Two things were adapted rather than authored from scratch:

- Slides may use `rounded` and Tailwind's generic `border-{colour}-400` on cards. `style.css` squares every corner
  (R24) and remaps those accent colours onto the real faculty palette — `red-400`→FMT, `blue-400`→EKF,
  `purple-400`→FAST, `orange-400`→FBI, `green-400`→university green — so the semantic contrast survives and nothing
  off-palette reaches a slide.
- Seriph sets `.slidev-layout.section h1 { font-weight: 500 }` at a higher specificity than a plain class selector,
  so the section layout needs `!important` on its heading weight. Don't remove it.
- **Mermaid renders inside a ShadowRoot.** `@slidev/client` mounts diagrams as `<ShadowRoot class="mermaid">`, so
  no rule in `style.css` can reach a node, edge, or label — such rules fail silently. Everything must go through
  `themeVariables` and `themeCSS` in `setup/mermaid.ts`, which mermaid injects into the SVG's own `<style>` inside
  the shadow tree. Only the host element's own box (centring, margins) is stylable from the page.

## 8. Open items before this is fully conformant

1. ~~**Presenter contact block**~~ — resolved: the `end` slide of `01-information-theory.md` carries name, phone
   and e-mail (§ 5.4 / R25). New decks must do the same.
2. **Verify the Level I crop** against the official standalone Level I file from vizual.vsb.cz. It was extracted
   from the department lockup rather than downloaded (see "Logo assets"), and while it is pixel-identical to the
   Level I portion of that file, an official source is preferable.
3. **Czech lockup** — needed if the deck is ever translated (R13b).
4. **Drive / Drive Mono** — only if the licence is obtained. Drop the webfonts into `public/fonts/` and the cascade
   in `style.css` picks them up with no other change.
5. **Approval** — anything beyond the official templates should go to vizual@vsb.cz before public use.

## 9. Authored lecture figures

Figures are SVGs in `public/figures/<deck>/`, generated by `scripts/generate-figures.py` (standard library only).
The Mermaid theme above is retained for ad-hoc diagrams; it does not style these SVGs.

- Carlito regular and bold are embedded in each SVG so standalone and PDF rendering match the slides.
- Square boxes, flat green tints, neutral axes and green data series follow R4 and R24. Additional chart series
  use the faculty palette in the R26 order (EKF blue, FBI orange, FMT red for error marks).
- FEI cyan is reserved for small graphical accents; labels use ink, muted neutral or dark green.
- Every SVG carries a descriptive title and description, and every slide image has alt text.
- White figure surfaces are intentional in dark mode, preserving the checked contrast.
- One SVG unit is one slide CSS pixel: full-width artwork is 880 px; the shared type scale is 18 px labels,
  15 px annotations, 16 px section labels and 24 px callouts. `.lecture-diagram` renders at native size.

Typography: body 17.6 px, code and `.text-xs`/`.text-sm` annotations 15 px, standard headings 34.5 px. Cover and
statement headings use 51.2 px and 46.4 px; their selectors include `.slidev-layout` so they win over the theme.
