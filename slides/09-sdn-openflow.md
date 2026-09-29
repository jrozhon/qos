---
theme: seriph
title: 09 · Software-defined networking with OpenFlow
info: |
  440-2216/01 Quality of Service — lecture 9.
  Why software-defined networking (SDN) separates the control plane from the data plane, the SDN architecture and
  its interfaces, the OpenFlow switch model (flow tables, pipeline, groups, meters, ports, channel, messages), and a
  comparison of centralized OpenFlow control with the distributed VXLAN-EVPN data-centre fabric.
  Companion lecture to Lab 05.
exportFilename: 09-sdn-openflow
layout: cover
transition: slide-left
mdc: true
lineNumbers: true
fonts:
  provider: none
  sans: Carlito
  mono: IBM Plex Mono
---

# Software-Defined Networking with OpenFlow

### 440-2216/01 Quality of Service · Lecture 09

<div class="pt-6 text-sm vsb-muted">
Jan Rozhon &middot; Department of Telecommunications, FEECS
</div>

<!--
Ninety minutes including checkpoints: 15 min motivation and history, 15 min architecture and interfaces, 35 min
OpenFlow (switch model, pipeline, groups/meters, channel and messages, reactive set-up, QoS use), 17 min
OpenFlow vs VXLAN-EVPN, 8 min summary/exit questions/lab set-up. Lectures 03–06 treated the network as a given
set of queues and links and asked what quality it delivers. This lecture asks who decides how those queues and
links are used, and what changes when that decision moves out of each box into software. Lab 05 then inspects
exactly these flow tables in Mininet and Open vSwitch.
-->

---

# Where we are going

<div class="grid grid-cols-4 gap-4 pt-4 text-sm">

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 1</div>

### Why SDN

Limits of box-by-box control, the three planes, the road to SDN

<div class="text-xs opacity-60 pt-2">↔ Question 2</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 2</div>

### Architecture

Planes, northbound / southbound / east–west interfaces, SDN vs NFV

<div class="text-xs opacity-60 pt-2">↔ Steps 1, 3</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 3</div>

### OpenFlow

Flow tables, pipeline, groups, meters, ports, channel, messages

<div class="text-xs opacity-60 pt-2">↔ Step 5, Questions 2–3</div>
</div>

<div class="border border-gray-400 p-3">
<div class="text-xs opacity-60">Part 4</div>

### OpenFlow vs VXLAN-EVPN

Centralized flow programming vs a distributed BGP overlay

<div class="text-xs opacity-60 pt-2">background</div>
</div>

</div>

<div class="pt-6">

One question runs through the lecture: **where is the forwarding decision made, and what does that placement cost in scale, reliability, and delay?**

</div>

<!--
Parts 1–3 are the core of the original course material, extended with the history and the pipeline details
from the OpenFlow specification. Part 4 is new: it places OpenFlow next to the technology that actually runs most
data-centre fabrics today, so that students see SDN as one design point, not the only one.
-->

---

# What you should be able to do

1. Distinguish the data, control, and management planes and explain what SDN changes about their placement.
2. Describe the SDN architecture and the role of the northbound, southbound, and east–west interfaces; distinguish SDN from NFV.
3. Read an OpenFlow flow entry, trace a packet through a multi-table pipeline, and explain groups, meters, and reserved ports.
4. Explain the OpenFlow message types and the reactive flow set-up, and estimate its effect on the first packet of a flow.
5. Compare OpenFlow with VXLAN-EVPN in control-plane placement, scale, failure behaviour, and QoS handling.

<div class="pt-6 vsb-muted">

Keep asking: **which plane does this component belong to, and what happens to the traffic if it fails?**

</div>

<!--
Five outcomes. Prerequisites: Ethernet switching and IP routing at the level of a bachelor networking course,
DSCP and the token bucket from Lecture 03. No new mathematics beyond simple delay arithmetic.
-->

---
layout: statement
---

# SDN separates deciding where a packet goes from forwarding it

## and puts the deciding into software that sees the whole network

<!--
This is the thesis of the lecture. Everything that follows is either a consequence of that separation (a
standard interface to the switch, a controller that must scale and survive failures, a first packet that waits for
a decision) or an alternative that keeps the decision distributed (VXLAN-EVPN in Part 4).
-->

---
layout: section
---

# Part 1
## Why software-defined networking

---

# Three planes in every network device

<div class="grid grid-cols-3 gap-6 pt-4 text-sm">
<div class="border border-gray-400 p-4">

**Data plane**

Forwards, drops, queues, or rewrites each packet according to local tables. Works per packet, at line rate: **nanoseconds to microseconds**.

</div>
<div class="border border-gray-400 p-4">

**Control plane**

Computes the tables: routing protocols (OSPF, BGP), spanning tree, MAC learning. Reacts to events: **milliseconds to seconds**.

</div>
<div class="border border-gray-400 p-4">

**Management plane**

Configures devices and collects telemetry: CLI, SNMP, NETCONF. Operator-driven: **minutes to days**.

</div>
</div>

<div class="pt-6">

In a traditional router or switch all three planes share one chassis, one vendor, and one operating system.

</div>

<div class="pt-2 vsb-muted text-sm">

Kurose & Ross call the resulting data-plane operation *match plus action*: look up header fields, apply an action. SDN generalizes which fields may be matched and which program fills the table.

</div>

<!--
The time-scale separation is the reason the split is possible at all: the data plane must be fast and simple,
the control plane can afford to be slower and smarter. Kurose & Ross (Computer Networking, ch. 4.4 and 5.5) is the
textbook framing; Feamster, Rexford & Zegura's "The Road to SDN" uses the same three-plane vocabulary.
-->

---

# Traditional networks: control distributed in every box

<Figure src="/figures/09/planes.svg" alt="Left: three traditional devices, each with its own control and data plane, whose control planes exchange routing protocol messages. Right: three SDN switches with only a data plane, programmed over OpenFlow by one logically centralized controller." />

<div class="pt-2 text-sm">

In a traditional network, the forwarding state is the **emergent result** of many independent control planes running distributed protocols. In SDN, a controller with a **global view** computes it and installs it.

