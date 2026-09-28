---
theme: seriph
title: 05 · Speech quality measurement
info: |
  440-2216/01 Quality of Service — lecture 5.
  Subjective listening tests and the MOS scale (ITU-T P.800), intrusive and non-intrusive objective models
  (PESQ, POLQA, ViSQOL, P.563), and the E-model (ITU-T G.107) as a parametric planning tool for VoIP.
exportFilename: 05-speech-quality
layout: cover
transition: slide-left
mdc: true
lineNumbers: true
fonts:
  provider: none
  sans: Carlito
  mono: IBM Plex Mono
---

# Speech Quality Measurement

### 440-2216/01 Quality of Service · Lecture 05

<div class="pt-6 text-sm vsb-muted">
Jan Rozhon, Miroslav Vozňák &middot; Department of Telecommunications, FEECS
</div>

<!--
Ninety minutes including checkpoints: 5 min framing, 25 min subjective testing and MOS statistics, 20 min
objective signal-based models, 30 min E-model with a worked example, 10 min summary/exit questions.
Lecture 03 gave the network impairments (delay, jitter, loss) and Lecture 04 their statistical models; this
lecture answers the question both left open — how much does a given impairment actually hurt the listener?
-->

---

# Where we are going

<div class="grid grid-cols-3 gap-4 pt-4 text-sm">

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 1</div>

### Subjective tests

Listeners, rating scales, MOS and its confidence interval

<div class="text-xs opacity-60 pt-2">↔ the ground truth everything else predicts</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 2</div>

### Signal-based models

PESQ, POLQA, ViSQOL — intrusive; P.563 — non-intrusive

<div class="text-xs opacity-60 pt-2">↔ Lab 03 scores recordings with these</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 3</div>

### The E-model

ITU-T G.107: from delay, loss and codec to a rating R

<div class="text-xs opacity-60 pt-2">↔ Lectures 03 and 04 supply its inputs</div>
</div>

</div>

<div class="pt-6">

One question runs through the lecture: **what does a quality number actually predict — and for which listeners, which task, and which audio bandwidth?**

</div>

<!--
The three parts trade accuracy for convenience: a listening test is the reference but costs days and
dozens of people; a signal-based model needs audio and (usually) the clean original; the E-model needs only a
handful of network and terminal parameters and can be evaluated before the network exists.
-->

---

# What you should be able to do

1. Describe the ACR, DCR and CCR test methods of ITU-T P.800, compute a MOS with its confidence interval, and use the P.800.1 labels (MOS-LQS, -LQO, -CQE …) correctly.
2. Distinguish intrusive, non-intrusive and parametric models, and outline how PESQ turns two signals into one score.
3. Choose a model that matches the audio bandwidth and the impairment being studied — and recognise when a model cannot see an impairment at all.
4. Compute the E-model rating R from delay, codec, packet loss and the advantage factor, and convert it to MOS and a user-satisfaction category.

<div class="pt-6 vsb-muted">

Keep asking: **was this number obtained from people, from a signal, or from parameters — and was it a listening or a conversational situation?**

</div>

<!--
Outcome 1 and 2 are exercised directly in Lab 03 (ACR/DCR tests on classmates, PESQ and ViSQOL on the
captured audio). Outcome 4 is the calculation students are expected to do by hand in the exam.
-->

---
layout: statement
---

# A quality score is a prediction of what listeners would say

## Every objective method is only as good as the subjective test it was calibrated against

<!--
This is the thesis. Parts 2 and 3 are both regression models fitted to large databases of P.800 listening
tests; they inherit the scale, the ceiling and the context of those tests. Students who remember this will not
be surprised when PESQ ignores delay or when the E-model never reaches MOS 5.
-->

---
layout: section
---

# Part 1
## Subjective assessment

---

# Why ask people at all?

<div class="pt-2">

Lecture 03 separated **QoS** — what the network delivers — from **QoE** — what the user perceives. Speech quality is a QoE quantity: it exists only in the listener's judgement, so the **reference method is to ask listeners**.

</div>

<div class="grid grid-cols-2 gap-6 pt-4 text-sm">
<div class="border border-gray-400 p-4">

**Mean Opinion Score (MOS)**

The mean of the values on a predefined scale that test subjects assign to their opinion of a system's performance (ITU-T P.10/G.100). A MOS is a property of a **condition** — a codec, a loss rate, a delay — averaged over many listeners and samples.

</div>
<div class="border border-gray-400 p-4">

**Methods of subjective determination — ITU-T P.800 (1996)**

The standard defines how to run the test so that results from different laboratories can be compared: rating scales, listener selection, speech material, playback conditions and reference conditions.

</div>
</div>

<!--
Emphasise that the MOS is the average over a whole condition, not the opinion of one person on one sentence.
Individual ratings are noisy — the averaging is what makes the number useful.
-->

---

# Three rating scales of ITU-T P.800

<img class="lecture-diagram" src="/figures/05/rating-scales.svg" alt="Three rating scales. ACR: 5 Excellent, 4 Good, 3 Fair, 2 Poor, 1 Bad. DCR: 5 degradation inaudible, 4 audible but not annoying, 3 slightly annoying, 2 annoying, 1 very annoying. CCR: a seven-point scale from +3 much better to −3 much worse." />

<div class="pt-2 text-sm">

**ACR** is the default and the basis of almost every objective model. **DCR** is more sensitive to small degradations because the listener hears the clean reference first. **CCR** also detects *improvements* — for example a noise-suppression algorithm that makes the output better than its input.

</div>

<!--
Lab 03 runs ACR and DCR on the same set of recordings, so students see directly that the two scales
do not produce interchangeable numbers. Note that the Czech labels in the original slides (vynikající, dobrá,
průměrná, nízká, špatná) are a translation of the ACR scale.
-->

---

# How a listening test is run

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div>

