import { useEffect, useRef, useState, type AudioHTMLAttributes } from 'react'
import { anySoloed, createMix, isAudible, setVolume, toggleMute, toggleSolo } from './mix'
import { formatTime } from './time'

export type Track = {
  name: string
  url: string
}

type Props = {
  tracks: Track[]
  background?: string
}

export function Mixer({ tracks, background }: Props) {
  const elements = useRef(new Map<string, HTMLAudioElement>())
  const backgroundElement = useRef<HTMLAudioElement>(null)
  const [mix, setMix] = useState(() => createMix(tracks.map((track) => track.name)))
  const [playing, setPlaying] = useState(false)
  const [position, setPosition] = useState(0)
  const [duration, setDuration] = useState(0)

  useEffect(() => {
    for (const [name, element] of elements.current) {
      element.muted = !isAudible(mix, name)
      element.volume = mix[name].volume
    }
    if (backgroundElement.current) {
      backgroundElement.current.muted = anySoloed(mix)
    }
  }, [mix])

  const everyElement = () =>
    [...elements.current.values(), backgroundElement.current].filter((element) => element !== null)

  const clockEvents: AudioHTMLAttributes<HTMLAudioElement> = {
    onLoadedMetadata: (event) => setDuration(event.currentTarget.duration),
    onTimeUpdate: (event) => setPosition(event.currentTarget.currentTime),
    onEnded: () => setPlaying(false),
  }

  function togglePlayback() {
    if (playing) {
      everyElement().forEach((element) => element.pause())
    } else {
      everyElement().forEach((element) => element.play().catch(() => setPlaying(false)))
    }
    setPlaying(!playing)
  }

  function seek(time: number) {
    everyElement().forEach((element) => {
      element.currentTime = time
    })
    setPosition(time)
  }

  return (
    <section aria-label="Mixer">
      <div>
        <button type="button" onClick={togglePlayback}>
          {playing ? 'Pause' : 'Play'}
        </button>
        <input
          type="range"
          aria-label="Position"
          min={0}
          max={duration}
          step={0.1}
          value={position}
          onChange={(event) => seek(Number(event.target.value))}
        />
        <span>
          {formatTime(position)} / {formatTime(duration)}
        </span>
      </div>
      {background && (
        <audio
          ref={backgroundElement}
          aria-label="background audio"
          src={background}
          preload="auto"
        />
      )}
      <ul>
        {tracks.map((track, index) => {
          const label = track.name.replaceAll('_', ' ')
          return (
            <li key={track.name} aria-label={label}>
              <audio
                ref={(element) => {
                  if (element) {
                    elements.current.set(track.name, element)
                  }
                  return () => {
                    elements.current.delete(track.name)
                  }
                }}
                aria-label={`${label} audio`}
                src={track.url}
                preload="auto"
                {...(index === 0 ? clockEvents : {})}
              />
              <span>{label}</span>
              <button
                type="button"
                aria-label={`Mute ${label}`}
                aria-pressed={mix[track.name].muted}
                onClick={() => setMix((current) => toggleMute(current, track.name))}
              >
                M
              </button>
              <button
                type="button"
                aria-label={`Solo ${label}`}
                aria-pressed={mix[track.name].soloed}
                onClick={() => setMix((current) => toggleSolo(current, track.name))}
              >
                S
              </button>
              <input
                type="range"
                aria-label={`${label} volume`}
                min={0}
                max={1}
                step={0.01}
                value={mix[track.name].volume}
                onChange={(event) =>
                  setMix((current) => setVolume(current, track.name, Number(event.target.value)))
                }
              />
            </li>
          )
        })}
      </ul>
    </section>
  )
}
