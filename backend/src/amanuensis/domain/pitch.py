import re
from dataclasses import dataclass
from typing import Self

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
NATURAL_OFFSETS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
ACCIDENTAL_OFFSETS = {"": 0, "#": 1, "B": -1}
NAME_PATTERN = re.compile(r"([A-G])([#B]?)(-1|\d)")
MIDI_RANGE = range(128)


@dataclass(frozen=True, order=True)
class Pitch:
    midi: int

    def __post_init__(self) -> None:
        if self.midi not in MIDI_RANGE:
            raise ValueError(f"MIDI number {self.midi} is outside 0-127")

    @classmethod
    def from_name(cls, name: str) -> Self:
        match = NAME_PATTERN.fullmatch(name.strip().upper())
        if match is None:
            raise ValueError(f"Invalid pitch name '{name}'")
        letter, accidental, octave = match.groups()
        semitone = NATURAL_OFFSETS[letter] + ACCIDENTAL_OFFSETS[accidental]
        return cls((int(octave) + 1) * 12 + semitone)

    @property
    def name(self) -> str:
        octave, index = divmod(self.midi, 12)
        return f"{NOTE_NAMES[index]}{octave - 1}"

    def __str__(self) -> str:
        return self.name
