---
theme: seriph
title: 04 · Network traffic modelling
info: |
  440-2216/01 Kvalita služeb — lecture 4.
  Time-domain traffic distributions (exponential, Weibull, jitter), Markov-chain packet-loss models from
  Bernoulli through the four-state model, and self-similarity / long-range dependence in measured network
  traffic.
exportFilename: 04-network-traffic-modelling
layout: cover
transition: slide-left
mdc: true
lineNumbers: true
fonts:
  provider: none
  sans: Carlito
  mono: IBM Plex Mono
---

# Network Traffic Modelling

### 440-2216/01 Kvalita služeb · Lecture 04

<div class="pt-6 text-sm vsb-muted">
Jan Rozhon, Miroslav Vozňák &middot; Department of Telecommunications, FEECS
</div>

<!--
Ninety minutes including checkpoints: 5 min framing, 15 min time-domain distributions (exponential, Weibull,
jitter), 35 min Markov-chain loss models (Bernoulli through the four-state model, with a simulated convergence
example), 25 min self-similarity and the Hurst parameter, 10 min summary/exit questions. Lecture 02 built the
Poisson/M/M/1 vocabulary; this lecture asks a different question — is the Poisson assumption even correct, and
what do we reach for when it is not, both for inter-arrival times and for the errors a channel produces?
-->

---

# Where we are going

<div class="grid grid-cols-3 gap-4 pt-4 text-sm">

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 1</div>

### Time-domain distributions

Exponential, Weibull, and jitter as Normal

<div class="text-xs opacity-60 pt-2">↔ Lecture 02's Poisson process</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 2</div>

### Markov loss models

Bernoulli → Simple Gilbert → Gilbert → Gilbert-Elliott → 4-state

<div class="text-xs opacity-60 pt-2">↔ increasing memory, increasing parameters</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 3</div>

### Self-similarity

The Hurst parameter and long-range dependence

<div class="text-xs opacity-60 pt-2">↔ why "just use Poisson" fails</div>
</div>

</div>

<div class="pt-6">

One question runs through the lecture: **when does the convenient model (memoryless, independent, Gaussian-tailed) stop matching what a real network actually produces?**

</div>

<!--
Each part adds a kind of memory the previous one lacked: Part 1 picks a distribution shape for one random
quantity; Part 2 adds state (memory between consecutive events); Part 3 asks what happens when that memory
never really dies out, at any time scale.
-->

---

# What you should be able to do

1. Name which quantity each of the exponential, Weibull, and Normal distributions models in network traffic, and why each departs from the simplest available choice.
2. Draw and parametrize the Bernoulli, Simple Gilbert, Gilbert, Gilbert-Elliott, and four-state Markov loss models, and explain what capability each new parameter buys.
3. Define the Hurst parameter and explain what "self-similar" traffic means and why it survives aggregation where a Poisson process does not.
4. Explain why long-range-dependent traffic breaks the delay and buffer-sizing intuition built from Lecture 02's M/M/1 formulas.

<div class="pt-6 vsb-muted">

Keep asking: **does this model still produce independent, short-memory behaviour — or does it now remember its own past?**

</div>

<!--
Four outcomes for the lecture. Students need Lecture 02's Poisson process, exponential inter-arrivals, and the
M/M/1 delay formula W = 1/(μ−λ) as a baseline "memoryless" model to contrast against everything here.
-->

---
layout: statement
---

# Real traffic looks random at every time scale you look at it

## Modelling it well means choosing the right statistical *structure* — not just the right average

<!--
This is the thesis the whole lecture supports. Part 1 already complicates "just use the mean"; Part 2 adds
memory between consecutive outcomes; Part 3 shows that memory can persist across every time scale
simultaneously, which no single Markov chain with finitely many states can produce.
-->

---
layout: section
---

# Part 1
## Time-domain traffic distributions

---

# Exponential distribution — the memoryless baseline

<img class="lecture-diagram" src="/figures/04/exp-pdf-cdf.svg" alt="Density and cumulative distribution of the exponential distribution with rate 1: the density decays monotonically from 1, the cumulative distribution rises from 0 towards 1." />

<div class="pt-2 text-sm">

Models packet, call, or session **inter-arrivals** for a Poisson process — exactly Lecture 02's arrival process. Most inter-arrival times are short; the (theoretically infinite) tail is where timeouts and packet drops live.

