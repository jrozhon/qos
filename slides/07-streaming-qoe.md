---
theme: seriph
title: 07 · Streaming and adaptive bit rate
info: |
  440-2216/01 Quality of Service — lecture 7.
  HTTP adaptive streaming (DASH, HLS, CMAF), the playout buffer and stalling, adaptive bit rate algorithms
  (throughput-based, buffer-based, hybrid and learned), the QoE factors of streaming and their models, and how
  network QoS parameters map onto streaming QoE.
  Builds on Lectures 03 and 06; no dedicated lab yet.
exportFilename: 07-streaming-qoe
layout: cover
transition: slide-left
mdc: true
lineNumbers: true
fonts:
  provider: none
  sans: Carlito
  mono: IBM Plex Mono
---

# Streaming and Adaptive Bit Rate: the QoE of Video Delivery

### 440-2216/01 Quality of Service · Lecture 07

<div class="pt-6 text-sm vsb-muted">
Jan Rozhon &middot; Department of Telecommunications, FEECS
</div>

<!--
Ninety minutes including checkpoints: 18 min from RTP to HTTP adaptive streaming, 17 min buffer dynamics, 25 min
ABR algorithms, 20 min QoE factors and the network's role, 10 min summary/exit questions. Lecture 06 asked how good
one video looks; this lecture asks what a viewer experiences when that video is delivered over a network whose
throughput changes every second. Lecture 06 already introduced stalling and P.1203; here we open the player and see
where stalls come from and what an algorithm can do about them.
-->

---

# Where we are going

<div class="grid grid-cols-4 gap-4 pt-4 text-sm">

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 1</div>

### HTTP adaptive streaming

Why video moved from RTP to HTTP; ladder, segments, manifest

<div class="text-xs opacity-60 pt-2">↔ Lecture 06</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 2</div>

### The playout buffer

Buffer dynamics, startup delay, stalling

<div class="text-xs opacity-60 pt-2">↔ Lecture 02 queues</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 3</div>

### ABR algorithms

Throughput-, buffer-based, hybrid, learned

<div class="text-xs opacity-60 pt-2">new</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 4</div>

### QoE and the network

Stalls, switches, startup; QoS → QoE mapping

<div class="text-xs opacity-60 pt-2">↔ Lectures 03, 05, 09</div>
</div>

</div>

<div class="pt-6">

One question runs through the lecture: **when the network cannot deliver the bit rate the viewer wants, what should the player sacrifice — picture quality, smoothness, or continuity?**

</div>

<!--
The four parts go from mechanism (how HAS works) through control (the buffer and the algorithm that manages it) to
perception (what the viewer notices) and back to the network (which QoS parameter drives which QoE factor).
-->

---

# What you should be able to do

1. Explain why video streaming moved from RTP/UDP to HTTP over TCP and describe the ladder–segment–manifest structure of DASH and HLS.
2. Write the buffer balance of a player, compute startup delay and time to stall for a given bit rate and throughput.
3. Explain how throughput-based, buffer-based, hybrid (MPC), and learned ABR algorithms choose the next segment, and name each one's typical failure.
4. Rank the QoE factors of adaptive streaming — startup delay, stalling, quality level, switching — and evaluate a simple QoE model.
5. Map network QoS parameters (throughput, its variation, RTT, loss) onto streaming QoE, and name mechanisms by which the network can assist the player.

<div class="pt-6 vsb-muted">

Keep asking: **is this impairment caused by the network, by the player's decision, or by the encoding?**

</div>

<!--
Prerequisites: the M/M/1 intuition of Lecture 02 (a buffer fills when arrivals exceed service), DSCP/queuing from
Lecture 03, the MOS scale from Lecture 05, and the video metrics and P.1203 of Lecture 06.
-->

---
layout: statement
---

# In adaptive streaming, packet loss becomes waiting

## TCP hides every lost packet — the viewer sees stalls, startup delay and quality changes instead of artefacts

<!--
The thesis. In Lab 03 a lost RTP packet was a click in the audio; in HTTP streaming TCP retransmits it, so loss turns
into lower throughput and extra delay, and the player's buffer and algorithm decide how that becomes visible. The
QoS-to-QoE mapping of this lecture is therefore different from the VoIP one of Lectures 03 and 05.
-->

