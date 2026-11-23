import { test } from 'node:test'
import assert from 'node:assert/strict'
import { MAX_ANIMATED_REFRESH, RsvpSim } from './qos-rsvp.ts'
import { ROUTERS } from './qos-topology.ts'

const run = (sim: RsvpSim, s: number) => { for (let i = 0; i < s * 100; i++) sim.tick(0.01) }
const runUntil = (sim: RsvpSim, t: number) => { while (sim.time < t - 1e-9) sim.tick(0.01) }
const noResv = (sim: RsvpSim, id: number, nodes: readonly string[]) => {
  for (const r of nodes) assert.equal(sim.resv[r as keyof typeof sim.resv].has(id), false, `resv at ${r}`)
}

test('one voice flow reserves on every router', () => {
  const sim = new RsvpSim({ seed: 1 }); const f = sim.addFlow('voice'); run(sim, 5)
  assert.equal(f.status, 'reserved')
  for (const r of ROUTERS) { assert.equal(sim.path[r].has(f.id), true); assert.equal(sim.resv[r].has(f.id), true) }
  assert.equal(sim.reserved('C1>C2'), 0.1)
})

test('PATH reaches R before any RESV exists', () => {
  const hop = 0.25
  const sim = new RsvpSim({ seed: 1, hopTime: hop }); const f = sim.addFlow('voice')
  // 7.5 hops: PATH is still on its last hop, nothing reserved
  sim.tick(7.5 * hop)
  assert.deepEqual(sim.msgs.map(m => [m.type, m.from, m.to]), [['PATH', 'E4', 'R']])
  noResv(sim, f.id, ROUTERS)
  // 8.5 hops: PATH has reached R, which answered with a RESV that is still on its first hop
  sim.tick(hop)
  assert.deepEqual(sim.msgs.map(m => [m.type, m.from, m.to]), [['RESV', 'R', 'E4']])
  for (const r of ROUTERS) assert.equal(sim.path[r].has(f.id), true)
  noResv(sim, f.id, ROUTERS)
})

test('sixth video flow is refused at C1 with capacity 10', () => {
  const sim = new RsvpSim({ seed: 1, cap: { A: 10, B: 100 } })
  const fs = Array.from({ length: 6 }, () => sim.addFlow('video')); run(sim, 10)
  assert.deepEqual(fs.map(f => f.status), ['reserved', 'reserved', 'reserved', 'reserved', 'reserved', 'refused'])
  assert.equal(fs[5].refusedAt, 'C1'); assert.equal(fs[5].reason, 'capacity')
  for (const r of ['C2', 'E2', 'E3', 'C3', 'E4']) assert.equal(sim.resv[r].has(fs[5].id), false)
  assert.equal(sim.reserved('C1>C2'), 10)
})

test('refusal in domain B at C3', () => {
  const sim = new RsvpSim({ seed: 1, cap: { A: 100, B: 4 } })
  const fs = Array.from({ length: 3 }, () => sim.addFlow('video')); run(sim, 10)
  assert.deepEqual(fs.map(f => f.status), ['reserved', 'reserved', 'refused'])
  assert.equal(fs[2].refusedAt, 'C3'); assert.equal(fs[2].reason, 'capacity')
  noResv(sim, fs[2].id, ROUTERS)
  assert.equal(sim.reserved('C3>E4'), 4)
})

test('foreign policy refuses at E3', () => {
  const sim = new RsvpSim({ seed: 1, foreignPolicy: true }); const f = sim.addFlow('voice'); run(sim, 10)
  assert.equal(f.status, 'refused'); assert.equal(f.refusedAt, 'E3'); assert.equal(f.reason, 'policy')
  noResv(sim, f.id, ROUTERS) // E4 and C3 were cleaned up by the ResvErr, E1..E2 never had any
})

test('data flows signal nothing', () => {
  const sim = new RsvpSim({ seed: 1 }); const f = sim.addFlow('data'); run(sim, 5)
  assert.equal(f.status, 'besteffort'); assert.equal(sim.msgs.length, 0)
  for (const r of ROUTERS) assert.equal(sim.stateCount(r), 0)
})

