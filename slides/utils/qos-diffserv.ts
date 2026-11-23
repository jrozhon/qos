// DiffServ simulation for lecture 08: one sender S emits voice, video and data
// flows along S - E1 - C1 - C2 - E2 | E3 - C3 - E4 - R. E1 classifies and
// meters, the two bottleneck links run a priority + WRR scheduler per class,
// and the E3 ingress applies the SLA between the domains.
//
// Simplifications, chosen so a slide can show the mechanism:
//  - a packet stands for PKT_BITS = 0.1 Mbit; a flow of r Mbit/s emits r / PKT_BITS
//    packets per simulated second, starting at a seeded random phase;
//  - every fast link is only a delay (hopTime); the queue and the scheduler live
//    at the output of C1 (link C1>C2) and C3 (link C3>E4), and the served packet
//    then travels the link in hopTime; delay is measured from creation at S (or
//    E3 for cross traffic) to arrival at R (or E4 for cross traffic), so it
//    includes 8 hops of propagation;
//  - the packet being served stays counted in its class queue until it leaves;
//  - the trTCM (RFC 2698, colour-blind) and the EF policers are token buckets
//    in Mbit refilled lazily when a packet arrives; each packet takes PKT_BITS;
//  - WRR is by packets with credits reset when every non-empty class used up its
//    weight; EF is strict priority over all of them;
//  - the SLA at E3 acts only when a packet arrives at E3: switching the boundary
//    mid-run does not touch packets already past it;
//  - origDscp is the DSCP E1 gave the packet by kind (EF / AF41 / CS0), before the
//    meter re-marked it and before the E3 boundary changed it;
//  - the model is event driven, so one tick(dt) equals many smaller ones.
// All randomness (flow kinds, phases) comes from a seeded PRNG, so a run replays exactly.

import {
  type Capacities, type FlowKind, type LinkId, type NodeId, type Rand,
  BOTTLENECK_A, BOTTLENECK_B, FLOW_RATE, LINKS, drawKind, linkCapacity, mulberry32, next,
} from './qos-topology.ts'

export const DSCP = {
  CS0: 0, LE: 1, AF11: 10, AF12: 12, AF13: 14, AF21: 18, AF22: 20, AF23: 22, AF31: 26, AF32: 28, AF33: 30,
  AF41: 34, AF42: 36, AF43: 38, CS1: 8, CS2: 16, CS3: 24, CS4: 32, CS5: 40, VA: 44, EF: 46, CS6: 48, CS7: 56,
} as const

const NAMES = new Map<number, string>(Object.entries(DSCP).map(([k, v]) => [v, k]))
NAMES.set(0, 'BE')

export function dscpName(d: number): string { return NAMES.get(d) ?? String(d) }

export type QueueClass = 'EF' | 'AF4' | 'AF3' | 'BE'
const QUEUE_CLASSES: readonly QueueClass[] = ['EF', 'AF4', 'AF3', 'BE']

export function queueOf(dscp: number): QueueClass {
  if (dscp === DSCP.EF) return 'EF'
  if (dscp === DSCP.AF41 || dscp === DSCP.AF42 || dscp === DSCP.AF43) return 'AF4'
  if (dscp === DSCP.AF31 || dscp === DSCP.AF32 || dscp === DSCP.AF33) return 'AF3'
  return 'BE'
}

export function dropPrecedence(dscp: number): 1 | 2 | 3 {
  const af = dscp >= 10 && dscp <= 38 && dscp % 2 === 0 && dscp % 8 !== 0 && dscp % 8 <= 6 && (dscp >> 3) <= 4
  return af ? ((dscp % 8) / 2) as 1 | 2 | 3 : 1
}

