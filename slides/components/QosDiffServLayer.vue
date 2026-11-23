<!--
  The DiffServ drawing of QosPathSim (lecture 08), rendered inside the parent's <svg> twice:
  layer="packets" under the nodes, layer="overlay" above them. It only reads the engine.

    packets   every packet on a link as a 5 px square in the lane of its kind (voice above, video
              on, data and cross traffic below the line), filled by its current DSCP; a voice
              packet that lost its EF mark keeps an EF-coloured ring around its square. Squares are binned by
              6 px per lane, so the number of drawn shapes is bounded however many flows run.
              DSCP names ride on sampled packets (one voice and one video packet every LABEL_GAP
              seconds), so the label visibly changes at E1 (marking, meter) and at E3 (SLA); unmarked
              packets before E1 carry no label. They are drawn in this layer, under the nodes, so a
              label slides behind a router ring instead of blinking off and on beside it.
    overlay   - at each bottleneck the four class queues (EF, AF4, AF3, BE) as two-row stacks of
                packet squares, head on the right, with the queue length and link rate above and
                "EF: strict priority" / "AF4 ×3 · AF3 ×2 · BE ×1" under the link (not compact);
              - dropped packets fall out in FMT red (police drops from E1, queue drops from the
                tail of their class queue);
              - the colour legend at legendY (not compact).
  sim / frame  the engine and a counter that changes whenever it advanced (every view depends on it)
  still        print mode: the drops of the last frame are spread along their fall instead of animated
-->
<script setup lang="ts">
import { computed } from 'vue'
import { BOTTLENECK_A, BOTTLENECK_B, linkCapacity, type LinkId, type NodeId } from '../utils/qos-topology'
import { AF_DROP_AT, QUEUE_LIMIT, WRR, DSCP, dropPrecedence, dscpName, queueOf, type DiffServSim, type DropRecord, type Pkt, type QueueClass } from '../utils/qos-diffserv'
import { CLASS_COLOUR, COLOUR_KEYS, colourKey, colourVar, textVar, type ColourKey } from '../utils/qos-dscp-colour'

const props = defineProps<{
  layer: 'packets' | 'overlay'
  sim: DiffServSim
  frame: number
  x: Record<NodeId, number>
  nodeY: number
  compact: boolean
  still: boolean
  /** Baseline of the first caption line under the bottlenecks. */
  captionY: number
  legendY: number
  width: number
}>()

const SQ = 5 // packet square, px
const BIN = 6 // in-flight squares are binned per lane by this many px
const LANE: Record<Pkt['kind'], number> = { voice: -6, video: 0, data: 6, cross: 6 }
const LANES = 3
const laneIdx = (k: Pkt['kind']) => (k === 'voice' ? 0 : k === 'video' ? 1 : 2)

const ROWS: readonly QueueClass[] = ['EF', 'AF4', 'AF3', 'BE']
const COLS = QUEUE_LIMIT / 2 // two rows of squares per class queue
const PITCH = 7
const ROW_TOP = 28
const ROW_PITCH = 13
const BOTTLENECKS: { link: LinkId, from: NodeId, to: NodeId }[] = [
  { link: BOTTLENECK_A, from: 'C1', to: 'C2' },
  { link: BOTTLENECK_B, from: 'C3', to: 'E4' },
]
/** Left edge of a bottleneck's queue squares; the class labels end just left of it. */
const qx0 = (from: NodeId) => props.x[from] + 22
const slotX = (from: NodeId, i: number) => qx0(from) + (COLS - 1 - Math.floor(i / 2)) * PITCH
const slotY = (row: number, i: number) => ROW_TOP + row * ROW_PITCH + (i % 2) * (SQ + 1)

const square = (x: number, y: number) => `M${x.toFixed(1)} ${y}h${SQ}v${SQ}h-${SQ}z`
/** The "was EF" ring: RING px outside the square, so the grey fill stays visible inside it. */
const RING = 1.6
const ring = (x: number, y: number) => `M${(x - RING).toFixed(1)} ${y - RING}h${SQ + 2 * RING}v${SQ + 2 * RING}h-${SQ + 2 * RING}z`
const wasEf = (p: Pkt) => p.origDscp === DSCP.EF && p.dscp !== DSCP.EF

