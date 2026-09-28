<!--
  Why self-similarity matters for capacity planning: two identical switch ports (capacity c packets per
  slot, buffer B packets) at the same mean load rho, one fed by Poisson arrivals, one by the aggregate of
  N ON/OFF sources with Pareto periods (same mean rate). Top: arrivals per slot against the capacity;
  bottom: buffer occupancy against the buffer size, with losses marked.

  rho    offered load, mean arrivals / capacity  (default 0.8)
  buffer buffer size [packets]                   (default 100)
  alpha  Pareto shape of the ON/OFF periods      (default 1.4)

  Browser only: its slide carries `class: export-skip` (see style.css and slides/README.md).
-->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, shallowRef } from 'vue'
import { onSlideLeave } from '@slidev/client'
import { makeSources, mulberry32, type OnOffSource, poisson, type Rand } from '../utils/traffic'

const props = withDefaults(defineProps<{ rho?: number, buffer?: number, alpha?: number, seed?: number }>(),
  { rho: 0.8, buffer: 100, alpha: 1.4, seed: 5 })

const C = 10 // capacity [packets per slot]
const N = 8 // ON/OFF sources: a few heavy users, each sending 2λ/N while ON
const MEAN = 40 // mean ON/OFF period [slots]
const W = 300 // slots on screen
const COLS = [{ x: 50, key: 'poisson' }, { x: 490, key: 'selfsim' }] as const
const CW = 370
const ARR = { y: 34, h: 100 }
const Q = { y: 178, h: 110 }
const ARR_MAX = 2.2 * C
const RED = '#E4002B'

const rho = ref(props.rho)
const buffer = ref(props.buffer)
const rate = ref(150) // slots per second
const running = ref(false)

type Key = 'poisson' | 'selfsim'
// drops: slot numbers in which packets were lost (within the window)
interface Port { q: number, arrived: number, lost: number, maxQ: number, arr: number[], occ: number[], drops: number[] }
const newPort = (): Port => ({ q: 0, arrived: 0, lost: 0, maxQ: 0, arr: [], occ: [], drops: [] })
const ports = shallowRef<Record<Key, Port>>({ poisson: newPort(), selfsim: newPort() })

let seed = props.seed
let rand: Rand
let sources: OnOffSource[]
let t = 0 // slots simulated so far
const slots = ref(0)
function init() {
  rand = mulberry32(seed)
  sources = makeSources(N, 'pareto', MEAN, props.alpha, rand)
  for (let i = 0; i < 5000; i++) sources.forEach(s => s.step())
  t = 0
  slots.value = 0
  ports.value = { poisson: newPort(), selfsim: newPort() }
}
init()

// one slot: arrivals join the queue, the port sends up to C packets, the overflow beyond the buffer is lost
function serve(p: Port, a: number, now: number) {
  p.arrived += a
  let q = Math.max(0, p.q + a - C)
  const over = Math.max(0, q - buffer.value)
  q -= over
  p.lost += over
  p.q = q
  p.maxQ = Math.max(p.maxQ, q)
  for (const [arr, v] of [[p.arr, a], [p.occ, q]] as const) {
    arr.push(v)
    if (arr.length > W) arr.shift()
  }
  p.drops = p.drops.filter(s => s > now - W)
  if (over > 0) p.drops.push(now)
}

function slot() {
  const lambda = rho.value * C
  let on = 0
  for (const s of sources) if (s.step()) on++
  serve(ports.value.poisson, poisson(lambda, rand), t)
  serve(ports.value.selfsim, (2 * lambda / N) * on, t) // each ON source sends 2λ/N per slot: mean λ
  t++
}

