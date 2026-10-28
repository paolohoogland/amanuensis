from functools import cached_property
from pathlib import Path
from threading import Lock

import torch
from demucs import api as demucs
from demucs.audio import save_audio

from amanuensis.device import Device


def detect_devices() -> frozenset[Device]:
    found = set()
    if torch.cuda.is_available():
        found.add(Device.CUDA)
    if torch.backends.mps.is_available():
        found.add(Device.MPS)
    return frozenset(found)


class DemucsSeparator:
    def __init__(self, device: Device, model: str = "htdemucs_6s") -> None:
        self._device = device
        self._model = model
        self._lock = Lock()

    @cached_property
    def _demucs(self) -> demucs.Separator:
        return demucs.Separator(model=self._model, device=str(self._device))

    def separate(self, source: Path, target: Path) -> list[str]:
        with self._lock:
            _, stems = self._demucs.separate_audio_file(source)
            for name, wav in stems.items():
                save_audio(wav, target / f"{name}.wav", samplerate=self._demucs.samplerate)
            return list(stems)