interface Shapes { fill: Record<ColourKey, string[]>, wasEf: string[] }
const newShapes = (): Shapes => ({ fill: Object.fromEntries(COLOUR_KEYS.map(k => [k, []])) as unknown as Record<ColourKey, string[]>, wasEf: [] })
const toPaths = (s: Shapes) => ({
  fill: COLOUR_KEYS.filter(k => s.fill[k].length).map(k => ({ key: k, d: s.fill[k].join('') })),
  wasEf: s.wasEf.join(''),
})

// --- packets on the links ----------------------------------------------------------
const bins: (Pkt | undefined)[] = new Array(LANES * Math.ceil(props.width / BIN)).fill(undefined)
const xOf = (p: Pkt) => {
  if (!p.link) return props.x[p.at]
  const [a, b] = p.link.split('>') as [NodeId, NodeId]
  return props.x[a] + (props.x[b] - props.x[a]) * p.t
}

const flying = computed(() => {
  void props.frame
  if (props.layer !== 'packets') return null
  const perLane = bins.length / LANES
  bins.fill(undefined)
  for (const p of props.sim.inFlight) {
    const b = Math.min(perLane - 1, Math.max(0, Math.round(xOf(p) / BIN)))
    bins[laneIdx(p.kind) * perLane + b] = p
  }
  const s = newShapes()
  for (let i = 0; i < bins.length; i++) {
    const p = bins[i]
    if (!p) continue
    const x = (i % perLane) * BIN - SQ / 2
    const y = props.nodeY + LANE[p.kind] - SQ / 2
    s.fill[colourKey(p.dscp)].push(square(x, y))
    if (wasEf(p)) s.wasEf.push(ring(x, y))
  }
  return toPaths(s)
})

// --- class queues at the bottlenecks --------------------------------------------------
const queues = computed(() => {
  void props.frame
  if (props.layer !== 'overlay') return []
  return BOTTLENECKS.map(b => {
    const q = props.sim.queues[b.link]
    const s = newShapes()
    let n = 0
    ROWS.forEach((cls, row) => {
      q[cls].forEach((p, i) => {
        const x = slotX(b.from, i)
        const y = slotY(row, i)
        s.fill[colourKey(p.dscp)].push(square(x, y))
        if (wasEf(p)) s.wasEf.push(ring(x, y))
      })
      n += q[cls].length
    })
    return {
      ...b,
      ...toPaths(s),
      x0: qx0(b.from),
      ticks: afTicks(b.from),
      header: `queue ${n} pkt · ${linkCapacity(b.link, props.sim.cfg.cap)} Mbit/s`,
      mid: (props.x[b.from] + props.x[b.to]) / 2,
    }
  })
})
/**
 * Drop-precedence thresholds of the AF queues (AF_DROP_AT): a tick across the AF4 and AF3 rows where the queue
 * length reaches the point at which AFx3 (10) and AFx2 (20) arrivals are dropped; the head is on the right, so a
 * tick sits between the slots of the 10th and 11th (20th and 21st) packet.
 */
const afTicks = (from: NodeId) => [AF_DROP_AT[3], AF_DROP_AT[2]].map(n => ({
  x: qx0(from) + (COLS - n / 2) * PITCH - 1,
  y1: ROW_TOP + ROWS.indexOf('AF4') * ROW_PITCH - 3,
  y2: ROW_TOP + ROWS.indexOf('AF3') * ROW_PITCH + 2 * SQ + 4,
}))
const rowLabels = ROWS.map((cls, row) => ({ cls, y: ROW_TOP + row * ROW_PITCH + 10, colour: textVar(CLASS_COLOUR[cls]) }))
const wrrCaption = `AF4 ×${WRR.AF4} · AF3 ×${WRR.AF3} · BE ×${WRR.BE}`

// --- DSCP labels on sampled packets ------------------------------------------------------
/** Simulated seconds of birth between two labelled packets of one kind. */
const LABEL_GAP = 0.5
/** Labels of one lane closer than this are skipped. */
const LABEL_MIN_DX = 38
const labelled = new WeakMap<Pkt, boolean>()
const lastLabel = { voice: -Infinity, video: -Infinity }
let lastTime = 0

