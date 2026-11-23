# Lecture 08 — QoS architectures (IntServ/RSVP, DiffServ) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A 90-minute Slidev deck `slides/08-qos-architectures.md` on IntServ/RSVP and DiffServ that builds on Lecture 03, with a live two-domain RSVP/DSCP visualisation (`QosPathSim`, `QosCompare`) and light/dark SVG figures.

**Architecture:** The simulation logic lives in pure, deterministic TypeScript engines under `slides/utils/` (topology, RSVP, DiffServ), unit-tested with Node's built-in test runner. Vue components only render engine state and drive `tick()` from `requestAnimationFrame`. Static diagrams are generated into `public/figures/08/` by a new `# 08` section of `scripts/generate-figures.py`. The deck is Markdown following the house rhythm.

**Tech Stack:** Slidev (theme seriph), Vue 3 `<script setup lang="ts">`, Node 26 (`node --test`, native type stripping), Python 3 standard library for figures, KaTeX.

**Spec:** `docs/superpowers/specs/2026-11-23-lecture-08-intserv-diffserv-design.md` — read it in full before any task; it carries the slide-by-slide content and the component behaviour this plan only points to.

## Global Constraints

- Work in `slides/`; every command below runs from `/home/loki/0-vsb/qos/slides` unless stated.
- Deck file `08-qos-architectures.md`, frontmatter copied from `09-sdn-openflow.md` with `title: 08 · QoS architectures in IP networks`, `exportFilename: 08-qos-architectures`, `info:` rewritten.
- House rhythm (slides/README.md): cover → where we are going → outcomes → `statement` thesis → `section` per part → content + checkpoints → common mix-ups → summary → exit questions → where you use this → references → `end` → Extras.
- Thesis statement verbatim: **"Guarantee needs state; scale forbids state"** / subtitle **"IntServ and DiffServ are the two ends of that trade-off"**.
- Checkpoints use `.checkpoint-question`, `<p class="vsb-muted">Predict first · discuss with a neighbour · then reveal</p>`, `.checkpoint-answer` with `v-click`. Speaker notes (`<!-- -->`) on every slide.
- Units in prose escaped: `\[Mbit/s\]`. KaTeX closing `$` not preceded by a space. Code fences only in known languages (`bash`).
- Figures: colours only from `PALETTES` names (G, D, C, INK, MUT, TINT…, FMT, EKF); 880 px wide; title + desc; embed with `<Figure src="/figures/08/<name>.svg" alt="…" />`.
- Components: colours only via `var(--vsb-*)` CSS variables, plus FMT red `#E4002B` for drops/refusals (as GilbertSim); FEI cyan never for text; text ≥ 14 px inside components, titles 18 px; rounded corners per VSB-STYLE R24; must read correctly in dark mode (`d`).
- Engine TypeScript must be erasable-only syntax (no `enum`, no parameter properties, no namespaces) so `node --test` runs it unmodified; relative imports between engine files carry the `.ts` extension.
- Every animation stops in `onSlideLeave`; print mode (`useNav().isPrintMode`) renders a static frame; the live slides do **not** use `export-skip`.
- Facts pinned by the spec: RSVP refresh R = 30 s, lifetime L ≥ (K + 0.5)·1.5·R with K = 3 (≈ 157 s); the animation expires state after 3 missed refreshes and says so on screen. DSCP: EF 46, VOICE-ADMIT 44, AF11 10 … AF43 38, CSn = 8n, LE 1, default 0.
- Do not touch `slides/10-diffserv.pdf` (untracked source material) and do not reuse its images.
- Commit after each task on branch `2026`, message ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Many flows (200) in the side-by-side slide** — the animation stays fluid (no per-frame allocation proportional to all packets ever sent) and the state tables show "+ n more" instead of overflowing. Test in Task 2 (`stateRows` caps) and Task 5 (manual 200-flow check).
2. **Leaving and re-entering a live slide, or pressing Reset mid-run** — no duplicated timers, the run restarts from the same seed and identical first events. Test in Task 1 (`reset` determinism) and Task 3 (manual check).
3. **Dark mode** — every queue, packet label, state table and bar keeps ≥ 3:1 contrast on `#0E1A19`. Manual check in Tasks 3–6 using the screenshot script.
4. **Changing a control mid-run** (capacity lowered below the reserved sum, boundary switched to bleach while packets are on the peering link, refresh switched off then on) — existing reservations stay until they expire or are refreshed; packets already past E3 keep their marks. Tests in Task 1 (`capacity lowered`) and Task 2 (`boundary switch applies only at E3 ingress`).
5. **PDF export** — the print frames are complete and nothing interactive is cut off. Verified in Task 9 by exporting and viewing pages.

---

## File structure

