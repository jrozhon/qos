<!--
  VŠB-TUO logo.

  level    'i'     VSB - Technical University of Ostrava. Aspect 2.73:1 (default)
           'full'  I+II+III lockup, ...Faculty of Electrical Engineering...
                   Department of Telecommunications. Aspect 5.97:1

  variant  'color' white or <=30% tint backgrounds   (manual 1.5)
           'white' backgrounds darker than 80% tint  (manual 1.5)
           'black' achromatic reproduction           (manual 1.6)

  Minimum height is 8 mm for the EN mark (manual 1.9). Slidev exports this deck
  at 735 pt = 259 mm wide for a 980 px canvas, i.e. 3.78 px/mm, so 8 mm is
  30.2 px. 31 px is the floor and the prop is clamped to it. Height drives width.
-->
<script setup lang="ts">
const props = withDefaults(defineProps<{
  level?: 'i' | 'full'
  variant?: 'color' | 'white' | 'black'
  height?: number
}>(), {
  level: 'i',
  variant: 'color',
  height: 72,
})

const stem = props.level === 'full' ? '/logo' : '/logo-lvl1'
const suffix = { color: '', white: '-white', black: '-black' }[props.variant]
const src = `${stem}${suffix}.svg`

const alt = props.level === 'full'
  ? 'VSB - Technical University of Ostrava, Faculty of Electrical Engineering and Computer Science, Department of Telecommunications'
  : 'VSB - Technical University of Ostrava'
</script>

<template>
  <img
    :src="src"
    :style="{ height: `${Math.max(height, 31)}px` }"
    class="vsb-logo"
    :alt="alt"
  >
</template>
