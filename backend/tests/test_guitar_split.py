from pathlib import Path

import numpy as np

from amanuensis.audio_io import read_wav, write_wav
from amanuensis.guitar_split import GuitarSplitter, split_by_panning

RATE = 44100


def tone(frequency: float, seconds: float = 1.0) -> np.ndarray:
    time = np.arange(int(RATE * seconds)) / RATE
    return (0.3 * np.sin(2 * np.pi * frequency * time)).astype(np.float32)


def panned(signal: np.ndarray, left: float, right: float) -> np.ndarray:
    return np.stack([signal * left, signal * right], axis=1)


def band_energy(signal: np.ndarray, frequency: float) -> float:
    spectrum = np.abs(np.fft.rfft(signal.mean(axis=1)))
    center = round(frequency * len(signal) / RATE)
    return float(np.sum(spectrum[center - 2 : center + 3] ** 2))


TWO_GUITARS = panned(tone(220), 1.0, 0.2) + panned(tone(330), 0.2, 1.0)
ONE_GUITAR = panned(tone(220) + tone(330), 1.0, 1.0)


def test_splits_two_panned_guitars_into_left_and_right() -> None:
    split = split_by_panning(TWO_GUITARS, RATE)

    assert split is not None
    left, right = split
    assert band_energy(left, 220) > 100 * band_energy(left, 330)
    assert band_energy(right, 330) > 100 * band_energy(right, 220)


def test_split_halves_add_up_to_the_original() -> None:
    split = split_by_panning(TWO_GUITARS, RATE)

    assert split is not None
    assert np.allclose(split[0] + split[1], TWO_GUITARS, atol=1e-3)


def test_does_not_split_a_centered_guitar() -> None:
    assert split_by_panning(ONE_GUITAR, RATE) is None


def test_does_not_split_mono() -> None:
    assert split_by_panning(tone(220).reshape(-1, 1), RATE) is None


def test_does_not_split_silence() -> None:
    assert split_by_panning(np.zeros((RATE, 2), dtype=np.float32), RATE) is None


class StemWriter:
    def __init__(self, stems: dict[str, np.ndarray]) -> None:
        self.stems = stems

    def separate(self, source: Path, target: Path) -> list[str]:
        for name, signal in self.stems.items():
            write_wav(target / f"{name}.wav", RATE, signal)
        return list(self.stems)


def test_replaces_a_two_guitar_stem_with_one_stem_per_guitar(tmp_path: Path) -> None:
    splitter = GuitarSplitter(StemWriter({"drums": ONE_GUITAR, "guitar": TWO_GUITARS}))

    stems = splitter.separate(tmp_path / "song.wav", tmp_path)

    assert stems == ["drums", "guitar_1", "guitar_2"]
    first = read_wav(tmp_path / "guitar_1.wav")[1]
    assert band_energy(first, 220) > 100 * band_energy(first, 330)


def test_keeps_a_single_guitar_stem(tmp_path: Path) -> None:
    splitter = GuitarSplitter(StemWriter({"drums": TWO_GUITARS, "guitar": ONE_GUITAR}))

    assert splitter.separate(tmp_path / "song.wav", tmp_path) == ["drums", "guitar"]


def test_passes_songs_without_guitar_through(tmp_path: Path) -> None:
    splitter = GuitarSplitter(StemWriter({"drums": ONE_GUITAR}))

    assert splitter.separate(tmp_path / "song.wav", tmp_path) == ["drums"]
