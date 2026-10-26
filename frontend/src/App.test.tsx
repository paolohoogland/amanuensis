import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import type { Separation, SeparationApi } from './api'

function separation(overrides: Partial<Separation> = {}): Separation {
  return { id: 'abc', status: 'queued', stems: [], background: null, error: null, ...overrides }
}

function fakeApi(...updates: Separation[]): SeparationApi {
  return {
    upload: vi.fn().mockResolvedValue(separation()),
    get: vi.fn().mockImplementation(() => Promise.resolve(updates.shift() ?? separation())),
    stemUrl: (id, stem) => `/separations/${id}/stems/${stem}`,
  }
}

async function uploadSong(api: SeparationApi) {
  const user = userEvent.setup()
  render(<App api={api} pollIntervalMs={0} />)
  await user.upload(screen.getByLabelText('Song'), new File(['audio'], 'song.mp3', { type: 'audio/mpeg' }))
  await user.click(screen.getByRole('button', { name: 'Separate' }))
}

describe('App', () => {
  beforeEach(() => window.history.replaceState(null, '', '/'))

  it('disables separation until a song is chosen', () => {
    render(<App api={fakeApi()} pollIntervalMs={0} />)

    expect(screen.getByRole('button', { name: 'Separate' })).toBeDisabled()
  })

  it('uploads the chosen song', async () => {
    const api = fakeApi(separation({ status: 'done', stems: ['drums'] }))

    await uploadSong(api)

    expect(api.upload).toHaveBeenCalledWith(expect.objectContaining({ name: 'song.mp3' }))
  })

  it('polls until the separation is done and lists the stems', async () => {
    const api = fakeApi(
      separation({ status: 'running' }),
      separation({ status: 'done', stems: ['drums', 'guitar'] }),
    )

    await uploadSong(api)

    expect(await screen.findByRole('listitem', { name: 'guitar' })).toBeInTheDocument()
    expect(screen.getByRole('listitem', { name: 'drums' })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('done')
    expect(api.get).toHaveBeenCalledTimes(2)
  })

  it('lets you listen to each stem', async () => {
    await uploadSong(fakeApi(separation({ status: 'done', stems: ['drums', 'guitar'] })))

    expect(await screen.findByLabelText('guitar audio')).toHaveAttribute(
      'src',
      '/separations/abc/stems/guitar',
    )
    expect(screen.getByLabelText('drums audio')).toHaveAttribute(
      'src',
      '/separations/abc/stems/drums',
    )
  })

  it('plays the background track with the stems', async () => {
    await uploadSong(
      fakeApi(separation({ status: 'done', stems: ['drums'], background: 'background' })),
    )

    expect(await screen.findByLabelText('background audio')).toHaveAttribute(
      'src',
      '/separations/abc/stems/background',
    )
  })

  it('remembers the separation in the url', async () => {
    await uploadSong(fakeApi(separation({ status: 'done', stems: ['drums'] })))

    await screen.findByRole('listitem', { name: 'drums' })
    expect(new URLSearchParams(window.location.search).get('separation')).toBe('abc')
  })

  it('resumes the separation found in the url', async () => {
    window.history.replaceState(null, '', '/?separation=xyz')
    const api = fakeApi(separation({ id: 'xyz', status: 'done', stems: ['bass'] }))

    render(<App api={api} pollIntervalMs={0} />)

    expect(await screen.findByRole('listitem', { name: 'bass' })).toBeInTheDocument()
    expect(api.get).toHaveBeenCalledWith('xyz')
  })

  it('shows why a separation failed', async () => {
    await uploadSong(fakeApi(separation({ status: 'failed', error: 'model exploded' })))

    expect(await screen.findByRole('alert')).toHaveTextContent('model exploded')
  })

  it('shows an error when the upload fails', async () => {
    const api = fakeApi()
    vi.mocked(api.upload).mockRejectedValue(new Error('Request failed: 500'))

    await uploadSong(api)

    expect(await screen.findByRole('alert')).toHaveTextContent('Request failed: 500')
  })
})
