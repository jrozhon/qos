<!--
  Title slide (R20): logo lockup, generous white space, www.vsb.cz at the foot.
  Mirrors the official PowerPoint title slide, manual 5.4.
-->
<template>
  <div class="slidev-layout cover vsb-cover">
    <div class="vsb-cover-body">
      <VsbLogo variant="color" :height="76" />
      <div class="vsb-rule vsb-cover-rule" />
      <slot />
    </div>

    <div class="vsb-cover-foot">
      <span>www.vsb.cz</span>
      <span class="vsb-rule vsb-cover-accent" />
    </div>
  </div>
</template>

<style>
.vsb-cover {
  position: relative;
  height: 100%;
  display: grid;
  padding: 3.5rem !important;
  text-align: left !important;
  background: var(--vsb-bg);
}

.vsb-cover-body { margin-top: auto; margin-bottom: auto; }

.vsb-cover-rule { width: 4.5rem; margin: 2.2rem 0 1.6rem; }

.slidev-layout.vsb-cover h1 {
  font-size: 3.2rem;
  line-height: 1.08;
  font-weight: 700;
  color: var(--vsb-green) !important;
  margin-bottom: 0.7rem;
}
.vsb-cover h1::after { content: none; }

.vsb-cover h2,
.vsb-cover h3 {
  font-size: 1.5rem;
  font-weight: 400;
  color: var(--vsb-ink) !important;
  line-height: 1.35;
}

.vsb-cover-foot {
  position: absolute;
  left: 3.5rem;
  right: 3.5rem;
  bottom: 2.2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.82rem;
  letter-spacing: 0.06em;
  color: var(--vsb-green-text);
}

/* Both rules on the cover are university green. They are the same kind of
   element - a brand keyline - so giving them two different colours read as an
   accident rather than a distinction. */
.vsb-cover-accent { flex: 1; }
</style>