/** Mbit per drawn packet. */
export const PKT_BITS = 0.1
/** Packets per class queue. */
export const QUEUE_LIMIT = 30
/** AF queue length at which that drop precedence is dropped. */
export const AF_DROP_AT: Record<1 | 2 | 3, number> = { 3: 10, 2: 20, 1: 30 }
/** Weights of the weighted round robin that runs after strict-priority EF. */
export const WRR: Record<'AF4' | 'AF3' | 'BE', number> = { AF4: 3, AF3: 2, BE: 1 }
const WRR_ORDER: readonly ('AF4' | 'AF3' | 'BE')[] = ['AF4', 'AF3', 'BE']
const DROP_RING = 50

export type Boundary = 'trust' | 'remark' | 'bleach'
export interface Pkt {
  id: number
  /** Flow id, -1 for cross traffic. */
  flow: number
  kind: FlowKind | 'cross'
  dscp: number
  origDscp: number
  /** Node the packet is at, or the node it left when it is on a link. */
  at: NodeId
  link: LinkId | null
  /** Progress along the link, 0..1. */
  t: number
  born: number
}
export interface DsConfig {
  cap: Capacities
  boundary: Boundary
  /** Mbit/s of best-effort cross traffic injected at E3 towards E4. */
  crossB: number
  /** EF policer at E1: rate in Mbit/s, burst in Mbit. */
  efPolice: { rate: number, burst: number }
  /** trTCM of the video aggregate at E1, rates in Mbit/s, buckets in Mbit. */
  videoMeter: { cir: number, pir: number, cbs: number, pbs: number }
  /** EF policer at E3 under 'remark'; excess EF becomes CS0. */
  efPoliceB: { rate: number, burst: number }
  /** Simulated seconds per fast hop. */
  hopTime: number
  seed: number
}
export interface ClassStats { sent: number, dropped: number, delivered: number, delaySum: number }
export type DropReason = 'police' | 'queue'
export interface DropRecord { pkt: Pkt, node: NodeId, reason: DropReason }

const DEFAULTS: DsConfig = {
  cap: { A: 100, B: 100 }, boundary: 'trust', crossB: 0,
  efPolice: { rate: 1, burst: 0.3 },
  videoMeter: { cir: 6, pir: 8, cbs: 0.3, pbs: 0.3 },
  efPoliceB: { rate: 0.5, burst: 0.3 },
  hopTime: 0.2, seed: 1,
}

const REMARK_B: Record<number, number> = { 34: 26, 36: 28, 38: 30 }

type Ev =
  | { t: number, seq: number, type: 'emit', flow: FlowRec }
  | { t: number, seq: number, type: 'cross' }
  | { t: number, seq: number, type: 'arrive', pkt: Pkt, node: NodeId }
  | { t: number, seq: number, type: 'done', link: LinkId }
interface FlowRec { id: number, kind: FlowKind, phase: number, alive: boolean }
interface Bucket { tokens: number, last: number }

function newStats(): ClassStats { return { sent: 0, dropped: 0, delivered: 0, delaySum: 0 } }
function emptyQueues(): Record<QueueClass, Pkt[]> { return { EF: [], AF4: [], AF3: [], BE: [] } }

export class DiffServSim {
  cfg: DsConfig
  time = 0
  flows: { id: number, kind: FlowKind }[] = []
  inFlight: Pkt[] = []
  queues!: Record<LinkId, Record<QueueClass, Pkt[]>>
  drops: DropRecord[] = []
  stats!: Record<FlowKind | 'cross', ClassStats>

  private rand: Rand
  private heap: Ev[] = []
  private seq = 0
  private nextPkt = 1
  private nextFlow = 1
  private recs = new Map<number, FlowRec>()
  private onLink = new Map<Pkt, number>()   // packet -> time it entered the link
  private serving = new Map<LinkId, { pkt: Pkt, cls: QueueClass }>()
  private credits = new Map<LinkId, Record<'AF4' | 'AF3' | 'BE', number>>()
  private bEf!: Bucket
  private bB!: Bucket
  private bTc!: Bucket
  private bTp!: Bucket

  constructor(cfg: Partial<DsConfig> = {}) {
    this.cfg = { ...DEFAULTS, ...cfg }
    this.rand = mulberry32(this.cfg.seed)
    this.init()
  }

