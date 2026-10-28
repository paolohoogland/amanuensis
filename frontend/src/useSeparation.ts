import { useEffect, useState } from 'react'
import { isFinished, type Separation, type SeparationApi } from './api'
import { readSeparationId, writeSeparationId } from './separationUrl'

export function useSeparation(api: SeparationApi, pollIntervalMs: number) {
  const [separation, setSeparation] = useState<Separation | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fail = (reason: Error) => setError(reason.message)

  useEffect(() => {
    const id = readSeparationId()
    if (id !== null) {
      api.get(id).then(setSeparation, fail)
    }
  }, [api])

  useEffect(() => {
    if (separation === null || isFinished(separation.status)) {
      return
    }
    const timer = setTimeout(() => {
      api.get(separation.id).then(setSeparation, fail)
    }, pollIntervalMs)
    return () => clearTimeout(timer)
  }, [api, pollIntervalMs, separation])

  async function upload(file: File) {
    setError(null)
    setSeparation(null)
    try {
      const started = await api.upload(file)
      writeSeparationId(started.id)
      setSeparation(started)
    } catch (reason) {
      fail(reason as Error)
    }
  }

  return { separation, error, upload }
}