---
layout: section
---

# Part 1
## From RTP to HTTP adaptive streaming

---

# Why streaming moved to HTTP

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**RTP/UDP streaming (RTSP, 1990s–2000s)**

- server keeps per-client session state
- packet loss visible as artefacts
- blocked by firewalls and NAT
- needs dedicated streaming servers
- low latency — still used for conversational video (WebRTC)

</div>
<div class="border border-gray-400 p-4">

**HTTP adaptive streaming (2008 →)**

- stateless web servers, cacheable by any **CDN**
- TCP (or QUIC) retransmits losses — no artefacts
- passes every firewall on port 443
- the **client** adapts the bit rate per segment
- latency of seconds, not milliseconds

</div>
</div>

<div class="pt-6 vsb-muted text-sm">

Today HTTP adaptive streaming carries the majority of all Internet traffic in volume; RTP remains the choice where end-to-end delay matters more than scale.

</div>

<!--
Move Networks (2007), Microsoft Smooth Streaming (2008) and Apple HLS (2009) established the approach; MPEG-DASH
standardized it in 2012. The economics are the point: reusing the web's caching infrastructure made video delivery
scale to billions of viewers. The trade-off against conversational video (WebRTC over RTP) is exactly the
delay-budget discussion of Lecture 03.
-->

---

# How HTTP adaptive streaming works

<Figure src="/figures/07/has-architecture.svg" alt="The encoder produces a ladder of bit rates, each cut into segments of a few seconds. Segments and a manifest are stored on an origin server and cached by a CDN. The player downloads the manifest, then requests one segment at a time over HTTP, choosing each segment's bit rate with its ABR logic." />

<div class="pt-2 text-sm">

The **ladder** offers each title at several resolution–bit-rate pairs; each version is cut into **segments** of 2–6 s that start with an I-frame, so the player can switch rung at every segment boundary.

</div>

<!--
Segments start with an IDR frame (Lecture 06 GOP slide) so each can be decoded on its own — that is what makes
switching possible. Per-title ladders (Lecture 06 extras) change which rungs exist, not the mechanism. The ladder in
the figures of this lecture is a subset of Netflix's former fixed ladder: 0.375 to 5.8 Mbit/s.
-->

---

# The standards

<div class="text-sm">

| Standard | Body, year | Role |
|---|---|---|
| **MPEG-DASH** | ISO/IEC 23009-1, 2012 | codec-agnostic; manifest = XML *Media Presentation Description* (MPD) |
| **HLS** | Apple 2009; RFC 8216, 2017 | manifest = M3U8 playlists; required on Apple devices |
| **CMAF** | ISO/IEC 23000-19, 2018 | common fragmented-MP4 segment format for both DASH and HLS |
| **SAND** | ISO/IEC 23009-5, 2017 | messages between player and network elements |
| **CMCD** | CTA-5004, 2020 | player reports buffer, bit rate, and throughput to the CDN in each request |
| **LL-HLS, LL-DASH** | 2019–2020 | low-latency live: chunked CMAF, partial segments |

</div>

<div class="pt-4 vsb-muted text-sm">

The standards fix formats and messages — **not** the adaptation algorithm. Every player may implement its own ABR logic.

</div>

<!--
This is the crucial design decision of HAS: the ABR algorithm is left to the implementer, which is why Part 3 has so
many of them. dash.js (DASH Industry Forum reference player), hls.js, Shaka Player and ExoPlayer each ship their own.
SAND and CMCD come back in Part 4 as network assistance.
-->

---

# Checkpoint — where did the packet loss go?

<div class="checkpoint-question">

A link used for two services loses 1 % of its packets. The VoIP call from Lab 03 sounds clearly degraded. A HAS video on the same link shows no blocking or smearing at all. Why — and does that mean the loss is harmless for the video?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**TCP retransmits every lost segment**, so every video byte eventually arrives intact — no artefacts. But loss **reduces TCP throughput** (congestion window halving) and adds retransmission delay. The player sees a slower link and reacts: it chooses a lower bit rate or, if the buffer runs out, stalls. The loss has changed form, not disappeared.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. Part 4 quantifies this with the Mathis
formula for TCP throughput under loss.
-->

