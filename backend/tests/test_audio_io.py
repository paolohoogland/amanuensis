import wave
from pathlib import Path

import numpy as np
import pytest

from amanuensis.audio_io import mix_wavs, read_wav, write_wav
from tests.wav import SAMPLE_RATE, write_tone


def test_reads_stereo_samples_as_floats_between_minus_one_and_one(tmp_path: Path) -> None:
    write_tone(tmp_path / "tone.wav", amplitude=0.5, seconds=0.1)

    rate, signal = read_wav(tmp_path / "tone.wav")

    assert rate == SAMPLE_RATE
    assert signal.shape == (SAMPLE_RATE // 10, 2)
    assert signal.dtype == np.float32
    assert 0.49 < np.abs(signal).max() <= 0.5


def test_reads_mono_as_a_single_column(tmp_path: Path) -> None:
    path = tmp_path / "mono.wav"
    write_wav(path, SAMPLE_RATE, np.zeros((100, 1), dtype=np.float32))

    assert read_wav(path)[1].shape == (100, 1)


def test_round_trips_written_audio(tmp_path: Path) -> None:
    signal = np.linspace(-0.9, 0.9, 200, dtype=np.float32).reshape(100, 2)

    write_wav(tmp_path / "out.wav", SAMPLE_RATE, signal)

    assert np.allclose(read_wav(tmp_path / "out.wav")[1], signal, atol=1e-4)


def test_clips_out_of_range_samples_when_writing(tmp_path: Path) -> None:
    write_wav(tmp_path / "loud.wav", SAMPLE_RATE, np.full((10, 2), 3.0, dtype=np.float32))

    assert np.abs(read_wav(tmp_path / "loud.wav")[1]).max() <= 1.0


def test_rejects_audio_that_is_not_16_bit(tmp_path: Path) -> None:
    path = tmp_path / "8bit.wav"
    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(1)
        file.setframerate(8000)
        file.writeframes(bytes(100))

    with pytest.raises(ValueError, match="16-bit"):
        read_wav(path)


def test_mixes_wav_files_by_adding_their_samples(tmp_path: Path) -> None:
    first = np.full((100, 2), 0.25, dtype=np.float32)
    second = np.full((100, 2), -0.1, dtype=np.float32)
    write_wav(tmp_path / "first.wav", SAMPLE_RATE, first)
    write_wav(tmp_path / "second.wav", SAMPLE_RATE, second)

    mix_wavs([tmp_path / "first.wav", tmp_path / "second.wav"], tmp_path / "mix.wav")

    rate, mixed = read_wav(tmp_path / "mix.wav")
    assert rate == SAMPLE_RATE
    assert np.allclose(mixed, first + second, atol=1e-4)
