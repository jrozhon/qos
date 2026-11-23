---
theme: seriph
title: 08 · QoS architectures in IP networks
info: |
  440-2216/01 Quality of Service — lecture 8.
  How quality of service is built end to end across many routers and two operators' domains: Integrated Services
  with RSVP (per-flow reservations, admission control, soft state), Differentiated Services (DSCP marking and
  conditioning at the edge, per-hop behaviours and class schedulers in the core), and the trade-off between
  guarantees and scalability that separates them. Builds on the mechanisms of Lecture 03.
exportFilename: 08-qos-architectures
layout: cover
transition: slide-left
mdc: true
lineNumbers: true
fonts:
  provider: none
  sans: Carlito
  mono: IBM Plex Mono
---

# QoS Architectures in IP Networks

### 440-2216/01 Quality of Service · Lecture 08

<div class="pt-6 text-sm vsb-muted">
Jan Rozhon, Miroslav Vozňák &middot; Department of Telecommunications, FEECS
</div>

<!--
Ninety minutes including checkpoints and two live demos: 8 min opening and Part 1 (why an architecture, not just
mechanisms), 25 min Part 2 (IntServ and RSVP, live RSVP demo), 32 min Part 3 (DiffServ: conditioning, DSCP, PHBs,
schedulers, live DiffServ demo), 15 min Part 4 (IntServ vs DiffServ side by side, DSCP in the real Internet),
10 min common mix-ups, summary, exit questions and lab pointers. Lecture 03 introduced the mechanisms one router
can run — admission control, the token bucket, WFQ, RED, the DSCP byte. This lecture asks how those mechanisms are
made to work together along a whole path and across operators, and what it costs to keep the state that a
guarantee needs. Lecture 09 then shows the same marking and metering done by an OpenFlow switch.
-->

---

# Where we are going

<div class="grid grid-cols-4 gap-4 pt-4 text-sm">

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 1</div>

### Why architecture

From mechanisms in one box to quality along a whole path

<div class="text-xs opacity-60 pt-2">↔ Lecture 03, Parts 3–4</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 2</div>

### IntServ and RSVP

Per-flow reservations, admission at every hop, soft state

<div class="text-xs opacity-60 pt-2">↔ Lecture 03: CAC, token bucket</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 3</div>

### DiffServ

Marking at the edge, per-hop behaviours and schedulers in the core

<div class="text-xs opacity-60 pt-2">↔ Lecture 03: DSCP, WFQ, RED</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 4</div>

### IntServ vs DiffServ

State and scale side by side; DSCP in the real Internet

<div class="text-xs opacity-60 pt-2">↔ Lecture 03 Extras · → Lecture 09</div>
</div>

</div>

<div class="pt-6">

One question runs through the lecture: **where does the network keep the state that a guarantee needs, and how much of it can it afford?**

</div>

<!--
The "↔" lines replace the lab steps of other decks: this lecture has no lab of its own, it extends Lecture 03.
Each part names the Lecture 03 mechanism it builds on, so students can look back at the one-box version.
Part 4 ends with a pointer to Lecture 09, where an OpenFlow switch meters and re-marks DSCP.
-->

---

# What you should be able to do

1. Explain why quality of service along a path needs an architecture that every hop and every domain follows, not just mechanisms in one router.
2. Describe the IntServ model — its four router functions, the Guaranteed and Controlled-Load services, TSpec and RSpec — and compute a Guaranteed-service delay bound.
3. Trace RSVP signalling hop by hop: PATH and RESV, admission and policy control, errors, soft-state refresh, reservation styles.
4. Describe DiffServ: traffic conditioning at the edge, the DSCP codepoints, and the EF, AF, CS and LE per-hop behaviours with the schedulers that realise them.
5. Compare IntServ and DiffServ in state, signalling, kind of guarantee and scale, and explain what happens to DSCP at a domain boundary.

<div class="pt-4 vsb-muted">

Keep asking: **which router keeps state about this packet, and for how many flows?**

</div>

<!--
Five outcomes. Prerequisites: Lecture 03's token bucket, WFQ, RED/ECN, CAC and the DSCP byte; Lecture 02's
queueing delay. The only new mathematics is the Guaranteed-service delay bound, used in its simple fluid form
with one worked example; the full RFC 2212 formula is in Extras.
-->

