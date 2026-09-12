<!--
  Section divider: full-bleed university green with the negative logo (R22).
  This is the deck's main rhythm device. Manual 1.5 requires the negative
  logo on backgrounds darker than an 80% tint — a 100% fill qualifies.
-->
<template>
  <div class="slidev-layout section vsb-section">
    <div class="vsb-section-body">
      <slot />
    </div>

    <!-- R1: the faculty accent appears against the university green -->
    <div class="vsb-section-accent" />
  </div>
</template>

<style>
.vsb-section {
  position: relative;
  height: 100%;
  background: var(--vsb-green) !important;
  color: #fff;
  display: grid;
  padding: 3.5rem !important;
  overflow: hidden;
}

.vsb-section-body {
  margin-top: auto;
  margin-bottom: auto;
  max-width: 80%;
}

/* White on #00A499 is 3.10:1 — AA for large text only, so keep these big (R5) */
.vsb-section h1 {
  color: #fff !important;
  font-size: 3.1rem !important;
  line-height: 1.08 !important;
  font-weight: 700 !important;
  margin-bottom: 0.6rem;
}
.vsb-section h1::after { content: none; }

.vsb-section h2 {
  color: #fff !important;
  font-size: 1.65rem !important;
  font-weight: 400 !important;
  line-height: 1.3 !important;
}

.vsb-section :is(p, li, strong, a) { color: #fff !important; }

/* Faculty colour as a fill, never as text (R5) */
.vsb-section-accent {
  position: absolute;
  left: 3.5rem;
  bottom: 2.6rem;
  width: 5.5rem;
  height: 5px;
  background: var(--vsb-fei);
}
</style>
