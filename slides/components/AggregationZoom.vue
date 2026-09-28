<!--
  Scale-invariance, live: a Poisson trace and a self-similar trace with the same mean rate, both aggregated
  over ever larger blocks of m slots (m = 1, 2, 4, … 256; each bar is the mean of m slots, the window grows
  to 128·m slots). The Poisson trace flattens into a line; the self-similar one stays bursty.

  Right: the variance-time plot, log10 of the variance of the m-aggregated trace (relative to m = 1) against
  log10 m, filled in as the zoom proceeds. Independent arrivals fall with slope −1; a self-similar trace with
  slope 2H − 2, so the fitted slope gives an estimate of H.

  alpha  Pareto shape of the ON/OFF periods (default 1.4, theory H = (3 − alpha)/2 = 0.8)

  Browser only: its slide carries `class: export-skip` (see style.css and slides/README.md).
-->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, shallowRef } from 'vue'
import { onSlideLeave } from '@slidev/client'
import { advanceRanges, countOn, hurstFromAlpha, makeSources, mulberry32, poisson } from '../utils/traffic'

const props = withDefaults(defineProps<{ alpha?: number, seed?: number }>(), { alpha: 1.4, seed: 11 })

const L = 1 << 16 // slots in each trace
const N = 40 // ON/OFF sources in the self-similar trace
const MEAN = 12 // mean ON/OFF period [slots]
const BARS = 128
const LEVELS = 9 // m = 1 … 256
const PANEL = { x: 50, w: 520, h: 110 }
const PANELS = [{ y: 34, key: 'poisson' }, { y: 196, key: 'selfsim' }] as const
const VT = { x: 640, y: 34, w: 220, h: 236 } // variance-time plot
const VT_Y = { top: 0.1, bottom: -2.7 } // log10 relative variance range

const GREEN = 'var(--vsb-green)'
const GREY = 'var(--vsb-muted)'

const level = ref(0) // m = 2^level
const running = ref(false)
let seed = props.seed

interface Trace {
  poisson: Float64Array
  selfsim: Float64Array
  logVar: { poisson: number[], selfsim: number[] }
  sd: number[] // standard deviation of the m-aggregated self-similar trace, per level
}
const trace = shallowRef<Trace>(generate())

// both traces have mean N/2 arrivals per slot
function generate(): Trace {
  const rand = mulberry32(seed)
  const sources = makeSources(N, 'pareto', MEAN, props.alpha, rand)
  sources.forEach(s => advanceRanges(s, 5000))
  const selfsim = Float64Array.from(countOn(sources, L)) // period by period, not slot by slot
  const pois = new Float64Array(L)
  for (let t = 0; t < L; t++) pois[t] = poisson(N / 2, rand)
  const logVar = { poisson: variances(pois), selfsim: variances(selfsim) }
  return { poisson: pois, selfsim, logVar, sd: sds(selfsim) }
}

function aggregate(x: Float64Array, m: number, count: number): number[] {
  const out: number[] = []
  for (let b = 0; b < count; b++) {
    let s = 0
    for (let i = b * m; i < (b + 1) * m; i++) s += x[i]
    out.push(s / m)
  }
  return out
}

function sds(x: Float64Array): number[] {
  return Array.from({ length: LEVELS }, (_, k) => {
    const a = aggregate(x, 1 << k, Math.floor(L / (1 << k)))
    const mean = a.reduce((s, y) => s + y, 0) / a.length
    return Math.sqrt(a.reduce((s, y) => s + (y - mean) ** 2, 0) / a.length)
  })
}

// log10 of Var(X^(m)) / Var(X) for every level, over the whole trace
function variances(x: Float64Array): number[] {
  const out: number[] = []
  let v1 = 1
  for (let k = 0; k < LEVELS; k++) {
    const m = 1 << k
    const a = aggregate(x, m, Math.floor(L / m))
    const mean = a.reduce((s, y) => s + y, 0) / a.length
    const v = a.reduce((s, y) => s + (y - mean) ** 2, 0) / a.length
    if (k === 0) v1 = v
    out.push(Math.log10(v / v1))
  }
  return out
}

const m = computed(() => 1 << level.value)
const bars = computed(() => ({
  poisson: aggregate(trace.value.poisson, m.value, BARS),
  selfsim: aggregate(trace.value.selfsim, m.value, BARS),
}))