**Listeners**
- **naive** — not involved in speech-quality work, so they rate as ordinary telephone users would
- tens of listeners per test, each hearing every condition

**Material**
- short sentence pairs (a few seconds) from several male and female talkers
- presented in **randomised order** to cancel learning and fatigue effects

</div>
<div>

**Environment**
- quiet, acoustically controlled room
- calibrated playback level through a standard handset or headphones

**Anchors**
- reference conditions such as the **MNRU** (Modulated Noise Reference Unit, ITU-T P.810) — noise of known SNR added to the speech — let results of different laboratories be aligned

</div>
</div>

<div class="pt-4 vsb-muted text-sm">

A single test with 24 listeners, 4 talkers and 20 conditions already needs almost 2 000 ratings — which is exactly why objective models exist.

</div>

<!--
The numbers in the footer are illustrative, not prescribed by P.800. The key point for students: MOS values
are only comparable when the conditions under which they were collected were comparable, and the anchors
are what makes that possible across laboratories and languages.
-->

---

# MOS is a statistic — report it with its uncertainty

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

For one condition rated by $N$ listeners with scores $x_i$:

$$
\mathrm{MOS} = \frac{1}{N}\sum_{i=1}^{N} x_i
$$

$$
s = \sqrt{\frac{1}{N-1}\sum_{i=1}^{N}\left(x_i-\mathrm{MOS}\right)^2}
$$

$$
\mathrm{CI}_{95\,\%} = \mathrm{MOS} \pm t_{0.975,\,N-1}\,\frac{s}{\sqrt{N}}
$$

</div>
<div class="text-sm">

**Three caveats** (Streijl, Winkler & Hands, 2016):

- The ACR scale is **ordinal** — "Good" is not guaranteed to be exactly twice as far from "Poor" as "Fair" is. The mean is used by convention; distributions and percentages "Good or better" carry extra information.
- Listeners avoid the scale ends, so even clean speech rarely scores above **≈ 4.5**.
- MOS values depend on the **context of the test** — the same sample scores higher among bad conditions than among good ones.

</div>
</div>

<!--
The t-quantile for N−1 = 23 degrees of freedom is 2.07; for large N it approaches 1.96. The scale-context
effect is why a MOS from one test must not be compared with a MOS from another test without anchors.
-->

---

# Checkpoint — are the two codecs different?

<div class="checkpoint-question">

In one ACR test with 24 listeners, codec A scores MOS 3.6 and codec B scores MOS 3.8. Both have a sample standard deviation of 0.8. Can you claim that codec B is better?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Not from these numbers.** The 95 % half-width is $2.07 \cdot 0.8/\sqrt{24} \approx 0.34$, so A lies in $3.6 \pm 0.34$ and B in $3.8 \pm 0.34$ — the intervals overlap widely. A difference of 0.2 MOS needs either many more listeners (the half-width shrinks only with $\sqrt{N}$) or a more sensitive method such as DCR or CCR, which compares the codecs directly.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. To halve the interval to 0.17
you need four times as many listeners — about 100. A paired test is the cheaper route.
-->

---

# Naming the result — P.800.1 labels, DMOS and CMOS

<div class="grid grid-cols-2 gap-8 pt-1 text-sm">
<div>

**ACR results — ITU-T P.800.1 labels**

| Method | Listening | Conversational |
|---|---|---|
| **S**ubjective | MOS-LQS | MOS-CQS |
| **O**bjective | MOS-LQO | MOS-CQO |
| **E**stimated | MOS-LQE | MOS-CQE |

<div class="pt-1 vsb-muted">

Suffixes -N, -W, -S, -F: NB, WB, SWB, FB.

</div>

<div class="pt-2">

**Listening** — one recording: distortion, noise, loss. **Conversational** — two people talking: **delay and echo** count too. **O** — from signals (Part 2); **E** — from parameters (Part 3).

</div>

</div>
<div>

**DCR and CCR results — ITU-T P.800**

| Method | Scale | Result |
|---|---|---|
| ACR | 5 … 1, absolute quality | MOS |
| DCR | 5 … 1, degradation vs. reference | DMOS |
| CCR | +3 … −3, comparison of a pair | CMOS |

<div class="pt-2">

P.800.1 labels cover the **ACR scale only** — DMOS and CMOS keep their own names and are never mixed with MOS:

- **DMOS 4** = "audible but not annoying", not "good".
- **CMOS 0** = "no difference"; signs are re-coded to the (reference, processed) order before averaging (P.800 Annex E).

</div>
</div>
</div>

<!--
The left table is ITU-T P.800.1 and it is the vocabulary for the rest of the lecture. Insist that students
label every number they report in Lab 03: a PESQ result is MOS-LQO, an E-model result is MOS-CQE, a
classroom ACR test is MOS-LQS, and the classroom DCR test gives a DMOS — not a MOS. Without the CCR re-coding
step, the scores of the two presentation orders cancel and every condition averages to about 0.
-->

---
layout: section
---

# Part 2
## Objective, signal-based models

---

# Three families of objective models

<img class="lecture-diagram" src="/figures/05/model-families.svg" alt="A reference speech signal passes through the system under test and comes out degraded. The intrusive model uses both reference and degraded signal; the non-intrusive model uses the degraded signal only; the parametric model uses network parameters and no audio." />

<div class="pt-2 text-sm">

**Intrusive** (full-reference) models need a test call with known speech — ideal for laboratories and drive tests. **Non-intrusive** models can monitor live traffic, but must guess what the clean signal was. **Parametric** models need no audio at all and work even at the planning stage.

</div>

<!--
The rest of Part 2 covers the first two families; Part 3 is the E-model. In-service parametric monitoring
probes read RTP/RTCP statistics (loss, jitter, codec) from live traffic; ITU-T P.564 specifies how such
models are conformance-tested.
-->

---

# PESQ — ITU-T P.862 (2001, withdrawn 2024)