---
layout: section
---

# Part 2
## The playout buffer

---

# The buffer balance

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

The buffer $B$ holds seconds of video. While a segment of duration $\tau$ and bit rate $R$ downloads over throughput $C$:

$$
\frac{\mathrm{d}B}{\mathrm{d}t} = \frac{C}{R} - 1
$$

- each second of download adds $C/R$ seconds of video,
- playback removes one second per second,
- $B = 0$ during playback → **stall** (rebuffering).

</div>
<div>

<div class="vsb-fill">

### The sustainability condition

$R \le C$ on average — the same condition as $\rho < 1$ for a queue in Lecture 02.

</div>

<div class="pt-4 text-sm vsb-muted">

Download time of one segment: $T_k = \dfrac{R_k\,\tau}{C_k}$. The player sees only these $T_k$, not $C$ directly.

</div>

</div>
</div>

<!--
The buffer is a queue whose arrival process is the download and whose service process is playback at exactly one
second per second. If the buffer is full (typically 30–60 s for video on demand), the player pauses requests: this is
the ON-OFF pattern that Part 3 shows confuses throughput estimation.
-->

---

# A player that never adapts

<Figure src="/figures/07/buffer-dynamics.svg" alt="Top: available throughput over 130 seconds with drops to about 1.4 and 2.2 Mbit/s, against a constant requested bit rate of 4.3 Mbit/s. Bottom: the playout buffer grows while throughput exceeds the bit rate and drains during the drops, emptying five times for 18 seconds of stalling in total." />

<!--
Produced by the small simulator in scripts/generate-figures.py: 30 segments of 4 s, buffer cap 30 s, playback starts
after the first segment. At 4.3 Mbit/s over 1.4 Mbit/s one segment takes 12.3 s to download and the buffer loses
8.3 s per segment — the 11 s built up in the first 20 s last barely one and a half segments.
-->

---

# Worked example — startup and time to stall

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

**Startup delay** (first segment, $\tau = 4$ s, $C = 6.5$ Mbit/s, ignoring RTTs):

| First rung | Download |
|---|---|
| 0.375 Mbit/s | $1.5/6.5 = 0.23$ s |
| 4.3 Mbit/s | $17.2/6.5 = 2.65$ s |

</div>
<div v-click>

**Time to stall** at $R = 3$ Mbit/s after the link drops to $C = 2$ Mbit/s with $B = 12$ s buffered:

$$
\frac{\mathrm{d}B}{\mathrm{d}t} = \frac{2}{3} - 1 = -\frac{1}{3}
\;\Rightarrow\; t_{\text{stall}} = 36\ \text{s}
$$

<div class="pt-2 text-sm vsb-muted">

36 s of warning — enough for any algorithm that watches the buffer to step down before the viewer notices.

</div>

</div>
</div>

<!--
The first calculation explains why almost every player starts at a low rung: a tenfold lower startup delay for a few
seconds of lower quality. The second is the argument for buffer-based adaptation: the buffer level is a direct,
noise-free measure of how much time the player has left.
-->

---

# Checkpoint — how big should the buffer be?

<div class="checkpoint-question">

A video-on-demand player allows 60 s of buffer; a live sports stream is watched 6 s behind the live edge. What does the larger buffer buy, and why can the live player not simply use it too?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

A large buffer **absorbs throughput dips** — at $C/R = 0.5$, 60 s of buffer survive two minutes of degraded link. But the buffer cannot hold video that does not exist yet: a live player can be at most as far ahead as it is **behind the live edge**. Low latency and robustness to throughput variation are in direct conflict; low-latency live streaming (2–6 s) is the hardest case for ABR.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. Classic HLS live used 3 segments of 6–10 s,
so 20–30 s behind live; LL-HLS and chunked CMAF bring that down to a few seconds at the cost of a tiny buffer.
-->

---
layout: section
---

# Part 3
## Adaptive bit rate algorithms

---

# The ABR problem

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

Before each segment $k$ the player chooses a rung $R_k$ from the ladder, knowing only the past download times and the current buffer.

Its goal is conflicting:

- **high** bit rate → better picture,
- **few** switches → smooth experience,
- **no** stalls, **short** startup.

