import argparse
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import ShortTimeFFT
from scipy.signal.windows import hann

WINDOW = 4096
HOP = 1024


def read(path: Path) -> tuple[int, np.ndarray]:
    rate, data = wavfile.read(path)
    return rate, data.astype(np.float32) / 32768


def write(path: Path, rate: int, signal: np.ndarray) -> None:
    wavfile.write(path, rate, (np.clip(signal, -1, 1) * 32767).astype(np.int16))


def two_means(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    low, high = np.quantile(values, [0.25, 0.75])
    for _ in range(50):
        threshold = (low + high) / 2
        left, right = values < threshold, values >= threshold
        low = np.average(values[left], weights=weights[left])
        high = np.average(values[right], weights=weights[right])
    return float(low), float(high)


def pan_split(signal: np.ndarray, rate: int, sharpness: float) -> tuple[np.ndarray, ...]:
    stft = ShortTimeFFT(hann(WINDOW, sym=False), hop=HOP, fs=rate)
    left, right = stft.stft(signal[:, 0]), stft.stft(signal[:, 1])
    magnitude_left, magnitude_right = np.abs(left), np.abs(right)
    pan = (magnitude_right - magnitude_left) / (magnitude_right + magnitude_left + 1e-9)
    energy = magnitude_left**2 + magnitude_right**2
    loud = energy > np.quantile(energy, 0.5)
    low, high = two_means(pan[loud], energy[loud])
    threshold = (low + high) / 2
    mask = 1 / (1 + np.exp(sharpness * (pan - threshold)))
    print(f"pan clusters: {low:+.2f} / {high:+.2f}  threshold {threshold:+.2f}")

    def rebuild(weight: np.ndarray) -> np.ndarray:
        channels = [stft.istft(spectrum * weight, k1=len(signal)) for spectrum in (left, right)]
        return np.stack(channels, axis=1)

    return rebuild(mask), rebuild(1 - mask)


def correlation(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.corrcoef(first.mean(axis=1), second.mean(axis=1))[0, 1])


def share_db(part: np.ndarray, whole: np.ndarray) -> float:
    return float(10 * np.log10(np.sum(part**2) / np.sum(whole**2) + 1e-12))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stems_dir", type=Path)
    parser.add_argument("--sharpness", type=float, default=8.0)
    args = parser.parse_args()

    rate, guitar = read(args.stems_dir / "guitar.wav")
    target = args.stems_dir / "guitar_split"
    target.mkdir(exist_ok=True)

    raw_left = np.repeat(guitar[:, :1], 2, axis=1)
    raw_right = np.repeat(guitar[:, 1:], 2, axis=1)
    pan_left, pan_right = pan_split(guitar, rate, args.sharpness)

    print(f"{'method':<6}{'corr':>7}{'left':>9}{'right':>9}")
    for method, first, second in (("raw", raw_left, raw_right), ("pan", pan_left, pan_right)):
        write(target / f"{method}_1.wav", rate, first)
        write(target / f"{method}_2.wav", rate, second)
        print(
            f"{method:<6}{correlation(first, second):>7.2f}"
            f"{share_db(first, guitar):>7.1f}dB{share_db(second, guitar):>7.1f}dB"
        )
    print(f"-> {target}")


if __name__ == "__main__":
    main()
