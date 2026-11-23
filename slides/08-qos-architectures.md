---
theme: seriph
title: 08 · QoS architectures in IP networks
info: |
  440-2216/01 Quality of Service — lecture 8.
  How quality of service is built end to end across many routers and domains: Integrated Services with RSVP
  (per-flow reservations, admission control, soft state) and Differentiated Services (DSCP marking at the edge,
  per-class behaviour in the core), and the trade-off between guarantees and scalability that separates them.
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
Jan Rozhon &middot; Department of Telecommunications, FEECS
</div>

<!--
Temporary deck for building the QosPathSim component; replaced by the full lecture.
-->

---

# RSVP along the path

<QosPathSim mode="rsvp" />

<!--
Test slide: RSVP view.
-->

---

# DiffServ along the path

<QosPathSim mode="diffserv" />

<!--
Test slide: DiffServ view (Task 4).
-->

---

# RSVP, smaller bottleneck in A

<QosPathSim mode="rsvp" :capacity-a="4" />

<!--
Test slide: refusal at C1 (temporary).
-->

---

# DiffServ, compact

<QosPathSim mode="diffserv" compact :initial-flows="12" />

<!--
Test slide: compact DiffServ view (temporary).
-->
