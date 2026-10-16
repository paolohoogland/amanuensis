import os
from pathlib import Path

from fastapi import FastAPI

from amanuensis.adapters.demucs_separator import DemucsSeparator, detect_devices
from amanuensis.api import create_app
from amanuensis.device import resolve_device
from amanuensis.separation import SeparationService


def build_app() -> FastAPI:
    device = resolve_device(detect_devices(), os.environ.get("AMANUENSIS_DEVICE"))
    data_dir = Path(os.environ.get("AMANUENSIS_DATA_DIR", "data"))
    return create_app(SeparationService(DemucsSeparator(device), data_dir))
