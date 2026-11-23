import { test } from 'node:test'
import assert from 'node:assert/strict'
import { DiffServSim, dscpName, dropPrecedence, queueOf, type Pkt } from './qos-diffserv.ts'
import { BOTTLENECK_A, BOTTLENECK_B, LINKS, type FlowKind } from './qos-topology.ts'

const run = (sim: DiffServSim, s: number) => { for (let i = 0; i < s * 100; i++) sim.tick(0.01) }
const make = (cfg: ConstructorParameters<typeof DiffServSim>[0], flows: Partial<Record<FlowKind, number>>) => {
  const sim = new DiffServSim(cfg)
  for (const k of ['voice', 'video', 'data'] as FlowKind[]) for (let i = 0; i < (flows[k] ?? 0); i++) sim.addFlow(k)
  return sim
}
/** Every packet currently on a link or in a queue. */
const allPkts = (sim: DiffServSim): Pkt[] => [
  ...sim.inFlight, ...LINKS.flatMap(l => Object.values(sim.queues[l]).flat()),
]
/** Counts dropped packets by DSCP, from drops seen while running (ring of 50 is too short, so poll often). */
const runCountingDrops = (sim: DiffServSim, s: number, dscp: number) => {
  let n = 0; const seen = new Set<number>()
  for (let i = 0; i < s * 100; i++) {
    sim.tick(0.01)
    for (const d of sim.drops) if (!seen.has(d.pkt.id)) { seen.add(d.pkt.id); if (d.pkt.dscp === dscp) n++ }
  }
  return n
}

test('dscpName and queueOf', () => {
  assert.equal(dscpName(34), 'AF41'); assert.equal(dscpName(0), 'BE'); assert.equal(dscpName(46), 'EF'); assert.equal(dscpName(24), 'CS3')
  assert.equal(dscpName(5), '5')
  assert.equal(queueOf(38), 'AF4'); assert.equal(queueOf(26), 'AF3'); assert.equal(queueOf(10), 'BE'); assert.equal(queueOf(46), 'EF')
  assert.equal(dropPrecedence(36), 2); assert.equal(dropPrecedence(30), 3); assert.equal(dropPrecedence(46), 1)
})

test('E1 marks by kind', () => {
  const sim = make({ seed: 1 }, { voice: 1, video: 1, data: 1 })
  const seen: Record<string, Set<number>> = { voice: new Set(), video: new Set(), data: new Set() }
  for (let i = 0; i < 1000; i++) { sim.tick(0.01); for (const p of allPkts(sim)) if (p.kind !== 'cross' && p.at !== 'S') seen[p.kind].add(p.origDscp) }
  assert.deepEqual([...seen.voice], [46]); assert.deepEqual([...seen.video], [34]); assert.deepEqual([...seen.data], [0])
  for (const k of ['voice', 'video', 'data'] as const) assert.ok(sim.stats[k].delivered > 0, k)
})

test('video above CIR is re-marked yellow, above PIR red', () => {
  const dscps = (n: number) => {
    const sim = make({ seed: 2 }, { video: n }); const seen = new Set<number>()
    for (let i = 0; i < 1500; i++) { sim.tick(0.01); for (const p of sim.inFlight) if (p.link === 'C1>C2') seen.add(p.dscp) }
    return seen
  }
  const four = dscps(4); assert.ok(four.has(36)); assert.ok(!four.has(38))
  const five = dscps(5); assert.ok(five.has(38))
  assert.ok(dscps(2).size === 1 && dscps(2).has(34))
})

test('EF above the policer is dropped at E1', () => {
  const sim = make({ seed: 3 }, { voice: 15 }); run(sim, 20)
  assert.ok(sim.drops.some(d => d.node === 'E1' && d.reason === 'police'))
  assert.ok(sim.stats.voice.dropped > 0)
  const ok = make({ seed: 3 }, { voice: 5 }); run(ok, 20)
  assert.equal(ok.stats.voice.dropped, 0)
})

