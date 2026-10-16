import argparse
import os
import time
from pathlib import Path

import torch
from demucs.api import Separator, save_audio

from amanuensis.device import Device, resolve_device


def available_devices() -> frozenset[Device]:
    found = set()
    if torch.cuda.is_available():
        found.add(Device.CUDA)
    if torch.backends.mps.is_available():
        found.add(Device.MPS)
    return frozenset(found)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, default=Path("data/stems"))
    parser.add_argument("--model", default="htdemucs_6s")
    args = parser.parse_args()

    device = resolve_device(available_devices(), os.environ.get("AMANUENSIS_DEVICE"))
    print(f"device: {device}  model: {args.model}  torch: {torch.__version__}")

    started = time.perf_counter()
    separator = Separator(model=args.model, device=str(device), progress=True)
    loaded = time.perf_counter()
    _, stems = separator.separate_audio_file(args.input)
    separated = time.perf_counter()

    target = args.out / args.input.stem
    target.mkdir(parents=True, exist_ok=True)
    for name, wav in stems.items():
        save_audio(wav, target / f"{name}.wav", samplerate=separator.samplerate)

    print(f"load: {loaded - started:.1f}s  separate: {separated - loaded:.1f}s")
    print(f"stems: {', '.join(stems)} -> {target}")


if __name__ == "__main__":
    main()
