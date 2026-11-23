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

Fluid bound (RFC 2212 with $p \to \infty$); $C_i$, $D_i$ are the error terms of hop $i$, $C_{\mathrm{tot}} = \sum C_i$, $D_{\mathrm{tot}} = \sum D_i$:

$$D \le \frac{b}{R} + \frac{C_{\mathrm{tot}}}{R} + D_{\mathrm{tot}}$$

A voice trunk: $b = 80$ kbit, $R = 2$ Mbit/s, 4 hops, each with $C_i = 12\,\mathrm{kbit}$ (one 1500-byte packet) and $D_i = 0.12\,\mathrm{ms}$ (1500 B at 100 Mbit/s).

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
Extras. This bounds queuing delay only: compare it with the queuing component of Lecture 03's VoIP budget
(5 ms lightly loaded, 100 ms on a busy link) — that was an estimate, this is a guarantee. Codec,
serialization and propagation delay still add on top, as in Lecture 03's 57.5 ms total.
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

PATH and RESV are refreshed hop by hop, each router on its own timer, every $R = 30$ s (default, randomised). A router keeps state for

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
   flow becomes best effort (grey). Point at the state panels: all seven routers hold rows for every flow
   that signalled. Domain B's bar briefly shows 6.2: the RESV was admitted in B before C1 refused it; then the
   ResvErr travels downstream and releases B's share, so the bar drops back to 4.2. (Real RSVP leaves this to
   the receiver, whose refreshes keep the downstream state — RFC 2205's blockade state.)
