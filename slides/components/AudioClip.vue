<!--
  Compact play/stop button for a short audio sample, sized to sit inside a table cell.

  src    path of the clip under public/, e.g. '/audio/05/g711-alaw.wav'
  label  optional text after the icon, e.g. '32' for a bit rate

  Starting one clip stops any other that is playing, so comparisons do not overlap.
  Hard-edged and drawn in the brand green (VSB-STYLE.md R6, R24). The static PDF
  export shows the button but cannot play it — present from `npm run dev` or the build.
-->
<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'

const props = defineProps<{ src: string, label?: string }>()
const playing = ref(false)
let audio: HTMLAudioElement | null = null

function stop() {
  if (!audio) return
  audio.pause()
  audio.currentTime = 0
  playing.value = false
}

function onOtherPlay(event: Event) {
  if ((event as CustomEvent<HTMLAudioElement>).detail !== audio) stop()
}

function toggle() {
  if (playing.value) return stop()
  if (!audio) {
    audio = new Audio(props.src)
    audio.addEventListener('ended', () => { playing.value = false })
  }
  window.dispatchEvent(new CustomEvent('audio-clip-play', { detail: audio }))
  audio.currentTime = 0
  audio.play()
  playing.value = true
}

window.addEventListener('audio-clip-play', onOtherPlay)
onBeforeUnmount(() => {
  window.removeEventListener('audio-clip-play', onOtherPlay)
  stop()
})
</script>

<template>
  <button
    type="button"
    class="audio-clip"
    :class="{ playing }"
    :aria-label="`${playing ? 'Stop' : 'Play'} ${label ?? 'sample'}`"
    @click.stop="toggle"
  >
    <span aria-hidden="true">{{ playing ? '■' : '▶' }}</span>
    <span v-if="label">{{ label }}</span>
  </button>
</template>

<style scoped>
.audio-clip {
  display: inline-flex;
  align-items: center;
  gap: 0.3em;
  margin: 0 0.25em 0.15em 0;
  padding: 0.05em 0.45em;
  border: 1.5px solid var(--vsb-green);
  border-radius: 0;
  background: transparent;
  color: var(--vsb-green-text);
  font: inherit;
  font-size: 0.85em;
  line-height: 1.4;
  cursor: pointer;
}
.audio-clip:hover,
.audio-clip.playing {
  background: #005F58;  /* white on the darkened green is 7.56:1; on #00A499 only 3.10 (R5) */
  border-color: #005F58;
  color: #FFFFFF;
}
</style>