---
layout: statement
---

# Guarantee needs state; scale forbids state

## IntServ and DiffServ are the two ends of that trade-off

<!--
This is the thesis of the lecture. A hard guarantee for one flow means every router on the path must know that
flow, its contract and its reservation — per-flow state. A core router carrying hundreds of thousands of flows
cannot afford that state, so DiffServ keeps only a handful of classes in the core and gives up the per-flow
guarantee. Every slide that follows sits somewhere on this line; Part 4 puts the two ends side by side.
-->

---
layout: section
---

# Part 1
## Why architecture, not just mechanisms

---

# Lecture 03's toolbox — mechanisms in one box

<div class="grid grid-cols-5 gap-3 pt-2 text-sm">
<div class="border border-gray-400 p-3">

**CAC**

admit or block a new flow

</div>
<div class="border border-gray-400 p-3">

**Token bucket**

hold a flow to rate $r$ and burst $b$

</div>
<div class="border border-gray-400 p-3">

**WFQ**

guarantee each queue a share

</div>
<div class="border border-gray-400 p-3">

**RED / ECN**

drop or mark before the queue fills

</div>
<div class="border border-gray-400 p-3">

**DSCP**

label a packet once, act on it later

</div>
</div>

<div class="pt-6">

Each of them works **inside one router**, on one output link. A voice call crosses ten or twenty routers, often in two or three operators' networks.

</div>

<div class="pt-2 vsb-muted">

This lecture is about the **architecture** that makes these mechanisms work end to end: who decides what a flow gets, how every router on the path learns it, and how much each router must remember.

</div>

<!--
Recap of Lecture 03 Parts 3–4 in one slide — do not re-teach them; point back at the figures there if the room
has forgotten. The new question is coordination: Lecture 03's CAC asked "is there room on this link?", IntServ
asks it on every link of the path; Lecture 03's DSCP labelled a packet, DiffServ defines what every router must do
with the label.
-->

---

# Best effort by default — two answers since the 1990s

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**Reserve per flow — Integrated Services**

The application asks for a guarantee; every router on the path checks capacity, reserves it and remembers the flow. RFC 1633 (1994), signalled by RSVP (RFC 2205).

*Absolute* guarantee · state per flow in every router

</div>
<div class="border border-gray-400 p-4">

**Treat per class — Differentiated Services**

The edge sorts packets into a few classes and writes the class into the DSCP; the core treats each class, not each flow. RFC 2474 / 2475 (1998).

*Relative* treatment · state per class in the core

</div>
</div>

<div class="pt-6">

The Internet's default stays **best effort**: one FIFO queue per link, no promises. Both architectures are ways of leaving it for traffic that cannot tolerate it.

</div>

<!--
The two answers came from the same community a few years apart (Clark, Shenker & Zhang's SIGCOMM 1992 paper
argued for real-time service classes; IntServ followed; DiffServ was the reaction once RSVP's scaling cost was
clear). "Absolute" vs "relative" returns in Part 4's comparison table.
-->

---

# From RFC 1633 to L4S

<Figure src="/figures/08/timeline.svg" alt="A timeline from 1994 to 2023. Above the axis, Integrated Services: RFC 1633 architecture 1994, RFC 2205 RSVP 1997, RFC 2998 IntServ over DiffServ 2000, RFC 3209 RSVP-TE for MPLS 2001. Below it, Differentiated Services: RFC 2474 and 2475 in 1998, RFC 2597 AF in 1999, RFC 3246 EF in 2002, RFC 4594 service classes in 2006, RFC 8622 LE in 2019, RFC 9330 to 9332 L4S in 2023." />

<div class="pt-1 text-sm vsb-muted">

Lecture 03's Extras listed the first DiffServ RFCs; here is the whole line, including where RSVP went after IntServ.

</div>

<!--
This extends the timeline table in Lecture 03's Extras. IntServ came first and was largely finished by 1997; the
DiffServ line keeps growing to this day — RFC 8622 (Lower Effort, 2019) and L4S (RFC 9330–9332, 2023), which
builds on Lecture 03's ECN. RSVP-TE (2001) is where RSVP lives on; it returns at the end of Part 2.
-->

