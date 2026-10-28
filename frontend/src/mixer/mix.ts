export type Channel = {
  muted: boolean
  soloed: boolean
  volume: number
}

export type Mix = Record<string, Channel>

export function createMix(stems: string[]): Mix {
  return Object.fromEntries(stems.map((stem) => [stem, { muted: false, soloed: false, volume: 1 }]))
}

export function anySoloed(mix: Mix): boolean {
  return Object.values(mix).some((channel) => channel.soloed)
}

export function isAudible(mix: Mix, stem: string): boolean {
  return anySoloed(mix) ? mix[stem].soloed : !mix[stem].muted
}

export function toggleMute(mix: Mix, stem: string): Mix {
  return update(mix, stem, { muted: !mix[stem].muted })
}

export function toggleSolo(mix: Mix, stem: string): Mix {
  return update(mix, stem, { soloed: !mix[stem].soloed })
}

export function setVolume(mix: Mix, stem: string, volume: number): Mix {
  return update(mix, stem, { volume: Math.min(1, Math.max(0, volume)) })
}

function update(mix: Mix, stem: string, changes: Partial<Channel>): Mix {
  return { ...mix, [stem]: { ...mix[stem], ...changes } }
}
