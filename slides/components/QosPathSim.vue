<!--
  One path across two operators' domains, animated as RSVP/IntServ or as DiffServ (lecture 08).

    S - E1 - C1 - C2 - E2 | E3 - C3 - E4 - R
        `--- Domain A ---'  `- Domain B -'

  Hosts are boxes, edge routers double rings, core routers single rings; the two bottleneck links
  (C1→C2 in A, C3→E4 in B) are drawn as wide pipes with a fill bar above them. Under every router a
  state panel shows how many entries it keeps and the newest five, with "+ n more" (compact: count only).
  The engines live in utils/qos-rsvp.ts and utils/qos-diffserv.ts; this file only draws them.

  mode        'rsvp'      PATH runs downstream (green, above the line), RESV comes back upstream (dark green,
                          below it) and is admission-checked at every router; a refusal flashes the router
                          red ("ResvErr: capacity" / "policy") and a red ResvErr runs downstream. Reserved
                          flows send data as a dotted stream in their colour (voice green, video blue), best
                          effort, refused and expired flows in muted grey. With refresh off every state row
                          gets a fading age bar and expires after 3 missed refreshes (stated on screen).
              'diffserv'  same topology, panels and footer; the per-class packet view is drawn by Task 4.
  compact     state panels show only the count, no legend (side-by-side slide)
  flows       if set, the component follows it via setFlowCount and hides its own flow buttons
  capacityA   Mbit/s of C1→C2 (default 10); capacityB Mbit/s of C3→E4 (default 10)
  seed        PRNG seed of the engine (default 1): the same clicks replay the same run
  initialFlows flows present at start and after Reset (default 0)

  Time: the animation runs in simulated seconds (RSVP refresh every 3 s stands for the real 30 s);
  the speed slider scales simulated seconds per real second (0.25×–4×). Step advances to the next
  message arrival or refresh (RSVP) or by 0.1 s (DiffServ).
  Exposes stateTotal(): entries summed over the seven routers (used by the side-by-side wrapper).

  Print mode (useNav().isPrintMode): no controls and no animation loop; the slide does not use
  export-skip.
-->
<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { onSlideLeave, useNav } from '@slidev/client'
import {
  BOTTLENECK_A, BOTTLENECK_B, PATH, ROLE, ROUTERS, linkCapacity,
  type FlowKind, type LinkId, type NodeId,
} from '../utils/qos-topology'
import { RsvpSim, type RsvpFlow } from '../utils/qos-rsvp'
import { DiffServSim, type Boundary } from '../utils/qos-diffserv'

const props = withDefaults(defineProps<{
  mode: 'rsvp' | 'diffserv'
  compact?: boolean
  flows?: number
  capacityA?: number
  capacityB?: number
  seed?: number
  initialFlows?: number
}>(), { compact: false, flows: undefined, capacityA: 10, capacityB: 10, seed: 1, initialFlows: 0 })

const { isPrintMode } = useNav()

// --- geometry (SVG units = slide px) -----------------------------------------
const W = 880
const H = props.compact ? 220 : 356
const NODE_Y = 102
const X = Object.fromEntries(PATH.map((n, i) => [n, 60 + i * 95])) as Record<NodeId, number>
const R_NODE = 18
const PANEL_W = 84
const PANEL_Y = 170 // baseline of the count
const ROW_H = 19
const MAX_ROWS = 5
const LANE_PATH = 78 // baseline of PATH labels (downstream, above the line)
const LANE_RESV = 140 // baseline of RESV / ResvErr labels (below the line)
const BOUNDARY_X = (X.E2 + X.E3) / 2
const DOMAIN_BOTTOM = props.compact ? 200 : 296
const DOMAINS = [
  { name: 'Domain A', x: X.E1 - 46, w: X.E2 - X.E1 + 92 },
  { name: 'Domain B', x: X.E3 - 46, w: X.E4 - X.E3 + 92 },
]
const BOTTLENECKS: { link: LinkId, from: NodeId, to: NodeId }[] = [
  { link: BOTTLENECK_A, from: 'C1', to: 'C2' },
  { link: BOTTLENECK_B, from: 'C3', to: 'E4' },
]
const BAR_W = 80
const SPEEDS = [0.25, 0.5, 1, 2, 4]
/** Simulated seconds DiffServ advances per Step press. */
const DS_STEP = 0.1