test('refresh off: state expires after 3 periods', () => {
  const sim = new RsvpSim({ seed: 1, refresh: false, refreshPeriod: 3 }); const f = sim.addFlow('voice')
  while (f.status !== 'reserved') sim.tick(0.01)
  const t0 = sim.time // setup done (about 4 s)
  runUntil(sim, t0 + 9 - 0.5)
  assert.equal(f.status, 'reserved'); assert.equal(sim.reserved('C1>C2'), 0.1)
  runUntil(sim, t0 + 9 + 3.5)
  assert.equal(f.status, 'expired'); assert.equal(sim.reserved('C1>C2'), 0)
})

test('refresh on keeps state alive for 60 s', () => {
  const sim = new RsvpSim({ seed: 1 }); const f = sim.addFlow('video'); run(sim, 60)
  assert.equal(f.status, 'reserved'); assert.equal(sim.reserved('C1>C2'), 2)
  for (const r of ROUTERS) assert.equal(sim.stateCount(r), 2)
})

test('failRouter is repaired by the next refresh', () => {
  const sim = new RsvpSim({ seed: 1 }); const f = sim.addFlow('voice'); run(sim, 20)
  sim.failRouter('C1'); assert.equal(sim.stateCount('C1'), 0)
  run(sim, sim.cfg.refreshPeriod + 2)
  assert.equal(sim.path.C1.has(f.id), true); assert.equal(sim.resv.C1.has(f.id), true)
  assert.equal(f.status, 'reserved')
})

test('lowering capacity does not evict', () => {
  const sim = new RsvpSim({ seed: 1, cap: { A: 10, B: 100 } })
  const fs = Array.from({ length: 5 }, () => sim.addFlow('video')); run(sim, 10)
  sim.cfg.cap.A = 4; run(sim, 20)
  assert.deepEqual(fs.map(f => f.status), Array(5).fill('reserved'))
  assert.equal(sim.reserved('C1>C2'), 10)
})

test('reset is deterministic', () => {
  const sim = new RsvpSim({ seed: 7 })
  const snap = () => {
    for (let i = 0; i < 10; i++) sim.addFlow()
    const early: unknown[] = []
    for (let i = 0; i < 10; i++) {
      run(sim, 1)
      early.push(sim.msgs.map(m => [m.type, m.flow, m.from, m.to, Math.round(m.t * 1000)]))
    }
    return { early, flows: sim.flows.map(f => [f.id, f.kind, f.status, f.refusedAt]) }
  }
  const a = snap(); sim.reset(); assert.equal(sim.time, 0); assert.equal(sim.flows.length, 0)
  const b = snap()
  assert.deepEqual(a, b)
})

test('setFlowCount removes newest first', () => {
  const sim = new RsvpSim({ seed: 1 })
  for (let i = 0; i < 5; i++) sim.addFlow('voice')
  run(sim, 6)
  const gone = sim.flows.slice(2).map(f => f.id)
  sim.setFlowCount(2)
  assert.deepEqual(sim.flows.map(f => f.id), [1, 2])
  for (const id of gone) {
    for (const r of ROUTERS) { assert.equal(sim.path[r].has(id), false); assert.equal(sim.resv[r].has(id), false) }
  }
  assert.ok(Math.abs(sim.reserved('C1>C2') - 0.2) < 1e-9)
  sim.setFlowCount(4); assert.equal(sim.flows.length, 4)
})

test('refreshMsgPerSecond', () => {
  const sim = new RsvpSim({ seed: 1 })
  for (let i = 0; i < 3; i++) sim.addFlow('voice')
  run(sim, 6)
  assert.equal(sim.refreshMsgPerSecond(), 0.2)
})

test('large tick handles arrivals in order', () => {
  const sim = new RsvpSim({ seed: 1 }); const f = sim.addFlow('voice')
  sim.tick(5)
  assert.equal(f.status, 'reserved')
})

test('many flows refresh without animated messages', () => {
  const n = MAX_ANIMATED_REFRESH + 5
  const sim = new RsvpSim({ seed: 1 })
  for (let i = 0; i < n; i++) sim.addFlow('voice')
  run(sim, 8)
  let refreshMsgs = 0
  for (let i = 0; i < 4000; i++) { sim.tick(0.01); refreshMsgs += sim.msgs.filter(m => m.refresh).length }
  assert.equal(refreshMsgs, 0)
  assert.ok(sim.flows.every(f => f.status === 'reserved'))
})

