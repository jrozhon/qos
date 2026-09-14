---
theme: seriph
title: 02 · Kendall's notation and the M/M/1 queue
info: |
  440-2216/01 Kvalita služeb — lecture 2.
  Queueing systems, Kendall's notation, the Poisson process, the exponential distribution, Little's law, the
  M/M/1 queue, and the erlang traffic-engineering formulas (Erlang B, Erlang C, Engset).
  Companion lecture to Exercise 02.
exportFilename: 02-queuing_theory
layout: cover
transition: slide-left
mdc: true
lineNumbers: true
fonts:
  provider: none
  sans: Carlito
  mono: IBM Plex Mono
---

# Kendall's notation and an introduction to queueing theory

### 440-2216/01 Kvalita služeb · Lecture 02

<div class="pt-6 text-sm vsb-muted">
Jan Rozhon, Miroslav Vozňák &middot; Department of Telecommunications, FEECS
</div>

<!--
Ninety minutes including checkpoints: 5 min motivation, 20 queueing systems/Kendall notation, 15 Poisson
process/exponential distribution, 30 Little's law/M/M/1 with two worked examples, 15 traffic engineering/Erlang
formulas, 5 exit questions and exercise setup. Part 1 supports Exercise 02 Steps 1-2; Part 2 supports the
Preparation step (random samples); Part 3 supports Steps 3-4; Part 4 supports README Question 1. Keep the
90-minute route to the closing slide. History, M/M/k, and the SimPy component reference are Extras after the
closing slide; skip them in the main lecture.

If they have already opened Exercise 01, start from "last time" — this lecture reuses the exponential distribution
and the arithmetic-mean skills from the noise experiments.
-->

---

# Where we are going

<div class="grid grid-cols-3 gap-5 pt-4">

<div class="border border-gray-400 p-4">
<div class="text-sm opacity-60">Part 1</div>

### Queueing systems

Arrivals, servers, waiting positions, and Kendall's A/B/C/D/E/F notation for classifying a queue

<div class="text-xs opacity-60 pt-3">↔ Exercise 02, Steps 1–2</div>
</div>

<div class="border border-gray-400 p-4">
<div class="text-sm opacity-60">Parts 2–3</div>

### From Poisson arrivals to M/M/1

The Poisson process, the exponential distribution, Little's law, and the M/M/1 delay and occupancy formulas

<div class="text-xs opacity-60 pt-3">↔ Exercise 02, Preparation and Steps 3–4</div>
</div>

<div class="border border-gray-400 p-4">
<div class="text-sm opacity-60">Part 4</div>

### Traffic engineering

The erlang, offered traffic, and the classic Erlang B, Erlang C and Engset formulas for dimensioning lines

<div class="text-xs opacity-60 pt-3">↔ README Question 1</div>
</div>

</div>

<div class="pt-8">

One question runs through the whole lecture: a shared resource serves requests one at a time — **how long does a request wait, and how many lines does the resource need?**

</div>

<!--
Lecture 1 asked how many bits a channel can carry. This lecture asks what happens when many messages compete
for one channel over time — the queue is the price of sharing a finite resource.
-->

---

# What you should be able to do

1. Read Kendall's A/B/C/D/E/F notation and state the assumptions behind M/M/1.
2. Explain why the exponential distribution is memoryless and why that makes Poisson-driven queues tractable.
3. Compute the offered traffic, utilization, mean occupancy, and mean delay of an M/M/1 system.
4. Apply Little's law to relate occupancy and delay for any stable queueing system.
5. Compute a blocking probability with Erlang B and a waiting probability with Erlang C.

<div class="pt-4 vsb-muted">

Keep asking: **which system, which rate, which distribution, and does it have a steady state?**

</div>

<!--
These are the five outcomes for the lecture. Students need arithmetic means, basic probability, and the natural
exponential/logarithm from Exercise 01. Kendall notation and the M/M/1 formulas are introduced here for the
first time — the exercise's theory cells cover the same random-variable background.
-->

---
layout: statement
---

# A queue is what happens when arrivals outrun service, even briefly

## QoS dimensions the servers, the buffer, and the discipline so that delay and loss stay bounded

<!--
Lecture 1 fixed the channel and asked how many bits it can carry. This lecture keeps the channel but lets
requests arrive at random and compete for it. Queueing theory quantifies the resulting wait — this is the
mathematics behind "how many trunks", "how big a buffer", and "how much of the link can we sell".
-->

---
layout: section
---

# Part 1
## Queueing systems and Kendall's notation

---

# A familiar queue, first

<div class="grid grid-cols-2 gap-8 pt-4">
<div>

Picture a small coffee shop with two baristas and a line by the door.

- Customers **arrive** at some average rate — some minutes two show up, some minutes none.
- Each **barista** takes a while to make a drink, then is free for the next customer.
- If both baristas are busy, new customers **wait in line**.
- The shop decides **who is served next** — usually whoever arrived first.

</div>
<div>

| Coffee shop | Queueing system |
|---|---|
| Customers arriving | Arrival rate $\lambda$ |
| One barista's pace | Service rate $\mu$ |
| Number of baristas | Number of servers |
| The line by the door | Waiting positions |
| "Next, please" order | Queueing discipline |

</div>
</div>

<div class="pt-6 vsb-muted">

Every formula in this lecture is this picture, made precise enough to compute with.

</div>

<!--
Anchor the abstract letters in something everyone has stood in. Ask the room for their own example (a router
port, a call centre, a supermarket till) before moving on — the mapping is the same every time.
-->

---

# Anatomy of a queueing system