| File | Responsibility |
|---|---|
| `slides/utils/qos-topology.ts` | node/link ids, path, link capacities, shared types, seeded RNG re-export |
| `slides/utils/qos-rsvp.ts` | `RsvpSim`: PATH/RESV messages, admission, soft state, refresh, policy refusal, router failure |
| `slides/utils/qos-diffserv.ts` | `DiffServSim`: packet generation, E1 classifier + trTCM meter + EF policer, per-class queues, boundary policy at E3, cross traffic, stats |
| `slides/utils/qos-*.test.ts` | Node unit tests of the three files |
| `slides/components/QosPathSim.vue` | rendering + controls of one simulation (`mode`, `compact`, print frame) |
| `slides/components/QosCompare.vue` | two `QosPathSim` side by side with one flows slider |
| `slides/scripts/generate-figures.py` | new `# 08` section (8 figures) |
| `slides/08-qos-architectures.md` | the deck |
| `slides/03-qos-mechanisms.md`, `slides/09-sdn-openflow.md`, `slides/README.md`, `CLAUDE.md` | cross-references and docs |

---

### Task 1: Topology and the RSVP engine

**Files:**
- Create: `slides/utils/qos-topology.ts`, `slides/utils/qos-rsvp.ts`
- Test: `slides/utils/qos-rsvp.test.ts`

**Interfaces:**
- Consumes: `mulberry32(seed: number): Rand` from `slides/utils/traffic.ts` (import as `./traffic.ts`).
- Produces (`qos-topology.ts`):
  ```ts
  export type NodeId = 'S' | 'E1' | 'C1' | 'C2' | 'E2' | 'E3' | 'C3' | 'E4' | 'R'
  export const PATH: readonly NodeId[] = ['S','E1','C1','C2','E2','E3','C3','E4','R']
  export const ROUTERS: readonly NodeId[]            // PATH without S and R (7 routers)
  export const DOMAIN: Record<NodeId, 'host' | 'A' | 'B'>
  export const ROLE: Record<NodeId, 'host' | 'edge' | 'core'>
  export type LinkId = `${NodeId}>${NodeId}`         // downstream links only, e.g. 'C1>C2'
  export const LINKS: readonly LinkId[]              // 8 consecutive pairs of PATH
  export const BOTTLENECK_A: LinkId = 'C1>C2'
  export const BOTTLENECK_B: LinkId = 'C3>E4'
  export const FAST_LINK = 100                       // Mbit/s for every non-bottleneck link
  export type FlowKind = 'voice' | 'video' | 'data'
  export const FLOW_RATE: Record<FlowKind, number> = { voice: 0.1, video: 2, data: 1 }  // Mbit/s
  export interface Capacities { A: number, B: number }  // Mbit/s of BOTTLENECK_A / _B
  export function linkCapacity(link: LinkId, cap: Capacities): number
  export function next(node: NodeId): NodeId | null; export function prev(node: NodeId): NodeId | null
  export function drawKind(rand: Rand): FlowKind     // voice 0.5, video 0.3, data 0.2
  export { mulberry32, type Rand } from './traffic.ts'
  ```
- Produces (`qos-rsvp.ts`):
  ```ts
  export type MsgType = 'PATH' | 'RESV' | 'ResvErr'
  export interface Msg { type: MsgType, flow: number, from: NodeId, to: NodeId, t: number /*0..1 along the hop*/, refresh: boolean }
  export type FlowStatus = 'signalling' | 'reserved' | 'refused' | 'expired' | 'besteffort'
  export interface RsvpFlow { id: number, kind: FlowKind, rate: number, status: FlowStatus, refusedAt?: NodeId, reason?: 'capacity' | 'policy' }
  export interface PathEntry { flow: number, phop: NodeId, rate: number, age: number }
  export interface ResvEntry { flow: number, link: LinkId, rate: number, age: number }
  export interface RsvpConfig { cap: Capacities, refresh: boolean, refreshPeriod: number /*sim s, default 3 (stands for 30 s)*/,
                               hopTime: number /*sim s per hop, default 0.25*/, foreignPolicy: boolean /*E3 refuses all RESV*/, seed: number }
  export class RsvpSim {
    constructor(cfg: Partial<RsvpConfig>)
    cfg: RsvpConfig; time: number
    flows: RsvpFlow[]; msgs: Msg[]
    path: Record<NodeId, Map<number, PathEntry>>; resv: Record<NodeId, Map<number, ResvEntry>>
    addFlow(kind?: FlowKind): RsvpFlow              // kind omitted → drawKind(rng); data → status 'besteffort', no messages
    removeFlow(id: number): void                    // PathTear: state of that flow removed everywhere immediately
    setFlowCount(n: number): void                   // add or remove (newest first) until flows.length === n
    failRouter(node: NodeId): void                  // clears path + resv of that router only
    reset(): void                                   // back to time 0 with the same seed
    tick(dt: number): void                          // advance; may be called with any dt ≥ 0
    step(): void                                    // advance to the next message arrival or refresh event
    reserved(link: LinkId): number                  // Mbit/s reserved on the link
    stateCount(node: NodeId): number                // path.size + resv.size (S/R: 0)
    refreshMsgPerSecond(): number                   // real-network equivalent: 2 · (#reserved) / 30
  }
  export const MAX_ANIMATED_REFRESH = 20            // above this many reserved flows refreshes update ages without Msg objects
  ```