</div>
<div>

A common objective (Yin et al., 2015) — the **linear QoE**:

$$
\begin{aligned}
\mathrm{QoE} = {} & \sum_{k} q(R_k) - \lambda \sum_{k} \bigl|q(R_{k+1}) - q(R_k)\bigr| \\
& - \mu\, T_{\text{stall}} - \mu_s T_s
\end{aligned}
$$

<div class="pt-2 text-sm vsb-muted">

$q(\cdot)$ quality of a rung (often $q(R)=R$), $T_{\text{stall}}$ total stall time, $T_s$ startup delay, $\lambda, \mu, \mu_s$ weights.

</div>

</div>
</div>

<!--
The future throughput is unknown, which makes this an online control problem under uncertainty. Every algorithm on
the next slides is a different answer to "how do I predict what I do not know" — from the past throughput, from the
buffer, or from a learned model.
-->

---

# Throughput-based adaptation

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

Estimate the throughput from recent segments and pick the highest rung below it, with a safety margin:

$$
\hat C = \frac{n}{\sum_{i=1}^{n} 1/C_{k-i}}, \qquad R_k = \max\{R \le \alpha \hat C\}
$$

The **harmonic mean** damps outliers (FESTIVE, Jiang et al., 2012); $\alpha \approx 0.8$–$0.9$.

</div>
<div class="text-sm">

**Failure modes**

- reacts **late** to a sudden drop: the estimate is still high when the buffer is already low
- **ON-OFF** download pattern: while the buffer is full the player idles, and short downloads underestimate TCP's capacity
- **downward spiral** next to a competing TCP flow: lower rate → smaller segments → lower estimate (Huang et al., IMC 2012)
- **unfairness** between players sharing a bottleneck

</div>
</div>

<!--
Huang, Handigol, Heller, McKeown, Johari, "Confused, timid, and unstable: picking a video streaming rate is hard",
IMC 2012 (Stanford) — the measurement study that showed commercial players collapsing to the lowest rate next to a
bulk download. Akhshabi et al. (MMSys 2011, NOSSDAV 2012) showed oscillation and unfairness between competing players.
-->

---

# Buffer-based adaptation

<Figure src="/figures/07/bba-map.svg" alt="Rate map of a buffer-based algorithm: below a reservoir of 8 seconds of buffer the lowest rate is requested, across an 18-second cushion the target rate rises linearly to the highest rate, and above it the highest rate is requested; the chosen rung follows as a staircase." />

<div class="pt-1 text-sm">

**BBA** (Huang et al., SIGCOMM 2014, Netflix trial): choose the rate from the **buffer level alone**. The reservoir protects against stalls; the cushion trades buffer for quality. Throughput estimation is needed only at startup.

</div>

<!--
Huang, Johari, McKeown, Trunnell, Watson, "A buffer-based approach to rate adaptation", SIGCOMM 2014: in a Netflix
field experiment BBA reduced the rebuffer rate by 10–20 % against the production algorithm while keeping a similar
average rate. BOLA (Spiteri, Urgaonkar, Sitaraman, INFOCOM 2016) puts buffer-based adaptation on a Lyapunov-
optimization footing and is the buffer rule in the dash.js reference player.
-->

---

# Two algorithms, one link

<Figure src="/figures/07/abr-compare.svg" alt="On the same throughput trace, the throughput-based algorithm starts high, is caught by the drop at 20 seconds and stalls twice, 5.2 seconds in total; the buffer-based algorithm ramps up slowly, keeps its buffer and never stalls, with 9 switches against 7 and a higher linear QoE." />

<!--
Same simulator, same trace, same ladder as the buffer-dynamics figure. The throughput-based player is not stupid: it
chose 4.3 Mbit/s because the link delivered 6.5 Mbit/s. It fails because its information is about the past; the
buffer-based player had built up 25 s of buffer before the drop and could ride it out. The price is a slow start and
more switches. The linear QoE uses q(R) = R, lambda = 1, mu = mu_s = 5.8.
-->

---

# Hybrid and learned algorithms

<div class="grid grid-cols-3 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**Model predictive control**