</div>

<!--
"Logically centralized" is the precise term: the controller may be a cluster of servers (Part 2), but it behaves
as one decision point. Note the contrast with a distributed routing protocol, where no single component ever
holds the whole network state — each router has its own link-state database and computes its own shortest paths.
-->

---

# Limitations of traditional networks

<div class="grid grid-cols-3 gap-4 pt-2 text-sm">
<div class="border border-orange-400 p-3">

**Limited scaling of operations**

Hundreds of devices configured one by one, each with its own CLI; policy is scattered over many configuration files.

</div>
<div class="border border-orange-400 p-3">

**Vendor lock-in**

Control software is bundled with the hardware; interoperability rests on whatever protocols the vendors chose to implement.

</div>
<div class="border border-orange-400 p-3">

**Slow innovation**

A new protocol needs standardization, then vendor implementation, then a hardware refresh — years (compare IPv6 with a mobile app release cycle).

</div>
<div class="border border-orange-400 p-3">

**Complicated resource migration**

A virtual machine or container that moves between hosts takes its addresses and policies with it; the network must follow within seconds.

</div>
<div class="border border-orange-400 p-3">

**Limited resource sharing**

Isolation by VLANs only: 4094 IDs, and no isolation of CPU, tables, or bandwidth between tenants or between production and experiments.

</div>
<div class="border border-orange-400 p-3">

**Hard to verify and debug**

No component knows the complete forwarding state, so questions such as "can host A reach host B?" have no single place to be answered.

</div>
</div>

<!--
The first five come from the original course slides. The sixth (verification) is the argument emphasized in the
Princeton and Stanford SDN courses: with a central view, reachability and loop-freedom can be checked before a
change is deployed (header space analysis, VeriFlow). The VLAN limit returns in Part 4 as the motivation for VXLAN.
-->

---

# The idea of SDN

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

**Separate the control plane from the data plane:**

- network elements become simple packet forwarders,
- one logically centralized program — the **controller** — computes the forwarding logic for all elements,
- the two are connected by an open, standardized interface.

</div>
<div>

<div class="vsb-fill">

### An old idea in telephony

Common Channel Signalling (SS7) moved call control out of the voice channel onto a separate signalling network, with central intelligence in the Intelligent Network (IN).

</div>

</div>
</div>

<div class="pt-6 vsb-muted text-sm">

SDN applies the same step to packet networks: decisions are made off the forwarding path, by software that can be replaced without replacing the switch.

</div>

<!--
The original slide asks "Remember the CCS signaling systems?" — this makes the analogy explicit. In-band (CAS)
signalling shared the voice channel; CCS/SS7 moved it to a separate network and allowed centralized service logic
(IN service control points). SDN's controller plays the role of the SCP; OpenFlow plays the role of the
signalling protocol between the controller and the switching element.
-->

---

# The road to SDN

<div class="text-sm">

| Year | Milestone | Contribution |
|---|---|---|
| 1990s | Active networks | programmable packet processing; no deployment path |
| 2003 | IETF ForCES | control/forwarding split in a router; new hardware needed |
| 2004 | RCP | central BGP route selection; limited to existing protocols |
| 2005 | 4D project | clean-slate decision / dissemination / discovery / data |
| 2007 | Ethane (Stanford) | central access-policy controller: the direct ancestor |
| 2008 | OpenFlow, NOX | open interface to existing switch tables; first network OS |
| 2013 | Google B4 | SDN-controlled inter-data-centre WAN in production |
| 2014 | P4 | programmable parser and match–action pipeline |

</div>

<!--
After Feamster, Rexford & Zegura, "The Road to SDN" (ACM Queue 2013 / CCR 2014), the standard history taught at
Princeton and Georgia Tech. The original slides list ForCES and RCP; the lesson is that OpenFlow succeeded where
ForCES did not because it asked vendors only to open an interface to tables they already had, not to build new
hardware. RCP showed the value of central decisions but was limited to what BGP could express.
-->

---
layout: section
---

# Part 2
## SDN architecture and interfaces

---

# Architecture — planes and interfaces

<Figure src="/figures/09/architecture.svg" alt="The application plane with routing, traffic engineering and policy applications talks to the control plane through the northbound API. Two controller instances are synchronized over an east-west interface and program five data-plane switches through the southbound API." />

<!--
One of many drawings of the architecture; RFC 7426 (SDN Layers and Architecture Terminology) gives the IRTF
reference model with separate control and management abstraction layers, and the ONF architecture (TR-521) a more
detailed one. The three-plane picture here is what every textbook shares.
-->

---

# SDN interfaces

<div class="grid grid-cols-3 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**Northbound interface (NBI)**

Between applications and the controller. Exposes topology, flows, and intents.

**Not standardized**; commonly REST or gRPC, specific to each controller (ONOS, OpenDaylight, Ryu).

</div>
<div class="border border-gray-400 p-4">

**Southbound interface (SBI)**

Between the controller and network elements; the ONF calls it the *Control–Data-Plane Interface* (CDPI).

**Standardized**: OpenFlow is the classic example; also P4Runtime, NETCONF/YANG, OVSDB, gNMI.

</div>
<div class="border border-gray-400 p-4">

**East–west interface**

Between controllers, to share state across domains or replicas.

Proposed as **SDNi** (IETF draft); in practice each controller cluster uses its own protocol (Raft, distributed stores).

</div>
</div>

<div class="pt-6 vsb-muted">

The southbound interface is where interoperability matters most: it is what lets one controller program switches from different vendors.

</div>

<!--
OpenFlow is the only southbound protocol that programs the forwarding tables directly and generically. NETCONF and
OVSDB configure the device (ports, queues, tunnels) rather than per-flow forwarding — Open vSwitch uses OVSDB for
configuration and OpenFlow for the flow tables side by side, which students see in Lab 05 (ovs-vsctl vs ovs-ofctl).
-->

---

# The controller — a network operating system

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

The controller maintains a **global network view** — topology, hosts, flows, statistics — and offers it to applications, much as an operating system abstracts hardware for programs.

