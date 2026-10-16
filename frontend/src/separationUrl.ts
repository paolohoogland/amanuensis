const PARAM = 'separation'

export function readSeparationId(): string | null {
  return new URLSearchParams(window.location.search).get(PARAM)
}

export function writeSeparationId(id: string) {
  const url = new URL(window.location.href)
  url.searchParams.set(PARAM, id)
  window.history.replaceState(null, '', url)
}
