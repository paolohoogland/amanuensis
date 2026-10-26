import { useState, type FormEvent } from 'react'
import { isFinished, type SeparationApi } from './api'
import { Mixer } from './mixer/Mixer'
import { useSeparation } from './useSeparation'

type Props = {
  api: SeparationApi
  pollIntervalMs?: number
}

export default function App({ api, pollIntervalMs = 1000 }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const { separation, error, upload } = useSeparation(api, pollIntervalMs)
  const busy = separation !== null && !isFinished(separation.status)

  function submit(event: FormEvent) {
    event.preventDefault()
    if (file) {
      upload(file)
    }
  }

  return (
    <main>
      <h1>Amanuensis</h1>
      <form onSubmit={submit}>
        <label>
          Song
          <input
            type="file"
            accept="audio/*"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <button type="submit" disabled={!file || busy}>
          Separate
        </button>
      </form>
      {separation && <p role="status">Status: {separation.status}</p>}
      {(error ?? separation?.error) && <p role="alert">{error ?? separation?.error}</p>}
      {separation?.status === 'done' && (
        <Mixer
          key={separation.id}
          tracks={separation.stems.map((stem) => ({
            name: stem,
            url: api.stemUrl(separation.id, stem),
          }))}
          background={
            separation.background ? api.stemUrl(separation.id, separation.background) : undefined
          }
        />
      )}
    </main>
  )
}
