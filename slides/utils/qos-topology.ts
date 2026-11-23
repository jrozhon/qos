// Fixed topology of the lecture 08 simulations (IntServ/RSVP and DiffServ):
//
//   S - E1 - C1 - C2 - E2 | E3 - C3 - E4 - R
//       `---- domain A ---'  `-- domain B --'
//
// One sender S, one receiver R and seven routers; E* are edge routers, C* core
// routers. Only the two bottleneck links are sized by the presenter, every
// other link is fast enough never to matter. Links are listed downstream
// only (S towards R), because both engines use them as reservation keys.

import type { Rand } from './traffic.ts'

export { mulberry32, type Rand } from './traffic.ts'

export type NodeId = 'S' | 'E1' | 'C1' | 'C2' | 'E2' | 'E3' | 'C3' | 'E4' | 'R'

export const PATH: readonly NodeId[] = ['S', 'E1', 'C1', 'C2', 'E2', 'E3', 'C3', 'E4', 'R']
/** The seven routers: PATH without the two hosts. */
export const ROUTERS: readonly NodeId[] = PATH.slice(1, -1)

export const DOMAIN: Record<NodeId, 'host' | 'A' | 'B'> = {
  S: 'host', E1: 'A', C1: 'A', C2: 'A', E2: 'A', E3: 'B', C3: 'B', E4: 'B', R: 'host',
}
export const ROLE: Record<NodeId, 'host' | 'edge' | 'core'> = {
  S: 'host', E1: 'edge', C1: 'core', C2: 'core', E2: 'edge', E3: 'edge', C3: 'core', E4: 'edge', R: 'host',
}

export type LinkId = `${NodeId}>${NodeId}`
/** The eight links between consecutive PATH nodes. */
export const LINKS: readonly LinkId[] = PATH.slice(0, -1).map((n, i) => `${n}>${PATH[i + 1]}` as LinkId)

export const BOTTLENECK_A: LinkId = 'C1>C2'
export const BOTTLENECK_B: LinkId = 'C3>E4'
/** Mbit/s of every non-bottleneck link. */
export const FAST_LINK = 100

export type FlowKind = 'voice' | 'video' | 'data'
/** Mbit/s per flow. */
export const FLOW_RATE: Record<FlowKind, number> = { voice: 0.1, video: 2, data: 1 }

/** Mbit/s of the two bottleneck links. */
export interface Capacities { A: number, B: number }

/** Mbit/s of a link; a fast link is never slower than the bottlenecks (FAST_LINK, or the larger bottleneck when that is faster). */
export function linkCapacity(link: LinkId, cap: Capacities): number {
  if (link === BOTTLENECK_A) return cap.A
  if (link === BOTTLENECK_B) return cap.B
  return Math.max(FAST_LINK, cap.A, cap.B)
}

export function next(node: NodeId): NodeId | null {
  return PATH[PATH.indexOf(node) + 1] ?? null
}
export function prev(node: NodeId): NodeId | null {
  const i = PATH.indexOf(node)
  return i > 0 ? PATH[i - 1] : null
}

/** Random flow kind: voice 50 %, video 30 %, data 20 %. */
export function drawKind(rand: Rand): FlowKind {
  const u = rand()
  return u < 0.5 ? 'voice' : u < 0.8 ? 'video' : 'data'
}