- Topology discovery (LLDP via Packet-Out/Packet-In)
- Host tracking, path computation
- Flow-rule installation and consistency
- Statistics collection

</div>
<div class="text-sm">

| Controller | Origin | Language |
|---|---|---|
| NOX / POX | Nicira, Stanford | C++ / Python |
| Ryu | NTT | Python |
| Floodlight | Big Switch | Java |
| OpenDaylight | Linux Foundation | Java |
| ONOS | ON.Lab / ONF | Java |

</div>
</div>

<!--
"Network operating system" is the term of Gude et al., NOX (CCR 2008). ONOS and OpenDaylight are the two
carrier-grade open-source controllers; both are clusters, which is where the east-west interface of the previous
slide lives. Mininet's default controller in Lab 05 is a simple reference learning controller.
-->

---

# Challenges of a centralized controller

<div class="grid grid-cols-3 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**Scalability**

One controller must process every Packet-In and hold the whole network state.

Mitigation: eliminate redundant route computation, index affected switches for fast updates, partition the network (e.g. an IGP between partitions), proactive rules.

</div>
<div class="border border-gray-400 p-4">

**Reliability**

The controller is a potential single point of failure.

Mitigation: hot-standby and clustered controllers (OpenFlow master/slave roles), and switch fail modes that keep forwarding.

</div>
<div class="border border-gray-400 p-4">

**Consistency**

Replicas must agree on the network state, and each needs its own information feed.

Mitigation: distributed stores (Onix, ONOS); consistent-update schemes so that no packet sees a mix of old and new rules.

</div>
</div>

<div class="pt-6 vsb-muted text-sm">

"Logically centralized, physically distributed" is the answer of every production controller — at the price of the consistency problems of any distributed system.

</div>

<!--
Research references: Koponen et al., Onix (OSDI 2010); Levin et al., "Logically centralized? State distribution
trade-offs in SDN" (HotSDN 2012); Heller et al., "The controller placement problem" (HotSDN 2012); Reitblatt et
al., "Abstractions for network update" (SIGCOMM 2012) for consistent updates. The consistency problem is the same
one BGP solves in a different way — Part 4 comes back to it.
-->

---

# Advantages of SDN

<div class="grid grid-cols-2 gap-x-10 gap-y-3 pt-2 text-sm">
<div>

**Virtualization and resource sharing** — slices isolated down to CPU and table level; production and experiments can coexist on one network.

**No vendor lock-in** — commodity (white-box) switches, control software chosen separately.

**Rapid and continuous development** — the control logic evolves after the switch is bought, at software speed.

</div>
<div>

**Dynamic resource allocation** — a change in demand is reflected in forwarding within one control loop.

**Complete overview of the network** — easier debugging, verification, and monitoring from one place.

**Lower costs** — simpler hardware and centralized orchestration.

</div>
</div>

<div class="pt-6 vsb-muted text-sm">

Each advantage is a consequence of the same step: the decision logic is software with a global view, not firmware in each box.

</div>

<!--
Slicing across CPU/application level is the FlowVisor idea (Sherwood et al., 2009), which was how the GENI and
campus deployments ran research traffic next to production traffic — the original motivation in the 2008 OpenFlow
paper ("enabling innovation in campus networks").
-->

---

# SDN vs NFV — complementary, not competing

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**Software-Defined Networking**

Separates control from forwarding. Concerns **where packets go**: layers 2–4 of switches and routers.

Standards: ONF, IETF.

</div>
<div class="border border-gray-400 p-4">

**Network Function Virtualization**

Replaces monolithic middleboxes (firewalls, load balancers, IDS, NAT) with **software on commodity servers**, composed from modules.

Standards: ETSI NFV ISG (2012).

</div>
</div>

<div class="pt-4 text-sm">

Example of modular NFV: the Snort IDS = IP defragmenter + preprocessing + misuse-detection engine + logger; each module can be scaled or replaced on its own.

</div>

<div class="pt-4 vsb-muted text-sm">

Together: SDN steers traffic through a **service chain** of virtual functions that NFV instantiates on demand.

</div>

<!--
NFV works at layers 4–7 (the functions), SDN at layers 2–4 (the forwarding). The original slide's picture shows this
as highlighted layers of the OSI stack. Neither requires the other, but service function chaining (RFC 7665) is
where they meet.
-->

---

# Checkpoint — which interface?

<div class="checkpoint-question">

An operator writes an application that moves video traffic off a congested link. Which interfaces does its decision cross before the first switch changes its behaviour, and which of them is standardized?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**Two.** The application asks the controller through the **northbound** API (REST/gRPC, controller-specific, not standardized). The controller translates the request into flow entries and installs them through the **southbound** interface (e.g. OpenFlow Flow-Mod, standardized). If the controller is a cluster, the new state is also replicated east–west.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. The point: portability of the
application depends on the northbound API, which is exactly the one without a standard.
-->

---
layout: section
---

# Part 3
## OpenFlow

---

# OpenFlow

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

A protocol between a network element and an external controller for installing forwarding rules into the element's **flow tables**; it implements the southbound interface (CDPI).

- Proposed at Stanford in 2008 (McKeown et al.); specified by the ONF since 2011
- **No custom hardware needed**: flow tables (TCAM) were already in 2008 switches; the vendor only opens an interface to them
- The switch stays closed — only the communication interface is open

</div>
<div class="text-sm">

| Version | Year | Key addition |
|---|---|---|
| 1.0 | 2009 | single table, 12 match fields |
| 1.1 | 2011 | multiple tables, groups |
| 1.2 | 2011 | extensible matches (OXM), IPv6 |
| 1.3 | 2012 | meters, per-flow QoS; long-term support |
| 1.4 | 2013 | bundles, flow monitoring |
| 1.5.1 | 2015 | egress tables — last release |

</div>
</div>

<div class="pt-4 vsb-muted text-sm">

No new version since 2015; the ONF shifted to P4 and P4Runtime. OpenFlow **remains in active use**, above all in Open vSwitch.

</div>

