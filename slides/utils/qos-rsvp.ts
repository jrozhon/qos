// RSVP/IntServ simulation for lecture 08: PATH goes S -> R, RESV comes back
// R -> S and is admission-checked at every router against the downstream link.
//
// Simplifications against RFC 2205, chosen so a slide can show the mechanism:
//  - time is in simulated seconds; refreshPeriod = 3 s stands for the real 30 s,
//    and refreshMsgPerSecond() converts back to real-network numbers;
//  - soft state expires after 3 missed refreshes (age > 3 * refreshPeriod), the
//    RFC's lifetime formula is not modelled;
//  - PATH and RESV refreshes are sent independently by S and R at every period
//    (real routers each run their own timers);
//  - finishing the setup counts as the first refresh: ages of the flow's state
//    are reset when RESV reaches S;
//  - one fixed path, no merging, no teardown messages (removeFlow clears
//    the state at once, as a PathTear would);
//  - only the bottleneck links ever run out of capacity (see qos-topology.ts).
// All randomness (flow kinds) comes from a seeded PRNG, so a run replays exactly.

import {
  type Capacities, type FlowKind, type LinkId, type NodeId,
  FLOW_RATE, ROUTERS, drawKind, linkCapacity, mulberry32, next, prev,
} from './qos-topology.ts'
import type { Rand } from './qos-topology.ts'

export type MsgType = 'PATH' | 'RESV' | 'ResvErr'
export interface Msg { type: MsgType, flow: number, from: NodeId, to: NodeId, t: number /* 0..1 along the hop */, refresh: boolean }
export type FlowStatus = 'signalling' | 'reserved' | 'refused' | 'expired' | 'besteffort'
export interface RsvpFlow { id: number, kind: FlowKind, rate: number, status: FlowStatus, refusedAt?: NodeId, reason?: 'capacity' | 'policy' }
export interface PathEntry { flow: number, phop: NodeId, rate: number, age: number }
export interface ResvEntry { flow: number, link: LinkId, rate: number, age: number }
export interface RsvpConfig {
  cap: Capacities
  refresh: boolean
  /** Simulated seconds between refreshes; stands for 30 s in a real network. */
  refreshPeriod: number
  /** Simulated seconds per hop. */
  hopTime: number
  /** E3 refuses every new reservation (a foreign domain with its own policy). */
  foreignPolicy: boolean
  seed: number
}

/** Above this many reserved flows, refreshes update ages directly instead of creating Msg objects. */
export const MAX_ANIMATED_REFRESH = 20
/** Real-network refresh period in seconds, for refreshMsgPerSecond(). */
const REAL_REFRESH_PERIOD = 30
/** Tolerance for floating-point time comparisons. */
const EPS = 1e-9

const ALL_NODES: NodeId[] = ['S', 'E1', 'C1', 'C2', 'E2', 'E3', 'C3', 'E4', 'R']

function emptyTables<T>(): Record<NodeId, Map<number, T>> {
  return Object.fromEntries(ALL_NODES.map(n => [n, new Map<number, T>()])) as Record<NodeId, Map<number, T>>
}

export class RsvpSim {
  cfg: RsvpConfig
  time = 0
  flows: RsvpFlow[] = []
  msgs: Msg[] = []
  path: Record<NodeId, Map<number, PathEntry>> = emptyTables()
  resv: Record<NodeId, Map<number, ResvEntry>> = emptyTables()
  private rng: Rand
  private nextId = 1
  private nextRefresh: number

  constructor(cfg: Partial<RsvpConfig> = {}) {
    this.cfg = {
      refresh: true, refreshPeriod: 3, hopTime: 0.25, foreignPolicy: false, seed: 1,
      ...cfg,
      cap: { A: 10, B: 10, ...cfg.cap },
    }
    this.rng = mulberry32(this.cfg.seed)
    this.nextRefresh = this.cfg.refreshPeriod
  }

  /** Back to time 0 with the same seed and configuration, no flows. */
  reset(): void {
    this.time = 0
    this.flows = []
    this.msgs = []
    this.path = emptyTables()
    this.resv = emptyTables()
    this.rng = mulberry32(this.cfg.seed)
    this.nextId = 1
    this.nextRefresh = this.cfg.refreshPeriod
  }

