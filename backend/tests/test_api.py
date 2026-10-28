from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from amanuensis.api import create_app
from amanuensis.separation import SeparationService, Separator
from tests.wav import write_tone


class FakeSeparator:
    def __init__(self, amplitudes: dict[str, float] | None = None) -> None:
        self.amplitudes = amplitudes or {"drums": 0.3, "guitar": 0.3}
        self.received: list[bytes] = []

    def separate(self, source: Path, target: Path) -> list[str]:
        self.received.append(source.read_bytes())
        for name, amplitude in self.amplitudes.items():
            write_tone(target / f"{name}.wav", amplitude, seconds=0.1)
        return list(self.amplitudes)


class FailingSeparator:
    def separate(self, source: Path, target: Path) -> list[str]:
        raise RuntimeError("model exploded")


def client_for(separator: Separator, data_dir: Path) -> TestClient:
    return TestClient(create_app(SeparationService(separator, data_dir)))


@pytest.fixture
def separator() -> FakeSeparator:
    return FakeSeparator()


@pytest.fixture
def client(separator: FakeSeparator, tmp_path: Path) -> TestClient:
    return client_for(separator, tmp_path)


def upload(client: TestClient, name: str = "song.mp3", content: bytes = b"song") -> str:
    response = client.post("/separations", files={"file": (name, content, "audio/mpeg")})
    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    return str(response.json()["id"])


def test_uploaded_song_is_given_to_the_separator(
    client: TestClient, separator: FakeSeparator
) -> None:
    upload(client, content=b"my song")

    assert separator.received == [b"my song"]


def test_finished_separation_lists_its_stems(client: TestClient) -> None:
    separation_id = upload(client)

    response = client.get(f"/separations/{separation_id}")

    assert response.json() == {
        "id": separation_id,
        "status": "done",
        "stems": ["drums", "guitar"],
        "error": None,
    }


def test_serves_stem_audio(client: TestClient, tmp_path: Path) -> None:
    separation_id = upload(client)

    response = client.get(f"/separations/{separation_id}/stems/guitar")

    stem_file = tmp_path / "separations" / separation_id / "stems" / "guitar.wav"
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == stem_file.read_bytes()


def test_silent_stems_are_hidden(tmp_path: Path) -> None:
    separator = FakeSeparator({"drums": 0.5, "piano": 0.0, "guitar": 0.5, "vocals": 0.001})
    client = client_for(separator, tmp_path)
    separation_id = upload(client)

    body = client.get(f"/separations/{separation_id}").json()

    assert body["stems"] == ["drums", "guitar"]
    assert client.get(f"/separations/{separation_id}/stems/piano").status_code == 404


def test_each_upload_gets_its_own_separation(client: TestClient) -> None:
    assert upload(client) != upload(client)


def test_failed_separation_reports_the_error(tmp_path: Path) -> None:
    client = client_for(FailingSeparator(), tmp_path)
    separation_id = upload(client)

    body = client.get(f"/separations/{separation_id}").json()

    assert body["status"] == "failed"
    assert body["error"] == "model exploded"
    assert body["stems"] == []


def test_unknown_separation_is_not_found(client: TestClient) -> None:
    assert client.get("/separations/nope").status_code == 404


@pytest.mark.parametrize("stem", ["piano", "..%2F..%2Fsecret"])
def test_unknown_stem_is_not_found(client: TestClient, stem: str) -> None:
    separation_id = upload(client)

    assert client.get(f"/separations/{separation_id}/stems/{stem}").status_code == 404


def test_upload_without_file_is_rejected(client: TestClient) -> None:
    assert client.post("/separations").status_code == 422
