import argparse
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pretty_midi
from basic_pitch import ICASSP_2022_MODEL_PATH
from basic_pitch.inference import predict

from amanuensis.audio_io import read_wav, write_wav
from amanuensis.domain.pitch import Pitch

RANGES = {
    "bass": (Pitch.from_name("B0"), Pitch.from_name("G4")),
    "guitar": (Pitch.from_name("D2"), Pitch.from_name("E6")),
}


def hertz(pitch: Pitch) -> float:
    return 440.0 * 2 ** ((pitch.midi - 69) / 12)


def max_polyphony(notes: list[tuple[float, float]]) -> int:
    events = sorted([(start, 1) for start, _ in notes] + [(end, -1) for _, end in notes])
    current = peak = 0
    for _, change in events:
        current += change
        peak = max(peak, current)
    return peak


def keep_lowest(midi: pretty_midi.PrettyMIDI) -> pretty_midi.PrettyMIDI:
    notes = midi.instruments[0].notes

    def masked(note: pretty_midi.Note) -> bool:
        for other in notes:
            overlap = min(note.end, other.end) - max(note.start, other.start)
            if other.pitch < note.pitch and overlap > 0.5 * (note.end - note.start):
                return True
        return False

    midi.instruments[0].notes = [note for note in notes if not masked(note)]
    return midi


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stem", type=Path)
    parser.add_argument("--instrument", choices=RANGES, required=True)
    parser.add_argument("--onset", type=float, default=0.5)
    parser.add_argument("--frame", type=float, default=0.3)
    parser.add_argument("--monophonic", action="store_true")
    args = parser.parse_args()

    low, high = RANGES[args.instrument]
    started = time.perf_counter()
    _, midi, events = predict(
        args.stem,
        ICASSP_2022_MODEL_PATH,
        onset_threshold=args.onset,
        frame_threshold=args.frame,
        minimum_frequency=hertz(low),
        maximum_frequency=hertz(high),
    )
    elapsed = time.perf_counter() - started
    if args.monophonic:
        midi = keep_lowest(midi)
        kept = {(round(n.start, 3), n.pitch) for n in midi.instruments[0].notes}
        events = [e for e in events if (round(e[0], 3), e[2]) in kept]

    suffix = "_mono" if args.monophonic else ""
    target = args.stem.with_name(f"{args.stem.stem}_basic_pitch{suffix}")
    midi.write(str(target.with_suffix(".mid")))

    rate, stem = read_wav(args.stem)
    synth = midi.synthesize(fs=rate)[: len(stem)]
    synth = np.pad(synth, (0, len(stem) - len(synth)))
    synth = 0.3 * synth / max(np.abs(synth).max(), 1e-9)
    overlay = np.stack([stem.mean(axis=1) * 0.7, synth], axis=1)
    write_wav(target.with_name(f"{target.name}_overlay.wav"), rate, overlay)

    pitches = [Pitch(int(pitch)) for _, _, pitch, _, _ in events]
    durations = [end - start for start, end, *_ in events]
    common = ", ".join(f"{p.name} x{n}" for p, n in Counter(pitches).most_common(8))
    seconds = len(stem) / rate
    print(f"transcribed {seconds:.0f}s of audio in {elapsed:.1f}s")
    print(f"notes: {len(events)} ({len(events) / seconds:.1f}/s)")
    print(f"range: {min(pitches).name} - {max(pitches).name}")
    print(f"max polyphony: {max_polyphony([(s, e) for s, e, *_ in events])}")
    median, shortest = np.median(durations) * 1000, min(durations) * 1000
    print(f"duration: median {median:.0f} ms, min {shortest:.0f} ms")
    print(f"most common: {common}")
    print(f"-> {target}.mid, {target.name}_overlay.wav (left: stem, right: midi)")


if __name__ == "__main__":
    main()