---

# Checkpoint — one router at a time?

<div class="checkpoint-question">

Why can't each router just do its own QoS — every operator configures priority queues on the routers it likes, and the rest stay as they are?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**A path is only as good as its worst hop.** One congested router with a plain FIFO queue adds queuing delay and loss that no other router can undo — all network elements on the path must take part. And they must **agree**: which packets deserve what, and how much of each link is already promised. That agreement is the architecture.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. The original course slide put it as
"all network elements need to be capable". Lecture 03's delay budget is additive, so one bad hop is enough. The
two halves of the answer foreshadow the two architectures: IntServ makes routers agree by signalling per flow,
DiffServ by a shared meaning of the DSCP.
-->

---
layout: section
---

# Part 2
## Integrated Services and RSVP

---

# The IntServ model — four functions in every router

<Figure src="/figures/08/intserv-router.svg" alt="An IntServ router split into a control plane and a data plane. In the control plane the RSVP agent receives PATH and RESV messages, asks admission control whether enough capacity is left, and writes admitted reservations into the traffic control database. In the data plane a classifier maps arriving packets to flows using filters from that database, and a packet scheduler serves per-flow queues and a best-effort queue at the reserved rates on the output link." />

<div class="pt-1 text-sm">

RFC 1633 names them: **reservation set-up**, **admission control**, **classifier**, **packet scheduler**. The control plane decides once per flow; the data plane applies the decision to every packet.

</div>

<!--
Redrawn from the original course slide. Admission control is Lecture 03's CAC, now run per link at every hop;
the packet scheduler is Lecture 03's WFQ with one queue per reserved flow. RSVP also runs policy control (is this
user allowed to reserve?) next to admission control — that is what refuses the reservation at E3 in the live
demo later. The point to stress: the classifier filter and the queue exist per flow, in every router.
-->

---

# Three service classes

<div class="grid grid-cols-3 gap-4 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**Guaranteed service** · RFC 2212

A firm, mathematically provable upper bound on queuing delay, and no queuing loss for traffic that conforms to its contract.

*For:* playback applications with a fixed delay budget — interactive voice.

</div>
<div class="border border-gray-400 p-4">

**Controlled-Load** · RFC 2211

No numeric bound: the flow is served as best effort would serve it **on an unloaded network** — little queuing, very little loss.

*For:* adaptive applications that tolerate some variation — streaming.

</div>
<div class="border border-gray-400 p-4">

**Best effort**

No reservation, no admission control. Everything that did not ask, or was refused, ends up here.

*For:* elastic traffic — web, e-mail, file transfer.

</div>
</div>

<div class="pt-6 vsb-muted">

Both reserved services need the flow to describe itself first — with the token bucket of Lecture 03.

</div>

<!--
RFC 2212 (Shenker, Partridge, Guérin, 1997) and RFC 2211 (Wroclawski, 1997). Controlled-Load is the more
pragmatic of the two: it promises a behaviour, not a number, so a router can admit with a looser, measurement-based
test. A refused flow is not dropped — it is carried as best effort; the live demo shows this in grey.
-->

---

# TSpec and RSpec — the token bucket as a contract

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div>

**TSpec** — what the sender will send (RFC 2210, 2212)

- token bucket rate $r$ and depth $b$
- peak rate $p$
- minimum policed unit $m$, maximum packet size $M$

Over any interval $T$ the flow sends at most

$$M + \min(pT,\ rT + b - M)$$

</div>
<div>

**RSpec** — what the receiver asks for (Guaranteed service)

- reserved rate $R \ge r$
- slack term $S$: delay the application could spare

**FlowSpec** = TSpec + RSpec; it is what each router admits or refuses.

</div>
</div>

<div class="pt-6 vsb-muted">

Lecture 03's token bucket bound $b + rT$ is the same contract without the peak rate: $(r, b)$ describe the flow, $R$ is what the network sets aside for it.

</div>

