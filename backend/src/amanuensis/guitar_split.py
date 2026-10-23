from pathlib import Path

import numpy as np
from scipy.signal import ShortTimeFFT
from scipy.signal.windows import hann

from amanuensis.audio_io import read_wav, write_wav
from amanuensis.separation import Separator

WINDOW = 4096
HOP = 1024
SHARPNESS = 8.0
MIN_SPREAD = 0.4
GUITAR = "guitar"


def split_by_panning(
    signal: np.ndarray,
    rate: int,
    sharpness: float = SHARPNESS,
    min_spread: float = MIN_SPREAD,
) -> tuple[np.ndarray, np.ndarray] | None:
    if signal.shape[1] != 2:
        return None
    stft = ShortTimeFFT(hann(WINDOW, sym=False), hop=HOP, fs=rate)
    left, right = stft.stft(signal[:, 0]), stft.stft(signal[:, 1])
    magnitude_left, magnitude_right = np.abs(left), np.abs(right)
    energy = magnitude_left**2 + magnitude_right**2
    loud = energy > np.quantile(energy, 0.5)
    if not loud.any():
        return None
    pan = (magnitude_right - magnitude_left) / (magnitude_right + magnitude_left + 1e-9)
    low, high = _pan_clusters(pan[loud], energy[loud])
    if high - low < min_spread:
        return None
    mask = 1 / (1 + np.exp(sharpness * (pan - (low + high) / 2)))

    def rebuild(weight: np.ndarray) -> np.ndarray:
        channels = [stft.istft(spectrum * weight, k1=len(signal)) for spectrum in (left, right)]
        return np.stack(channels, axis=1).astype(np.float32)

    return rebuild(mask), rebuild(1 - mask)


def _pan_clusters(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    low, high = (float(value) for value in np.quantile(values, [0.25, 0.75]))
    for _ in range(50):
        below = values < (low + high) / 2
        if below.all() or not below.any():
            return low, low
        low = float(np.average(values[below], weights=weights[below]))
        high = float(np.average(values[~below], weights=weights[~below]))
    return low, high


class GuitarSplitter:
    def __init__(self, inner: Separator) -> None:
        self._inner = inner

    def separate(self, source: Path, target: Path) -> list[str]:
        stems = self._inner.separate(source, target)
        if GUITAR not in stems:
            return stems
        rate, signal = read_wav(target / f"{GUITAR}.wav")
        split = split_by_panning(signal, rate)
        if split is None:
            return stems
        names = [f"{GUITAR}_1", f"{GUITAR}_2"]
        for name, part in zip(names, split, strict=True):
            write_wav(target / f"{name}.wav", rate, part)
        index = stems.index(GUITAR)
        return [*stems[:index], *names, *stems[index + 1 :]]
