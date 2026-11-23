// Colours of DSCP marks in the lecture 08 components (QosPathSim, QosDiffServLayer).
// Each key names a CSS variable --qp-<key> defined in QosPathSim.vue for light and dark mode:
// EF in the green family, AF4x in EKF blue and AF3x in dark green, three tints each by drop
// precedence (lighter = dropped first), BE (DSCP 0, also unmarked) in the muted grey.

import { DSCP, type QueueClass } from './qos-diffserv.ts'

export type ColourKey = 'ef' | 'af41' | 'af42' | 'af43' | 'af31' | 'af32' | 'af33' | 'be'
export const COLOUR_KEYS: readonly ColourKey[] = ['ef', 'af41', 'af42', 'af43', 'af31', 'af32', 'af33', 'be']

const BY_DSCP = new Map<number, ColourKey>([
  [DSCP.EF, 'ef'], [DSCP.AF41, 'af41'], [DSCP.AF42, 'af42'], [DSCP.AF43, 'af43'],
  [DSCP.AF31, 'af31'], [DSCP.AF32, 'af32'], [DSCP.AF33, 'af33'],
])

/** Colour key of a DSCP; anything without its own colour (CS0, LE, other classes) is drawn as best effort. */
export function colourKey(dscp: number): ColourKey {
  return BY_DSCP.get(dscp) ?? 'be'
}

/** Colour key of a DSCP name as dscpName() writes it ('EF', 'AF42', 'BE', …). */
export function colourKeyOfName(name: string): ColourKey {
  const d = (DSCP as Record<string, number>)[name]
  return d === undefined ? 'be' : colourKey(d)
}

/** Colour key of a queue class: the class's lowest drop precedence. */
export const CLASS_COLOUR: Record<QueueClass, ColourKey> = { EF: 'ef', AF4: 'af41', AF3: 'af31', BE: 'be' }

export const colourVar = (k: ColourKey): string => `var(--qp-${k})`
