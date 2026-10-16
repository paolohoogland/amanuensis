import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO, Protocol
from uuid import uuid4


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
    error: str | None = None


class SeparationService:
    def __init__(
        self,
        separator: Separator,
        data_dir: Path,
        new_id: Callable[[], str] = lambda: uuid4().hex,
    ) -> None:
        self._separator = separator
        self._root = data_dir / "separations"
        self._new_id = new_id
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
        folder = self._root / separation_id
        stems_dir = folder / "stems"
        stems_dir.mkdir()
        try:
            separation.stems = self._separator.separate(next(folder.glob("input*")), stems_dir)
            separation.status = Status.DONE
        except Exception as error:
            separation.error = str(error)
            separation.status = Status.FAILED

    def get(self, separation_id: str) -> Separation | None:
        return self._separations.get(separation_id)

    def stem_path(self, separation_id: str, stem: str) -> Path | None:
        separation = self.get(separation_id)
        if separation is None or stem not in separation.stems:
            return None
        return self._root / separation_id / "stems" / f"{stem}.wav"
