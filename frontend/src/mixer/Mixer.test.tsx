import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { Mixer } from './Mixer'

const tracks = [
  { name: 'drums', url: '/stems/drums' },
  { name: 'guitar', url: '/stems/guitar' },
]

function audio(name: string): HTMLAudioElement {
  return screen.getByLabelText(`${name} audio`) as HTMLAudioElement
}

function loadSong(seconds: number) {
  Object.defineProperty(audio('drums'), 'duration', { value: seconds })
  fireEvent(audio('drums'), new Event('loadedmetadata'))
}

describe('Mixer', () => {
  beforeEach(() => {
    vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue(undefined)
    vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => {})
  })

  afterEach(() => vi.restoreAllMocks())

  it('loads one audio element per stem', () => {
    render(<Mixer tracks={tracks} />)

    expect(audio('drums')).toHaveAttribute('src', '/stems/drums')
    expect(audio('guitar')).toHaveAttribute('src', '/stems/guitar')
  })

  it('plays and pauses every stem together', async () => {
    const user = userEvent.setup()
    render(<Mixer tracks={tracks} />)

    await user.click(screen.getByRole('button', { name: 'Play' }))
    await user.click(screen.getByRole('button', { name: 'Pause' }))

    const everyStem = expect.arrayContaining([audio('drums'), audio('guitar')])
    expect(vi.mocked(HTMLMediaElement.prototype.play).mock.contexts).toEqual(everyStem)
    expect(vi.mocked(HTMLMediaElement.prototype.pause).mock.contexts).toEqual(everyStem)
    expect(screen.getByRole('button', { name: 'Play' })).toBeInTheDocument()
  })

  it('mutes a single stem', async () => {
    const user = userEvent.setup()
    render(<Mixer tracks={tracks} />)

    await user.click(screen.getByRole('button', { name: 'Mute guitar' }))

    expect(screen.getByRole('button', { name: 'Mute guitar' })).toHaveAttribute('aria-pressed', 'true')
    expect(audio('guitar').muted).toBe(true)
    expect(audio('drums').muted).toBe(false)
  })

  it('silences the other stems when one is soloed', async () => {
    const user = userEvent.setup()
    render(<Mixer tracks={tracks} />)

    await user.click(screen.getByRole('button', { name: 'Solo drums' }))

    expect(audio('drums').muted).toBe(false)
    expect(audio('guitar').muted).toBe(true)
  })

  it('changes the volume of a stem', () => {
    render(<Mixer tracks={tracks} />)

    fireEvent.change(screen.getByLabelText('guitar volume'), { target: { value: '0.5' } })

    expect(audio('guitar').volume).toBe(0.5)
    expect(audio('drums').volume).toBe(1)
  })

  it('seeks every stem to the same position', () => {
    render(<Mixer tracks={tracks} />)
    loadSong(120)

    fireEvent.change(screen.getByLabelText('Position'), { target: { value: '30' } })

    expect(audio('drums').currentTime).toBe(30)
    expect(audio('guitar').currentTime).toBe(30)
    expect(screen.getByText('0:30 / 2:00')).toBeInTheDocument()
  })

  it('shows readable stem names', () => {
    render(<Mixer tracks={[{ name: 'guitar_1', url: '/stems/guitar_1' }]} />)

    expect(screen.getByText('guitar 1')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Mute guitar 1' })).toBeInTheDocument()
    expect(screen.getByLabelText('guitar 1 volume')).toBeInTheDocument()
  })

  it('stops when the song ends', async () => {
    const user = userEvent.setup()
    render(<Mixer tracks={tracks} />)

    await user.click(screen.getByRole('button', { name: 'Play' }))
    fireEvent(audio('drums'), new Event('ended'))

    expect(screen.getByRole('button', { name: 'Play' })).toBeInTheDocument()
  })
})