<!--
Correction to the original slides: OpenFlow was first defined in 2008 by the Stanford group (the "Clean Slate"
program); the Open Networking Foundation was founded in 2011 and took over the specification from version 1.2.
Development has effectively stopped: 1.5.1 (2015) is the last published version, and ONF merged into the Linux
Foundation in 2023. OVS, OpenStack Neutron and Mininet (Lab 05, which uses OpenFlow 1.0 and 1.3) still use it daily.
-->

---

# The OpenFlow switch

<Figure src="/figures/09/openflow-switch.svg" alt="A controller connects over the OpenFlow channel, TCP port 6653 with optional TLS, to an OpenFlow switch. Inside the switch, packets pass from the ingress port through flow tables 0 to n to the egress port; flow entries may use a group table and a meter table." />

<div class="pt-2 text-sm">

Every OpenFlow switch has at least one **flow table**; the controller adds, modifies, and deletes entries in it. Optional **group** and **meter** tables extend what an entry can do.

</div>

<!--
This is the ONF specification's own decomposition (OpenFlow Switch Specification 1.5.1, section 2). The original
course picture (controller, OpenFlow client, flow table with rule/actions/statistics) is the OpenFlow 1.0 version
of the same model: one table, rule = match fields.
-->

---

# A flow entry

<Figure src="/figures/09/flow-entry.svg" alt="The seven parts of an OpenFlow 1.3 flow entry: match fields, priority, counters, instructions, timeouts, cookie and flags, each with an example value." />

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div>

**Match fields** — ingress port, Ethernet, VLAN, IPv4/IPv6, DSCP, TCP/UDP ports, tunnel ID, metadata, … any field may be wildcarded or masked.

</div>
<div>

**Timeouts** — `idle_timeout` removes an unused entry; `hard_timeout` removes it regardless. Expiry can trigger a Flow-Removed message.

</div>
</div>

<!--
Match fields from OpenFlow 1.2 on are OXM TLVs, which is why the number of matchable fields could grow from 12
(1.0) to more than 40 (1.4). ↔ Lab 05 Step 5: students read exactly these fields in `dpctl dump-flows`, where the
counters show up as n_packets, n_bytes and duration.
-->

---

# Worked example — which entry matches?

<div class="grid grid-cols-2 gap-8 pt-2">
<div class="text-sm">

Table 0 of a switch:

| Prio | Match | Instructions |
|---|---|---|
| 300 | `ip, ip_dscp=46` | `set_queue:1, output:2` |
| 200 | `tcp, tp_dst=22` | `output:CONTROLLER` |
| 100 | `in_port=1` | `output:2` |
| 0 | *(any)* | `drop` |

</div>
<div class="text-sm">

1. A VoIP RTP packet from port 1, DSCP EF?
2. An SSH packet from port 1, DSCP 0?
3. An ARP request from port 3?

<div v-click class="pt-4">

1. **Prio 300** — queue 1, port 2. It also matches prio 100, but the higher priority wins.
2. **Prio 200** — sent to the controller, not forwarded.
3. **Prio 0** — the table-miss entry drops it: ARP is not IP and did not arrive on port 1.

</div>

</div>
</div>

<!--
Only the highest-priority match is executed; entries of equal priority that overlap give undefined results, which
is why the spec provides the CHECK_OVERLAP flag. Question 3 connects directly to Lab 05 Step 5: with two manual
`in_port` rules only, ARP still works because those rules match all traffic from the port, but a switch with more
ports would need per-destination rules. `set_queue` refers to a queue configured on the port (in OVS via OVSDB).
-->

---

# Pipeline processing

<Figure src="/figures/09/pipeline.svg" alt="A packet enters table 0 and may continue through later tables via Goto-Table, which only goes forward and may skip tables; an action set accumulates as it goes and is executed after the last table, before the packet leaves." />

<div class="pt-2 text-sm">

Flow tables are chained: an entry's **Goto-Table** instruction continues the lookup in a later table, which allows cascaded, modular processing (e.g. table 0 = access control, table 1 = QoS marking, table 2 = forwarding). If no entry matches, the **table-miss** entry decides: next table, controller, or drop.

</div>

<!--
Instructions per OpenFlow 1.3: Meter, Apply-Actions, Clear-Actions, Write-Actions, Write-Metadata, Goto-Table.
Without a table-miss entry an unmatched packet is dropped in 1.3; in 1.0 it was sent to the controller. Lab 05
exploits exactly this difference in its secure-mode OpenFlow 1.3 experiment. Multiple tables avoid the
cross-product explosion of one big table: N ACL rules times M forwarding rules become N + M entries.
-->

---

# Group table and meter table

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div>

**Group table** — an extra level of indirection, referenced by `group:<id>` from a flow entry. A group holds a list of **action buckets**:

| Type | Behaviour |
|---|---|
| `all` | every bucket — multicast, flooding |
| `select` | one bucket (hash) — load sharing, ECMP |
| `indirect` | single bucket — shared next hop |
| `fast failover` | first live bucket — local protection |

</div>
<div>

**Meter table** (since OpenFlow 1.3) — per-flow rate measurement and limiting, referenced by the `meter` instruction. An entry contains:

- meter identifier,
- **meter bands**: rate, burst, and type — `drop` or `dscp_remark`,
- counters.

<div class="pt-3 vsb-muted">

A meter band is Lecture 03's token-bucket **policer**: excess traffic is dropped or re-marked to a lower DSCP class.

</div>

</div>
</div>

<!--
Fast failover lets the switch itself switch to a backup port when the primary goes down, without waiting for a
controller round trip — important for the reliability challenge in Part 2. Meters police; they do not shape. For
shaping, OpenFlow's set_queue action puts the packet into a queue whose rate is configured outside OpenFlow
(OVSDB, tc). This is the bridge to Lecture 03's scheduling discussion.
-->

---

# Ports

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div>

**Physical ports** — the switch's hardware interfaces.

**Logical ports** — defined outside OpenFlow: link aggregation groups, tunnels, loopbacks. A packet from a logical port can carry a **Tunnel-ID** as metadata.

**Reserved ports** — used as the target of an output action for generic forwarding.

</div>
<div>