<!--
Lecture 03 introduced the bucket as an enforcement tool; here it becomes the language a flow uses to describe
itself to the network. m exists so that tiny packets are counted as if they were m bytes (header overhead), M so
that a router can size its buffers. The slack term S lets a router reserve less than R if the application's delay
budget allows it; it is not used in the example on the next slide.
-->

---

# Guaranteed service — a delay bound you can compute

<div class="grid grid-cols-2 gap-8 pt-2">
<div class="text-sm">

Fluid bound (RFC 2212 with $p \to \infty$), $C_i$ and $D_i$ the error terms of hop $i$:

$$D \le \frac{b}{R} + \frac{C_{\mathrm{tot}}}{R} + D_{\mathrm{tot}}$$

A voice aggregate: $b = 80$ kbit, $R = 2$ Mbit/s, 4 hops, each with $C_i = 12$ kbit (one 1500-byte packet) and $D_i = 0.12$ ms (1500 B at 100 Mbit/s).

</div>
<div v-click>

<div class="vsb-fill">

### $D \le 40 + 24 + 0.48 \approx 64.5$ ms

whatever the other traffic on the path does

</div>

<div class="pt-4 text-sm vsb-muted">

The burst term $b/R$ dominates: reserve more rate and the bound shrinks. This is Parekh and Gallager's result for WFQ — a token-bucket flow with a guaranteed rate has bounded delay.

</div>

</div>
</div>