test('EF is protected under overload in A', () => {
  const sim = make({ seed: 4, cap: { A: 5, B: 100 } }, { voice: 5, data: 8 }); run(sim, 30)
  assert.equal(sim.stats.voice.dropped, 0)
  assert.ok(sim.stats.data.dropped > 0)
  assert.ok(sim.meanDelayMs('voice') < sim.meanDelayMs('data'))
})

test('AF43 dropped before AF41', () => {
  const sim = make({ seed: 5, cap: { A: 8, B: 100 } }, { video: 6 })
  const af43 = runCountingDrops(sim, 60, 38)
  const sim2 = make({ seed: 5, cap: { A: 8, B: 100 } }, { video: 6 })
  const af41 = runCountingDrops(sim2, 60, 34)
  assert.ok(af43 > af41, `${af43} vs ${af41}`)
})

test("bleach puts voice into B's BE queue", () => {
  const cfg = { seed: 6, cap: { A: 100, B: 10 }, crossB: 12 }
  const trust = make({ ...cfg, boundary: 'trust' }, { voice: 5 }); run(trust, 40)
  const bleach = make({ ...cfg, boundary: 'bleach' }, { voice: 5 }); run(bleach, 40)
  assert.equal(trust.stats.voice.dropped, 0)
  assert.ok(bleach.stats.voice.dropped > 0)
  assert.ok(bleach.meanDelayMs('voice') > 5 * trust.meanDelayMs('voice'))
})

test('remark maps AF41 to AF31 in B', () => {
  const sim = make({ seed: 7, boundary: 'remark' }, { video: 2 }); const seen = new Set<string>()
  for (let i = 0; i < 1000; i++) {
    sim.tick(0.01)
    for (const p of allPkts(sim)) if (p.at === 'C3' || p.link === 'C3>E4' || p.link === 'E3>C3') seen.add(`${p.dscp}/${p.origDscp}`)
  }
  assert.deepEqual([...seen], ['26/34'])
})

test('boundary switch applies only at E3 ingress', () => {
  const sim = make({ seed: 8, cap: { A: 100, B: 100 } }, { voice: 3, video: 2 }); run(sim, 5)
  sim.cfg.boundary = 'bleach'
  let checked = 0
  for (let i = 0; i < 20; i++) {
    sim.tick(0.01)
    for (const p of allPkts(sim)) {
      if (p.at === 'C3' || p.at === 'E4' || p.link === 'E3>C3' || p.link === 'C3>E4') {
        // E3 is 5 hops (1.0 s) from creation: packets born before t = 4 passed E3 before the switch
        if (p.born < 4 && p.kind !== 'cross') { assert.notEqual(p.dscp, 0, `pkt ${p.id}`); checked++ }
      }
    }
  }
  assert.ok(checked > 0)
  // after enough time every packet that arrived at E3 post-switch is bleached
  run(sim, 5)
  assert.ok(sim.inFlight.filter(p => p.link === 'E3>C3').every(p => p.dscp === 0))
})

test('core state does not grow with flows', () => {
  const sim = new DiffServSim({ seed: 9 }); sim.setFlowCount(200)
  assert.equal(sim.stateRows('C1').rows.length, 4)
  assert.equal(sim.stateRows('E1').rows.length, 5); assert.equal(sim.stateRows('E1').more, 195)
  assert.equal(sim.stateRows('E1').rows[0].key, 'flow 1')
  assert.match(sim.stateRows('E1').rows[0].detail, /→/)
  assert.equal(sim.stateRows('E3').rows.length, 3)
  sim.setFlowCount(3); assert.equal(sim.flows.length, 3)
})

