---
theme: seriph
title: 06 · Video quality assessment
info: |
  440-2216/01 Quality of Service — lecture 6.
  Methods for evaluating the quality of multimedia services II: where video quality is lost (hybrid coding,
  codecs, artefacts), subjective assessment (ITU-T P.910, ITU-R BT.500), and objective metrics from PSNR and
  SSIM to VMAF, no-reference and parametric streaming models.
exportFilename: 06-video-quality
layout: cover
transition: slide-left
mdc: true
lineNumbers: true
fonts:
  provider: none
  sans: Carlito
  mono: IBM Plex Mono
---

# Video Quality Assessment

### 440-2216/01 Quality of Service · Lecture 06

<div class="pt-6 text-sm vsb-muted">
Jan Rozhon &middot; Department of Telecommunications, FEECS
</div>

<!--
Ninety minutes including checkpoints: 5 min framing, 20 min video coding and artefacts, 25 min subjective
assessment, 30 min objective metrics (PSNR, SSIM, VMAF, NR and parametric models), 10 min summary/exit questions.
This is part II of "Methods for evaluating the quality of multimedia services": Lecture 05 did speech, this one
transfers the same three ideas — subjective reference, signal-based model, parametric model — to video.
-->

---

# Where we are going

<div class="grid grid-cols-3 gap-4 pt-4 text-sm">

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 1</div>

### Where quality is lost

The delivery chain, hybrid video coding, codec generations, artefacts

<div class="text-xs opacity-60 pt-2">↔ what the metrics have to detect</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 2</div>

### Subjective assessment

ITU-T P.910, ITU-R BT.500: viewers, content, methods, scales

<div class="text-xs opacity-60 pt-2">↔ the ground truth, as MOS was for speech</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 3</div>

### Objective assessment

PSNR, SSIM, VMAF; no-reference and parametric models

<div class="text-xs opacity-60 pt-2">↔ Lab 04 implements PSNR and SSIM</div>
</div>

</div>

<div class="pt-6">

One question runs through the lecture: **which property of the picture does a number measure — and how closely does it follow what viewers actually see?**

</div>

<!--
The structure deliberately mirrors Lecture 05. Students already know MOS, confidence intervals, intrusive vs
non-intrusive and parametric models; this lecture shows which parts carry over to video unchanged and which
parts (spatial structure, motion, content dependence) are new.
-->

---

# What you should be able to do

1. Explain where in the delivery chain video quality is lost, why lossy compression is unavoidable, and how a single packet loss propagates through a group of pictures.
2. Design a subjective video test according to ITU-T P.910 / ITU-R BT.500: viewers, content selection by SI/TI, method (ACR, ACR-HR, DCR, PC, DSCQS) and rating scale.
3. Compute MSE and PSNR, explain the luminance, contrast and structure terms of SSIM, and explain why the two can disagree.
4. Describe how VMAF fuses elementary features, how metrics are validated against subjective scores, and when a no-reference or parametric model is the right tool.

<div class="pt-6 vsb-muted">

Keep asking: **full reference, reduced reference, no reference or no pixels at all — and validated on which content?**

</div>

<!--
Outcome 3 is exercised directly in Lab 04 (students implement MSE and PSNR and use the supplied SSIM).
Outcomes 1 and 2 are typical exam questions; outcome 4 is the context for the lab's final question on VMAF.
-->

---
layout: statement
---

# A video metric is judged by one criterion only

## How well it predicts what viewers would say — measured against a subjective test

<!--
This is the thesis, and it is the same thesis as in Lecture 05. PSNR is easy, SSIM is cleverer, VMAF is
trained — but every one of them is ranked by its correlation with MOS from a P.910 or BT.500 experiment.
Part 3 closes with exactly that comparison.
-->

---
layout: section
---

# Part 1
## Where video quality is lost

---

# The video delivery chain

<Figure src="/figures/06/video-chain.svg" alt="Five stages from capture through pre-processing, encoding and transmission to playback. Capture adds limited resolution, sensor noise and motion blur; pre-processing adds down-scaling, colour conversion and chroma loss; encoding adds blocking, blurring, ringing and mosquito noise; transmission adds packet loss, delay, jitter and stalling; playback adds error concealment and depends on screen size and viewing distance." />

<div class="pt-1 text-sm">

Two evaluation approaches, as for speech: **subjective** — ask viewers; **objective** — compute a number from the signal or from parameters. Both must state *which* stages they cover: a codec comparison isolates encoding, a service-level test covers the whole chain.

</div>

<!--
Original slide 2 ("affected by camera, processing, transmission link impairments"), expanded into the full
chain. Emphasise the last stage: the same stream looks different on a phone at arm's length and on a 65"
television at 2 m. That is why viewing distance is a mandatory parameter of every subjective test (Part 2) and
why VMAF has separate models for TV, 4K and phone viewing (Part 3).
-->

---

# Why compression is unavoidable

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

Raw 1080p video, 30 frames/s, 8-bit 4:2:0 (12 bit/pixel on average):

$$
1920 \cdot 1080 \cdot 12 \cdot 30 \approx 746\ \mathrm{Mbit/s}
$$

A typical 1080p stream carries 4–6 Mbit/s — a compression ratio of **about 150 : 1**. That is only possible by discarding information viewers are unlikely to miss.

<div class="pt-2 text-sm vsb-muted">

4:2:0 already halves the raw data: the eye resolves colour more coarsely than brightness, so both chroma planes are stored at half resolution in each direction.

</div>

</div>
<div class="text-sm">

**Hybrid video coding** — common to every standard from H.261 to H.266 and AV1:

1. **Prediction** — *intra* from neighbouring blocks of the same frame, *inter* from other frames by motion compensation; only the residual is coded.
2. **Transform** — the residual block is converted to spatial frequencies (a DCT or its integer approximation).
3. **Quantisation** — coefficients are divided by a step size and rounded. **This is the only lossy step**, controlled by the quantisation parameter (QP).
4. **Entropy coding** — lossless (CAVLC, CABAC, arithmetic coding).

</div>
</div>

<!--
Speech had the same trade-off (64 kbit/s PCM vs 8 kbit/s G.729), but the factor here is two orders of
magnitude larger. The encoder's rate control varies QP to hit a target bit rate; content that is hard to
predict (motion, fine texture) needs a coarser QP at the same bit rate — which is why quality depends on
content, the subject of the first checkpoint.
-->

---

# Groups of pictures and error propagation

<Figure src="/figures/06/gop.svg" alt="Thirteen frames in display order: I, B, B, P, B, B, P, B, B, P, B, B, I. P-frames are predicted from the previous reference frame, B-frames from references on both sides. A packet lost in the first P-frame damages that frame, the two B-frames before it and every later frame up to the next I-frame." />

<div class="pt-1 text-sm">

Inter prediction is what makes compression efficient — and what makes video fragile. A lost packet damages not one frame but **every frame predicted from it** until the next I-frame (or intra refresh). The same loss rate therefore hurts video far more when it hits a reference frame than a non-reference B-frame.

</div>

<!--
Connect to Lecture 04: bursty loss (Gilbert) concentrates damage in fewer frames, random loss spreads it over
more GOPs. Decoders conceal errors by copying co-located blocks from the previous frame, which produces the
typical "smearing" artefact when there is motion. Typical GOP lengths: 0.5–2 s for streaming, longer for
broadcast; low-latency conferencing often avoids B-frames entirely and uses gradual intra refresh.
-->

---

# Compression standards

<div class="text-sm pt-1">

