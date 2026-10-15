import pytest

from amanuensis.domain.pitch import Pitch


@pytest.mark.parametrize(
    ("name", "midi"),
    [
        ("C-1", 0),
        ("E1", 28),
        ("E2", 40),
        ("A4", 69),
        ("C#3", 49),
        ("G9", 127),
    ],
)
def test_parses_and_formats_names(name: str, midi: int) -> None:
    assert Pitch.from_name(name) == Pitch(midi)
    assert Pitch(midi).name == name


@pytest.mark.parametrize(("flat", "sharp"), [("Db3", "C#3"), ("Eb2", "D#2"), ("Bb1", "A#1")])
def test_flats_are_parsed_as_enharmonic_sharps(flat: str, sharp: str) -> None:
    assert Pitch.from_name(flat) == Pitch.from_name(sharp)


def test_parsing_ignores_case_and_whitespace() -> None:
    assert Pitch.from_name(" eb2 ") == Pitch.from_name("D#2")


def test_str_is_the_name() -> None:
    assert str(Pitch(40)) == "E2"


def test_pitches_are_ordered_by_height() -> None:
    assert Pitch.from_name("E2") < Pitch.from_name("A2")


@pytest.mark.parametrize("midi", [-1, 128])
def test_rejects_out_of_range_midi(midi: int) -> None:
    with pytest.raises(ValueError, match=str(midi)):
        Pitch(midi)


@pytest.mark.parametrize("name", ["", "H2", "E", "E#", "Ebb2", "C10", "2E"])
def test_rejects_invalid_names(name: str) -> None:
    with pytest.raises(ValueError):
        Pitch.from_name(name)
