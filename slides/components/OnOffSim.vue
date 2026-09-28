<!--
  Where self-similarity comes from: N independent ON/OFF sources and their aggregate.

  Top: the ON periods of all N sources over the last 400 slots, scrolling (exponential or Pareto periods,
  toggle). Bottom: the long view — the fraction of the N sources that are ON, averaged over 250-slot blocks,
  for the last 100 000 slots, for BOTH period distributions at once. In any single slot the two look alike
  (each source is ON half the time, independently); the difference is how long deviations last.
  Exponential periods are forgotten quickly, so the long-run average hugs the mean; Pareto periods leave
  long excursions at every time scale.

  n      number of sources, all drawn (default 16, fixed during the run: the contrast is about time scales,
         not about how many sources are multiplexed)
  alpha  Pareto shape, 1 < alpha < 2 (default 1.4); the aggregate has H = (3 - alpha) / 2
  tail   period distribution of the rows drawn at the top (default 'pareto')

  The long view is built period by period (advanceRanges / a difference array), not slot by slot, so moving
  a slider recomputes it in milliseconds.

  Browser only: its slide carries `class: export-skip` (see style.css and slides/README.md).
-->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import { onSlideLeave } from '@slidev/client'
import { advanceRanges, hurstFromAlpha, makeSources, mulberry32, type OnOffSource, type Tail } from '../utils/traffic'

const props = withDefaults(defineProps<{ n?: number, alpha?: number, tail?: Tail, seed?: number }>(),
  { n: 16, alpha: 1.4, tail: 'pareto', seed: 7 })

const W = 400 // slots in the rows view
const MEAN = 12 // mean ON and OFF period [slots]
const BLOCK = 250 // slots per point of the long view
const POINTS = 400 // points in the long view (100 000 slots)
const X0 = 60
const PX = 800 / W
const ROWS = { y: 24, h: 174 } // area of the rows view
const AGG = { y: 232, h: 100, lo: 0.2, hi: 0.8 }
const GREEN = 'var(--vsb-green)'
const GREY = 'var(--vsb-muted)'
const TAILS: Tail[] = ['exponential', 'pareto']

const n = props.n
const alpha = ref(props.alpha)
const tail = ref<Tail>(props.tail)
const rate = ref(60) // slots per second
const running = ref(false)

let seed = props.seed
interface Pop { sources: OnOffSource[], block: number, filled: number }
let pops: Record<Tail, Pop>
const rows = shallowRef<boolean[][]>([]) // selected tail, per source, the last W slots
const long = shallowRef<Record<Tail, number[]>>({ exponential: [], pareto: [] }) // block averages

// warm up both populations, then build the long view and the rows in one pass over whole periods
function rebuild() {
  const rand = mulberry32(seed)
  const T = BLOCK * POINTS
  const out = {} as Record<Tail, number[]>
  pops = {} as Record<Tail, Pop>
  let shownRows: boolean[][] = []
  for (const t of TAILS) {
    const sources = makeSources(n, t, MEAN, alpha.value, rand)
    sources.forEach(s => advanceRanges(s, 5000))
    const diff = new Int32Array(T + 1)
    const r = sources.map(() => Array.from({ length: W }, () => false))
    sources.forEach((s, i) => advanceRanges(s, T, (a, b) => {
      diff[a]++
      diff[b]--
      for (let k = Math.max(a, T - W); k < b; k++) r[i][k - (T - W)] = true
    }))
    const avg: number[] = []
    let on = 0
    let sum = 0
    for (let k = 0; k < T; k++) {
      on += diff[k]
      sum += on
      if ((k + 1) % BLOCK === 0) {
        avg.push(sum / BLOCK / n)
        sum = 0
      }
    }
    out[t] = avg
    pops[t] = { sources, block: 0, filled: 0 }
    if (t === tail.value) shownRows = r
  }
  rows.value = shownRows
  long.value = out
}

// one slot of both populations, slot by slot for the live scroll; a finished block scrolls the long view
function advance(out: Record<Tail, number[]>): boolean[] {
  let shown: boolean[] = []
  for (const t of TAILS) {
    const p = pops[t]
    let on = 0
    const states = p.sources.map((s) => {
      const was = s.step()
      if (was) on++
      return was
    })
    if (t === tail.value) shown = states
    p.block += on / p.sources.length
    if (++p.filled === BLOCK) {
      out[t].push(p.block / BLOCK)
      out[t].shift()
      p.block = 0
      p.filled = 0
    }
  }
  return shown
}

rebuild()
watch([alpha, tail], rebuild)

let frame = 0
let last = 0
let acc = 0
function loop(now: number) {
  acc += Math.min(0.1, (now - last) / 1000) * rate.value
  last = now
  if (acc >= 1) {
    const r = rows.value.map(row => row.slice())
    const l = { exponential: long.value.exponential.slice(), pareto: long.value.pareto.slice() }
    while (acc >= 1) {
      acc -= 1
      const states = advance(l)
      r.forEach((row, i) => { row.push(states[i]); row.shift() })
    }
    rows.value = r
    long.value = l
  }
  if (running.value) frame = requestAnimationFrame(loop)
}
function play() {
  running.value = true
  last = performance.now()
  cancelAnimationFrame(frame)
  frame = requestAnimationFrame(loop)
}
function pause() {
  running.value = false
  cancelAnimationFrame(frame)
}
function reseed() {
  seed++
  rebuild()
}
onSlideLeave(pause)
onBeforeUnmount(pause)