| Generation | Standard | Year | Developed by | Typical use |
|---|---|---|---|---|
| — | MPEG-2 / H.262 | 1995 | ISO/IEC MPEG + ITU-T | DVD, first-generation DVB-T |
| 1 | **H.264 / AVC** (MPEG-4 Part 10) | 2003 | JVT (MPEG + VCEG) | Blu-ray, web video, videoconferencing |
| 2 | **H.265 / HEVC** (MPEG-H Part 2) | 2013 | JCT-VC | UHD broadcasting, DVB-T2 in Czechia |
| 3 | **H.266 / VVC** | 2020 | JVET | UHD/8K, 360° video |
| 2 | **VP9** | 2013 | Google | YouTube, WebRTC |
| 3 | **AV1** | 2018 | Alliance for Open Media | royalty-free streaming (Netflix, YouTube) |

</div>

<div class="grid grid-cols-2 gap-6 pt-3 text-sm">
<div>

**Rule of thumb:** each generation needs **up to about half the bit rate** of its predecessor for the same *subjective* quality, averaged over broad test sets — at the cost of much higher encoder complexity. On a single clip the saving can be far smaller (Part 3 measures it).

</div>
<div class="vsb-muted">

AV1 merged the unreleased VP10 (Google), Daala (Xiph.Org/Mozilla) and Thor (Cisco) into one royalty-free design; VP8 (2010) was VP9's predecessor.

</div>
</div>

<!--
The original slide listed VP8/VP9/VP10, AV1, Daala and Thor as separate alternatives; since 2018 the last
three live on only inside AV1. The "half the bit rate" figure is measured with subjective tests, not with
PSNR — HEVC vs AVC ≈ 50 % (Ohm et al., IEEE TCSVT 2012; verification tests 2016), VVC vs HEVC ≈ 50 % (JVET
verification tests 2020–21), with the reference encoders tuned for quality. The measured curves in Part 3
("Comparing codecs") show how much the saving varies from clip to clip.
-->

---

# Typical impairments

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**Compression artefacts** — spatial

- **blocking** — visible edges of transform blocks at coarse quantisation
- **blurring** — high-frequency coefficients quantised to zero
- **ringing, mosquito noise** — oscillations around sharp edges, flickering in time
- **colour bleeding** — a consequence of chroma subsampling
- **banding** — steps in smooth gradients (sky)

</div>
<div class="border border-gray-400 p-4">

**Temporal and transmission impairments**

- **jerkiness** — reduced frame rate or dropped frames
- **smearing, frozen blocks** — packet loss plus error concealment
- **freezing** — decoder waits for a lost reference frame
- **stalling (rebuffering)** — the player's buffer runs empty in HTTP adaptive streaming
- **quality switching** — adaptive bit rate changes resolution mid-stream

</div>
</div>

<div class="pt-4 vsb-muted text-sm">

A metric can only react to what it can see: a per-frame image metric has no notion of stalling, and a stalling counter has no notion of blocking.

</div>

<!--
Ask students which of these they have seen on a streaming service in the last week — usually banding and
quality switching. Stalling is the dominant QoE factor in adaptive streaming (Hoßfeld et al. 2012; Seufert
et al. 2015): one stall of a few seconds costs more than a long initial delay. This returns in Part 3 with
ITU-T P.1203.
-->

---

# What compression artefacts look like

<div class="grid grid-cols-4 gap-3 pt-3 text-sm">
<figure class="artefact"><img src="/images/06/artefact-reference.png" alt="Detail of a Stockholm church spire against the sky and the roofs behind it, uncompressed." /><figcaption><b>Reference</b> · uncompressed</figcaption></figure>
<figure class="artefact"><img src="/images/06/artefact-blocking.png" alt="The same detail after MPEG-2 compression at 1.5 Mbit/s: the picture is made of visible 8 by 8 pixel squares, the fine roofs are flat blocks." /><figcaption><b>Blocking</b> · MPEG-2, 1.5 Mbit/s</figcaption></figure>
<figure class="artefact"><img src="/images/06/artefact-blurring.png" alt="The same detail after H.264 compression at 250 kbit/s: the deblocking filter hides the block edges, but the spire and roofs are smeared into soft shapes." /><figcaption><b>Blurring</b> · H.264, 250 kbit/s</figcaption></figure>
<figure class="artefact"><img src="/images/06/artefact-ringing.png" alt="The same detail after HEVC compression at 150 kbit/s: the spire keeps its outline, but a halo of oscillating noise surrounds its edges and the roofs." /><figcaption><b>Ringing, mosquito noise</b> · HEVC, 150 kbit/s</figcaption></figure>
</div>

<div class="pt-4 text-sm">

Each codec fails in its own way. **MPEG-2** shows its 8 × 8 transform blocks. **H.264** has an in-loop **deblocking filter**, which trades the block edges for blur. **HEVC** keeps edges sharper with larger transforms, but the quantisation error oscillates around them. A metric has to catch all three.

</div>

<div class="pt-1 text-xs vsb-muted">

Crops of 120 × 90 px, enlarged 2 ×, from the SVT test sequence *old_town_cross* (720p50, no copyright), 2 s encodes with ffmpeg.

</div>

<!--
Generated by scripts/generate-video-samples.py: the first 2 s of old_town_cross, encoded at deliberately low
bit rates so each artefact is obvious; frame 50, crop at (592, 262). The bit rates are not comparable across
codecs — each was chosen to make its codec's typical failure visible. Ask students to name each artefact
before revealing the captions (cover them, or show the slide on the overview first).
-->

---

# Impairments in motion

<div class="grid grid-cols-4 gap-3 pt-3">
<VideoClip src="/video/06/reference.mp4" poster="/video/06/reference.jpg" caption="Reference — park_joy, 720p50" :width="205" />
<VideoClip src="/video/06/mpeg2-3mbit.mp4" poster="/video/06/mpeg2-3mbit.jpg" caption="MPEG-2 at 3 Mbit/s — blocking that moves with the scene" :width="205" />
<VideoClip src="/video/06/packet-loss.mp4" poster="/video/06/packet-loss.jpg" caption="H.264, 3 datagrams lost in frame 12 — smearing until the I-frame at 1 s" :width="205" />
<VideoClip src="/video/06/stall.mp4" poster="/video/06/stall.jpg" caption="Stall — the picture freezes for 1.2 s, then resumes" :width="205" />
</div>

<div class="pt-5 text-sm">

Click a clip to play it (loops, no sound). Watch the **packet-loss** clip closely: the damaged area is dragged along with the motion for almost a second — the error propagation of the GOP slide made visible. The **stall** loses no pixel at all, yet viewers rate it among the worst impairments.

</div>

<!--
Clips from scripts/generate-video-samples.py, SVT park_joy (first 2 s, 720p50, no copyright). Packet loss:
H.264 at constant quality (CRF 26), one I-frame per second, no B-frames, packed in MPEG-TS; 21 TS packets
(three 7 × 188-byte datagrams) are deleted inside frame 12 and the stream is decoded with ffmpeg's default
error concealment. The browser copies are re-encoded near-transparently at 854 × 480. The videos play only in
`npm run dev` or the built site; the PDF shows the posters (the packet-loss poster is frame 30, inside the
damaged stretch). Part 3 measures the same packet-loss clip frame by frame (temporal pooling slide).
-->

---

# Checkpoint — same bit rate, same quality?

<div class="checkpoint-question">

Two 1080p streams are encoded with the same encoder at the same bit rate, 4 Mbit/s. One is a studio interview, the other a football match filmed with a moving camera. Will they look equally good? What does that imply for a subjective test?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**No.** The football match has far more motion and fine texture (grass, crowd), so prediction leaves larger residuals and the encoder must quantise more coarsely to hit the same bit rate — it shows artefacts the interview does not. Quality is a property of **content × condition**, not of the bit rate alone, so a test set must span a range of spatial and temporal complexity (SI and TI, next part) or its results will not generalise.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. This is the reason modern
streaming services use per-title (per-shot) encoding: the bit-rate ladder is chosen from measured quality,
not fixed per resolution.
-->

