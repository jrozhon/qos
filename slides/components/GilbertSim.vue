<!--
  Animated two-state packet-loss model as a network device.

  Packets enter from the left, the chain (T = transmit, L = loss) steps once per packet, and the
  packet either leaves on the right (transmitted) or drops out of the box (lost). Every random draw
  is shown on a 0–1 bar with its comparison. The grid on the right records every packet's fate row
  by row; the chart below plots the cumulative loss percentage against the model's steady state.

  model  'bernoulli'  next state is L with probability p, whatever the current state (no memory)
         'simple'     Simple Gilbert: T -> L with p, L -> T with q; the state decides the fate
         'gilbert'    adds emission h: in L a packet still gets through with probability h
         'elliott'    Gilbert-Elliott: adds k as well: in T a packet gets through with probability k
  p, q, h, k          model parameters (defaults 0.05, 0.3, 0.2, 0.97)
  rate   packets per second of animation        (default 6)
  total  packets per run, one grid square each  (default 240)
  seed   seed of the first run; Reset moves on to the next seed

  Runs only in the browser (`npm run dev`, the built site). Its slide carries `class: export-skip`,
  which drops it from the PDF (see style.css and slides/README.md).
-->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, shallowRef, useId } from 'vue'
import { onSlideLeave } from '@slidev/client'

type Model = 'bernoulli' | 'simple' | 'gilbert' | 'elliott'
type State = 'T' | 'L'

const props = withDefaults(defineProps<{
  model?: Model
  p?: number
  q?: number
  h?: number
  k?: number
  rate?: number
  total?: number
  seed?: number
  diagram?: boolean // draw only the state diagram: no current state, no animation, no controls
  alt?: string // accessible description in diagram mode
}>(), { model: 'simple', p: 0.05, q: 0.3, h: 0.2, k: 0.97, rate: 6, total: 240, seed: 1, diagram: false })

const EMITS = props.model === 'gilbert' || props.model === 'elliott' // fate needs its own draw
const TITLES = { bernoulli: 'Bernoulli', simple: 'Simple Gilbert', gilbert: 'Gilbert', elliott: 'Gilbert–Elliott' }

// ids must be unique per instance: the static diagram and the live slide of a model are in the DOM together
const uid = useId()

// geometry (SVG units = slide px); a second draw row pushes the chain diagram down by DY
const DY = EMITS && !props.diagram ? 24 : 0
const DIAGRAM_VIEW = '154 62 212 106' // the chain alone, as a static slide figure
const LANE_Y = 112 + DY
const BOX = { x: 160, y: 22, w: 200, h: 163 + DY }
const BAR = { x: 180, w: 160, h: 7 }
const ROWS = EMITS ? [31, 56] : [31] // bar y of the transition draw and of the emission draw
const DECIDE_X = BOX.x + BOX.w / 2
const EXIT_X = 480
const PKT = 12
const SPEED = 240 // px/s along the lane
const COLS = 20
const CELL = 16
const GRID = { x: 540, y: 32 }
const CHART = { x: 60, y: 250, w: 800, h: 90 }

const GREEN = 'var(--vsb-green)'
const RED = '#E4002B' // FMT red, reserved for loss/error marks (VSB-STYLE.md §9)

const p = ref(props.p)
const q = ref(props.q)
const h = ref(props.h)
const k = ref(props.model === 'elliott' ? props.k : 1) // the Gilbert model always transmits in T
const rate = ref(props.rate)
const running = ref(false)
const state = ref<State>('T')
const lastMove = ref<'' | 'TT' | 'TL' | 'LT' | 'LL'>('')
const stepNo = ref(0) // restarts the per-step pulse animations, even when the state does not change
const outcomes = ref<number[]>([]) // 1 = lost, 0 = transmitted

// the last transition draw: u compared with thr, below it the chain goes to `below`, otherwise to `above`
const move = ref<{ u: number, thr: number, sym: string, below: State, above: State } | null>(null)
// the last emission draw: v below ok = transmitted (k in T, h in L)
const emit = ref<{ v: number, ok: number, sym: string, state: State } | null>(null)

