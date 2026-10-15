from enum import StrEnum


class Device(StrEnum):
    CUDA = "cuda"
    MPS = "mps"
    CPU = "cpu"


PRIORITY = (Device.CUDA, Device.MPS, Device.CPU)


class DeviceUnavailableError(RuntimeError):
    pass


def resolve_device(available: frozenset[Device], requested: str | None = None) -> Device:
    usable = available | {Device.CPU}
    if requested and requested.strip():
        return _validate(Device(requested.strip().lower()), usable)
    return next(device for device in PRIORITY if device in usable)


def _validate(device: Device, usable: frozenset[Device]) -> Device:
    if device not in usable:
        raise DeviceUnavailableError(f"Requested device '{device}' is not available")
    return device