Behaviour the tests pin (from the spec, Part 2 and "mode=rsvp"): PATH travels S→R one hop per `hopTime`, writing a `PathEntry` at each router on arrival; on reaching R a RESV travels back R→S; on arrival at router X, admission checks the link X→next(X): `reserved(link) + rate ≤ linkCapacity(link)`; at E3 with `foreignPolicy` it refuses with reason `'policy'`. Refusal: flow `refused` with `refusedAt`, a ResvErr travels downstream to R, and every `ResvEntry` of that flow already installed downstream is removed as the ResvErr passes. When RESV reaches S the flow is `reserved`. Refresh on: every `refreshPeriod` each reserved flow resets `age` of its entries (and re-creates missing entries, re-running admission — this is how `failRouter` recovers). Refresh off: ages grow; an entry with `age > 3 · refreshPeriod` is deleted; a reserved flow that lost any entry becomes `expired` and its bandwidth is released. Lowering `cfg.cap` mid-run does not evict existing reservations; it only affects new admissions and refresh re-admissions of re-created entries.

- [ ] **Step 1: Write the failing tests** in `slides/utils/qos-rsvp.test.ts` (`import { test } from 'node:test'; import assert from 'node:assert/strict'`):

```ts
const run = (sim, s) => { for (let i = 0; i < s * 100; i++) sim.tick(0.01) }
test('one voice flow reserves on every router', () => {
  const sim = new RsvpSim({ seed: 1 }); const f = sim.addFlow('voice'); run(sim, 5)
  assert.equal(f.status, 'reserved')
  for (const r of ROUTERS) { assert.equal(sim.path[r].has(f.id), true); assert.equal(sim.resv[r].has(f.id), true) }
  assert.equal(sim.reserved('C1>C2'), 0.1)
})
test('PATH reaches R before any RESV exists', ...)          // after 7.5 hops: R has seen PATH, no resv anywhere
test('sixth video flow is refused at C1 with capacity 10', () => {
  const sim = new RsvpSim({ seed: 1, cap: { A: 10, B: 100 } })
  const fs = Array.from({ length: 6 }, () => sim.addFlow('video')); run(sim, 10)
  assert.deepEqual(fs.map(f => f.status), ['reserved','reserved','reserved','reserved','reserved','refused'])
  assert.equal(fs[5].refusedAt, 'C1'); assert.equal(fs[5].reason, 'capacity')
  for (const r of ['C2','E2','E3','C3','E4']) assert.equal(sim.resv[r].has(fs[5].id), false)
})
test('refusal in domain B at C3', ...)                     // cap {A:100,B:4}: third video refusedAt 'C3'
test('foreign policy refuses at E3', ...)                  // foreignPolicy: voice refusedAt 'E3', reason 'policy', no resv at E1..E2
test('data flows signal nothing', ...)                     // status 'besteffort', msgs.length === 0
test('refresh off: state expires after 3 periods', () => { // refreshPeriod 3: reserved at t≈5; still reserved at t=5+9-0.5; expired by t=5+9+3.5; reserved('C1>C2') === 0
})
test('refresh on keeps state alive for 60 s', ...)         // status 'reserved' after run(sim, 60)
test('failRouter is repaired by the next refresh', ...)    // failRouter('C1'); stateCount('C1') === 0; after refreshPeriod + 2 s: path & resv of C1 restored
test('lowering capacity does not evict', ...)              // 5 videos reserved at A=10; cfg.cap.A = 4; run 20 s with refresh: all 5 still reserved
test('reset is deterministic', ...)                        // addFlow() ×10 with seed 7, record kinds+statuses at t=10; reset(); repeat; deepEqual
test('setFlowCount removes newest first', ...)             // 5 flows → setFlowCount(2) → ids are the first two; state of removed ids gone everywhere
test('refreshMsgPerSecond', ...)                           // 3 reserved voice flows → 0.2
```

- [ ] **Step 2: Run** `node --test utils/qos-rsvp.test.ts` — Expected: FAIL (module not found).
- [ ] **Step 3: Implement `qos-topology.ts` and `RsvpSim`** with the interfaces above. Messages are plain objects in `msgs`; `tick` advances every message's `t` by `dt / hopTime` and handles arrivals in time order (several arrivals within one large `dt` must be processed in order — loop until no message has `t ≥ 1`). Refresh with more than `MAX_ANIMATED_REFRESH` reserved flows updates ages directly instead of creating `Msg` objects.
- [ ] **Step 4: Run** `node --test utils/qos-rsvp.test.ts` — Expected: all pass.
- [ ] **Step 5: Commit** `feat(slides): RSVP simulation engine for lecture 08`.

---

### Task 2: The DiffServ engine

**Files:**
- Create: `slides/utils/qos-diffserv.ts`
- Test: `slides/utils/qos-diffserv.test.ts`