// transition arrows of the chain, all clockwise, so every arrow moves rightward along its top;
// the pulse overlay reuses the same paths
const EDGES = {
  TL: 'M240,96 Q260,78 280,96',
  LT: 'M280,128 Q260,146 240,128',
  TT: 'M210,126 C180,144 180,80 210,98',
  LL: 'M310,98 C340,80 340,144 310,126',
} as const
// cross-arc labels above and below, self-loop labels out beside their loops
const LABEL_POS = {
  TL: { x: 260, y: 76, anchor: 'middle' },
  LT: { x: 260, y: 160, anchor: 'middle' },
  TT: { x: 183, y: 116, anchor: 'end' },
  LL: { x: 337, y: 116, anchor: 'start' },
} as const
const EDGE_LABEL = props.model === 'bernoulli'
  ? { TL: 'p', LT: '1−p', TT: '1−p', LL: 'p' }
  : { TL: 'p', LT: 'q', TT: '1−p', LL: '1−q' }

interface Packet { id: number, x: number, y: number, phase: 'in' | 'out' | 'drop', alpha: number }
const packets = shallowRef<Packet[]>([])

let seed = props.seed
let rand = mulberry32(seed)
let spawned = 0
let spawnAcc = 1 // first packet appears at once
let nextId = 0
let frame = 0
let last = 0

