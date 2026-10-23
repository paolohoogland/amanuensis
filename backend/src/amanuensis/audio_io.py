from pathlib import Path

import numpy as np
from scipy.io import wavfile

FULL_SCALE = 32768


def read_wav(path: Path) -> tuple[int, np.ndarray]:
    rate, data = wavfile.read(path)
    if data.dtype != np.int16:
        raise ValueError(f"{path.name} is not 16-bit PCM")
    return rate, data.reshape(len(data), -1).astype(np.float32) / FULL_SCALE


def write_wav(path: Path, rate: int, signal: np.ndarray) -> None:
    samples = np.clip(signal * FULL_SCALE, -FULL_SCALE, FULL_SCALE - 1).astype(np.int16)
    wavfile.write(path, rate, samples)