  private init(): void {
    this.time = 0; this.heap = []; this.seq = 0; this.nextPkt = 1
    this.flows = []; this.recs.clear(); this.inFlight = []; this.onLink.clear()
    this.serving.clear(); this.credits.clear(); this.drops = []
    this.queues = Object.fromEntries(LINKS.map(l => [l, emptyQueues()])) as Record<LinkId, Record<QueueClass, Pkt[]>>
    this.stats = { voice: newStats(), video: newStats(), data: newStats(), cross: newStats() }
    const m = this.cfg.videoMeter
    this.bEf = { tokens: this.cfg.efPolice.burst, last: 0 }
    this.bB = { tokens: this.cfg.efPoliceB.burst, last: 0 }
    this.bTc = { tokens: m.cbs, last: 0 }; this.bTp = { tokens: m.pbs, last: 0 }
    this.schedule({ t: 0.05, type: 'cross' })
  }

  addFlow(kind?: FlowKind): void {
    const k = kind ?? drawKind(this.rand)
    this.insertFlow(this.nextFlow++, k, this.rand() * (PKT_BITS / FLOW_RATE[k]), this.time)
  }
  private insertFlow(id: number, kind: FlowKind, phase: number, from: number): void {
    const rec: FlowRec = { id, kind, phase, alive: true }
    this.recs.set(id, rec); this.flows.push({ id, kind })
    this.schedule({ t: from + phase, type: 'emit', flow: rec })
  }
  removeFlow(id: number): void {
    const rec = this.recs.get(id); if (!rec) return
    rec.alive = false; this.recs.delete(id)
    this.flows = this.flows.filter(f => f.id !== id)
  }
  setFlowCount(n: number): void {
    while (this.flows.length > n) this.removeFlow(this.flows[this.flows.length - 1].id)
    while (this.flows.length < n) this.addFlow()
  }

  /** Back to t = 0 with the same flows (same ids, same phases) and an empty network. */
  reset(): void {
    const keep = [...this.recs.values()]
    const nextFlow = this.nextFlow
    this.init()
    for (const r of keep) this.insertFlow(r.id, r.kind, r.phase, 0)
    this.nextFlow = nextFlow
  }

  tick(dt: number): void {
    const target = this.time + dt
    for (;;) {
      const ev = this.heap[0]
      if (!ev || ev.t > target) break
      this.pop()
      this.time = ev.t
      this.handle(ev)
    }
    this.time = target
    this.syncInFlight()
  }

  meanDelayMs(kind: FlowKind): number {
    const s = this.stats[kind]
    return s.delivered ? s.delaySum / s.delivered * 1000 : NaN
  }

  stateRows(node: NodeId, max = 5): { rows: { key: string, detail: string }[], more: number } {
    let rows: { key: string, detail: string }[] = []
    if (node === 'E1') {
      rows = this.flows.map(f => ({ key: `flow ${f.id}`, detail: `${f.kind} → ${dscpName(MARK[f.kind])}` }))
    } else if (node === 'E3') {
      const b = this.cfg.boundary
      rows = [
        { key: 'AF4x', detail: b === 'remark' ? '→ AF3x' : b === 'bleach' ? '→ BE' : 'as is' },
        { key: 'EF', detail: b === 'remark' ? `≤ ${this.cfg.efPoliceB.rate} Mbit/s` : b === 'bleach' ? '→ BE' : 'as is' },
        { key: 'other', detail: b === 'bleach' ? '→ BE' : 'as is' },
      ]
    } else {
      const out = (`${node}>${next(node)}`) as LinkId
      const q = this.queues[out]
      rows = QUEUE_CLASSES.map(c => ({ key: c, detail: `${q?.[c].length ?? 0} pkt` }))
    }
    return { rows: rows.slice(0, max), more: Math.max(0, rows.length - max) }
  }

