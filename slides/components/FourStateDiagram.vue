<!--
  Four-state Markov packet-loss model, drawn in the same style as GilbertSim's diagrams
  (grey arrows, italic labels, states outlined green for "transmit" and red for "loss").

  States in a row: 4 (isolated loss) – 1 (gap, received) – 3 (burst, lost) – 2 (burst, received).
  Arcs along the top run rightwards, along the bottom leftwards; self-loops on 1, 3 and 2 sit on top,
  clockwise. State 4 has no self-loop: it always returns to 1 (p41 = 1).

  alt   accessible description of the figure
-->
<script setup lang="ts">
import { useId } from 'vue'

defineProps<{ alt?: string }>()

const uid = useId()
const GREEN = 'var(--vsb-green)'
const RED = '#E4002B' // FMT red, the "loss" state colour (VSB-STYLE.md §9)

const Y = 112
const R = 19
const X = { 4: 60, 1: 140, 3: 220, 2: 300 } as const
const NODES = [
  { id: 4, kind: 'L' },
  { id: 1, kind: 'T' },
  { id: 3, kind: 'L' },
  { id: 2, kind: 'T' },
] as const

// neighbour arcs: top ones left -> right, bottom ones right -> left
const top = (a: number, b: number) => `M${a + 15},${Y - 16} Q${(a + b) / 2},${Y - 34} ${b - 15},${Y - 16}`
const bottom = (a: number, b: number) => `M${b - 15},${Y + 16} Q${(a + b) / 2},${Y + 34} ${a + 15},${Y + 16}`
const loop = (x: number) => `M${x - 7},${Y - 18} C${x - 24},${Y - 54} ${x + 24},${Y - 54} ${x + 7},${Y - 18}`

const EDGES = [
  { d: top(X[4], X[1]), label: 'p₄₁ = 1', lx: (X[4] + X[1]) / 2, ly: Y - 36 },
  { d: top(X[1], X[3]), label: 'p₁₃', lx: (X[1] + X[3]) / 2, ly: Y - 36 },
  { d: top(X[3], X[2]), label: 'p₃₂', lx: (X[3] + X[2]) / 2, ly: Y - 36 },
  { d: bottom(X[4], X[1]), label: 'p₁₄', lx: (X[4] + X[1]) / 2, ly: Y + 48 },
  { d: bottom(X[1], X[3]), label: 'p₃₁', lx: (X[1] + X[3]) / 2, ly: Y + 48 },
  { d: bottom(X[3], X[2]), label: 'p₂₃', lx: (X[3] + X[2]) / 2, ly: Y + 48 },
  { d: loop(X[1]), label: 'p₁₁', lx: X[1], ly: Y - 50 },
  { d: loop(X[3]), label: 'p₃₃', lx: X[3], ly: Y - 50 },
  { d: loop(X[2]), label: 'p₂₂', lx: X[2], ly: Y - 50 },
]
</script>

<template>
  <div class="four-state">
    <svg viewBox="30 46 300 124" role="img" :aria-label="alt ?? 'Four-state packet-loss model'">
      <defs>
        <marker :id="`fs-arrow-${uid}`" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" class="arrow-head" />
        </marker>
      </defs>
      <g v-for="e in EDGES" :key="e.label">
        <path :d="e.d" class="edge" :marker-end="`url(#fs-arrow-${uid})`" />
        <text :x="e.lx" :y="e.ly" class="edge-label" text-anchor="middle">{{ e.label }}</text>
      </g>
      <g v-for="n in NODES" :key="n.id">
        <circle :cx="X[n.id]" :cy="Y" :r="R" fill="var(--vsb-bg)" :stroke="n.kind === 'T' ? GREEN : RED" stroke-width="2" />
        <text :x="X[n.id]" :y="Y + 6" text-anchor="middle" class="state">{{ n.id }}</text>
        <text :x="X[n.id]" :y="Y + 32" text-anchor="middle" class="kind">{{ n.kind }}</text>
      </g>
    </svg>
  </div>
</template>

<style scoped>
/* a little smaller than GilbertSim's diagram scale, so the slide keeps room for its paragraph */
.four-state { width: 580px; margin: 0.2rem auto 0; }
svg { display: block; width: 100%; height: auto; font-family: var(--vsb-font-text); }
.edge { fill: none; stroke: var(--vsb-muted); stroke-width: 1.5; }
.arrow-head { fill: var(--vsb-muted); }
.edge-label { font-size: 13px; fill: var(--vsb-ink); font-style: italic; }
.state { font-size: 17px; font-weight: 700; fill: var(--vsb-ink); }
.kind { font-size: 10px; fill: var(--vsb-muted); }
</style>