const KIND_COLOUR: Record<FlowKind, string> = {
  voice: 'var(--vsb-green-text)',
  video: 'var(--qp-blue)',
  data: 'var(--vsb-muted)',
}

// --- engine --------------------------------------------------------------------
const cap = () => ({ A: props.capacityA, B: props.capacityB })
const sim = shallowRef<RsvpSim | DiffServSim>(
  props.mode === 'rsvp'
    ? new RsvpSim({ cap: cap(), seed: props.seed })
    : new DiffServSim({ cap: cap(), seed: props.seed }),
)
const rsvpSim = () => sim.value as RsvpSim
const dsSim = () => sim.value as DiffServSim

const frame = ref(0) // bumped after every engine change; every view below depends on it
const running = ref(false)
const speedIdx = ref(2)
const speed = computed(() => SPEEDS[speedIdx.value])
const refresh = ref(true)
const foreignPolicy = ref(false)
const boundary = ref<Boundary>('trust')
const crossB = ref(0)

interface Flash { node: NodeId, text: string, until: number }
const flashes = shallowRef<Flash[]>([])
const FLASH_SECONDS = 3 // simulated seconds a refusal or crash stays marked
let seenRefused = new Set<number>()

function startFlows(): void {
  const n = props.flows ?? props.initialFlows
  if (n > 0) sim.value.setFlowCount(n)
}
startFlows()

watch(refresh, v => { if (props.mode === 'rsvp') rsvpSim().cfg.refresh = v })
watch(foreignPolicy, v => { if (props.mode === 'rsvp') rsvpSim().cfg.foreignPolicy = v })
watch(boundary, v => { if (props.mode === 'diffserv') dsSim().cfg.boundary = v })
watch(crossB, v => { if (props.mode === 'diffserv') dsSim().cfg.crossB = v })
watch(() => [props.capacityA, props.capacityB], () => { sim.value.cfg.cap = cap(); bump() })
watch(() => props.flows, n => { if (n !== undefined) { sim.value.setFlowCount(n); bump() } })

function bump(): void {
  if (props.mode === 'rsvp') noteRefusals()
  frame.value++
}

/** Flash every router that refused a flow since the last frame. */
function noteRefusals(): void {
  const s = rsvpSim()
  const now = s.time
  let list = flashes.value.filter(f => f.until > now)
  for (const f of s.flows) {
    if (f.status !== 'refused' || seenRefused.has(f.id) || !f.refusedAt) continue
    seenRefused.add(f.id)
    list = [...list.filter(x => x.node !== f.refusedAt), { node: f.refusedAt, text: `ResvErr: ${f.reason}`, until: now + FLASH_SECONDS }]
  }
  if (list.length !== flashes.value.length || list.some((f, i) => f !== flashes.value[i])) flashes.value = list
}

// --- animation loop --------------------------------------------------------------
let raf = 0
let last = 0

function loop(now: number): void {
  const dt = Math.min(0.05, (now - last) / 1000)
  last = now
  sim.value.tick(dt * speed.value)
  bump()
  if (running.value) raf = requestAnimationFrame(loop)
}

function play(): void {
  if (isPrintMode.value) return
  running.value = true
  last = performance.now()
  cancelAnimationFrame(raf)
  raf = requestAnimationFrame(loop)
}

function pause(): void {
  running.value = false
  cancelAnimationFrame(raf)
}

function step(): void {
  pause()
  if (props.mode === 'rsvp') rsvpSim().step()
  else dsSim().tick(DS_STEP)
  bump()
}

function reset(): void {
  pause()
  sim.value.reset() // same seed: the same clicks replay the same run
  flashes.value = []
  seenRefused = new Set()
  if (props.mode === 'rsvp') startFlows() // RSVP reset drops the flows, DiffServ keeps them
  bump()
}

function addFlows(n: number): void {
  for (let i = 0; i < n; i++) sim.value.addFlow()
  bump()
}

function failC1(): void {
  const s = rsvpSim()
  s.failRouter('C1')
  flashes.value = [...flashes.value.filter(f => f.node !== 'C1'), { node: 'C1', text: 'crash: state lost', until: s.time + FLASH_SECONDS }]
  bump()
}

