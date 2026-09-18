---
theme: seriph
title: 03 · QoS mechanisms and the road to QoE
info: |
  440-2216/01 Kvalita služeb — lecture 3.
  Quality of Service vs Quality of Experience, the end-to-end delay budget, congestion management (CAC, queuing,
  RED), and link efficiency and marking (compression, LFI, DSCP).
  Companion lecture to Exercise 03.
exportFilename: 03-qos-mechanisms
layout: cover
transition: slide-left
mdc: true
lineNumbers: true
fonts:
  provider: none
  sans: Carlito
  mono: IBM Plex Mono
---

# Quality of Service mechanisms and the road to Quality of Experience

### 440-2216/01 Kvalita služeb · Lecture 03

<div class="pt-6 text-sm vsb-muted">
Jan Rozhon, Miroslav Vozňák &middot; Department of Telecommunications, FEECS
</div>

<!--
Ninety minutes including checkpoints: 8 min QoS/QoE definitions, 17 delay budget with worked example, 32
congestion management (CAC, token bucket, WFQ, RED), 23 link efficiency and marking, 10 summary/exit
questions/exercise setup. Lecture 01 asked how many bits a channel can carry; Lecture 02 asked how long a
request waits in a
queue. This lecture asks what a network operator actually does about that delay, jitter, and loss — and where
the line falls between "the network's numbers" (QoS) and "what the user makes of them" (QoE). Exercise 03
injects exactly these impairments with tc netem and scores their effect with PESQ/ViSQOL.
-->

---

# Where we are going

<div class="grid grid-cols-4 gap-4 pt-4 text-sm">

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 1</div>

### QoE and QoS

Definitions, scope, and the four QoS parameters

<div class="text-xs opacity-60 pt-2">↔ Step 1, Q1</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 2</div>

### Delay budget

Fixed vs variable delay components

<div class="text-xs opacity-60 pt-2">↔ Step 3, Q3</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 3</div>

### Congestion

CAC, token bucket, WFQ, RED

<div class="text-xs opacity-60 pt-2">↔ Steps 3–4, Q4</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 4</div>

### Link efficiency

Compression, LFI, DSCP marking

<div class="text-xs opacity-60 pt-2">↔ Question 2</div>
</div>

</div>

<div class="pt-6">

One question runs through the lecture: **which mechanism changes what a network provides, and does that change what a person perceives?**

</div>

<!--
Lecture 2 built the vocabulary (arrival rate, service rate, delay, loss) from queueing theory. This lecture
attaches names and standards to the network mechanisms that manage those quantities in practice, then asks
where the QoS/QoE line actually falls.
-->

---

# What you should be able to do

1. State the ITU-T definitions of QoS and QoE and explain how their scope and focus differ.
2. Decompose an end-to-end delay budget into fixed and variable components and identify which one dominates under load.
3. Explain what CAC, token-bucket enforcement, WFQ scheduling, and RED each do, and why RED does not help non-responsive UDP/RTP traffic.
4. Explain why link fragmentation/interleaving and header compression matter on slow links, and how DSCP marking classifies traffic for a scheduler.

<div class="pt-6 vsb-muted">

Keep asking: **which QoS parameter does this mechanism change — throughput, delay, jitter, or loss — and for whom?**

</div>