MPC (Yin et al., SIGCOMM 2015): predict throughput for the next few segments, optimize the linear QoE over that horizon, apply only the first decision, repeat.

</div>
<div class="border border-gray-400 p-4">

**Hybrid rules**

dash.js *DYNAMIC*: throughput rule at startup and after seeks, BOLA once the buffer is established — the best of both failure modes.

</div>
<div class="border border-gray-400 p-4">

**Learned policies**

Pensieve (Mao et al., SIGCOMM 2017): reinforcement learning trained on throughput traces. Fugu (Yan et al., NSDI 2020): learned transmit-time predictor inside MPC.

</div>
</div>

<div class="pt-6 vsb-muted text-sm">

Stanford's **Puffer** study streamed live TV to real viewers for a year: in the wild, simple buffer-based control matched several sophisticated schemes, and only an algorithm trained *in situ* improved on it.

</div>

<!--
Yan et al., "Learning in situ: a randomized experiment in video streaming", NSDI 2020 — a cautionary result on
evaluating ABR in emulation: schemes that won on recorded traces did not win on the real Internet. It is a good
general lesson on the gap between simulated QoS and measured QoE.
-->

---

# Checkpoint — which algorithm, when?

<div class="checkpoint-question">

A viewer's phone moves from Wi-Fi to a congested cell: throughput falls from 20 to 1.5 Mbit/s in one second. The player has 25 s of buffer at 4.3 Mbit/s. Which reacts better — throughput-based or buffer-based — and what does each do in the next 20 s?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

The **throughput-based** player's next estimate still averages the fast Wi-Fi samples, so it requests another 4.3 Mbit/s segment; its download takes 11.5 s, only then does the estimate collapse and it jumps to the lowest rung — one abrupt switch. The **buffer-based** player also finishes that segment, but its rate map lowers the request step by step as the buffer falls through the cushion. With 25 s of buffer neither stalls; the buffer-based one degrades more gracefully.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. 4.3 Mbit/s × 4 s / 1.5 Mbit/s ≈ 11.5 s.
With only 8 s of buffer the throughput-based player would stall; that is the figure on the previous slide.
-->

---
layout: section
---

# Part 4
## Streaming QoE and the network

---

# The QoE factors of adaptive streaming

<div class="grid grid-cols-2 gap-x-10 gap-y-3 pt-2 text-sm">
<div>

**Stalling** — number, duration, and position of rebuffering events. The **dominant** factor.

**Initial (startup) delay** — tolerated much better than a stall of the same length: viewers expect waiting at the start.

</div>
<div>

**Quality level** — bit rate, resolution, and the resulting visual quality (Lecture 06 metrics).

**Quality switching** — frequency and amplitude; downward and abrupt switches hurt most, gradual steps are preferred.

</div>
</div>

<div class="pt-6">

Ordering from the literature (Seufert et al., 2015): **stalling ≫ initial delay**, and **stalling > low but constant quality > frequent switching**.

</div>

<!--
Seufert et al., "A survey on quality of experience of HTTP adaptive streaming", IEEE COMST 2015 is the reference
survey. Memory effects also matter: recent events weigh more (recency), and one bad experience lowers the tolerance
for the next — which is why P.1203 models a whole session, not isolated events.
-->

---

# How much does a stall cost?

<Figure src="/figures/07/stall-mos.svg" alt="MOS against the number of stalls for stall lengths of 1, 3 and 5 seconds according to the exponential model of Hossfeld et al.: the score falls steeply from 5 with the first stalls and saturates near 1.5." />

<div class="pt-1 text-sm">

One 3 s stall in a 30 s clip: $3.5\,e^{-(0.15\cdot 3 + 0.19)} + 1.5 = 3.35$ — from "excellent" to "fair" with a single event.

</div>

<!--
Hossfeld, Schatz, Seufert, Hirth, Zinner, Tran-Gia, "Quantification of YouTube QoE via crowdsourcing", 2011. The model
is for short clips; for long sessions the stall frequency (stalls per minute) and the rebuffering ratio are used. In the
exponent, the number of stalls counts more than their length: five 1 s stalls cost more than one 5 s stall.
-->

---

# Viewers vote with their feet

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

<div class="vsb-fill">

### 2 s

