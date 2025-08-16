from typing import Iterable, Optional, Generator
import subprocess
import shutil
import tempfile
import os

# We will use openai-whisper for now since faster-whisper has dependency issues
try:
    import whisper  # type: ignore
    WhisperModel = whisper
except ImportError:
    whisper = None  # type: ignore
    WhisperModel = None  # type: ignore

SUPPORTED_LANGS = {"en", "uk"}  # English + Ukrainian

class StreamingWhisperRecognizer:
    def __init__(self, model_size: str = "small"):
        if WhisperModel is None:
            raise RuntimeError("openai-whisper not installed. pip install openai-whisper")
        print(f"Loading Whisper model: {model_size}")
        self.model = whisper.load_model(model_size)

    def transcribe_chunks(self, chunks: Iterable[bytes], language: Optional[str] = None) -> Generator[str, None, None]:
        """Yield partial text for each aggregated chunk. (Naive implementation)
        For a real streaming solution we would maintain context and pass overlapping windows.
        """
        buffer = b""
        for chunk in chunks:
            buffer += chunk
            # Heuristic: process every ~1s (16000 samples * 2 bytes = 32000 bytes)
            if len(buffer) >= 32000:
                text = self._run_once(buffer, language=language)
                if text.strip():
                    yield text.strip()
                buffer = b""
        if buffer:
            text = self._run_once(buffer, language=language)
            if text.strip():
                yield text.strip()

    def _run_once(self, pcm16: bytes, language: Optional[str]):
        # Simple approach: save PCM as numpy array and use whisper directly
        import numpy as np
        
        # Convert PCM16 bytes to float32 array for whisper
        audio_np = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Specify language for better Ukrainian recognition
        result = self.model.transcribe(
            audio_np, 
            language=language,
            # Better options for Ukrainian
            task="transcribe",
            verbose=False
        )
        return result["text"]