| Reserved port | Meaning |
|---|---|
| `ALL` | flood to all ports except ingress |
| `CONTROLLER` | encapsulate and send to the controller |
| `TABLE` | submit to the pipeline (Packet-Out only) |
| `IN_PORT` | send back out through the ingress port |
| `LOCAL` | the switch's own network stack |
| `NORMAL` | traditional non-OpenFlow forwarding |
| `FLOOD` | traditional flooding, respecting STP |

</div>
</div>

<!--
NORMAL and FLOOD are optional and only exist in hybrid switches that also have a conventional L2/L3 pipeline —
they are how a hybrid switch hands traffic back to "the old world". A packet is never sent out of its ingress port
unless IN_PORT is used explicitly, which prevents trivial loops.
-->

---

# The OpenFlow channel

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

- Carries configuration requests from the controller and events from the switch
- **TCP**, optionally **TLS**; IANA port **6653** (6633 in older implementations)
- **Connection initiated by the switch**
- Usually a separate management network (**out-of-band**); in-band control is possible
- Several controllers: roles *equal*, *master*, *slave* (1.2+)

</div>
<div>

<div class="vsb-fill">

### When the channel fails

**fail-secure** — keep installed entries, drop packets that would go to the controller

**fail-standalone** — behave as an ordinary learning switch (NORMAL)

</div>

</div>
</div>

<!--
The original slides say port 6633: that was the de-facto port before IANA assigned 6653 in 2013; OVS and most
controllers still accept both. Lab 05 prints the actual port with `ovs-vsctl get-controller s1`. The two fail modes
are what Lab 05 selects with `failMode=secure` versus `--switch ovsbr`.
-->

---

# OpenFlow message types

<div class="text-sm">

| Type | Initiated by | Purpose | Examples |
|---|---|---|---|
| **Controller-to-switch** | controller | configure, modify, and read the switch | Features-Request/Reply, Flow-Mod, Group-Mod, Meter-Mod, Port-Mod, Packet-Out, Multipart (statistics), Barrier, Role-Request |
| **Asynchronous** | switch, on an event | report without being asked | Packet-In, Flow-Removed, Port-Status |
| **Symmetric** | either side, unsolicited | keep the session alive | Hello, Echo-Request/Reply, Error, Experimenter |

</div>

<div class="pt-6 vsb-muted text-sm">

Every message starts with the same 8-byte header: version, type, length, transaction ID (`xid`). A Barrier-Reply tells the controller that all earlier requests have been processed — the only way to know that a rule is really installed.

</div>

<!--
The session starts with Hello (version negotiation), then Features-Request/Reply (datapath ID, number of tables,
capabilities), then configuration. Echo messages detect a dead channel, which triggers the fail modes of the
previous slide. Barrier matters for consistency: Flow-Mods may be applied out of order without one.
-->

---

# Reactive flow set-up

<Figure src="/figures/09/reactive-setup.svg" alt="Sequence diagram: packet 1 from host h1 misses in switch s1, which sends a Packet-In to the controller. The controller replies with a Flow-Mod installing an entry and a Packet-Out releasing packet 1 to host h2. Packet 2 matches the installed entry and is forwarded by the switch alone." />

<!--
This is the behaviour of the learning controller in Lab 05 Step 5: dump-flows is empty before the ping and
populated after it. The flow set-up delay is the controller round-trip time plus the controller's processing time
plus the time the switch needs to write the entry into its table (TCAM updates can take milliseconds on
hardware switches).
-->

---

# Reactive vs proactive flow installation

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**Reactive**

Entries are installed on demand, after a Packet-In.

- \+ small tables, only active flows
- \+ fine-grained, per-flow policy
- − first packet waits for the controller
- − controller load grows with the flow arrival rate
- − traffic for new flows stops if the controller is lost

</div>
<div class="border border-gray-400 p-4">

**Proactive**

Entries are installed in advance, from topology and policy.

- \+ no set-up delay, no per-flow controller load
- \+ forwarding survives a controller outage
- − tables must hold every possible rule (TCAM size)
- − coarser policy, usually wildcard rules

</div>
</div>

<div class="pt-4 vsb-muted text-sm">

Production networks are mostly proactive, with reactive handling only for exceptions — the same trade-off the controller's scalability challenge forces.

</div>

<!--
Connects the Part 2 challenges to a design choice. Hardware flow tables are TCAM, typically a few thousand to tens of
thousands of wildcard entries, while software switches such as OVS hold millions of exact-match entries in a cache.
The controller load of the reactive mode is a queueing problem: Packet-In arrivals at rate lambda served by a
controller at rate mu — Lecture 02's M/M/1 applies directly.
-->

---

# Checkpoint — the slow first ping

<div class="checkpoint-question">

In Mininet with a reactive learning controller, the first `ping` between two hosts takes 5–10 ms, every following one about 0.05 ms. Explain the difference. What would change after `del-flows` on the switch?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

The first echo request (and the ARP exchange before it) **misses** in the empty flow table: the switch sends a Packet-In, the controller computes a decision and answers with Flow-Mod and Packet-Out, and the reply does the same in the other direction. Later packets match the installed entries and stay in the data plane. After `del-flows` the next ping pays the **flow set-up delay again**, and the controller reinstalls the entries.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. ↔ Lab 05 Question 2. The numbers are
typical for Mininet on one machine; with a remote controller the set-up delay grows with the controller RTT.
-->

---

# Checkpoint — the controller crashes

<div class="checkpoint-question">

A switch in **fail-secure** mode loses its only controller. What happens to an ongoing video call, and what happens to a call that starts a minute later?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**The ongoing call continues** — its entries are already in the flow table and the data plane does not need the controller (unless an idle or hard timeout expires them). **The new call fails** if its packets need a Packet-In: in fail-secure mode those packets are dropped. With proactive rules both calls would work; in **fail-standalone** mode the switch would fall back to ordinary learning and forward both, without the controller's policy.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. This is the reliability challenge made
concrete, and it sets up the comparison with EVPN, where there is no controller to lose.
-->

---

# OpenFlow as a QoS tool

<div class="grid grid-cols-2 gap-8 pt-2 text-sm">
<div>