<img class="lecture-diagram" src="/figures/02/queue-model.svg" alt="Arrivals enter a buffer of waiting positions, are served by one or more servers, then depart." />

Same shape as the coffee shop — now with the vocabulary we will use for the rest of the lecture. A queueing system is described by five things:

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div>

- **Arrival rate** $\lambda$ \[s$^{-1}$\] — requests offered per second
- **Service rate** $\mu$ \[s$^{-1}$\] — requests one server completes per second
- **Number of servers** — how many requests can be served at once

</div>
<div>

- **Number of waiting positions** — buffer size; default is unbounded
- **Queueing discipline** — FIFO/FCFS, LIFO/LCFS, SIRO (serve in random order), priority queueing (PQ), …

</div>
</div>

<!--
Requests, customers, calls and packets are the same abstraction here. Map the picture onto a router port: source
= incoming packets, waiting positions = the port's buffer, server = the outgoing link at its bit rate. Emphasise
that arrival rate and service rate are both rates (events per second), not counts.
-->

---

# What we want to know

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

### The customer's side

- Queueing delay and total delay in the system
- Number of requests waiting, or in the system
- The probability of having to wait, or of being blocked outright

</div>
<div>

### The provider's side

- Server utilization / occupancy
- Buffer utilization / occupancy
- Revenue obtained versus revenue lost to blocking
- Customer satisfaction — grade of service (GoS)

</div>
</div>

<div class="pt-6">

The rest of this lecture builds the formulas that connect these quantities to $\lambda$, $\mu$, and the number of servers.

</div>

<!--
This is the QoS/QoE split again, one lecture early: the customer experiences delay and blocking, the provider
manages utilization and revenue. Grade of service (GoS) is usually a target blocking probability, e.g. Erlang B
= 1% is a classic telephony dimensioning target — introduced properly in Part 4.
-->

---

# Kendall's notation — A/B/C/D/E/F

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div>

- **A** — inter-arrival time distribution
- **B** — service time distribution
- **C** — number of servers
- **D** — system capacity $K$ (waiting **+** in service). Default: infinite
- **E** — population size (number of potential sources). Default: infinite
- **F** — queueing discipline. Default: FIFO

</div>
<div>

**Distribution codes for A and B:**

- **M** — exponential (*Markovian* / memoryless)
- **D** — deterministic (constant, "degenerate")
- **E$_k$** — Erlang of order $k$ (sum of $k$ exponential stages)
- **G** — general (any distribution)

</div>
</div>

<div class="pt-4 vsb-muted text-sm">

Trailing fields may be omitted when they take their default value: A/B/C means A/B/C/∞/∞/FIFO.

</div>

<!--
D is sometimes written as just the queue length in older texts; the total-system-capacity reading is the one
used in Kleinrock and in Gross & Harris and is the one this course uses. Flag the ambiguity, do not relitigate
it. E finite reappears in Part 4 as the Engset model — population size changes the arrival process itself,
because a busy source cannot also be generating a new arrival.
-->

---

# Kendall's notation — worked examples

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

**M/M/1** $\;=\;$ M/M/1/∞/∞/FIFO

- Poisson arrivals
- exponentially distributed service times
- one server, unbounded queue, FIFO

The model this lecture builds toward.

</div>
<div>

**M/M/N/N** $\;=\;$ Erlang B

- Poisson arrivals, exponential service
- $N$ servers, **no waiting positions**
- a blocked call is lost, not queued

The model behind Part 4's first formula.

</div>
</div>

<div v-click class="pt-6">

**M/D/1/20** — Poisson arrivals, **constant** service time, one server, room for 20 requests total (19 waiting while one is served).

</div>

<!--
Give the room 30 seconds to parse M/D/1/20 themselves before the reveal — this is the checkpoint's warm-up.
M/M/N/N is sometimes written M/M/N/0 for "zero extra waiting positions"; both notations appear in the
literature and mean the same loss system.
-->

---

# Checkpoint — reading Kendall's notation

<div class="checkpoint-question">

A support hotline is modeled as G/M/2/5. What does each symbol say about how it works, and what happens to caller number six?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**General inter-arrival times, exponential (Markovian) call-handling times, 2 agents, room for 5 callers total.**

Two callers are served at once; up to three more wait on hold. A sixth caller, arriving while all five places are occupied, is **blocked** — Kendall's notation says nothing about what happens to a blocked request; that is a system-design choice (busy tone, overflow route, voicemail, …).

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. G means the model does not assume
Poisson arrivals — realistic call-centre arrivals are often not memoryless. Population and discipline default
to infinite/FIFO since E and F are omitted.
-->

---
layout: section
---

# Part 2
## The Poisson process and the exponential distribution

---

# The Poisson process — arrivals at a constant, memoryless rate

<img class="lecture-diagram" src="/figures/02/poisson-process.svg" alt="Arrival instants on a time axis; the gaps between consecutive arrivals are independent exponential inter-arrival times." />

A **homogeneous Poisson process** models arrivals happening independently, at a constant average rate $\lambda$, completely at random.