<!--
Four outcomes for the lecture. Students need the queueing vocabulary from Lecture 02 (arrival/service rate,
utilization, Little's law) and the RTP/packet-size arithmetic from the Exercise 03 theory section. No new
mathematics is introduced beyond arithmetic and the RED linear interpolation.
-->

---
layout: statement
---

# A network can only ever manage Quality of Service

## Quality of Experience is what a person makes of it — QoS mechanisms are the tools this lecture builds

<!--
This is the thesis the whole lecture supports. Every mechanism from here on (CAC, queuing, RED, LFI,
compression, marking) manages a QoS parameter — throughput, delay, jitter, or loss. None of them can reach
into the user's head; Exercise 03 measures how far that gap actually is with PESQ and ViSQOL.
-->

---
layout: section
---

# Part 1
## Quality of Service and Quality of Experience

---

# Quality of Service — a formal definition

<div class="pt-2">

ITU-T Recommendation E.800 defines Quality of Service as the

> "Totality of characteristics of a telecommunications service that bear on its ability to satisfy stated and implied needs of the user of the service."

</div>

<div class="pt-4">

Traditionally, technology-centric approaches based on QoS parameters — throughput, delay, jitter, packet loss — have been used to ensure service quality. They are **objective**, **measurable at the network layer**, and the subject of the rest of this lecture.

</div>

<!--
ITU-T E.800 (09/2008). This is deliberately a network-side definition: it talks about a service's
characteristics, not about how a person feels about them. That gap is exactly what QoE closes on the next
slide.
-->

---

# Quality of Experience — a formal definition

<img class="lecture-diagram" src="/figures/03/qoe-qos-scope.svg" alt="Three stacked layers: the network layer provides Quality of Service (throughput, delay, jitter, packet loss), which is encoded into application and content, which the user perceives as Quality of Experience." />

<div class="pt-2 text-sm">

**QoE** is "the degree of delight or annoyance of the user of an application or service" (Qualinet White Paper, 2013; ITU-T P.10/G.100 Amd. 5). It expands the horizon beyond network performance to people's expectations and even hedonic needs.

</div>

<!--
QoE can apply even without telecommunications at all — e.g. HD video played in a home theatre, judged on
screen, room lighting, and seating, none of which a network operator controls. QoS is necessary machinery;
QoE is the outcome a person actually reports.
-->

---

# Scope and focus: how QoS and QoE differ

<div class="grid grid-cols-1 gap-4 pt-2">

<div class="border border-gray-400 p-4">

**Scope** — QoS typically focuses on telecommunications services. QoE covers a much broader domain that sometimes does not involve telecommunications at all, e.g. HD video played in a home theatre.

</div>
<div class="border border-gray-400 p-4">

**Focus** — QoS deals with performance aspects of physical systems. QoE deals with the user's *assessment* of that performance, as colored by context, culture, expectations and their fulfillment, socio-economic factors, and psychological profile, among other factors.

</div>

</div>

<div class="pt-6 vsb-muted text-sm">

Both readings matter for Exercise 03: the network side is what `tc netem` controls; the human side is what the ACR/DCR listening tests capture.

</div>

<!--
This slide is close to the original course material almost verbatim — it is the cleanest statement of the
distinction and is worth reading nearly as written. Ask the room for their own scope/focus example before
moving on.
-->

---

# The QoS parameters this course measures

QoS features affect a network by manipulating four characteristics:

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div>

- **Throughput** — data delivered per unit time
- **Delay** — one-way latency from sender to receiver

</div>
<div>

- **Jitter** — delay *variation* between consecutive packets
- **Packet loss** — packets discarded or corrupted in transit

</div>
</div>

<div class="pt-6">

These four are exactly what Exercise 03's `tc netem` injects (`delay`, a jitter argument, and `loss`) and exactly what PESQ and ViSQOL then score the perceptual effect of.

</div>

<!--
↔ Exercise 03 Question 1 (which layer carries what) and the netem theory section. Keep this list on the board
for the rest of the lecture — every mechanism in Parts 2–4 manages one or more of these four.
-->

---

# Checkpoint — is this a QoS problem?

<div class="checkpoint-question">

A user complains a video call "feels bad", but monitoring shows 0% packet loss, jitter comfortably inside the receiver's buffer, and ample throughput. Is this necessarily a QoS problem?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Not necessarily.** All four measured QoS parameters look fine, yet QoE can still be poor for reasons outside them entirely: codec artifacts, screen or speaker hardware, poor lighting for video, mismatched expectations, or an urgent call versus a casual one. This is the scope/focus slide made concrete — good QoS numbers are necessary but not sufficient for good QoE.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. This previews why Exercise 03 pairs
objective network measurements with subjective ACR/DCR ratings rather than relying on netem parameters alone.
-->

---
layout: section
---

# Part 2
## The one-way delay budget

---

# Fixed delay: set once the link and codec are chosen

<img class="lecture-diagram" src="/figures/03/delay-budget.svg" alt="A one-way delay timeline of six components: fixed codec, serialization, and propagation delay, followed by variable queuing, forwarding, and shaping delay." />

<div class="grid grid-cols-3 gap-6 pt-2 text-sm">
<div>

**Serialization** — time to encode a packet's bits onto the physical interface: packet size over link rate.

</div>
<div>

**Propagation** — time for one bit to cross the link, close to the speed of light in the medium.

</div>
<div>

**Codec / packetization** — time to encode a frame and accumulate enough samples to fill one packet.

</div>
</div>

<!--
All three depend only on the link, the path, and the codec/packetization interval chosen at design time — none
of them changes when the network gets busy. Serialization = packet size [bit] / link rate [bit/s]; propagation
≈ distance / (2/3 c) for typical fiber, roughly 5 μs/km.
-->

---

# Variable delay: grows under load

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

**Queuing delay** — time spent waiting in a router's output buffer before transmission begins.

**Forwarding/processing delay** — time to decide where to send a packet, typically small enough to ignore in a delay budget.

</div>
<div>

**Shaping delay** — added deliberately to match a contracted rate, so a carrier does not discard traffic that exceeds it.

**Network delay** — delay contributed by the carrier's own internal network components.

</div>
</div>

<div class="pt-6 vsb-muted">

All four depend on **how busy the path is right now** — this is where Lecture 02's queueing theory re-enters the picture.

</div>

<!--
Forwarding delay is typically negligible in modern routers (hardware-switched); it is listed for completeness
because the source material distinguishes it from queuing delay. Network delay is deliberately vague — it is
whatever the carrier's own internal topology adds, outside the customer's visibility.
-->

---

# Worked example — a VoIP call's delay budget

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

G.711 call from Exercise 03: 160 B payload, 40 B of RTP/UDP/IP headers, 20 ms packetization, over a 64 kbit/s branch-office link, 1500 km path.

| Component | Delay |
|---|---|
| Codec/packetization (fixed) | 20 ms |
| Serialization: 1600 bit / 64 kbit/s (fixed) | 25 ms |
| Propagation: ≈1500 km (fixed) | 7.5 ms |
| Queuing, lightly loaded (variable) | 5 ms |

</div>
<div v-click>

<div class="vsb-fill">

### Total ≈ 57.5 ms

well inside ITU-T G.114's ≈150 ms one-way guidance

</div>

<div class="pt-4 text-sm vsb-muted" v-click>

Now let the link get busy: queuing delay alone climbs to 100 ms (Lecture 02: $W=1/(\mu-\lambda)$ as $\rho\to1$). Total becomes **157.5 ms** — over budget, with every fixed component unchanged.

</div>

</div>
</div>

<!--
Numbers reuse Exercise 03's G.711 arithmetic (200 B packet, 20 ms interval) so the two decks stay consistent.
The second reveal is the point of the slide: nothing about the codec, the link, or the path changed — only
queuing delay, under load, was enough to blow the whole budget.
-->

---

# Checkpoint — the dangerous component

<div class="checkpoint-question">

Recall Lecture 02: $W = 1/(\mu-\lambda)$ grows without bound as $\rho \to 1$. Which single component of this delay budget behaves that way, and what does it imply for link dimensioning?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Queuing delay** — the only component governed by an M/M/1-style formula that diverges as utilization approaches 1. Serialization, propagation, and codec delay are fixed once the link, path, and codec are chosen; shaping and network delay move only mildly. This is exactly why Lecture 02 stressed running links well below full utilization: near saturation, queuing delay alone can consume a delay budget that every other component left comfortably under threshold.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. Directly reuses Lecture 02's
ρ→1 result; if students struggle, point back at the L=ρ/(1-ρ) table from that lecture.
-->

---
layout: section
---

# Part 3
## Managing congestion: admission, enforcement, scheduling, and avoidance

---

# Call Admission Control (CAC)

<div class="pt-2">

CAC tools decide whether a network can accept a new voice or video call **before it starts**. That decision might rest on many factors, but several of them involve a measurement or estimate of available throughput.

</div>

<div class="pt-6 vsb-muted">

This is Lecture 02's Erlang B logic, applied online: a loss system (M/M/N/N) decides per arriving call whether capacity remains, rather than dimensioning a trunk group offline from an average traffic figure.

</div>

<!--
CAC and Erlang B answer the same question — "is there room?" — at different moments: Erlang B dimensions N in
advance from expected traffic A; CAC tests the current state of a specific link or codec budget for each
arriving call. A call CAC rejects is blocked, exactly like a call Erlang B predicts will be blocked.
-->

---

# Traffic enforcement — the token bucket

<img class="lecture-diagram" src="/figures/03/token-bucket.svg" alt="Tokens accumulate in a bucket at rate r up to depth b. A packet needs enough tokens to be sent immediately; otherwise it waits (shaping) or is dropped or marked (policing)." />

<div class="pt-2 text-sm">

Tokens fill a bucket at rate $r$, up to a maximum depth $b$. Sending a packet costs one token per byte. Traffic entering any interval of length $T$ is bounded by $b + rT$: bursts up to $b$ pass immediately, but the long-run rate never exceeds $r$.

</div>

<div class="pt-2 vsb-muted text-sm">

**Shaping** delays a non-conformant packet until tokens accumulate (Part 2's "shaping delay"); **policing** instead drops or marks it immediately, without adding delay.

</div>

<!--
This is the mechanism behind two things already introduced: Part 2's "shaping delay" bullet, and CAC's promise
on the previous slide — CAC can only reason about whether a new flow fits because admitted flows are held to a
token-bucket contract. Reused everywhere in QoS architectures: IntServ's traffic specs and DiffServ's edge
policers are both stated as (r, b) token-bucket parameters.
-->

---

# Queuing and scheduling — Weighted Fair Queuing

<img class="lecture-diagram" src="/figures/03/weighted-queues.svg" alt="Router R1 splits incoming packets between two output queues before one output link: queue 1 is scheduled 25 percent of link capacity, queue 2 the remaining 75 percent." />

<div class="pt-2">

Queuing tools create multiple queues; a **scheduling algorithm** decides which queue to serve next. **Weighted Fair Queuing (WFQ)** gives each queue a guaranteed minimum share — on a 1 Mbit/s link, the example above guarantees queue 1 at least 250 kbit/s and queue 2 at least 750 kbit/s.

</div>

<div class="pt-2 vsb-muted text-sm">

This is **proportional** scheduling, not strict priority — queue 1 is never starved, only rate-limited relative to queue 2.

</div>

<!--
Queuing/scheduling manages traffic already admitted and already enforced (contrast with CAC and the token
bucket on the previous two slides, which decide whether a flow is admitted and hold it to a contract). WFQ's
underlying intuition — approximate serving all queues "at once" by always advancing whichever queue is
furthest behind its guaranteed share — is more than this course needs formally; class-based WFQ (CBWFQ) is the
deployed variant. Strict priority queuing (used for voice, in Part 4) is a different discipline again.
-->

---

# Why not just drop-tail? Three failure modes

<div class="grid grid-cols-3 gap-6 pt-4 text-sm">
<div class="border border-gray-400 p-4">

**Lock-out**

A single flow's burst can fill the queue first and keep refilling it, leaving no room for any other flow's packets.

</div>
<div class="border border-gray-400 p-4">

**Full-queue bias**

Packets are dropped only once the buffer is completely full — every flow suffers the maximum possible queuing delay before anything is dropped.

</div>
<div class="border border-gray-400 p-4">

**Global synchronization**

Many TCP flows overflow the buffer at the same instant, all lose a packet together, and all back off and speed up in lockstep — causing periodic dips in link utilization.

</div>
</div>

<div class="pt-8 vsb-muted">

An **active queue management** scheme — dropping before the buffer fills, not after — can avoid all three.

</div>

<!--
This is the standard motivation for RED taught in networking courses: drop-tail is not just "less proactive"
than RED, it has three specific, nameable failure modes. Global synchronization is the one worth dwelling on —
it is a direct, visible consequence of many independent TCP flows all reacting to the same congestion event at
the same moment.
-->

---

# Congestion avoidance — Random Early Detection (RED)

<img class="lecture-diagram" src="/figures/03/red-drop-profile.svg" alt="RED drop probability as a function of average queue depth: zero below a minimum threshold, rising linearly to a maximum probability between the minimum and maximum thresholds, then tail drop above the maximum threshold." />

<div class="pt-2 text-sm">

RED discards some packets **before** a queue fills, with drop probability $p(\mathrm{avg})$ rising linearly between the two thresholds shown above. $\mathrm{avg}$ is a **smoothed average** queue size — a short burst passes untouched, but a sustained trend still triggers drops.

</div>

<div class="pt-1 vsb-muted text-sm">

An ECN-capable receiver (RFC 3168) can be **marked** instead of dropped — but this still relies on the sender responding to the signal.

</div>

<!--
Floyd & Jacobson, 1993. RED reduces the load entering the network before queues fill, spreading drops (and
therefore TCP backoffs) out over time instead of dropping a whole burst at once — solving all three failure
modes from the previous slide. The full piecewise definition is exactly the figure: 0 below min_th, linear up
to max_p between the thresholds, 1 (tail drop) at or above max_th — p(avg) = max_p*(avg-min_th)/(max_th-min_th).
ECN is mentioned here because the DSCP figure in Part 4 already shows a 2-bit ECN field — this is what it is
for. It does not change the next slide's RTP/UDP story: ECN still needs a responsive sender.
-->

---

# RED and real-time media don't mix well

<div class="pt-2">

RED's whole mechanism assumes the sender **responds** to a dropped packet by slowing down — true for TCP, **not** true for RTP over UDP.

</div>

<div class="pt-4 grid grid-cols-2 gap-6 text-sm">
<div class="border border-orange-400 p-4">

**A TCP flow hit by RED**

Loses a packet, halves its window, offers less load. RED's early warning does its job.

</div>
<div class="border border-orange-400 p-4">

**An RTP/UDP flow hit by RED**

Loses a packet — degraded audio or video, packet-loss concealment at best — and keeps sending at exactly the same rate. Nothing about the congestion improves.

</div>
</div>

<div class="pt-6 vsb-muted">

This is why real-time media additionally needs a **priority** discipline (a low-latency or strict-priority queue) rather than relying on RED alone — Part 4 revisits this once DSCP marking identifies which traffic that queue should protect.

</div>

<!--
This point is not in the original source material and is worth dwelling on — it is the single most important
practical nuance connecting congestion avoidance to the VoIP focus of Exercise 03. RTP's non-responsiveness is
exactly why VoIP deployments pair marking (Part 4) with strict priority queuing rather than trusting RED or
plain weighted queuing to protect call quality.
-->

---

# Checkpoint — who actually backs off?

<div class="checkpoint-question">

A congested router runs RED only, no priority queuing. A VoIP call and a large FTP transfer share the same queue. Whose packets get dropped, and does dropping either one relieve the congestion the way RED intends?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**RED drops from both flows in proportion to their share of the queue — it does not distinguish them.** The FTP's TCP stack backs off after a drop, relieving congestion exactly as RED intends. The VoIP call's RTP/UDP stream does not back off: its lost packets degrade the call without reducing its offered load at all. RED protects the network from responsive (TCP) flows; it does not protect a real-time flow from the network.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. Sets up the next slide's two
answers to this gap.
-->

---

# Fair Queuing vs. RED — two ways to protect a flow

<div class="grid grid-cols-2 gap-6 pt-4 text-sm">
<div class="border border-gray-400 p-4">

**(Weighted) Fair Queuing**

Separates flows into their own queues, so one flow's misbehavior cannot consume another's guaranteed share. Real **isolation** — at the cost of per-flow or per-class state and classification.

</div>
<div class="border border-gray-400 p-4">

**RED on a shared queue**

Needs no per-flow state — cheap to run at every hop. Provides **no isolation**: a non-adaptive flow is dropped at the same rate as everyone else and simply keeps going.

</div>
</div>

<div class="pt-8 vsb-muted">

This is why real-time media is usually placed in its **own** priority queue (Part 4's DSCP marking identifies which packets belong there), rather than trusting RED alone to protect it on a shared queue.

</div>

<!--
Direct trade-off, not a "which is better" question: WFQ (already introduced this Part) buys isolation at
implementation cost; RED buys cheap congestion signaling with no isolation. Deployed networks use both
together — WFQ/priority queuing across classes, RED (or tail drop) within each class's queue.
-->

---
layout: section
---

# Part 4
## Link efficiency and marking

---

# Compression and the cost of packet headers

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

Exercise 03's G.711 packet: 160 B payload plus 40 B of RTP + UDP + IP headers = 200 B, so headers alone are **20% overhead** — significant on a slow access link.

RTP header compression (cRTP, RFC 2508) exploits how little those header fields change packet to packet on a point-to-point link, compressing 40 B down to as little as 2–4 B.

</div>
<div v-click>

<div class="vsb-fill">

### 200 B → ≈162 B

overhead drops from 20% to about 1–2%

</div>

<div class="pt-4 text-sm vsb-muted">

Compression is not free: it costs CPU time at both ends of the link (the "compression delay" from Part 2's fixed-delay list) — a trade worth making exactly on the slow links where serialization delay already matters.

</div>

</div>
</div>

<!--
Answers the original source material's open discussion prompt ("compression ratio vs no compression?") with a
concrete number instead of leaving it open. cRTP mechanics and its failure modes are in Extras.
-->

---

# Link Fragmentation and Interleaving (LFI)

<img class="lecture-diagram" src="/figures/03/lfi-fragmentation.svg" alt="Without link fragmentation and interleaving, a small delay-sensitive packet waits behind an entire large packet already being sent. With fragmentation and interleaving, the large packet is split into fragments and the small packet is sent after just the first fragment." />

<div class="pt-2 text-sm">

Once a router starts sending a packet, it finishes it — a delay-sensitive packet arriving just after a large one has begun transmission must wait for the whole thing. LFI fragments the large packet and interleaves the small, urgent one between fragments.

</div>

<div class="pt-1 vsb-muted text-sm">

Standardized for multilink PPP (RFC 1990) and Frame Relay (FRF.12) — this bounds serialization delay's effect on someone else's queuing delay.

</div>

<!--
LFI matters specifically on slow links, the same regime where compression (previous slide) pays off — both
are link-efficiency mechanisms for constrained access circuits, not core/backbone concerns.
-->

---

# Classification and marking — Class of Service

<div class="pt-2">

Classification and marking tools do the (potentially expensive) work of classifying a packet **once**, then mark a field in its header so every later device can act on that mark cheaply.

</div>

<div class="pt-4">

At Layer 2, **CoS** (Class of Service) is carried in the 802.1Q tag's 3-bit User Priority field, defined by IEEE 802.1p — meaningful only between devices that share a VLAN trunk.

</div>

<!--
Deliberately brief — CoS is layer-2 and link-local; the IP-layer DSCP marking on the next slide is what survives
end-to-end and is what the rest of the network (and this course) generally cares about.
-->

---

# Classification and marking — IP Precedence and DSCP

<img class="lecture-diagram" src="/figures/03/dscp-header.svg" alt="The pre-DiffServ Type of Service byte splits into 3 bits of IP Precedence, 4 ToS bits, and 1 unused bit. The Differentiated Services field reuses the same byte as 6 bits of DSCP plus 2 bits of Explicit Congestion Notification." />

<div class="pt-2 text-sm">

RFC 2474/2475 redefine the same byte as **DSCP**, with standard per-hop behaviors (PHBs): **EF** for voice, **AF** for video, **CS0**/default for best-effort.

</div>

<div class="pt-2 vsb-muted text-sm">

Marking only **classifies** — it changes nothing until a scheduler (Part 3's priority queue) is configured to treat EF-marked traffic differently.

</div>

<!--
Ties Parts 3 and 4 together explicitly: marking (this slide) plus a configured priority/LLQ discipline
(Part 3) is the actual fix for the RED/RTP mismatch from the earlier checkpoint. Neither mechanism alone
protects a voice call under congestion.
-->

---

# Checkpoint — does marking alone help?

<div class="checkpoint-question">

An engineer marks all VoIP traffic DSCP EF, but the congested interface still uses plain FIFO queuing. Does the marking help?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Not by itself.** DSCP EF is a classification label; nothing enforces different treatment unless a scheduler is configured to read that label and act on it — for example, a low-latency queue that always serves EF-marked packets first. Marking and scheduling are two separate mechanisms that must be configured together, exactly as CAC and queuing are two separate decisions (admit vs. treat).

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. Closes the Part 3/Part 4 loop
before the Common mix-ups and summary slides restate it explicitly.
-->

---

# Common mix-ups

<div class="grid grid-cols-3 gap-4 pt-2 text-sm">
<div class="border border-orange-400 p-3">

**Marking vs. enforcing**

DSCP/CoS labels a packet. Only a configured scheduler changes how it is actually treated.

</div>
<div class="border border-orange-400 p-3">

**RED vs. tail drop**

RED drops early to warn TCP before the buffer is full. Tail drop happens once it is full — and can synchronize many flows' backoffs.

</div>
<div class="border border-orange-400 p-3">

**CAC vs. queuing**

CAC decides whether a flow is admitted **at all**. Queuing/scheduling manage flows already admitted.

</div>
<div class="border border-orange-400 p-3">

**Blocked vs. delayed vs. dropped**

CAC-rejected: never starts. Queued: delayed, not lost. RED/tail-dropped: discarded outright.

</div>
<div class="border border-orange-400 p-3">

**Shaping vs. policing**

Both enforce a token-bucket contract. Shaping **delays** non-conformant traffic; policing **drops or marks** it.

</div>
</div>

<!--
Five confusions seen most often when this material is discussed: (1) assuming a DSCP mark by itself changes
scheduling, (2) conflating RED's proactive drops with reactive tail drop, (3) treating admission control and
in-progress traffic management as the same decision, (4) blurring blocking, queuing delay, and packet loss —
three distinct QoS outcomes with three distinct causes, (5) treating shaping and policing as the same response
to the same token-bucket violation when they trade delay for loss differently.
-->

---

# Summary — seven mechanisms to keep straight

<div class="grid grid-cols-2 gap-x-10 gap-y-2 pt-2 text-sm">

<div>

**QoS ⇒ QoE, not the reverse**
Throughput, delay, jitter, and loss are necessary but not sufficient inputs to QoE.

**The delay budget**
Fixed (serialization + propagation + codec) plus variable (queuing + forwarding + shaping) — queuing is the one that blows up under load.

**CAC vs. enforcement vs. scheduling**
CAC admits or blocks a flow; the token bucket holds it to a rate/burst contract; WFQ isolates queues from each other.

**RED needs three failure modes to motivate it**
Drop-tail suffers lock-out, full-queue bias, and global synchronization — RED drops early and probabilistically to avoid all three.

</div>
<div>

**RED does not help real-time media**
Non-responsive UDP/RTP traffic needs priority/WFQ queuing instead — RED buys cheap signaling, not isolation.

**Shaping vs. policing**
Both enforce a token-bucket contract; shaping delays non-conformant traffic, policing drops or marks it.

**Link efficiency**
LFI bounds serialization delay on slow links; header compression removes fixed per-packet overhead.

**Marking needs a scheduler**
CoS/DSCP classify traffic; treatment changes only once a configured scheduler honors the marking.

</div>

</div>

<!--
Read them aloud, one sentence each. Then the exit questions.
-->

---

# Exit questions — use the ideas

1. A branch office's WAN link runs at 64 kbit/s. From this lecture's delay budget, which two components dominate, and how do they scale if the link is downgraded to 32 kbit/s?
2. Why is RED, by itself, an incomplete strategy for protecting a VoIP call sharing a link with bulk TCP downloads?
3. A packet arrives marked DSCP CS0 (best-effort). What, if anything, changes automatically about how a router queues it?
4. Contrast what happens to a call rejected by CAC, a packet delayed in a queue, and a packet dropped by RED.

<div v-click class="pt-5 vsb-muted">

**Explain the mechanism**, not just its name.

</div>

<!--
Allow two minutes for individual answers, then discuss. Answers: (1) Serialization (1600 bit/64 kbit/s = 25 ms
becomes 50 ms at 32 kbit/s) and, under load, queuing delay — both scale directly or worsen as capacity halves.
(2) RED only signals responsive (TCP) senders; RTP/UDP does not back off, so RED alone does not protect voice
quality — priority queuing is also needed. (3) Nothing automatically — CS0/default receives whatever the
interface's configured scheduling gives best-effort traffic, typically the least favorable share. (4) A
rejected call never starts (blocked, Erlang B); a queued packet arrives late (delayed, bounded by the queue);
a RED-dropped packet never arrives at all (lost) — three distinct QoS outcomes.
-->

---

# Exercise 03 — where these mechanisms meet measured QoE

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

This lecture explained **where** delay, jitter, and loss come from on a real network. Exercise 03 injects them **synthetically** and measures what a listener actually hears:

- Delay, jitter, loss ↔ `tc netem` parameters (Step 3)
- Header overhead and bit rate ↔ RTP/UDP/IP arithmetic (Question 2)
- The resulting audio ↔ PESQ and ViSQOL scoring (Steps 5–6)

</div>
<div>

<div class="text-sm">

Then the README questions connect network-layer causes (this lecture) to perceptual effects (the listening tests) — including whether *bursty* loss at the same average rate sounds worse than independent loss.

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
Exercise 03 does not hands-on practice CAC, queuing, or marking — those stay conceptual background from this
lecture. What it does practice is everything in Part 1's four QoS parameters and Part 2's delay budget,
injected directly with netem and scored with PESQ/ViSQOL.
-->

---

# References — foundations

- ITU-T Recommendation E.800, *Definitions of terms related to quality of service*, 2008.
- ITU-T Recommendation P.10/G.100 Amendment 5, *New definition of Quality of Experience*, 2017.
- L. U. Rehman Khan, K. Connelly, N. Crespi, "Toward total quality of experience: A QoE model in a communication ecosystem," *IEEE Communications Magazine*, 50(4), art. 6178834, 58–65, 2012.
- Qualinet, *Qualinet White Paper on Definitions of Quality of Experience*, European Network on Quality of Experience in Multimedia Systems and Services (COST Action IC 1003), 2013.
- ITU-T Recommendation G.114, *One-way transmission time*, 2003.
- S. Floyd, V. Jacobson, "Random Early Detection Gateways for Congestion Avoidance," *IEEE/ACM Transactions on Networking*, 1(4), 397–413, 1993.

<!--
Primary sources for the QoS/QoE definitions, the G.114 delay guidance, and RED. Further reading, not
prerequisites for Exercise 03.
-->

---

# References — standards and practice

- K. Nichols, S. Blake, F. Baker, D. Black, "Definition of the Differentiated Services Field (DS Field) in the IPv4 and IPv6 Headers," RFC 2474, 1998.
- S. Blake et al., "An Architecture for Differentiated Services," RFC 2475, 1998.
- B. Davie et al., "An Expedited Forwarding PHB," RFC 3246, 2002.
- J. Heinanen, F. Baker, W. Weiss, J. Wroclawski, "Assured Forwarding PHB Group," RFC 2597, 1999.
- K. Sklower, B. Lloyd, G. McGregor, D. Carr, T. Coradetti, "The PPP Multilink Protocol (MP)," RFC 1990, 1996.
- S. Casner, V. Jacobson, "Compressing IP/UDP/RTP Headers for Low-Speed Serial Links," RFC 2508, 1999.
- T. Szigeti, C. Hattingh, *End-to-End QoS Network Design*. Cisco Press, 2004.

<!--
The DiffServ/PHB RFCs and RFC 2508 back the marking and compression slides in Part 4; Szigeti & Hattingh is the
practitioner reference the original course material drew its Cisco-style content from.
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
## Header compression details and a QoS standards timeline

<!--
Not part of the timed 90-minute route. Use to answer questions or extend an advanced class.
-->

---

# Extras — how cRTP actually behaves

<div class="pt-2">

RFC 2508 compression runs **hop-by-hop** between one compressor/decompressor pair sharing per-flow context state — it only helps on that one link, not end-to-end.

</div>

<div class="pt-4 grid grid-cols-2 gap-6 text-sm">
<div class="border border-gray-400 p-4">

**Why it works**

Most IP/UDP/RTP header fields are static or change predictably packet to packet (sequence number and timestamp both increment by a fixed step) — only the small delta needs to be sent.

</div>
<div class="border border-gray-400 p-4">

**Why it can fail**

If the *link itself* loses a packet, the decompressor's context can desynchronize from the compressor's, corrupting every packet after it until a full header is resent.

</div>
</div>

<!--
Worth knowing before recommending cRTP: it trades bandwidth for a new failure mode on lossy links, and it is
only usable where compressor and decompressor are the two ends of one physical link (typically a slow serial
WAN link), not across an arbitrary IP path.
-->

---

# Extras — a QoS/DiffServ standards timeline

| Year | Standard | Contribution |
|---|---|---|
| 1981 | RFC 791 | The IPv4 header's Type of Service byte |
| 1994 | RFC 1633 | Integrated Services (IntServ) — per-flow reservations |
| 1998 | RFC 2474 / 2475 | Differentiated Services (DiffServ) — per-hop behaviors, not per-flow state |
| 1999 | RFC 2597 | Assured Forwarding (AF) PHB group |
| 2002 | RFC 3246 | Expedited Forwarding (EF) PHB |
| 2003 | ITU-T G.114 | One-way delay guidance for conversational quality |

<div class="pt-4 text-sm vsb-muted">

DiffServ won out over IntServ for wide deployment because it needs no per-flow state in core routers — a PHB is a property of a marking, not of a reservation that must be signaled and maintained hop by hop.

</div>

<!--
Optional history. IntServ (RSVP-based, per-flow reservations) does not scale to backbone router flow counts;
DiffServ's insight — push classification to the edge, keep the core stateless — is why DSCP marking (Part 4)
is the mechanism still in use today.
-->
