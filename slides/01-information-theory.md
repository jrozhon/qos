---
theme: seriph
title: 01 · Channel capacity and information theory
info: |
  440-2216/01 Kvalita služeb — lecture 1.
  Signals, PCM, Gaussian noise, SNR, the Shannon–Hartley theorem, and Hartley's and Shannon's measures of information.
  Companion lecture to Exercise 01.
exportFilename: 01-information-theory
layout: cover
transition: slide-left
mdc: true
lineNumbers: true
fonts:
  provider: none
  sans: Carlito
  mono: IBM Plex Mono
---

# Channel capacity and an introduction to information theory

### 440-2216/01 Kvalita služeb · Lecture 01

<div class="pt-6 text-sm vsb-muted">
Jan Rozhon, Miroslav Vozňák &middot; Department of Telecommunications, FEECS
</div>

<!--
Ninety minutes including checkpoints: 5 min motivation, 18 signals/PCM, 15 noise/SNR, 20 symbols/capacity,
10 network rates and qualitative MIMO, 17 information/entropy, 5 exit questions and exercise setup.
Parts 1–2 support Exercise 01 Step 1; Parts 2–4 support the metrics and noise experiments in Steps 2–4.
Part 5 introduces source coding. Keep the 90-minute route to the slides before the closing slide. The course overview, signal recap, biography, technology/English surveys, and mathematical extensions are Extras slides
after the closing slide; skip them in the main lecture.

If they have already opened the notebook, refer to the sliders — "remember what happened when you pushed sigma up".
-->

---

# Where we are going

<div class="grid grid-cols-3 gap-5 pt-4">

<div class="border border-gray-400 p-4">
<div class="text-sm opacity-60">Part 1</div>

### Signals and PCM

What carries information, and how an analog signal becomes bits: PCM, sampling, aliasing

<div class="text-xs opacity-60 pt-3">↔ Exercise 01, Step 1</div>
</div>

<div class="border border-gray-400 p-4">
<div class="text-sm opacity-60">Parts 2–4</div>

### Channel capacity

Gaussian noise, SNR, symbols vs bits, and the Shannon–Hartley bound

<div class="text-xs opacity-60 pt-3">↔ Exercise 01, Steps 2–4</div>
</div>

<div class="border border-gray-400 p-4">
<div class="text-sm opacity-60">Part 5</div>

### Information

Hartley's measure, Shannon entropy, and how a source model guides compression

<div class="text-xs opacity-60 pt-3">↔ README questions</div>
</div>

</div>

<div class="pt-8">

Two questions run through the whole lecture: **how many bits can a channel carry**, and **how many bits does a message actually need**.

</div>

<!--
The two questions lead to Shannon's channel-coding and source-coding theorems. Distinguish the information
produced by a source from the rate of a particular representation and the resources used to transport it.
-->

---

# What you should be able to do

1. Compute a PCM source rate from sampling frequency and bits per sample.
2. Convert SNR from decibels and calculate an AWGN capacity bound.
3. Distinguish source rate, raw coded bit rate, and delivered payload rate.
4. Calculate entropy and average code length for a small discrete source.

<div class="pt-6 vsb-muted">

Keep asking: **which signal, which channel, which rate, and which assumptions?**

</div>

<!--
These are the four outcomes for the lecture. Use the exit questions to check transfer, not just formula recall.
Students need arithmetic means, basic probability, and base-2/base-10 logarithms; introduce notation as it appears.
-->

---
layout: statement
---

# Channel conditions set a capacity limit

## QoS manages rate, delay, jitter, and loss within available resources

<!--
Capacity is defined for specified bandwidth, power, noise, and channel conditions. It can change when those
conditions change. QoS allocates resources and manages service performance within those constraints.
-->

---
layout: section
---

# Part 1
## Signals and PCM — from waveform to bits

---

# A signal is a physical quantity that carries information

<img class="lecture-diagram" src="/figures/01/comm-system.svg" alt="Source, transmitter, channel with noise added, receiver, destination." />

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

**In telecommunications** — a voltage, a current, an electromagnetic wave that varies in time.

</div>
<div>

**In information theory** — a sequence of input symbols or a waveform used to encode a message.

</div>
</div>

<!--
Same picture Shannon drew in 1948. Keep coming back to it: every later slide is about one box. Part 1 is the
transmitter, Part 2 is the noise arrow, Part 4 is the channel box, Part 5 is the source box.
-->

---

# Continuous time, discrete time

<img class="lecture-diagram" src="/figures/01/continuous-discrete.svg" alt="A continuous sine wave on the left; the same wave read at evenly spaced sampling instants on the right." />

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

Period $T$ \[s\] — duration of one repetition.
Frequency $f = 1/T$ \[Hz\] — repetitions per second.

</div>
<div>

Sampling period $T_s$ \[s\] — spacing of the samples.
Sampling frequency $f_s = 1/T_s$ \[Hz\] — samples per second.

</div>
</div>

<!--
Two frequencies on this slide and they are different things. f describes the signal, f_s describes what we do to
it. Students mix them up in the notebook constantly; name both explicitly here.
-->

---

# PCM in three steps

<img class="lecture-diagram" src="/figures/01/pcm.svg" alt="Sampling reads the waveform at regular instants, quantization rounds each sample to one of four levels, encoding writes each level as a 2-bit code." />

1. **Sampling** — read the signal every $T_s$. Discrete in time, still any amplitude.
2. **Quantization** — round each sample to the nearest of a finite set of levels. The rounding error is *quantization noise*.
3. **Encoding** — give each level a binary code word. $b$ bits per sample → up to $2^b$ levels.

<!--
Walk the figure left to right. In the middle panel the grey dot is the original sample and the green stem is the level it
was rounded to — the gap between them is the quantization error, and more bits per sample make it smaller. Step 3 is bookkeeping.
-->

---

# The sampling theorem

<div class="pt-4 text-2xl">

$$
f_s > 2\,f_{\max}
$$

</div>

For an ideally low-pass band-limited signal, exact reconstruction from **ideal, unquantized samples** is possible when the sampling frequency exceeds **twice the highest frequency present**.

<div v-click class="pt-4">

Components above $f_s/2$ fold into the sampled baseband: **aliasing**. Ordinary reconstruction cannot tell the overlapping components apart. Use an anti-alias low-pass filter *before* sampling.

</div>

<div v-click class="pt-4 vsb-muted">

The sampling theorem is commonly called Nyquist–Shannon. The same $2B$ appears in Part 3 for ideal real baseband signaling; quantization is a separate source of error.

</div>

<!--
The 2B remark is a hook for ideal real baseband PAM. Shannon published a reconstruction treatment in 1949;
Kotelnikov had published one in 1933. Keep historical priority details in Extras. Bandpass sampling requires
additional assumptions and is outside this introductory low-pass statement.
-->

---

# Checkpoint — a 5 kHz tone sampled at 8 kHz

<div class="checkpoint-question">

Telephone PCM samples at $f_s = 8$ kHz. A 5 kHz tone reaches the converter unfiltered. What comes out at the far end?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**A 3 kHz tone.**

$f_s/2 = 4$ kHz is the fold line. $5$ kHz sits $1$ kHz above it and lands $1$ kHz below: $|f_s - f| = 8 - 5 = 3$ kHz. The samples match a 3 kHz sine with the appropriate phase.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. Ask for a reason before revealing.
README question 4. The next slide shows the samples so nobody has to take the formula on faith.
-->

---

# Aliasing, seen

<img class="lecture-diagram" src="/figures/01/aliasing.svg" alt="A 5 kHz sine sampled every 125 microseconds; the samples lie exactly on a 3 kHz sine." />

<div class="pt-2">

The grey 5 kHz tone and the orange 3 kHz tone pass through **exactly the same samples**. After sampling, the information that told them apart is gone.

</div>

<!--
This is why the telephone band stops at 3 400 Hz and not at 4 000 Hz: the anti-aliasing filter needs a transition
band. This explains the upper-edge margin, not the lower speech-band cutoff. For a zero-phase 5 kHz sine,
the matching 3 kHz sine is phase reversed; the figure generator includes that minus sign.
-->

