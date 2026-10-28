export type Status = 'queued' | 'running' | 'done' | 'failed'

export type Separation = {
  id: string
  status: Status
  stems: string[]
  error: string | null
}

export type SeparationApi = {
  upload(file: File): Promise<Separation>
  get(id: string): Promise<Separation>
  stemUrl(id: string, stem: string): string
}

export function isFinished(status: Status): boolean {
  return status === 'done' || status === 'failed'
}

export function createHttpApi(fetcher: typeof fetch = fetch): SeparationApi {
  async function json(response: Promise<Response>): Promise<Separation> {
    const resolved = await response
    if (!resolved.ok) {
      throw new Error(`Request failed: ${resolved.status}`)
    }
    return resolved.json()
  }

  return {
    upload(file) {
      const body = new FormData()
      body.append('file', file)
      return json(fetcher('/separations', { method: 'POST', body }))
    },
    get(id) {
      return json(fetcher(`/separations/${id}`))
    },
    stemUrl(id, stem) {
      return `/separations/${id}/stems/${stem}`
    },
  }
}