<img class="lecture-diagram" src="/figures/05/pesq-pipeline.svg" alt="Six processing steps of PESQ: level alignment and handset filtering, time alignment, auditory transform into Bark bands and loudness, disturbance as loudness difference, a cognitive model with asymmetry and aggregation, and a mapping from the raw score to MOS-LQO." />

<div class="pt-2 text-sm">

The core idea: transform both signals into an **internal representation of what the ear perceives** and measure the difference there, not in the waveform. The cognitive model penalises **added** components (noise, artefacts) more than **missing** ones — listeners find them more annoying.

<div class="pt-1 vsb-muted text-sm">

ITU-T deleted the P.862 family in January 2024 in favour of P.863 (POLQA). PESQ remains the most widely published baseline, and its reference code is freely available — which is why Lab 03 still uses it.

</div>

</div>

<!--
Rix, Beerends, Hollier and Hekstra, ICASSP 2001. Step 2 is what made PESQ suitable for VoIP: earlier models
(PSQM, P.861) failed when the delay changed during a call because the jitter buffer adapted; PESQ re-aligns
every utterance separately. The Lp aggregation (different norms over time and frequency) is how the model
reproduces that a short loud click hurts more than its average energy suggests.
-->

---

# From raw PESQ to MOS-LQO — and what PESQ cannot see

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

The raw score (−0.5 … 4.5) is mapped to the ACR scale by **P.862.1**:

$$
\mathrm{MOS\text{-}LQO} = 0.999 + \frac{4}{1 + e^{-1.4945\,x + 4.6607}}
$$

For wideband speech, **P.862.2** uses the same shape with coefficients $1.3669$ and $3.8224$.

<div class="pt-2 text-sm vsb-muted">

Always report which output you use — raw PESQ and MOS-LQO differ by up to about 0.4 in the middle of the scale.

</div>

</div>
<div class="text-sm">

**Outside the scope of P.862** — inaccurate or not intended (Table 2):

- delay in conversation, talker echo — it is a **listening** model
- sidetone, listening level and loudness loss (signals are level-aligned to 79 dB SPL first)
- in-service, non-intrusive measurement

**Not validated in the 2001 edition** (Table 3): music, codecs below 4 kbit/s, echo cancellers, noise reduction — and **packet loss with PCM codecs and PLC**. Keep that in mind when you score netem-degraded G.711 in Lab 03.

</div>
</div>

<!--
The P.862.1/P.862.2 coefficients match the ITU-T reference C code (pesqmain.h). Lab 03 prints the mapped
score where the binary provides it; students should label it MOS-LQO and keep the raw value separate.
-->

---

# Beyond PESQ — POLQA, ViSQOL and the bandwidth question

<img class="lecture-diagram" src="/figures/05/bandwidths.svg" alt="Audio bandwidth classes on a logarithmic frequency axis: narrowband 300 to 3400 hertz, wideband 50 to 7000, super-wideband 50 to 14000, fullband 20 to 20000, each with typical codecs and the matching quality standards." />

<div class="grid grid-cols-2 gap-6 pt-1 text-sm">
<div>

**POLQA, ITU-T P.863 (2011, current edition 2018)** — PESQ's successor and official replacement: narrowband, super-wideband and fullband modes, better handling of time-scaling and modern codecs.

</div>
<div>

**ViSQOL (Google, open source)** — compares spectro-temporal similarity of the two signals; speech and audio modes. Used in Lab 03.

</div>
</div>

<!--
Beerends et al. (JAES 2013) describe POLQA; Hines et al. (2015) and Chinen et al. (2020) describe ViSQOL.
POLQA is licensed, which is why the lab uses PESQ and ViSQOL. Upsampling narrowband audio for a wideband
model does not add the missing high frequencies — the model will simply rate it as band-limited.
-->

---

# Non-intrusive signal-based models

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**ITU-T P.563 (2004)** — single-ended narrowband model

Reconstructs a plausible clean signal from the degraded one using a model of human speech production (vocal tract), then evaluates the distortion classes it detects: noise, temporal clipping, robotisation, unnatural pitch. Accuracy is clearly below the intrusive models.

</div>
<div class="border border-gray-400 p-4">

**Learned models — DNSMOS and similar**

Deep networks trained directly on large crowdsourced ACR databases (ITU-T P.808 methodology). They predict MOS from the degraded signal alone and are widely used to rank noise suppressors — but they inherit the bias of their training data and are not standardised.

</div>
</div>

<div class="pt-4 vsb-muted text-sm">

Non-intrusive models are the only signal-based option for **live monitoring**, where the original speech is never available.

</div>

<!--
Malfait, Berger and Kastner (IEEE TASLP 2006) is the reference for P.563. DNSMOS is from Reddy, Gopal and
Cutler (ICASSP 2021). The trade-off is the same one as in the model-families figure: less input information,
lower accuracy, easier deployment.
-->

---

# Checkpoint — the satellite hop

<div class="checkpoint-question">

A call is routed over a geostationary satellite, adding 270 ms of one-way delay. There is no loss and the codec is G.711. You record both ends and run PESQ. What score do you expect, and does it describe the user's experience?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**PESQ will report nearly clean quality (MOS-LQO above 4)** — its time-alignment step removes the constant delay before comparing the signals, exactly as designed. But the delay degrades **conversational** quality: users talk over each other and any residual echo becomes clearly audible. PESQ produces a listening-quality score; the conversational effect has to come from a conversation test or from a model that includes delay — the E-model in Part 3.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. This is question 5 of the
Lab 03 README in disguise.
-->

---
layout: section
---

# Part 3
## The E-model — ITU-T G.107

---

# The idea behind the E-model

<div class="pt-2">

Developed by ETSI and adopted as ITU-T G.107 (first edition 1998) as a **transmission-planning tool**: predict the quality of a connection that does not exist yet, from the parameters of its components.