**Interfaces:**
- Consumes: everything from `qos-topology.ts` (Task 1).
- Produces:
  ```ts
  export const DSCP = { CS0: 0, LE: 1, AF11: 10, AF12: 12, AF13: 14, AF21: 18, AF22: 20, AF23: 22, AF31: 26, AF32: 28, AF33: 30,
                        AF41: 34, AF42: 36, AF43: 38, CS1: 8, CS2: 16, CS3: 24, CS4: 32, CS5: 40, VA: 44, EF: 46, CS6: 48, CS7: 56 } as const
  export function dscpName(d: number): string        // 34 → 'AF41', 0 → 'BE', 46 → 'EF', 24 → 'CS3', unknown → String(d)
  export type QueueClass = 'EF' | 'AF4' | 'AF3' | 'BE'
  export function queueOf(dscp: number): QueueClass  // 46 → EF; 34/36/38 → AF4; 26/28/30 → AF3; everything else → BE
  export function dropPrecedence(dscp: number): 1 | 2 | 3   // AFxy → y; others 1
  export const PKT_BITS = 0.1                         // Mbit per drawn packet
  export const QUEUE_LIMIT = 30                       // packets per class queue
  export const AF_DROP_AT: Record<1 | 2 | 3, number> = { 3: 10, 2: 20, 1: 30 }  // AF queue length at which that precedence is dropped
  export const WRR: Record<'AF4' | 'AF3' | 'BE', number> = { AF4: 3, AF3: 2, BE: 1 }  // after strict-priority EF
  export type Boundary = 'trust' | 'remark' | 'bleach'
  export interface Pkt { id: number, flow: number /* -1 = cross traffic */, kind: FlowKind | 'cross', dscp: number, origDscp: number,
                         at: NodeId, link: LinkId | null, t: number /*0..1 on link*/, born: number }
  export interface DsConfig { cap: Capacities, boundary: Boundary, crossB: number /*Mbit/s BE injected at E3 → E4*/,
                              efPolice: { rate: number, burst: number }   /* E1, default {rate: 1, burst: 0.3} Mbit/s, Mbit */,
                              videoMeter: { cir: number, pir: number, cbs: number, pbs: number }   /* E1 trTCM, default {6, 8, 0.3, 0.3} */,
                              efPoliceB: { rate: number, burst: number }  /* E3 under 'remark', default {0.5, 0.3}; excess EF → CS0 */,
                              hopTime: number /*sim s per fast hop, default 0.2*/, seed: number }
  export interface ClassStats { sent: number, dropped: number, delivered: number, delaySum: number }
  export class DiffServSim {
    constructor(cfg: Partial<DsConfig>)
    cfg: DsConfig; time: number; flows: { id: number, kind: FlowKind }[]
    inFlight: Pkt[]                                   // packets on links (drawn)
    queues: Record<LinkId, Record<QueueClass, Pkt[]>> // only BOTTLENECK_A and BOTTLENECK_B are ever non-empty
    drops: { pkt: Pkt, node: NodeId, reason: 'police' | 'queue' }[]  // last 50 only, for the drop animation
    stats: Record<FlowKind | 'cross', ClassStats>     // delivered at R (cross traffic leaves at E4)
    addFlow(kind?: FlowKind): void; removeFlow(id: number): void; setFlowCount(n: number): void
    reset(): void; tick(dt: number): void
    meanDelayMs(kind: FlowKind): number               // mean sim delay of delivered packets × 1000; NaN if none
    stateRows(node: NodeId, max?: number): { rows: { key: string, detail: string }[], more: number }
  }
  ```

Behaviour the tests pin (spec "mode=diffserv"): each flow emits packets at `FLOW_RATE / PKT_BITS` per sim second with a seeded random phase. E1 marks voice EF, video AF41, data CS0; the video aggregate passes one RFC 2698 colour-blind trTCM (green → AF41, yellow → AF42, red → AF43); EF above the E1 policer is dropped (`reason 'police'`). Bottleneck output links serve one packet per `PKT_BITS / capacity` s: EF strictly first, then WRR over AF4/AF3/BE by `WRR` weights. Enqueue drop: AF packet dropped when its queue length ≥ `AF_DROP_AT[precedence]`; EF/BE tail-drop at `QUEUE_LIMIT`. At E3 ingress (and only there, at the moment a packet arrives at E3): `trust` keeps the DSCP; `remark` maps AF4y → AF3y and polices EF with `efPoliceB` (excess → CS0); `bleach` sets 0. Cross traffic: CS0 packets created at E3 at `crossB / PKT_BITS` per s, leaving at E4. `stateRows`: E1 → one row per flow (`key` `flow 7`, `detail` `voice → EF`), E3 → three SLA rows (`AF4x → …`, `EF ≤ 0.5 Mbit/s`, `other → as is` / per boundary), core routers and E2/E4 → one row per QueueClass with its current length; `max` default 5, the remainder in `more`.

- [ ] **Step 1: Write the failing tests** in `slides/utils/qos-diffserv.test.ts`:

```ts
test('dscpName and queueOf', () => {
  assert.equal(dscpName(34), 'AF41'); assert.equal(dscpName(0), 'BE'); assert.equal(dscpName(46), 'EF'); assert.equal(dscpName(24), 'CS3')
  assert.equal(queueOf(38), 'AF4'); assert.equal(queueOf(26), 'AF3'); assert.equal(queueOf(10), 'BE'); assert.equal(dropPrecedence(36), 2)
})
test('E1 marks by kind', ...)                     // one of each kind, trust, run 10 s: every delivered voice pkt origDscp 46, video 34, data 0
test('video above CIR is re-marked yellow, above PIR red', ...)  // 4 videos (8 Mbit/s): some AF42, no AF43; 5 videos (10): some AF43
test('EF above the policer is dropped at E1', ...) // 15 voice (1.5 > 1 Mbit/s): drops with node 'E1', reason 'police' > 0
test('EF is protected under overload in A', ...)  // 5 voice + 8 data, A=5: stats.voice.dropped === 0, meanDelayMs(voice) < meanDelayMs(data)
test('AF43 dropped before AF41', ...)             // 6 videos, A=8: count dropped AF43 > dropped AF41
test('bleach puts voice into B\'s BE queue', ...) // 5 voice, A=100, B=10, crossB=12, boundary bleach: voice dropped > 0 and meanDelayMs(voice) > 5× the same run with trust
test('remark maps AF41 to AF31 in B', ...)        // 2 videos, remark: packets past E3 have dscp 26, origDscp 34
test('boundary switch applies only at E3 ingress', ...) // trust run 5 s, switch to bleach: packets with at ∈ {C3,E4} or on 'E3>C3'/'C3>E4' keep their dscp
test('core state does not grow with flows', ...)  // setFlowCount(200): stateRows('C1').rows.length === 4, stateRows('E1').more === 195
test('reset is deterministic', ...)
test('inFlight stays bounded', ...)               // 200 flows, run 60 s: inFlight.length + all queue lengths < 2000
```

- [ ] **Step 2: Run** `node --test utils/qos-diffserv.test.ts` — Expected: FAIL.
- [ ] **Step 3: Implement `DiffServSim`.** Packets on fast links advance by `dt / hopTime`; at each node arrival apply E1/E3 rules, then enqueue on the outgoing link (bottlenecks) or go straight onto the fast link. Keep `stats` as running sums (no per-packet history); `drops` is a ring of 50.
- [ ] **Step 4: Run** `node --test utils/*.test.ts` — Expected: all pass (Task 1 included).
- [ ] **Step 5: Commit** `feat(slides): DiffServ simulation engine for lecture 08`.

---

### Task 3: `QosPathSim.vue` — shell, topology and RSVP view

**Files:**
- Create: `slides/components/QosPathSim.vue`
- Create (scratch, not committed): `/tmp/claude-1000/-home-loki-0-vsb-qos/05cb84e2-319e-4a17-9678-d48cc1c1a72b/scratchpad/shot.mjs`
- Create (temporary, deleted in Task 7): `slides/08-qos-architectures.md` with frontmatter and two test slides `<QosPathSim mode="rsvp" />`, `<QosPathSim mode="diffserv" />`

**Interfaces:**
- Consumes: `RsvpSim` (Task 1), `DiffServSim` (Task 2), topology constants.
- Produces (props of `QosPathSim`):
  ```ts
  defineProps<{ mode: 'rsvp' | 'diffserv', compact?: boolean, flows?: number /* if set, the component follows it via setFlowCount and hides its own flow buttons */,
                capacityA?: number /*10*/, capacityB?: number /*10*/, seed?: number /*1*/, initialFlows?: number /*0*/ }>()
  defineExpose({ stateTotal: () => number })        // sum of stateCount over ROUTERS (used by QosCompare)
  ```

Layout (880 × ~400 px SVG, plus an HTML control row): the 9 nodes on one horizontal line at y≈90 with ≈ 95 px spacing; hosts as rounded boxes, edge routers as double-ring circles, core routers as single circles; two dashed rounded rectangles "Domain A" (E1…E2) and "Domain B" (E3…E4) with the peering link between them labelled "domain boundary"; bottleneck links drawn thicker with a capacity fill bar above (reserved Mbit/s in rsvp mode, queue occupancy in diffserv mode). Under each router a state panel: big count "n entries" and up to 5 rows from the engine, "+ n more" (compact: count only). Controls row: Play/Pause, Step, Reset, speed slider (0.25×–4×), +1 flow, +10 flows, and per mode: rsvp → refresh toggle, "B refuses foreign reservations" toggle, "fail C1" button; diffserv → boundary selector (trust / re-mark / bleach), "cross-traffic in B" slider 0–15 \[Mbit/s\]. Footer line: rsvp → "refresh messages on the bottleneck: x /s (real network, R = 30 s)" and the on-screen note "simplified: state expires after 3 missed refreshes"; diffserv → mean delay per kind at R and drops per kind.

RSVP view: PATH messages as small labelled arrows moving downstream (green), RESV upstream (darker green), ResvErr FMT red; a refusing router flashes red with "ResvErr: capacity" / "policy"; reserved flows' data drawn as a dotted stream along the path in the flow's colour, best-effort/refused flows in muted grey; row age as a fading bar when refresh is off.