// each level is drawn on mean ± 3σ of the self-similar trace at that level, as if zooming the y-axis with
// the x-axis: the self-similar trace keeps its look, the Poisson one shrinks towards the mean
const MEAN_RATE = N / 2
const SPAN = 3
const barW = PANEL.w / BARS
const lo = computed(() => MEAN_RATE - SPAN * trace.value.sd[level.value])
const barH = (v: number) => (Math.min(Math.max(v - lo.value, 0), 2 * SPAN * trace.value.sd[level.value]) / (2 * SPAN * trace.value.sd[level.value])) * PANEL.h
const MEAN_Y = PANEL.h / 2 // the mean sits mid-panel

// least-squares slope of the revealed variance-time points, and H = 1 + slope / 2
function fit(ys: number[]) {
  const pts = ys.slice(0, level.value + 1).map((y, k) => [k * Math.log10(2), y])
  if (pts.length < 3) return null
  const mx = pts.reduce((s, p) => s + p[0], 0) / pts.length
  const my = pts.reduce((s, p) => s + p[1], 0) / pts.length
  const slope = pts.reduce((s, p) => s + (p[0] - mx) * (p[1] - my), 0) / pts.reduce((s, p) => s + (p[0] - mx) ** 2, 0)
  return { slope, H: 1 + slope / 2 }
}
const fits = computed(() => ({ poisson: fit(trace.value.logVar.poisson), selfsim: fit(trace.value.logVar.selfsim) }))

const vtX = (logm: number) => VT.x + (logm / Math.log10(1 << (LEVELS - 1))) * VT.w
const vtY = (lv: number) => VT.y + ((VT_Y.top - lv) / (VT_Y.top - VT_Y.bottom)) * VT.h
const refLine = computed(() => {
  const x2 = Math.log10(1 << (LEVELS - 1))
  return { x1: vtX(0), y1: vtY(0), x2: vtX(x2), y2: vtY(-x2) }
})

let timer = 0
function play() {
  if (level.value >= LEVELS - 1) level.value = 0
  running.value = true
  timer = window.setInterval(() => {
    if (level.value >= LEVELS - 1) return pause()
    level.value++
  }, 1300)
}
function pause() {
  running.value = false
  clearInterval(timer)
}
function newTrace() {
  pause()
  seed++
  trace.value = generate()
  level.value = 0
}
onSlideLeave(pause)
onBeforeUnmount(pause)
</script>