// every source gets a row; rows get thinner as N grows, labels only while they fit
const rowH = computed(() => ROWS.h / rows.value.length)
const labelEvery = computed(() => (rowH.value >= 8 ? 1 : rowH.value >= 4 ? 5 : 10))
const runs = computed(() => rows.value.map((row) => {
  const out: { x: number, w: number }[] = []
  let start = -1
  row.forEach((on, t) => {
    if (on && start < 0) start = t
    if ((!on || t === row.length - 1) && start >= 0) {
      const end = on ? t + 1 : t
      out.push({ x: X0 + start * PX, w: (end - start) * PX })
      start = -1
    }
  })
  return out
}))

const aggY = (f: number) => AGG.y + AGG.h - ((Math.min(Math.max(f, AGG.lo), AGG.hi) - AGG.lo) / (AGG.hi - AGG.lo)) * AGG.h
const line = (vals: number[]) => vals.map((f, i) => `${(X0 + (i * 800) / (POINTS - 1)).toFixed(1)},${aggY(f).toFixed(1)}`).join(' ')
const sd = (vals: number[]) => {
  const m = vals.reduce((s, x) => s + x, 0) / vals.length
  return Math.sqrt(vals.reduce((s, x) => s + (x - m) ** 2, 0) / vals.length)
}
const lines = computed(() => ({ exponential: line(long.value.exponential), pareto: line(long.value.pareto) }))
const spreads = computed(() => ({ exponential: sd(long.value.exponential), pareto: sd(long.value.pareto) }))
</script>

<template>
  <div class="onoff-sim">
    <svg viewBox="0 0 880 360" role="img" aria-label="Animated ON/OFF sources: every source's ON periods scroll above a long-run chart of the fraction of sources ON, for exponential and for Pareto periods">
      <text :x="X0" y="14" class="label">
        ON periods of all {{ n }} sources, last {{ W }} slots
        ({{ tail === 'pareto' ? `Pareto, α = ${alpha.toFixed(2)}` : 'exponential' }}, mean {{ MEAN }} slots)
      </text>
      <g v-for="(r, i) in runs" :key="i">
        <rect
          v-for="(s, j) in r" :key="j" :x="s.x" :y="ROWS.y + i * rowH" :width="s.w" :height="Math.max(rowH * 0.72, 0.8)"
          :fill="tail === 'pareto' ? GREEN : GREY"
        />
        <text v-if="(i + 1) % labelEvery === 0 || labelEvery === 1" :x="X0 - 8" :y="ROWS.y + i * rowH + Math.min(rowH * 0.72, 8)" class="tick" text-anchor="end">{{ i + 1 }}</text>
      </g>

      <text :x="X0" :y="AGG.y - 12" class="label">
        the long view: fraction of the {{ n }} sources ON, {{ BLOCK }}-slot averages over {{ (BLOCK * POINTS).toLocaleString('en') }} slots
      </text>
      <line :x1="X0" :x2="X0" :y1="AGG.y" :y2="AGG.y + AGG.h" class="axis" />
      <line :x1="X0" :x2="X0 + 800" :y1="AGG.y + AGG.h" :y2="AGG.y + AGG.h" class="axis" />
      <g v-for="f in [AGG.lo, 0.5, AGG.hi]" :key="f">
        <line :x1="X0" :x2="X0 + 800" :y1="aggY(f)" :y2="aggY(f)" :class="f === 0.5 ? 'mean' : 'grid'" />
        <text :x="X0 - 8" :y="aggY(f) + 4" class="tick" text-anchor="end">{{ f }}</text>
      </g>
      <polyline :points="lines.exponential" class="agg" :stroke="GREY" />
      <polyline :points="lines.pareto" class="agg" :stroke="GREEN" />
      <text :x="X0 + 800" :y="AGG.y + AGG.h + 16" class="stats" text-anchor="end">
        spread (std) of the averages:
        <tspan :fill="GREY" font-weight="700">exponential {{ spreads.exponential.toFixed(3) }}</tspan> ·
        <tspan :fill="GREEN" font-weight="700">Pareto {{ spreads.pareto.toFixed(3) }}</tspan>
      </text>
    </svg>

    <div class="sim-controls">
      <button type="button" @click="running ? pause() : play()">{{ running ? 'Pause' : 'Play' }}</button>
      <button type="button" @click="reseed">New run</button>
      <button type="button" :class="{ on: tail === 'exponential' }" @click="tail = 'exponential'">exponential</button>
      <button type="button" :class="{ on: tail === 'pareto' }" @click="tail = 'pareto'">Pareto</button>
      <label>α <input v-model.number="alpha" type="range" min="1.1" max="1.9" step="0.05"> {{ alpha.toFixed(2) }}</label>
      <label>speed <input v-model.number="rate" type="range" min="20" max="240" step="10"> {{ rate }} slots/s</label>
      <span class="readout">Pareto H = {{ hurstFromAlpha(alpha).toFixed(2) }}</span>
    </div>
  </div>
</template>

<style scoped>
.onoff-sim { width: 100%; }
svg { display: block; width: 100%; height: auto; font-family: var(--vsb-font-text); }
.label { font-size: 14px; fill: var(--vsb-muted); }
.stats { font-size: 13px; fill: var(--vsb-ink); font-variant-numeric: tabular-nums; }
.tick { font-size: 11px; fill: var(--vsb-muted); }
.axis { stroke: var(--vsb-muted); stroke-width: 1; }
.grid { stroke: var(--vsb-hairline); stroke-width: 1; }
.mean { stroke: var(--vsb-muted); stroke-width: 1.2; stroke-dasharray: 6 4; }
.agg { fill: none; stroke-width: 1.6; }
</style>