test('ResvErr removes downstream entries hop by hop', () => {
  const sim = new RsvpSim({ seed: 1, cap: { A: 2, B: 100 } })
  const first = sim.addFlow('video'); run(sim, 5)
  const f = sim.addFlow('video')
  // added at t=5: PATH done at 7, RESV reaches C1 (refusal) 6 hops later, at 8.5
  runUntil(sim, 8.5 + 0.05)
  assert.equal(f.status, 'refused'); assert.equal(f.refusedAt, 'C1')
  for (const r of ['C2', 'E2', 'E3', 'C3', 'E4']) assert.equal(sim.resv[r].has(f.id), true, r)
  runUntil(sim, 8.5 + 0.25 + 0.05) // ResvErr has passed C2
  assert.equal(sim.resv.C2.has(f.id), false); assert.equal(sim.resv.E2.has(f.id), true)
  runUntil(sim, 8.5 + 5 * 0.25 + 0.05) // and E4
  noResv(sim, f.id, ROUTERS)
  assert.equal(first.status, 'reserved')
})

test('removeFlow with messages in flight leaves no stray state', () => {
  const sim = new RsvpSim({ seed: 1 }); const f = sim.addFlow('voice')
  sim.tick(1) // PATH in flight
  sim.removeFlow(f.id)
  run(sim, 15)
  assert.equal(sim.msgs.length, 0)
  for (const r of ROUTERS) assert.equal(sim.stateCount(r), 0)
  const g = sim.addFlow('voice'); sim.tick(2.6) // RESV in flight
  sim.removeFlow(g.id); run(sim, 15)
  assert.equal(sim.msgs.length, 0)
  for (const r of ROUTERS) assert.equal(sim.stateCount(r), 0)
})

test('failRouter mid-signalling: RESV still installs, refresh restores PATH state', () => {
  const sim = new RsvpSim({ seed: 1 }); const f = sim.addFlow('voice')
  sim.tick(2.6) // PATH done, RESV on its way back
  sim.failRouter('C1')
  sim.tick(1.5) // RESV has passed C1
  assert.equal(sim.resv.C1.has(f.id), true); assert.equal(sim.path.C1.has(f.id), false)
  run(sim, 10)
  assert.equal(f.status, 'reserved'); assert.equal(sim.path.C1.has(f.id), true)
})

test('failRouter recovery refused when capacity is gone', () => {
  const sim = new RsvpSim({ seed: 1, cap: { A: 10, B: 100 } }); const f = sim.addFlow('video'); run(sim, 10)
  sim.failRouter('C1'); sim.cfg.cap.A = 1
  run(sim, 6)
  assert.equal(f.status, 'refused'); assert.equal(f.refusedAt, 'C1'); assert.equal(f.reason, 'capacity')
  noResv(sim, f.id, ROUTERS)
  assert.equal(sim.reserved('C1>C2'), 0)
})

test('refresh switched off and on again', () => {
  const sim = new RsvpSim({ seed: 1, refresh: false }); const f = sim.addFlow('voice'); run(sim, 8)
  sim.cfg.refresh = true; run(sim, 30)
  assert.equal(f.status, 'reserved')
  sim.cfg.refresh = false; run(sim, 15)
  assert.equal(f.status, 'expired')
  sim.cfg.refresh = true; run(sim, 15) // an expired flow is not revived by refreshes
  assert.equal(f.status, 'expired'); assert.equal(sim.reserved('C1>C2'), 0)
})

test('one large tick equals many small ticks with many flows', () => {
  const make = () => {
    const sim = new RsvpSim({ seed: 3, cap: { A: 10, B: 10 } })
    for (let i = 0; i < 30; i++) sim.addFlow()
    return sim
  }
  const a = make(), b = make()
  run(a, 40); b.tick(40)
  assert.deepEqual(b.flows.map(f => [f.status, f.refusedAt]), a.flows.map(f => [f.status, f.refusedAt]))
  for (const r of ROUTERS) assert.equal(b.stateCount(r), a.stateCount(r), r)
  assert.equal(b.reserved('C1>C2'), a.reserved('C1>C2'))
})