---
layout: section
---

# Part 2
## Subjective assessment

---

# Why ask viewers at all?

<div class="grid grid-cols-2 gap-6 pt-3 text-sm">
<div class="border border-gray-400 p-4">

**Properties of subjective assessment**

- human observers rate what they see — the **most reliable** measure of perceived quality and the reference for every objective metric
- **time-consuming** and **costly**: laboratory, calibrated displays, tens of viewers, hours of material
- not repeatable on demand — every new codec setting means a new test

</div>
<div class="border border-gray-400 p-4">

**The result is influenced by** (Qualinet QoE influence factors)

- **human** — individual interests, expectations, visual acuity, experience with the medium
- **system** — display size, resolution, calibration, tools and equipment
- **context** — ambient light, viewing distance, task (entertainment vs. surveillance)

</div>
</div>

<div class="pt-4 vsb-muted text-sm">

Standards exist to fix as many of these factors as possible, so that results from different laboratories can be compared.

</div>

<!--
Original slides 4–5: "What can you tell about the subjective methods in general?" Ask the question before
revealing the slide. The three-way split of influence factors is from the Qualinet White Paper on Definitions
of Quality of Experience (Le Callet, Möller, Perkis, 2013) — the same QoE definition as in Lecture 03.
-->

---

# The standards

<div class="text-sm pt-1">

| Recommendation | Scope | Methods |
|---|---|---|
| **ITU-T P.910** | multimedia video: videoconferencing, streaming, storage | ACR, ACR-HR, DCR, PC (+ SDSCE in an appendix) |
| **ITU-R BT.500** | television pictures, broadcast quality | DSIS, DSCQS, SSCQE, SDSCE, … |
| ITU-R BT.1788 | multimedia, multi-stimulus with random access | SAMVIQ |
| ITU-T P.913 | any environment: home, public places, crowdsourcing | ACR, ACR-HR, DCR, PC |

</div>

<div class="grid grid-cols-2 gap-6 pt-3 text-sm">
<div>

**ITU-T P.910** — *Subjective video quality assessment methods for multimedia applications*: first published 1996, revised 1999, 2008 and repeatedly since 2021; the current edition is from 2026.

</div>
<div>

The methods overlap under different names: P.910's **ACR** is BT.500's **single stimulus (SS)**; P.910's **DCR** is BT.500's **DSIS**.

</div>
</div>

<!--
Correction compared with the original slides, which gave 2008 as the first version: P.910 exists since
08/1996; editions 09/1999, 04/2008, 11/2021, 07/2022, 10/2023 and 07/2026 (prepublished). BT.500 is the
older, broadcast-oriented family (current revision BT.500-15, 2023). SAMVIQ lets the viewer replay and compare
all versions of one clip freely before scoring; it discriminates well between high-quality conditions.
-->

---

# Designing the test — viewers and viewing conditions

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div>

**Viewers** (P.910)

- from **4 to 40** depending on the required validity — 4 is the statistical minimum, beyond 40 there is rarely any benefit
- **at least 15** should normally participate; P.913 asks for ≥ 24 after screening, ≥ 35 in public environments
- **non-experts** — not involved in picture-quality work; experts (4–8) only for pilot tests
- screened for **visual acuity** (no errors on the 20/30 line of an eye chart) and **colour vision** (≤ 2 of 12 Ishihara plates missed)

</div>
<div>

**Viewing conditions** (P.910, Table 1)

| Parameter | Setting |
|---|---|
| viewing distance | 1–8 H (picture heights) |
| peak screen luminance | 100–200 cd/m² |
| background room illumination | ≤ 20 lx |
| background chromaticity | D65 |

**Session length** — at most about **30 minutes**, including training; longer tests are split into sessions with breaks.

</div>
</div>

<!--
Numbers checked against ITU-T P.910 (09/1999) clauses 7.1 and 7.3; the 2008 edition kept them. The 24/35 rule
comes from P.913 and was carried into the recent P.910 editions. Viewing distance matters because the
visibility of artefacts depends on the angle a pixel subtends: at 3 H a 1080p pixel is about one arc-minute —
the resolution limit of normal vision — which is why VMAF's default model assumes 3 H.
-->

---

# Structure of a test session

<Figure src="/figures/06/session.svg" alt="A session starts with training sequences of representative conditions, followed by a break for questions. The session proper opens with stabilising sequences whose scores are discarded, followed by the main part in randomised order. The session lasts at most about 30 minutes." />

<div class="pt-1 text-sm">

**Training** explains the scale and shows the range of quality to expect, without telling viewers what "good" is. **Stabilising** sequences absorb the first, less consistent votes. **Replications** of identical conditions measure each viewer's consistency and allow unreliable viewers to be discarded.

</div>

<!--
Redrawn after the P.910/BT.500 session diagram of the original slide 8. P.910 recommends at least five
conditions in the training phase and two to four replications per condition. Screening rules for
inconsistent viewers: BT.500 Annex 1 (kurtosis-based), P.913 (correlation of each viewer with the panel mean).
-->

---

# Choosing the test content — SI and TI

<div class="grid grid-cols-[1fr_470px] gap-6 pt-1">
<div class="text-sm">

P.910 quantifies how demanding a sequence is:

$$
\mathrm{SI} = \max_{n}\Big\{\operatorname{std}_{i,j}\big[\mathrm{Sobel}(F_n)\big]\Big\}
$$

$$
M_n(i,j) = F_n(i,j) - F_{n-1}(i,j)
$$

$$
\mathrm{TI} = \max_{n}\Big\{\operatorname{std}_{i,j}\big[M_n(i,j)\big]\Big\}
$$

$F_n$ is the luminance of frame $n$. **SI** grows with edges and texture, **TI** with motion. Test sequences (~10 s each) should cover all four quadrants of the SI–TI plane.

</div>
<div>

<Figure src="/figures/06/siti-plane.svg" alt="Schematic SI–TI plane: low SI and low TI — news presenter or video call; high SI, low TI — landscape pan, text; low SI, high TI — fast pan over smooth surfaces; high SI and high TI — sport or crowd, the hardest content to compress." />

</div>
</div>

<!--
This answers the checkpoint of Part 1 formally. The Sobel filter gives the gradient magnitude; its spatial
standard deviation is large for detailed frames. For scenes with cuts, P.910 allows TI to be reported both with
and without the cut. ITU-T provides reference software (and the open-source "siti-tools" implements the 2022
revision of the definitions).
-->

---

# Test methods — presentation patterns

<Figure src="/figures/06/methods-timing.svg" alt="Timelines of five methods. ACR: one test sequence, then a vote of at most 10 seconds. ACR-HR: the same, with the unprocessed reference hidden among the test sequences. DCR or DSIS: reference, a short grey pause, the test sequence, a vote. PC: the same content through system A and system B, then a preference vote. DSCQS: A, B, A, B, then a vote on both; the viewer does not know which one is the reference." />

<div class="pt-1 text-sm">

**ACR** is fast and resembles normal viewing. **DCR** is more sensitive to small impairments because the viewer sees the reference first. **PC** discriminates best between similar systems, but the number of pairs grows as $n(n-1)$.

</div>

<!--
Redrawn after the original slide 10, with ACR-HR and PC added and the P.910 timing: about 10 s per sequence,
voting ≤ 10 s, about 2 s of grey between the stimuli of a pair. P.910's own advice: use ACR for qualification
tests, DCR when fidelity to the source matters (high-quality systems), and PC as a second stage only for the
conditions that ACR or DCR could not separate.
-->

