import wave
from pathlib import Path

import pytest

from amanuensis.stem_levels import audible_stems, wav_energy
from tests.wav import write_tone


def test_silence_has_no_energy(tmp_path: Path) -> None:
    write_tone(tmp_path / "silence.wav", amplitude=0.0)

    assert wav_energy(tmp_path / "silence.wav") == 0


def test_louder_audio_has_more_energy(tmp_path: Path) -> None:
    write_tone(tmp_path / "quiet.wav", amplitude=0.1)
    write_tone(tmp_path / "loud.wav", amplitude=0.4)

    assert wav_energy(tmp_path / "loud.wav") > wav_energy(tmp_path / "quiet.wav")


def test_keeps_stems_above_the_threshold_share_of_total_energy() -> None:
    energies = {"drums": 50.0, "bass": 49.0, "piano": 0.9, "vocals": 0.05}

    assert audible_stems(energies, threshold_db=-30) == ["drums", "bass", "piano"]


def test_drops_stems_below_the_threshold_share_of_total_energy() -> None:
    energies = {"guitar": 1000.0, "drums": 0.5}

    assert audible_stems(energies, threshold_db=-30) == ["guitar"]


def test_nothing_is_audible_in_silence() -> None:
    assert audible_stems({"drums": 0.0, "bass": 0.0}, threshold_db=-30) == []


def test_rejects_audio_that_is_not_16_bit(tmp_path: Path) -> None:
    path = tmp_path / "8bit.wav"
    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(1)
        file.setframerate(8000)
        file.writeframes(bytes(100))

    with pytest.raises(ValueError, match="16-bit"):
        wav_energy(path)