</div>

<div class="grid grid-cols-2 gap-6 pt-4 text-sm">
<div class="border border-gray-400 p-4">

**Additivity on a psychological scale**

Each impairment is expressed as a number on one common scale, the **transmission rating R** (0–100 for narrowband). Impairments are assumed to be independent, so their contributions are **subtracted** from a best-case value.

</div>
<div class="border border-gray-400 p-4">

**What it is — and is not**

The output is an **estimate** (MOS-CQE) for an average user. G.107 states that such estimates are made "only for transmission planning purposes and not for actual customer opinion prediction".

</div>
</div>

<!--
The additivity assumption is what makes the E-model easy to compute and easy to reason about: one number per
impairment, one budget. It is also its main weakness — when several strong impairments occur together, the
real degradation can be smaller than the sum. G.107 Annex A itself lists additivity as "not checked to a
satisfactory extent" (see also Möller 2000; Raake 2006).
-->

---

# The reference connection

<img class="lecture-diagram" src="/figures/05/emodel-connection.svg" alt="E-model reference connection: send side with send loudness, room noise, sidetone and handset factor; network with codec impairment, packet loss and robustness, delays, echo and noise; receive side with receive loudness, room noise, listener sidetone and handset factor. All feed R equals Ro minus Is minus Id minus Ie-eff plus A." />

<div class="pt-2 text-sm">

Around twenty input parameters, each with a **default value** in G.107. For a VoIP study most stay at their defaults; the ones that change are **delay**, the **codec** (Ie, Bpl), **packet loss** (Ppl, BurstR) and **echo** (TELR).

</div>

<!--
The defaults describe a good narrowband wirebound connection. Loudness ratings (SLR, RLR, OLR) are in dB and
come from electro-acoustic measurements of the terminals; students do not need to derive them.
-->

---

# The rating formula

$$
R = R_o - I_s - I_d - I_{e\text{-}\mathrm{eff}} + A
$$

<div class="text-sm pt-2">

| Term | Meaning | Depends on | Default |
|---|---|---|---|
| $R_o$ | basic signal-to-noise ratio | circuit and room noise, loudness | 94.77 |
| $I_s$ | simultaneous impairments | loudness, sidetone, quantizing noise | 1.41 |
| $I_d$ | delay impairments | one-way delay, echo (TELR, WEPL) | 0.15 |
| $I_{e\text{-}\mathrm{eff}}$ | effective equipment impairment | codec, packet loss, burstiness | 0 |
| $A$ | advantage (expectation) factor | the user's situation | 0 |

</div>

<div class="pt-2">

With all defaults: $R = 94.77 - 1.41 - 0.15 - 0 + 0 \approx \mathbf{93.2}$ — the best a narrowband connection can achieve.

</div>

<!--
The first two terms describe the terminals and the analogue path; for VoIP planning they stay at their
defaults, so R ≈ 93.2 − Id − Ie-eff + A. That simplified form is what the rest of Part 3 uses.
-->

---

# From R to MOS and to user satisfaction

<img class="lecture-diagram" src="/figures/05/r-to-mos.svg" alt="MOS as an S-shaped function of R from 1 at R equals 0 to 4.5 at R equals 100, with G.109 bands: 90 to 100 very satisfied, 80 to 90 satisfied, 70 to 80 some users dissatisfied, 60 to 70 many dissatisfied, 50 to 60 nearly all dissatisfied, below 50 not recommended. The default R of 93.2 maps to MOS 4.41." />

<div class="pt-1 text-sm">

For $R \le 0$, MOS = 1; for $R \ge 100$, MOS = 4.5. The categories are from ITU-T **G.109**; R below 50 is not recommended for any service.

</div>

<!--
The mapping is G.107 Annex B. Note it saturates at 4.5, not 5 — consistent with the ACR ceiling from Part 1.
The curve is dashed above R = 93.2: that is the rating with every G.107 parameter at its default — a perfect
narrowband connection — so no narrowband call can score higher. Annex B still defines MOS up to R = 100 (and
4.5 beyond), but that part of the scale is only reached on the extended wideband/fullband scales of G.107.1
and G.107.2, where R is first divided by 1.29 or 1.48 (see Extras).
At the other end (red, dashed), the Annex B polynomial is defined for 0 < R < 100 but falls slightly below
MOS 1 (minimum ≈ 0.99) for R < 6.5. There the mapping is not monotonic — two values of R give the same
MOS — so G.107 Appendix I inverts it (MOS → R) only for 6.5 ≤ R ≤ 100. In practice, treat anything below
R ≈ 6.5 as MOS 1: such a connection is unusable anyway, far inside the "not recommended" region.
R is linear in impairments, MOS is not: 10 points of R cost 0.3 MOS at the top of the scale and 0.5 in the
middle.
-->

---

# Delay impairment $I_d$ — delay and echo together

<img class="lecture-diagram" src="/figures/05/r-vs-delay.svg" alt="R from 50 to 100 against one-way delay from 0 to 500 milliseconds for talker echo loudness ratings of 65, 60, 55, 50 and 45 decibels. With 65 dB echo loss R stays near 90 up to 150 ms; with 45 dB it falls below 70 at about 100 ms." />

<div class="pt-1 text-sm">

$I_d = I_{dte} + I_{dle} + I_{dd}$: **talker echo**, **listener echo**, and **pure delay** ($I_{dd} = 0$ below 100 ms). A higher TELR means better echo cancellation. The 150 ms guideline from Lecture 03 (ITU-T G.114) is where R starts to fall steeply even with good echo control.

</div>