  // ---- event machinery ------------------------------------------------------

  private schedule(e: Omit<Ev, 'seq'> & { seq?: number }): void {
    const ev = { ...e, seq: this.seq++ } as Ev
    const h = this.heap; h.push(ev)
    let i = h.length - 1
    while (i > 0) {
      const p = (i - 1) >> 1
      if (!before(h[i], h[p])) break
      ;[h[i], h[p]] = [h[p], h[i]]; i = p
    }
  }
  private pop(): void {
    const h = this.heap; const last = h.pop()!
    if (!h.length) return
    h[0] = last
    let i = 0
    for (;;) {
      const l = 2 * i + 1; const r = l + 1; let m = i
      if (l < h.length && before(h[l], h[m])) m = l
      if (r < h.length && before(h[r], h[m])) m = r
      if (m === i) break
      ;[h[i], h[m]] = [h[m], h[i]]; i = m
    }
  }

  private handle(ev: Ev): void {
    switch (ev.type) {
      case 'emit': {
        if (!ev.flow.alive) return
        const k = ev.flow.kind
        this.stats[k].sent++
        this.arrive(this.newPkt(ev.flow.id, k, 'S'), 'E1')
        this.schedule({ t: ev.t + PKT_BITS / FLOW_RATE[k], type: 'emit', flow: ev.flow })
        return
      }
      case 'cross': {
        const rate = this.cfg.crossB
        if (rate > 0) {
          this.stats.cross.sent++
          this.forward(this.newPkt(-1, 'cross', 'E3'), 'E3')
        }
        this.schedule({ t: ev.t + (rate > 0 ? PKT_BITS / rate : 0.1), type: 'cross' })
        return
      }
      case 'arrive': {
        this.onLink.delete(ev.pkt)
        this.inFlightSet.delete(ev.pkt)
        this.arrive(ev.pkt, ev.node)
        return
      }
      case 'done': {
        const s = this.serving.get(ev.link)!
        this.serving.delete(ev.link)
        this.queues[ev.link][s.cls].shift()
        this.launch(s.pkt, ev.link)
        this.startService(ev.link)
      }
    }
  }

  private inFlightSet = new Set<Pkt>()
  private syncInFlight(): void {
    const h = this.cfg.hopTime
    for (const p of this.inFlightSet) p.t = Math.min(1, Math.max(0, (this.time - this.onLink.get(p)!) / h))
    this.inFlight.length = 0
    for (const p of this.inFlightSet) this.inFlight.push(p)
  }

  private newPkt(flow: number, kind: FlowKind | 'cross', at: NodeId): Pkt {
    return { id: this.nextPkt++, flow, kind, dscp: 0, origDscp: 0, at, link: null, t: 0, born: this.time }
  }

  private launch(pkt: Pkt, link: LinkId): void {
    const to = link.split('>')[1] as NodeId
    pkt.at = link.split('>')[0] as NodeId; pkt.link = link; pkt.t = 0
    this.onLink.set(pkt, this.time); this.inFlightSet.add(pkt)
    this.schedule({ t: this.time + this.cfg.hopTime, type: 'arrive', pkt, node: to })
  }

  private drop(pkt: Pkt, node: NodeId, reason: DropReason): void {
    pkt.at = node; pkt.link = null
    if (pkt.kind !== 'cross') this.stats[pkt.kind].dropped++; else this.stats.cross.dropped++
    this.drops.push({ pkt, node, reason })
    if (this.drops.length > DROP_RING) this.drops.shift()
  }

  /** The packet has reached `node`: apply the node's rules, then forward or deliver. */
  private arrive(pkt: Pkt, node: NodeId): void {
    pkt.at = node; pkt.link = null; pkt.t = 0
    if (node === 'R' || (node === 'E4' && pkt.kind === 'cross')) {
      const s = this.stats[pkt.kind]
      s.delivered++; s.delaySum += this.time - pkt.born
      return
    }
    if (node === 'E1' && !this.classify(pkt)) return
    if (node === 'E3' && !this.ingressB(pkt)) return
    this.forward(pkt, node)
  }