const labels = computed(() => {
  void props.frame
  if (props.layer !== 'packets') return []
  const sim = props.sim
  if (sim.time < lastTime) { lastLabel.voice = -Infinity; lastLabel.video = -Infinity } // reset
  lastTime = sim.time
  const out: { id: number, x: number, y: number, text: string, colour: string, lane: number }[] = []
  for (const p of sim.inFlight) {
    if (p.kind !== 'voice' && p.kind !== 'video') continue
    let on = labelled.get(p)
    if (on === undefined) { // decided once per packet, when it is first seen on a link
      on = p.born - lastLabel[p.kind] >= LABEL_GAP
      if (on) lastLabel[p.kind] = p.born
      labelled.set(p, on)
    }
    if (!on || p.at === 'S') continue // not marked before E1
    const x = xOf(p)
    // video under the line, clear of the lower pipe edge (nodeY + 9)
    const y = p.kind === 'voice' ? props.nodeY - 12 : props.nodeY + 26
    const text = dscpName(p.dscp)
    out.push({
      id: p.id,
      x,
      y,
      text,
      colour: textVar(colourKey(p.dscp)),
      lane: laneIdx(p.kind),
    })
  }
  out.sort((a, b) => a.lane - b.lane || a.x - b.x)
  return out.filter((l, i) => i === 0 || out[i - 1].lane !== l.lane || l.x - out[i - 1].x >= LABEL_MIN_DX)
})

// --- drops ---------------------------------------------------------------------------
const FALL_S = 0.8 // simulated seconds a dropped packet takes to fall out
const FALL_PX = 34
const firstSeen = new WeakMap<DropRecord, number>()

const drops = computed(() => {
  void props.frame
  if (props.layer !== 'overlay') return []
  const sim = props.sim
  const n = sim.drops.length
  const out: { key: number, x: number, y: number, opacity: number }[] = []
  sim.drops.forEach((r, i) => {
    let age: number
    if (props.still) age = (n - 1 - i) * 0.04
    else {
      let t = firstSeen.get(r)
      if (t === undefined || t > sim.time) { t = sim.time; firstSeen.set(r, t) }
      age = sim.time - t
    }
    if (age >= FALL_S) return
    let x = props.x[r.node] - SQ / 2
    let y = props.nodeY + 10
    if (r.reason === 'queue') { // from where its class queue turned it away
      const cls = queueOf(r.pkt.dscp)
      const limit = cls === 'AF4' || cls === 'AF3' ? AF_DROP_AT[dropPrecedence(r.pkt.dscp)] : QUEUE_LIMIT
      x = limit === QUEUE_LIMIT ? qx0(r.node) - 1 : qx0(r.node) + (COLS - limit / 2) * PITCH - SQ - 2
      y = slotY(ROWS.indexOf(cls), 0)
    }
    out.push({ key: r.pkt.id, x, y: y + FALL_PX * age / FALL_S, opacity: 1 - 0.7 * age / FALL_S })
  })
  return out
})

/**
 * "policed" beside an edge router while its policer is dropping (E1's EF policer; E3 under re-mark only
 * re-marks), so a red packet falling there is not read as a full queue. Held POLICED_HOLD simulated
 * seconds after the last such drop, so it does not blink between drops.
 */
const POLICED_HOLD = 1.5
const policedAt = computed(() => {
  void props.frame
  if (props.layer !== 'overlay') return []
  const sim = props.sim
  const nodes = new Set<NodeId>()
  for (const r of sim.drops) {
    if (r.reason !== 'police') continue
    if (props.still || (r.t <= sim.time && sim.time - r.t < POLICED_HOLD)) nodes.add(r.node)
  }
  return [...nodes].map(n => ({ node: n, x: props.x[n] + 8 }))
})

// --- legend --------------------------------------------------------------------------
const LEGEND: { text: string, colour: string, outline?: boolean, tick?: boolean }[] = [
  { text: 'EF', colour: colourVar('ef') },
  { text: 'AF41', colour: colourVar('af41') },
  { text: 'AF42', colour: colourVar('af42') },
  { text: 'AF43', colour: colourVar('af43') },
  { text: 'AF31–33', colour: colourVar('af31') },
  { text: 'BE', colour: colourVar('be') },
  { text: 'was EF', colour: colourVar('be'), outline: true },
  { text: 'dropped', colour: 'var(--qp-red)' },
  { text: 'AFx3 dropped from 10, AFx2 from 20', colour: 'var(--vsb-ink)', tick: true },
]
const legend = (() => {
  let x = 0
  return LEGEND.map(l => {
    const item = { ...l, x }
    x += 22 + l.text.length * 7.2
    return item
  })
})()
</script>