---
class: compact-table
---

# The methods at a glance

<div class="text-sm pt-1">

| Method | Reference | Scale | Output | Best for |
|---|---|---|---|---|
| **ACR** — Absolute Category Rating (= SS) | none | 5-grade quality | MOS | many conditions, realistic viewing |
| **ACR-HR** — ACR with Hidden Reference | hidden | 5-grade quality | DMOS | removing the influence of the source content |
| **DCR** — Degradation Category Rating (= DSIS) | explicit, first | 5-grade impairment | DMOS | high-quality systems, small impairments |
| **PC** — Pair Comparison | the other system | preference | preference scale | ranking similar systems |
| **DSCQS** — Double Stimulus Continuous Quality Scale | unknown, A or B | continuous 0–100 | difference score | broadcast codec evaluation |
| **SSCQE** — Single Stimulus Continuous Quality Evaluation | none | slider, sampled in time | quality over time | long clips with varying quality |
| **SDSCE** — Simultaneous Double Stimulus for Continuous Evaluation | side by side | slider, fidelity 0–100 | fidelity over time | sparse transmission errors |

</div>

<!--
The five variants of the original slide 7, completed with ACR-HR and PC and with the output each produces.
In ACR-HR a DV above 5 (the processed clip rated better than its source) is valid and must not be clipped —
it happens with enhancement filters. The continuous methods (SSCQE, SDSCE) capture the recency effect from
Lecture 05's Extras: a quality drop near the end weighs more than one at the start.
-->

---

# Rating scales

<Figure src="/figures/06/video-scales.svg" alt="Four rating scales: the five-grade ACR scale from 5 Excellent to 1 Bad; a nine-grade scale with the same labels on every second grade; an eleven-grade scale from 0 to 10 where 10 means perfectly faithful to the original and 0 no similarity, the endpoints serving only as anchors; and a continuous 0 to 100 scale with the five labels as guides, shown with a vote at 63." />

<div class="pt-1 text-sm">

The **nine-grade** scale adds resolution where the five categories are too coarse — typically when comparing low-bit-rate codecs. The **eleven-grade** scale adds anchored endpoints. **Continuous** scales avoid forcing a vote into a category. All of them keep the verbal labels, because the labels give the numbers their meaning.

</div>

<!--
From P.910 Annex B (nine- and eleven-grade scales, quasi-continuous scale) and BT.500 (continuous DSCQS
scale). The original slide 9 wording "extension to 10 grades: 10 = perfectly identical, 0 = completely
different" is the eleven-grade scale. Warn about translation: the Czech labels are not guaranteed to be equally
spaced in perception — P.910 itself mentions it.
-->

---

# From votes to a result

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

For a condition rated by $N$ viewers, exactly as in Lecture 05:

$$
\mathrm{MOS} = \frac{1}{N}\sum_{i=1}^{N} x_i
$$

$$
\mathrm{CI}_{95\,\%} = \mathrm{MOS} \pm t_{0.975,\,N-1}\,\frac{s}{\sqrt{N}}
$$

<div class="text-sm pt-2">

Report MOS **per condition**, averaged over contents, *and* per content — a codec may fail only on high-TI material.

**ACR-HR** scores each sequence against the hidden reference of the same content, then averages into a DMOS:

$$
\mathrm{DV} = V(\text{test}) - V(\text{ref}) + 5
$$

</div>

</div>
<div class="text-sm">

**Before averaging**

- discard the training and stabilising votes
- screen out inconsistent viewers (BT.500 Annex 1, correlation with the panel in P.913)
- keep the scale's name: MOS from ACR, DMOS from ACR-HR or DCR, difference scores from DSCQS are **not interchangeable**

**What the result is used for**

- ranking codecs or settings
- the **ground truth** for training and validating objective metrics — Part 3

</div>
</div>

<!--
Deliberately short: the statistics are the same as for speech, and students computed them in Lecture 05.
The new point is the content dimension — a video MOS table has one row per condition and one column per
source sequence.
-->

---

# Checkpoint — which method?

<div class="checkpoint-question">

A streaming provider wants to know whether its new encoder at 3 Mbit/s is **indistinguishable** from the current one at 4 Mbit/s on a 4K television. Should the test use ACR or DCR — and why?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**DCR (or a pair comparison).** Both versions are close to transparent, so on the absolute ACR scale both land at "Good"–"Excellent" and the difference drowns in the scale context and the viewers' spread. DCR shows the source first and asks about the *impairment*, which separates "imperceptible" from "perceptible but not annoying". The display (4K TV) and viewing distance (≈ 1.5 H for UHD) must match the service, or the test measures a different product.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. The same argument as the codec
checkpoint in Lecture 05 (ACR vs DCR/CCR). ACR-HR is an acceptable compromise when many contents have to be
tested and a full DCR session would be too long.
-->

---
layout: section
---

# Part 3
## Objective assessment

---

# Four families of objective models

<Figure src="/figures/06/vqa-families.svg" alt="The source video passes through the system under test to the received video. A full-reference model such as PSNR, SSIM or VMAF compares both videos pixel by pixel. A reduced-reference model compares a few features sent along with the video. A no-reference model sees only the received video. A bitstream or parametric model such as ITU-T P.1203 uses packet headers, bit rate and stalling events without decoding pixels." />

<div class="pt-1 text-sm">

**Full reference (FR)** needs the pristine source, so it lives in the encoding lab and in codec development. **No reference (NR)** and **parametric** models are what a network operator can deploy on live traffic — the video counterparts of P.563 and the E-model.

</div>

<!--
Original slides 11–12: "What can you tell about the objective methods in general?" Ask first. The general
properties: fast, repeatable, cheap, automatable — but each is a model with a validity range. Reduced-reference
standards (J.249 for SD, J.342 for HD) are rarely deployed; they are mentioned for completeness.
-->

---

# MSE and PSNR

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

For a reference image $I$ and a test image $K$ of $m \times n$ pixels:

$$
\mathrm{MSE} = \frac{1}{mn}\sum_{i=0}^{m-1}\sum_{j=0}^{n-1}\big[I(i,j) - K(i,j)\big]^2
$$

$$
\begin{aligned}
\mathrm{PSNR} &= 10 \log_{10} \frac{\mathrm{MAX}_I^2}{\mathrm{MSE}} = 20 \log_{10} \frac{\mathrm{MAX}_I}{\sqrt{\mathrm{MSE}}} \\
&= 20 \log_{10} \mathrm{MAX}_I - 10 \log_{10} \mathrm{MSE}
\end{aligned}
$$

$\mathrm{MAX}_I$ is the maximum **possible** pixel value — 255 for 8-bit video, 1023 for 10-bit — not the largest value in the image.

</div>
<div class="text-sm">

**Example:** 8-bit frames, MSE = 100:

$$
\mathrm{PSNR} = 10 \log_{10} \frac{255^2}{100} \approx 28.1\ \mathrm{dB}
$$

**For video**

- usually computed on luminance (Y) only, or as a weighted Y:U:V average (e.g. 6:1:1)
- per frame, then **pooled** over time — the mean of frame PSNRs differs from the PSNR of the mean MSE, because the logarithm is nonlinear
- identical frames give MSE = 0 and PSNR = ∞; tools report ∞ or cap it at a fixed value

<div class="pt-2 vsb-muted">

There is no universal "good" PSNR threshold: the same value can look fine on one content and poor on another.

</div>

</div>
</div>