onSlideLeave(pause)
onBeforeUnmount(pause)
onMounted(bump)

defineExpose({
  stateTotal: (): number => {
    void frame.value
    if (props.mode === 'rsvp') return ROUTERS.reduce((a, n) => a + rsvpSim().stateCount(n), 0)
    return ROUTERS.reduce((a, n) => { const r = dsSim().stateRows(n, 0); return a + r.rows.length + r.more }, 0)
  },
})

// --- views (all recomputed when `frame` changes) ----------------------------------
const fmtRate = (r: number) => {
  const v = Math.round(r * 10) / 10 // sums of 0.1 carry float noise
  return Number.isInteger(v) ? String(v) : v.toFixed(1)
}

interface Row { kind: 'P' | 'R', flow: number, colour: string, hop: string, rate: string, life: number | null }
interface Panel { node: NodeId, x: number, count: number, rows: Row[], more: number, detail: { key: string, value: string }[] }

const flowMap = computed(() => {
  void frame.value
  if (props.mode !== 'rsvp') return new Map<number, RsvpFlow>()
  return new Map(rsvpSim().flows.map(f => [f.id, f]))
})

function flowColour(f: RsvpFlow | undefined): string {
  if (!f || f.status === 'besteffort' || f.status === 'refused' || f.status === 'expired') return 'var(--vsb-muted)'
  return KIND_COLOUR[f.kind]
}

/** The newest MAX_ROWS entries of one RSVP router, PATH before RESV for the same flow, without sorting all of them. */
function rsvpPanel(node: NodeId): Panel {
  const s = rsvpSim()
  const count = s.stateCount(node)
  const base = { node, x: X[node], count, detail: [] as { key: string, value: string }[] }
  if (props.compact) return { ...base, rows: [], more: 0 }
  const limit = 3 * s.cfg.refreshPeriod
  const life = (age: number) => (refresh.value ? null : Math.max(0, 1 - age / limit))
  const top: Row[] = []
  const consider = (r: Row) => {
    // keep `top` ordered newest flow first, P before R for one flow, at most MAX_ROWS long
    const key = (x: Row) => x.flow * 2 + (x.kind === 'P' ? 1 : 0)
    let i = top.length
    while (i > 0 && key(top[i - 1]) < key(r)) i--
    if (i < MAX_ROWS) { top.splice(i, 0, r); if (top.length > MAX_ROWS) top.pop() }
  }
  for (const e of s.path[node].values()) {
    consider({ kind: 'P', flow: e.flow, colour: flowColour(flowMap.value.get(e.flow)), hop: `←${e.phop}`, rate: fmtRate(e.rate), life: life(e.age) })
  }
  for (const e of s.resv[node].values()) {
    consider({ kind: 'R', flow: e.flow, colour: flowColour(flowMap.value.get(e.flow)), hop: `→${e.link.split('>')[1]}`, rate: fmtRate(e.rate), life: life(e.age) })
  }
  return { ...base, rows: top, more: count - top.length }
}

function dsPanel(node: NodeId): Panel {
  const r = dsSim().stateRows(node, props.compact ? 0 : MAX_ROWS)
  return { node, x: X[node], count: r.rows.length + r.more, rows: [], more: r.more, detail: r.rows.map(x => (x.key.startsWith('flow ')
    ? { key: x.key.slice(5), value: x.detail.split('→ ').pop() ?? x.detail } // E1: flow id and its DSCP
    : { key: x.key, value: x.detail })) }
}

const panels = computed<Panel[]>(() => {
  void frame.value
  return ROUTERS.map(n => (props.mode === 'rsvp' ? rsvpPanel(n) : dsPanel(n)))
})

const bars = computed(() => {
  void frame.value
  return BOTTLENECKS.map(b => {
    const capacity = linkCapacity(b.link, sim.value.cfg.cap)
    const used = props.mode === 'rsvp' ? rsvpSim().reserved(b.link) : 0 // DiffServ: queue occupancy (Task 4)
    const x0 = (X[b.from] + X[b.to]) / 2 - BAR_W / 2
    return { ...b, x0, fill: BAR_W * Math.min(1, capacity > 0 ? used / capacity : 0), label: `${props.mode === 'rsvp' ? 'reserved ' : ''}${fmtRate(used)} / ${fmtRate(capacity)} Mbit/s` }
  })
})