function mulberry32(a: number) {
  return () => {
    a |= 0
    a = (a + 0x6D2B79F5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// the rule for the next state, as "u < thr -> below, otherwise above"
function transitionRule(from: State) {
  if (props.model === 'bernoulli') return { thr: p.value, sym: 'p', below: 'L' as State, above: 'T' as State }
  return from === 'T'
    ? { thr: p.value, sym: 'p', below: 'L' as State, above: 'T' as State }
    : { thr: q.value, sym: 'q', below: 'T' as State, above: 'L' as State }
}
const emissionRule = (s: State) => (s === 'T' ? { ok: k.value, sym: 'k' } : { ok: h.value, sym: 'h' })

// one step of the chain per packet (the first packet starts in T), then the packet's fate:
// the state itself, or for the emission models a second draw against k or h
function decide(): boolean {
  if (outcomes.value.length > 0) {
    const from = state.value
    const u = rand()
    const rule = transitionRule(from)
    state.value = u < rule.thr ? rule.below : rule.above
    move.value = { u, ...rule }
    lastMove.value = `${from}${state.value}` as typeof lastMove.value
    stepNo.value++
  }
  let lost = state.value === 'L'
  if (EMITS) {
    const v = rand()
    const rule = emissionRule(state.value)
    lost = v >= rule.ok
    emit.value = { v, ...rule, state: state.value }
  }
  outcomes.value = [...outcomes.value, lost ? 1 : 0]
  return lost
}

function step(dt: number) {
  spawnAcc += dt * rate.value
  const fresh: Packet[] = []
  while (spawnAcc >= 1 && spawned < props.total) {
    spawnAcc -= 1
    spawned++
    fresh.push({ id: nextId++, x: -PKT, y: LANE_Y, phase: 'in', alpha: 1 })
  }
  if (spawned >= props.total) spawnAcc = 0
  const next: Packet[] = []
  for (const pk of [...packets.value, ...fresh]) {
    if (pk.phase === 'in') {
      pk.x += SPEED * dt
      if (pk.x >= DECIDE_X) {
        if (decide()) {
          pk.phase = 'drop'
          pk.x = DECIDE_X
          pk.y = BOX.y + BOX.h
        }
        else {
          pk.phase = 'out'
          pk.x = BOX.x + BOX.w
        }
      }
    }
    else if (pk.phase === 'out') {
      pk.x += SPEED * dt
      if (pk.x > EXIT_X) continue
    }
    else {
      pk.y += 50 * dt
      pk.alpha -= 2.2 * dt
      if (pk.alpha <= 0) continue
    }
    next.push(pk)
  }
  packets.value = next
  if (spawned >= props.total && packets.value.length === 0) running.value = false
}

function loop(now: number) {
  const dt = Math.min(0.05, (now - last) / 1000)
  last = now
  step(dt)
  if (running.value) frame = requestAnimationFrame(loop)
}

function play() {
  if (done.value) reset()
  running.value = true
  last = performance.now()
  cancelAnimationFrame(frame)
  frame = requestAnimationFrame(loop)
}

function pause() {
  running.value = false
  cancelAnimationFrame(frame)
}

function reset() {
  pause()
  seed++
  rand = mulberry32(seed)
  spawned = 0
  spawnAcc = 1
  state.value = 'T'
  lastMove.value = ''
  stepNo.value = 0
  move.value = null
  emit.value = null
  outcomes.value = []
  packets.value = []
}

onSlideLeave(pause)
onBeforeUnmount(pause)

const sent = computed(() => outcomes.value.length)
const lost = computed(() => outcomes.value.reduce((a, b) => a + b, 0))
const done = computed(() => sent.value >= props.total && packets.value.length === 0)
const lossPct = computed(() => (sent.value ? (100 * lost.value) / sent.value : 0))
const steadyPct = computed(() => {
  if (props.model === 'bernoulli') return 100 * p.value
  const piL = p.value / (p.value + q.value)
  if (!EMITS) return 100 * piL
  return 100 * ((1 - piL) * (1 - k.value) + piL * (1 - h.value))
})
const steadyFormula = { bernoulli: 'p', simple: 'p/(p+q)', gilbert: 'π(L)·(1−h)', elliott: 'π(T)·(1−k) + π(L)·(1−h)' }[props.model]

const cells = computed(() =>
  Array.from({ length: props.total }, (_, i) => ({
    x: GRID.x + (i % COLS) * CELL,
    y: GRID.y + Math.floor(i / COLS) * CELL,
    fill: i < outcomes.value.length ? (outcomes.value[i] ? RED : GREEN) : 'none',
  })),
)

const yMax = computed(() => {
  const need = Math.max(steadyPct.value * 1.6, lossPct.value * 1.2, 10)
  return Math.min(100, Math.ceil(need / 10) * 10)
})
const cx = (i: number) => CHART.x + (i / props.total) * CHART.w
const cy = (pct: number) => CHART.y + CHART.h - (pct / yMax.value) * CHART.h
const lossLine = computed(() => {
  let lostSoFar = 0
  return outcomes.value
    .map((o, i) => {
      lostSoFar += o
      return `${cx(i + 1).toFixed(1)},${cy((100 * lostSoFar) / (i + 1)).toFixed(1)}`
    })
    .join(' ')
})
const xTicks = computed(() => [0, 0.25, 0.5, 0.75, 1].map(f => Math.round(f * props.total)))
const yTicks = computed(() => [0, yMax.value / 2, yMax.value])

const arrow = (m: string) => (lastMove.value === m ? 'active' : '')
// finish each pulse before the next packet arrives, at every speed
const pulseDur = computed(() => `${Math.min(0.55, 0.85 / rate.value).toFixed(3)}s`)
const colour = (s: State) => (s === 'T' ? GREEN : RED)
const shown = computed(() => (props.diagram ? null : state.value))

// emission pairs under the states (the Gilbert model emits only in L, like its static diagram)
const STATE_X = { T: 225, L: 295 }
const emitPairs = [
  ...(props.model === 'elliott' ? [{ state: 'T' as State, cx: STATE_X.T, ok: 'k', lost: '1−k' }] : []),
  ...(EMITS ? [{ state: 'L' as State, cx: STATE_X.L, ok: 'h', lost: '1−h' }] : []),
]
const isHit = (s: State, ok: boolean) =>
  !!emit.value && emit.value.state === s && (emit.value.v < emit.value.ok) === ok
const emitFlash = computed(() => {
  const e = emit.value
  if (!e || !emitPairs.some(pair => pair.state === e.state)) return null
  const ok = e.v < e.ok
  return { ok, x: ok ? STATE_X[e.state] - 22 : STATE_X[e.state] + 1 }
})

// one bar per draw: [0, thr) coloured by where "below" leads, [thr, 1) by where "above" leads, marker at the draw
const bars = computed(() => {
  const t = move.value ?? { u: null, ...transitionRule(state.value) }
  const rows = [{
    cut: BAR.x + t.thr * BAR.w,
    lo: colour(t.below),
    hi: colour(t.above),
    marker: t.u === null ? null : BAR.x + t.u * BAR.w,
    text: t.u === null
      ? 'u ~ U(0, 1), one draw per packet'
      : t.u < t.thr
        ? `u = ${t.u.toFixed(3)} < ${t.sym} = ${t.thr.toFixed(2)} → ${t.below}`
        : `u = ${t.u.toFixed(3)} ≥ ${t.sym} = ${t.thr.toFixed(2)} → ${t.above}`,
  }]
  if (EMITS) {
    const e = emit.value ?? { v: null, ...emissionRule(state.value) }
    rows.push({
      cut: BAR.x + e.ok * BAR.w,
      lo: GREEN,
      hi: RED,
      marker: e.v === null ? null : BAR.x + e.v * BAR.w,
      text: e.v === null
        ? 'v ~ U(0, 1), decides the packet'
        : e.v < e.ok
          ? `v = ${e.v.toFixed(3)} < ${e.sym} = ${e.ok.toFixed(2)} → transmitted`
          : `v = ${e.v.toFixed(3)} ≥ ${e.sym} = ${e.ok.toFixed(2)} → lost`,
    })
  }
  return rows
})
</script>

<template>
  <div :class="['gilbert-sim', { diagram }]">
    <svg
      :viewBox="diagram ? DIAGRAM_VIEW : '0 0 880 360'" role="img"
      :aria-label="diagram ? (alt ?? `${TITLES[model]} loss model`) : `Animated ${TITLES[model]} loss model: packets pass a two-state device, their fate fills a grid, and a chart tracks the loss percentage`"
    >
      <defs>
        <marker :id="`gs-arrow-${uid}`" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" class="arrow-head" />
        </marker>
        <marker :id="`gs-link-${uid}`" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="5" markerHeight="5" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" class="link-head" />
        </marker>
        <!-- early points can exceed the axis; let them leave the plot instead of flattening at the top -->
        <clipPath :id="`gs-chart-${uid}`">
          <rect :x="CHART.x" :y="CHART.y - 6" :width="CHART.w + 2" :height="CHART.h + 7" />
        </clipPath>
      </defs>

      <template v-if="!diagram">
      <!-- lane and labels -->
      <line :x1="0" :y1="LANE_Y + PKT / 2" :x2="EXIT_X" :y2="LANE_Y + PKT / 2" class="lane" />
      <text x="0" :y="LANE_Y - 10" class="label">incoming</text>
      <text :x="EXIT_X" :y="LANE_Y - 10" class="label" text-anchor="end">transmitted</text>
      <text :x="DECIDE_X + 14" :y="BOX.y + BOX.h + 20" class="label lost-label">lost</text>

      <!-- packets (drawn under the device box) -->
      <rect
        v-for="pk in packets" :key="pk.id"
        :x="pk.x" :y="pk.y" :width="PKT" :height="PKT"
        :fill="pk.phase === 'in' ? 'var(--vsb-muted)' : pk.phase === 'out' ? GREEN : RED"
        :opacity="pk.alpha"
      />

      <!-- the device -->
      <rect :x="BOX.x" :y="BOX.y" :width="BOX.w" :height="BOX.h" class="box" />
      <text :x="BOX.x + BOX.w / 2" :y="BOX.y - 8" class="label" text-anchor="middle">{{ TITLES[model] }} device</text>

      <!-- the random draws of this step: 0–1 bar split at the threshold, marker at the drawn value -->
      <g v-for="(b, i) in bars" :key="`bar${i}`">
        <rect :x="BAR.x" :y="ROWS[i]" :width="b.cut - BAR.x" :height="BAR.h" :fill="b.lo" class="bar-part" />
        <rect :x="b.cut" :y="ROWS[i]" :width="BAR.x + BAR.w - b.cut" :height="BAR.h" :fill="b.hi" class="bar-part" />
        <text :x="BAR.x - 4" :y="ROWS[i] + 7" class="bar-end" text-anchor="end">0</text>
        <text :x="BAR.x + BAR.w + 4" :y="ROWS[i] + 7" class="bar-end">1</text>
        <path v-if="b.marker !== null" :d="`M${b.marker},${ROWS[i] - 3} v${BAR.h + 6}`" class="u-marker" />
        <text :x="BOX.x + BOX.w / 2" :y="ROWS[i] + (EMITS ? 19 : 22)" class="draw-label" text-anchor="middle">{{ b.text }}</text>
      </g>

      </template>

      <!-- the chain, shifted down when there is a second draw row -->
      <g :transform="`translate(0, ${DY})`">
        <template v-for="(d, m) in EDGES" :key="m">
          <path :class="['edge', arrow(m)]" :d="d" :marker-end="`url(#gs-arrow-${uid})`" />
          <text :x="LABEL_POS[m].x" :y="LABEL_POS[m].y" :text-anchor="LABEL_POS[m].anchor" class="edge-label">{{ EDGE_LABEL[m] }}</text>
        </template>

        <!-- emission probabilities: transmitted | lost under each emitting state;
             the box the last v-draw picked is filled, and flashes once per packet -->
        <g v-for="e in emitPairs" :key="e.state">
          <!-- connectors: the state emits into its transmitted | lost pair -->
          <path :d="`M${e.cx - 4},131.5 L${e.cx - 10},144`" :class="['emit-link', { hit: isHit(e.state, true) }]" :marker-end="`url(#gs-link-${uid})`" />
          <path :d="`M${e.cx + 4},131.5 L${e.cx + 10},144`" :class="['emit-link', { hit: isHit(e.state, false) }]" :marker-end="`url(#gs-link-${uid})`" />
          <rect :x="e.cx - 22" y="145" width="21" height="14" :class="['emit', 'emit-ok', { hit: isHit(e.state, true) }]" />
          <text :x="e.cx - 11.5" y="156" text-anchor="middle" :class="['emit-label', { hit: isHit(e.state, true) }]">{{ e.ok }}</text>
          <rect :x="e.cx + 1" y="145" width="21" height="14" :class="['emit', 'emit-lost', { hit: isHit(e.state, false) }]" />
          <text :x="e.cx + 11.5" y="156" text-anchor="middle" :class="['emit-label', { hit: isHit(e.state, false) }]">{{ e.lost }}</text>
        </g>
        <rect
          v-if="emitFlash" :key="`emit${sent}`"
          :x="emitFlash.x" y="145" width="21" height="14" class="emit-flash"
          :stroke="emitFlash.ok ? GREEN : RED" :style="{ animationDuration: pulseDur }"
        />

        <!-- per-step pulse: a short segment runs along the arrow just taken (keyed, so it replays every packet) -->
        <path
          v-if="lastMove" :key="`pulse${stepNo}`"
          :d="EDGES[lastMove]" pathLength="100" class="pulse"
          :stroke="colour(lastMove[1] as State)" :style="{ animationDuration: pulseDur }"
        />

        <!-- the current state is filled solid; the static diagram shows no current state -->
        <circle cx="225" cy="112" r="19" :fill="shown === 'T' ? GREEN : 'var(--vsb-bg)'" :stroke="GREEN" stroke-width="2" />
        <text x="225" y="118" text-anchor="middle" :class="['state', { on: shown === 'T' }]">T</text>
        <circle cx="295" cy="112" r="19" :fill="shown === 'L' ? RED : 'var(--vsb-bg)'" :stroke="RED" stroke-width="2" />
        <text x="295" y="118" text-anchor="middle" :class="['state', { on: shown === 'L' }]">L</text>
        <circle
          v-if="lastMove" :key="`ring${stepNo}`"
          :cx="state === 'T' ? 225 : 295" cy="112" r="19" class="ring"
          :stroke="colour(state)" :style="{ animationDuration: pulseDur }"
        />
        <text v-if="!diagram" x="260" y="178" class="step-label" text-anchor="middle">
          <template v-if="lastMove">packet {{ sent }}: {{ lastMove[0] }} → {{ lastMove[1] }} ({{ EDGE_LABEL[lastMove] }})</template>
          <template v-else-if="sent">packet 1: starts in T</template>
        </text>
      </g>

      <template v-if="!diagram">
      <!-- grid of packet fates -->
      <text :x="GRID.x" :y="GRID.y - 12" class="label">packet fate, row by row</text>
      <rect
        v-for="(c, i) in cells" :key="i"
        :x="c.x" :y="c.y" :width="CELL - 3" :height="CELL - 3"
        :fill="c.fill" class="cell"
      />

      <!-- loss chart -->
      <line :x1="CHART.x" :y1="CHART.y + CHART.h" :x2="CHART.x + CHART.w" :y2="CHART.y + CHART.h" class="axis" />
      <line :x1="CHART.x" :y1="CHART.y" :x2="CHART.x" :y2="CHART.y + CHART.h" class="axis" />
      <g v-for="t in yTicks" :key="`y${t}`">
        <line :x1="CHART.x" :y1="cy(t)" :x2="CHART.x + CHART.w" :y2="cy(t)" class="grid" />
        <text :x="CHART.x - 6" :y="cy(t) + 4" class="tick" text-anchor="end">{{ t }} %</text>
      </g>
      <text v-for="t in xTicks" :key="`x${t}`" :x="cx(t)" :y="CHART.y + CHART.h + 15" class="tick" text-anchor="middle">{{ t }}</text>
      <text :x="CHART.x + CHART.w" :y="CHART.y + CHART.h + 15" class="tick" text-anchor="end" dy="-18">packets sent</text>
      <text :x="CHART.x - 48" :y="CHART.y - 8" class="tick">cumulative loss [%]</text>
      <text :x="CHART.x + CHART.w" :y="CHART.y - 8" class="stats" text-anchor="end">
        sent {{ sent }} · lost {{ lost }} · loss {{ lossPct.toFixed(1) }} %
      </text>
      <line :x1="CHART.x" :y1="cy(steadyPct)" :x2="CHART.x + CHART.w" :y2="cy(steadyPct)" class="steady" />
      <polyline :points="lossLine" class="loss-line" :stroke="RED" :clip-path="`url(#gs-chart-${uid})`" />
      <text :x="CHART.x + CHART.w" :y="cy(steadyPct) + 15" class="tick halo" text-anchor="end">
        steady state {{ steadyFormula }} = {{ steadyPct.toFixed(1) }} %
      </text>
      </template>
    </svg>

    <div v-if="!diagram" :class="['controls', { many: EMITS }]">
      <button type="button" @click="running ? pause() : play()">{{ running ? 'Pause' : done ? 'Replay' : 'Play' }}</button>
      <button type="button" @click="reset">Reset</button>
      <label>p <input v-model.number="p" type="range" min="0.01" max="0.5" step="0.01"> {{ p.toFixed(2) }}</label>
      <label v-if="model !== 'bernoulli'">q <input v-model.number="q" type="range" min="0.05" max="1" step="0.05"> {{ q.toFixed(2) }}</label>
      <label v-if="EMITS">h <input v-model.number="h" type="range" min="0" max="1" step="0.05"> {{ h.toFixed(2) }}</label>
      <label v-if="model === 'elliott'">k <input v-model.number="k" type="range" min="0.5" max="1" step="0.01"> {{ k.toFixed(2) }}</label>
      <label>speed <input v-model.number="rate" type="range" min="2" max="14" step="1"> {{ rate }} packets/s</label>
    </div>
  </div>
</template>

<style scoped>
.gilbert-sim { width: 100%; }
/* static slide figure: the chain alone, centred */
.gilbert-sim.diagram { width: 470px; margin: 0.6rem auto 0; }
svg { display: block; width: 100%; height: auto; font-family: var(--vsb-font-text); }
.label { font-size: 14px; fill: var(--vsb-muted); }
.lost-label { fill: #E4002B; }
.lane { stroke: var(--vsb-hairline); stroke-width: 2; }
.box { fill: var(--vsb-bg); stroke: var(--vsb-ink); stroke-width: 1.5; }
.edge { fill: none; stroke: var(--vsb-muted); stroke-width: 1.5; transition: stroke 0.15s, stroke-width 0.15s; }
.edge.active { stroke: var(--vsb-ink); stroke-width: 3; }
.arrow-head { fill: var(--vsb-muted); }
.edge.active + text { font-weight: 700; }
.edge-label { font-size: 13px; fill: var(--vsb-ink); font-style: italic; }
.step-label { font-size: 12px; fill: var(--vsb-muted); font-variant-numeric: tabular-nums; }
.draw-label { font-size: 12px; fill: var(--vsb-ink); font-variant-numeric: tabular-nums; }
.bar-part { opacity: 0.45; }
.bar-end { font-size: 10px; fill: var(--vsb-muted); }
.u-marker { stroke: var(--vsb-ink); stroke-width: 2.5; }
.pulse {
  fill: none;
  stroke-width: 5;
  stroke-linecap: round;
  stroke-dasharray: 22 200;
  stroke-dashoffset: 22;
  animation: gs-travel linear forwards;
}
@keyframes gs-travel {
  from { stroke-dashoffset: 22; opacity: 1; }
  85%  { opacity: 1; }
  to   { stroke-dashoffset: -100; opacity: 0; }
}
.ring {
  fill: none;
  stroke-width: 3;
  transform-box: fill-box;
  transform-origin: center;
  animation: gs-ring ease-out forwards;
}
@keyframes gs-ring {
  from { transform: scale(1); opacity: 0.9; }
  to   { transform: scale(1.55); opacity: 0; }
}
.emit { stroke-width: 1.2; transition: fill-opacity 0.1s; }
.emit-link { fill: none; stroke: var(--vsb-muted); stroke-width: 1.2; }
.emit-link.hit { stroke: var(--vsb-ink); stroke-width: 2; }
.link-head { fill: var(--vsb-muted); }
.emit-ok { fill: var(--vsb-green); fill-opacity: 0.15; stroke: var(--vsb-green); }
.emit-lost { fill: #E4002B; fill-opacity: 0.12; stroke: #E4002B; }
.emit.hit { fill-opacity: 1; }
.emit-label { font-size: 10px; font-style: italic; fill: var(--vsb-ink); pointer-events: none; }
.emit-label.hit { fill: #FFFFFF; font-weight: 700; }
.emit-flash {
  fill: none;
  stroke-width: 2.5;
  transform-box: fill-box;
  transform-origin: center;
  animation: gs-emit ease-out forwards;
}
@keyframes gs-emit {
  from { transform: scale(1); opacity: 1; }
  to   { transform: scale(1.7); opacity: 0; }
}
.state { font-size: 17px; font-weight: 700; fill: var(--vsb-ink); }
.state.on { fill: #FFFFFF; }
.cell { stroke: var(--vsb-hairline); stroke-width: 1; }
.axis { stroke: var(--vsb-muted); stroke-width: 1; }
.grid { stroke: var(--vsb-hairline); stroke-width: 1; }
.tick { font-size: 12px; fill: var(--vsb-muted); }
.stats { font-size: 13px; fill: var(--vsb-ink); font-variant-numeric: tabular-nums; }
.halo { paint-order: stroke; stroke: var(--vsb-bg); stroke-width: 4px; }
.steady { stroke: var(--vsb-muted); stroke-width: 1.5; stroke-dasharray: 6 4; }
.loss-line { fill: none; stroke-width: 2.5; }

.controls {
  display: flex;
  align-items: center;
  gap: 1.1em;
  margin-top: 0.3rem;
  font-size: 0.8rem;
  color: var(--vsb-ink);
}
.controls label { display: inline-flex; align-items: center; gap: 0.35em; }
.controls input[type='range'] { width: 90px; accent-color: var(--vsb-green); }
.controls.many { gap: 0.9em; }
.controls.many input[type='range'] { width: 70px; }
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