**Classification** — match on any header field, including `ip_dscp`, ports, and addresses (Lecture 03's classifier, programmable per flow).

**Marking** — `set_field:ip_dscp` re-marks at the network edge.

**Policing** — meter bands drop or re-mark traffic above a rate.

**Scheduling** — `set_queue` selects a port queue; the queue's rate and discipline are configured outside OpenFlow.

</div>
<div>

**Measurement** — per-flow, per-port, and per-queue counters polled by Multipart requests give the controller a live traffic matrix.

**Traffic engineering** — the controller places flows on paths according to the measured load.

<div class="vsb-fill mt-4">

### Google B4 (2013)

SDN traffic engineering drove inter-data-centre WAN links close to 100 % utilization, against 30–40 % typical for conventionally routed WANs.

</div>

</div>
</div>

<!--
This slide ties the lecture back to the QoS mechanisms of Lecture 03: every one of them (classify, mark, police,
queue, measure) has an OpenFlow counterpart, but now all switches are configured from one place with one view of the
load. Jain et al., "B4: Experience with a Globally-Deployed Software Defined WAN", SIGCOMM 2013.
-->

---

# Beyond OpenFlow

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

**The limits of a fixed protocol**

- Every new header field needs a new specification: from 12 fields (1.0) to more than 40 (1.4)
- The switch chip still decides which fields it can parse
- Hardware table sizes (TCAM) limit wildcard entries

</div>
<div>

**P4 and P4Runtime**

- **P4** describes the parser and the match–action pipeline itself; the program is compiled onto a programmable chip
- **P4Runtime** is the southbound API that fills the tables of that program — the role OpenFlow plays for a fixed pipeline

</div>
</div>

<div class="pt-6 vsb-muted text-sm">

SDN as an architecture outlived OpenFlow as a protocol: controllers such as ONOS now speak OpenFlow, P4Runtime, NETCONF, and gNMI side by side.

</div>

<!--
Bosshart et al., "P4: Programming Protocol-Independent Packet Processors", CCR 2014 — the "12 to 41 fields"
observation comes from that paper. This slide prepares the "not either/or" message of Part 4: the concepts of the
lecture (separation, central view, match–action) survive even where OpenFlow itself is not used.
-->

---
layout: section
---

# Part 4
## OpenFlow vs VXLAN-EVPN

---

# The data-centre problem

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

A multi-tenant data centre needs:

- **millions** of isolated tenant networks, not 4094 VLANs,
- layer-2 adjacency for virtual machines that **move** between racks,
- an **IP underlay** (leaf–spine, ECMP) without spanning tree,
- multi-vendor interoperability at the scale of thousands of switches.

</div>
<div>

<div class="vsb-fill">

### Two answers

**OpenFlow**: a controller programs every switch (or virtual switch) directly.

**VXLAN-EVPN**: an overlay data plane plus a standard, distributed BGP control plane.

</div>

</div>
</div>

<!--
The same problems as the "limitations" slide of Part 1 — resource migration and resource sharing — in their
data-centre form. Both answers are in wide use; the comparison that follows is about where each fits.
-->

---

# VXLAN — the overlay data plane

<Figure src="/figures/09/vxlan-frame.svg" alt="VXLAN encapsulation: the ingress VTEP adds an outer Ethernet header of 14 bytes, an outer IPv4 header of 20 bytes, an outer UDP header of 8 bytes and an 8-byte VXLAN header with a 24-bit VNI to the tenant Ethernet frame, 50 bytes in total." />

<div class="pt-2 text-sm">

**VXLAN** (RFC 7348, 2014) tunnels Ethernet frames in UDP/IP between **VXLAN tunnel endpoints (VTEPs)** — leaf switches or hypervisors. The underlay only routes IP; tenant MAC addresses never reach it.

</div>

<!--
The 50 B overhead is for IPv4 without an outer VLAN tag (70 B for IPv6). The underlay MTU must therefore be at least
1550 B for a 1500 B tenant MTU; jumbo frames (9216 B) are common in practice. VXLAN by itself specifies only the
data plane — its original learning mechanism is flood-and-learn over underlay multicast, which does not scale.
That missing control plane is what EVPN adds.
-->

---

# EVPN — a distributed control plane in BGP

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

**BGP EVPN** (RFC 7432, 8365) carries MAC and IP reachability in the MP-BGP address family L2VPN/EVPN. Each VTEP **advertises** its local hosts; the others install the routes. No flood-and-learn in the data plane.

</div>
<div class="text-sm">

| Route type | Carries |
|---|---|
| 1 — Ethernet auto-discovery | multihoming, fast convergence |
| 2 — MAC/IP advertisement | host MAC and IP behind a VTEP |
| 3 — Inclusive multicast | VTEP list for BUM traffic per VNI |
| 4 — Ethernet segment | designated-forwarder election |
| 5 — IP prefix | routed subnets between VNIs (RFC 9136) |

</div>
</div>

<div class="pt-4 vsb-muted text-sm">

Type-2 routes also enable **ARP suppression**: the leaf answers ARP locally from BGP-learned bindings.

</div>

<!--
EVPN was first defined for MPLS (RFC 7432, 2015); RFC 8365 (2018) applies it to network virtualization overlays
such as VXLAN. Integrated routing and bridging (RFC 9135) and the type-5 route (RFC 9136) make the fabric a routed
L2/L3 overlay. BGP route reflectors on the spines avoid a full mesh of iBGP sessions between leaves.
-->

---

# Where the control plane lives

<Figure src="/figures/09/control-placement.svg" alt="Left: an SDN controller cluster pushes flow entries into four switches. Right: a leaf-spine fabric where two spines act as BGP route reflectors, four leaves exchange EVPN routes over iBGP, and tenant traffic between two leaves runs in a VXLAN tunnel." />

<!--
Both are "separation of control and data plane" in a loose sense — EVPN also separates the overlay control
plane (BGP) from the data plane (VXLAN) — but only OpenFlow moves the control plane out of the switch. In EVPN each
leaf still runs its own control plane and computes its own forwarding table, exactly as an IP router does.
-->

---

# OpenFlow vs VXLAN-EVPN

<div class="text-sm">

| Aspect | OpenFlow | VXLAN-EVPN |
|---|---|---|
| Control plane | logically centralized controller | distributed: MP-BGP on every VTEP |
| What is programmed | per-flow match–action entries, any L1–L4 field | per-destination MAC/IP reachability, per VNI and VRF |
| Data plane | any; OpenFlow mandates no encapsulation | VXLAN over a routed IP underlay |
| Standardization | ONF; frozen at 1.5.1 (2015) | IETF RFCs, actively evolving |
| Scaling limit | controller capacity, TCAM size | BGP (Internet-proven), route reflectors |
| Controller failure | new reactive flows fail (fail-secure) | no controller; BGP reconverges locally |
| Vendor support | OVS, few hardware switches today | all data-centre switch vendors |
| Typical use | virtual switches, research, WAN TE | leaf–spine data-centre fabrics, DCI |

</div>

<!--
The key row is the first one: this is not "SDN vs non-SDN" but centralized vs distributed control. OpenFlow wins
on flexibility (any field, any action, one program); EVPN wins on robustness and operational familiarity (BGP skills,
no single component whose loss stops new traffic). Hardware OpenFlow support has declined since about 2018; OVS
remains the main implementation.
-->

---

# OpenFlow vs VXLAN-EVPN — the QoS view

<div class="grid grid-cols-2 gap-6 pt-2 text-sm">
<div class="border border-gray-400 p-4">

**OpenFlow**

- Per-flow classification, policing (meters), re-marking, and queue selection from one place
- Traffic engineering: explicit path per flow, driven by measured load
- Flow set-up delay for reactive flows; controller is on the critical path of new traffic

</div>
<div class="border border-gray-400 p-4">

**VXLAN-EVPN**

- QoS is the DiffServ of Lecture 03: the VTEP copies the inner DSCP to the outer IP header so that the underlay can schedule it
- Load spreading by ECMP on the outer UDP source-port hash — statistical, not per-flow placement
- No set-up delay: routes exist before the first packet

</div>
</div>

<div class="pt-6 vsb-muted text-sm">

Fine-grained control against predictable, distributed behaviour — the same trade-off as IntServ against DiffServ.

</div>

<!--
DSCP copying at encapsulation follows the tunnel models of RFC 2983 (uniform/pipe). ECMP hashing can place two
elephant flows on the same uplink — the classical argument for centralized traffic engineering (Hedera, NSDI 2010).
The IntServ/DiffServ analogy recalls the Lecture 03 extras: per-flow state versus aggregate behaviour.
-->

---

# Not either/or

<div class="grid grid-cols-2 gap-8 pt-2">
<div>

**OpenFlow driving VXLAN**

Network virtualization platforms (OpenStack with OVS/OVN, VMware NSX) use a central controller to program **Open vSwitch** in every hypervisor over OpenFlow — including the VXLAN or Geneve tunnels between hosts.

</div>
<div>

**Controllers managing EVPN fabrics**

Fabric controllers and intent-based systems configure the EVPN switches through NETCONF/YANG or gNMI: **centralized management**, **distributed control**.

</div>
</div>

<div class="pt-8">

The SDN idea — software with a global view defines the network — appears in both. What differs is **which plane is centralized**.

</div>

<!--
Koponen et al., "Network virtualization in multi-tenant datacenters" (NSDI 2014) describes NSX/NVP: OpenFlow and
OVSDB to OVS, tunnels between hypervisors. This is where most OpenFlow runs today — in software, at the edge. The
hardware fabric underneath is increasingly EVPN.
-->

---

# Checkpoint — choose the design

<div class="checkpoint-question">

(a) A cloud provider builds a fabric of 2000 racks from switches of two vendors. (b) A university wants to steer individual research flows onto an experimental path and meter them. Which approach suits each, and why?

</div>

<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>

<div class="checkpoint-answer" v-click>

**(a) VXLAN-EVPN** — standard, multi-vendor, BGP scales to that size, and no controller outage can stop new tenant traffic. **(b) OpenFlow** — per-flow matching on any field, meters, and explicit paths are exactly what it offers, and a campus is the scale the 2008 OpenFlow paper was written for. Either may still be centrally *managed*.

</div>

<!--
Allow 30 seconds for individual thought, then 30 seconds of pair discussion. Accept hybrid answers (EVPN fabric
with OVS/OpenFlow at the hypervisor edge) if students justify them.
-->

---

# Common mix-ups

<div class="grid grid-cols-3 gap-4 pt-2 text-sm">
<div class="border border-orange-400 p-3">

**SDN vs OpenFlow**

SDN is an architecture; OpenFlow is one southbound protocol for it.

</div>
<div class="border border-orange-400 p-3">

**Centralized vs single**

"Logically centralized" controllers are usually clusters of several servers.

</div>
<div class="border border-orange-400 p-3">

**SDN vs NFV**

SDN separates control from forwarding; NFV moves middlebox functions into software.

</div>
<div class="border border-orange-400 p-3">

**Controller loss vs traffic loss**

Installed entries keep forwarding; only traffic needing the controller stops.

</div>
<div class="border border-orange-400 p-3">

**VXLAN vs EVPN**

VXLAN is the encapsulation (data plane); EVPN is the BGP control plane that fills it.

</div>
<div class="border border-orange-400 p-3">

**Meter vs queue**

A meter polices (drop/re-mark); `set_queue` selects a queue whose shaping is configured elsewhere.

</div>
</div>

<!--
Six confusions that recur in exam answers: (1) equating SDN with OpenFlow, (2) assuming a single controller
machine, (3) conflating SDN and NFV, (4) believing that a controller crash stops all traffic, (5) treating VXLAN
and EVPN as one protocol, (6) expecting a meter to shape traffic.
-->

---

# Summary

<div class="grid grid-cols-2 gap-x-10 gap-y-2 pt-2 text-sm">

<div>

**Separation of planes**
The data plane forwards; the control plane decides. SDN moves the decision into a logically centralized controller.

**Architecture**
Applications — northbound API — controller — southbound API — switches; east–west between controllers.

**Flow entries**
Match fields, priority, counters, instructions, timeouts; the highest-priority match wins, the table-miss entry catches the rest.

**Pipeline**
Goto-Table forward only; the action set executes at the end. Groups for multicast, ECMP, failover; meters for policing.

</div>
<div>

**Channel and messages**
Switch-initiated TCP/TLS on 6653; controller-to-switch, asynchronous, and symmetric messages.

**Reactive set-up**
Packet-In → Flow-Mod + Packet-Out: the first packet pays the controller round trip.

**OpenFlow vs VXLAN-EVPN**
Central, per-flow, flexible — against distributed, per-destination, BGP-robust.

**Beyond OpenFlow**
P4/P4Runtime for programmable pipelines; SDN as an architecture persists.

</div>

</div>

<!--
Read them aloud, one sentence each. Then the exit questions.
-->

---

# Exit questions — use the ideas

1. A switch receives a packet that matches two flow entries with priorities 50 and 200. Which is applied, and what happens if neither exists and the table has no table-miss entry (OpenFlow 1.3)?
2. A controller is 20 ms RTT away from a switch and needs 2 ms per decision. Estimate the extra delay of a new TCP connection's SYN in reactive mode.
3. Why can a VXLAN-EVPN fabric keep accepting new hosts when every management server is down, while a reactive OpenFlow network in fail-secure mode cannot?
4. Which OpenFlow feature implements Lecture 03's token-bucket policer, and which one would you combine it with to prioritize EF-marked voice?

<div v-click class="pt-5 vsb-muted">

**Explain the mechanism**, not just its name.

</div>

<!--
Answers: (1) Priority 200; without any match and no table-miss entry the packet is dropped (in 1.0 it would go to
the controller). (2) About 22 ms plus the table-write time, once per direction if the reply also misses — the
SYN-ACK in the reverse direction may pay again. (3) EVPN learning is part of the switches' own BGP control plane;
nothing central is needed to advertise a new MAC/IP route. The OpenFlow switch needs a Packet-In answered.
(4) A meter band (drop or dscp_remark) polices; match ip_dscp=46 with set_queue to a strict-priority queue to
prioritize voice.
-->

---

# Lab 05 — SDN in Mininet

<div class="grid grid-cols-5 gap-8 pt-2">
<div class="col-span-2">

This lecture described the switch model; Lab 05 lets you **read and write its flow table** by hand:

- Controller-installed entries before and after a ping ↔ reactive set-up (Step 5)
- Empty secure-mode switch, manual `in_port` rules ↔ table miss, fail-secure (Step 5)
- `tc` links with bandwidth, delay, loss ↔ Lecture 03's parameters (Steps 7–8)

</div>
<div class="col-span-3">

<div class="text-sm vsb-muted">

```bash {lines:false}
ssh student@<lab-server>
sudo mn --topo single,2 --mac --controller=none \
  --switch ovsk,protocols=OpenFlow13,failMode=secure
# in the Mininet CLI:
sh ovs-ofctl -O OpenFlow13 dump-flows s1
```

</div>

<div class="pt-4 text-sm">

Before you type `add-flow`, predict which packets each entry will match.

</div>
</div>
</div>

<!--
Lab 05 has no notebook; everything runs in the Mininet CLI on the lab servers. Questions 2 and 3 of the lab README
are the checkpoint questions of Part 3 in written form.
-->

---

# References — foundations

- N. McKeown et al., "OpenFlow: Enabling Innovation in Campus Networks," *ACM SIGCOMM CCR*, 38(2), 69–74, 2008.
- N. Feamster, J. Rexford, E. Zegura, "The Road to SDN: An Intellectual History of Programmable Networks," *ACM SIGCOMM CCR*, 44(2), 87–98, 2014.
- D. Kreutz et al., "Software-Defined Networking: A Comprehensive Survey," *Proceedings of the IEEE*, 103(1), 14–76, 2015.
- M. Casado et al., "Ethane: Taking Control of the Enterprise," *ACM SIGCOMM*, 2007.
- N. Gude et al., "NOX: Towards an Operating System for Networks," *ACM SIGCOMM CCR*, 38(3), 2008.
- T. Koponen et al., "Onix: A Distributed Control Platform for Large-scale Production Networks," *USENIX OSDI*, 2010.
- S. Jain et al., "B4: Experience with a Globally-Deployed Software Defined WAN," *ACM SIGCOMM*, 2013.
- P. Bosshart et al., "P4: Programming Protocol-Independent Packet Processors," *ACM SIGCOMM CCR*, 44(3), 2014.
- L. Peterson et al., *Software-Defined Networks: A Systems Approach*. Systems Approach LLC, 2021 (online, sdn.systemsapproach.org).
- J. F. Kurose, K. W. Ross, *Computer Networking: A Top-Down Approach*, 8th ed., ch. 4.4 and 5.5. Pearson, 2021.

<!--
McKeown (Stanford) and Feamster/Rexford (Princeton) are the primary academic sources; the Peterson et al. book is
the open textbook used by several SDN courses. Kreutz et al. is the most cited survey.
-->

---

# References — standards

- Open Networking Foundation, *OpenFlow Switch Specification*, version 1.3.5 (TS-023) and 1.5.1 (TS-025), 2015.
- E. Haleplidis et al., "Software-Defined Networking (SDN): Layers and Architecture Terminology," RFC 7426, 2015.
- L. Yang et al., "Forwarding and Control Element Separation (ForCES) Framework," RFC 3746, 2004.
- M. Mahalingam et al., "Virtual eXtensible Local Area Network (VXLAN)," RFC 7348, 2014.
- A. Sajassi et al., "BGP MPLS-Based Ethernet VPN," RFC 7432, 2015.
- A. Sajassi et al., "A Network Virtualization Overlay Solution Using Ethernet VPN (EVPN)," RFC 8365, 2018.
- J. Rabadan et al., "IP Prefix Advertisement in Ethernet VPN (EVPN)," RFC 9136, 2021.
- ETSI GS NFV 002, *Network Functions Virtualisation (NFV); Architectural Framework*, 2013.

<!--
The OpenFlow 1.3.5 specification is the version Lab 05 uses; 1.5.1 is the last one. The RFCs back Part 4.
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