<!--
b/R = 80 kbit / 2 Mbit/s = 40 ms; C_tot/R = 4 × 12 kbit / 2 Mbit/s = 24 ms; D_tot = 4 × 0.12 ms = 0.48 ms.
C is the rate-dependent error (a hop may hold up to one packet before WFQ catches up, so it is divided by R),
D the rate-independent one (here one packet's serialization at 100 Mbit/s). The bound is shown, not derived;
Parekh & Gallager (IEEE/ACM ToN 1993) proved it for GPS/WFQ. The full RFC 2212 bound with the peak rate p is in
Extras. Compare Lecture 03's VoIP budget of 57.5 ms: that was an estimate, this is a guarantee.
-->

---

# RSVP — the signalling that sets reservations up

<div class="rsvp-fig">
<Figure src="/figures/08/rsvp-messages.svg" alt="A sequence diagram with sender, router R1, router R2 and receiver. PATH carrying the sender TSpec travels hop by hop to the receiver, each router storing the previous hop. The receiver answers with RESV carrying the flowspec, which travels back along the stored previous hops; R2 and then R1 run admission control and reserve. Thirty seconds later PATH and RESV are refreshed hop by hop; a PathTear removes the state along the path at once. Without refreshes the state expires after about 157 seconds." />
</div>

<div class="text-sm">

**Receiver-initiated**: PATH tells the receiver what the sender offers; the receiver decides what to reserve.

</div>

<style>
.rsvp-fig .lecture-diagram { height: 360px; }
</style>

<!--
RFC 2205 (Braden et al., 1997); the design is in Zhang, Deering, Estrin, Shenker & Zappala, IEEE Network 1993.
PATH runs downstream along the route the data will take and leaves previous-hop (PHOP) state in every router;
RESV follows those PHOPs back upstream, so it takes exactly the reverse of the data path even if routing is
asymmetric. Receiver-initiated because in multicast only the receivers know what they can use. Reservations are
simplex: a two-way call needs two of them.
-->

---

# RSVP messages

<div class="text-sm">

| Message | Direction | Carries / does |
|---|---|---|
| **PATH** | sender → receiver | sender TSpec; every hop stores the previous hop (PHOP) |
| **RESV** | receiver → sender, hop by hop | FlowSpec (TSpec + RSpec); admission and policy control at every hop |
| **ResvErr** | towards the receiver | a hop refused the reservation (capacity or policy) |
| **PathErr** | towards the sender | the PATH could not be processed |
| **PathTear** / **ResvTear** | down / upstream | remove the state at once, without waiting for it to expire |

</div>

<div class="pt-4 vsb-muted">

RSVP is **not a routing protocol**: it follows the routes that unicast or multicast routing already chose, and reserves along them.

</div>

<!--
RFC 2205 §3. ResvConf (optional confirmation to the receiver) is left out. Admission control answers "is there
capacity?", policy control "is this user allowed?"; either can produce a ResvErr. When a ResvErr arrives the flow
is not torn down — its packets travel as best effort. The live demo shows both refusal reasons.
-->

---

# Soft state — reservations that expire unless refreshed

<div class="grid grid-cols-2 gap-8 pt-2">
<div class="text-sm">

Senders repeat PATH and receivers repeat RESV every refresh period $R = 30$ s (default, randomised). A router keeps state for

$$L \ge (K + 0.5) \cdot 1.5 \cdot R$$

where $K = 3$ refreshes may be lost: $L \approx 157$ s.

</div>
<div class="text-sm">

**Why soft state**: a route change, a rebooted router or a vanished receiver needs no explicit repair. New refreshes build state on the new path; state nobody refreshes ages out.

**Teardown** messages only speed this up — the bandwidth comes back at once instead of after $L$.

</div>
</div>

<div class="pt-6 vsb-muted">

The price: every reservation costs refresh messages for as long as it lives — in every router on the path.

</div>

<!--
RFC 2205 §3.7: the refresh period is randomised in [0.5 R, 1.5 R] to avoid synchronisation, hence the 1.5;
(3 + 0.5) × 1.5 × 30 s = 157.5 s. The live demo's "refresh off" expires state after 3 missed refreshes — a
simplification it states on screen. The last line sets up the scaling argument after the demo.
-->

---

# Reservation styles and merging

<div class="text-sm">

| Style | Reservation | Senders | Use |
|---|---|---|---|
| **FF** — Fixed Filter | distinct per sender | explicit list | video from each speaker |
| **SE** — Shared Explicit | one, shared | explicit list | an audio conference: few speak at once |
| **WF** — Wildcard Filter | one, shared | any sender | as SE, without naming the senders |

</div>

<div class="pt-4 text-sm">

With multicast, RESVs from many receivers **merge** on the way up: a router forwards upstream only the largest request, so a sender's link carries one reservation, not one per receiver.

</div>

<!--
RFC 2205 §1.3. Two attributes — distinct vs shared reservation, explicit vs wildcard sender selection — give
three defined styles (distinct + wildcard is not defined). Shared styles exist because in a conference only one
or two people talk at a time, so reserving for every sender would waste capacity. Merging is why RSVP is
receiver-initiated. The live demo is unicast, one sender, FF style.
-->

---

# Checkpoint — a reboot mid-call

<div class="checkpoint-question">

A core router on the path reboots in the middle of a reserved call. What happens to the reservation — and who repairs it?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Nobody repairs it explicitly.** The router comes back with empty tables, so the call's packets cross it as best effort. The next PATH refresh rebuilds the path state, the next RESV refresh runs admission again and reinstalls the reservation — within one refresh period. Soft state needs no repair protocol (and if capacity has meanwhile gone to others, the RESV is refused).

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. The other routers keep their state
— their timers have not expired. The parenthesis is the honest catch: re-admission is a new admission decision.
The next slide's "fail C1" button shows exactly this.
-->

---

# Live — RSVP across two domains

<QosPathSim mode="rsvp" :capacity-a="6" :capacity-b="10" :initial-flows="0" />

<!--
Domain A's bottleneck C1→C2 is 6 Mbit/s, Domain B's C3→E4 10 Mbit/s, so refusals come from C1 (the RESV reaches
B's bottleneck first; with equal capacities B would refuse first). Refresh every 3 s stands for the real 30 s.
Demo script (seed 1, after Reset):
1. Press Play (nothing moves while paused), then "+1 flow" seven times, one at a time, narrating PATH down,
   RESV up. Flows 1–3 and 6 (video, voice,
   video, voice) are reserved — 4.2 Mbit/s on C1→C2; flows 4–5 are data and signal nothing (best effort);
   flow 7 is a video that needs 2 Mbit/s more: C1 flashes "ResvErr: capacity", the ResvErr runs to R and the
   flow becomes best effort (grey). Point at the state panels: all seven routers hold rows for every flow.
   Domain B's bar shows 6.2: the RESV was admitted in B before C1 refused it, and that orphaned reservation
   stays until it times out — ask the room why.
2. Switch refresh off: the age bars fade and the state expires after 3 missed refreshes ("simplified" on screen;
   the RFC's lifetime is ≈ 157 s). The bandwidth bar empties.
3. Refresh back on, tick "B refuses foreign reservations", add a flow: E3 refuses with "policy" — Domain B has no
   contract with A's customer. This is why inter-domain IntServ never happened (Huston, RFC 2990). Untick it.
4. With a few flows reserved and refresh on, press "fail C1": C1's table is empty, the flows cross it as best
   effort, and the next refresh rebuilds it — the checkpoint answer, live.
The PDF shows a fixed frame: 2 voice + 5 video, the 5th video refused at C1.
-->

---

# Why IntServ did not scale

<div class="grid grid-cols-2 gap-4 pt-2 text-sm">
<div class="border border-orange-400 p-3">

**State ∝ flows** — every router on the path keeps PATH and RESV state, a filter and a queue for every flow.

</div>
<div class="border border-orange-400 p-3">

**Refreshes ∝ flows** — two refresh messages per flow every 30 s, processed in software in every router.

</div>
<div class="border border-orange-400 p-3">

**Per-flow classification** — every packet is looked up among all reserved flows, at line rate.

</div>
<div class="border border-orange-400 p-3">

**Policy and billing** — who may reserve across another operator's network, and who pays? No inter-domain answer.

</div>
</div>

<div class="pt-6 vsb-muted">

None of these is a problem in a campus network with a hundred calls. All of them are in a core router with a hundred thousand.

</div>

<!--
The first three are technical and grow with the number of flows; the fourth is organisational and is the one
the live demo's "B refuses foreign reservations" toggle shows. Huston's RFC 2990 (2000) and Bell's "Failure to
thrive" (2003) are the critical accounts, cited in Part 4.
-->

---

# Worked example — 100 000 flows through one core router

<div class="grid grid-cols-2 gap-8 pt-2">
<div class="text-sm">

A core router carries 100 000 reserved flows; each one refreshes a PATH and a RESV every 30 s.

- refreshes: $2 \cdot 10^5 / 30 \approx 6\,700$ messages per second
- state at a few hundred bytes per flow (illustrative): tens of MB
- classification: every packet matched against 100 000 entries

</div>
<div v-click>

<div class="vsb-fill">

### ≈ 6 700 messages/s

just to keep standing still

</div>

<div class="pt-4 text-sm vsb-muted">

RFC 2961 (2000) cuts the messages — **bundles**, **message IDs** so unchanged state is not reprocessed, **summary refresh** — but not the per-flow state.

</div>

</div>
</div>

<!--
2 × 100 000 / 30 s = 6 667 refresh messages per second, before any new call is set up; each needs a lookup and
a timer update. The per-flow byte count is illustrative: a few hundred bytes for PATH state, RESV state, filter
and scheduler entry give 20–50 MB — small for a server, large for a line card's fast memory, which also has to
hold the classifier. Part 4's side-by-side slide counts the same quantities live.
-->

---

# Where RSVP lives on

<div class="grid grid-cols-3 gap-4 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**RSVP-TE** · RFC 3209

Reserves bandwidth for MPLS label-switched paths. One LSP carries many flows, so a core keeps thousands of reservations, not millions.

</div>
<div class="border border-gray-400 p-4">

**IntServ over DiffServ** · RFC 2998

RSVP at the edges for per-flow admission; the core forwards the admitted traffic as a DiffServ class.

</div>
<div class="border border-gray-400 p-4">

**Voice-Admit** · RFC 5865

DSCP 44 marks voice that passed admission control, so the core can tell it from unadmitted EF traffic.

</div>
</div>

<div class="pt-6 vsb-muted">

The lesson kept: signal and admit **at the edge or per aggregate**, never per flow in the core.

</div>

<!--
RSVP-TE is the main deployed descendant: operators use it for MPLS traffic engineering and fast reroute — note
that RSVP is the signalling and IntServ the service model; RSVP-TE uses the first without the second (a common
mix-up at the end of the lecture). RFC 2998 is the bridge to Part 3: aggregates in the core are exactly what
DiffServ provides. Voice-Admit returns in the DSCP table of Part 3.
-->