  /** Add a flow; data flows are best effort and signal nothing. */
  addFlow(kind?: FlowKind): RsvpFlow {
    const k = kind ?? drawKind(this.rng)
    const flow: RsvpFlow = { id: this.nextId++, kind: k, rate: FLOW_RATE[k], status: k === 'data' ? 'besteffort' : 'signalling' }
    this.flows.push(flow)
    if (k !== 'data') this.send('PATH', flow.id, 'S', 'E1', false)
    return flow
  }

  /** Tear a flow down: its state disappears everywhere at once. */
  removeFlow(id: number): void {
    this.flows = this.flows.filter(f => f.id !== id)
    this.msgs = this.msgs.filter(m => m.flow !== id)
    for (const n of ALL_NODES) {
      this.path[n].delete(id)
      this.resv[n].delete(id)
    }
  }

  /** Add random flows or remove the newest ones until there are exactly n. */
  setFlowCount(n: number): void {
    while (this.flows.length > n) this.removeFlow(this.flows[this.flows.length - 1].id)
    while (this.flows.length < n) this.addFlow()
  }

  /** A router crash: it forgets all its soft state (and nothing else). */
  failRouter(node: NodeId): void {
    this.path[node].clear()
    this.resv[node].clear()
  }

  /** Mbit/s reserved on a link. */
  reserved(link: LinkId): number {
    const from = link.split('>')[0] as NodeId
    let sum = 0
    for (const e of this.resv[from].values()) if (e.link === link) sum += e.rate
    return sum
  }

  /** Number of soft-state entries a router holds (hosts hold none). */
  stateCount(node: NodeId): number {
    return this.path[node].size + this.resv[node].size
  }

  /** What the refreshes would cost in a real network: PATH + RESV per reserved flow every 30 s. */
  refreshMsgPerSecond(): number {
    return 2 * this.reservedFlows().length / REAL_REFRESH_PERIOD
  }

  /** Advance simulated time by dt >= 0, handling every event in time order. */
  tick(dt: number): void {
    let left = dt
    for (;;) {
      const step = Math.min(left, this.untilEvent())
      this.advance(step)
      left -= step
      const handled = this.handleDue()
      if (left <= EPS && !handled) break
    }
  }

  /** Advance to the next message arrival or refresh event. */
  step(): void {
    this.tick(this.untilEvent())
  }

  // --- internals -----------------------------------------------------------

  private reservedFlows(): RsvpFlow[] {
    return this.flows.filter(f => f.status === 'reserved')
  }

  private send(type: MsgType, flow: number, from: NodeId, to: NodeId, refresh: boolean): void {
    this.msgs.push({ type, flow, from, to, t: 0, refresh })
  }

  /** Simulated seconds until the next message arrival or refresh event (never negative). */
  private untilEvent(): number {
    let d = Math.max(0, this.nextRefresh - this.time)
    for (const m of this.msgs) d = Math.min(d, Math.max(0, (1 - m.t) * this.cfg.hopTime))
    return d
  }

  /** Move the clock: message positions and entry ages grow, old state is dropped. */
  private advance(dt: number): void {
    if (dt <= 0) return
    this.time += dt
    for (const m of this.msgs) m.t += dt / this.cfg.hopTime
    for (const n of ALL_NODES) {
      for (const e of this.path[n].values()) e.age += dt
      for (const e of this.resv[n].values()) e.age += dt
    }
    this.expire()
  }

  /** Delete entries older than 3 refresh periods; a reserved flow that loses one is expired. */
  private expire(): void {
    const limit = 3 * this.cfg.refreshPeriod + EPS
    const lost = new Set<number>()
    for (const n of ALL_NODES) {
      for (const [id, e] of this.path[n]) if (e.age > limit) { this.path[n].delete(id); lost.add(id) }
      for (const [id, e] of this.resv[n]) if (e.age > limit) { this.resv[n].delete(id); lost.add(id) }
    }
    for (const id of lost) {
      const f = this.flows.find(x => x.id === id)
      if (f?.status !== 'reserved') continue
      f.status = 'expired'
      for (const n of ALL_NODES) this.resv[n].delete(id) // bandwidth is released
    }
  }