- [ ] **Step 1: Write the screenshot script** `shot.mjs` (playwright-chromium from `slides/node_modules`): arguments `<slide> <light|dark> <out.png> [clicks…]`; opens `http://localhost:3030/<slide>`, sets `localStorage['slidev-color-schema']` to the theme before load, optionally clicks buttons by visible text, waits 3 s, screenshots the slide. Start the server with `npx slidev 08-qos-architectures.md --port 3030` in the background.
- [ ] **Step 2: Implement the shell, topology drawing and RSVP view** of `QosPathSim.vue` with a header comment in the style of `GilbertSim.vue` (props, behaviour, print mode). Engine instance in `shallowRef`, rendering driven by a `frame` counter bumped from `requestAnimationFrame`; `onSlideLeave(pause)`; `onBeforeUnmount` cancels the frame.
- [ ] **Step 3: Verify** `npm run build -- 08-qos-architectures.md` exits 0, then screenshots of the rsvp slide in light and dark after clicking "+1 flow" ×6 with capacity 10 (expect one red ResvErr at C1), and after clicking the refresh toggle off and waiting (expect fading rows, flow expired). Read the PNGs and check: labels legible, no light-mode colour in dark, nothing overlapping.
- [ ] **Step 4: Commit** `feat(slides): QosPathSim RSVP view`.

---

### Task 4: `QosPathSim.vue` — DiffServ view and print frames

**Files:**
- Modify: `slides/components/QosPathSim.vue`

**Interfaces:**
- Consumes: `DiffServSim`, `dscpName`, `queueOf` (Task 2); the shell of Task 3.
- Produces: no new props.

DiffServ view: packets as small rounded rectangles carrying their DSCP name (EF / AF41 / AF42 / AF43 / AF31… / BE), filled by class — EF green, AF4 EKF blue at three tints by drop precedence (lighter = higher drop precedence), AF3 the same in the D (dark-green) family, BE muted grey; the label visibly changes at E1 (meter) and at E3 (boundary). At each bottleneck draw the four class queues (EF, AF4, AF3, BE) as stacked bars of packet squares with "EF: strict priority", "AF4 ×3 · AF3 ×2 · BE ×1" captions; dropped packets fall out in FMT red. State panels from `stateRows` (E1 per flow, core per class, E3 per SLA) — the caption under E1 reads "edge: per-flow rules", under cores "core: per-class queues".

Print frames (`isPrintMode`): build an engine with a fixed scenario and advance it deterministically, no controls. RSVP: 2 voice + 5 video at A = 10 (0.2 + 4 × 2 = 8.2 \[Mbit/s\] reserved), so the 5th video is refused at C1, state tables filled, one ResvErr arrow drawn. DiffServ: 4 voice, 4 video, 4 data, `boundary: 'bleach'`, `crossB: 12`, advanced 8 s so an EF-origin packet sits in C3's BE queue; a caption "Domain B bleached the marks: voice now waits with best effort".

- [ ] **Step 1: Implement the DiffServ view.**
- [ ] **Step 2: Implement both print frames.**
- [ ] **Step 3: Verify** build exits 0; screenshots light + dark of the diffserv slide with 4 voice/4 video/4 data, boundary trust then bleach with cross traffic 12 — expect voice delay at R to rise visibly after bleach; then `npm run export -- 08-qos-architectures.md --format png --output /tmp/claude-1000/-home-loki-0-vsb-qos/05cb84e2-319e-4a17-9678-d48cc1c1a72b/scratchpad/print` and view both print frames.
- [ ] **Step 4: Commit** `feat(slides): QosPathSim DiffServ view and print frames`.

---

### Task 5: `QosCompare.vue` — the scaling slide

**Files:**
- Create: `slides/components/QosCompare.vue`

**Interfaces:**
- Consumes: `QosPathSim` props `mode`, `compact`, `flows`, `seed`; exposed `stateTotal()`.
- Produces: `<QosCompare :max="200" />` (prop `max`, default 200).

Two `QosPathSim compact` (rsvp left, diffserv right, both with `capacity-a`/`capacity-b` = 1000 so that nothing is refused and the comparison is about state alone) in a 2-column grid, each scaled to fit 430 px width; one shared flows slider 0…`max`; under each a line "state in the core: n entries" (RSVP: summed over C1, C2, C3; DiffServ: 4 per core router), plus "refresh messages: x /s" for RSVP. Print mode: both frames at flows = 50.

- [ ] **Step 1: Implement `QosCompare.vue`.**
- [ ] **Step 2: Verify** build exits 0; screenshot with the slider at 200 in light and dark: RSVP core state equals 3 core routers × 2 entries (path + resv) × the number of signalled (voice/video) flows — ≈ 960 for 200 flows with the default kind mix — and DiffServ reads "12" (3 core routers × 4 classes); the animation stays smooth (watch the dev server for 20 s with flows = 200, no visible stutter).
- [ ] **Step 3: Commit** `feat(slides): QosCompare scaling view`.