</div>

<!--
Direct continuation of Lecture 02: the Poisson arrival process has i.i.d. Exponential(λ) inter-arrival times.
This slide is the anchor the rest of Part 1 pushes against — Weibull generalizes it, and Part 3's self-similar
traffic breaks the independence assumption behind it entirely.
-->

---

# Weibull distribution — a better fit at scale

<img class="lecture-diagram" src="/figures/04/weibull-pdf.svg" alt="Weibull probability density for shape parameter k from 1 to 5 and scale 1: k equals 1 reproduces the exponential; larger k concentrates the density more tightly around x equals 1." />

<div class="pt-2 text-sm">

Also models packet, flow, or session inter-arrivals, but with a **shape parameter k** that the exponential lacks (k = 1 recovers it exactly). Arfeen et al. (2013) found it scales better than the exponential as traffic aggregates from access to core networks, and from packet to session level.

</div>

<!--
The pedagogical point: the exponential is a special case, not a law of nature. Whether inter-arrivals look
closer to k=1 or k>1 depends on where in the network — and at what level of aggregation — you are measuring.
This is a preview of Part 3, where aggregation itself starts to matter even more.
-->

---

# Normal distribution — jitter

<img class="lecture-diagram" src="/figures/04/normal-jitter.svg" alt="Density and cumulative distribution of a zero-mean, unit-variance Normal distribution used to model jitter: the density is symmetric and bell-shaped." />

<div class="pt-2 text-sm">

Models the **distribution of packet delay variation (jitter)** for a single flow — not inter-arrival times, but how much each packet's delay deviates from the flow's typical delay. Symmetric around zero, unlike the one-sided exponential and Weibull above.

</div>

<div class="pt-2 vsb-muted text-sm">

A playout buffer's size is chosen against this distribution's tail, not its mean.

</div>

<!--
Jitter is the one quantity in Part 1 that is naturally two-sided (a packet can arrive early or late relative to
the expected schedule), which is why it gets its own distribution family instead of reusing the exponential or
Weibull.
-->

---

# Checkpoint — why not just use the exponential everywhere?

<div class="checkpoint-question">

The exponential distribution is simpler than the Weibull and has one fewer parameter to fit. Why does this lecture bother introducing the Weibull at all?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Because measured inter-arrival times often are not memoryless.** The exponential's defining property — the memoryless property, $P(T>s+t \mid T>s) = P(T>t)$ — is a strong, testable assumption. Real traffic frequently deviates from it, especially as flows aggregate from individual packets up through sessions, and Arfeen et al. found the extra shape parameter k measurably improves the fit at exactly those aggregation points. Simplicity is not a substitute for matching the data.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. Foreshadows Part 3 — self-similar
traffic is an even more dramatic example of "the convenient model doesn't match the data," at the level of an
entire aggregated process rather than a single inter-arrival distribution.
-->

---
layout: section
---

# Part 2
## Markov-chain packet-loss models

---

# Markov chains

<div class="pt-2">

Probabilistic models often used to simulate losses in both telco and packet networks — named for **Andrey Markov**, whose first paper on the topic appeared in 1906.

</div>

<div class="pt-4 text-sm">

**Features:**

- generate a sequence of possible events from a **finite set of states**,
- states are interconnected by **transition probabilities**,
- the current event depends **only on the state attained at the previous event** — no longer memory than that,
- can reach a **steady state**, where the outcome sequence no longer depends on where the model started.

</div>

<div class="pt-4 vsb-muted text-sm">

Related tools built on the same idea: **Erlang models** (Lecture 02) and **(Hidden) Markov models**.

</div>

<!--
This is exactly one step more memory than the exponential distribution's inter-arrival process: instead of
every event being independent, each state depends on the immediately preceding one. The five models on the
following slides differ only in how many states and emission probabilities they add on top of this idea.
-->

---

# Packet loss — Bernoulli model

<img class="lecture-diagram" src="/figures/04/bernoulli-model.svg" alt="Two-state diagram: Transmit and Loss, connected symmetrically with transition probability p into Loss and 1 minus p into Transmit, from either state." />

<div class="pt-2 text-sm">

The simplest loss model: just two states and a **single independent variable p**. Every transition into Loss happens with probability p regardless of the current state — losses are **completely independent** of one another.