<!--
Original slide 13, with the equations typeset and MAX_I explained. Lab 04 Step 1 is exactly this computation;
Lab 04 question 1 asks why PSNR uses the peak value and not the signal power. PSNR is still the default metric
in codec development (BD-rate), because it is cheap, differentiable and the encoder optimises MSE internally.
-->

---

# Equal MSE, very different pictures

<Figure src="/figures/06/equal-mse.svg" alt="A synthetic 32 by 32 pixel reference image and four distortions, each scaled to exactly the same MSE of 225 and therefore the same PSNR of 24.6 dB: a uniform brightness shift with SSIM 0.99, Gaussian noise with SSIM 0.84, blur with SSIM 0.71, and 8 by 8 blocking with SSIM 0.76." />

<div class="pt-1 text-sm">

MSE treats every pixel error alike, regardless of **where** it is and **what structure** it destroys. A brightness shift barely changes the picture; blur and blocking destroy edges and texture — at identical PSNR. This is the classic argument of Wang & Bovik, *"Mean squared error: love it or leave it?"* (2009).

</div>

<!--
The figure is generated by scripts/generate-figures.py: a 32 × 32 synthetic reference, four distortions scaled
to MSE = 225 exactly, SSIM computed with uniform 8 × 8 windows, L = 255, k1 = 0.01, k2 = 0.03 — the same
formula as lab 04's ssim_map with a uniform window. Lab 04 Step 3 makes the same point with dense vs sparse
noise on real photographs; don't give away their numbers, let them find the disagreement.
-->

---

# SSIM — the idea

<Figure src="/figures/06/ssim-diagram.svg" alt="Block diagram of SSIM. For signal x and signal y, the luminance is measured as the mean, the contrast as the standard deviation, and the structure as the signal normalised by mean and standard deviation. Luminance, contrast and structure comparisons are formed between the two signals and multiplied into SSIM(x, y)." />

<div class="pt-1 text-sm">

*"The human visual system is highly adapted to extract structural information from a scene"* — so measure the loss of **structure**, separately from changes of mean brightness and contrast, which the eye largely discounts (Wang, Bovik, Sheikh & Simoncelli, 2004).

</div>

<!--
Original slide 14, redrawn: the comparisons are placed between the two rows so the diagram reads as the
formula on the next slide. SSIM received a Primetime Engineering Emmy in 2015 and is the most widely used
perceptual image metric. Its limits: it is still a full-reference, per-image measure, and it is sensitive to
small geometric misalignment (a one-pixel shift lowers it markedly although nothing is visible).
-->

---

# SSIM — the formula

<div class="grid grid-cols-[1.3fr_1fr] gap-6 pt-1">
<div>

Local statistics of windows $x$, $y$ (mean, std. dev., covariance):

$$
\mu_x = \frac{1}{N}\sum_{i=1}^{N} x_i, \quad
\sigma_x = \Big(\frac{1}{N-1}\sum_{i=1}^{N}(x_i - \mu_x)^2\Big)^{1/2}
$$

$$
l = \frac{2\mu_x\mu_y + C_1}{\mu_x^2 + \mu_y^2 + C_1}, \quad
c = \frac{2\sigma_x\sigma_y + C_2}{\sigma_x^2 + \sigma_y^2 + C_2}
$$

$$
s = \frac{\sigma_{xy} + C_3}{\sigma_x\sigma_y + C_3}
$$

With $C_3 = C_2/2$ the product $l \cdot c \cdot s$ simplifies to

$$
\mathrm{SSIM}(x,y) = \frac{(2\mu_x\mu_y + C_1)(2\sigma_{xy} + C_2)}{(\mu_x^2 + \mu_y^2 + C_1)(\sigma_x^2 + \sigma_y^2 + C_2)}
$$

</div>
<div class="text-sm">

- $C_1 = (K_1 L)^2$, $C_2 = (K_2 L)^2$, with $K_1 = 0.01$, $K_2 = 0.03$ and $L$ the dynamic range — they keep the fractions stable when the denominators approach zero.
- The structure term compares the **normalised** signals $(x - \mu_x)/\sigma_x$ — it is their correlation coefficient.
- Evaluated in a sliding **11 × 11 Gaussian window** ($\sigma = 1.5$ px); the map is averaged into one **mean SSIM**.
- Range $[-1, 1]$; 1 only for identical windows.

**MS-SSIM** (Wang, Simoncelli & Bovik, 2003) evaluates contrast and structure at five scales, which accounts for viewing distance and resolution.

</div>
</div>

<!--
Original slide 15 (luminance, contrast, structure with the three statistics), completed with the comparison
functions and the combined formula. Lab 04 uses population statistics (1/N) and symmetric padding; the paper
uses 1/(N−1) for σ — students should note the convention when comparing implementations (Lab 04 README,
"record window size, weights, padding and L"). Lab 04 question 3 asks which constant keeps a flat window
defined.
-->

---

# Worked example — one 3 × 3 window

<div class="grid grid-cols-2 gap-6 pt-1 text-sm">
<div class="min-w-0">

A bright pixel on a flat background, and a **lower-contrast** copy of it ($L = 255$, $C_1 = 6.5$, $C_2 = 58.5$):

$$
x = \begin{bmatrix} 60 & 60 & 60 \\ 60 & 150 & 60 \\ 60 & 60 & 60 \end{bmatrix} \qquad
y = \begin{bmatrix} 65 & 65 & 65 \\ 65 & 110 & 65 \\ 65 & 65 & 65 \end{bmatrix}
$$

**1 · MSE and PSNR**

$$
\begin{aligned}
\mathrm{MSE} &= \tfrac{1}{9}\,(8 \cdot 5^2 + 40^2) = 200 \\
\mathrm{PSNR} &= 10\log_{10}\tfrac{255^2}{200} \approx 25.1\ \mathrm{dB}
\end{aligned}
$$

</div>
<div class="min-w-0" v-click>

**2 · Statistics** (with $1/(N-1)$, $N = 9$)

$$
\begin{aligned}
\mu_x &= \mu_y = 70 \\
\sigma_x^2 &= \tfrac{8 \cdot 10^2 + 80^2}{8} = 900, \quad \sigma_y^2 = \tfrac{8 \cdot 5^2 + 40^2}{8} = 225 \\
\sigma_{xy} &= \tfrac{8 \cdot (-10)(-5) + 80 \cdot 40}{8} = 450
\end{aligned}
$$

**3 · The three terms** — $l = 1$ (equal means), $s = 1$ ($\sigma_{xy} = \sigma_x\sigma_y$), and

$$
c = \frac{2 \cdot 30 \cdot 15 + 58.5}{900 + 225 + 58.5} \approx 0.81
$$

**4 · Result:** $\mathrm{SSIM} = l \cdot c \cdot s \approx \mathbf{0.81}$ — the structure is intact, only the contrast is halved.

<div class="pt-1 border border-gray-400 px-3 py-1">

A **uniform brightness shift** with the same MSE ($y = x + 14.1$) gives $c = s = 1$, $l \approx 0.98$: SSIM **0.98** at the same PSNR.

</div>
</div>
</div>

<!--
Work through this on the board; the numbers were chosen so every step is exact. The means are equal, so the
luminance term is 1; the deviations of y are exactly half of those of x, so the correlation (structure) is 1;
only the contrast term penalises. Note the constants: C1 = (0.01·255)² = 6.5, C2 = (0.03·255)² = 58.5,
C3 = C2/2. Lab 04 uses population statistics (1/N) — the variances change to 800 and 200, SSIM to 0.81 again
to two decimals. Point out that the brightness shift, which viewers barely notice, costs the same PSNR as
halving the contrast.
-->

---

# Try it — six distortions, one MSE

<QualityExplorer />