<!--
Curves computed from the G.107 (06/2015) formulas with all other parameters at default, T = Ta and Tr = 2T,
default delay-sensitivity class (sT = 1, mT = 100 ms); script in scripts/generate-figures.py. The original course figure had the same layout
and TELR values but was computed with the 1998 E-model, whose default R was 94.2 (G.107 notes the change to
93.2 in 2000) — so every curve here sits exactly one R point below the original. The 2015 edition
also defines "low" and "very low" delay-sensitivity classes for non-interactive use — the default class is
mandatory for carrier- and enterprise-grade telephony. The original course material showed the same family of curves. The practical
message: an echo canceller is worth more than shaving 50 ms from the path — compare the vertical spread of the
curves at 150 ms with the slope of any one curve.
-->

---

# Equipment impairment $I_e$ — the codec

<div class="grid grid-cols-[2fr_1fr] gap-6 pt-1">
<div class="text-sm">

| Codec | kbit/s | $I_e$ | Listen |
|---|---|---|---|
| G.711 PCM | 64 | 0 | <AudioClip src="/audio/05/g711-alaw.wav" label="64" /> |
| G.726/G.727 ADPCM | 40 · 32 · 24 · 16 | 2 · 7 · 25 · 50 | <AudioClip src="/audio/05/g726-40k.wav" label="40" /><AudioClip src="/audio/05/g726-32k.wav" label="32" /><AudioClip src="/audio/05/g726-24k.wav" label="24" /><AudioClip src="/audio/05/g726-16k.wav" label="16" /> |
| G.728 LD-CELP | 16 · 12.8 | 7 · 20 | — |
| G.729A CS-ACELP | 8 | 10 | <AudioClip src="/audio/05/g729a.wav" label="8" /> |
| G.729A + VAD | 8 | 11 | <AudioClip src="/audio/05/g729a-vad.wav" label="8" /><AudioClip src="/audio/05/g729a-vad-nocng.wav" label="CNG off" /> |
| G.723.1 MP-MLQ, ACELP | 6.3 · 5.3 | 15 · 19 | <AudioClip src="/audio/05/g723-1-6k3.wav" label="6.3" /> |

</div>
<div class="text-sm">

Values from **ITU-T G.113, Appendix I**, from subjective tests of each codec without transmission errors.

- $I_e$ is **not** proportional to bit rate — LD-CELP at 16 kbit/s beats ADPCM at 24 kbit/s: it models speech, not the waveform.
- Transcoding (G.729 → G.711 → G.729) adds the impairments of every stage.

<div class="pt-2">

Reference, 128 kbit/s linear PCM: <AudioClip src="/audio/05/reference.wav" label="original" />

</div>

<div class="pt-1 text-xs vsb-muted">

Speech: Open Speech Repository. G.728 and G.723.1 at 5.3 kbit/s have no freely available encoder.

</div>
</div>
</div>

<!--
The table is the original course table, checked against G.113. Ask students to find the break-even point:
G.729 at 8 kbit/s costs 10 R points, G.711 at 64 kbit/s costs none — is the bandwidth saving worth it? That
depends on what else the budget has to absorb, which the next slides quantify.
Listening: play the original, then G.726 from 40 down to 16 kbit/s (Ie 2 → 50: the hiss grows steadily), then
G.729A and G.723.1 — much lower bit rates than G.726-16, yet cleaner, because they model speech instead of
the waveform. VAD: G.729A with and without VAD sound almost the same — that is the point of Annex B's
comfort-noise generation (CNG), which fills the frames VAD stops sending with noise matched to the background.
"CNG off" is the same bitstream with those frames played as silence (a teaching illustration, not a codec
mode): listen for the background hiss cutting out in the pause between the sentences and at the end. VAD
dropped 58 of 730 frames here (8 %); in a real conversation each side is silent roughly half the time, which
is where the bandwidth saving comes from. Samples: two sentences (7.3 s) encoded and decoded with ffmpeg
(G.711, G.726, G.723.1) and bcg729 (G.729A/B); regenerate with `python3 scripts/generate-codec-samples.py`.
The players work in `npm run dev` and the built site, not in the PDF export.
Wideband codecs (G.722, AMR-WB, Opus) are rated on the extended wideband scale of G.107.1 — see Extras.
-->

---

# Effective equipment impairment — adding packet loss

$$
I_{e\text{-}\mathrm{eff}} = I_e + (95 - I_e)\,\frac{P_{pl}}{\dfrac{P_{pl}}{\mathit{BurstR}} + B_{pl}}
$$

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div>

- $P_{pl}$ — packet-loss probability \[%\]
- $B_{pl}$ — **packet-loss robustness factor** of the codec and its concealment (PLC), from G.113
- 95 — the ceiling: at total loss, $I_{e\text{-}\mathrm{eff}} \to 95$ and nothing is left

</div>
<div>

**BurstR** — burst ratio: the mean length of observed loss bursts divided by the mean length expected for random loss.

- $\mathit{BurstR} = 1$ — random (Bernoulli) loss
- $\mathit{BurstR} > 1$ — bursty loss; for Lecture 04's **simple Gilbert model** $\mathit{BurstR} = 1/(p+q)$
- validated only up to $\mathit{BurstR} = 2$, or beyond that for $P_{pl} < 2\,\%$ (G.107 Annex A)

</div>
</div>

<!--
This slide connects directly to Lecture 04: the Markov loss models there give BurstR directly (G.107 eq. 7-30).
Ppl must be measured at the output of the jitter buffer — late packets discarded there count as lost (G.113). With p the
probability of entering the loss state and q of leaving it, a Bernoulli process has p + q = 1 and BurstR = 1.
Longer bursts (small q) increase BurstR and push Ie-eff up for the same average loss.
-->

---

# $I_e$ against packet loss — tabulated values

<img class="lecture-diagram" src="/figures/05/ie-vs-loss.svg" alt="Tabulated Ie against packet loss from ITU-T G.113 Appendix I, 1999. G.711 without PLC rises steeply to 55 at 5 percent. G.711 with PLC rises slowly to 45 at 20 percent under random loss, but jumps to 30 at 5 percent under bursty loss. G.729A and G.723.1 with VAD start at 11 and 15 and reach 49 and 55 at 16 percent. GSM EFR starts at 5 and reaches 33 at 5 percent." />