</div>

<!--
Emphasize: this is exactly an i.i.d. Bernoulli(p) process dressed up as a two-state chain — the "chain"
structure adds nothing here because both self-loop and cross-transition probabilities are identical regardless
of the current state. It is the baseline the next three models improve on by adding memory.
-->

---

# Packet loss — Simple Gilbert model

<img class="lecture-diagram" src="/figures/04/gilbert-simple-model.svg" alt="Two-state diagram: Transmit and Loss, with independent transition probabilities p from Transmit to Loss and q from Loss to Transmit." />

<div class="pt-2 text-sm">

A more elaborate version of the Bernoulli model, adding a **second independent variable q**. Because p and q can differ, the chain can now produce **consecutive loss events** that resemble the loss bursts seen in real networks — the Bernoulli model cannot do this at all.

</div>

<!--
The key conceptual jump from Bernoulli: p and q being independent parameters means the chain now has memory.
A small q (slow to leave Loss) produces long bursts; a large q produces short, isolated losses. This is the
first model in the lecture with genuine state-dependence.
-->

---

# Simple Gilbert model — convergence to steady state

<img class="lecture-diagram" src="/figures/04/gilbert-convergence.svg" alt="Two panels showing the empirical probability of Transmit and Loss over time for a simple Gilbert chain with p equals 0.8 and q equals 0.4, starting in Transmit and starting in Loss, both converging to the same steady-state probabilities." />

<div class="pt-2 text-sm">

With **p = 0.8, q = 0.4**, both panels converge to the same steady-state probabilities — $\pi_L = \frac{p}{p+q} \approx 0.667$ and $\pi_T = \frac{q}{p+q} \approx 0.333$ — regardless of which state the chain started in.

</div>

<!--
This is the "steady state" bullet from the Markov chains slide made concrete: long-run behaviour stops
depending on initial conditions. Point out that the fluctuation around the steady-state line never disappears —
it is a property of any finite stochastic realization, not evidence the chain hasn't converged.
-->

---

# Packet loss — Gilbert model

<img class="lecture-diagram" src="/figures/04/gilbert-model.svg" alt="The Simple Gilbert two-state diagram with an added emission probability h at the Loss state: even in Loss, a packet is transmitted correctly with probability h and lost with probability 1 minus h." />

<div class="pt-2 text-sm">

An advancement of the Simple Gilbert model, adding an **emission probability h** to the "bad" state. Even while the chain is in Loss, the system can still transmit an individual packet correctly — Loss now describes a state of **elevated risk**, not certain loss.

</div>

<!--
This decouples the chain's state (which models burst structure over time) from the packet-level outcome (which
is now itself probabilistic). It is a closer match to real link behaviour, where a "bad" radio or congested
period does not lose every single packet.
-->

---

# Packet loss — Gilbert-Elliott model

<img class="lecture-diagram" src="/figures/04/gilbert-elliott-model.svg" alt="The Gilbert two-state diagram with a second emission probability k added at the Transmit state: even in Transmit, a packet is lost with probability 1 minus k." />

<div class="pt-2 text-sm">

An advancement of the Gilbert model, adding a **second emission probability k** to the "good" state. Even while the chain is in Transmit, the system can still lose a packet — both states now carry their own independent emission probability.

</div>

<!--
Four free parameters now (p, q, h, k) fully decouple "how long a bad period lasts" from "how bad the bad
period actually is" — the most flexible two-state model in the family, at the cost of needing four numbers
fitted from data instead of one. Worth noting for anyone who reads further: this is the most commonly cited
two-state loss model in the networking literature, and "Gilbert model" / "Gilbert-Elliott model" are sometimes
used loosely to mean either — check which emission probabilities a given paper actually assumes.
-->

---

# Packet loss — four-state model

<img class="lecture-diagram" src="/figures/04/four-state-model.svg" alt="Four states in a row: state 4 (Loss), state 1 (Transmit), state 3 (Loss), state 2 (Transmit), connected by transition arrows, with self-loops on states 3 and 2 only. State 4 always transitions to state 1 with probability 1 and never repeats itself." />

<div class="pt-2 text-sm">