---

### Task 6: Figures for deck 08

**Files:**
- Modify: `slides/scripts/generate-figures.py` (append a `# 08 — QoS architectures` section before the final `print`, keeping the deck sections in numeric order by placing it before the `# 09` section)

**Interfaces:**
- Consumes: `SVG`, `cell`, palette names already in the script.
- Produces: `public/figures/08/{timeline,intserv-router,rsvp-messages,tcb,trtcm,dscp-table,llq,wred-profiles}.svg` and `.dark.svg`.

Contents (spec "Static figures"; old PDF layout is only a hint, redraw everything):
- `timeline` — RFC 1633 (1994) → 2205 (1997) → 2474/2475 (1998) → 2597 (1999) / 3246 (2002) → 2998 (2000) → 3209 (2001) → 4594 (2006) → 8622 (2019) → 9330–9332 (2023), IntServ line above, DiffServ line below.
- `intserv-router` — control plane (reservation set-up agent / RSVP, admission control, traffic control database) above data plane (classifier → packet scheduler with per-flow queues → output), PATH/RESV arrows at the sides.
- `rsvp-messages` — sender, R1, R2, receiver as lifelines; PATH down with "stores previous hop", RESV up with "admission ✓", a refresh pair after 30 s, PathTear.
- `tcb` — classifier → meter → marker / shaper / dropper, labelled "edge only".
- `trtcm` — two buckets (CIR/CBS, PIR/PBS) and the decision green/yellow/red → AFx1/x2/x3.
- `dscp-table` — rows Default (0 / 000000), AF1–AF4 × low/med/high drop with decimal and binary (class bits and drop bits in different colours), EF (46 / 101110), plus a side column CS0–CS7 and LE (1).
- `llq` — strict-priority EF queue + CBWFQ AF4/AF3/BE with weights into one scheduler.
- `wred-profiles` — drop probability vs average queue for AFx3, AFx2, AFx1 (thresholds 10/20/30 to match the component), extending Lecture 03's RED figure style (`red-drop-profile`).

- [ ] **Step 1: Implement the 8 figures.**
- [ ] **Step 2: Verify** `python3 scripts/generate-figures.py` exits 0; `ls public/figures/08/*.svg | wc -l` prints `16`; `git status --short public/figures | grep -v '/08/'` prints nothing (other decks unchanged); `grep -c '#[0-9A-Fa-f]\{6\}' scripts/generate-figures.py` is the same before and after except inside `PALETTES` (no literal colours added). Render 3 figures to PNG (`npx playwright` screenshot of the SVG file or the deck slide) in both themes and look at them.
- [ ] **Step 3: Commit** `feat(slides): figures for lecture 08`.

---

### Task 7: Deck — opening, Part 1, Part 2 (IntServ and RSVP)

**Files:**
- Modify: `slides/08-qos-architectures.md` (replace the Task 3 test slides)

**Interfaces:**
- Consumes: `QosPathSim mode="rsvp"`, figures `timeline`, `intserv-router`, `rsvp-messages`.

Content: spec "Deck content" Opening, Part 1, Part 2, in order. Pinned numbers:
- Guaranteed-service worked example: TSpec $b = 80$ kbit, $R = 2$ Mbit/s, 4 hops, $C_i = 12$ kbit (one 1500-byte packet), $D_i = 0.12$ ms (1500 B at 100 Mbit/s); fluid bound $D \le \frac{b}{R} + \frac{C_{tot}}{R} + D_{tot} = 40 + 24 + 0.48 \approx 64.5$ ms. State the full RFC 2212 bound only in Extras (Task 8).
- Scaling worked example: 100 000 reserved flows through one core router, R = 30 s → $2 \cdot 10^5 / 30 \approx 6\,700$ refresh messages per second per link direction; at an assumed few hundred bytes of state per flow → tens of MB of per-flow state and a per-packet classification over 100 000 entries. Label the per-flow byte count "illustrative".
- Checkpoints: "Why can't each router just do its own QoS?" (Part 1); "A core router reboots mid-call — what happens to the reservation?" (Part 2; answer: data falls back to best effort until the next PATH/RESV refresh rebuilds state — soft state needs no explicit repair).
- The live RSVP slide: title "Live — RSVP across two domains", `<QosPathSim mode="rsvp" :initial-flows="0" />`, notes with a demo script: add 5 videos (reserved), a 6th (refused at C1), switch refresh off (expiry), switch "B refuses foreign reservations" on (policy refusal at E3), fail C1 with refresh on (recovery).

- [ ] **Step 1: Write the slides** (frontmatter, cover with "Lecture 08", "Where we are going" grid with "↔ Lecture 03" links, outcomes, statement, Part 1, Part 2).
- [ ] **Step 2: Verify** `npm run build -- 08-qos-architectures.md` exits 0 with no KaTeX warnings; screenshot every new slide in light mode (and the live slide also dark); check nothing overflows the slide.
- [ ] **Step 3: Commit** `feat(slides): lecture 08 opening and IntServ/RSVP`.

---