<div class="pt-1 text-sm">

**Concealment matters**: 1 % loss costs G.711 25 R points without PLC, 5 with it. **So does burstiness**: at 5 % loss, 30 vs 15. The $I_{e\text{-}\mathrm{eff}}$ formula was fitted to these values (G.729A, 8 %: table 36, formula 35.9).

</div>

<!--
Data: Tables I.2 and I.3 of ITU-T G.113 Appendix I (09/1999), provisional planning values from subjective
tests — the same data as the figure in the original course slides. The G.711-without-PLC column was withdrawn
in the 10/2001 edition as "too pessimistic"; the other columns are unchanged there. From 05/2002 the tables
were replaced by the Bpl robustness factors and the Ie-eff formula of the previous slide (G.107 Annex A:
"results very similar to those previously defined as Ie").
Formula vs table, random loss: G.729A 2 % 19.0 vs 19, 16 % 49.4 vs 49; GSM EFR 5 % 35 vs 33; G.711+PLC 10 %
27.1 vs 25; G.711 without PLC 1 % 17.9 vs 25 — the withdrawn column is where they disagree most.
The crossing of the G.711-no-PLC curve over the compressed codecs below 1 % loss is a good discussion point:
an uncompressed codec is only the best choice on a clean network.
-->

---

# $B_{pl}$ and the advantage factor $A$

<div class="grid grid-cols-2 gap-8 pt-2">
<div class="text-sm">

| Codec | $I_e$ | Packet \[ms\] | $B_{pl}$ |
|---|---|---|---|
| G.723.1 + VAD | 15 | 30 | 16.1 |
| G.729A CS-ACELP + VAD | 11 | 20 | 19.0 |
| GSM EFR | 5 | 20 | 10.0 |
| G.711, no PLC | 0 | 10 | 4.3 |
| G.711 with PLC | 0 | 10 | 25.1 |

<div class="pt-1 vsb-muted">Source: ITU-T G.113 (2024), Appendix I, Table I.4.</div>

</div>
<div class="text-sm">

| Communication system | $A$ (max.) |
|---|---|
| Conventional wirebound | 0 |
| Mobility within a building | 5 |
| Mobility in a geographical area or in a vehicle | 10 |
| Hard-to-reach locations, e.g. multi-hop satellite | 20 |

<div class="pt-1 vsb-muted">Source: ITU-T G.107, provisional values.</div>

<div class="pt-3">

$A$ models **user expectation**: people accept lower quality in exchange for convenience or access. It is an upper bound, not a mandatory bonus.

</div>
</div>
</div>

<!--
Correction compared with the original slides: G.107 gives A = 0 for a fixed terminal and 10 for a cellular
phone in motion; the values 15/5/15/20 in the earlier deck were a transcription error. A is controversial —
expectations change over time (mobile quality is now expected to match fixed), so most planners set A = 0.
-->

---

# A simplified E-model for VoIP

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

With terminals and echo control at their defaults:

$$
R \approx 93.2 - I_d - I_{e\text{-}\mathrm{eff}} + A
$$

Cole & Rosenbluth (2001) fit the delay term, for good echo cancellation, with one line and a knee:

$$
I_d \approx 0.024\,d + 0.11\,(d - 177.3)\,H(d - 177.3)
$$

where $d$ is the one-way delay in ms and $H$ the unit step function.

</div>
<div class="text-sm">

**Why it is useful**

- Only three measurable inputs — **delay, loss, codec** — all available from RTP/RTCP statistics.
- Easy to compute in a monitoring probe for every call.
- Close to the full model where it matters: at $d = 150$ ms it gives $I_d = 3.6$, the full G.107 computation 3.8.

**What it ignores**

- noise, loudness, sidetone and echo loss other than the default — and every impairment the default terminal does not have.

</div>
</div>

<!--
The original course slides used the simplification "Id = 0 below 100 ms"; the Cole-Rosenbluth line is
a better approximation that students can still evaluate by hand. The knee at 177.3 ms is where the slope of the
delay impairment increases sharply — the same bend visible in the TELR = 65 dB curve two slides back.
-->

---

# Worked example — G.729A over a lossy path

<div class="grid grid-cols-2 gap-8 pt-1 text-sm">
<div>

**Given:** G.729A + VAD ($I_e = 11$, $B_{pl} = 19$), 2 % random loss, one-way delay 150 ms, good echo control, fixed terminal ($A = 0$).

**1 · Effective equipment impairment**

$$
I_{e\text{-}\mathrm{eff}} = 11 + 84 \cdot \frac{2}{2 + 19} = 19.0
$$

**2 · Delay impairment** (G.107, TELR = 65 dB): $I_d \approx 3.8$

**3 · Rating**

$$
R = 94.77 - 1.41 - 3.8 - 19.0 + 0 \approx 70.5
$$

</div>
<div>

**4 · MOS**

$$
\begin{aligned}
\mathrm{MOS} &= 1 + 0.035 \cdot 70.5 \\
&\quad + 70.5 \cdot 10.5 \cdot 29.5 \cdot 7 \cdot 10^{-6} \\
&= 1 + 2.47 + 0.15 \approx 3.62
\end{aligned}
$$

**Verdict:** *some users dissatisfied*, just above the 70 boundary.

<div class="pt-2 border border-gray-400 p-3">

The same path with **G.711 + PLC** ($I_{e\text{-}\mathrm{eff}} = 7.0$): $R \approx 82.5$, MOS ≈ 4.12 — *satisfied*. On this path the 56 kbit/s saved by G.729A costs one satisfaction category.

</div>
</div>
</div>