The most advanced model in this group, with **no emission probabilities** at all — the state alone determines whether a packet is lost. Splitting each outcome into two states lets a **short, isolated event** (states 4 and 1) and a **sustained run** (states 3 and 2, which can self-loop) carry independently tunable durations.

</div>

<!--
The trade-off across this whole progression: Bernoulli (1 parameter, no memory) → Simple Gilbert (2 parameters,
one memory time constant per outcome) → Gilbert / Gilbert-Elliott (up to 4 parameters, memory plus per-state
risk) → four-state (6 parameters, independent burst-length and good-run-length distributions, but no
per-packet risk within a state). More parameters buy more realistic burst statistics at the cost of harder
estimation from measured traces.
-->

---

# Checkpoint — which model would you reach for?

<div class="checkpoint-question">

You have a measured trace where loss events cluster into bursts of noticeably variable length, and even within a burst, some packets still get through. Which of the five models fits best, and which two capabilities are you actually using?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**The Gilbert-Elliott model** is the natural minimum fit: you need state *memory* to produce bursts at all (ruling out Bernoulli), and you need an *emission probability* in the bad state to let some packets through during a burst (ruling out the Simple Gilbert model, which treats Loss as certain loss). Reach for the four-state model only if the burst-length and good-run-length distributions themselves need independent shapes — that model buys duration flexibility, not per-packet risk.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. The point is matching model
complexity to what the data actually shows, not defaulting to the most complex model available.
-->

---
layout: section
---

# Part 3
## Self-similarity and long-range dependence

---

# Why the Poisson process isn't enough

<div class="pt-2">

A Poisson process is **bursty on a fine time scale** but **flattens (smooths) on a coarse time scale** — averaged over long enough windows, it looks like white noise. Real network traffic does not do this: it stays visibly bursty however far you zoom out.

</div>

<div class="pt-4">

**How do you keep burstiness across a wide range of time scales?** Self-similarity.

</div>

<div class="pt-4 text-sm vsb-muted">

Features: slow decay of autocorrelation, and **scale-invariance** — the process "looks the same," statistically, whatever time scale it is viewed at.

</div>

<!--
This directly follows from the Central Limit Theorem applied to aggregation: summing many independent
increments smooths toward a Gaussian/white-noise shape. Self-similar traffic defeats this because its
increments are not independent enough for the CLT's smoothing to take hold — the next slide gives the
mechanism.
-->

---

# Where self-similarity comes from

<div class="pt-2 text-sm">

The classical explanation (Willinger, Taqqu, Sherman & Wilson, 1997): aggregate traffic is the **superposition of many independent ON/OFF sources** — think individual users or flows, each alternating between sending and idle periods.

</div>

<div class="pt-4 grid grid-cols-2 gap-6 text-sm">
<div class="border border-gray-400 p-4">

**If ON/OFF durations were light-tailed** (e.g. exponential)

the Central Limit Theorem smooths the sum — the aggregate looks Poisson-like at coarse scales, exactly like Lecture 02's arrival process.

</div>
<div class="border border-gray-400 p-4">

**If ON/OFF durations are heavy-tailed** (Pareto, infinite variance)

occasional very long ON or OFF periods keep contributing noticeable structure at every aggregation level — the sum stays self-similar.

</div>
</div>

<!--
This is the answer to the previous slide's question, and it is the piece of the story the original course
material does not spell out. "Heavy-tailed" here specifically means a Pareto shape parameter α between 1 and
2 (finite mean, infinite variance); the resulting Hurst parameter works out to H = (3 − α) / 2, so α close to 1
produces H close to 1 — highly self-similar traffic.
-->

---

# The Hurst parameter

<div class="pt-2 text-sm">

Introduced by **Harold Hurst (1965)** — a measure of "burstiness," also considered a measure of self-similarity.

</div>

<div class="grid grid-cols-2 gap-6 pt-4 text-sm">
<div>

- $0 < H < 1$
- H increases as traffic becomes **more self-similar**
- **white noise has H = 0**
- measures **long-term dependence** of the process

</div>
<div>

- a parameter of an **infinite series** — for any trace of finite length, it must be **estimated**, not computed exactly
- $H > 0.5$ indicates **long-range dependence (LRD)**: correlations that decay so slowly their sum diverges

</div>
</div>

