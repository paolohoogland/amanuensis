import { describe, expect, it, vi } from 'vitest'
import { createHttpApi, type Separation } from './api'

const separation: Separation = {
  id: 'abc',
  status: 'queued',
  stems: [],
  background: null,
  error: null,
}

function respondingWith(body: unknown, status = 200) {
  return vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify(body), { status }))
}

describe('createHttpApi', () => {
  it('uploads the file as multipart form data', async () => {
    const fetcher = respondingWith(separation, 202)
    const file = new File(['audio'], 'song.mp3')

    const result = await createHttpApi(fetcher).upload(file)

    const [url, init] = fetcher.mock.calls[0]
    expect(url).toBe('/separations')
    expect(init).toMatchObject({ method: 'POST' })
    expect((init as RequestInit).body).toBeInstanceOf(FormData)
    expect(((init as RequestInit).body as FormData).get('file')).toBe(file)
    expect(result).toEqual(separation)
  })

  it('fetches a separation by id', async () => {
    const fetcher = respondingWith(separation)

    const result = await createHttpApi(fetcher).get('abc')

    expect(fetcher).toHaveBeenCalledWith('/separations/abc')
    expect(result).toEqual(separation)
  })

  it('rejects when the server answers with an error', async () => {
    const fetcher = respondingWith({ detail: 'Unknown separation' }, 404)

    await expect(createHttpApi(fetcher).get('nope')).rejects.toThrow('404')
  })

  it('builds stem urls', () => {
    expect(createHttpApi(respondingWith(null)).stemUrl('abc', 'guitar')).toBe(
      '/separations/abc/stems/guitar',
    )
  })
})