<!--
Interactive in the browser; the PDF export shows a static version instead (all six distortions at
MSE 200 with their SSIM maps and a one-line explanation each — QualityExplorer switches layout in print
mode). The slider sets one target MSE for all six distortions,
so PSNR is identical in every row; SSIM ranks them. Things to show: (1) at MSE 200 the mean shift (0.99) and
the contrast reduction (0.96) barely change SSIM, while Gaussian noise (≈ 0.5), blur and blocking (≈ 0.7)
fall far lower — the equal-MSE figure again, on a real picture; noise is worst here because the flat sky has
almost no structure of its own, so every added fluctuation is new structure; (2) the SSIM
map of the impulse noise: damage is confined to isolated points, so SSIM stays high despite the large MSE
of each hit — compare with Lab 04 Step 3 (sparse noise); (3) blur and blocking reach "max" — their full
strength cannot produce a larger MSE. The picture is a grayscale crop of SVT old_town_cross.
-->

---

# VMAF — Video Multimethod Assessment Fusion

<Figure src="/figures/06/vmaf-pipeline.svg" alt="VMAF pipeline: reference and distorted video are scaled to the model resolution. Motion is computed from the reference; visual information fidelity at four scales and the detail loss metric ADM are computed from both. A support vector regressor trained on subjective scores fuses them into a per-frame score from 0 to 100, averaged over time." />

<div class="grid grid-cols-3 gap-4 pt-1 text-sm">
<div>

**VIF** — Visual Information Fidelity (Sheikh & Bovik, 2006): information shared by reference and distorted image, at four scales.

</div>
<div>

**ADM / DLM** — Detail Loss Metric (Li et al., 2011): lost detail, separated from additive impairments that distract attention.

</div>
<div>

**Motion** — mean co-located pixel difference of consecutive reference frames: artefacts are masked in fast motion.

</div>
</div>

<!--
Netflix with USC and UT Austin (Li, Aaron, Katsavounidis, Moorthy, Manohara, 2016), open source (libvmaf,
integrated in FFmpeg). The SVR was trained on Netflix's own subjective data set (NFLX) collected with ACR-type
tests at 3H on a 1080p TV. VMAF is a full-reference metric: it needs the source, just like PSNR. The "NEG"
(no enhancement gain) variant clips the features so that sharpening and contrast boosting can no longer raise
the score — see the checkpoint later. In practice, differences of a few VMAF points between encodings are what
matters; the absolute value depends on the model and the viewing condition it assumes.
-->

---

# From frames to one number — temporal pooling

<Figure src="/figures/06/temporal-pooling.svg" alt="Per-frame VMAF of park_joy with and without a transmission error in frame 12. The lossy clip drops from about 91 to between 65 and 77 until the next I-frame at frame 50, then recovers. Pooled, the lossy clip scores 83.1 as arithmetic mean, 82.2 as harmonic mean, 68.0 as 5th percentile and 64.8 as minimum; the error-free clip averages 89.4." />

<div class="pt-1 text-sm">

Every image metric produces **one value per frame**; a video needs one per clip. The **arithmetic mean** dilutes a short, severe drop; the **harmonic mean** (a VMAF option) and **low percentiles** weight the worst frames more, as viewers do. No pooling rule models **recency** — the last seconds of a clip weigh most in the viewer's memory.

</div>

<!--
Measured, not drawn: the packet-loss clip of the "Impairments in motion" slide, per-frame VMAF from libvmaf
(scripts/generate-video-samples.py). The VMAF harmonic mean is n / Σ 1/(1 + v) − 1. The spread from 65 to 83
for the same frames is the point: always state the pooling together with the score. Continuous subjective
methods (SSCQE) and P.1203's integration module address the temporal dimension explicitly.
-->

---

# Comparing codecs — rate–quality curves and BD-rate

<Figure src="/figures/06/rd-curves.svg" alt="VMAF against bit rate for H.264, HEVC and AV1 on two SVT clips. On park_joy all codecs need several megabits per second; HEVC needs about 1 percent more bit rate than H.264 and AV1 27 percent less. On old_town_cross the same quality costs a tenth of the bit rate; HEVC needs 33 percent and AV1 50 percent less than H.264." />

<div class="pt-1 text-sm">

Codecs are compared by their **rate–quality curves**. The **Bjøntegaard delta rate** (BD-rate) is the average horizontal distance between two curves: the bit-rate change needed for the same quality. The saving is **not a property of the codec alone** — on the demanding *park_joy* HEVC gains almost nothing over H.264, on *old_town_cross* a third.

</div>

<!--
Measured with scripts/generate-video-samples.py on the first 2 s of each clip: x264 and x265 preset medium,
SVT-AV1 preset 8, constant-quality (CRF) sweeps, VMAF v0.6.1. BD-rate after Bjøntegaard (VCEG-M33, 2001):
fit log(rate) as a cubic in quality for each codec, integrate over the common quality range, and convert the
mean difference back to a percentage. Two-second clips and default presets are far from a codec evaluation —
the standard figures ("half the bit rate per generation") come from long, varied test sets with tuned encoders
and subjective tests. The point for the lecture is the spread between contents, which is the SI/TI argument of
Part 1 with numbers. Also note that the BD-rates computed with PSNR differ from those with VMAF — the metric
is part of the result.
-->

---

# How good are the metrics?

<Figure src="/figures/06/metric-srocc.svg" alt="Spearman rank correlation with subjective scores over all codecs of the MSU video quality metrics benchmark. VMAF variants reach 0.913 to 0.945, MS-SSIM 0.835 to 0.909, SSIM 0.843 to 0.906, PSNR 0.865 to 0.883, other full-reference metrics 0.537 to 0.937." />

<div class="grid grid-cols-2 gap-6 pt-1 text-sm">
<div>

Metrics are validated by correlating their output with MOS over a database: **SROCC** (Spearman, rank order — monotonicity) and **PLCC** (Pearson, after a nonlinear mapping — accuracy), plus the RMSE of the prediction.

</div>
<div class="vsb-muted">

On compression artefacts all established metrics are close — PSNR too. The differences grow on other distortions (noise, enhancement, transmission errors), and every metric is only validated for the content and distortions of its test database.

</div>
</div>

<!--
Data read from the MSU Video Quality Metrics Benchmark chart (videoprocessing.ai; Antsiferova et al., NeurIPS
2022 Datasets and Benchmarks) as shown in the original slide 17, summarised per metric family: each bar spans
all variants of one metric (colour planes Y/YUV/U, weightings 4:1:1 … 10:1:1, VMAF model versions). The
counter-intuitive finding that PSNR is not far behind is worth dwelling on: the benchmark is compression-only,
the regime PSNR is least bad at. The VQEG (Video Quality Experts Group) runs this kind of validation before
metrics become ITU recommendations.
-->

---

# No-reference and learned models

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**Natural scene statistics**

Undistorted natural images follow characteristic statistical regularities; distortions break them. **BRISQUE** (Mittal, Moorthy & Bovik, UT Austin, 2012) learns quality from these features; **NIQE** (2013) needs no subjective scores at all, only a model of pristine images.

</div>
<div class="border border-gray-400 p-4">

**Deep learning**

**Convolutional networks** extract spatial features per frame, **recurrent** networks or temporal pooling model their evolution over time — e.g. VSFA (2019), DOVER (2023). Trained on large user-generated-content databases (KoNViD-1k, YouTube-UGC) where no pristine reference exists.

</div>
</div>

<div class="pt-4 text-sm">

Strength: work on **any** received video, including user uploads. Weakness: they learn their training data — including its biases — and generalise poorly to unseen distortions; none is yet an ITU standard.

</div>

