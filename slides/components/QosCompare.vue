<!--
  The scaling slide of lecture 08: the same path as RSVP/IntServ (left) and DiffServ (right), two
  compact QosPathSim instances driven by one flows slider (0…max). Both bottlenecks get 1000 Mbit/s so
  that nothing is refused and the comparison is about state alone. Each instance draws at its native
  880 px viewBox, scaled down to its column (~430 px) by the SVG itself. The EF policer at DiffServ's
  E1 (the SLA) is raised to the same 1000 Mbit/s, else 100 voice flows would be policed there. Under
  each instance two lines at
  slide size:
    state in the core   entries summed over C1, C2, C3: RSVP 3 × (path + resv) per signalled
                        (voice / video) flow, DiffServ 3 × 4 class queues however many flows run;
    refresh messages    RSVP: PATH + RESV per reserved flow every 30 s in a real network; DiffServ: 0.
  One control row (Play / Pause, Reset, flows) drives both; the instances hide their own.

  max         upper end of the flows slider (default 200)

  Print mode (useNav().isPrintMode): both frames with PRINT_FLOWS flows, no controls.
-->
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useNav } from '@slidev/client'
import QosPathSim from './QosPathSim.vue'

const props = withDefaults(defineProps<{ max?: number }>(), { max: 200 })

const { isPrintMode } = useNav()
const PRINT_FLOWS = 50
/** Mbit/s of both bottlenecks: far above any flow mix the slider can make, so no RESV is refused. */
const CAP = 1000

const flows = ref(isPrintMode.value ? PRINT_FLOWS : Math.min(10, props.max))

type Sim = InstanceType<typeof QosPathSim>
const rsvp = ref<Sim>()
const ds = ref<Sim>()
const sims = () => [rsvp.value, ds.value].filter((s): s is Sim => !!s)

const running = computed(() => !!rsvp.value?.running)
function toggle(): void {
  const play = !running.value
  for (const s of sims()) play ? s.play() : s.pause()
}
function reset(): void {
  for (const s of sims()) s.reset()
}

/** As QosPathSim's own footer writes it, so the two numbers agree. */
const fmtRate = (r: number) => (r === 0 ? '0' : r < 10 ? r.toFixed(2) : r.toFixed(0))
const columns = computed(() => [
  {
    key: 'rsvp',
    title: 'IntServ / RSVP: per-flow state',
    core: rsvp.value?.coreStateTotal() ?? 0,
    refresh: `${fmtRate(rsvp.value?.refreshRate() ?? 0)} /s`,
  },
  {
    key: 'diffserv',
    title: 'DiffServ: per-class state',
    core: ds.value?.coreStateTotal() ?? 0,
    refresh: '0 /s (nothing to refresh)',
  },
])
</script>

<template>
  <div class="qos-compare">
    <div class="columns">
      <div class="column">
        <p class="title">{{ columns[0].title }}</p>
        <QosPathSim
          ref="rsvp" mode="rsvp" compact :controls="false"
          :flows="flows" :capacity-a="CAP" :capacity-b="CAP"
        />
        <p class="line">state in the core: <strong>{{ columns[0].core }}</strong> {{ columns[0].core === 1 ? 'entry' : 'entries' }}</p>
        <p class="line">refresh messages: <strong>{{ columns[0].refresh }}</strong></p>
      </div>
      <div class="column">
        <p class="title">{{ columns[1].title }}</p>
        <QosPathSim
          ref="ds" mode="diffserv" compact :controls="false"
          :flows="flows" :capacity-a="CAP" :capacity-b="CAP" :ef-police="CAP"
        />
        <p class="line">state in the core: <strong>{{ columns[1].core }}</strong> {{ columns[1].core === 1 ? 'entry' : 'entries' }}</p>
        <p class="line">refresh messages: <strong>{{ columns[1].refresh }}</strong></p>
      </div>
    </div>

    <div v-if="!isPrintMode" class="controls">
      <button type="button" @click="toggle">{{ running ? 'Pause' : 'Play' }}</button>
      <button type="button" @click="reset">Reset</button>
      <label>flows <input v-model.number="flows" type="range" min="0" :max="max" step="1"> <span class="n">{{ flows }}</span></label>
      <span class="note">both bottlenecks {{ CAP }} Mbit/s: nothing is refused, only the state differs</span>
    </div>
    <p v-else class="line">{{ flows }} flows, both bottlenecks {{ CAP }} Mbit/s: nothing is refused, only the state differs</p>
  </div>
</template>

<style scoped>
.qos-compare { width: 100%; color: var(--vsb-ink); }
.columns { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.column { min-width: 0; }
.title { margin: 0 0 0.2rem; font-size: 18px; font-weight: 700; color: var(--vsb-green-text); }
.line { margin: 0.15rem 0 0; font-size: 16px; font-variant-numeric: tabular-nums; }
.line strong { color: var(--vsb-ink); }
.controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4em 0.9em;
  margin-top: 0.8rem;
  font-size: 16px;
}
.controls label { display: inline-flex; align-items: center; gap: 0.35em; }
.controls input[type='range'] { width: 220px; accent-color: var(--vsb-green); }
.controls .n { display: inline-block; min-width: 2.2em; font-variant-numeric: tabular-nums; }
.controls .note { color: var(--vsb-muted); }
.controls button {
  padding: 0.05em 0.7em;
  border: 1.5px solid var(--vsb-green);
  border-radius: 0; /* R24 — hard edges */
  background: transparent;
  color: var(--vsb-green-text);
  font: inherit;
  cursor: pointer;
}
.controls button:hover { background: var(--vsb-green-dark); border-color: var(--vsb-green-dark); color: var(--vsb-bg); }
</style>