/** Messages closer than this on one lane and of one type are drawn as one label with a count. */
const MSG_MERGE = 44

const messages = computed(() => {
  void frame.value
  if (props.mode !== 'rsvp') return []
  const all = rsvpSim().msgs.map(m => ({ type: m.type, x: X[m.from] + (X[m.to] - X[m.from]) * Math.min(1, m.t) }))
  all.sort((a, b) => (a.type < b.type ? -1 : a.type > b.type ? 1 : a.x - b.x))
  const out: { key: string, type: typeof all[number]['type'], x: number, y: number, label: string }[] = []
  let head: { type: string, x: number, n: number } | null = null
  const flush = () => {
    if (!head) return
    const t = head.type as typeof all[number]['type']
    const n = head.n > 1 ? head.n : 0
    out.push({
      key: `${t}${out.length}`,
      type: t,
      x: head.x,
      y: t === 'PATH' ? LANE_PATH : LANE_RESV,
      // PATH and ResvErr end at the arrow on their right, RESV starts at the arrow on its left
      label: t === 'RESV' ? `RESV${n ? ` ×${n}` : ''}` : `${n ? `${n}× ` : ''}${t}`,
    })
  }
  for (const m of all) {
    if (head && head.type === m.type && m.x - head.x < MSG_MERGE) { head.n++; continue }
    flush()
    head = { type: m.type, x: m.x, n: 1 }
  }
  flush()
  return out
})

const activeFlashes = computed(() => {
  void frame.value
  return flashes.value.filter(f => f.until > sim.value.time)
})

/** Dotted data streams: which kinds are on the wire, and the dash phase that makes them move. */
const streams = computed(() => {
  void frame.value
  if (props.mode !== 'rsvp') return []
  let voice = 0
  let video = 0
  let be = 0
  for (const f of rsvpSim().flows) {
    if (f.status === 'reserved') f.kind === 'voice' ? voice++ : video++
    else if (f.status !== 'signalling') be++
  }
  const offset = -((sim.value.time * 30) % 10)
  return [
    { key: 'voice', y: NODE_Y - 5, n: voice, colour: KIND_COLOUR.voice },
    { key: 'video', y: NODE_Y, n: video, colour: KIND_COLOUR.video },
    { key: 'be', y: NODE_Y + 5, n: be, colour: 'var(--vsb-muted)' },
  ].filter(s => s.n > 0).map(s => ({ ...s, offset }))
})

const rsvpSummary = computed(() => {
  void frame.value
  if (props.mode !== 'rsvp') return null
  const s = rsvpSim()
  const by = (st: string) => s.flows.filter(f => f.status === st).length
  const rate = refresh.value ? s.refreshMsgPerSecond() : 0
  return {
    flows: s.flows.length,
    reserved: by('reserved'),
    be: by('besteffort'),
    refused: by('refused'),
    expired: by('expired'),
    rate: rate < 10 ? rate.toFixed(2) : rate.toFixed(0),
  }
})

const dsSummary = computed(() => {
  void frame.value
  if (props.mode !== 'diffserv') return null
  const s = dsSim()
  const kinds: FlowKind[] = ['voice', 'video', 'data']
  return kinds.map(k => ({ kind: k, delay: s.meanDelayMs(k), drops: s.stats[k].dropped }))
})

const nodeRing = (n: NodeId) => (activeFlashes.value.some(f => f.node === n) ? 'var(--qp-red)' : 'var(--vsb-ink)')
</script>