<!--
Original slide 16 listed "general ML-based methods: CNN, RNN". The references here give concrete, widely
cited examples from university groups (UT Austin LIVE, Konstanz, NTU). The trade-off mirrors DNSMOS in
Lecture 05: impressive correlation on in-domain data, uncertain elsewhere.
-->

---

# Parametric models for adaptive streaming — ITU-T P.1203

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div>

HTTP adaptive streaming (DASH, HLS) changes the dominant impairments: packet loss is hidden by TCP, and the viewer sees instead **initial loading delay**, **stalling** and **quality switching**.

**ITU-T P.1203 (2017)** estimates the MOS of a 1–5 min streaming session from:

- per-segment bit rate, resolution, frame rate, codec
- initial loading delay, stalling events and their positions
- in modes 0–3: from metadata only (mode 0) up to full bitstream parsing (mode 3)

**P.1204 (2020)** extends the approach to H.264, HEVC and VP9 up to 4K.

</div>
<div>

<div class="border border-gray-400 p-4">

**What the subjective studies show**

- one stall of a few seconds hurts more than a much longer initial delay (Hoßfeld et al., 2012)
- the number and duration of stalls dominate QoE; frequent quality switches are also penalised
- a recent drop weighs more than an early one — recency

</div>

<div class="pt-3 vsb-muted">

P.1203 is to streaming video what the E-model is to VoIP: quality from parameters, available in every player.

</div>
</div>
</div>

<!--
Seufert et al. (IEEE Communications Surveys & Tutorials, 2015) is the survey to recommend. P.1203 was the first
standardised model for adaptive streaming; its reference implementation is open source (itu-p1203 on GitHub,
Robitza et al.). This slide links video quality back to the network topics of Lectures 03 and 04: for HAS, the
network's QoS reaches the viewer as buffer behaviour, not as pixel errors.
-->

---

# Checkpoint — sharpening the score

<div class="checkpoint-question">