### Task 8: Deck — Part 3 (DiffServ), Part 4, closing, Extras

**Files:**
- Modify: `slides/08-qos-architectures.md`

**Interfaces:**
- Consumes: `QosPathSim mode="diffserv"`, `QosCompare`, figures `tcb`, `trtcm`, `dscp-table`, `llq`, `wred-profiles`.

Content: spec "Deck content" Part 3, Part 4, closing, Extras. Pinned:
- DSCP decode exercise: ToS byte `0x88` = `1000 1000` → DSCP `100010` = 34 = AF41, ECN `00`.
- RFC 4594 table rows as listed in the spec.
- Checkpoints: "Everything marked EF" (answer: EF must be policed at the edge; without it EF starves every other class and itself loses its low delay once the EF queue builds); "AF12 vs AF21 — which is dropped first?" (answer: undefined — different classes have separate queues/resources; drop precedence only orders packets within one class).
- Common mix-ups (≥ 5) as listed in the spec.
- Exit questions (3–4) that require applying, e.g. decode a DSCP, predict the effect of bleaching on a voice call, compute refresh load for N flows.
- "Where you use this": `qos-05` (Mininet + `tc`: `htb`/`prio` qdisc with a DSCP filter, e.g. `tc filter add dev s1-eth2 parent 1: protocol ip u32 match ip dsfield 0xb8 0xfc flowid 1:1` in a `bash` fence) and `qos-03` (measure the voice effect).
- References: two slides (standards; literature) with the citations in spec "References to use". **Verify every citation** (author list, title, year) against rfc-editor.org (`https://www.rfc-editor.org/rfc/rfcNNNN`) and the publisher/DBLP page via the web-fetch agent before writing it; drop any measurement-study citation that cannot be confirmed and keep RFC 9435 for the DSCP-modification claim.
- Extras: full RFC 2212 bound ($\frac{b-M}{R}\frac{p-R}{p-r} + \frac{M + C_{tot}}{R} + D_{tot}$ for $p > R \ge r$), Core-Stateless Fair Queueing, 5QI example (3GPP TS 23.501: 5QI 1 conversational voice, GBR, 100 ms packet delay budget).
- The live DiffServ slide `<QosPathSim mode="diffserv" />` with a demo script in notes (load A until BE drops while EF stays clean; push video above CIR/PIR to see AF42/43; switch boundary to bleach with cross traffic 12 to see voice degrade in B); the scaling slide `<QosCompare />` opening Part 4.

- [ ] **Step 1: Verify the citations** and note any dropped.
- [ ] **Step 2: Write the slides.**
- [ ] **Step 3: Verify** build exits 0; screenshot every new slide in light mode, live slides also in dark; count slides and check the timing comment on the cover adds to 90 min.
- [ ] **Step 4: Commit** `feat(slides): lecture 08 DiffServ, comparison and closing`.

---

### Task 9: Cross-deck edits, docs, export

**Files:**
- Modify: `slides/03-qos-mechanisms.md` (notes of the "Extras — a QoS/DiffServ standards timeline" slide: one line "Lecture 08 develops IntServ and DiffServ in full.")
- Modify: `slides/09-sdn-openflow.md` (line ~116 prerequisites → "DSCP and the token bucket from Lecture 03, DiffServ from Lecture 08"; "QoS is the DiffServ of Lecture 03" → "Lecture 08"; "IntServ/DiffServ analogy recalls the Lecture 03 extras" → "Lecture 08"; notes of "OpenFlow as a QoS tool" gain "the classifier/meter/marker chain of Lecture 08's traffic conditioning block")
- Modify: `slides/README.md` (deck table row for `08-qos-architectures.md` with companion labs `qos-03`, `qos-05`; a bullet describing `QosPathSim`/`QosCompare` next to the GilbertSim/QualityExplorer paragraph, including that they print a static frame instead of `export-skip`; mention `node --test utils/*.test.ts`)
- Modify: `/home/loki/0-vsb/qos/CLAUDE.md` (Commands block: `node --test utils/*.test.ts` for the slide engines; one sentence in the slides paragraph naming `QosPathSim`/`QosCompare` and `utils/qos-*.ts`)

- [ ] **Step 1: Make the edits.** Run `grep -n 'Lecture 03' 09-sdn-openflow.md` afterwards and confirm only Lecture-03-specific pointers (token bucket, DSCP byte) remain.
- [ ] **Step 2: Verify** `node --test utils/*.test.ts` passes; `npm run build -- 09-sdn-openflow.md` and `npm run build -- 03-qos-mechanisms.md` exit 0; `npm run export -- 08-qos-architectures.md` writes `08-qos-architectures.pdf`; read the PDF pages with the live slides and confirm complete print frames; `npm run export -- 09-sdn-openflow.md` regenerates 09's PDF.
- [ ] **Step 3: Commit** `docs: lecture 08 cross-references` (include the regenerated `08-qos-architectures.pdf` and `09-sdn-openflow.pdf`, as the other decks' PDFs are tracked; spec and plan docs under `docs/superpowers/`).