<template>
  <div :class="['qos-path-sim', { compact }]">
    <svg
      :viewBox="`0 0 ${W} ${H}`" role="img"
      :aria-label="mode === 'rsvp'
        ? 'RSVP along a path through two domains: PATH messages go downstream, RESV messages come back with admission control at every router, and every router keeps per-flow state'
        : 'DiffServ along a path through two domains: packets are marked at the edge and the core keeps per-class state'"
    >
      <!-- domains and their boundary -->
      <g v-for="d in DOMAINS" :key="d.name">
        <rect :x="d.x" y="24" :width="d.w" :height="DOMAIN_BOTTOM - 24" class="domain" />
        <text :x="d.x + 8" y="43" class="domain-label">{{ d.name }}</text>
      </g>
      <line :x1="BOUNDARY_X" y1="22" :x2="BOUNDARY_X" :y2="DOMAIN_BOTTOM" class="boundary" />
      <text :x="BOUNDARY_X" y="16" class="label" text-anchor="middle">domain boundary</text>

      <!-- links: fast ones thin, bottlenecks as wide pipes -->
      <line :x1="X.S" :y1="NODE_Y" :x2="X.R" :y2="NODE_Y" class="link" />
      <g v-for="b in BOTTLENECKS" :key="b.link">
        <line :x1="X[b.from]" :y1="NODE_Y - 9" :x2="X[b.to]" :y2="NODE_Y - 9" class="pipe" />
        <line :x1="X[b.from]" :y1="NODE_Y + 9" :x2="X[b.to]" :y2="NODE_Y + 9" class="pipe" />
      </g>

      <!-- capacity bars above the bottlenecks -->
      <g v-for="b in bars" :key="`bar-${b.link}`">
        <text :x="b.x0 + BAR_W / 2" y="40" class="value" text-anchor="middle">{{ b.label }}</text>
        <rect :x="b.x0" y="46" :width="BAR_W" height="8" class="bar-frame" />
        <rect :x="b.x0" y="46" :width="b.fill" height="8" class="bar-fill" />
      </g>

      <!-- data streams (under the nodes) -->
      <line
        v-for="s in streams" :key="s.key"
        :x1="X.S" :y1="s.y" :x2="X.R" :y2="s.y" class="stream"
        :style="{ stroke: s.colour }" :stroke-dashoffset="s.offset"
      />

      <!-- nodes -->
      <g v-for="n in PATH" :key="n">
        <template v-if="ROLE[n] === 'host'">
          <rect :x="X[n] - 20" :y="NODE_Y - 15" width="40" height="30" class="node" />
          <text :x="X[n]" :y="NODE_Y + 52" class="label" text-anchor="middle">{{ n === 'S' ? 'sender' : 'receiver' }}</text>
        </template>
        <template v-else>
          <circle :cx="X[n]" :cy="NODE_Y" :r="R_NODE" class="node" :stroke="nodeRing(n)" />
          <circle v-if="ROLE[n] === 'edge'" :cx="X[n]" :cy="NODE_Y" :r="R_NODE - 4" class="node inner" :stroke="nodeRing(n)" />
        </template>
        <text :x="X[n]" :y="NODE_Y + 5" class="node-label" text-anchor="middle">{{ n }}</text>
      </g>

      <!-- refusal / crash flashes -->
      <g v-for="f in activeFlashes" :key="`flash-${f.node}`">
        <circle :cx="X[f.node]" :cy="NODE_Y" :r="R_NODE + 5" class="flash-ring" />
        <text :x="X[f.node]" y="71" class="flash-label halo" text-anchor="middle">{{ f.text }}</text>
      </g>

      <!-- RSVP messages: PATH above the line going right, RESV below going left, ResvErr below going right -->
      <g v-for="m in messages" :key="m.key" :transform="`translate(${m.x.toFixed(1)}, ${m.y})`" :class="['msg', m.type]">
        <template v-if="m.type === 'RESV'">
          <text x="-16" y="0" class="halo">{{ m.label }}</text>
          <polygon points="-19,-10 -25,-6 -19,-2" />
        </template>
        <template v-else>
          <text x="16" y="0" text-anchor="end" class="halo">{{ m.label }}</text>
          <polygon points="19,-10 25,-6 19,-2" />
        </template>
      </g>

      <!-- state panels -->
      <g v-for="p in panels" :key="`panel-${p.node}`">
        <text :x="p.x" :y="PANEL_Y" class="count" text-anchor="middle">
          <tspan class="count-n">{{ p.count }}</tspan><tspan dx="4">{{ p.count === 1 ? 'entry' : 'entries' }}</tspan>
        </text>
        <g v-for="(r, i) in p.rows" :key="`${r.kind}${r.flow}`" :transform="`translate(${p.x - PANEL_W / 2}, ${PANEL_Y + 20 + i * ROW_H})`">
          <text x="0" y="0" :class="['row-kind', r.kind]">{{ r.kind }}</text>
          <text x="11" y="0" class="row" :style="{ fill: r.colour }">{{ r.flow }}</text>
          <text x="35" y="0" class="row muted">{{ r.hop }}</text>
          <text :x="PANEL_W" y="0" class="row" text-anchor="end">{{ r.rate }}</text>
          <rect v-if="r.life !== null" x="0" y="4" :width="PANEL_W * r.life" height="2.5" class="age" :opacity="0.25 + 0.75 * r.life" />
        </g>
        <g v-for="(d, i) in p.detail" :key="`d${i}`" :transform="`translate(${p.x - PANEL_W / 2}, ${PANEL_Y + 20 + i * ROW_H})`">
          <text x="0" y="0" class="row">{{ d.key }}</text>
          <text :x="PANEL_W" y="0" class="row muted" text-anchor="end">{{ d.value }}</text>
        </g>
        <text v-if="!compact && p.more > 0" :x="p.x" :y="PANEL_Y + 20 + MAX_ROWS * ROW_H" class="row muted" text-anchor="middle">+ {{ p.more }} more</text>
      </g>

      <!-- footer -->
      <template v-if="rsvpSummary">
        <g v-if="!compact" class="legend" transform="translate(0, 322)">
          <text x="0" y="0" class="msg PATH">PATH</text><polygon points="38,-10 44,-6 38,-2" class="msg PATH" />
          <polygon points="76,-10 70,-6 76,-2" class="msg RESV" /><text x="80" y="0" class="msg RESV">RESV</text>
          <text x="136" y="0" class="msg ResvErr">ResvErr</text>
          <text x="206" y="0" class="label">data: reserved</text>
          <line x1="302" y1="-5" x2="326" y2="-5" class="stream" :style="{ stroke: KIND_COLOUR.voice }" />
          <text x="331" y="0" class="label">voice</text>
          <line x1="372" y1="-5" x2="396" y2="-5" class="stream" :style="{ stroke: KIND_COLOUR.video }" />
          <text x="401" y="0" class="label">video</text>
          <line x1="444" y1="-5" x2="468" y2="-5" class="stream" style="stroke: var(--vsb-muted)" />
          <text x="473" y="0" class="label">best effort</text>
          <text :x="W" y="0" class="label" text-anchor="end">simplified: state expires after 3 missed refreshes</text>
        </g>
        <text x="0" :y="H - 8" class="value">
          refresh messages on the bottleneck: {{ rsvpSummary.rate }} /s (real network, R = 30 s)
        </text>
        <text v-if="!compact" :x="W" :y="H - 8" class="value" text-anchor="end">
          flows {{ rsvpSummary.flows }} · reserved {{ rsvpSummary.reserved }} · best effort {{ rsvpSummary.be }}<tspan v-if="rsvpSummary.refused" class="refused"> · refused {{ rsvpSummary.refused }}</tspan><tspan v-if="rsvpSummary.expired"> · expired {{ rsvpSummary.expired }}</tspan>
        </text>
      </template>
      <text v-if="dsSummary" x="0" :y="H - 8" class="value">
        mean delay at R: {{ dsSummary.map(d => `${d.kind} ${Number.isNaN(d.delay) ? '–' : d.delay.toFixed(0)} ms (${d.drops} dropped)`).join(' · ') }}
      </text>
    </svg>

    <div v-if="!isPrintMode" class="controls">
      <button type="button" @click="running ? pause() : play()">{{ running ? 'Pause' : 'Play' }}</button>
      <button type="button" @click="step">Step</button>
      <button type="button" @click="reset">Reset</button>
      <label>speed <input v-model.number="speedIdx" type="range" min="0" :max="SPEEDS.length - 1" step="1"> {{ speed }}×</label>
      <template v-if="flows === undefined">
        <button type="button" @click="addFlows(1)">+1 flow</button>
        <button type="button" @click="addFlows(10)">+10 flows</button>
      </template>
      <template v-if="mode === 'rsvp'">
        <label><input v-model="refresh" type="checkbox"> refresh</label>
        <label><input v-model="foreignPolicy" type="checkbox"> B refuses foreign reservations</label>
        <button type="button" @click="failC1">fail C1</button>
      </template>
      <template v-else>
        <label>boundary
          <select v-model="boundary">
            <option value="trust">trust</option>
            <option value="remark">re-mark</option>
            <option value="bleach">bleach</option>
          </select>
        </label>
        <label>cross-traffic in B <input v-model.number="crossB" type="range" min="0" max="15" step="1"> {{ crossB }} Mbit/s</label>
      </template>
    </div>
  </div>