<!--
H = 0.5 is the boundary case (uncorrelated increments, like ordinary Brownian motion); H > 0.5 is the
long-range-dependent regime real traffic traces consistently fall into, typically in the 0.7–0.9 range for
measured Ethernet and WAN traffic. Estimation methods (R/S statistic, variance-time plots, wavelet-based
estimators) are in Extras.
-->

---

# Self-similar traffic across aggregation levels

<img class="lecture-diagram" src="/figures/04/self-similar-traffic.svg" alt="Four bar-chart panels of a synthetic self-similar trace, zoomed from 1 fine time bin per bar up to the whole trace aggregated into about 328 bins per bar, all four remaining visibly bursty." />

<div class="pt-2 text-sm">

A synthetic trace built exactly as the previous slide describes — many ON/OFF sources with Pareto-distributed periods — stays bursty from the finest bin up to the whole trace aggregated into roughly 328-bin blocks.

</div>

<div class="pt-1 vsb-muted text-sm">

Leland, Taqqu, Willinger & Wilson's 1994 Bellcore Ethernet measurements are the empirical result that made this phenomenon famous.

</div>

<!--
Compare directly against the Poisson-process figure from Lecture 02: aggregating that process's arrivals over
a wide enough window converges to a smooth rate. Nothing here converges — every panel shows comparable
relative variability, which is the operational definition of scale-invariance from two slides ago.
-->

---

# Why this matters for capacity planning

<div class="pt-2">

Lecture 02's queueing formulas — $W = 1/(\mu-\lambda)$, buffer occupancy from $\rho$ — assume **independent, Poisson-like arrivals**. Self-similar, long-range-dependent traffic violates that assumption directly.

</div>

<div class="pt-4 vsb-muted text-sm">

Paxson & Floyd's 1995 study, "Wide-Area Traffic: The Failure of Poisson Modeling," is the paper-length version of this point: measured WAN traffic systematically fails Poisson-process tests, and models that ignore this **under-predict** queueing delay and required buffer size.

</div>

<div class="pt-4 text-sm">

A link dimensioned from an M/M/1 formula calibrated only to the traffic's **mean rate** will be under-provisioned whenever $H$ is meaningfully above 0.5 — the sustained above-average periods that self-similarity produces are exactly what an independence-based formula cannot see coming.

</div>

<!--
This closes the loop back to Lecture 02 explicitly: the "queuing delay diverges as ρ→1" result from that
lecture assumed independent arrivals throughout. Self-similar traffic can produce that same delay blow-up at
utilizations well below 1, simply because sustained bursts look, locally, like a much higher arrival rate than
the long-run average.
-->

---

# Checkpoint — under-provisioned by how much?

<div class="checkpoint-question">

A link is dimensioned using an M/M/1 formula calibrated to match the traffic's long-run mean rate. The real traffic turns out to be self-similar with H ≈ 0.8. What happens to actual queueing delay relative to the M/M/1 prediction, and why?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Actual delay will run higher than the M/M/1 prediction**, often substantially. M/M/1 assumes independent arrivals, so it only ever "sees" the long-run mean rate. Self-similar traffic with H ≈ 0.8 has long-range dependence: sustained periods well above the mean rate are far more likely, and far longer-lived, than an independence-based model allows for — and it is precisely those sustained bursts that build up queueing delay and overflow buffers. The mean rate alone does not determine performance when H is well above 0.5.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. This is the practical payoff of
the whole lecture: matching a model's assumptions to the data is not academic — mismatched assumptions here
translate directly into under-provisioned links.
-->

---

# Common mix-ups

<div class="grid grid-cols-3 gap-4 pt-2 text-sm">
<div class="border border-orange-400 p-3">

**Exponential vs. Weibull**

Both model inter-arrivals. Exponential is memoryless and a special case (k = 1) of Weibull, which fits better once traffic aggregates.

</div>
<div class="border border-orange-400 p-3">

**Emission probability vs. transition probability**

p and q govern the *chain's* state. h and k govern whether an *individual packet* is lost, given the current state.

</div>
<div class="border border-orange-400 p-3">

**Steady state vs. self-similarity**

A Markov chain's steady state is a long-run *average*. Self-similarity is about variability *persisting* across time scales — the two are unrelated properties.

</div>
<div class="border border-orange-400 p-3">

**H = 0.5 vs. H = 0**