<!--
Work through this on the board. All numbers were checked against the implementation used for the figures.
Ask: what loss rate would push the G.729A call below R = 60? (Solve 93.2 − 3.8 − Ie-eff = 60 → Ie-eff = 29.4,
so Ppl ≈ 5.3 % for random loss.)
-->

---

# Checkpoint — can the advantage factor rescue a design?

<div class="checkpoint-question">

A planner computes R = 55 for a VoIP service to a remote research station reached over two satellite hops. They add $A = 20$, obtain R = 75, and declare the service acceptable. Is this legitimate?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Formally allowed, but it hides the problem.** $A$ represents users' willingness to accept worse quality in exchange for access — here plausible, since there is no alternative. But the audio is exactly as bad as R = 55 says; $A$ changes the predicted **satisfaction**, not the signal. A defensible report states both values, and first checks whether $I_d$ or $I_{e\text{-}\mathrm{eff}}$ can be reduced — echo control or a more robust codec is a real improvement, $A$ is not.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. The distinction between the
quality of the signal and the satisfaction of the user is the QoS/QoE distinction from Lecture 03 again.
-->

---

# Common mix-ups

<div class="grid grid-cols-3 gap-4 pt-2 text-sm">
<div class="border border-orange-400 p-3">

**MOS-LQO vs. MOS-CQE**

PESQ produces a listening score from signals; the E-model estimates a conversational score from parameters. Similar numbers, different meanings.

</div>
<div class="border border-orange-400 p-3">

**R vs. MOS**

R is additive in impairments; MOS is not. Subtract impairments on the R scale, then convert once.

</div>
<div class="border border-orange-400 p-3">

**"PESQ says the call is fine"**

PESQ removes delay before scoring and ignores echo and sidetone. It cannot judge a conversation.

</div>
<div class="border border-orange-400 p-3">

**Ie vs. Ie-eff**

$I_e$ is the codec on a perfect network; $I_{e\text{-}\mathrm{eff}}$ adds packet loss through $B_{pl}$ and BurstR.

</div>
<div class="border border-orange-400 p-3">

**Wrong bandwidth**

Narrowband PESQ on wideband audio, or comparing narrowband R (max. 93.2) with wideband R (max. 129), gives meaningless results.

</div>
<div class="border border-orange-400 p-3">

**MOS without a confidence interval**

A MOS difference smaller than the interval half-width is not a difference.

</div>
</div>

<!--
Six confusions seen most often in Lab 03 reports and exam answers.
-->

---

# Summary — three ways to put a number on speech quality

<div class="grid grid-cols-2 gap-x-10 gap-y-2 pt-2 text-sm">

<div>

**Subjective tests are the reference**
ACR, DCR and CCR (P.800) produce MOS-LQS or MOS-CQS; always with a confidence interval, always in the context of the test.

**Intrusive models compare two signals**
PESQ, POLQA and ViSQOL model hearing and judgement; accurate for listening quality in their bandwidth, blind to delay and echo.

</div>
<div>

**Non-intrusive models listen to one signal**
P.563 or learned models such as DNSMOS enable live monitoring at lower accuracy.

**The E-model plans from parameters**
$R = R_o - I_s - I_d - I_{e\text{-}\mathrm{eff}} + A$; delay with echo, codec with loss and burstiness, mapped to MOS-CQE and G.109 satisfaction categories.

</div>

</div>

<!--
Read them aloud, one sentence each. Then the exit questions.
-->

---

# Exit questions — use the ideas

1. Why is a DCR test more sensitive than an ACR test to a small codec degradation, and what does it cost you?
2. A monitoring system reports MOS 4.3 for every call on a link with 250 ms one-way delay. Which kind of model is it probably using, and what is it missing?
3. Two paths have the same 2 % average loss, one random and one with Gilbert parameters $p = 0.01$, $q = 0.49$. Which gets the higher $I_{e\text{-}\mathrm{eff}}$ for G.711 without PLC, and by how much?
4. Why does the E-model's MOS never exceed 4.5, and why is that consistent with Part 1?

<div v-click class="pt-5 vsb-muted">

**Explain the mechanism**, not just the name.

</div>

<!--
Allow two minutes for individual answers, then discuss. Answers: (1) the listener hears the reference first
and rates the difference, so small changes are not masked by the scale context; it costs the need for a
reference and longer sessions. (2) An intrusive listening model, or a parametric model that ignores delay; it
misses the conversational effect of delay and any echo. (3) The Gilbert path: loss p/(p+q) = 2 %, BurstR = 1/0.5 = 2 (the edge of the validated range),
Ie-eff = 95·2/(2/2 + 4.3) ≈ 35.8 versus 95·2/(2 + 4.3) ≈ 30.2 for random loss — about 5.6 R points worse.
With PLC (Bpl = 25.1) the same comparison gives only 7.3 vs 7.0: concealment makes burstiness matter less. (4) The mapping was fitted to ACR
tests, where listeners rarely give the top score; a model can only predict the scale it was trained on.
-->

---

# Where you use this — Lab 03

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

Lab 03 builds the whole chain of this lecture on a real VoIP call:

- inject delay, jitter and loss with `tc netem` (Lecture 03)
- extract the audio from the captured RTP stream
- run **ACR and DCR** tests with your classmates → MOS-LQS, DMOS
- score the same recordings with **PESQ and ViSQOL** → MOS-LQO
- compare the rankings — and compute the E-model estimate for the same conditions by hand

</div>
<div>

<div class="text-sm">

Label every number with its P.800.1 name and, for subjective scores, its confidence interval.

</div>

<div class="pt-4 text-sm vsb-muted">

```bash
ssh <lab-server>
cd qos-03 && uv sync
uv run jupyter lab --ip 0.0.0.0
```

</div>
</div>
</div>

