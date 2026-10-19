import wave
from collections.abc import Mapping
from pathlib import Path

import numpy as np

SAMPLE_WIDTH = 2
FULL_SCALE = 32768


def wav_energy(path: Path) -> float:
    with wave.open(str(path)) as file:
        if file.getsampwidth() != SAMPLE_WIDTH:
            raise ValueError(f"{path.name} is not 16-bit PCM")
        frames = file.readframes(file.getnframes())
    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float64) / FULL_SCALE
    return float(np.sum(samples**2))


def audible_stems(energies: Mapping[str, float], threshold_db: float) -> list[str]:
    floor = sum(energies.values()) * 10 ** (threshold_db / 10)
    return [stem for stem, energy in energies.items() if energy > floor]
