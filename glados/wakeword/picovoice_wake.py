from typing import Optional, Callable
import time
import struct
import os

try:
    from pvporcupine import create as porcupine_create  # type: ignore
    import pyaudio  # type: ignore
except ImportError:
    porcupine_create = None  # type: ignore
    pyaudio = None  # type: ignore

class WakeWordDetector:
    def __init__(self, keyword_path: str, sensitivity: float = 0.65):
        if porcupine_create is None:
            raise RuntimeError("pvporcupine not installed. pip install pvporcupine pyaudio")
        self.porcupine = porcupine_create(access_key=os.getenv("PICOVOICE_ACCESS_KEY"), keyword_paths=[keyword_path], sensitivities=[sensitivity])
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(rate=self.porcupine.sample_rate,
                                   channels=1,
                                   format=pyaudio.paInt16,
                                   input=True,
                                   frames_per_buffer=self.porcupine.frame_length)

    def listen(self, on_detect: Callable[[], None]):
        try:
            while True:
                pcm = self.stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                result = self.porcupine.process(pcm)
                if result >= 0:
                    on_detect()
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.pa.terminate()
            self.porcupine.delete()