test('reset is deterministic', () => {
  const sim = new DiffServSim({ seed: 10, cap: { A: 5, B: 10 }, crossB: 5 }); sim.setFlowCount(12); run(sim, 10)
  const first = JSON.stringify(sim.stats); const n = sim.flows.length
  sim.reset(); assert.equal(sim.time, 0); assert.equal(sim.flows.length, n); assert.equal(sim.inFlight.length, 0)
  run(sim, 10)
  assert.equal(JSON.stringify(sim.stats), first)
  const again = new DiffServSim({ seed: 10 }); again.setFlowCount(12); again.tick(0.3); again.reset(); again.tick(0.001)
  const clean = new DiffServSim({ seed: 10 }); clean.setFlowCount(12); clean.tick(0.001)
  assert.ok(again.inFlight.every(p => Number.isFinite(p.t)))
  assert.equal(again.inFlight.length, clean.inFlight.length)
  const other = new DiffServSim({ seed: 10, cap: { A: 5, B: 10 }, crossB: 5 }); other.setFlowCount(12); run(other, 10)
  assert.equal(JSON.stringify(other.stats), first)
})

test('one tick(5) equals 500 x tick(0.01)', () => {
  const mk = () => { const s = new DiffServSim({ seed: 11, cap: { A: 4, B: 6 }, crossB: 5, boundary: 'remark' }); s.setFlowCount(8); return s }
  const a = mk(); a.tick(5); const b = mk(); for (let i = 0; i < 500; i++) b.tick(0.01)
  for (const k of ['voice', 'video', 'data', 'cross'] as const) {
    assert.equal(a.stats[k].sent, b.stats[k].sent, k); assert.equal(a.stats[k].dropped, b.stats[k].dropped, k)
    assert.equal(a.stats[k].delivered, b.stats[k].delivered, k)
  }
  assert.ok(a.stats.cross.delivered > 0)
})

test('inFlight stays bounded', () => {
  const sim = new DiffServSim({ seed: 12, cap: { A: 5, B: 5 }, crossB: 20 }); sim.setFlowCount(200)
  let max = 0
  for (let i = 0; i < 600; i++) { sim.tick(0.1); max = Math.max(max, allPkts(sim).length) }
  assert.ok(max < 2000, String(max))
  assert.ok(sim.drops.length <= 50)
})

test('reset restarts the PRNG from the seed', () => {
  const sim = new DiffServSim({ seed: 13 }); sim.setFlowCount(6); sim.reset(); sim.setFlowCount(0)
  sim.setFlowCount(3)
  const fresh = new DiffServSim({ seed: 13 }); fresh.setFlowCount(3)
  assert.deepEqual(sim.flows.map(f => f.kind), fresh.flows.map(f => f.kind))
})

test('a saturated domain A and cross traffic in B share B fairly, no phase lock', () => {
  // A leaves C1 one serialisation apart and B is as fast as A: with constant gaps and no jitter, the
  // first mix locked A out of C3's full BE queue (8 of ~1580 delivered) and the second locked out the cross traffic
  for (const flows of [{ data: 6, video: 3 }, { data: 4, video: 4, voice: 4 }]) {
    const sim = make({ seed: 14, cap: { A: 10, B: 10 }, crossB: 12, boundary: 'bleach' }, flows); run(sim, 30)
    const a = sim.stats.voice.delivered + sim.stats.video.delivered + sim.stats.data.delivered
    const share = a / (a + sim.stats.cross.delivered)
    assert.ok(share > 0.3 && share < 0.7, `${JSON.stringify(flows)}: A's share ${share.toFixed(2)}`)
  }
})

test('cross-traffic gaps are random but do not change the flow kinds', () => {
  const sim = new DiffServSim({ seed: 15, crossB: 5 }); run(sim, 5)
  const sent = sim.stats.cross.sent
  assert.ok(sent > 150 && sent < 350 && sent !== 250, String(sent))   // Poisson around 50 pkt/s
  sim.setFlowCount(10)
  const quiet = new DiffServSim({ seed: 15 }); run(quiet, 5); quiet.setFlowCount(10)
  assert.deepEqual(sim.flows.map(f => f.kind), quiet.flows.map(f => f.kind))
})