let frame = 0
let last = 0
let acc = 0
function loop(now: number) {
  acc += Math.min(0.1, (now - last) / 1000) * rate.value
  last = now
  if (acc >= 1) {
    while (acc >= 1) {
      acc -= 1
      slot()
    }
    ports.value = { ...ports.value } // redraw
    slots.value = t
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
function reset() {
  pause()
  seed++
  init()
}
onSlideLeave(pause)
onBeforeUnmount(pause)

const px = CW / W
const arrY = (v: number) => ARR.y + ARR.h - (Math.min(v, ARR_MAX) / ARR_MAX) * ARR.h
const qY = (v: number) => Q.y + Q.h - (v / buffer.value) * Q.h
const lines = computed(() => {
  const out = {} as Record<Key, { arr: string, occ: string, area: string, drops: number[], loss: number, maxQ: number }>
  for (const { key, x } of COLS) {
    const p = ports.value[key]
    const arr = p.arr.map((v, i) => `${(x + i * px).toFixed(1)},${arrY(v).toFixed(1)}`).join(' ')
    const occ = p.occ.map((v, i) => `${(x + i * px).toFixed(1)},${qY(v).toFixed(1)}`).join(' ')
    const area = p.occ.length ? `${x},${Q.y + Q.h} ${occ} ${(x + (p.occ.length - 1) * px).toFixed(1)},${Q.y + Q.h}` : ''
    out[key] = { arr, occ, area, drops: p.drops.map(s => x + (s - (t - p.occ.length)) * px), loss: p.arrived ? (100 * p.lost) / p.arrived : 0, maxQ: p.maxQ }
  }
  return out
})
</script>

<template>
  <div class="ss-queue">
    <svg viewBox="0 0 880 360" role="img" aria-label="Two switch ports at the same load, one fed by Poisson arrivals and one by self-similar traffic, with their arrivals and buffer occupancy over time">
      <g v-for="col in COLS" :key="col.key">
        <text :x="col.x" :y="ARR.y - 12" class="label">
          {{ col.key === 'poisson' ? 'Poisson arrivals' : `self-similar arrivals (${N} ON/OFF sources, Pareto α = ${alpha})` }}
        </text>
        <!-- arrivals per slot vs capacity -->
        <line :x1="col.x" :x2="col.x" :y1="ARR.y" :y2="ARR.y + ARR.h" class="axis" />
        <line :x1="col.x" :x2="col.x + CW" :y1="ARR.y + ARR.h" :y2="ARR.y + ARR.h" class="axis" />
        <polyline :points="lines[col.key].arr" :class="['arr', col.key]" />
        <line :x1="col.x" :x2="col.x + CW" :y1="arrY(C)" :y2="arrY(C)" class="cap" />
        <line :x1="col.x" :x2="col.x + CW" :y1="arrY(rho * C)" :y2="arrY(rho * C)" class="mean" />
        <text :x="col.x - 5" :y="arrY(rho * C) + 4" class="tick" text-anchor="end">λ</text>
        <text :x="col.x - 5" :y="arrY(C) + 4" class="tick" text-anchor="end">c</text>
        <text :x="col.x" :y="ARR.y + ARR.h + 14" class="tick">arrivals per slot [packets]</text>
        <text :x="col.x" :y="ARR.y + ARR.h + 27" class="tick">
          dashed c = {{ C }} (capacity) · dotted λ = ρ·c = {{ +(rho * C).toFixed(1) }} (mean arrivals), both packets/slot
        </text>

        <!-- buffer occupancy vs buffer size, losses marked -->
        <line :x1="col.x" :x2="col.x" :y1="Q.y" :y2="Q.y + Q.h" class="axis" />
        <line :x1="col.x" :x2="col.x + CW" :y1="Q.y + Q.h" :y2="Q.y + Q.h" class="axis" />
        <line :x1="col.x" :x2="col.x + CW" :y1="Q.y" :y2="Q.y" class="cap" />
        <text :x="col.x + CW" :y="Q.y - 4" class="tick" text-anchor="end">buffer B = {{ buffer }} packets</text>
        <polygon v-if="lines[col.key].area" :points="lines[col.key].area" class="occ-area" />
        <polyline :points="lines[col.key].occ" class="occ" />
        <path v-for="(d, i) in lines[col.key].drops" :key="i" :d="`M${d},${Q.y - 2} v8`" class="drop" />
        <text :x="col.x" :y="Q.y + Q.h + 14" class="tick">buffer occupancy [packets]</text>

        <text :x="col.x" :y="Q.y + Q.h + 40" class="stats">
          loss <tspan :fill="lines[col.key].loss > 0 ? RED : 'currentColor'" font-weight="700">{{ lines[col.key].loss.toFixed(2) }} %</tspan>
          · max queue {{ Math.round(lines[col.key].maxQ) }} of {{ buffer }} packets
        </text>
      </g>
    </svg>

    <div class="sim-controls">
      <button type="button" @click="running ? pause() : play()">{{ running ? 'Pause' : 'Play' }}</button>
      <button type="button" @click="reset">Reset</button>
      <label>load ρ <input v-model.number="rho" type="range" min="0.5" max="0.95" step="0.05"> {{ rho.toFixed(2) }}</label>
      <label>buffer <input v-model.number="buffer" type="range" min="20" max="400" step="10"> {{ buffer }} packets</label>
      <label>speed <input v-model.number="rate" type="range" min="20" max="300" step="10"> {{ rate }} slots/s</label>
      <span class="readout">time {{ slots.toLocaleString('en') }} slots</span>
    </div>
  </div>
</template>

<style scoped>
.ss-queue { width: 100%; }
svg { display: block; width: 100%; height: auto; font-family: var(--vsb-font-text); }
.label { font-size: 14px; fill: var(--vsb-muted); }
.stats { font-size: 13px; fill: var(--vsb-ink); font-variant-numeric: tabular-nums; }
.tick { font-size: 11px; fill: var(--vsb-muted); }
.axis { stroke: var(--vsb-muted); stroke-width: 1; }
.cap { stroke: var(--vsb-ink); stroke-width: 1.2; stroke-dasharray: 6 4; }
.mean { stroke: var(--vsb-muted); stroke-width: 1; stroke-dasharray: 2 3; }
.arr { fill: none; stroke-width: 1.2; }
.arr.poisson { stroke: var(--vsb-muted); }
.arr.selfsim { stroke: var(--vsb-green); }
.occ { fill: none; stroke: var(--vsb-green-dark); stroke-width: 1.5; }
.occ-area { fill: var(--vsb-green); fill-opacity: 0.18; }
.drop { stroke: #E4002B; stroke-width: 2; }
</style>