<!--
The E-model calculation is not in the notebook; it is a good extension task for students who finish early:
take the netem settings of each condition, assume G.711 with PLC, and compare the MOS-CQE with the measured
MOS-LQS. The disagreement where delay is large is the point of the lab.
-->

---

# References — standards

- ITU-T P.800, *Methods for subjective determination of transmission quality*, 1996.
- ITU-T P.800.1, *Mean opinion score (MOS) terminology*, 2016. ITU-T P.10/G.100, *Vocabulary for performance, quality of service and quality of experience*, 2017.
- ITU-T P.810, *Modulated noise reference unit (MNRU)*, 1996.
- ITU-T P.862, *Perceptual evaluation of speech quality (PESQ)*, 2001; P.862.1 (mapping to MOS-LQO), 2003; P.862.2 (wideband extension), 2005 — all withdrawn January 2024.
- ITU-T P.863, *Perceptual objective listening quality prediction*, 2018 (first edition 2011).
- ITU-T P.563, *Single-ended method for objective speech quality assessment in narrow-band telephony applications*, 2004.
- ITU-T G.107, *The E-model: a computational model for use in transmission planning*, 2015; G.107.1 (wideband) and G.107.2 (fullband), 2019.
- ITU-T G.113, *Transmission impairments due to speech processing*, 2024. ITU-T G.109, *Definition of categories of speech transmission quality*, 1999.

<!--
Current editions are on itu.int and freely downloadable (the withdrawn P.862 texts no longer are). The Ie and
Bpl tables on the slides are G.113 Appendix I — unchanged since 2007, the 2024 edition adds LC3plus; the R–MOS
mapping, the delay formulas and the A table are G.107 (06/2015).
-->

---

# References — literature

- A. W. Rix, J. G. Beerends, M. P. Hollier, A. P. Hekstra, "Perceptual evaluation of speech quality (PESQ) — a new method for speech quality assessment of telephone networks and codecs," *Proc. IEEE ICASSP*, vol. 2, 749–752, 2001.
- J. G. Beerends et al., "Perceptual Objective Listening Quality Assessment (POLQA), the third generation ITU-T standard for end-to-end speech quality measurement, Part I — Temporal alignment," *J. Audio Eng. Soc.*, 61(6), 366–384, 2013.
- A. Hines, J. Skoglund, A. C. Kokaram, N. Harte, "ViSQOL: an objective speech quality model," *EURASIP J. Audio, Speech, and Music Processing*, 2015:13.
- L. Malfait, J. Berger, M. Kastner, "P.563 — The ITU-T standard for single-ended speech quality assessment," *IEEE Trans. Audio, Speech, and Language Processing*, 14(6), 1924–1934, 2006.
- R. G. Cole, J. H. Rosenbluth, "Voice over IP performance monitoring," *ACM SIGCOMM Computer Communication Review*, 31(2), 9–24, 2001.
- R. C. Streijl, S. Winkler, D. S. Hands, "Mean opinion score (MOS) revisited: methods and applications, limitations and alternatives," *Multimedia Systems*, 22(2), 213–227, 2016.
- S. Möller, *Assessment and Prediction of Speech Quality in Telecommunications*, Kluwer, 2000. A. Raake, *Speech Quality of VoIP*, Wiley, 2006.

<!--
Möller and Raake are the two textbooks to recommend for students who want the full derivation of the E-model
and its limits. DNSMOS: C. K. A. Reddy, V. Gopal, R. Cutler, ICASSP 2021.
-->

---
layout: end
---

# Thank you for your attention

<div class="pt-6 opacity-85">

Jan Rozhon, Miroslav Vozňák

+420 596 995 900 &middot; jan.rozhon@vsb.cz

</div>

<!--
Manual 5.4 (R25): closing slide carries presenter name, phone and e-mail.
-->

---
layout: section
---

# Extras
## Wideband E-model and the limits of additivity

<!--
Not part of the timed 90-minute route. Use to answer questions or extend an advanced class.
-->

---

# Extras — beyond narrowband: G.107.1 and G.107.2

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div>

The narrowband E-model tops out at $R \approx 93.2$ — the quality of a good PCM telephone. Wideband and fullband speech are **better than that**, so the scale is extended rather than rescaled:

| Model | Bandwidth | $R_{\max}$ |
|---|---|---|
| G.107 | narrowband | ≈ 93 |
| G.107.1 | wideband | 129 |
| G.107.2 | fullband | 148 |

</div>
<div>

A narrowband codec on the extended scale carries an extra impairment for its **missing bandwidth**. This is why a wideband call with some loss can still be rated better than a perfect narrowband call — and why R values must never be compared across the three scales without saying which one is used.

<div class="pt-4 vsb-muted">

To map an extended-scale R to MOS, G.107.1 first scales it back to the 0–100 range.

</div>
</div>
</div>

<!--
Useful when students ask why their smartphone's VoLTE/EVS calls sound better than "MOS 4.4". The
narrowband MOS scale simply has no room for better-than-telephone quality.
-->

---

# Extras — when additivity breaks

<div class="pt-2 text-sm">

The E-model assumes impairments add on the R scale. Subjective tests show systematic deviations (Möller 2000; Raake 2006):

</div>

<div class="grid grid-cols-2 gap-6 pt-4 text-sm">
<div class="border border-gray-400 p-4">

**Combined strong impairments**

When a low-bit-rate codec meets heavy loss, the measured degradation can be **smaller than the sum** — the listener's quality judgement saturates, while the model keeps subtracting.

</div>
<div class="border border-gray-400 p-4">

**Time-varying quality**

A burst of loss near the end of a call hurts more than the same burst at the start (**recency effect**). The E-model uses call-level averages and cannot express this; monitoring models that score short windows and pool them over time can.

</div>
</div>

<!--
Good closing thought for an advanced group: every model in this lecture is a regression on some set of
listening tests, and each breaks where its training data did not reach. That is the thesis slide again.
-->
