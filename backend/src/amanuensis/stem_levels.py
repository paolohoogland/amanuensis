from collections.abc import Mapping
from pathlib import Path

import numpy as np

from amanuensis.audio_io import read_wav


def wav_energy(path: Path) -> float:
    return float(np.sum(read_wav(path)[1].astype(np.float64) ** 2))


def audible_stems(energies: Mapping[str, float], threshold_db: float) -> list[str]:
    floor = sum(energies.values()) * 10 ** (threshold_db / 10)
    return [stem for stem, energy in energies.items() if energy > floor]
