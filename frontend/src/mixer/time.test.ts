import { describe, expect, it } from 'vitest'
import { formatTime } from './time'

describe('formatTime', () => {
  it.each([
    [0, '0:00'],
    [5.9, '0:05'],
    [65.4, '1:05'],
    [600, '10:00'],
    [Number.NaN, '0:00'],
  ])('formats %s seconds as %s', (seconds, expected) => {
    expect(formatTime(seconds)).toBe(expected)
  })
})
