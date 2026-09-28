// Traffic generators shared by deck 04's self-similarity animations
// (OnOffSim, AggregationZoom, SelfSimilarQueue).
//
// Everything runs on a seeded PRNG so a run can be replayed exactly.

export type Rand = () => number
export type Tail = 'exponential' | 'pareto'

/** mulberry32: small, fast, seedable PRNG returning floats in [0, 1). */
export function mulberry32(seed: number): Rand {
  let a = seed | 0
  return () => {
    a = (a + 0x6D2B79F5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/**
 * Duration sampler with a given mean.
 * exponential: light-tailed; pareto: x_m / U^(1/alpha), finite mean for alpha > 1, infinite variance for alpha < 2.
 */
export function sampler(tail: Tail, mean: number, alpha: number, rand: Rand): () => number {
  if (tail === 'exponential') return () => -mean * Math.log(1 - rand())
  const xm = (mean * (alpha - 1)) / alpha
  return () => xm / (1 - rand()) ** (1 / alpha)
}

/** One ON/OFF source in discrete time slots. `step()` advances one slot and says whether it was ON. */
export class OnOffSource {
  on: boolean
  left: number
  draw: () => number
  constructor(draw: () => number, rand: Rand) {
    this.draw = draw
    this.on = rand() < 0.5
    this.left = Math.max(1, Math.round(draw()))
  }

  step(): boolean {
    const was = this.on
    if (--this.left <= 0) {
      this.on = !this.on
      this.left = Math.max(1, Math.round(this.draw()))
    }
    return was
  }
}

/**
 * Advance a source by `slots` slots in one go, period by period instead of slot by slot, calling `onRange`
 * for every ON stretch [start, end) (relative to the start of the call). Leaves the source exactly where
 * `slots` calls of step() would, so step() can continue from there. Cost grows with the number of periods,
 * not with the number of slots.
 */
export function advanceRanges(src: OnOffSource, slots: number, onRange?: (start: number, end: number) => void) {
  let t = 0
  while (t < slots) {
    const len = Math.min(src.left, slots - t)
    if (src.on && onRange) onRange(t, t + len)
    t += len
    src.left -= len
    if (src.left <= 0) {
      src.on = !src.on
      src.left = Math.max(1, Math.round(src.draw()))
    }
  }
}

/** Number of sources ON in each of the next `slots` slots (difference array over the ON ranges). */
export function countOn(sources: OnOffSource[], slots: number): Int32Array {
  const diff = new Int32Array(slots + 1)
  for (const s of sources) {
    advanceRanges(s, slots, (a, b) => {
      diff[a]++
      diff[b]--
    })
  }
  const out = new Int32Array(slots)
  let run = 0
  for (let t = 0; t < slots; t++) {
    run += diff[t]
    out[t] = run
  }
  return out
}

export function makeSources(n: number, tail: Tail, mean: number, alpha: number, rand: Rand): OnOffSource[] {
  const draw = sampler(tail, mean, alpha, rand)
  return Array.from({ length: n }, () => new OnOffSource(draw, rand))
}

/** Poisson-distributed count with mean lambda (Knuth; fine for the small means used here). */
export function poisson(lambda: number, rand: Rand): number {
  const limit = Math.exp(-lambda)
  let k = 0
  let prod = rand()
  while (prod > limit) {
    k++
    prod *= rand()
  }
  return k
}

/** Hurst parameter of the aggregate of ON/OFF sources with Pareto periods (Taqqu et al.): H = (3 - alpha) / 2. */
export const hurstFromAlpha = (alpha: number) => (3 - alpha) / 2