Viewers begin to abandon a video whose startup delay exceeds 2 s; each further second adds about **5.8 %** abandonment (Krishnan & Sitaraman, IMC 2012, 23 M views).

</div>

</div>
<div>

<div class="vsb-fill">

### 1 % → 3 min

A 1 % increase of the **buffering ratio** (stall time / session time) cut viewing time of a live event by more than 3 minutes (Dobrian et al., SIGCOMM 2011).

</div>

</div>
</div>

<div class="pt-6 vsb-muted text-sm">

Engagement — abandonment, viewing time, return rate — is QoE measured at scale without asking anyone. It is what streaming providers actually optimize.

</div>

<!--
These two measurement studies (Akamai data, Conviva data) moved QoE research from the lab into production. They
complement the MOS-based models: MOS says how a viewer rates a session, engagement says whether the viewer stays.
-->

---

# Worked example — two sessions, one score

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div>

Five 4 s segments; linear QoE with $q(R)=R$, $\lambda = 1$, $\mu = 4.3$:

| | Session A | Session B |
|---|---|---|
| Rates, Mbit/s | 3, 3, 3, 3, 3 | 4.3, 4.3, 1.75, 4.3, 4.3 |
| $\sum q$ | 15.0 | 18.95 |
| Switching | 0 | 2.55 + 2.55 = 5.1 |
| Stall | 0 s | 2 s → 8.6 |

</div>
<div v-click>

<div class="vsb-fill">

### A: 15.0 · B: 5.25

</div>

<div class="pt-4 vsb-muted">

B delivered **26 % more bits** and scores **less than half** of A. A constant middle rung beats an ambitious one that must fall back — the ranking of the factors slide, in numbers.

</div>

</div>
</div>

<!--
18.95 − 5.1 − 2 × 4.3 = 5.25. The weights are a modelling choice: with mu = 4.3 one second of stall costs as much as
one second of the best quality. Standardized models (P.1203, Lecture 06) calibrate such weights against subjective
tests instead of choosing them.
-->

---

# From network QoS to streaming QoE

<div class="text-sm">

| Network QoS parameter | Effect in the player | QoE factor |
|---|---|---|
| Mean throughput | highest sustainable rung | quality level |
| Throughput variation | estimate errors, buffer drain | switching, stalls |
| Round-trip time | slower TCP ramp-up, request gaps | startup delay, lower throughput |
| Packet loss | retransmission, cwnd halving → lower throughput | quality level, stalls — **not** artefacts |
| Jitter | absorbed by the buffer | none, if the buffer is non-empty |

</div>

<div class="pt-4 text-sm">

TCP throughput under loss (Mathis et al., 1997): $\;C \approx \dfrac{\mathrm{MSS}}{\mathrm{RTT}} \cdot \dfrac{1.22}{\sqrt{p}}$ — with MSS 1460 B, RTT 50 ms, $p = 0.1\,\%$: $C \approx 9$ Mbit/s per connection.

</div>

<!--
Contrast with Lecture 05's E-model, where loss and jitter enter directly as impairments: in HAS they enter only through
throughput. The Mathis formula is an approximation for Reno-style congestion control; CUBIC and BBR behave differently
but the qualitative message holds: throughput falls with the square root of loss and inversely with RTT, so a
long-distance path with a little loss can starve even a fast access link — the reason for CDNs close to the viewer.
-->

---

# The network can help

<div class="grid grid-cols-3 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**Tell the network**

**CMCD**: the player adds its buffer level, bit rate, and measured throughput to every request; the CDN can prioritize players about to stall.

</div>
<div class="border border-gray-400 p-4">

**Tell the player**

**SAND** and CMSD: network or CDN elements send hints — available bandwidth, cache state — so the player does not have to guess.

</div>
<div class="border border-gray-400 p-4">

**Control the network**

**SDN** (Lecture 09): a controller that sees all players on a bottleneck allocates bandwidth or queues per player for fairness and fewer stalls.

</div>
</div>

<div class="pt-6 vsb-muted text-sm">

Network assistance closes the loop between QoS mechanisms and QoE — at the price of cooperation between parties that encrypted HTTPS traffic otherwise keeps apart.

</div>