<!--
This is the M in Kendall's notation. The two boxed properties below the figure are what "completely at random"
means precisely: independent increments (disjoint intervals don't influence each other) and a rate that does
not depend on the time of day (stationarity, in the homogeneous case).
-->

---

# Two equivalent descriptions

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

### Counting arrivals

The number of arrivals $N$ in an interval of length $t$ is Poisson-distributed:

$$
P(N=k) = \frac{(\lambda t)^k}{k!}\,e^{-\lambda t}, \quad k=0,1,2,\dots
$$

Mean $E(N)=\lambda t$, variance $D(N)=\lambda t$.

</div>
<div>

### Timing arrivals

The **inter-arrival times** are independent and exponentially distributed with rate $\lambda$:

$$
f(x)=\lambda e^{-\lambda x}, \quad x \geq 0
$$

Mean $E(T) = 1/\lambda$, variance $D(T)=1/\lambda^2$.

</div>
</div>

<div v-click class="pt-6">

**These describe the same process.** A packet source that draws each inter-arrival time from Exponential($\lambda$) generates a Poisson process with rate $\lambda$ — this is how the simulation builds arrivals.

</div>

<!--
Both halves matter for the exercise: the theory cells sample from the exponential directly, and PacketSource is
configured with an exponential inter-arrival callable. Splitting and merging independent Poisson streams gives
another Poisson stream with the summed rate, λ=λ1+λ2 — useful when several sources feed one queue, mention only
if time allows.
-->

---

# The exponential distribution is memoryless

<img class="lecture-diagram" src="/figures/02/exponential-pdf.svg" alt="Exponential probability density for two rates, both decaying monotonically from their peak at zero." />

$$
P(T > s+t \mid T > s) = P(T > t)
$$

<div class="pt-2">

**The time still to wait does not depend on how long you have already waited.** A server that has been busy for ten minutes is, under this model, no more likely to finish in the next second than one that just started.

</div>

<!--
This is the property that makes M/M/1 tractable: the state of the system (how many are present) is enough to
predict its future, without remembering how long the current service has been running — a continuous-time
Markov chain. It is also the property to interrogate critically: human conversation length and job-processing
time are often not memoryless in reality; M/M/1 is a tractable baseline, not a universal truth about service
times. Deterministic (D) or general (G) service models drop this assumption at the cost of simpler formulas.
-->

---

# Checkpoint — why not measure elapsed service time?

<div class="checkpoint-question">

A router port is mid-way through transmitting a large packet when a new one arrives. Under the M/M/1 model, does knowing that the current packet has already been "in service" for a while change your prediction of how much longer it needs?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**No — that is exactly what memorylessness means for the exponential service-time model.**

The remaining service time still has the same Exponential($\mu$) distribution, regardless of elapsed time. This is a modeling assumption, not a law of physics: real transmission times for a fixed-size packet are close to **deterministic**, which is why M/D/1 and G/G/1 models also matter in practice.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. Use this to preview why the
exercise also samples a normal and a uniform distribution: contrasting a memoryless model with bounded,
non-memoryless alternatives sharpens what "memoryless" buys you mathematically and costs you physically.
-->

---
layout: section
---

# Part 3
## Little's law and the M/M/1 queue

---

# Little's law

<img class="lecture-diagram" src="/figures/02/littles-law.svg" alt="A request waits Wq in the queue, then receives service of mean length 1/mu; total time in the system is W." />

<div class="pt-1 text-xl">

$$
L = \lambda W, \qquad L_q = \lambda W_q
$$

</div>

<div class="grid grid-cols-3 gap-6 pt-2 text-sm">
<div>

$L$ — mean number **in the system** \[–\]

</div>
<div>

$\lambda$ — mean **admitted** rate \[s$^{-1}$\]

</div>
<div>

$W$ — mean time **in the system** \[s\]

</div>
</div>

<div v-click class="pt-3">

Holds for **any** stable queueing system, whatever the arrival and service distributions are — a very general accounting identity, not specific to M/M/1.

</div>

<!--
Little 1961 proved this for essentially any work-conserving stable system. λ is the admitted rate — blocked or
lost requests do not count. The second form, Lq=λWq, isolates the waiting room from the server: the figure's gap
between the two brackets, L−Lq=λ(W−Wq)=λ/μ=ρ, is the mean number in service; the algebra is spelled out again
in Extras for a written sanity check.
-->

---

# Little's law — a worked example

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

Three independent message classes share a system with **no waiting queue** — each message is served immediately (ample capacity), so $W$ is simply the mean handling time.

| Class | Rate | Mean time $W$ |
|---|---|---|
| 1 | 120 msg/min | 200 ms |
| 2 | 20 msg/min | 10 s (6 msg/min served) |
| 3 | 10 msg/min | 30 s |

</div>
<div>

$$
L_1 = \frac{120}{60}\cdot0.2 = 0.4
$$
$$
L_2 = \frac{20}{60}\cdot10 = 3.33
$$
$$
L_3 = \frac{10}{60}\cdot30 = 5.0
$$

<div v-click class="pt-2 vsb-fill">

$$
L = L_1+L_2+L_3 = 8.73
$$

</div>
</div>
</div>

<!--
Convert every rate to per-second before multiplying, or keep everything per-minute consistently — the mixed
units (ms, s, min) are the point of the exercise. Because expectation is linear, the mean total occupancy is
the sum of the per-class means even though the classes interleave on one system; this does not require the
classes to be independent, only that "number of class i in the system" adds up to "number in the system".
-->

---

# The M/M/1 queue

<img class="lecture-diagram" src="/figures/02/mm1-birth-death.svg" alt="Birth-death diagram of the M/M/1 queue: arrivals push the state up, services pull it down." />

**M/M/1:** Poisson arrivals ($\lambda$), exponential service times ($\mu$), one server, unbounded queue, FIFO.

$$
\rho = \frac{\lambda}{\mu} \qquad \text{(utilization = offered traffic, in erlang)}
$$

<div class="pt-2 vsb-muted text-sm">

A steady state exists only for $\rho < 1$. At or above this threshold, the mean queue length grows without bound.

</div>

<!--
The state is simply "how many customers are present" — memorylessness of both A and B (M and M) is exactly
what makes this one number enough to predict the future, giving the birth-death chain on this slide. ρ carries
two readings: fraction of time the server is busy, and offered traffic in erlang — Part 4 reuses the second one.
-->

---

# Where the formulas come from

<div class="pt-2">

At steady state, the flow **up** across any cut of the chain must equal the flow **down** across it — the rate of leaving state $n$ upward equals the rate of arriving there from above:

</div>

$$
\lambda\,p_n = \mu\,p_{n+1} \quad\Rightarrow\quad p_n = \rho^n\,(1-\rho)
$$

<div class="pt-4">

$p_n$ is the steady-state probability of finding $n$ requests in the system — a geometric distribution in $n$. Summing $n\,p_n$ over all $n$ is exactly where

$$
L = \sum_{n=0}^{\infty} n\,p_n = \frac{\rho}{1-\rho}
$$

comes from — the formula on the next slide is this sum, not a rule to memorize independently of the picture.

</div>

<!--
Keep this to the one balance idea — "cut the chain anywhere, up-flow equals down-flow" — and the resulting
geometric p_n. The full derivation (normalizing Σp_n=1, then summing the geometric series for L) is not
examined; the point is that the diagram from the previous slide is where the next slide's formulas live, not a
separate fact to memorize. W then follows from L via Little's law: W=L/λ=1/(μ−λ).
-->

---

# M/M/1 — occupancy and delay

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

**In the system:**

$$
L = \frac{\rho}{1-\rho} \qquad\qquad W = \frac{1}{\mu-\lambda}
$$

</div>
<div>

**In the queue (waiting only):**

$$
L_q = \frac{\rho^2}{1-\rho} \qquad\qquad W_q = \frac{\rho}{\mu-\lambda}
$$

</div>
</div>

<div class="pt-4 vsb-muted text-sm">

$L$, $L_q$ are dimensionless \[–\]; $W$, $W_q$ are times \[s\]. All four grow without bound as $\rho \to 1$:

</div>

<div v-click class="pt-1 text-sm">

| $\rho$ | 0.5 | 0.8 | 0.9 | 0.95 | 0.99 |
|---|---|---|---|---|---|
| $L=\rho/(1-\rho)$ | 1 | 4 | 9 | 19 | 99 |
| $W$, as a multiple of $1/\mu$ | 2× | 5× | 10× | 20× | 100× |

</div>

<div v-click class="pt-2 text-sm">

This is why links are run well below full utilization. With $k$ identical servers (M/M/k), utilization is $\rho = A/k$ instead; these four formulas are M/M/1 only.

</div>

<!--
Derivable from the birth-death chain's steady-state probabilities p_n=(1-ρ)ρ^n and Little's law — spelled out on
the previous slide; the full derivation itself is optional and not examined. Emphasise L−Lq=ρ (mean number in
service) matches the littles-law figure. Walk the table left to right: doubling ρ from 0.5 to 0.99 (2x) produces
a 50x blow-up in W, not a 2x one — this is the same number the saturation checkpoint asks about, made concrete.
The M/M/k caveat matters because a common student error is applying these formulas to a multi-server port.
-->

---

# M/M/1 — from packet size to delay

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

Poisson arrivals at $\lambda=5$ packet/s, exponential sizes with mean $\bar b = 100$ B, link rate $R=8\,000$ bit/s.

<div v-click class="pt-2">

$$
S = \frac{8\bar b}{R} = \frac{8\cdot100}{8000} = 0.1\ \mathrm{s} \;\Rightarrow\; \mu = 10\ \mathrm{s}^{-1}
$$

</div>
<div v-click class="pt-2">

$$
\rho = \frac{\lambda}{\mu} = 0.5
$$

</div>

</div>
<div v-click>

<div class="vsb-fill">

### $L=1$, $W=0.2$ s

$W_q = 0.1$ s waiting, $1/\mu = 0.1$ s transmitting

</div>

<div class="pt-4 text-sm vsb-muted">

This is Exercise 02, Step 4: a `SwitchPort` with exponential inter-arrivals and exponential packet sizes approximates M/M/1 when its buffer is large enough that loss is negligible.

</div>

</div>
</div>

<!--
Do the arithmetic on the board: S from bits per packet over bit rate, μ=1/S, ρ=λ/μ, then L and W from the
previous slide's formulas. In the notebook this is checked against a NetworkTap's mean occupancy and a
PacketSink's mean delay after an 1000 s warm-up period — finite buffers and warm-up transients are why the
simulated numbers only approximate the ideal ones.
-->

---

# Checkpoint — delay near saturation

<div class="checkpoint-question">

A link runs at $\rho=0.9$. The server is busy only 90% of the time — it is not saturated. Why does the mean delay $W$ already feel enormous?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Because $W=1/(\mu-\lambda)$ has $\rho$ in its denominator through $1-\rho$, not in a bounded ratio.**

At $\rho=0.9$, $W$ is already $10\times$ the mean service time $1/\mu$; at $\rho=0.99$ it is $100\times$. The server being idle 10% of the time is enough for a long queue to build up during the busy stretches and only slowly drain — occasional idleness does not undo an accumulated backlog.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. Exercise 02 README question 4 asks
this in the notebook's own words. Sketch L=ρ/(1-ρ) versus ρ on the board if there is time: it is flat until
about ρ=0.7 and then rises steeply — this is why "utilization under 100%" is not the same as "no problem".
-->

---
layout: section
---

# Part 4
## Traffic engineering: the erlang and the Erlang formulas

---

# Traffic engineering

<div class="grid grid-cols-3 gap-6 pt-4">
<div class="border border-green-400 p-4">

### Erlang B

Blocking probability of a **loss system**: no waiting positions, a blocked call is refused. M/M/N/N.

</div>
<div class="border border-green-400 p-4">

### Erlang C

Probability that a call must **wait**: blocked calls stay in the system until served. M/M/N.

</div>
<div class="border border-green-400 p-4">

### Engset

Like Erlang B, but for a **finite population** of sources — low-traffic scenarios where Erlang B's infinite-population assumption breaks down.

</div>
</div>

<div class="pt-8 vsb-muted">

**Agner Krarup Erlang** (1878–1929), a Danish mathematician, founded traffic engineering and queueing theory at the Copenhagen Telephone Company.

</div>

<!--
Erlang's 1909 paper proved the Poisson distribution applies to random telephone traffic; his 1917 paper gives
the classic loss and waiting-time formulas that carry his name. Engset's model, published from 1918, is named
for T. O. Engset, a contemporary Norwegian engineer.
-->

---

# The erlang — a unit of traffic load

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

**1 erlang (Erl)** = full-time occupancy of one channel: 60 minutes of traffic carried in 60 minutes, or equivalently one call continuously in progress.

For $N_x(t)$ simultaneously busy channels, the **carried traffic** over a period $T$ is

$$
Y = \frac{1}{T}\int_{t_0}^{t_0+T} N_x\,dt \quad [\mathrm{Erl}]
$$

</div>
<div>

**Offered traffic** $A$ \[Erl\] is what arrives; **carried traffic** $Y$ \[Erl\] is what gets served; **lost traffic** $Z$ \[Erl\] is what is blocked and routed elsewhere or dropped:

$$
Y = A - Z
$$

For an M/M/1 queue with no loss, $A=\rho$ — the same offered traffic from Part 3, just in telephony units.

</div>
</div>

<!--
The erlang is dimensionless (it is a ratio, arrivals×holding time), which is why it slots into both a queueing
formula's ρ and a trunk-group's A without a unit conversion. Full utilization of the line capacity is the
"60 minutes of traffic in 60 minutes" reading of one erlang; a value above the number of channels is possible
as offered traffic, just not as carried traffic.
-->

---

# Traffic engineering vocabulary

- **BHT** — Busy Hour Traffic: offered/carried traffic during the network's busiest hour
- **BHCA** — Busy Hour Call Attempts
- **BHCC** — Busy Hour Call Completions
- **CPS** — Calls Per Second
- **AHT** — Average Hold Time (mean service/holding time, $1/\mu$)

<div class="pt-6 vsb-muted">

Networks are dimensioned for the **busy hour**, not the daily average — a link sized for average load would be overloaded every peak.

</div>

<!--
These are the traffic-engineering names for quantities already introduced with different labels: BHCA/CPS are
arrival-rate measurements, AHT is 1/μ. Dimensioning for the busy hour is the same idea as designing a road for
rush-hour traffic, not the 24-hour average.
-->

---

# Erlang B — the loss formula

<div class="pt-2 text-2xl">

$$
E_B(A,N) = \frac{\dfrac{A^N}{N!}}{\displaystyle\sum_{i=0}^{N}\dfrac{A^i}{i!}}
$$

</div>

$A$ — offered traffic \[Erl\] · $N$ — number of channels · $E_B$ — probability an arriving call is **blocked**

<div class="pt-4 text-sm vsb-muted">

Assumes Poisson arrivals, an **infinite population** of sources, and **no waiting positions** (M/M/N/N). [erlang.com/calculator/erlb](https://www.erlang.com/calculator/erlb/)

</div>

<!--
Blocked calls are simply lost under this model — no retry, no overflow, unless the surrounding system explicitly
adds one. Grade of service (GoS) targets, such as "block no more than 1% of calls", are stated as a target E_B.
-->

---

# Erlang B — worked example

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

$N=3$ trunks, offered traffic $A=1.5$ Erl:

$$
\frac{A^i}{i!}:\quad 1,\ 1.5,\ 1.125,\ 0.5625 \quad (i=0..3)
$$

$$
E_B = \frac{0.5625}{1+1.5+1.125+0.5625} = \frac{0.5625}{4.1875}
$$

</div>
<div v-click>

<div class="vsb-fill">

### $E_B \approx 13.4\%$

about one call in seven is blocked

</div>

<div class="pt-4 text-sm vsb-muted">

Adding a 4th trunk (A still 1.5 Erl) drops $E_B$ to about 4.2% — diminishing blocking, not diminishing traffic.

</div>

</div>
</div>

<!--
Walk the sum term by term on the board. The 4th-trunk figure is worth stating to show that Erlang B does not
scale linearly with N — small increases in capacity near saturation buy large drops in blocking, which is the
whole logic of trunk dimensioning.
-->

---

# Checkpoint — what if blocked calls didn't hang up?

<div class="checkpoint-question">

Erlang B assumes a blocked call is simply lost. What would have to change about the system for a blocked call to **wait** instead — and what happens to the formula's denominator once waiting is allowed?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**The system needs somewhere to put a waiting call — unlimited waiting positions instead of none.**

That single change turns M/M/N/N (Erlang B) into M/M/N (Erlang C): callers beyond the $N$ busy servers are held, not dropped. The next two slides build exactly that formula.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. This primes Erlang C as "Erlang B's
system with a queue added" before the formula appears, rather than as an unrelated new expression to memorize.
-->

---

# Erlang C — the waiting-time formula

<div class="pt-2 text-xl">

$$
E_C(A,N) = \frac{\dfrac{A^N}{N!}\cdot\dfrac{N}{N-A}}{\displaystyle\sum_{i=0}^{N-1}\dfrac{A^i}{i!} + \dfrac{A^N}{N!}\cdot\dfrac{N}{N-A}}
\qquad\qquad
t_c = \frac{t_{os}\cdot E_C}{N-A}
$$

</div>

$E_C$ — probability an arriving call must **wait** · $t_{os}$ — mean holding time \[s\] · $t_c$ — mean wait, **averaged over all calls**

<div class="pt-4 text-sm vsb-muted">

Assumes blocked calls **stay in the system** until served, with unlimited waiting room (M/M/N). [erlang.com/calculator/erlc](https://www.erlang.com/calculator/erlc/)

</div>

<!--
For N=1, Erlang C reduces to the M/M/1 formulas from Part 3: t_c becomes ρ/(μ−λ)=Wq. Requires A<N for a steady
state, same stability idea as ρ<1 in M/M/1. t_c mixes over both the callers who wait and those who don't (who
wait zero), which is why it needs the extra E_C factor compared to a "mean wait given that you wait" figure.
-->

---

# Erlang C — worked example

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

Same $N=3$, $A=1.5$ Erl scenario, now with unlimited waiting (M/M/3):

$$
\frac{A^N}{N!}\cdot\frac{N}{N-A} = 0.5625\cdot\frac{3}{1.5}=1.125
$$

$$
E_C = \frac{1.125}{(1+1.5+1.125)+1.125} = \frac{1.125}{4.75}
$$

</div>
<div v-click>

<div class="vsb-fill">

### $E_C \approx 23.7\%$

with mean holding time $t_{os}=3$ min:

$$
t_c = \frac{3\cdot0.237}{1.5} \approx 0.47\ \mathrm{min} \approx 28\ \mathrm{s}
$$

</div>

</div>
</div>

<!--
Same A and N as the Erlang B example, so the two results are directly comparable: the loss system (Erlang B)
blocks 13.4% of calls outright, while the queueing system (Erlang C) makes 23.7% of calls wait, averaging 28 s
across all callers. Neither number is "better" in the abstract — it is a design choice between losing traffic
and making it wait. README Question 1 uses different numbers deliberately; do not pre-solve it here.
-->

---

# The Engset model

<div class="pt-2 text-2xl">

$$
E_N(\alpha) = \frac{\dbinom{s-1}{N}\alpha^N}{\displaystyle\sum_{i=0}^{N}\dbinom{s-1}{i}\alpha^i}
$$

</div>

$s$ — number of traffic sources (finite population) · $N$ — number of channels · $\alpha$ — offered traffic **per idle source**

<div class="pt-4">

Erlang B assumes an **infinite** population, so a busy source never "uses up" a potential arrival. With only $s$ sources, a source already in a call **cannot** also be generating a new one — Engset accounts for this, and is more accurate for **low-traffic** scenarios with few sources.

</div>

<div class="pt-2 text-sm vsb-muted">

Erlang B is the $s\to\infty$ limit of Engset. [erlang.com/calculator/engset](https://www.erlang.com/calculator/engset/)

</div>

<!--
This is Kendall's E parameter (population) made finite, connecting back to Part 1. A PBX serving 8 extensions
with 3 trunks is a textbook Engset scenario: 8 is nowhere near infinite. Do not derive the binomial-coefficient
formula in class; state the assumption and point at the calculator.
-->

---

# Checkpoint — loss or wait?

<div class="checkpoint-question">

A call centre wants to know whether to add a third agent or upgrade its phone system to put overflow calls on hold. Which formula answers which question — Erlang B or Erlang C?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Both are legitimate designs, computing different things.**

**Erlang B** (no hold queue): with 2 agents, what fraction of callers gets a busy signal? **Erlang C** (calls held): with 2 agents and a hold queue, what fraction of callers wait, and how long on average? "Add a third agent" changes $N$ in either formula; "put callers on hold" is the choice between the two models, not a formula parameter.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. The point is that the formula
choice encodes a design decision (lose the call or make it wait), not just a parameter choice.
-->

---

# Notation cheat-sheet

<div class="grid grid-cols-2 gap-x-10 text-sm">
<div>

| Symbol | Meaning | Introduced |
|---|---|---|
| $\lambda$ | Arrival rate \[s$^{-1}$\] | Part 1 |
| $\mu$ | Service rate \[s$^{-1}$\] | Part 1 |
| $\rho$ | Utilization = $\lambda/\mu$ (M/M/1) | Part 3 |
| $L$, $L_q$ | Mean number in system / in queue | Part 3 |
| $W$, $W_q$ | Mean time in system / in queue | Part 3 |

</div>
<div>

| Symbol | Meaning | Introduced |
|---|---|---|
| $A$ | Offered traffic \[Erl\] ($=N\rho$ for $N$ servers) | Part 4 |
| $N$ | Number of servers / channels | Parts 1, 4 |
| $E_B$, $E_C$ | Erlang B blocking / Erlang C waiting probability | Part 4 |
| $s$ | Number of traffic sources (Engset) | Part 4 |
| $\alpha$ | Offered traffic per **idle** source (Engset) | Part 4 |

</div>
</div>

<div class="pt-6 vsb-muted text-sm">

$A$ and $\rho$ both mean "offered traffic" — $\rho$ is the M/M/1 name for it, $A$ is the general telephony name used once there may be several servers.

</div>

<!--
A reference slide, not new content — read it aloud once and let students photograph it. A and α are the pair
most often confused: A is total offered traffic across the whole group, α is traffic per single idle source.
-->

---

# Common mix-ups

<div class="grid grid-cols-2 gap-6 pt-2">
<div class="border border-orange-400 p-4">

**$\rho=\lambda/\mu$ vs. $\rho=A/k$**

The M/M/1 formulas for $L$, $W$, $L_q$, $W_q$ assume **one** server. With $k$ servers, utilization is $A/k$, and the M/M/1 occupancy/delay formulas do not apply directly — see Extras.

</div>
<div class="border border-orange-400 p-4">

**Erlang B vs. Erlang C**

Same-looking formulas, different systems: B assumes **no** waiting room (blocked = lost); C assumes **unlimited** waiting room (blocked = delayed). Check which one a problem describes before reaching for either.

</div>
<div class="border border-orange-400 p-4">

**Convert units before you add**

Little's law worked example mixed ms, s, and min on purpose — mixing units silently is the single most common arithmetic error with these formulas.

</div>
<div class="border border-orange-400 p-4">

**$\lambda$ is the *admitted* rate**

In Little's law and in $\rho=\lambda/\mu$, $\lambda$ counts requests that actually **enter** the system. Blocked or lost traffic does not count toward it.

</div>
</div>

<!--
Four errors seen most often when marking this material: (1) applying L=ρ/(1-ρ) to a multi-server port,
(2) reaching for Erlang B when a problem clearly describes callers on hold (or vice versa), (3) forgetting to
convert minutes/seconds/milliseconds to a common unit before multiplying, (4) using offered rather than
admitted arrival rate when a system has non-negligible loss. Read these once, quickly, right before the summary.
-->

---

# Summary — six formulas to keep

<div class="grid grid-cols-2 gap-x-10 gap-y-2 pt-2">

<div>

**Little's law** — any stable system
$$ L = \lambda W $$

**M/M/1 utilization**
$$ \rho = \lambda/\mu $$

**M/M/1 occupancy and delay**
$$ L = \frac{\rho}{1-\rho} \qquad W=\frac{1}{\mu-\lambda} $$

</div>
<div>

**Poisson counting**
$$ P(N{=}k)=\frac{(\lambda t)^k}{k!}e^{-\lambda t} $$

**Erlang B** — loss system
$$ E_B(A,N)=\dfrac{A^N/N!}{\sum_{i=0}^{N} A^i/i!} $$

</div>

</div>

<div class="pt-2 vsb-muted">

A steady state needs $\rho<1$ (M/M/1) or $A<N$ (Erlang C). Kendall's notation says which model applies before any formula is chosen.

</div>

<!--
Read them aloud, one sentence each. Then the exit questions.
-->

---

# Exit questions — use the ideas

1. In Kendall's notation, what changes between M/M/1 and M/D/1, and which formulas from this lecture still apply?
2. Why does a memoryless service-time model make the M/M/1 formulas tractable?
3. Does doubling the arrival rate $\lambda$ (at fixed $\mu$) double the mean delay $W$?
4. A trunk group blocks too many calls. Name two independent ways to reduce $E_B$.

<div v-click class="pt-5 vsb-muted">

**Explain the assumptions**, not just the formula.

</div>

<!--
Allow two minutes for individual answers, then discuss. Answers: (1) Only C=1 and A=M stay the same; the M/M/1
L/W/Wq formulas assume exponential service and do not apply to M/D/1, though Little's law and ρ=λ/μ still do.
(2) The system's future depends only on its current state (number present), not on elapsed service time — a
Markov chain. (3) No: W=1/(μ−λ) is nonlinear in λ, diverging as λ→μ. (4) Add channels (increase N) or reduce
offered traffic A (reduce λ or the mean holding time). These lead into the exercise and README Question 1.
-->

---

# Exercise 02 — what you will do

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

1. **Generate random samples** — uniform, exponential, and normal distributions; compare histograms with theory.
2. **Source and sink** — one `PacketSource`, then several, feeding a `PacketSink` directly.
3. **Source, switch, sink** — a buffered `SwitchPort`; record dropped packets as rate or buffer shrink.
4. **Network tap and M/M/1** — measure occupancy and delay against the analytical formulas, and check Little's law.

</div>
<div>

Then the README questions:

- a payphone under Erlang C — is a second line needed?
- $\lambda$, $\mu$, $\rho$, and $W$ vs $W_q$ in Step 4
- why delay explodes as $\rho \to 1$
- which sampled distribution is memoryless, and why it matters

<div class="pt-4 text-sm vsb-muted">

```bash
ssh <lab-server>
cd qos-02 && uv sync
uv run jupyter lab --ip 0.0.0.0
```

</div>
</div>
</div>

<!--
All README questions were touched somewhere in this deck; question 1 specifically needs Erlang C from Part 4,
not just the M/M/1 formulas from Part 3, because it asks whether waiting time stays under a target — read the
payphone as "is one line an M/M/1 queue with Wq under 3 minutes, or does it need a second line".
-->

---

# References — foundations

- D. G. Kendall, "Stochastic Processes Occurring in the Theory of Queues and their Analysis by the Method of the Embedded Markov Chain," *Annals of Mathematical Statistics*, 24(3), 338–354, 1953.
- J. D. C. Little, "A Proof for the Queuing Formula: $L=\lambda W$," *Operations Research*, 9(3), 383–387, 1961.
- A. K. Erlang, "The Theory of Probabilities and Telephone Conversations," 1909.
- A. K. Erlang, "Solution of some Problems in the Theory of Probabilities of Significance in Automatic Telephone Exchanges," 1917.
- T. O. Engset, "On the Calculation of Switches in an Automatic Telephone System," manuscript 1918 (English translation, *Telektronikk*, 1998).
- L. Kleinrock, *Queueing Systems, Volume I: Theory*. Wiley, 1975.

<!--
Primary sources for Kendall notation, Little's law, and the three erlang formulas. Kendall's paper is the
origin of the notation this lecture builds on; further reading, not prerequisites for Exercise 02.
-->

---

# References — explanations and applications

- D. Gross, J. F. Shortle, J. M. Thompson, and C. M. Harris, *Fundamentals of Queueing Theory*, 4th ed. Wiley, 2008.
- Erlang traffic calculators: [Erlang B](https://www.erlang.com/calculator/erlb/) · [Erlang C](https://www.erlang.com/calculator/erlc/) · [Engset](https://www.erlang.com/calculator/engset/).
- G. Bernstein, "Discrete Event Simulation in Python," Grotto Networking — origin of the SimPy components used in Exercise 02.
- SimPy documentation, [simpy.readthedocs.io](https://simpy.readthedocs.io/).

<!--
The erlang.com calculators are the same ones cited in the source deck; they are useful for checking the two
worked examples in Part 4 by hand.
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
## M/M/k, simulation components, and the erlang formulas' history

<!--
Not part of the timed 90-minute route. Use to answer questions or extend an advanced class.
-->

---

# Extras — from one server to many: M/M/k

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

With $k$ identical servers instead of one, offered traffic $A=\lambda/\mu$ spreads across all of them:

$$
\rho = \frac{A}{k}
$$

The M/M/1 formulas for $L$, $W$, $L_q$, $W_q$ from Part 3 **do not apply directly** — M/M/k has its own (more involved) steady-state formulas, related to the Erlang C expression from Part 4.

</div>
<div>

**A common mix-up:** doubling the number of servers at fixed total offered traffic is **not** the same as doubling $\mu$ for one server — the two servers can each be idle while the other queues, unlike a single faster server.

M/M/k with **no** waiting room is exactly the Erlang B system (M/M/k/k); M/M/k with unlimited waiting room is exactly the Erlang C system.

</div>
</div>

<!--
Connects Parts 3 and 4 explicitly: Erlang B/C are M/M/k in Kendall's notation, just examined through their
blocking/waiting probabilities rather than through L and W directly. Full M/M/k occupancy/delay formulas are
beyond this course; point interested students at Kleinrock or Gross & Harris.
-->

---

# Extras — the simulation building blocks

| Component | Role |
|---|---|
| `PacketSource` | Generates packets with specified sizes and inter-arrival times |
| `SwitchPort` | Buffers waiting packets and transmits one packet at a fixed bit rate |
| `Switch` | Groups several ports |
| `PacketSink` | Records the elapsed time from packet creation to reception |
| `NetworkTap` | Samples system occupancy in packets, including a packet in service |
| `PacketFork` | Sends each packet to one of several destinations with given probabilities |

<div class="pt-4 text-sm vsb-muted">

Components connect through a `destination` attribute; sizes and intervals may be a number or a zero-argument callable, e.g. `partial(rng.exponential, 2)`.

</div>

<!--
This table mirrors qos-02/README.md exactly — use it to orient students inside lib/core.py before they start
Step 1. One simulation time unit (STU) represents one second throughout the exercise.
-->

---
class: compact-table
---

# Extras — Erlang's and Engset's papers

| Year | Author | Contribution |
|---|---|---|
| 1909 | A. K. Erlang | *The Theory of Probabilities and Telephone Conversations* — proves the Poisson distribution applies to random telephone traffic |
| 1917 | A. K. Erlang | *Solution of some Problems...* — the classic loss (Erlang B) and waiting-time (Erlang C) formulas |
| 1918 | T. O. Engset | Finite-source loss formula, independently derived; published in English only in 1998 |
| 1953 | D. G. Kendall | The A/B/C queueing notation used throughout this lecture |

<div class="pt-4 text-sm vsb-muted">

Erlang worked at the Copenhagen Telephone Company; the erlang (Erl) traffic unit is named for him in 1946 by the CCIF (a predecessor of today's ITU-T).

</div>

<!--
Optional history. Engset's priority is a good example of near-simultaneous independent discovery in applied
mathematics — his formula predates wide publication by decades because it appeared only in Norwegian and German
technical reports until the 1998 translation.
-->

---

# Extras — computing Erlang B by hand

<div class="pt-2 text-2xl">

$$
E_B(0,A) = 1, \qquad E_B(N,A) = \frac{A\cdot E_B(N-1,A)}{N + A\cdot E_B(N-1,A)}
$$

</div>

<div class="pt-4">

Equivalent to the closed form on the earlier slide, but computed by **one multiplication and one division per step** instead of two large factorial sums — no term ever grows past 1.

</div>

<div class="pt-4 text-sm vsb-muted">

$N=3$, $A=1.5$: $E_B(0){=}1 \to E_B(1){=}0.6 \to E_B(2){\approx}0.310 \to E_B(3){\approx}0.134$ — matches the worked example.

</div>

<!--
This is the recursion actually used in traffic-engineering software and spreadsheets, since A^N/N! overflows
for large N long before E_B does. It also makes the "diminishing blocking" claim from the worked example
mechanical: each step only ever shrinks the previous value, so adding trunks always helps, just by less and less.
-->

---

# Extras — Little's law, decomposed

Subtracting the queue-only form of Little's law from the system-wide form:

$$
L - L_q = \lambda(W-W_q) = \lambda\cdot\frac{1}{\mu} = \rho
$$

The gap between system and queue occupancy is exactly $\rho$: the mean number of requests **in service** at any instant — the algebraic step behind the delay-decomposition figure shown in Part 3.

<!--
Useful as a written sanity check when comparing a NetworkTap's system-count reading against a hand calculation
of L and Lq separately: their difference should sit close to ρ=λ/μ.
-->
