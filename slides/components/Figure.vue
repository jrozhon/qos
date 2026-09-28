<!--
  A lecture figure from public/figures/, in the variant that matches the deck's colour scheme.

  scripts/generate-figures.py writes every figure twice: name.svg (light, also used by the PDF export)
  and name.dark.svg (dark palette). The SVGs are shown as <img>, which page CSS cannot restyle, so the
  file itself has to be swapped when the presenter toggles dark mode (`d`).

  src    path of the light variant, e.g. '/figures/04/pareto-ccdf.svg'
  alt    description of the figure
-->
<script setup lang="ts">
import { computed } from 'vue'
import { useDarkMode } from '@slidev/client'

const props = defineProps<{ src: string, alt: string }>()
const { isDark } = useDarkMode()
const shown = computed(() => (isDark.value ? props.src.replace(/\.svg$/, '.dark.svg') : props.src))
</script>

<template>
  <img class="lecture-diagram" :src="shown" :alt="alt">
</template>
