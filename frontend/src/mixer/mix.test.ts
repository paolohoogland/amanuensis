import { describe, expect, it } from 'vitest'
import { anySoloed, createMix, isAudible, setVolume, toggleMute, toggleSolo } from './mix'

const stems = ['drums', 'bass', 'guitar']

describe('mix', () => {
  it('starts with every stem audible at full volume', () => {
    const mix = createMix(stems)

    expect(stems.every((stem) => isAudible(mix, stem))).toBe(true)
    expect(mix.guitar.volume).toBe(1)
  })

  it('silences a muted stem only', () => {
    const mix = toggleMute(createMix(stems), 'guitar')

    expect(isAudible(mix, 'guitar')).toBe(false)
    expect(isAudible(mix, 'drums')).toBe(true)
  })

  it('unmutes when toggled twice', () => {
    const mix = toggleMute(toggleMute(createMix(stems), 'guitar'), 'guitar')

    expect(isAudible(mix, 'guitar')).toBe(true)
  })

  it('plays only soloed stems', () => {
    const mix = toggleSolo(toggleSolo(createMix(stems), 'drums'), 'bass')

    expect(isAudible(mix, 'drums')).toBe(true)
    expect(isAudible(mix, 'bass')).toBe(true)
    expect(isAudible(mix, 'guitar')).toBe(false)
  })

  it('lets solo win over mute', () => {
    const mix = toggleSolo(toggleMute(createMix(stems), 'drums'), 'drums')

    expect(isAudible(mix, 'drums')).toBe(true)
  })

  it('restores mutes when the last solo is released', () => {
    const soloed = toggleSolo(toggleMute(createMix(stems), 'guitar'), 'drums')
    const mix = toggleSolo(soloed, 'drums')

    expect(isAudible(mix, 'bass')).toBe(true)
    expect(isAudible(mix, 'guitar')).toBe(false)
  })

  it('knows when any stem is soloed', () => {
    expect(anySoloed(createMix(stems))).toBe(false)
    expect(anySoloed(toggleSolo(createMix(stems), 'bass'))).toBe(true)
  })

  it('keeps volume between 0 and 1', () => {
    expect(setVolume(createMix(stems), 'bass', 0.4).bass.volume).toBe(0.4)
    expect(setVolume(createMix(stems), 'bass', 2).bass.volume).toBe(1)
    expect(setVolume(createMix(stems), 'bass', -1).bass.volume).toBe(0)
  })

  it('never changes the original mix', () => {
    const mix = createMix(stems)

    toggleMute(mix, 'drums')
    toggleSolo(mix, 'drums')
    setVolume(mix, 'drums', 0)

    expect(mix).toEqual(createMix(stems))
  })
})
