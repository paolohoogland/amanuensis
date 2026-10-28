import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44100


def write_tone(path: Path, amplitude: float = 0.3, seconds: float = 2.0) -> None:
    time = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    tone = (amplitude * np.sin(2 * np.pi * 110 * time) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as file:
        file.setnchannels(2)
        file.setsampwidth(2)
        file.setframerate(SAMPLE_RATE)
        file.writeframes(np.repeat(tone, 2).tobytes())