H = 0.5 is uncorrelated (Brownian-motion-like) traffic. H = 0 is white noise specifically. Neither is the self-similar regime — that needs H > 0.5.

</div>
<div class="border border-orange-400 p-3">

**More parameters ≠ automatically better**

The four-state model is not "more correct" than Gilbert-Elliott — it fits a different feature (independently shaped burst/run lengths) that not every trace needs.

</div>
</div>

<!--
Five confusions seen most often: (1) treating Weibull as an unrelated distribution rather than a generalization
of the exponential, (2) conflating a Markov chain's transition structure with its per-packet emission
probabilities, (3) assuming any Markov chain's convergence to steady state has something to do with
self-similarity, (4) misreading H=0.5 as the self-similar case rather than the boundary, (5) reaching for the
most complex loss model by default instead of matching model complexity to the data.
-->

---

# Summary — three layers of structure

<div class="grid grid-cols-2 gap-x-10 gap-y-2 pt-2 text-sm">

<div>

**Time-domain distributions**
Exponential (memoryless, k=1 baseline), Weibull (shape parameter, better fit at scale), Normal (two-sided, models jitter).

**Markov loss models add memory**
Bernoulli has none; Simple Gilbert adds a second transition probability; Gilbert and Gilbert-Elliott add emission probabilities for per-packet risk within a state.

</div>
<div>

**The four-state model separates duration from risk**
No emission probabilities — burst length and good-run length each get their own transition structure instead.

**Self-similarity is memory that never fully decays**
Long-range dependence (H > 0.5) breaks the independence assumption behind Lecture 02's queueing formulas, and under-predicts delay and buffer needs.

</div>

</div>

<!--
Read them aloud, one sentence each. Then the exit questions.
-->

---

# Exit questions — use the ideas

1. A vendor claims their access-network trace fits an exponential inter-arrival model better than a Weibull one. What would you check before believing that claim?
2. Sketch the state diagram of a loss process where losses are always isolated (never two in a row) but occur with fixed probability p. Which named model is this?
3. A colleague says "the chain reached steady state, so the traffic must be self-similar." What is wrong with this reasoning?
4. Two traces have the same mean arrival rate; one is Poisson, the other has H = 0.85. Which one needs a bigger router buffer to hit the same packet-loss target, and why?

<div v-click class="pt-5 vsb-muted">

**Explain the mechanism**, not just the name.

</div>

<!--
Allow two minutes for individual answers, then discuss. Answers: (1) check whether the memoryless property
actually holds at the aggregation level in question — Arfeen et al.'s point was specifically about
access-to-core scaling. (2) That is exactly the Bernoulli model — the state has no memory, so consecutive
losses are as independent as any other pair of outcomes; "isolated" just describes what memorylessness looks
like when p is small. (3) Steady state is a long-run average property of any ergodic Markov chain; self-
similarity is about variability persisting across time scales and needs an entirely different mechanism (e.g.
heavy-tailed ON/OFF superposition). (4) The H = 0.85 trace needs the bigger buffer — long-range dependence
produces sustained above-mean periods that a same-mean Poisson process essentially never does.
-->

---

# Where these models are used

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

This lecture is a modelling toolbox, not a hands-on exercise on its own — but every piece of it plugs directly into Exercise 02's `simpy`-based pipeline:

- `PacketSource`'s inter-arrival argument accepts **any zero-argument callable**, so an exponential, Weibull, or self-similar generator drops in unchanged.
- A Gilbert/Gilbert-Elliott loss process is a natural model for a lossy `SwitchPort`.

</div>
<div>

<div class="text-sm">

Nothing here requires new tooling — `functools.partial` around a NumPy RNG, exactly as Exercise 02 already uses for inter-arrival and size callables, is enough to try any distribution from Part 1 or 2.

</div>

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
Deliberately honest that this lecture has no dedicated exercise directory of its own, unlike Lectures 01–03 —
its content is meant to extend what Exercise 02's simulation pipeline already supports, not to introduce a new
notebook.
-->

---

# References — foundations

