import { test } from 'node:test'
import assert from 'node:assert/strict'
import { DSCP, dscpName, queueOf } from './qos-diffserv.ts'
import { CLASS_COLOUR, colourKey, colourKeyOfName } from './qos-dscp-colour.ts'

test('every AF4x / AF3x drop precedence and EF have their own colour, the rest is best effort', () => {
  assert.equal(colourKey(DSCP.EF), 'ef')
  assert.deepEqual([DSCP.AF41, DSCP.AF42, DSCP.AF43].map(colourKey), ['af41', 'af42', 'af43'])
  assert.deepEqual([DSCP.AF31, DSCP.AF32, DSCP.AF33].map(colourKey), ['af31', 'af32', 'af33'])
  for (const d of [DSCP.CS0, DSCP.LE, DSCP.AF11, DSCP.CS5, DSCP.VA]) assert.equal(colourKey(d), 'be')
})

test('names from dscpName map to the same colour as their DSCP', () => {
  for (const d of [0, 46, 34, 36, 38, 26, 28, 30, 10]) assert.equal(colourKeyOfName(dscpName(d)), colourKey(d))
})

test('a queue class is drawn in the colour of its lowest drop precedence', () => {
  for (const d of [DSCP.EF, DSCP.AF41, DSCP.AF31, DSCP.CS0]) assert.equal(CLASS_COLOUR[queueOf(d)], colourKey(d))
})
