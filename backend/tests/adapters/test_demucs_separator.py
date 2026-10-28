from pathlib import Path

import pytest

from amanuensis.adapters.demucs_separator import DemucsSeparator, detect_devices
from amanuensis.device import resolve_device
from tests.wav import write_tone


@pytest.mark.slow
def test_separates_a_song_into_six_wav_stems(tmp_path: Path) -> None:
    source = tmp_path / "tone.wav"
    write_tone(source)
    target = tmp_path / "stems"
    target.mkdir()

    stems = DemucsSeparator(resolve_device(detect_devices())).separate(source, target)

    assert sorted(stems) == ["bass", "drums", "guitar", "other", "piano", "vocals"]
    assert sorted(path.stem for path in target.glob("*.wav")) == sorted(stems)