- P. A. P. Moran (ed.), A. K. Erlang's original traffic formulas; A. A. Markov, "Rasprostranenie zakona bol'shih chisel na velichiny, zavisyaschie drug ot druga" [Extension of the law of large numbers to dependent quantities], 1906.
- M. A. Arfeen, K. Pawlikowski, D. McNickle, A. Willig, "The Role of the Weibull Distribution in Internet Traffic Modeling," Proceedings of the 25th International Teletraffic Congress (ITC), 2013.
- H. E. Hurst, "Long-Term Storage Capacity of Reservoirs," Transactions of the American Society of Civil Engineers, 116, 1951 (the estimator later named the Hurst parameter).

<!--
Primary sources for the distribution shapes and the Hurst parameter's origin. Hurst's original work is
hydrological — reservoir storage, not network traffic — which is worth mentioning as a striking example of a
statistical tool crossing fields.
-->

---

# References — self-similarity and its consequences

- W. E. Leland, M. S. Taqqu, W. Willinger, D. V. Wilson, "On the Self-Similar Nature of Ethernet Traffic (Extended Version)," IEEE/ACM Transactions on Networking, 2(1), 1–15, 1994.
- W. Willinger, M. S. Taqqu, R. Sherman, D. V. Wilson, "Self-Similarity Through High-Variability: Statistical Analysis of Ethernet LAN Traffic at the Source Level," IEEE/ACM Transactions on Networking, 5(1), 71–86, 1997.
- K. Park, W. Willinger, "Self-Similar Network Traffic: An Overview," in *Self-Similar Network Traffic and Performance Evaluation*, Wiley, 2000.
- V. Paxson, S. Floyd, "Wide Area Traffic: The Failure of Poisson Modeling," IEEE/ACM Transactions on Networking, 3(3), 226–244, 1995.

<!--
The four papers that carry Part 3: Leland et al. is the famous Bellcore measurement study; Willinger et al.
supplies the ON/OFF superposition mechanism used two slides into Part 3; Park & Willinger's overview chapter is
where the original course material's second reference comes from; Paxson & Floyd is the queueing-consequences
paper cited on the capacity-planning slide.
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
## Estimating the Hurst parameter, and a model complexity ladder

<!--
Not part of the timed 90-minute route. Use to answer questions or extend an advanced class.
-->

---

# Extras — estimating H from a finite trace

<div class="pt-2 text-sm">

H is a parameter of an infinite series; every practical method **estimates** it from a finite measured trace.

</div>

<div class="pt-4 grid grid-cols-2 gap-6 text-sm">
<div class="border border-gray-400 p-4">

**Variance-time plot**

Aggregate the trace at increasing block sizes m and plot $\log(\mathrm{Var}(X^{(m)}))$ against $\log m$. Poisson-like traffic decays with slope −1; self-similar traffic decays more slowly, with slope $2H-2$.

</div>
<div class="border border-gray-400 p-4">

**Rescaled range (R/S) statistic**

Plot $\log(R/S)$ against $\log n$ for windows of length n. The slope of the resulting line is a direct estimate of H — Hurst's original 1951 method, from reservoir data.

</div>
</div>

<div class="pt-4 vsb-muted text-sm">

Both are simple to implement but biased on short traces; wavelet-based estimators are preferred in modern traffic-analysis tooling.

</div>

<!--
The variance-time plot is the most intuitive to derive on a whiteboard: it is exactly the self-similar-traffic
figure from Part 3, quantified — instead of eyeballing "does it still look bursty," you measure how fast the
variance falls as you aggregate.
-->

---

# Extras — the loss-model complexity ladder

| Model | Parameters | What the new parameter buys |
|---|---|---|
| Bernoulli | p | baseline — independent loss, no memory |
| Simple Gilbert | p, q | state memory → loss bursts |
| Gilbert | p, q, h | probabilistic recovery *within* a burst |
| Gilbert-Elliott | p, q, h, k | probabilistic loss *within* a good period too |
| Four-state | p₄₁, p₁₄, p₁₃, p₃₁, p₃₂, p₂₃ | independently shaped burst-length and good-run-length distributions |

<div class="pt-4 text-sm vsb-muted">

Fitting more parameters needs more data and a longer trace before the estimate is trustworthy — pick the simplest model that reproduces the burst statistics you actually measured, not the most elaborate one available.

</div>

<!--
Optional reference table. The general lesson generalizes past this lecture: every one of these models, and the
Weibull vs. exponential choice from Part 1, is a trade between fitting the data better and needing more data to
fit it reliably.
-->