<template>
  <g v-if="layer === 'packets' && flying">
    <path v-for="p in flying.fill" :key="p.key" :d="p.d" :style="{ fill: colourVar(p.key) }" />
    <path v-if="flying.wasEf" :d="flying.wasEf" class="was-ef" />
    <!-- DSCP names on sampled packets, under the nodes -->
    <text
      v-for="l in labels" :key="l.id" :x="l.x.toFixed(1)" :y="l.y"
      class="dscp halo" text-anchor="middle" :style="{ fill: l.colour }"
    >{{ l.text }}</text>
  </g>
  <g v-else-if="layer === 'overlay'">
    <!-- class queues at the bottlenecks -->
    <g v-for="q in queues" :key="q.link">
      <text :x="q.x0 + COLS * PITCH / 2" y="18" class="value" text-anchor="middle">{{ q.header }}</text>
      <g v-for="r in rowLabels" :key="r.cls">
        <text :x="q.x0 - 5" :y="r.y" class="row-label" text-anchor="end" :style="{ fill: r.colour }">{{ r.cls }}</text>
        <rect :x="q.x0 - 1.5" :y="r.y - 11.5" :width="COLS * PITCH + 1" :height="2 * SQ + 3" class="slot" />
      </g>
      <path v-for="p in q.fill" :key="p.key" :d="p.d" :style="{ fill: colourVar(p.key) }" />
      <line v-for="t in q.ticks" :key="t.x" :x1="t.x" :x2="t.x" :y1="t.y1" :y2="t.y2" class="tick" />
      <path v-if="q.wasEf" :d="q.wasEf" class="was-ef" />
      <template v-if="!compact">
        <text :x="q.mid" :y="captionY" class="caption halo" text-anchor="middle">EF: strict priority</text>
        <text :x="q.mid" :y="captionY + 16" class="caption halo" text-anchor="middle">{{ wrrCaption }}</text>
      </template>
    </g>

    <!-- drops -->
    <text
      v-for="p in policedAt" :key="`policed${p.node}`" :x="p.x" :y="nodeY + 42"
      class="caption halo policed" text-anchor="start"
    >policed</text>
    <rect
      v-for="d in drops" :key="`drop${d.key}`" :x="d.x" :y="d.y.toFixed(1)"
      :width="SQ" :height="SQ" class="drop" :opacity="d.opacity.toFixed(2)"
    />

    <!-- legend -->
    <g v-if="!compact" :transform="`translate(0, ${legendY})`">
      <g v-for="l in legend" :key="l.text" :transform="`translate(${l.x}, 0)`">
        <line v-if="l.tick" x1="4.5" x2="4.5" y1="-13" y2="2" class="tick" />
        <template v-else-if="l.outline">
          <rect :x="2" :y="-8" :width="SQ" :height="SQ" :style="{ fill: l.colour }" />
          <rect :x="2 - RING" :y="-8 - RING" :width="SQ + 2 * RING" :height="SQ + 2 * RING" class="was-ef" />
        </template>
        <rect v-else x="0" y="-10" width="9" height="9" :style="{ fill: l.colour }" />
        <text x="14" y="0" class="caption">{{ l.text }}</text>
      </g>
      <text :x="width" y="0" class="caption" text-anchor="end">1 square = 0.1 Mbit</text>
    </g>
  </g>
</template>

<style scoped>
.value { font-size: 14px; fill: var(--vsb-ink); font-variant-numeric: tabular-nums; }
.caption { font-size: 14px; fill: var(--vsb-muted); }
.row-label { font-size: 14px; font-weight: 700; }
.dscp { font-size: 14px; font-weight: 700; }
.halo { paint-order: stroke; stroke: var(--vsb-bg); stroke-width: 4px; stroke-linejoin: round; }
.policed { fill: var(--qp-red); font-weight: 700; }
.tick { stroke: var(--vsb-ink); stroke-width: 1.5; }
.slot { fill: none; stroke: var(--vsb-muted); stroke-width: 0.8; stroke-opacity: 0.6; }
.was-ef { stroke: var(--qp-ef); stroke-width: 1.6; }
path.was-ef, rect.was-ef { fill: none; }
.drop { fill: var(--qp-red); }
</style>