<!--
CTA-5004 (CMCD, 2020) is already implemented in dash.js, hls.js and several CDNs. SDN-assisted streaming (e.g.
Bentaleb et al., SDNDASH, 2016; Georgopoulos et al., 2013) is the research line that connects this lecture to Lecture
09. DSCP marking of video (Lecture 03, AF41) is the classical, per-class version of the same idea.
-->

---

# Checkpoint — start delay or stall?

<div class="checkpoint-question">

A provider can either (a) start every video 3 s later with a larger initial buffer, or (b) start in 0.5 s and accept one 2 s stall in 10 % of sessions. Which improves QoE, and which improves engagement?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

For **MOS**, stalls cost far more than initial delay, so (a) looks safer. For **engagement**, 3 s is past the 2 s abandonment threshold: every session pays it, and ≈ 6 % of viewers leave before the video starts — while (b) hurts only one session in ten. The answer depends on which QoE measure the provider optimizes — and a good ABR (small startup rung, buffer-based ramp-up) avoids having to choose.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. There is no single right answer; the goal
is to see that MOS models and engagement data answer different questions.
-->

---

# Common mix-ups

<div class="grid grid-cols-3 gap-4 pt-2 text-sm">
<div class="border border-orange-400 p-3">

**Bit rate vs throughput**

Bit rate is what the player requests; throughput is what the network delivers. Stalls come from the gap.

</div>
<div class="border border-orange-400 p-3">

**Stall vs startup delay**

Both are waiting, but viewers penalize a mid-stream stall far more.

</div>
<div class="border border-orange-400 p-3">

**Standard vs algorithm**

DASH and HLS define formats; the ABR algorithm is each player's own choice.

</div>
<div class="border border-orange-400 p-3">

**Loss vs artefacts**

Over TCP, loss causes lower throughput and stalls, not blocking.

</div>
<div class="border border-orange-400 p-3">

**More bits vs better QoE**

A higher mean bit rate with stalls or switches can score lower than a constant lower rate.

</div>
<div class="border border-orange-400 p-3">

**MOS vs engagement**

Ratings and viewer behaviour are both QoE measures — and can disagree.

</div>
</div>

<!--
Six confusions that recur in exam answers.
-->

---

# Summary

<div class="grid grid-cols-2 gap-x-10 gap-y-2 pt-2 text-sm">

<div>

**HTTP adaptive streaming**
Ladder × segments × manifest on plain web servers and CDNs; the client adapts.

**Buffer balance**
$\mathrm{d}B/\mathrm{d}t = C/R - 1$; stall when $B = 0$; sustainable only if $R \le C$.

**Throughput-based ABR**
Estimates $C$ from the past; late on sudden drops, confused by ON-OFF traffic.

**Buffer-based ABR**
Rate from buffer level; robust against stalls, slower to ramp up.

</div>
<div>

**Hybrid and learned ABR**
MPC optimizes a QoE objective over a horizon; learned schemes must be tested in the wild.

**QoE factors**
Stalling ≫ initial delay; constant quality beats frequent switching.

**QoS → QoE mapping**
Loss and RTT act through TCP throughput; jitter vanishes in the buffer.

**Network assistance**
CMCD, SAND, and SDN let the network and the player cooperate.

</div>

</div>

<!--
Read them aloud, one sentence each. Then the exit questions.
-->

---

# Exit questions — use the ideas

1. A player requests 3 Mbit/s segments of 4 s over a 2.4 Mbit/s link with 10 s buffered. When does it stall if it never switches?
2. Why does a throughput-based player that idles because its buffer is full tend to underestimate the available throughput?
3. Session A: 1 stall of 6 s. Session B: 3 stalls of 2 s. Using the exponential model, which scores higher, and why?
4. An operator cuts packet loss on a path from 0.4 % to 0.1 %. Using the Mathis formula, by what factor can per-connection throughput rise, and which QoE factors could improve?

<div v-click class="pt-5 vsb-muted">

**Explain the mechanism**, not just its name.

</div>