2. Switch refresh off: the age bars fade and the state expires after 3 missed refreshes ("simplified" on screen;
   the RFC's lifetime is ≈ 157 s). The bandwidth bar empties. Expired is final: the endpoints gave up, so these
   flows do not re-signal when refresh comes back — nothing is reserved any more.
3. Refresh back on, tick "B refuses foreign reservations", add a flow (after exactly seven clicks in step 1 it is a
   video; if the new flow is data, add another): E3 refuses with "policy" — Domain B has no contract with A's
   customer. This is why inter-domain IntServ never happened (Huston, RFC 2990). Untick it.
4. Add a few flows first (with seed 1, the next five are voice, data, voice, voice, voice: four reservations,
   0.4 Mbit/s on C1→C2), then press "fail C1": C1's table is empty. Until the next refresh C1 has no reservation
   for them — a real router would forward them as best effort; the drawing keeps their colour. The next refresh
   rebuilds it (2.5 s here) — the checkpoint answer, live.
The PDF shows a fixed frame with its own scenario, not these props: A = 10, B = 20 Mbit/s, 2 voice + 5 video,
the 5th video refused at C1.
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

RFC 2961 (2001) cuts the messages — **bundles**, **message IDs** so unchanged state is not reprocessed, **summary refresh** — but not the per-flow state.

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

---
layout: section
---

# Part 3
## Differentiated Services

---

# DiffServ — domains, edges and aggregates

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div>

A **DS domain** (RFC 2475) is a set of routers under one operator that agree on one set of per-hop behaviours.

- **Boundary nodes** classify, meter and condition the traffic that enters the domain — per customer or per flow.
- **Interior nodes** read only the DSCP. All packets with one codepoint form a **behaviour aggregate** and get the same **per-hop behaviour** (PHB).

</div>
<div>

Between two domains sits a **service level agreement** (SLA) and its **traffic conditioning agreement** (TCA): which codepoints are carried, at what rates, and what happens to the excess.

The origin is Nichols, Jacobson and Zhang's **"two-bit" architecture** (RFC 2638): a *premium* bit for shaped, strictly served traffic and an *assured* bit for traffic in or out of its profile.

</div>
</div>

<div class="pt-6 vsb-muted">

Lecture 03 showed the byte: 6-bit DSCP + 2-bit ECN (RFC 2474, RFC 3168). This part is about what every router does with it.

</div>

<!--
Serves outcome 4. RFC 2475 (Blake et al., 1998) is the architecture, RFC 2474 the field. The two-bit memo
(RFC 2638, 1999, first circulated as a draft in 1997) is where the two big PHBs come from: premium became EF,
assured became AF. The key contrast with Part 2: per-flow work moves to the boundary, where a router sees a few
customers, and the interior keeps a handful of aggregates. The live demo later has two domains, A and B, with E1
and E3 as their boundary nodes.
-->

---

# The traffic conditioner — at the edge only

<Figure src="/figures/08/tcb.svg" alt="A traffic conditioner at the edge of a DiffServ domain. Packets pass a classifier that looks at addresses, ports and DSCP, then a meter with one or two token buckets that decides whether each packet is in or out of profile, then a marker that sets or re-marks the DSCP, for example AF11 to AF12, and a shaper or dropper that delays or discards the excess. The packets then go to a core router, which only reads the DSCP and applies its per-hop behaviour, with no metering and no per-flow state." />

<div class="text-sm">

**BA classifier**: on the DSCP alone (trusted neighbours). **MF classifier**: on several fields — addresses, ports, protocol (customer edge).

</div>

<!--
Serves outcome 4; redrawn from the original course slides 8–9. Each block is a Lecture 03 mechanism: the meter
is the token bucket, the shaper delays and the dropper polices (Lecture 03's shaping vs policing mix-up), and the
marker writes the result into the DSCP so that no later router has to meter again. BA = behaviour aggregate,
MF = multi-field (RFC 2475 §2.3). All per-customer state lives here; the core router on the right keeps none.
-->

---

# Meters — two buckets instead of one

<Figure src="/figures/08/trtcm.svg" alt="The two-rate three-colour marker. Bucket P fills at the peak rate PIR up to PBS, bucket C at the committed rate CIR up to CBS. For a packet of B bytes the marker first asks whether bucket P holds fewer than B tokens: if so the packet is red and becomes AFx3, high drop precedence. Otherwise it asks whether bucket C holds fewer than B tokens: if so the packet is yellow, becomes AFx2, and only bucket P is debited. Otherwise it is green, becomes AFx1, and both buckets are debited. A legend explains CIR and PIR (committed and peak information rate), CBS and PBS (committed and peak burst size), Tc and Tp (tokens in buckets C and P), B (packet size) and AFxy (AF class x, drop precedence y)." />

<div class="text-sm">

**srTCM** (RFC 2697): one rate CIR, two bursts CBS and EBS (excess burst size) — excess **burst** turns yellow. **trTCM** (RFC 2698): CIR/CBS and PIR/PBS — excess **rate** turns yellow, above PIR red.

</div>

<!--
Serves outcome 4. Lecture 03's token bucket answered yes/no; a three-colour marker answers green/yellow/red, and
the marker turns the colour into the AF drop precedence. Both RFCs are by Heinanen and Guérin (1999). Colour-blind
mode, shown here, ignores any colour the packet already carries; colour-aware mode lets an upstream marking only
get worse, never better. The live demo meters video with CIR 6 and PIR 8 Mbit/s.
-->

---

# Worked example — a video aggregate through a trTCM

<div class="grid grid-cols-2 gap-8 pt-2">
<div class="text-sm">

A customer's video aggregate is metered with CIR = 6 Mbit/s, PIR = 8 Mbit/s and CBS = PBS = 0.3 Mbit, both buckets full. It sends a steady 10 Mbit/s for $T = 1$ s.

- bucket P lets through $\mathrm{PBS} + \mathrm{PIR} \cdot T = 8.3$ Mbit
- bucket C lets through $\mathrm{CBS} + \mathrm{CIR} \cdot T = 6.3$ Mbit

</div>
<div v-click>

<div class="vsb-fill">

### 6.3 green · 2 yellow · 1.7 red Mbit

AF41 · AF42 · AF43

</div>

<div class="pt-4 text-sm vsb-muted">

The buckets absorb the first 0.3 Mbit of the burst; after that, everything above CIR is yellow and everything above PIR red. Under congestion the core drops AF43 first.

</div>

</div>
</div>

<!--
Serves outcome 4. Green = what passes both buckets = CBS + CIR·T = 6.3 Mbit. Yellow = what P allows minus what
C allows = 8.3 − 6.3 = 2 Mbit. Red = 10 − 8.3 = 1.7 Mbit. They add up to the 10 Mbit sent. Over a long burst
the bucket sizes stop mattering: green 6, yellow 2, red 2 per second. Nothing is dropped here — the meter only
colours; drops happen later, in a congested AF queue (WRED, a few slides on). Exit question 4 is the same
calculation without the buckets.
-->

---

# The DSCP codepoint space

<Figure src="/figures/08/dscp-table.svg" alt="Table of DiffServ code points. EF is 46 and VOICE-ADMIT 44. The Assured Forwarding grid has four classes and three drop precedences: AF41, 42, 43 are 34, 36, 38; AF31 to AF33 are 26, 28, 30; AF21 to AF23 are 18, 20, 22; AF11 to AF13 are 10, 12, 14. Default best effort is 0. The class selectors CS7 to CS0 are 56, 48, 40, 32, 24, 16, 8 and 0, and LE is 1. CSn equals 8n and keeps the IP Precedence order; LE sits below best effort. A legend spells out EF (Expedited Forwarding, low delay and jitter), VOICE-ADMIT (EF for CAC-admitted voice), AFxy (Assured Forwarding, class x, drop precedence y, value 8x + 2y), CSn (Class Selector), LE (Lower Effort) and Default (best effort)." />

<!--
Serves outcome 4; replaces the old raster table of the original course slides. RFC 2474 split the 64 codepoints
into pools: xxxxx0 for standards, xxxx11 and xxxx01 for experimental and local use (RFC 8436 later opened the
last pool to standards, which is how LE got 000001). VOICE-ADMIT 44 (RFC 5865) is the admitted-voice codepoint
from Part 2. Lecture 05's voice is EF; Lecture 07's streaming is AF3x.
-->

---

# Exercise — decode a ToS byte

<div class="grid grid-cols-2 gap-8 pt-2">
<div class="text-sm">

`tcpdump -v` prints a video call's IPv4 header with **`tos 0x88`** — the old name of the DS byte.

Which DSCP is it, which per-hop behaviour does it ask for, and is the packet ECN-capable?

</div>
<div v-click>

<div class="vsb-fill">

### 0x88 = 1000 1000 → DSCP 34 = AF41

DSCP bits **100010**: class 4, drop precedence 1 · ECN bits **00**: not ECN-capable

</div>

<div class="pt-4 text-sm vsb-muted">

Shift right by two: $\mathrm{0x88} \gg 2 = 34 = 8 \cdot 4 + 2 \cdot 1$. Wireshark decodes the same byte as "DSCP: AF41, ECN: Not-ECT".

</div>

</div>
</div>

<!--
Serves outcome 4. Give the room 30 seconds before revealing. The top six bits are the DSCP, the bottom two the ECN
field of Lecture 03 (00 = not ECN-capable transport). Common slip: reading 0x88 = 136 as the DSCP. The reverse is
what the tc filter at the end of the lecture needs: EF 46 << 2 = 184 = 0xb8.
-->

---

# Per-hop behaviours

<div class="text-sm">

| PHB | Codepoints | What a router must do | Typical traffic |
|---|---|---|---|
| **Default** (RFC 2474) | 0 | best effort, as before DiffServ | everything unmarked |
| **EF** — Expedited Forwarding (RFC 3246) | 46 | serve at least at a configured rate, whatever else is queued: low delay, low jitter | voice |
| **AF** — Assured Forwarding (RFC 2597) | AF11 … AF43 | 4 independent classes with their own resources; 3 drop precedences inside each | video, business data |
| **CS** — Class Selector (RFC 2474) | 8n | keep the order of the old IP Precedence values | signalling, network control |
| **LE** — Lower Effort (RFC 8622) | 1 | below best effort: use only what nobody else needs | backups, updates |

</div>

<div class="pt-4 vsb-muted">

A PHB says how an aggregate is treated **in one hop**. The end-to-end service is what the operator builds from PHBs and edge conditioning.

</div>

<!--
Serves outcome 4. A PHB is a forwarding behaviour, not an implementation: EF is usually a priority queue, AF a
set of weighted queues with WRED — the next slides. CS exists so that routers configured for IP Precedence
(Lecture 03's 3-bit field) keep working: CS5 behaves at least as well as CS4, and so on. LE replaces the old
"scavenger" use of CS1, which some networks treated better than best effort.
-->

---

# EF and AF — what the RFCs actually promise

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**EF** · RFC 3246

The EF aggregate departs at **at least its configured rate** over any interval, independent of other traffic — so its queue stays short: low delay, low jitter.

A priority queue can starve everything else, so the RFC requires a **rate limiter** on EF, and the domain edge **polices EF to the agreed rate**; with no agreement, the rate is 0.

</div>
<div class="border border-gray-400 p-4">

**AF** · RFC 2597

**4 classes**, each with its own share of buffer and bandwidth, forwarded **independently** of each other.

Inside a class, **3 drop precedences**: under congestion AFx3 is more likely to be dropped than AFx2, AFx2 than AFx1.

Packets of one flow are **never reordered** within a class — which is why the meter changes only the drop precedence, never the class.

</div>
</div>

<!--
Serves outcome 4. EF: RFC 3246 §2.10 — an implementation with unlimited preemption "MUST include some means to
limit the damage" and discard the excess; §3 — the edge SHOULD police EF to the rate negotiated with the upstream
domain, and use 0 if none was negotiated. AF: RFC 2597 (Heinanen, Baker, Weiss, Wroclawski, 1999). Moving an
out-of-profile packet into another class would let it overtake its own flow; changing only its drop precedence
keeps the order. Both points return as checkpoints.
-->

---

# Schedulers that realise the PHBs

<Figure src="/figures/08/llq.svg" alt="Low-latency queuing. Arriving packets are classified by DSCP into four queues: EF, AF4, AF3 and best effort. The EF queue is served by strict priority, always first, and is policed at the edge. The other three are served by weighted round robin with weights 3 to 2 to 1 out of what EF leaves; together they form CBWFQ. EF waits only behind other EF packets, and policing keeps it from starving the weighted classes." />

<div class="text-sm">

**LLQ = PQ + CBWFQ**: one strict-priority queue for EF, weighted queues for the AF classes and best effort — Lecture 03's WFQ, per class instead of per flow.

</div>

<!--
Serves outcome 4. This is the scheduler the live demo runs at C1 and C3 (EF strict priority, then WRR 3:2:1 for
AF4, AF3, BE). In software the weights are often deficit round robin (Shreedhar & Varghese, SIGCOMM 1995), which
handles variable packet sizes with O(1) work per packet. The figure's caption is the point for the next
checkpoint: the priority queue is only safe because the edge polices EF. Extras has a table comparing FIFO, PQ,
round robin, WFQ, CBWFQ and LLQ.
-->

---

# Checkpoint — everything marked EF

<div class="checkpoint-question">

A customer discovers that EF gets the best treatment and marks **all** of its traffic EF — voice, video and backups. The core routers run the LLQ of the previous slide. What happens?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Without edge policing, EF starves every other class — and then loses its own low delay.** The priority queue takes the whole link, AF and best effort wait forever, and the EF queue itself builds up, so voice now queues behind backups. That is why the edge must police EF to the contracted rate and drop (or re-mark) the excess: EF works only while it is a small, policed share of the link.

</div>

<!--
Serves outcome 4. Allow 30 seconds for individual thought, then 30 seconds of pair discussion. Lecture 03's
checkpoint said marking alone does nothing; this is the opposite trap — marking *with* a priority scheduler but
without a policer does too much. In the live demo the EF policer at E1 is 1 Mbit/s (ten voice flows).
-->


---

# WRED — drop precedence inside one AF queue

<Figure src="/figures/08/wred-profiles.svg" alt="Drop probability against average queue depth in packets for three WRED profiles. The red profile AFx3 starts dropping at 10 packets, the yellow profile AFx2 at 20 and the green profile AFx1 at 30. Each ramps up to a maximum probability of 0.1 over 10 packets and then drops everything. A note says that the live demo simplifies this and drops each precedence outright at its threshold; either way red goes first, then yellow, then green." />

<div class="text-sm">

Lecture 03's RED curve, three times, with different thresholds — one queue, so the order of a flow's packets is kept.

</div>

<!--
Serves outcome 4. The idea goes back to Clark & Fang's RIO ("RED with In and Out", IEEE/ACM ToN 1998): one queue,
two RED curves, out-of-profile packets dropped earlier. WRED generalises it to three colours. The demo's fixed
thresholds 10 / 20 / 30 are a simplification, stated on the figure. AF traffic is usually TCP-like video or data
that backs off on loss, unlike EF voice. The figure's colours are the meter colours (green / yellow / red = AFx1 /
AFx2 / AFx3), not the classes: the live demo colours packets by class (AF4 blue tints, AF3 dark green tints —
orange in dark mode).
-->

---

# Checkpoint — AF12 vs AF21

<div class="checkpoint-question">

Both queues of a router are congested. One packet is marked **AF12**, another **AF21**. Which of the two is dropped first?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Neither — the question has no answer.** AF12 is in class 1, AF21 in class 2: different queues with their own buffer and bandwidth, forwarded independently. Drop precedence only orders packets **within one class** — AF12 before AF11, AF23 before AF22 before AF21. Whether class 1 or class 2 loses more depends on the weights and the load of each class.

</div>

<!--
Serves outcome 4. Allow 30 seconds for individual thought, then 30 seconds of pair discussion. The tempting answer
is "AF12, because 2 is a higher drop precedence than 1" or "AF21, because class 2 is better" — both compare across
classes. RFC 2597 defines no order between classes: an AF1 class with a large weight and little traffic can be
better than an AF4 class with a small weight.
-->

---

# RFC 4594 — which traffic gets which codepoint

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div>

| Service class | DSCP | Example |
|---|---|---|
| Network control | CS6 | routing |
| **Telephony** | **EF** | VoIP bearer |
| Signaling | CS5 | SIP |
| Multimedia conferencing | AF41–43 | video calls |
| Real-time interactive | CS4 | gaming |
| **Multimedia streaming** | **AF31–33** | video on demand |

</div>
<div>

| Service class | DSCP | Example |
|---|---|---|
| Broadcast video | CS3 | live TV |
| Low-latency data | AF21–23 | transactions |
| OAM | CS2 | management |
| High-throughput data | AF11–13 | bulk transfer |
| Standard | CS0 | everything else |
| Low-priority data | CS1 → LE | backups |

</div>
</div>

<div class="pt-4 vsb-muted">

A configuration guideline, not a law: each operator decides what its routers honour.

</div>

<!--
Serves outcomes 4 and 5. RFC 4594 (Babiarz, Chan, Baker, 2006), Figure 3. Telephony = Lecture 05's voice; the
streaming row is the AF3x that Lecture 07's notes cite. RFC 5865 later added VOICE-ADMIT 44 for admitted
telephony, and RFC 8622 recommends LE instead of CS1 for low-priority data. Real-time interactive uses CS4
because those flows are not elastic and should not be dropped by precedence.
-->

---

# Live — DSCP across two domains

<QosPathSim mode="diffserv" :seed="30" />

<!--
Serves outcomes 4 and 5. Both bottlenecks (C1→C2 in A, C3→E4 in B) are 10 Mbit/s; E1 marks voice EF, video AF41,
data BE, meters video with a trTCM (CIR 6, PIR 8 Mbit/s) and polices EF at 1 Mbit/s. One drawn packet is
0.1 Mbit, so even a voice packet takes 10 ms to serialise at each bottleneck: the footer's ≈ 30 ms for voice is two
serialisations (20 ms) plus, at each bottleneck, waiting for the packet in service to finish (≈ 5 ms on average)
— the floor, not congestion. Data flows send 0.5 Mbit/s each and never back off (UDP-like). Cross traffic in B is
a random (Poisson) stream. With seed 30 the first ten flows fit into A and the second ten congest it. Reset keeps
the flows in this mode; reload the page for a clean start.
Demo script (the numbers are the footer's 2 s window):
1. Press Play, then "+10 flows": 5 data, 3 video, 2 voice — 8.7 Mbit/s into A's 10 Mbit/s. Nothing queues for
   long: every class sees ≈ 20–40 ms, nothing is dropped, and video (exactly 6 Mbit/s = CIR) stays AF41. Ask the
   room what marking buys while the link is not congested (nothing visible).
2. "+10 flows" again: 7 data, 7 voice, 6 video — 16.2 Mbit/s. Video is now 12 Mbit/s, above PIR: packets leave E1
   relabelled AF42 and AF43, and C1 drops AF43 most, some AF42, no AF41 (in 20 s ≈ 780 AF43, 190 AF42, 0 AF41);
   the BE queue fills too and data waits ≈ 1.3 s. Voice still ≈ 30 ms with 0 dropped (0.7 Mbit/s, under the
   policer, strict priority).
3. Cross-traffic in B to 12 Mbit/s: B's BE queue at C3 overflows and A's data barely gets through — but voice
   keeps ≈ 30 ms, because B trusts the DSCP.
4. Boundary → bleach: E3 sets every DSCP to 0, so voice and video join C3's full BE queue behind the cross
   traffic. Within two seconds voice's queuing delay jumps from ≈ 30 ms to ≈ 310 ms — twice the 150 ms one-way
   budget on its own — and its dropped count climbs by about 3 a second: some 4 in 10 voice packets are lost
   at C3 (35–50 % depending on when you clicked). Protected in A, lost in B.
5. Optional, boundary → re-mark: B maps AF4x to AF3x and honours EF only up to 0.5 Mbit/s. That EF policer is one
   token bucket for the aggregate, so about 2 in 7 voice packets — across all seven flows, not two whole flows —
   are re-marked BE, and most of those are dropped in C3's full BE queue (voice loss ≈ 20–25 %). The footer's
   voice mean mixes ≈ 30 ms EF with the few ≈ 300 ms BE survivors, so it wanders between ≈ 50 and ≈ 180 ms.
   Back to trust and voice recovers to ≈ 30 ms.
The PDF shows a fixed frame: 4 voice, 4 video, 4 data, boundary bleach, 12 Mbit/s cross traffic, voice waiting
in C3's BE queue.
-->

---
layout: section
---

# Part 4
## IntServ vs DiffServ, and DSCP in the real Internet

---

# Scaling: state in the core

<QosCompare />

<!--
Serves outcome 5 and the thesis. The same path twice: RSVP/IntServ on the left, DiffServ on the right, one flows
slider for both. Both bottlenecks are 1000 Mbit/s so nothing is refused and the comparison is about state alone;
for the same reason DiffServ's EF policer and video meter at E1 are sized for the traffic — an SLA sized for 200
flows — otherwise most voice would be policed there and most video would leave E1 re-marked AF43.
Press Reset first, then Play, and drag the slider from 10 up to 200 in one go (the numbers below hold for that
first upward drag; dragging back and forth draws other flows). RSVP's core state is 3 core routers × 2 entries (path + resv) × the
flows that signal (voice and video; data does not): 972 entries at 200 flows with this seed (162 signalled
flows, 324 entries in every router), and 11 refresh messages per second (2 × 162 / 30 s). DiffServ's core
stays at 12 entries — 3 core routers × 4 class queues — and has nothing to refresh. Its per-flow state did not vanish: it moved to E1, the edge, which sees only its own customers. Scale
the slider to a backbone's 100 000 flows in your head — Part 2's worked example.
-->

---

# IntServ vs DiffServ

<div class="text-sm">

| | IntServ / RSVP | DiffServ |
|---|---|---|
| **Granularity** | one flow | one class (behaviour aggregate) |
| **State in the core** | per flow, in every router | per class, fixed |
| **Signalling** | RSVP per flow, soft-state refresh | none — provisioned SLAs |
| **Admission** | per flow, at every hop | at the edge, by policing |
| **Guarantee** | absolute: a computable delay bound | relative: better than another class |
| **Scales to** | campus, edge, MPLS aggregates | backbones of any size |
| **Where you meet it** | RSVP-TE in MPLS cores; IntServ over DiffServ (RFC 2998) | enterprise WANs, VPNs, mobile backhaul, Wi-Fi, data centres |

</div>

<div class="pt-2 vsb-muted">

DiffServ trades the per-flow guarantee for a simple core.

</div>

<!--
Serves outcome 5. "Relative" is the honest word: DiffServ alone promises that EF is treated better than BE at
every hop, not a number. Operators turn it into a numeric SLA by keeping the EF share small and the links
over-provisioned, and by admitting at the edge (RFC 2998's IntServ over DiffServ, Voice-Admit). This table is the
thesis statement in rows: guarantee needs state, scale forbids it.
-->

---

# DSCP across domain boundaries

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div>

At a peering point the receiving domain decides:

- **trust** — keep the DSCP (an SLA covers it)
- **re-mark** — map to its own classes, police EF to the agreed rate
- **bleach** — set everything to 0

Measurements find DSCPs re-marked or zeroed on many Internet paths; bleaching to 0 is most common near the edge, and routers still configured for ToS Precedence zero the top three bits — AF41 (34) arrives as 2 (RFC 9435).

</div>
<div>

Where marking does survive, it is **agreed**:

- **RFC 8100** — four interconnection classes: telephony (EF, VOICE-ADMIT), bulk real-time (AF41), assured elastic (AF31, AF32), default (CS0)
- **WebRTC** (RFC 8837) — EF for medium/high-priority audio, AF4x for interactive video; low priority stays DF
- **Wi-Fi** (RFC 8325) — map EF to 802.11 user priority 6, the voice access category

</div>
</div>

<!--
Serves outcome 5. The live demo's boundary selector showed the three policies. RFC 9435 (Custura, Fairhurst,
Secchi, 2023) summarises the measurement work from Aberdeen (e.g. Custura, Secchi & Fairhurst, Computer
Communications 2018): resetting the whole field is seen more at the edge than in core networks, and "ToS
precedence bleaching" turns AF11/AF21/AF31/AF41 into DSCP 2. RFC 8837's table uses EF for medium and high
priority audio and AF41/AF42 for high-priority interactive video. RFC 8325: the default mapping (top three bits)
would put EF into the video access category (UP 5), so it recommends UP 6.
-->

---

# Why inter-domain QoS stalled

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**The architect's view** · Huston, RFC 2990 (2000)

Per-hop tools do not add up to an end-to-end service by themselves: how domains agree, how a service is measured and how it is accounted for were left open.

</div>
<div class="border border-gray-400 p-4">

**The operator's view** · Bell, "Failure to thrive" (2003)

The obstacles were operational: QoS adds configuration, failure modes and troubleshooting effort to every router, while adding capacity is simple.

</div>
</div>

<div class="pt-6">

The result today: DiffServ **inside** one operator's network, where one team controls every edge; best effort **between** operators, with rare agreed exceptions.

</div>

<!--
Serves outcome 5. RFC 2990 is an IAB document written when both architectures were standardised; it lists the
open architectural issues rather than proposing a design. Bell's workshop paper (ACM SIGCOMM RIPQoS, 2003) is
the critical account from the operations side. Ask the room: who would pay Domain B for carrying A's EF traffic,
and how would A check that B delivered it? That is Part 2's "policy and billing" box again.
-->

---

# Where QoS architecture went next

<div class="grid grid-cols-2 gap-4 pt-2 text-sm">
<div class="border border-gray-400 p-3">

**L4S** · RFC 9330–9332 (2023)

ECT(1) in the ECN field marks scalable congestion control; a DualQ coupled AQM keeps its queue shallow next to classic traffic. Low queuing delay for everyone who reacts — Lecture 03's ECN, not a priority class.

</div>
<div class="border border-gray-400 p-3">

**DetNet / TSN** · RFC 8655 (2019)

Bounded latency and no congestion loss through reserved resources and fixed paths — reservations return, inside one bounded domain.

</div>
<div class="border border-gray-400 p-3">

**5G QoS flows** · 3GPP TS 23.501

Every QoS flow has a 5QI with a delay budget and loss rate — per-flow again, inside one operator; the transport network carries it as a DSCP.

</div>
<div class="border border-gray-400 p-3">

**SDN / OpenFlow** → Lecture 09

Meters and `set_field` on `ip_dscp`: the traffic conditioner of this lecture, programmed into a switch by a controller.

</div>
</div>

<!--
Serves outcome 5 and points forward. L4S: RFC 9330 architecture, RFC 9331 the ECN identifier (ECT(1)), RFC 9332
DualQ Coupled AQM. DetNet's architecture is RFC 8655; TSN is the IEEE 802.1 counterpart on Ethernet. In 5G the
SMF chooses the DSCP of the outer IP header per 5QI (TS 23.501), so the backhaul is DiffServ again — Extras has
the 5QI example. Lecture 09 does the conditioner in OpenFlow: meter bands drop or re-mark, set_field writes the
DSCP.
-->

---

# Common mix-ups

<div class="grid grid-cols-3 gap-4 pt-2 text-sm">
<div class="border border-orange-400 p-3">

**DSCP vs guarantee**

A DSCP asks for a treatment; only provisioning and edge policing turn it into a promise.

</div>
<div class="border border-orange-400 p-3">

**EF vs "unlimited priority"**

EF is low delay for a policed rate. Over that rate it is dropped or re-marked, not prioritised.

</div>
<div class="border border-orange-400 p-3">

**Drop precedence across classes**

AFx3 before AFx1 holds inside one class. AF12 vs AF21 has no defined order.

</div>
<div class="border border-orange-400 p-3">

**Who reserves in RSVP**

The receiver requests with RESV; PATH only describes what the sender will send.

</div>
<div class="border border-orange-400 p-3">

**IntServ vs RSVP**

IntServ is the service model; RSVP is signalling — RSVP-TE uses it without IntServ.

</div>
<div class="border border-orange-400 p-3">

**Edge vs core state**

DiffServ keeps per-customer state at the edge; only the core is per class.

</div>
</div>

<!--
Six confusions that recur in exam answers: (1) treating a mark as a guarantee, (2) treating EF as "always first,
however much", (3) comparing drop precedence across AF classes, (4) thinking the sender reserves in RSVP,
(5) equating IntServ with RSVP, (6) believing DiffServ needs no per-flow state anywhere.
-->

---

# Summary

<div class="grid grid-cols-2 gap-x-10 gap-y-2 pt-2 text-sm">

<div>

**Architecture, not mechanisms**
Every hop and every domain must take part; one FIFO hop undoes the rest.

**IntServ**
Per-flow guarantees: TSpec/RSpec, admission at every hop, a computable delay bound.

**RSVP**
PATH down, RESV up, admission per hop; soft state refreshed every 30 s.

**Why it did not scale**
State, refreshes and classification grow with the number of flows.

</div>
<div>

**DiffServ**
Condition at the edge, mark the DSCP, treat aggregates per hop in the core.

**PHBs and schedulers**
EF = policed priority queue; AF = 4 classes × 3 drop precedences with WRED; LLQ = PQ + CBWFQ.

**Across domains**
Trust, re-mark or bleach; DSCP survives only where it is agreed.

**The trade-off**
Guarantee needs state; scale forbids state.

</div>

</div>

<!--
Read them aloud, one sentence each. Then the exit questions.
-->

---

# Exit questions — use the ideas

1. One stream in a capture carries the DS byte 0xb8, another 0x28. Decode both DSCPs and name the PHB each asks for.
2. A voice call is marked EF and protected in your network; the next operator bleaches DSCP at the peering and its access link is congested. Predict what the caller hears, and why your own configuration cannot fix it.
3. A core router would hold 50 000 RSVP reservations with $R = 30$ s. How many refresh messages per second does it process, and how many queue entries would a DiffServ core keep instead?
4. Video is metered by a trTCM with CIR 4 Mbit/s and PIR 6 Mbit/s and sends a steady 7 Mbit/s. How much becomes AF41, AF42 and AF43, and which is dropped first?

<div v-click class="pt-5 vsb-muted">

**Explain the mechanism**, not just its name.

</div>

<!--
Allow two minutes for individual answers, then discuss. Answers: (1) 0xb8 = 1011 1000 → 101110 = 46, EF; 0x28 =
0010 1000 → 001010 = 10, AF11; both with ECN 00. (2) In the next domain the call is best effort: it queues and
is dropped with everything else on the congested link, so delay, jitter and loss rise — late packets are lost
at the jitter buffer (Lecture 05) and the MOS drops. Your EF ends at your boundary. (3) 2 × 50 000 / 30 ≈ 3 300
messages per second, plus 50 000 flows of state; DiffServ keeps one queue per class, a handful (4 in the demo),
and nothing to refresh. (4) Steady state: AF41 4, AF42 2, AF43 1 Mbit/s; AF43 is dropped first, within the AF4
queue.
-->

---

# Where you use this — Labs 05 and 03

<div class="grid grid-cols-5 gap-8 pt-2">
<div class="col-span-2 text-sm">

**Lab 05** (Mininet, `tc` links): put a priority qdisc with a DSCP filter on a switch port and send marked and unmarked pings — the counters show which band each lands in.

**Lab 03** (`tc netem`, PESQ/ViSQOL, Steps 3–6): give a call the delay and loss of the BE queue from the demo and score what bleaching costs.

</div>
<div class="col-span-3">

<div class="text-sm vsb-muted">

```bash {lines:false}
# Mininet CLI, Lab 05 Step 7 topology: s1-eth2 faces s2
sh tc qdisc replace dev s1-eth2 root handle 1: prio
sh tc filter add dev s1-eth2 parent 1: protocol ip \
   u32 match ip dsfield 0xb8 0xfc flowid 1:1
h1 ping -c 5 -Q 0xb8 h2
sh tc -s class show dev s1-eth2
```

</div>

<div class="pt-4 text-sm">

0xb8 = EF 46 shifted left by two; mask 0xfc ignores the ECN bits.

</div>
</div>
</div>

<!--
Neither lab has a DiffServ task; this slide says where the tools are. In Lab 05's Step 7 topology s1-eth1 faces
h1 and s1-eth2 the 10 Mbit/s link to s2. The prio qdisc has three bands (classes 1:1–1:3); the filter sends EF
to band 1:1, the highest, and everything else follows the default priomap. Replacing the root qdisc removes
Mininet's htb and netem from that port, so this shows classification, not delay under load — for that, the
rate limit has to go back underneath the prio bands, an extension beyond the lab README. ping -Q sets the whole
ToS byte. Lab 03 measures the effect: Step 3's netem trials and the PESQ/ViSQOL scoring of Steps 5–6.
-->

---

# References — standards: IntServ, RSVP and the DS field

<div class="text-xs">

- R. Braden, D. Clark, S. Shenker, "Integrated Services in the Internet Architecture: an Overview," RFC 1633, 1994.
- R. Braden (ed.) et al., "Resource ReSerVation Protocol (RSVP) — Version 1 Functional Specification," RFC 2205, 1997.
- J. Wroclawski, "The Use of RSVP with IETF Integrated Services," RFC 2210, 1997.
- J. Wroclawski, "Specification of the Controlled-Load Network Element Service," RFC 2211, 1997.
- S. Shenker, C. Partridge, R. Guérin, "Specification of Guaranteed Quality of Service," RFC 2212, 1997.
- L. Berger et al., "RSVP Refresh Overhead Reduction Extensions," RFC 2961, 2001.
- G. Huston, "Next Steps for the IP QoS Architecture," RFC 2990, 2000.
- Y. Bernet et al., "A Framework for Integrated Services Operation over Diffserv Networks," RFC 2998, 2000.
- D. Awduche et al., "RSVP-TE: Extensions to RSVP for LSP Tunnels," RFC 3209, 2001.
- F. Baker, J. Polk, M. Dolly, "A Differentiated Services Code Point (DSCP) for Capacity-Admitted Traffic," RFC 5865, 2010.
- K. Nichols, S. Blake, F. Baker, D. Black, "Definition of the Differentiated Services Field (DS Field) in the IPv4 and IPv6 Headers," RFC 2474, 1998.
- S. Blake et al., "An Architecture for Differentiated Services," RFC 2475, 1998.
- K. Nichols, V. Jacobson, L. Zhang, "A Two-bit Differentiated Services Architecture for the Internet," RFC 2638, 1999.
- K. Ramakrishnan, S. Floyd, D. Black, "The Addition of Explicit Congestion Notification (ECN) to IP," RFC 3168, 2001.

</div>

<!--
Part 2's IntServ and RSVP documents and the DiffServ foundations. Every entry was checked against the RFC
Editor's record (authors, title, year).
-->

---

# References — standards: PHBs, practice and what came next

<div class="text-xs">

- J. Heinanen, F. Baker, W. Weiss, J. Wroclawski, "Assured Forwarding PHB Group," RFC 2597, 1999.
- J. Heinanen, R. Guérin, "A Single Rate Three Color Marker," RFC 2697, and "A Two Rate Three Color Marker," RFC 2698, 1999.
- B. Davie et al., "An Expedited Forwarding PHB (Per-Hop Behavior)," RFC 3246, 2002.
- J. Babiarz, K. Chan, F. Baker, "Configuration Guidelines for DiffServ Service Classes," RFC 4594, 2006.
- R. Geib (ed.), D. Black, "Diffserv-Interconnection Classes and Practice," RFC 8100, 2017.
- T. Szigeti, J. Henry, F. Baker, "Mapping Diffserv to IEEE 802.11," RFC 8325, 2018.
- R. Bless, "A Lower-Effort Per-Hop Behavior (LE PHB) for Differentiated Services," RFC 8622, 2019.
- P. Jones et al., "Differentiated Services Code Point (DSCP) Packet Markings for WebRTC QoS," RFC 8837, 2021.
- A. Custura, G. Fairhurst, R. Secchi, "Considerations for Assigning a New Recommended DSCP," RFC 9435, 2023.
- B. Briscoe (ed.) et al., "Low Latency, Low Loss, and Scalable Throughput (L4S) Internet Service: Architecture," RFC 9330, 2023.
- K. De Schepper, B. Briscoe (ed.), "The Explicit Congestion Notification (ECN) Protocol for … (L4S)," RFC 9331, and K. De Schepper et al., "Dual-Queue Coupled Active Queue Management (AQM) for … (L4S)," RFC 9332, 2023.
- N. Finn, P. Thubert, B. Varga, J. Farkas, "Deterministic Networking Architecture," RFC 8655, 2019.
- 3GPP TS 23.501, *System architecture for the 5G System (5GS)*, Table 5.7.4-1 (standardized 5QI values).

</div>

<!--
The DiffServ PHBs, meters and service classes of Part 3, and the interconnection, measurement and outlook
documents of Part 4. In the RFC 9331 and 9332 titles the "…" stands for "Low Latency, Low Loss, and Scalable
Throughput".
-->

---

# References — literature

<div class="text-xs">

- D. D. Clark, S. Shenker, L. Zhang, "Supporting Real-Time Applications in an Integrated Services Packet Network: Architecture and Mechanism," *ACM SIGCOMM*, 1992.
- L. Zhang, S. Deering, D. Estrin, S. Shenker, D. Zappala, "RSVP: A New Resource ReSerVation Protocol," *IEEE Network*, 7(5), 8–18, 1993.
- A. K. Parekh, R. G. Gallager, "A Generalized Processor Sharing Approach to Flow Control in Integrated Services Networks: The Single-Node Case," *IEEE/ACM Transactions on Networking*, 1(3), 344–357, 1993.
- M. Shreedhar, G. Varghese, "Efficient Fair Queueing Using Deficit Round Robin," *ACM SIGCOMM*, 1995.
- D. D. Clark, W. Fang, "Explicit Allocation of Best-Effort Packet Delivery Service," *IEEE/ACM Transactions on Networking*, 6(4), 362–373, 1998.
- I. Stoica, S. Shenker, H. Zhang, "Core-Stateless Fair Queueing: Achieving Approximately Fair Bandwidth Allocations in High Speed Networks," *ACM SIGCOMM*, 1998.
- I. Stoica, H. Zhang, "Providing Guaranteed Services Without Per Flow Management," *ACM SIGCOMM*, 1999.
- G. Bell, "Failure to Thrive: QoS and the Culture of Operational Networking," *ACM SIGCOMM Workshop on Revisiting IP QoS (RIPQoS)*, 2003.
- A. Custura, R. Secchi, G. Fairhurst, "Exploring DSCP Modification Pathologies in the Internet," *Computer Communications*, 127, 86–94, 2018.
- L. Peterson, B. Davie, *Computer Networks: A Systems Approach*, section 6.5 "Quality of Service" (open edition, book.systemsapproach.org).
- J. F. Kurose, K. W. Ross, *Computer Networking: A Top-Down Approach*, 7th ed., ch. 9 "Multimedia Networking". Pearson, 2017.
- T. Szigeti, C. Hattingh, *End-to-End QoS Network Design*. Cisco Press, 2004.

</div>

<!--
Clark, Shenker & Zhang and Zhang et al. are the design papers behind IntServ and RSVP; Parekh & Gallager the
delay bound; DRR and RIO the scheduler and dropper ideas behind CBWFQ and WRED; Stoica et al. the stateless-core
research in Extras; Bell and Custura et al. the operational and measured view of Part 4. Peterson & Davie is the
open textbook chapter to read first.
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
## The full delay bound, queue disciplines, stateless cores and 5G QoS

<!--
Not part of the timed 90-minute route. Use to answer questions or extend an advanced class.
-->

---

# Extras — the full Guaranteed-service delay bound

<div class="grid grid-cols-2 gap-8 pt-2">
<div class="text-sm">

RFC 2212 with the peak rate $p$ and maximum packet size $M$, for $p > R \ge r$:

$$D \le \frac{b-M}{R}\,\frac{p-R}{p-r} + \frac{M + C_{\mathrm{tot}}}{R} + D_{\mathrm{tot}}$$

and for $R \ge p \ge r$ only the last two terms remain. As $p \to \infty$ it becomes Part 2's fluid bound.

</div>
<div v-click class="text-sm">

Part 2's voice trunk with $r = 1$ Mbit/s, $p = 10$ Mbit/s, $M = 12$ kbit:

- burst term: $68 / 2 \cdot 8/9 \approx 30.2$ ms
- $(12 + 48) / 2 = 30$ ms, plus $D_{\mathrm{tot}} = 0.48$ ms

<div class="vsb-fill mt-4">

### $D \le 60.7$ ms

instead of 64.5 ms: a known peak rate tightens the bound

</div>

</div>
</div>

<!--
RFC 2212's "Policing" and "Exported information" sections define the terms; the formula is quoted from its
end-to-end behaviour section. Units in the example: b − M = 80 − 12 = 68 kbit, R = 2 Mbit/s → 34 ms, times
(p − R)/(p − r) = 8/9; M + C_tot = 12 + 48 kbit over 2 Mbit/s = 30 ms. If the receiver reserved R = 10 Mbit/s ≥ p,
the bound would collapse to 60 kbit / 10 Mbit/s + 0.48 ms ≈ 6.5 ms: the burst never queues.
-->

---

# Extras — queue disciplines compared

<div class="text-sm">

| Discipline | Queues | Served | Protects | Risk |
|---|---|---|---|---|
| **FIFO** | one | in arrival order | nothing | one burst delays everybody |
| **PQ** — priority | a few, ranked | highest non-empty first | the top queue's delay | lower queues starve |
| **CQ / WRR** — round robin | per class | a quota of packets or bytes each | a share of the link | delay grows with the round |
| **WFQ** | per flow | by virtual finish time | each flow's share | per-flow state |
| **CBWFQ** | per class | WFQ over classes, configured weights | each class's share | no strict low delay |
| **LLQ** | PQ + CBWFQ | priority first, then weights | delay of EF *and* shares of the rest | EF must be policed |

</div>

<!--
Extends Part 3's scheduler slide; condenses the original course slides' list of queue types (FIFO, CQ,
WFQ, CBWFQ, PQ, LLQ).
WFQ is Lecture 03's per-flow scheduler — the IntServ choice; CBWFQ is the same algorithm over DiffServ classes.
Parekh and Gallager's delay bound from Part 2 holds for WFQ; LLQ gives EF something close to it as long as EF is
policed. Custom queuing (CQ) is Cisco's name for byte-quota round robin.
-->

---

# Extras — guarantees without per-flow state in the core?

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**Core-Stateless Fair Queueing** · Stoica, Shenker, Zhang, SIGCOMM 1998

The edge measures each flow's rate $r_i$ and writes it into the packet. A core router estimates the fair share $\alpha$ and drops each packet with probability $\max(0,\ 1 - \alpha / r_i)$ — fair bandwidth without knowing the flows.

</div>
<div class="border border-gray-400 p-4">

**Dynamic packet state** · Stoica, Zhang, SIGCOMM 1999

The same trick for IntServ: the packet carries the scheduling state its flow needs, so a core router can give Guaranteed-service delay bounds while keeping no per-flow state.

</div>
</div>

<div class="pt-6 vsb-muted">

Research answers to the thesis: move the state into the packet header. They needed header bits that the IP header did not have, and were not deployed.

</div>

<!--
Both papers keep the DiffServ split — per-flow work at the edge, simple core — but carry per-flow information
in each packet instead of a class label. Stoica & Zhang's scheduler is Core-Jitter Virtual Clock (CJVC). The
"not deployed" sentence is the honest status; the ideas reappear in later programmable-switch research.
-->

---

# Extras — a 5G QoS flow

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div>

3GPP TS 23.501, Table 5.7.4-1 (excerpt):

| 5QI | Type | Delay budget | Packet error rate | Example |
|---|---|---|---|---|
| 1 | GBR | 100 ms | $10^{-2}$ | conversational voice |
| 5 | non-GBR | 100 ms | $10^{-6}$ | IMS signalling |

</div>
<div>

A VoNR call (VoLTE: QCI 1 in 4G) gets a **guaranteed-bit-rate QoS flow** with 5QI 1, set up per call — admission and per-flow state, as in IntServ, but inside one operator's radio and core network.

Between the base station and the core the packets travel in GTP-U tunnels whose outer IP header carries a **DSCP chosen per 5QI** — DiffServ again.

</div>
</div>

<!--
Ties Lecture 05's voice to the 5G system: 5QI 1 is the voice bearer, 5QI 5 its SIP signalling. The 100 ms
packet delay budget is between the terminal and the UPF; the 10⁻² packet error rate is loss the codec and the
jitter buffer must hide. TS 23.501 §5.7: the SMF determines the transport-level DSCP of the outer IP header from
the 5QI. Per-flow state works here because one operator controls the whole path and charges for it.
-->