  /** E1: mark by kind, meter video, police EF. Returns false when the packet was dropped. */
  private classify(pkt: Pkt): boolean {
    const kind = pkt.kind as FlowKind
    pkt.dscp = pkt.origDscp = MARK[kind]
    if (kind === 'voice') {
      if (!this.take(this.bEf, this.cfg.efPolice, PKT_BITS)) { this.drop(pkt, 'E1', 'police'); return false }
    } else if (kind === 'video') {
      const m = this.cfg.videoMeter
      this.refill(this.bTc, m.cir, m.cbs); this.refill(this.bTp, m.pir, m.pbs)
      if (this.bTp.tokens < PKT_BITS) pkt.dscp = DSCP.AF43
      else if (this.bTc.tokens < PKT_BITS) { this.bTp.tokens -= PKT_BITS; pkt.dscp = DSCP.AF42 }
      else { this.bTp.tokens -= PKT_BITS; this.bTc.tokens -= PKT_BITS }
    }
    return true
  }

  /** E3 ingress under the configured boundary. Returns false when the packet was dropped. */
  private ingressB(pkt: Pkt): boolean {
    const b = this.cfg.boundary
    if (b === 'bleach') pkt.dscp = 0
    else if (b === 'remark') {
      if (pkt.dscp === DSCP.EF) {
        if (!this.take(this.bB, this.cfg.efPoliceB, PKT_BITS)) pkt.dscp = 0
      } else if (REMARK_B[pkt.dscp] !== undefined) pkt.dscp = REMARK_B[pkt.dscp]
    }
    return true
  }

  private refill(b: Bucket, rate: number, burst: number): void {
    b.tokens = Math.min(burst, b.tokens + (this.time - b.last) * rate); b.last = this.time
  }
  private take(b: Bucket, p: { rate: number, burst: number }, size: number): boolean {
    this.refill(b, p.rate, p.burst)
    if (b.tokens < size) return false
    b.tokens -= size; return true
  }

  private forward(pkt: Pkt, node: NodeId): void {
    const to = next(node)!
    const link = `${node}>${to}` as LinkId
    if (link !== BOTTLENECK_A && link !== BOTTLENECK_B) { this.launch(pkt, link); return }
    const cls = queueOf(pkt.dscp)
    const q = this.queues[link][cls]
    const limit = cls === 'AF4' || cls === 'AF3' ? AF_DROP_AT[dropPrecedence(pkt.dscp)] : QUEUE_LIMIT
    if (q.length >= limit) { this.drop(pkt, node, 'queue'); return }
    pkt.at = node; pkt.link = link; pkt.t = 0
    q.push(pkt)
    if (!this.serving.has(link)) this.startService(link)
  }

  private startService(link: LinkId): void {
    const cls = this.pickClass(link)
    if (!cls) return
    const pkt = this.queues[link][cls][0]
    this.serving.set(link, { pkt, cls })
    this.schedule({ t: this.time + PKT_BITS / linkCapacity(link, this.cfg.cap), type: 'done', link })
  }

  private pickClass(link: LinkId): QueueClass | null {
    const q = this.queues[link]
    if (q.EF.length) return 'EF'
    let c = this.credits.get(link)
    if (!c) { c = { ...WRR }; this.credits.set(link, c) }
    for (let pass = 0; pass < 2; pass++) {
      for (const cls of WRR_ORDER) if (q[cls].length && c[cls] > 0) { c[cls]--; return cls }
      if (!WRR_ORDER.some(k => q[k].length)) return null
      Object.assign(c, WRR)
    }
    return null
  }
}

const MARK: Record<FlowKind, number> = { voice: DSCP.EF, video: DSCP.AF41, data: DSCP.CS0 }

function before(a: Ev, b: Ev): boolean { return a.t < b.t || (a.t === b.t && a.seq < b.seq) }