---

# Quantization: how many bits per sample?

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

**Uniform quantization** — $2^b$ equally spaced levels. At fixed input range, each extra bit gives about **6 dB** more signal-to-quantization-noise ratio (SQNR).

For an ideal ADC and a full-scale sine:

$$
\mathrm{SQNR}_{\mathrm{dB}} \approx 6.02b + 1.76
$$

- 8 bits → 256 levels → ≈ 50 dB
- 16 bits → 65 536 levels → ≈ 98 dB

</div>
<div>

**Companding** — G.711 uses A-law or μ-law: finer amplitude steps near zero, coarser steps for louder samples.

Amplitude compression before quantization and expansion after decoding improve weak-signal resolution.

It still produces **8 bits per sample**; it does not have the full-range accuracy of a higher-bit uniform quantizer.

</div>
</div>

<div class="pt-3 text-sm vsb-muted">

Ideal quantization model, no clipping. [SQNR assumptions: Analog Devices MT-001](https://www.analog.com/media/en/training-seminars/tutorials/mt-001.pdf) · [Companding: MIT PCM notes](https://ocw.mit.edu/courses/16-36-communication-systems-engineering-spring-2009/d91cdcc10683c573cc668c5b1ab3aab6_MIT16_36s09_lec04.pdf)

</div>

<!--
Use the 6 dB/bit rule as the takeaway, not a universal measured SNR. It assumes a fixed full-scale range,
suitable input, and the usual quantization-error model; low-amplitude inputs have lower SQNR. Quantization error
need not behave like independent random noise. A-law is common in Europe; mu-law in North America and Japan.
G.711 companding compresses amplitude range; distinguish it from additional statistical/predictive bit-rate
compression. Students meet G.711 A-law in Exercise 03.
-->

---

# Worked example — the G.711 telephone stream

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

The telephone speech signal is filtered to **300–3400 Hz**.

<div v-click>

Sampling theorem: $f_s > 2 \times 3400 = 6800$ Hz → the standard chose **8 000 Hz** (with margin for the filter).

</div>
<div v-click class="pt-2">

Quantization: **8 bits** per sample, companded.

</div>
<div v-click class="pt-2">

Bit rate: $8\,000 \times 8 = 64\,000$ **bit/s**.

</div>

</div>
<div v-click>

<div class="vsb-fill">

### 64 kbit/s

one sample every 125 µs · one byte each · fixed bit rate

</div>

<div class="pt-4 text-sm vsb-muted">

This stream is the payload of the RTP packets you will dissect in Exercise 03: 20 ms → 160 samples → 160 bytes per packet, 50 packets per second.

</div>

</div>
</div>

<!--
Return to the chain: microphone → anti-alias filter → sampler → quantizer → 64 kbit/s → packets → link → playout.
The 3.1 kHz voiceband describes the analog speech signal, not the digital transport link. E1 has 32 time slots
of 64 kbit/s, including framing/signaling allocations; it does not carry 32 ordinary voice calls.
G.711 quantization is lossy relative to the original analog waveform.
-->

---
layout: section
---

# Part 2
## Noise and the signal-to-noise ratio

---

# Model noise as a random signal added to the useful one

<img class="lecture-diagram" src="/figures/01/gaussian.svg" alt="Two zero-mean Gaussian densities: standard deviation 1 is wide and low, standard deviation 0.5 is narrow and tall." />

$$
p(x) = \frac{1}{\sigma\sqrt{2\pi}}\; e^{-\frac{(x-\mu)^2}{2\sigma^2}}
$$

Mean $\mu$ (zero in this course) and standard deviation $\sigma$ — the square root of the variance $\sigma^2$. **$\sigma$ is the strength of the noise.**

<!--
Thermal noise is the sum of an enormous number of tiny independent contributions, which is why the central limit
theorem makes it Gaussian. The notebook's sigma slider is this sigma.
-->

---

# AWGN — the standard channel model

<img class="lecture-diagram" src="/figures/01/signal-noise.svg" alt="A clean sine on the left; the same sine with Gaussian noise of variance 0.1 added on the right." />

<div class="grid grid-cols-3 gap-6 pt-2">
<div>

**Additive** — $y = x + n$; the noise does not multiply or distort the signal, it is summed onto it.

</div>
<div>

**White** — flat power spectral density over the modeled band.

</div>
<div>

**Gaussian** — noise amplitudes follow a joint Gaussian model. Our simulation uses independent normal draws.

</div>
</div>

<!--
White refers to a flat power spectral density, not the marginal amplitude distribution. Whiteness gives
uncorrelated samples in the discrete-time white model; joint Gaussianity then gives independence.
Band-limiting can correlate samples taken at arbitrary spacings. In Exercise 01 we explicitly generate
independent Gaussian samples. Assume noise independent of the transmitted signal. AWGN is a useful baseline,
not a claim that every real channel has white Gaussian noise.
-->

---

# Signal power

For $n$ real samples $x_1, \dots, x_n$, estimate **mean power** using

$$
P = \frac{1}{n} \sum_{i=1}^{n} x_i^2
$$

<div class="grid grid-cols-2 gap-8 pt-4">
<div>

Watts if $x_i$ are volts across $1\,\Omega$; otherwise a relative measure — and relative is all we need, because the next quantity is a ratio.

</div>
<div v-click>

Sine, averaged over a period: $P = A^2/2$.
Zero-mean noise, expected power: $P = \sigma^2$.

The previous figure has **theoretical** $S = 0.5$, $N = 0.1$. Finite-record estimates vary.

</div>
</div>

<div v-click class="pt-6 vsb-muted">

Exercise 01, Step 2 asks you to implement this before importing the reference `calc_signal_power`. Do it yourself first — it is three lines of NumPy.

</div>

<!--
The notebook says "implement first". Hold them to it: the reference implementation exists so they can check, not
so they can skip.
-->

---

# Signal-to-noise ratio, linear and in decibels

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

$$
\mathrm{SNR} = \frac{S}{N} \quad [-]
$$

$$
\mathrm{SNR}_{\mathrm{dB}} = 10 \log_{10}\frac{S}{N}
\qquad
\frac{S}{N} = 10^{\mathrm{SNR}_{\mathrm{dB}}/10}
$$

Decibels are a **power** ratio on a log scale: every 10 dB is a factor of 10, every ≈ 3 dB a factor of 2.

</div>
<div>

| dB | $S/N$ |
|---|---|
| 0 | 1 |
| 3 | ≈ 2 |
| 10 | 10 |
| 20 | 100 |
| 30 | 1 000 |
| 40 | 10 000 |

</div>
</div>

<div class="pt-4">

**Convert to the linear ratio before the capacity formula.** The formula wants $S/N$, not decibels.

</div>

<!--
README question 1. The classic mistake in the notebook is feeding 20 into log2(1 + 20) instead of log2(1 + 100).
-->

---

# Checkpoint — a datasheet says "SNR 20 dB"

<div class="checkpoint-question">

A link has an SNR of 20 dB. What number goes into $\log_2(1 + S/N)$, and by how much would the answer be wrong if you used 20 directly?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**100.** $10^{20/10} = 100$, so $\log_2(101) \approx 6.66$ bit/s/Hz.

With 20 you would get $\log_2(21) \approx 4.39$ — a third of the capacity thrown away by a unit error.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. Ask for a reason before revealing.
-->

---
layout: section
---

# Part 3
## Symbols and bits — the noiseless limit

---

# A symbol can carry more than one bit

<img class="lecture-diagram" src="/figures/01/symbols.svg" alt="A two-level waveform sends one bit per symbol; a four-level waveform at half the symbol rate sends the same ten bits." />

<div class="pt-1">

$M$ distinct signal states label $\log_2 M$ bits per symbol when $M$ is a power of two. Symbol rate is measured in **baud** \[Bd\]; raw bit rate is measured in bit/s. For binary signaling there is one raw bit per symbol.

</div>

<!--
The discussion prompt on the original draft: "symbol rate vs bit rate". Draw the distinction hard. A 1000 Bd link
with 16 levels is a 4000 bit/s link. "Baud rate" as a synonym for bit rate is wrong outside of binary modems.
-->

---

# Nyquist — ideal baseband PAM

$$
R_{\max} = 2B \log_2 L
$$

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

**Pulse-amplitude modulation (PAM):** a real low-pass channel of bandwidth $B$ \[Hz\], $L$ amplitude levels, no noise, and ideal pulse shaping with zero intersymbol interference.

The maximum symbol rate in this model is $2B$ baud. Each symbol labels $\log_2 L$ bits.

</div>
<div>

**Example:** $B = 3\,100$ Hz, $L = 16$:

$$
R_{\max} = 2 \times 3100 \times 4 = 24\,800\;\mathrm{bit/s}
$$

With no noise and unlimited amplitude resolution, $L$ and the ideal information rate are unbounded.

</div>
</div>

<div class="pt-4 vsb-muted text-sm">

This $2B$ rule counts real baseband PAM symbols. Quadrature amplitude modulation (QAM) uses two coordinates per point; its constellation size is not the number of PAM levels.

</div>

<div v-click class="pt-3">

**One carrier frequency is not bandwidth:** an ideal unmodulated tone at $f_c$ has $B=0$, even when $f_c$ is large. Sending successive symbols changes the waveform and requires nonzero bandwidth.

</div>

<!--
Nyquist's ideal zero-ISI result is the sampling-theorem connection. Do not call this a telephone modem example:
a voiceband QAM channel needs the passband convention. For ideal passband QAM, Rs is approximately B; raised-
cosine roll-off alpha gives B=(1+alpha)Rs. For real baseband PAM it gives B=(1+alpha)Rs/2.
The detailed distinction is in an Extras slide. Noiseless arbitrary-precision signaling has no finite capacity
under a bandwidth constraint alone; this is why specifying the channel model matters.
For finite L, the Nyquist expression gives zero symbol/bit rate at B=0. A pure carrier has fixed amplitude,
frequency, and phase: it provides no ongoing stream of new symbols. Choosing its initial parameters is not
the same as transmitting successive independent symbols at a positive rate. Changing amplitude or phase to
send data introduces additional frequency components. The ideal zero-bandwidth tone lasts indefinitely;
switching it on/off or limiting its duration also broadens its spectrum. Distinguish the carrier's passband
width from the low-pass bandwidth B used in this PAM formula: never substitute fc for B.
-->

---

# Johnson–Nyquist noise — why $N$ grows with $B$

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

Available thermal noise power into a matched load, in the classical regime:

$$
N = kTB
$$

- $k = 1.38 \times 10^{-23}$ J/K
- $T$ — temperature \[K\]
- $B$ — effective noise bandwidth \[Hz\]

At 290 K: **−174 dBm/Hz**.

</div>
<div>

| Bandwidth | Thermal noise floor |
|---|---|
| 3.1 kHz | −139 dBm |
| 20 MHz | −101 dBm |
| 2 GHz | −81 dBm |

<div v-click class="pt-3">

More bandwidth admits more noise: about **58 dB** between the first and last row.

At fixed **received signal power**, increasing bandwidth lowers SNR. Capacity then grows less than linearly.

</div>
</div>
</div>

<div class="text-sm vsb-muted pt-3">

Receiver noise and interference can raise the actual floor. [Nyquist, 1928](https://123.physics.ucdavis.edu/johnson_files/nyquist_1928.pdf)

</div>

<!--
Explain dBm as absolute power relative to 1 mW; dBm/Hz is power spectral density. Do not confuse it with SNR in dB.
Johnson measured thermal noise and Nyquist derived it. The ideal matched-load/classical model is enough here.
The fixed-received-power wideband limit is in Extras. Retain the essential point that changing B may change N.
-->

---

# Checkpoint — why not a million levels?

<div class="checkpoint-question">

Nyquist says more levels means more bits per symbol at the same bandwidth. What stops us from using $L = 10^6$ and getting 20 bits per symbol?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Noise.** In a fixed amplitude range, adding levels shrinks their spacing. When that spacing is comparable to $\sigma$, decisions between neighboring levels become error-prone.

Closer signal points are harder to distinguish in noise. **Shannon accounts for coding across many symbols** to find the ultimate reliable information rate; there is no universal level-count formula based on SNR alone.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion.
Keep the spacing/noise intuition, but do not derive Shannon by assigning an effective number of levels.
Constellation geometry, coding, and target error probability determine the performance of a particular scheme.
-->

---
layout: section
---

# Part 4
## The Shannon–Hartley theorem

---

# Capacity of a noisy channel

<div class="pt-2 text-3xl">

$$
C = B \log_2\!\left(1 + \frac{S}{N}\right)
$$

</div>

<div class="grid grid-cols-3 gap-6 pt-4">
<div>

$C$ — channel capacity \[bit/s\]

</div>
<div>

$B$ — bandwidth \[Hz\]

</div>
<div>

$S/N$ — **linear** signal-to-noise ratio \[–\]

</div>
</div>

<div v-click class="pt-6">

With bandwidth $B$, fixed average **received** signal power $S$, and independent AWGN of power $N$ over that band: any information rate below $C$ can achieve **arbitrarily small error probability** with sufficiently long codes.

</div>

<div v-click class="pt-4 vsb-muted">

Above $C$, arbitrarily reliable communication is impossible under this model. Approaching $C$ generally costs coding complexity and delay — a practical concern for voice.

</div>

<!--
Shannon 1948, "A Mathematical Theory of Communication", and 1949, "Communication in the Presence of Noise".
Hartley's logarithmic information measure is introduced in Part 5. Decades of coding theory have developed
practical codes, including Hamming, convolutional, turbo, LDPC, and polar codes. This theorem does not promise
zero error or a finite-delay code exactly at C. Finite modulation alphabets can impose a lower achievable rate.
-->

---

# Knob 1 — bandwidth is linear

<img class="lecture-diagram" src="/figures/01/capacity-bandwidth.svg" alt="Capacity versus bandwidth for SNR of 15, 100 and 1000: three straight lines through the origin." />

At fixed $S/N$, **doubling $B$ doubles $C$**. Wider channels are one way to increase rate; the condition **fixed SNR** matters.

<div class="vsb-muted text-sm">

The catch: thermal noise is $N = kTB$ (Johnson–Nyquist), so if the signal power stays fixed, a wider channel also lowers $S/N$. "Fixed SNR" must be checked, not assumed.

</div>

<!--
The catch is the README's "if bandwidth changes, the noise power may also change". In the limit B → ∞ with fixed
S, C → 1.44 S/N_0 — finite. Mention it only if the room is ahead of schedule.
-->

---

# Knob 2 — SNR is logarithmic

<img class="lecture-diagram" src="/figures/01/capacity-snr.svg" alt="Spectral efficiency versus SNR in dB: nearly flat below 0 dB, then one extra bit per hertz for every 3 dB." />

At high SNR, doubling $S/N$ adds approximately **1 bit/s/Hz**; multiplying it by ten adds approximately **3.3 bit/s/Hz**. With unchanged propagation and noise, more transmit power has diminishing returns.

<!--
There is no cutoff at 30 dB: moving from 30 to 40 dB still adds about 3.32 bit/s/Hz. At 0 dB, C/B is 1,
not zero. Compare with the exit questions. Low SNR alone does not determine the best modulation or spreading
strategy; bandwidth, power, interference, and implementation constraints all matter.
-->

---

# Worked example

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

A channel with $B = 3\,000$ Hz and $S/N = 15$.

<div v-click class="pt-3">

$$
C = 3000 \cdot \log_2(1 + 15) = 3000 \cdot \log_2 16
$$

</div>
<div v-click class="pt-2">

$$
C = 3000 \cdot 4 = 12\,000 \ \mathrm{bit/s}
$$

</div>

</div>
<div v-click>

<div class="vsb-fill">

### 12 kbit/s

for 3 kHz of bandwidth at 11.8 dB

</div>

<div class="pt-4 text-sm">

Units check: $B$ is bandwidth \[Hz\]; $C$ is an information rate \[bit/s\]. Their ratio $C/B = \log_2(1+S/N)$ is **spectral efficiency**, measured in bit/s/Hz.

</div>

</div>
</div>

<!--
Do this on the board too, slowly. S/N = 15 was chosen because 16 is a power of two; make them notice that and ask
what S/N would give exactly 5 bit/s/Hz (31).
-->

---

# Checkpoint — 64 kbit/s through a 33 kbit/s channel?

<div class="checkpoint-question">

For an analog voiceband channel, $B=3.1$ kHz and $S/N=1585$ give $C\approx33$ kbit/s. G.711 produces 64 kbit/s. Is the capacity bound being violated?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**No — these rates describe different channels.**

The 3.1 kHz band describes the analog voiceband circuit. The 64 kbit/s PCM representation travels over a **digital transport link** with its own bandwidth, noise, and capacity.

The 33 kbit/s value is a result for the stated assumptions, not a universal limit for every telephone connection.

</div>

<!--
Exercise 01 README question 3. Give 30 seconds of individual thought and 30 seconds of pair discussion.
Draw analog speech → PCM → digital network → reconstructed speech. V.34 reached 33.6 kbit/s under suitable
conditions, not exactly at the bound for these numbers (32.9566 kbit/s). V.90 used digital-network access for
up to 56 kbit/s downstream and 33.6 upstream; V.92 allowed up to 48 upstream. Neither violated Shannon.
References and the historical comparison are on the Extras technology slide.
-->

---

# Capacity, coded bits, and useful data

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

### Physical-channel quantities

**Capacity $C$:** the reliable information-rate limit for the specified channel model.

**Raw coded bit rate:** includes error-correction redundancy. It can exceed $C$.

**Net information rate:** $R_{\mathrm{info}}=rR_{\mathrm{raw}}$, where $r$ is information bits / coded bits. Reliable operation must respect $C$.

</div>
<div>

### Measured network quantities

**Throughput:** successful transfer rate at a stated layer, such as IP. Contention, loss, and retransmissions affect it.

**Goodput:** useful application payload delivered per second, excluding protocol overhead and duplicates.

Codec output is usually application payload.

</div>
</div>

<div class="pt-5">

QoS manages **rate, delay, jitter, loss, and fairness** within the available resources.

</div>

<!--
Define the measurement layer before comparing numbers. Coding redundancy is different from packet headers.
A rate-1/2 code doubles the raw coded bit count; capacity constrains information, not that redundant count.
Lecture 3–4 examine network measurements; 5–6 connect them to perceived service quality.
-->

---

# From 64 kbit/s of speech to 80 kbit/s of IP traffic

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

**G.711, 20 ms packetization**

- 160 bytes of speech per packet
- RTP 12 B + UDP 8 B + IPv4 20 B
- 50 packets/s, in each direction

$$
R_{\mathrm{IP}}=(160+40)\times8\times50
$$

**80 kbit/s at IP; 64 kbit/s of payload.**

</div>
<div>

### What if packets cover 40 ms?

<div v-click>

320 bytes of speech, 25 packets/s:

$$
R_{\mathrm{IP}}=(320+40)\times8\times25
$$

**72 kbit/s at IP; still 64 kbit/s of payload.**

Less overhead per second, but more packetization delay and more speech affected by each lost packet.

</div>
</div>
</div>

<div class="pt-3 text-sm vsb-muted">

No IPv4 options, no RTP extensions, no link-layer overhead; continuous speech transmission. Same calculation as Exercise 03.

</div>

<!--
Trace microphone → PCM → packets → link → playout again. Ask the room to calculate the 40 ms case before the
reveal. This is a concrete QoS tradeoff, not a universal percentage reduction between protocol layers.
Rates are per direction. Successful reception is assumed when comparing these offered rates with goodput.
-->

---

# MIMO — antennas can separate spatial streams

<div class="grid grid-cols-2 gap-8 pt-3">
<div>

**Multiple-input multiple-output (MIMO)** uses several transmit and receive antennas.

Different spatial paths can let the receiver separate several streams **in the same frequency band**.

With $n_t$ transmit and $n_r$ receive antennas, there are at most $\min(n_t,n_r)$ spatial streams.

</div>
<div>

### Antennas do not guarantee streams

The channel must distinguish the transmitted signals well enough. Similar paths may provide only one useful mode.

Available power must be allocated across streams; each has its own SNR.

More antennas can also improve reliability or received signal strength.

</div>
</div>

<div class="pt-5 vsb-muted text-sm">

Exercise 01, README question 2 · [Tse and Viswanath, chapters 7–8](https://web.stanford.edu/~dntse/wireless_book.html) · Formula and assumptions in Extras

</div>

<!--
Use the analogy of solving simultaneous equations: the received mixtures must differ enough to recover the
unknown streams. In a compact, co-polarized far-field array with a single propagation path, the channel can be
approximately rank one. Line of sight alone does not forbid multiple streams: geometry and polarization matter.
Keep the matrix mathematics and per-mode capacity formula in Extras, but answer the lab's conceptual question here.
-->

---
layout: section
---

# Part 5
## Measuring information — Hartley and Shannon

---

# How much information is in one letter?

<img class="lecture-diagram" src="/figures/01/guessing-tree.svg" alt="Yes-or-no questions halve 26 candidates to 13, 7, 4, 2, 1; four or five questions suffice." />

Someone picks one of **26 equally likely letters**. You may ask yes/no questions. How many do you need in the worst case?

<!--
A guessing-game illustration of Hartley's measure. Specify that letters are equally likely. Ask for the worst
case: five questions suffice. Some paths need four. Distinguish those integer counts from log2(26) bits of
information, and explain block coding on the next slide.
-->

---

# Hartley's measure — 1928

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

**26 equally likely letters:**

$$
I_{\mathrm{Hartley}}=\log_2 26\approx4.700\;\text{bits}
$$

Five yes/no questions suffice in the worst case.

An optimal separate-letter question tree averages **4.769 questions**, not 4.700.

</div>
<div>

**Blocks of $n$ independent uniform letters:**

There are $26^n$ possible messages. A fixed-length binary block code needs

$$
\left\lceil n\log_2 26\right\rceil\;\text{bits}.
$$

As blocks grow, bits per letter approach **4.700**.

</div>
</div>

<div v-click class="pt-4 vsb-muted">

For all $s^n$ possible messages: $I_{\mathrm{Hartley}}=n\log_2s$. Base 2 gives bits; base $e$ gives nats; base 10 gives hartleys.

</div>

<!--
The optimal uniform 26-letter binary tree has six leaves at depth 4 and twenty at depth 5:
(6×4+20×5)/26=4.76923. Repeating separate-letter coding does not remove the gap. Long-block coding does.
For n=5, log2(26^5)=23.502 bits, so a fixed-length block code needs 24 bits, or 4.8 bits per letter.
The logarithm makes information additive when the number of possible independent choices multiplies.
-->

---

# Unequal probabilities change the questions

<div class="grid grid-cols-2 gap-8 pt-3">
<div>

### Equal probabilities

Divide the **number of candidates** roughly in half.

For 26 uniform letters, a split of 13 versus 13 is balanced.

</div>
<div>

### Unequal probabilities

Divide the **remaining probability mass** roughly in half.

Common outcomes can receive shorter descriptions. Guessing the most frequent letter first is not generally the best yes/no question.

</div>
</div>

<div v-click class="pt-6">

Shannon's measure accounts for how likely each outcome is. We will calculate it for a four-outcome source and build a code.

</div>

<!--
Contrast set size with probability mass. For an English model with P(E)=0.127, asking “Is it E?” splits
probability 0.127/0.873, not nearly 0.5/0.5. An optimal whole decision tree minimizes expected depth; approximate
probability-halving is intuition, not a claim that a greedy split always produces the optimal code.
Do not confuse free yes/no subset questions with guessing successive individual letters in Shannon's experiment.
-->

---

# Self-information of one outcome

<div class="pt-2 text-2xl">

$$
I(x_i) = \log_2 \frac{1}{p_i} = -\log_2 p_i \quad [\text{bit}]
$$

</div>

<div class="grid grid-cols-2 gap-8 pt-4">
<div>

- $p = 1$ → $0$ bits. A certain outcome tells you nothing.
- $p = 1/2$ → $1$ bit. A fair coin.
- $p = 1/26$ → $4.7$ bits. Hartley's uniform letter.

</div>
<div>

- If $p = 1/4$ → $2$ bits
- If $p = 1/8$ → $3$ bits

**The rarer the outcome, the more it tells you.** Information is surprise, measured in bits.

</div>
</div>

<div v-click class="pt-6 vsb-muted">

Information measures **uncertainty under a probability model**. It does not measure a message's importance, usefulness, or truth.

</div>

<!--
The statistical-mechanics analogy is optional: for W equally likely microstates, Boltzmann entropy k ln W
is proportional to a logarithmic count. Do not identify communication entropy with physical units or semantic
value. Avoid the disputed von Neumann naming anecdote. Use powers of two here to prepare the coding example.
-->

---

# Shannon entropy — the average information per symbol

<div class="pt-2 text-2xl">

$$
H = \sum_i p_i \log_2 \frac{1}{p_i} = -\sum_i p_i \log_2 p_i \quad [\text{bit/symbol}]
$$

</div>

<div class="grid grid-cols-2 gap-8 pt-4">
<div>

**One symbol repeated** — $p = 1$ for it, $0$ for all others:
$H = 0$. With the source and framing known, each next symbol is certain.

</div>
<div>

**All $N$ symbols equally likely** — $p_i = 1/N$:
$H = \log_2 N$. Hartley's value, and the **maximum** possible for $N$ symbols.

</div>
</div>

<div v-click class="pt-6">

$$
0 \;\le\; H \;\le\; \log_2 N
$$

For a fixed alphabet of $N$ symbols, the maximum occurs only at the uniform distribution. Use $0\log_2 0 := 0$.

</div>

<!--
H(X) has units of bits for one random variable; bits per source symbol is its operational interpretation here.
For a fixed finite alphabet, uniform probabilities maximize entropy. Probabilities must still sum to one.
The convention 0 log2(0)=0 follows by a limit. H describes this source model, not an individual file size.
-->

---

# A source and a code we can calculate

| Outcome | Probability | Information $-\log_2p$ | Code | Length |
|---|---|---|---|---|
| A | $1/2$ | 1 bit | `0` | 1 |
| B | $1/4$ | 2 bits | `10` | 2 |
| C | $1/8$ | 3 bits | `110` | 3 |
| D | $1/8$ | 3 bits | `111` | 3 |

<div v-click>

$$
H=\tfrac12\cdot1+\tfrac14\cdot2+\tfrac18\cdot3+\tfrac18\cdot3=1.75\;\text{bit/symbol}
$$

Average code length is also **1.75 bits/symbol**, versus 2 for a fixed-length code.

</div>

<div class="pt-2">

**Decode:** `010110111` <span v-click>→ A · B · C · D</span>

</div>

<!--
Give students a minute to calculate H and average length before revealing. A prefix code has no codeword that
is the beginning of another, so the stream can be decoded without separators. The dyadic probabilities make
exact equality possible here; general sources need long blocks to approach H. Assume independent symbols and
a shared codebook. This example illustrates source coding without requiring the Huffman construction algorithm.
-->

---

# The binary source

<img class="lecture-diagram" src="/figures/01/binary-entropy.svg" alt="Entropy of a binary source versus the probability of a one: zero at both ends, one bit at one half." />

$$
H(p) = -p \log_2 p - (1-p)\log_2(1-p)
$$

Independent biased tosses with $p = 0.1$ have $H \approx 0.469$ bit per toss. With a known model and suitable block coding, 1 000 tosses need **about 469–470 bits on average**, not for every possible sequence.

<!--
This curve is worth memorising. It is concave, symmetric, and 1 bit at the top. Every "a bit is a bit" intuition
fails on it: an independent binary source carries one bit per symbol only when both values are equally likely.
The average block-code length can approach nH; individual blocks can be much longer. Codebook/framing overhead
is excluded from the illustrative number. Source dependencies need the next slide's additional qualification.
-->

---

# Same symbol counts, different predictability

<div class="grid grid-cols-2 gap-8 pt-4">
<div>

### Independent fair bits

`011010001101…`

Each new bit is equally likely to be 0 or 1, even after seeing the past.

**Entropy rate: 1 bit per symbol.**

</div>
<div>

### A known alternating rule

`010101010101…`

The counts are also half 0, half 1. Once the starting bit is known, every next bit is determined.

**Entropy rate: 0 bits per symbol.**

</div>
</div>

<div v-click class="pt-6">

Single-symbol frequencies miss dependencies. For a source with memory, compression is limited by its **entropy rate**: the uncertainty per symbol that remains after accounting for the past.

</div>

<!--
For the alternating source, choose the starting bit at random and assume the rule and message length are known.
Each marginal symbol is fair, but an n-symbol block has only one bit of uncertainty: H(X1,...,Xn)/n=1/n → 0.
A known starting phase makes even that initial uncertainty zero. Students need the intuition, not a proof.
Observed counts in one finite realization are not themselves a complete source model.
-->

---

# Three different jobs called encoding

| Stage | What it does | Example |
|---|---|---|
| **PCM encoding** | Labels quantized samples with bit patterns | G.711: 8 bits per sample |
| **Lossless source coding** | Removes statistical redundancy | Shorter codes for common outcomes |
| **Channel coding** | Adds controlled redundancy for error protection | Extra coded bits to recover damaged data |

<div v-click class="pt-5">

**Lossy source coding** can use fewer bits by accepting distortion. G.711 quantization and speech codecs such as Opus do not preserve the original analog waveform exactly.

</div>

<!--
Resolve the apparent contradiction: source coding removes redundancy; channel coding adds redundancy for a
different purpose. PCM's binary labeling alone adds no error protection. Once a quantized stream is given,
a lossless compressor can preserve those digital samples exactly, but it cannot undo earlier quantization.
The distortion/rate/quality tradeoff returns in the multimedia lectures.
-->

---

# The two theorems, and where QoS lives

<div class="grid grid-cols-2 gap-8 pt-2">

<div class="border border-green-400 p-4">

### Source coding

For independent symbols, lossless coding can **approach $H$ bits per symbol on average** with long blocks, but cannot beat that average limit. For dependent sources, use the entropy rate.

**How many bits does the message need?**

</div>

<div class="border border-green-400 p-4">

### Channel coding

Under the stated AWGN constraints, any information rate below $C$ can achieve arbitrarily small error with sufficiently long codes. No rate above $C$ can do so.

**How many bits can the channel carry?**

</div>

</div>

<div class="pt-6">

A codec produces a stream; packets and protection add overhead; a link serves the traffic. **Queues, scheduling, admission, and congestion control** help meet rate, delay, jitter, and loss requirements.

</div>

<!--
Close the loop to the thesis: these are asymptotic average limits under specified models, not finite-packet
guarantees. Lossy codec rates also depend on accepted distortion. G.711 is 64 kbit/s; RFC 6716 specifies an Opus
operating range of 6–510 kbit/s, not a lossless speech bound. Lecture 2 studies queues; lectures 5–6 study
quality and codecs. Longer codes and blocks can add delay, which matters for voice.
-->

---

# Summary — five formulas to keep

<div class="grid grid-cols-2 gap-x-10 gap-y-2 pt-2">

<div>

**Sampling** — ideal low-pass, unquantized samples
$$ f_s > 2 f_{\max} $$

**Signal-to-noise ratio** — convert to linear first
$$ S/N = 10^{\mathrm{SNR}_{\mathrm{dB}}/10} $$

**Nyquist** — ideal real baseband PAM, $L$ levels
$$ R_{\max} = 2B \log_2 L $$

</div>
<div>

**Shannon–Hartley** — AWGN, specified power and band
$$ C = B \log_2(1 + S/N) $$

**Entropy** — average surprise for one source symbol
$$ H = -\sum_i p_i \log_2 p_i $$

</div>

</div>

<div class="pt-2 vsb-muted">

Capacity is linear in bandwidth **at fixed SNR**. A binary symbol has 1 bit of entropy only when its two outcomes are equally likely; dependencies require entropy rate.

</div>

<!--
Read them aloud, one sentence each. Then the exercise preview.
-->

---

# Exit questions — use the ideas

1. Does 0 dB SNR mean zero channel capacity?
2. Does doubling bandwidth double capacity at fixed received signal power?
3. Can a binary source have less than one bit of entropy per symbol?
4. Why does a 64 kbit/s G.711 payload produce 80 kbit/s of IPv4 traffic?

<div v-click class="pt-5 vsb-muted">

**Explain the assumptions and units**, not just the formula.

</div>

<!--
Allow two minutes for individual answers and then discuss. Answers: (1) No: S/N=1, so C=B bit/s in AWGN.
(2) Not generally: with fixed thermal-noise density N grows with B, so SNR falls. (3) Yes: biased independent
bits have H<1; dependencies can reduce entropy rate further. (4) 40 bytes of RTP/UDP/IPv4 headers per 160-byte
payload, 50 packets/s; exclude link overhead. These questions check the learning outcomes and lead to the lab.
-->

---

# Exercise 01 — what you will do

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

1. **Model a signal with noise** — a harmonic signal, Gaussian noise with a $\sigma$ slider, watch the SNR move.
2. **Implement the channel metrics** — signal power, SNR, Shannon capacity — *before* importing the reference versions from `lib.core`.
3. **Noise on audio** — add AWGN to a WAV file and listen to what 20 dB, 10 dB and 0 dB sound like.
4. **Noise on an image** — the same, seen.

</div>
<div>

Then the README questions:

- SNR units and the linear ratio
- MIMO and why antennas ≠ streams
- 64 kbit/s vs the 33 kbit/s telephone channel
- the 5 kHz tone at $f_s = 8$ kHz

<div class="pt-4 text-sm vsb-muted">

```bash
ssh <lab-server>
cd qos-01 && uv sync
uv run jupyter lab --ip 0.0.0.0
```

</div>
</div>
</div>

<!--
All four README questions were answered somewhere in this deck. Don't tell them where.
-->

---

# References — foundations

- C. E. Shannon, [“A Mathematical Theory of Communication,” 1948](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf).
- C. E. Shannon, “Communication in the Presence of Noise,” *Proc. IRE*, 37(1), 10–21, 1949.
- C. E. Shannon, [“Prediction and Entropy of Printed English,” 1951](https://fizyka.umk.pl/~milosz/KKK/shannon-1951.pdf).
- R. V. L. Hartley, “Transmission of Information,” *Bell System Technical Journal*, 7, 535–563, 1928.
- H. Nyquist, “Certain Topics in Telegraph Transmission Theory,” *Trans. AIEE*, 47, 617–644, 1928.
- H. Nyquist, [“Thermal Agitation of Electric Charge in Conductors,” 1928](https://123.physics.ucdavis.edu/johnson_files/nyquist_1928.pdf).

<!--
Primary sources for the information measures, channel limits, sampling, English experiment, and thermal noise.
These are further reading, not prerequisites for Exercise 01. Extras slides follow the closing slide.
-->

---

# References — explanations and applications

- [MIT: PCM, sampling, and companding](https://ocw.mit.edu/courses/16-36-communication-systems-engineering-spring-2009/d91cdcc10683c573cc668c5b1ab3aab6_MIT16_36s09_lec04.pdf); [Huffman coding](https://ocw.mit.edu/courses/18-200-principles-of-discrete-applied-mathematics-spring-2024/mit18_200_s24_lec19.pdf); [source-coding theory](https://ocw.mit.edu/courses/6-441-information-theory-spring-2016/5d8f16adc3385c9ff2975b121bd620e4_MIT6_441S16_course_notes.pdf).
- Analog Devices, [MT-001: quantization SNR and its assumptions](https://www.analog.com/media/en/training-seminars/tutorials/mt-001.pdf).
- D. Tse and P. Viswanath, [*Fundamentals of Wireless Communication*, chapters 7–8](https://web.stanford.edu/~dntse/wireless_book.html).
- ITU-T [G.711](https://www.itu.int/rec/T-REC-G.711-198811-I/en), [V.90](https://www.itu.int/rec/T-REC-V.90), and [V.92](https://www.itu.int/rec/T-REC-V.92); [RFC 6716: Opus](https://www.rfc-editor.org/rfc/rfc6716.html).
- [ETSI TS 138 104 v19.2.0](https://www.etsi.org/deliver/etsi_ts/138100_138199/138104/19.02.00_60/ts_138104v190200p.pdf), NR channel bandwidths.

<!--
The G.711/IP arithmetic is also worked through in qos-03/README.md. Technology inputs in Extras are illustrative,
with standards cited for actual bandwidth options. No generic Wi-Fi or compressor performance is assumed.
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
## Optional history, comparisons, and mathematical detail

<!--
Not part of the timed 90-minute route. Use to answer questions or extend an advanced class.
-->

---

# Extras — the course in thirteen lectures

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div>

1. **Channel capacity, information theory, entropy** ← today
2. Kendall's classification of queueing systems; basic models
3. QoS vs QoE; approaches to achieving QoS
4. Models of network traffic; qualitative parameters in IP networks
5. Evaluating the quality of multimedia services I
6. Evaluating the quality of multimedia services II
7. Quality of Internet access services (ČTÚ, invited lecture)

</div>
<div>

8. Network modelling in software tools
9. The SDN concept and its use
10. Quality of service in SDN networks I
11. Quality of service in SDN networks II
12. Quality of service in SDN networks III
13. QoS in quantum communication infrastructure

</div>
</div>

<div class="pt-6 vsb-muted text-sm">

Lab exercises (`qos-01` … `qos-05`) run on the laboratory servers over SSH. Each lecture has a matching README with the theory and a notebook with the tasks.

</div>

<!--
Lecture 1 establishes the physical-channel baseline. Later lectures consider delay, jitter, loss, fairness,
and service requirements when traffic shares finite resources.
-->

---

# Extras — signal classification

| Criterion | Classes | Example |
|---|---|---|
| **Amplitude** | *analog* — any value in a continuous range<br>*digital* — a finite set of values, usually binary codes | microphone output<br>computer data |
| **Time** | *continuous-time* — defined at every instant<br>*discrete-time* — defined only at sampling instants | voltage on a wire<br>samples in a WAV file |
| **Repetition** | *periodic* — repeats with period $T$<br>*aperiodic* — has no repeating period | sine wave<br>a single pulse |
| **Predictability** | *deterministic* — given exactly by a function<br>*random* — described only statistically | $\sin(2\pi f t)$<br>thermal noise |

<div class="pt-4 vsb-muted">

The axes are independent: a WAV file is digital *and* discrete-time; noise is analog, continuous-time *and* random.

</div>

<!--
Ask them to classify three things: the voice on a phone line, a G.711 stream, the noise floor of a Wi-Fi receiver.
The point of "independent" is that "digital" says nothing about time, and "sampled" says nothing about amplitude.
-->

---

# Extras — why we go digital

<div class="grid grid-cols-3 gap-6 pt-4">

<div class="border border-green-400 p-4">

### Regeneration

Analog repeaters also amplify noise. A digital regenerator decides a symbol and sends a clean waveform — correctly if the decision was correct.

</div>

<div class="border border-green-400 p-4">

### Processing

Once it is numbers, it can be compressed, encrypted, mixed, stored and routed by a computer.

</div>

<div class="border border-green-400 p-4">

### Multiplexing

Bits from many sources interleave on one link. Packets are this idea taken to its conclusion.

</div>

</div>

<div class="pt-8">

For an analog source, conversion adds two concerns: **aliasing** and **quantization error**. Part 1 is how to keep both under control.

</div>

<!--
The three benefits are why the whole course is about IP networks and not analog telephony. The two errors are what
the sampling theorem and the bit-depth choice are for.
-->

---
class: compact-table
---

# Extras — modulation states and bit rates

$$
R_{\mathrm{raw}} = R_s \log_2 M
$$

$R_{\mathrm{raw}}$ — raw coded bit rate \[bit/s\] · $R_s$ — symbol rate \[Bd\] · $M$ — signal states

<div v-click class="pt-3">

| Scheme | Distinct states $M$ | Bits per symbol | At 1 000 Bd |
|---|---|---|---|
| Binary PAM | 2 amplitudes | 1 | 1 000 bit/s |
| PAM-4 | 4 amplitudes | 2 | 2 000 bit/s |
| QPSK | 4 phases | 2 | 2 000 bit/s |
| 16-QAM | 16 constellation points | 4 | 4 000 bit/s |

</div>

<div v-click class="pt-4">

With channel-code rate $r$, the information bit rate is $R_{\mathrm{info}} = r R_{\mathrm{raw}}$ before framing and protocol overhead.

</div>

<!--
Reserve S and N for signal and noise power throughout. Rs is symbol rate; M counts distinct states, not always
amplitude levels. QAM has two coordinates, in-phase and quadrature. The simple bit labeling assumes M is a
power of two. If a rate-1/2 code sends two coded bits per information bit, raw bit rate is twice information rate.
This distinction matters again when comparing rates with Shannon capacity.
-->

---
class: compact-table
---

# Extras — Nyquist's contributions

| Year | Paper | Contribution |
|---|---|---|
| 1924 | *Certain Factors Affecting Telegraph Speed* | Telegraph speed, bandwidth, and signal levels |
| 1928 | *Certain Topics in Telegraph Transmission Theory* | Ideal pulse transmission and the $2B$ rate |
| 1928 | *Thermal Agitation of Electric Charge in Conductors* | Thermal-noise theory |
| 1932 | *Regeneration Theory* | Feedback stability criterion |

Born in Sweden in 1889; PhD at Yale in 1917. Worked in the Bell System until 1954 and received 138 US patents.

<div class="pt-4 text-sm vsb-muted">

[Contemporary biography: Bell Laboratories Record, November 1960](https://www.worldradiohistory.com/Archive-Bell-Laboratories-Record/60s/Bell-Laboratories-Record-1960-11.pdf) · [Shannon's 1948 introduction cites Nyquist and Hartley](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf)

</div>

<!--
Optional history; the stability criterion is named for context, not taught in this lecture. The sampling
theorem has several contributors: Kotelnikov published a reconstruction result in 1933; Shannon in 1949.
Do not attribute all of information theory's logarithmic or sampling ideas exclusively to one person.
-->

---

# Extras — bandwidth conventions

<div class="grid grid-cols-2 gap-8 pt-3">
<div>

### Real baseband PAM

$L$ amplitude levels, symbol rate $R_s$, roll-off $\alpha$:

$$
B=\frac{(1+\alpha)R_s}{2}
$$

At $\alpha=0$: $R_{\max}=2B\log_2L$.

</div>
<div>

### Passband QAM

$M$ two-dimensional constellation points:

$$
B=(1+\alpha)R_s
$$

At $\alpha=0$: $R_{\mathrm{raw}}=B\log_2M$.

</div>
</div>

<div class="pt-5 vsb-muted">

$B$ is occupied bandwidth \[Hz\]; $R_s$ is symbols/s. Both formulas assume ideal raised-cosine pulse shaping. Noise and coding determine the reliable information rate.

</div>

<!--
A QAM point has I and Q coordinates. The different factors of two reflect real low-pass versus complex
baseband/passband conventions, not contradictory physical limits. Ideal zero roll-off pulses have infinite
time support. More practical pulse shaping trades extra occupied bandwidth for implementation convenience.
This is a note about conventional zero-ISI symbol transmission, not a universal limit on arbitrary signaling.
-->

---

# Extras — a carrier frequency is not bandwidth

$$
x(t)=A\cos(2\pi f_c t+\phi)
$$

$A$ — amplitude; $f_c$ — carrier frequency \[Hz\]; $\phi$ — phase \[rad\].

<div class="grid grid-cols-2 gap-8 pt-3">
<div>

### A pure tone

With $A$, $f_c$, and $\phi$ fixed forever, the ideal tone occupies **one frequency: $B=0$**.

A 1 GHz carrier has a billion cycles per second, but those predictable cycles are not a billion independent symbols.

</div>
<div>

### Sending new choices

Successive symbols must change the waveform. Amplitude changes introduce **sidebands** around the carrier.

A 1 MHz-wide band centered at 1 GHz still has only **1 MHz of bandwidth**.

</div>
</div>

<!--
Extension of the B=0 note on the main Nyquist PAM slide. For a real tone the two-sided Fourier spectrum has
lines at positive and negative fc; “one frequency” here uses the usual positive-frequency RF convention.
Choosing initial tone parameters can convey a choice, but it is not an ongoing stream of independent symbols.
An exactly zero-bandwidth tone lasts indefinitely. Switching it on/off or limiting its duration broadens the
spectrum. Nyquist's real low-pass B and a carrier's center frequency fc must not be confused.
-->

---

# Extras — where AM sidebands come from

Vary a carrier's amplitude with a message tone of frequency $f_m$:

$$
x(t)=A_c[1+\mu\cos(2\pi f_m t)]\cos(2\pi f_c t)
$$

$A_c$ — carrier amplitude; $\mu$ — modulation depth; $f_c>f_m>0$ — frequencies \[Hz\].

Use $\cos a\cos b=\tfrac12\cos(a+b)+\tfrac12\cos(a-b)$:

<div v-click>

$$
\begin{aligned}
x(t)={}&A_c\cos(2\pi f_c t)\\
&+\frac{\mu A_c}{2}\cos\!\bigl(2\pi(f_c+f_m)t\bigr)\\
&+\frac{\mu A_c}{2}\cos\!\bigl(2\pi(f_c-f_m)t\bigr).
\end{aligned}
$$

**Carrier:** $f_c$ · **Upper sideband:** $f_c+f_m$ · **Lower sideband:** $f_c-f_m$

</div>

<div class="pt-2 text-sm vsb-muted">

[MIT modulation notes](https://ocw.mit.edu/courses/mas-160-signals-systems-and-information-for-media-technology-fall-2007/7df297c0c228664dad6391e7c325cbbf_1210_modulation.pdf)

</div>

<!--
This is conventional double-sideband amplitude modulation with a transmitted carrier and a single sinusoidal
message. The modulation depth mu is dimensionless: mu=0.5 means 50 percent. With 0≤mu≤1 the envelope does not
change sign. Expand the product and apply the identity on the board. Each sideband sinusoid has peak amplitude
mu Ac/2. These formulas are specific to AM; FM/PM generally have additional sidebands. Removing the DC offset
in the amplitude envelope suppresses the explicit carrier term, but the shifted message spectrum remains.
-->

---

# Extras — calculate the sideband frequencies

Carrier $f_c=1$ MHz; message $f_m=2$ kHz; $A_c=1$ V; modulation depth $\mu=0.5$.

| Component | Frequency | Peak amplitude |
|---|---|---|
| Lower sideband | $f_c-f_m=998$ kHz | $\mu A_c/2=0.25$ V |
| Carrier | $f_c=1\,000$ kHz | $A_c=1$ V |
| Upper sideband | $f_c+f_m=1\,002$ kHz | $\mu A_c/2=0.25$ V |

<div v-click class="pt-4">

The span from the lower to the upper sideband is **4 kHz**, even though the carrier is at 1 MHz.

For a real message occupying baseband frequencies up to $W$, double-sideband AM occupies $f_c-W$ to $f_c+W$: **passband width $2W$**, assuming $f_c>W$.

</div>

<!--
Ask students to predict the frequencies before calculating amplitudes. Convert MHz and kHz consistently.
The spectral span of this three-line spectrum is 2fm; a general band-limited message produces two bands.
Peak amplitudes are not powers: across the same resistance, sinusoidal power is proportional to amplitude
squared. The carrier can consume power without carrying the changing message. This example is double-sideband
AM; single-sideband transmission can remove one redundant sideband and needs a different receiver scheme.
-->

---

# Extras — sidebands of a digital PAM stream

A symbol stream has many frequency components. **Symbol rate and pulse shape** determine its spectral extent.

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

### Ideal raised-cosine pulse shaping

For symbol rate $R_s$ \[Bd\] and roll-off $0\le\alpha\le1$:

$$
W=\frac{(1+\alpha)R_s}{2}
$$

$W$ is real baseband bandwidth \[Hz\]. Multiplying by a carrier shifts the spectrum to $f_c-W$ through $f_c+W$.

**Passband width:** $2W=(1+\alpha)R_s$.

</div>
<div>

### Example

$R_s=1\,000$ Bd, $\alpha=0.25$:

$$
W=\frac{1.25\times1000}{2}=625\;\mathrm{Hz}
$$

Around a 1 MHz carrier:

**999.375–1 000.625 kHz**

Total passband width: **1.25 kHz**.

</div>
</div>

<div class="pt-3 text-sm vsb-muted">

Abrupt rectangular pulses have spectral tails extending indefinitely. Practical bandwidth then needs a convention, such as first-null bandwidth or a specified power fraction.

</div>

<!--
Assume fc>W and ordinary double-sideband upconversion of a real PAM waveform. Start with
m(t)=sum_k a_k p(t-kTs): the pulse spectrum P(f) shapes the spectrum of the symbol sequence. Multiplication
by cos(2pi fc t) gives X(f)=[M(f-fc)+M(f+fc)]/2. The data sequence affects the detailed spectrum, while an ideal
raised-cosine pulse limits its support to ±W. This is not a claim that baud alone fixes bandwidth.
For rectangular pulses lasting Ts=1/Rs, the pulse spectrum has sinc-shaped tails and first zeros at ±Rs;
the upconverted main-lobe null-to-null width is 2Rs, but total spectral support is infinite. Do not confuse
that first-null convention with the strict bandwidth of ideal raised-cosine shaping.
-->

---

# Extras — the wideband limit

At fixed **received** signal power $S$ and thermal-noise density $kT$:

$$
C(B)=B\log_2\left(1+\frac{S}{kTB}\right)
\quad\xrightarrow{B\to\infty}\quad
\frac{S}{kT\ln2}
$$

- $C$ — capacity \[bit/s\]; $B$ — effective bandwidth \[Hz\]
- $S$ — average received signal power \[W\]
- $kT$ — noise power spectral density \[W/Hz\]

<div v-click class="pt-5">

At low SNR, $\ln(1+x)\approx x$: increasing bandwidth spreads the fixed signal power over more noise. Capacity grows toward a **finite limit**.

</div>

<!--
Optional algebra following the noise-bandwidth and Shannon slides. Let x=S/(kTB) and use ln(1+x)/x → 1.
The model assumes fixed received power and flat noise density. Fixed transmit power alone does not guarantee
fixed received power as the channel changes. Practical receiver noise changes the effective density.
-->

---
class: compact-table
---

# Extras — compare illustrative channels

| Model / configuration | Bandwidth $B$ | Assumed linear $S/N$ | AWGN capacity |
|---|---|---|---|
| Analog voiceband example | 3.1 kHz | 1 585 | 33.0 kbit/s |
| One idealized DSL tone | 4.3125 kHz | 1 000 | 43.0 kbit/s |
| Idealized 20 MHz radio | 20 MHz | 100 | 133.2 Mbit/s |
| NR FR2-1 example, 28 GHz | 400 MHz | 6.3 | 1.147 Gbit/s |

**SNRs are hypothetical.** These are single-channel AWGN calculations, not promised service rates. DSL tones have different SNRs; real radios add coding constraints, guard intervals, overhead, and possibly spatial streams.

<div class="pt-3 text-sm vsb-muted">

400 MHz is a component-carrier option in FR2-1; aggregation is separate. [ETSI TS 138 104, §5.3.5](https://www.etsi.org/deliver/etsi_ts/138100_138199/138104/19.02.00_60/ts_138104v190200p.pdf)

</div>

<!--
Use as an optional calculation exercise; the notebook may use different illustrative numbers. The source's
upper spectrum edge is not automatically the usable bandwidth in one direction. Carrier frequency is not an
independent argument of Shannon–Hartley, although it affects propagation and practical spectrum availability.
The first row gives 32956.65 bit/s. V.34 reached 33.6 kbit/s with suitable channel conditions, not exactly the
limit for this row. V.90's digital-network access supported 56 kbit/s downstream; V.92 up to 48 upstream.
Sources: https://www.itu.int/rec/T-REC-V.90 and https://www.itu.int/rec/T-REC-V.92 .
FR2-2 n263 is a different 57–71 GHz band with options up to 2000 MHz; do not pair those widths with a generic
28/38/72 GHz row. Technology labels do not specify SNR or achievable throughput.
-->

---

# Extras — MIMO capacity by spatial mode

A fixed MIMO channel can be decomposed into $m$ parallel spatial modes:

$$
C=B\sum_{i=1}^{m}\log_2(1+\mathrm{SNR}_i),
\qquad m\le\min(n_t,n_r)
$$

Here $B$ is bandwidth \[Hz\]; $\mathrm{SNR}_i$ is the linear SNR of mode $i$ after its power allocation. Capacity uses the optimal allocation under the specified power constraint.

<div v-click class="pt-4">

For equal per-mode SNR $\gamma$, this becomes $mB\log_2(1+\gamma)$. **Keeping total transmit power fixed does not keep every mode's SNR fixed.**

</div>

<div class="pt-4 text-sm vsb-muted">

Mode gains depend on geometry, scattering, and polarization. Line of sight alone does not imply rank one. [Tse and Viswanath, chapters 7–8](https://web.stanford.edu/~dntse/wireless_book.html)

</div>

<!--
Assume a known fixed channel and Gaussian noise, decomposed into orthogonal modes; SNR_i includes mode gain
and noise. For a given nonoptimal allocation the sum is an achievable information rate, not necessarily
capacity. A compact co-polarized far-field single-path model is approximately rank one; suitable LOS geometry
or polarization can provide multiple modes. The scalar Shannon S must not be reused as though it were the
power allocated to every stream. Keep these qualifications out of the main qualitative MIMO slide.
-->

---

# Extras — entropy estimates for English

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

| Model | Approximate bits / letter |
|---|---|
| 26 equally likely letters | 4.70 |
| Unequal letter frequencies | 4.14 |
| Also condition on the previous letter | 3.56 |

Shannon's long-context guessing experiment used **27 symbols, including space**, and found experimental bounds around **0.6–1.3 bits/symbol** for its longest context.

</div>
<div>

### A model-dependent estimate

Structure makes the next symbol more predictable. These numbers depend on the text, alphabet, and model.

Plain ASCII stored one byte per character uses 8 bits. A lossless compressor exploits statistical structure to reduce the average length.

**Entropy rate is the asymptotic average limit**, not a promised size for every file.

</div>
</div>

<div class="pt-3 text-sm vsb-muted">

[Shannon, “Prediction and Entropy of Printed English,” 1951](https://fizyka.umk.pl/~milosz/KKK/shannon-1951.pdf), tables of letter statistics and experimental bounds

</div>

<!--
Distinguish the 26-letter frequency table from the 27-symbol guessing experiment. These are historical
model/experiment results, not a universal entropy constant for English. Shannon discusses sampling error
and assumptions in interpreting the experimental bounds. A predictor plus an entropy coder can compress;
its achieved rate or cross-entropy is an upper bound under suitable conditions, not automatically true entropy.
Avoid generic ZIP/LLM performance claims without a corpus, coding method, and overhead convention.
-->
