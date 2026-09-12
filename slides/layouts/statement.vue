<!--
  Thesis slide: white ground, oversized green statement. Deliberately NOT
  full-bleed green so it stays distinct from the section dividers (R22).
-->
<template>
  <div class="slidev-layout statement vsb-statement">
    <div class="my-auto">
      <div class="vsb-rule vsb-statement-rule" />
      <slot />
    </div>
  </div>
</template>

<style>
.vsb-statement {
  display: grid;
  height: 100%;
  padding: 3.5rem !important;
  text-align: left !important;
}

.vsb-statement-rule { width: 4.5rem; margin-bottom: 1.4rem; }

.slidev-layout.vsb-statement h1 {
  font-size: 2.9rem;
  line-height: 1.12;
  font-weight: 700;
  color: var(--vsb-green) !important;
  margin-bottom: 0.9rem;
  max-width: 92%;
}
.vsb-statement h1::after { content: none; }

.vsb-statement h2 {
  font-size: 1.5rem;
  font-weight: 400;
  line-height: 1.35;
  color: var(--vsb-muted) !important;
  max-width: 88%;
}
</style>
