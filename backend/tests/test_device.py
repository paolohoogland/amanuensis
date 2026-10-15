import pytest

from amanuensis.device import Device, DeviceUnavailableError, resolve_device


@pytest.mark.parametrize(
    ("available", "expected"),
    [
        ({Device.CUDA, Device.MPS}, Device.CUDA),
        ({Device.CUDA}, Device.CUDA),
        ({Device.MPS}, Device.MPS),
        (set(), Device.CPU),
    ],
)
def test_picks_fastest_available_device(available: set[Device], expected: Device) -> None:
    assert resolve_device(frozenset(available)) is expected


def test_requested_device_wins_over_priority() -> None:
    assert resolve_device(frozenset({Device.CUDA}), requested="cpu") is Device.CPU


def test_requested_device_is_case_insensitive() -> None:
    assert resolve_device(frozenset({Device.MPS}), requested=" MPS ") is Device.MPS


def test_cpu_is_always_available() -> None:
    assert resolve_device(frozenset(), requested="cpu") is Device.CPU


def test_rejects_requested_device_that_is_not_available() -> None:
    with pytest.raises(DeviceUnavailableError, match="cuda"):
        resolve_device(frozenset({Device.MPS}), requested="cuda")


def test_rejects_unknown_device() -> None:
    with pytest.raises(ValueError, match="tpu"):
        resolve_device(frozenset(), requested="tpu")


def test_empty_request_falls_back_to_priority() -> None:
    assert resolve_device(frozenset({Device.MPS}), requested="") is Device.MPS
