import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO, Protocol
from uuid import uuid4

from amanuensis.audio_io import mix_wavs
from amanuensis.stem_levels import audible_stems, wav_energy

BACKGROUND = "background"


class Separator(Protocol):
    def separate(self, source: Path, target: Path) -> list[str]: ...


class Status(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Separation:
    id: str
    status: Status = Status.QUEUED
    stems: list[str] = field(default_factory=list)
    background: str | None = None
    error: str | None = None


class SeparationService:
    def __init__(
        self,
        separator: Separator,
        data_dir: Path,
        new_id: Callable[[], str] = lambda: uuid4().hex,
        silence_threshold_db: float = -30.0,
    ) -> None:
        self._separator = separator
        self._root = data_dir / "separations"
        self._new_id = new_id
        self._silence_threshold_db = silence_threshold_db
        self._separations: dict[str, Separation] = {}

    def submit(self, filename: str, content: BinaryIO) -> Separation:
        separation = Separation(self._new_id())
        folder = self._root / separation.id
        folder.mkdir(parents=True)
        with (folder / f"input{Path(filename).suffix.lower()}").open("wb") as source:
            shutil.copyfileobj(content, source)
        self._separations[separation.id] = separation
        return separation

    def run(self, separation_id: str) -> None:
        separation = self._separations[separation_id]
        separation.status = Status.RUNNING
        source = next((self._root / separation_id).glob("input*"))
        stems_dir = self._stems_dir(separation_id)
        stems_dir.mkdir()
        try:
            stems = self._separator.separate(source, stems_dir)
            energies = {stem: wav_energy(self._stem_file(separation_id, stem)) for stem in stems}
            separation.stems = audible_stems(energies, self._silence_threshold_db)
            self._mix_background(separation, [s for s in stems if s not in separation.stems])
            separation.status = Status.DONE
        except Exception as error:
            separation.error = str(error)
            separation.status = Status.FAILED

    def get(self, separation_id: str) -> Separation | None:
        return self._separations.get(separation_id)

    def stem_path(self, separation_id: str, stem: str) -> Path | None:
        separation = self.get(separation_id)
        if separation is None or stem not in [*separation.stems, separation.background]:
            return None
        return self._stem_file(separation_id, stem)

    def _mix_background(self, separation: Separation, hidden: list[str]) -> None:
        if not hidden:
            return
        files = [self._stem_file(separation.id, stem) for stem in hidden]
        mix_wavs(files, self._stem_file(separation.id, BACKGROUND))
        separation.background = BACKGROUND

    def _stems_dir(self, separation_id: str) -> Path:
        return self._root / separation_id / "stems"

    def _stem_file(self, separation_id: str, stem: str) -> Path:
        return self._stems_dir(separation_id) / f"{stem}.wav"