An encoder vendor adds a sharpening filter before encoding. VMAF (default model) rises from 85 to 92 while PSNR falls by 1 dB. Is the video better?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Not necessarily.** Sharpening moves the output *away* from the source (PSNR falls) but boosts the detail and contrast features VMAF rewards — VMAF can be **gamed** by enhancement. Moderate sharpening may even be preferred by viewers; strong sharpening produces halos. Only a subjective test decides. Netflix introduced **VMAF NEG** (no enhancement gain) for exactly this case: codec comparisons should report it alongside the default model.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. The general lesson: any metric
that becomes a target gets optimised against (Goodhart's law) — the thesis slide again: the metric is only as
good as its agreement with viewers, and that agreement was measured on unsharpened content.
-->

---

# Common mix-ups

<div class="grid grid-cols-3 gap-4 pt-2 text-sm">
<div class="border border-orange-400 p-3">

**Bit rate = quality**

The same bit rate gives very different quality on different content (SI/TI). Compare codecs on a range of contents.

</div>
<div class="border border-orange-400 p-3">

**MAX in PSNR**

It is the maximum *possible* value (255, 1023), not the brightest pixel of the image.

</div>
<div class="border border-orange-400 p-3">

**Averaging PSNR**

Mean of frame PSNRs ≠ PSNR of the mean MSE. Always state the pooling.

</div>
<div class="border border-orange-400 p-3">

**SSIM is not a percentage**

SSIM 0.95 is not "95 % quality"; its scale is nonlinear and content-dependent.

</div>
<div class="border border-orange-400 p-3">

**VMAF is not no-reference**

VMAF needs the source video, exactly like PSNR and SSIM.

</div>
<div class="border border-orange-400 p-3">

**MOS vs. DMOS**

ACR gives MOS; ACR-HR and DCR give DMOS. Different scales, not interchangeable.

</div>
</div>

<!--
Six confusions seen most often in Lab 04 reports and exam answers.
-->

---

# Summary — putting a number on video quality

<div class="grid grid-cols-2 gap-x-10 gap-y-2 pt-2 text-sm">

<div>

**Quality is lost along the whole chain**
Hybrid coding trades bits for artefacts through quantisation; inter prediction makes a single loss propagate to the next I-frame.

**Subjective tests are the reference**
P.910 and BT.500 fix viewers, content (SI/TI), conditions and method — ACR, ACR-HR, DCR, PC, DSCQS — and yield MOS or DMOS with confidence intervals.

</div>
<div>

**Full-reference metrics compare with the source**
PSNR measures error energy; SSIM compares luminance, contrast and structure; VMAF fuses VIF, ADM and motion with a model trained on MOS.

**Deployable models need less input**
No-reference models judge the received video alone; parametric models such as P.1203 predict streaming QoE from bit rate, resolution and stalling.

</div>

</div>

<!--
Read them aloud, one sentence each. Then the exit questions.
-->

---

# Exit questions — use the ideas

1. Why does a packet loss in a P-frame degrade quality for longer than the same loss in a B-frame?
2. Why must a subjective test state the viewing distance, and what would you expect to change if viewers moved from 3 H to 6 H?
3. Two degraded frames have the same PSNR. Construct a distortion for which SSIM stays close to 1, and one for which it drops sharply.
4. A network operator wants to monitor video quality on live IPTV traffic. Which families of models can it use, and which can it not?

<div v-click class="pt-5 vsb-muted">

**Explain the mechanism**, not just the name.

</div>

<!--
Allow two minutes for individual answers, then discuss. Answers: (1) other frames are predicted from a P-frame,
so the error propagates until the next I-frame; a non-reference B-frame affects only itself. (2) Artefact
visibility depends on the angle a pixel subtends; at 6 H fine artefacts fall below the eye's resolution, so
ratings rise and differences between conditions shrink. (3) A uniform brightness shift or a small contrast
change keeps structure (SSIM ≈ 1); blur or blocking at the same MSE destroys it — the equal-MSE figure.
(4) No-reference and parametric/bitstream models; not full-reference ones, since the source is not available
at the monitoring point (reduced-reference only if features are transmitted alongside).
-->

---

# Where you use this — Lab 04

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

Lab 04 applies the full-reference part of this lecture to still images:

- implement **MSE and PSNR** yourself, then compare with the reference implementation
- compute **SSIM** with the supplied loop and vectorised versions, and inspect the **SSIM map**
- compare **dense and sparse** noise at similar MSE — and rank the images by PSNR, by SSIM and by your own eye
- vary the SSIM **window** (uniform vs Gaussian, 7 to 15 px)

</div>
<div>

<div class="text-sm">

A video metric is an image metric per frame plus **temporal pooling** — everything in the lab carries over frame by frame.

</div>

<div class="pt-4 text-sm vsb-muted">

```bash
ssh <lab-server>
cd qos-04 && uv sync
uv run jupyter lab --ip 0.0.0.0
```

</div>
</div>
</div>

<!--
The ranking task in Step 3 is the lab's version of the "how good are the metrics" slide: students act as a
one-person subjective test and correlate their own ranking with PSNR and SSIM. Lab 04 question 5 (VMAF vs
SSIM) is answered by the VMAF and correlation slides.
-->

---

# References — standards

- ITU-T P.910, *Subjective video quality assessment methods for multimedia applications*, 1996; editions 1999, 2008, 2021–2023; current edition 2026.
- ITU-R BT.500-15, *Methodologies for the subjective assessment of the quality of television images*, 2023.
- ITU-R BT.1788, *Methodology for the subjective assessment of video quality in multimedia applications* (SAMVIQ), 2007.
- ITU-T P.913, *Methods for the subjective assessment of video quality, audio quality and audiovisual quality of Internet video and distribution quality television in any environment*, 2021.
- ITU-T P.1203, *Parametric bitstream-based quality assessment of progressive download and adaptive audiovisual streaming services over reliable transport*, 2017. ITU-T P.1204, 2020.
- ITU-T H.264 (AVC), 2003; H.265 (HEVC), 2013; H.266 (VVC), 2020. AOMedia, *AV1 Bitstream & Decoding Process Specification*, 2019.

<!--
P.910 and P.913 are freely downloadable from itu.int, as are BT.500 and BT.1788. The P.910 details on the
slides (viewers, viewing conditions, timing, SI/TI, scales) were checked against the 1999 text; they are
unchanged in principle in later editions, which add ACR-HR, crowdsourcing guidance and the P.913 rules.
-->

---

# References — literature

- Z. Wang, A. C. Bovik, H. R. Sheikh, E. P. Simoncelli, "Image quality assessment: from error visibility to structural similarity," *IEEE Trans. Image Processing*, 13(4), 600–612, 2004.
- Z. Wang, A. C. Bovik, "Mean squared error: love it or leave it?," *IEEE Signal Processing Magazine*, 26(1), 98–117, 2009.
- H. R. Sheikh, A. C. Bovik, "Image information and visual quality," *IEEE Trans. Image Processing*, 15(2), 430–444, 2006.
- Z. Li, A. Aaron, I. Katsavounidis, A. Moorthy, M. Manohara, "Toward a practical perceptual video quality metric," Netflix Technology Blog, 2016; github.com/Netflix/vmaf.
- A. Mittal, A. K. Moorthy, A. C. Bovik, "No-reference image quality assessment in the spatial domain," *IEEE Trans. Image Processing*, 21(12), 4695–4708, 2012.
- M. Seufert et al., "A survey on quality of experience of HTTP adaptive streaming," *IEEE Communications Surveys & Tutorials*, 17(1), 469–492, 2015.
- A. Antsiferova et al., "Video compression dataset and benchmark of learning-based video-quality metrics," *NeurIPS Datasets and Benchmarks*, 2022.

<!--
MS-SSIM: Z. Wang, E. P. Simoncelli, A. C. Bovik, "Multiscale structural similarity for image quality
assessment," Proc. 37th Asilomar Conf. Signals, Systems and Computers, 2003.
Further reading for interested students: the Qualinet White Paper on Definitions of Quality of Experience
(2013); T. Hoßfeld et al., "Initial delay vs. interruptions: between the devil and the deep blue sea," QoMEX
2012; S. Li, F. Zhang, L. Ma, K. N. Ngan, "Image quality assessment by separately evaluating detail losses and
additive impairments," IEEE Trans. Multimedia 13(5), 2011 (the DLM feature of VMAF); G. J. Sullivan et al.,
"Overview of the HEVC standard," IEEE TCSVT 22(12), 2012.
Measured slides: G. Bjøntegaard, "Calculation of average PSNR differences between RD-curves," ITU-T SG16
VCEG-M33, 2001 (BD-rate); A. Aaron et al., "Per-title encode optimization," Netflix Technology Blog, 2015.
Test sequences: SVT Sveriges Television AB, distributed by Xiph.Org (media.xiph.org/video/derf) — "no
restrictions, no copyright".
-->

---
layout: end
---

# Thank you for your attention

<div class="pt-6 opacity-85">

Jan Rozhon

+420 596 995 900 &middot; jan.rozhon@vsb.cz

</div>

<!--
Manual 5.4 (R25): closing slide carries presenter name, phone and e-mail.
-->

---
layout: section
---

# Extras
## Beyond the standard 2D picture

<!--
Not part of the timed 90-minute route. Use to answer questions or extend an advanced class.
-->

---

# Extras — per-title encoding and the convex hull

<Figure src="/figures/06/convex-hull.svg" alt="VMAF against bit rate for park_joy encoded with H.264 at 270p, 360p, 540p and 720p, each upscaled to 720p. Lower resolutions win at low bit rates. The convex hull of all points starts at 270p from 155 kbit/s, moves to 360p from 541 kbit/s, 540p from 1266 kbit/s and 720p from 4726 kbit/s." />

<div class="pt-1 text-sm">

An adaptive-streaming service offers each title at several **resolution–bit-rate pairs** (the *ladder*). Below a few Mbit/s, a *lower* resolution upscaled by the player looks better than a starved full-resolution encode. The **convex hull** over all encodes gives the best ladder for *this* clip; a fixed ladder for all titles wastes bits on easy content and starves hard content (Netflix, *per-title encoding*, 2015).

</div>

<!--
Measured on the first 2 s of park_joy (scripts/generate-video-samples.py): H.264 medium, CRF 18–42 at four
resolutions, upscaled with bicubic filtering to 1280 × 720 before VMAF — as a player would upscale before
display. The hull is the upper convex hull in linear bit rate. Above about 5 Mbit/s 540p and 720p are
practically equal. For easy content (old_town_cross) the hull moves to higher resolutions at much lower bit
rates — exactly why a per-title ladder beats a fixed one.
-->

---

# Extras — HDR, wide colour gamut and 360° video

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**High dynamic range, wide colour gamut** (ITU-R BT.2100)

Pixel values are no longer proportional to perceived brightness in the way 8-bit SDR assumes: PQ and HLG transfer functions, 10-bit samples, peak luminance up to 1 000 cd/m² and more. PSNR and SSIM on code values mis-weight errors in dark and bright regions. Used instead: metrics in perceptual colour spaces (**ΔE ITP**, ITU-R BT.2124), **HDR-VDP** (Mantiuk et al.), and HDR-specific VMAF models.

</div>
<div class="border border-gray-400 p-4">

**360° video** (ITU-T P.919 for subjective tests)

The sphere is stored in a flat projection (equirectangular, cube map), which over-represents the poles. **WS-PSNR** weights each pixel by the solid angle it covers; only the **viewport** the viewer actually looks at matters, and head-motion data decide which. Subjective tests use head-mounted displays and must control simulator sickness.

</div>
</div>

<!--
Both topics show the thesis again: a metric designed for one viewing situation (8-bit SDR on a flat screen)
is invalid in another until it is re-validated. References: ITU-R BT.2100 (2016), BT.2124 (2019); R. Mantiuk
et al., "HDR-VDP-2," ACM Trans. Graphics 30(4), 2011; Y. Sun, A. Lu, L. Yu, "Weighted-to-spherically-uniform
quality evaluation for omnidirectional video," IEEE Signal Processing Letters 24(9), 2017; ITU-T P.919 (2020).
-->

---

# Extras — crowdsourced subjective tests

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div>

Laboratory tests are slow and expensive; **crowdsourcing** runs the same ACR, ACR-HR, DCR or CCR test on hundreds of remote workers in hours.

**What changes**

- no control of display, distance, light or attention
- far more votes per condition compensate for the extra noise
- quality control becomes part of the method: qualification tests, **gold questions** with known answers, **trapping questions**, environment and hardware checks

</div>
<div>

**Standards and practice**

- ITU-T **P.913** — tests outside the laboratory, including crowdsourcing
- ITU-T **P.808** — the crowdsourcing counterpart for speech (Lecture 05)
- open-source P.910 crowdsourcing toolkit (Naderi & Cutler, 2022) — shown to reproduce laboratory results for ACR, ACR-HR, DCR and CCR

<div class="pt-3 vsb-muted">

Crowdsourced MOS is what most learned no-reference models are trained on — their bias starts here.

</div>
</div>
</div>

<!--
T. Hoßfeld et al., "Best practices for QoE crowdtesting," IEEE Trans. Multimedia 16(2), 2014; B. Naderi,
R. Cutler, "A crowdsourcing approach to video quality assessment," arXiv 2204.06784, 2022 (the toolkit and
its validation against P.910 lab studies).
-->