</template>

<style scoped>
.qos-path-sim {
  width: 100%;
  --qp-red: #E4002B;  /* FMT red, reserved for refusals and drops (VSB-STYLE.md §9) */
  --qp-blue: #0047BB; /* EKF blue, second series colour (R26) */
}
:global(html.dark .qos-path-sim) {
  --qp-red: #FF4D6D;  /* dark-mode FMT, as PALETTES in generate-figures.py (R7a) */
  --qp-blue: #6E9BFF; /* dark-mode EKF */
}
svg { display: block; width: 100%; height: auto; font-family: var(--vsb-font-text); }
.label { font-size: 14px; fill: var(--vsb-muted); }
.value { font-size: 14px; fill: var(--vsb-ink); font-variant-numeric: tabular-nums; }
.halo { paint-order: stroke; stroke: var(--vsb-bg); stroke-width: 4px; stroke-linejoin: round; }
.domain { fill: none; stroke: var(--vsb-muted); stroke-width: 1.2; stroke-dasharray: 6 4; }
.domain-label { font-size: 16px; font-weight: 700; fill: var(--vsb-green-text); }
.boundary { stroke: var(--vsb-fei); stroke-width: 2; }
.link { stroke: var(--vsb-muted); stroke-width: 1.5; }
.pipe { stroke: var(--vsb-ink); stroke-width: 2; }
.bar-frame { fill: none; stroke: var(--vsb-muted); stroke-width: 1; }
.bar-fill { fill: var(--vsb-green); }
.stream { stroke-width: 3; stroke-linecap: round; stroke-dasharray: 0.1 10; }
.node { fill: var(--vsb-bg); stroke: var(--vsb-ink); stroke-width: 2; }
.node.inner { stroke-width: 1.5; }
.node-label { font-size: 14px; font-weight: 700; fill: var(--vsb-ink); }
.flash-ring { fill: none; stroke: var(--qp-red); stroke-width: 3; }
.flash-label { font-size: 14px; font-weight: 700; fill: var(--qp-red); }
.msg { font-size: 14px; font-weight: 700; }
.msg.PATH { fill: var(--vsb-green-text); }
.msg.RESV { fill: var(--vsb-green-dark); }
.msg.ResvErr { fill: var(--qp-red); }
.count { font-size: 14px; fill: var(--vsb-muted); }
.count-n { font-size: 20px; font-weight: 700; fill: var(--vsb-ink); font-variant-numeric: tabular-nums; }
.row { font-size: 14px; fill: var(--vsb-ink); font-variant-numeric: tabular-nums; }
.row.muted { fill: var(--vsb-muted); }
.row-kind { font-size: 14px; font-weight: 700; fill: var(--vsb-ink); }
.row-kind.R { fill: var(--vsb-green-dark); }
.age { fill: var(--vsb-green); }
.refused { fill: var(--qp-red); }

.controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4em 0.9em;
  margin-top: 0.3rem;
  font-size: 0.8rem;
  color: var(--vsb-ink);
}
.controls label { display: inline-flex; align-items: center; gap: 0.35em; }
.controls input[type='range'] { width: 80px; accent-color: var(--vsb-green); }
.controls input[type='checkbox'] { accent-color: var(--vsb-green); }
.controls select {
  font: inherit;
  color: var(--vsb-ink);
  background: var(--vsb-bg);
  border: 1px solid var(--vsb-muted);
  border-radius: 0; /* R24 */
}
.controls button {
  padding: 0.05em 0.7em;
  border: 1.5px solid var(--vsb-green);
  border-radius: 0; /* R24 — hard edges */
  background: transparent;
  color: var(--vsb-green-text);
  font: inherit;
  cursor: pointer;
}
.controls button:hover { background: #005F58; border-color: #005F58; color: #FFFFFF; }
</style>
