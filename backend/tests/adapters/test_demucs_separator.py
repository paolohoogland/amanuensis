import wave
from pathlib import Path

import numpy as np
import pytest

from amanuensis.adapters.demucs_separator import DemucsSeparator, detect_devices
from amanuensis.device import resolve_device

SAMPLE_RATE = 44100


def write_tone(path: Path, seconds: float = 2.0) -> None:
    time = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    tone = (0.3 * np.sin(2 * np.pi * 110 * time) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as file:
        file.setnchannels(2)
        file.setsampwidth(2)
        file.setframerate(SAMPLE_RATE)
        file.writeframes(np.repeat(tone, 2).tobytes())


@pytest.mark.slow
def test_separates_a_song_into_six_wav_stems(tmp_path: Path) -> None:
    source = tmp_path / "tone.wav"
    write_tone(source)
    target = tmp_path / "stems"
    target.mkdir()

    stems = DemucsSeparator(resolve_device(detect_devices())).separate(source, target)

    assert sorted(stems) == ["bass", "drums", "guitar", "other", "piano", "vocals"]
    assert sorted(path.stem for path in target.glob("*.wav")) == sorted(stems)