<template>
  <div class="agg-zoom">
    <svg viewBox="0 0 880 360" role="img" aria-label="A Poisson trace and a self-similar trace aggregated over growing blocks, beside a variance-time plot that estimates the Hurst parameter">
      <g v-for="p in PANELS" :key="p.key">
        <text :x="PANEL.x" :y="p.y - 10" class="label">
          {{ p.key === 'poisson' ? 'Poisson arrivals (independent)' : `ON/OFF sources, Pareto α = ${alpha}` }}
        </text>
        <line :x1="PANEL.x" :x2="PANEL.x + PANEL.w" :y1="p.y + MEAN_Y" :y2="p.y + MEAN_Y" class="mean" />
        <rect
          v-for="(v, i) in bars[p.key]" :key="i"
          :x="PANEL.x + i * barW" :y="p.y + PANEL.h - barH(v)" :width="barW * 0.8" :height="barH(v)"
          :fill="p.key === 'poisson' ? GREY : GREEN"
        />
        <line :x1="PANEL.x" :x2="PANEL.x + PANEL.w" :y1="p.y + PANEL.h" :y2="p.y + PANEL.h" class="axis" />
        <text :x="PANEL.x - 6" :y="p.y + MEAN_Y + 4" class="tick" text-anchor="end">mean</text>
      </g>
      <text :x="PANEL.x" :y="PANELS[1].y + PANEL.h + 22" class="stats">
        each bar = mean of m = {{ m }} slot{{ m > 1 ? 's' : '' }} · window {{ (BARS * m).toLocaleString('en') }} slots
      </text>
      <text :x="PANEL.x" :y="PANELS[1].y + PANEL.h + 38" class="tick">
        y-axis at every m: mean ± 3σ of the ON/OFF trace at that m
      </text>

      <!-- variance-time plot -->
      <text :x="VT.x" :y="VT.y - 10" class="label">variance–time plot</text>
      <line :x1="VT.x" :x2="VT.x" :y1="VT.y" :y2="VT.y + VT.h" class="axis" />
      <line :x1="VT.x" :x2="VT.x + VT.w" :y1="VT.y + VT.h" :y2="VT.y + VT.h" class="axis" />
      <g v-for="k in [0, 2, 4, 6, 8]" :key="`x${k}`">
        <text :x="vtX(k * Math.log10(2))" :y="VT.y + VT.h + 14" class="tick" text-anchor="middle">{{ 1 << k }}</text>
      </g>
      <text :x="VT.x + VT.w" :y="VT.y + VT.h + 28" class="tick" text-anchor="end">m (log scale)</text>
      <g v-for="y in [0, -1, -2]" :key="`y${y}`">
        <line :x1="VT.x" :x2="VT.x + VT.w" :y1="vtY(y)" :y2="vtY(y)" class="grid" />
        <text :x="VT.x - 5" :y="vtY(y) + 4" class="tick" text-anchor="end">{{ y === 0 ? '1' : `10${y === -1 ? '⁻¹' : '⁻²'}` }}</text>
      </g>
      <line v-bind="refLine" class="ref" />
      <!-- legend for the reference line, in the empty lower-left corner -->
      <line :x1="VT.x + 10" :x2="VT.x + 34" :y1="VT.y + VT.h - 14" :y2="VT.y + VT.h - 14" class="ref" />
      <text :x="VT.x + 40" :y="VT.y + VT.h - 10" class="tick">slope −1: independent</text>
      <template v-for="key in (['poisson', 'selfsim'] as const)" :key="key">
        <circle
          v-for="k in level + 1" :key="k"
          :cx="vtX((k - 1) * Math.log10(2))" :cy="vtY(trace.logVar[key][k - 1])" r="4"
          :fill="key === 'poisson' ? GREY : GREEN"
        />
      </template>
      <text :x="VT.x - 30" :y="VT.y + VT.h + 50" class="fit" :fill="GREEN">
        self-similar: {{ fits.selfsim ? `slope ${fits.selfsim.slope.toFixed(2)} → H ≈ ${fits.selfsim.H.toFixed(2)}` : 'zoom out to fit…' }}
      </text>
      <text :x="VT.x - 30" :y="VT.y + VT.h + 66" class="fit" :fill="GREY">
        Poisson: {{ fits.poisson ? `slope ${fits.poisson.slope.toFixed(2)} → H ≈ ${fits.poisson.H.toFixed(2)}` : '' }}
      </text>
    </svg>

    <div class="sim-controls">
      <button type="button" @click="running ? pause() : play()">{{ running ? 'Pause' : level >= LEVELS - 1 ? 'Replay' : 'Zoom out' }}</button>
      <button type="button" @click="pause(); level = 0">Reset</button>
      <button type="button" @click="newTrace">New trace</button>
      <label>m <input v-model.number="level" type="range" min="0" :max="LEVELS - 1" step="1" @input="pause"> {{ m }} slot{{ m > 1 ? 's' : '' }}/bar</label>
      <span class="readout">theory for the ON/OFF trace: H = (3 − α)/2 = {{ hurstFromAlpha(alpha).toFixed(2) }}</span>
    </div>
  </div>
</template>

<style scoped>
.agg-zoom { width: 100%; }
svg { display: block; width: 100%; height: auto; font-family: var(--vsb-font-text); }
.label { font-size: 14px; fill: var(--vsb-muted); }
.stats { font-size: 13px; fill: var(--vsb-ink); font-variant-numeric: tabular-nums; }
.fit { font-size: 12px; font-weight: 700; font-variant-numeric: tabular-nums; }
.tick { font-size: 11px; fill: var(--vsb-muted); }
.axis { stroke: var(--vsb-muted); stroke-width: 1; }
.grid { stroke: var(--vsb-hairline); stroke-width: 1; }
.mean { stroke: var(--vsb-muted); stroke-width: 1; stroke-dasharray: 5 4; }
.ref { stroke: var(--vsb-muted); stroke-width: 1.2; stroke-dasharray: 6 4; }
</style>