  /** Process messages that have arrived and a refresh event that is due; true if anything was handled. */
  private handleDue(): boolean {
    let handled = false
    const arrived = this.msgs.filter(m => m.t >= 1 - EPS)
    if (arrived.length) {
      handled = true
      this.msgs = this.msgs.filter(m => m.t < 1 - EPS)
      for (const m of arrived) this.arrive(m)
    }
    if (this.time >= this.nextRefresh - EPS) {
      handled = true
      this.nextRefresh += this.cfg.refreshPeriod
      if (this.cfg.refresh) this.refreshAll()
    }
    return handled
  }

  private arrive(m: Msg): void {
    const flow = this.flows.find(f => f.id === m.flow)
    if (!flow) return
    if (m.type === 'PATH') this.arrivePath(m, flow)
    else if (m.type === 'RESV') this.arriveResv(m, flow)
    else this.arriveErr(m)
  }

  private arrivePath(m: Msg, flow: RsvpFlow): void {
    const at = m.to
    if (at === 'R') {
      if (!m.refresh && flow.status === 'signalling') this.send('RESV', flow.id, 'R', prev('R')!, false)
      return
    }
    this.path[at].set(flow.id, { flow: flow.id, phop: m.from, rate: flow.rate, age: 0 })
    this.send('PATH', flow.id, at, next(at)!, m.refresh)
  }

  private arriveResv(m: Msg, flow: RsvpFlow): void {
    const at = m.to
    if (m.refresh ? flow.status !== 'reserved' : flow.status !== 'signalling') return
    if (at === 'S') {
      if (!m.refresh) {
        flow.status = 'reserved'
        this.resetAges(flow.id) // finishing the setup counts as the first refresh
      }
      return
    }
    if (!this.installResv(flow, at)) return
    this.send('RESV', flow.id, at, prev(at)!, m.refresh)
  }

  private arriveErr(m: Msg): void {
    const at = m.to
    if (at === 'R') return
    this.resv[at].delete(m.flow)
    this.send('ResvErr', m.flow, at, next(at)!, false)
  }

  /**
   * Admission control at a router for the link towards R. An existing entry is
   * just refreshed; a new one needs room on the link (and the foreign domain's
   * consent at E3). On refusal the flow is marked refused and a ResvErr cleans
   * up downstream. Returns whether the RESV may travel on.
   */
  private installResv(flow: RsvpFlow, at: NodeId): boolean {
    const existing = this.resv[at].get(flow.id)
    if (existing) { existing.age = 0; return true }
    const link = `${at}>${next(at)}` as LinkId
    let reason: 'capacity' | 'policy' | null = null
    if (this.cfg.foreignPolicy && at === 'E3') reason = 'policy'
    else if (this.reserved(link) + flow.rate > linkCapacity(link, this.cfg.cap) + EPS) reason = 'capacity'
    if (reason) {
      flow.status = 'refused'
      flow.refusedAt = at
      flow.reason = reason
      for (const n of ROUTERS) this.resv[n].delete(flow.id) // upstream leftovers of a refused refresh
      this.send('ResvErr', flow.id, at, next(at)!, false)
      return false
    }
    this.resv[at].set(flow.id, { flow: flow.id, link, rate: flow.rate, age: 0 })
    return true
  }

  private resetAges(id: number): void {
    for (const n of ALL_NODES) {
      const p = this.path[n].get(id)
      if (p) p.age = 0
      const r = this.resv[n].get(id)
      if (r) r.age = 0
    }
  }

  /** One refresh period: every reserved flow re-sends PATH (from S) and RESV (from R). */
  private refreshAll(): void {
    const flows = this.reservedFlows()
    if (flows.length > MAX_ANIMATED_REFRESH) {
      for (const f of flows) {
        for (const n of ROUTERS) {
          this.path[n].set(f.id, { flow: f.id, phop: prev(n)!, rate: f.rate, age: 0 })
        }
        for (const n of [...ROUTERS].reverse()) {
          if (f.status === 'reserved') this.installResv(f, n) // downstream first, as RESV would
        }
      }
      return
    }
    for (const f of flows) {
      this.send('PATH', f.id, 'S', 'E1', true)
      this.send('RESV', f.id, 'R', prev('R')!, true)
    }
  }
}
