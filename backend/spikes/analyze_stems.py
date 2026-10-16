import argparse
import wave
from pathlib import Path

import numpy as np


def read_stereo(path: Path) -> np.ndarray:
    with wave.open(str(path)) as file:
        frames = file.readframes(file.getnframes())
    return np.frombuffer(frames, dtype=np.int16).reshape(-1, 2).astype(np.float64) / 32768


def energy(signal: np.ndarray) -> float:
    return float(np.sum(signal**2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stems_dir", type=Path)
    args = parser.parse_args()

    stems = {path.stem: read_stereo(path) for path in sorted(args.stems_dir.glob("*.wav"))}
    total = sum(energy(signal) for signal in stems.values())

    print(f"{'stem':<8}{'share':>9}{'L/R':>10}{'corr L-R':>10}")
    for name, signal in stems.items():
        left, right = signal[:, 0], signal[:, 1]
        balance = energy(left) / max(energy(right), 1e-12)
        correlation = float(np.corrcoef(left, right)[0, 1])
        share = 10 * np.log10(max(energy(signal) / total, 1e-12))
        print(f"{name:<8}{share:>7.1f}dB{balance:>10.2f}{correlation:>10.2f}")


if __name__ == "__main__":
    main()