<!--
Answers: (1) dB/dt = 2.4/3 − 1 = −0.2, so 10/0.2 = 50 s. (2) Short downloads after an idle period spend much of their
time in TCP slow start (and the congestion window may have decayed during idle), so the measured rate is below the
path capacity. (3) A: 3.5 e^(−(0.9+0.19)) + 1.5 = 2.68; B: 3.5 e^(−(0.3+0.19)·3) + 1.5 = 2.30 — A scores higher: the
number of stalls weighs more than their length. (4) sqrt(0.4/0.1) = 2, so twice the throughput: higher rungs, fewer
stalls, faster startup.
-->

---

# Where you use this

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

There is no dedicated streaming lab yet; the tools of the other labs cover the pieces:

- `tc` shaping and `netem` (Lab 03, Lab 05) create the throughput traces of Part 2
- PSNR, SSIM, VMAF (Lab 04) score the rungs of the ladder
- the `simpy` pipeline (Lab 02) can model the buffer as a queue

</div>
<div>

<div class="text-sm">

Try it on your own machine: limit your link, open the dash.js reference player, and watch its buffer and bit-rate graphs.

</div>

<div class="pt-2 text-sm vsb-muted">

```bash {lines:false}
sudo tc qdisc add dev eth0 root \
  tbf rate 2mbit burst 32kbit \
  latency 400ms
# play in the dash.js reference player
sudo tc qdisc del dev eth0 root
```

</div>
</div>
</div>

<!--
Replace eth0 with the machine's interface. The dash.js reference player shows buffer level, requested and downloaded
bit rate, and switches live; switching the ABR strategy between throughput, BOLA and dynamic reproduces the comparison
of Part 3 on a real network.
-->

---

# References — standards

- ISO/IEC 23009-1, *Dynamic adaptive streaming over HTTP (DASH) — Part 1: Media presentation description and segment formats*, 5th ed., 2022.
- R. Pantos, W. May, "HTTP Live Streaming," RFC 8216, 2017.
- ISO/IEC 23000-19, *Common media application format (CMAF) for segmented media*, 2018.
- ISO/IEC 23009-5, *DASH — Part 5: Server and network assisted DASH (SAND)*, 2017.
- CTA-5004, *Web Application Video Ecosystem — Common Media Client Data*, 2020.
- ITU-T P.1203, *Parametric bitstream-based quality assessment of progressive download and adaptive audiovisual streaming services over reliable transport*, 2017.

<!--
The standards behind Parts 1 and 4. P.1203 was covered in Lecture 06.
-->

---

# References — literature

<div class="text-sm">

- M. Seufert et al., "A survey on quality of experience of HTTP adaptive streaming," *IEEE Communications Surveys & Tutorials*, 17(1), 469–492, 2015.
- T. Hoßfeld et al., "Quantification of YouTube QoE via crowdsourcing," *IEEE ISM Workshop on Multimedia Quality*, 2011.
- F. Dobrian et al., "Understanding the impact of video quality on user engagement," *ACM SIGCOMM*, 2011.
- S. S. Krishnan, R. K. Sitaraman, "Video stream quality impacts viewer behavior," *ACM IMC*, 2012.
- T.-Y. Huang et al., "Confused, timid, and unstable: picking a video streaming rate is hard," *ACM IMC*, 2012.
- T.-Y. Huang et al., "A buffer-based approach to rate adaptation: evidence from a large video streaming service," *ACM SIGCOMM*, 2014.
- X. Yin et al., "A control-theoretic approach for dynamic adaptive video streaming over HTTP," *ACM SIGCOMM*, 2015.
- K. Spiteri, R. Urgaonkar, R. K. Sitaraman, "BOLA: near-optimal bitrate adaptation for online videos," *IEEE INFOCOM*, 2016.
- H. Mao, R. Netravali, M. Alizadeh, "Neural adaptive video streaming with Pensieve," *ACM SIGCOMM*, 2017.
- F. Y. Yan et al., "Learning in situ: a randomized experiment in video streaming," *USENIX NSDI*, 2020.
- M. Mathis et al., "The macroscopic behavior of the TCP congestion avoidance algorithm," *ACM SIGCOMM CCR*, 27(3), 1997.

</div>

<!--
Stanford (Huang, McKeown, Yan), MIT (Mao, Alizadeh), CMU (Yin, Jiang, Sekar) and UMass (Sitaraman, Spiteri) are the
main academic groups behind ABR research.
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
