<!--
  Closing slide (R25): full-bleed green, negative logo, www.vsb.cz.

  The manual's closing slide also carries the presenter's name, phone and
  e-mail (manual 5.4). Add those in the slide body - they are not filled in
  here because inventing contact details would be worse than leaving the slot
  visibly empty.
-->
<template>
  <div class="slidev-layout end vsb-end">
    <div class="vsb-end-body">
      <slot />
    </div>

    <div class="vsb-end-foot">www.vsb.cz</div>
  </div>
</template>

<style>
.vsb-end {
  position: relative;
  height: 100%;
  display: grid;
  padding: 3.5rem !important;
  background: var(--vsb-green) !important;
  color: #fff;
}

.vsb-end-body {
  margin-top: auto;
  margin-bottom: auto;
  text-align: center;
}

.vsb-end h1 {
  color: #fff !important;
  font-size: 3.1rem;
  font-weight: 700;
  line-height: 1.1;
}
.vsb-end h1::after { content: none; }

.vsb-end :is(h2, h3, p, li, strong) { color: #fff !important; }
.vsb-end a { color: #fff !important; border-bottom-color: rgba(255, 255, 255, 0.5); }

.vsb-end-foot {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 2.2rem;
  text-align: center;
  font-size: 0.82rem;
  letter-spacing: 0.06em;
  color: #fff;
  opacity: 0.85;
}
</style>
