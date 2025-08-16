import queue
import threading
import sys
import time
import math
from typing import Optional, Callable, List, List
import math
import time

try:
    import pyaudio  # Lightweight enough for Pi
except ImportError:
    pyaudio = None

class MicrophoneStream:
    """Opens a recording stream as a generator yielding audio chunks."""

    def __init__(self, rate: int = 16000, chunk: int = 1024, device_index: Optional[int] = None):
        self.rate = rate
        self.chunk = chunk
        self.device_index = device_index
        self._buff: "queue.Queue[bytes]" = queue.Queue()
        self.closed = True
        self._audio_interface = None
        self._audio_stream = None

    def __enter__(self):
        if pyaudio is None:
            raise RuntimeError("pyaudio not installed. Install with: pip install pyaudio")
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
            input_device_index=self.device_index,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._audio_stream is not None:
            self._audio_stream.stop_stream()
            self._audio_stream.close()
        if self._audio_interface is not None:
            self._audio_interface.terminate()
        self.closed = True
        # Clear any remaining data in buffer
        self.clear_buffer()
        # Signal the generator to terminate
        self._buff.put(None)  # type: ignore

    def clear_buffer(self):
        """Clear the audio buffer to avoid stale audio."""
        try:
            while True:
                self._buff.get_nowait()
        except queue.Empty:
            pass

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield b"".join(data)

    def capture_until_silence(self, 
                              max_duration: float = 8.0,
                              silence_duration: float = 0.5,  # Faster response
                              energy_threshold: float = 200.0,  # Lower threshold for better sensitivity
                              min_duration: float = 0.3) -> bytes:  # Faster minimum
        """Capture audio until silence detected (improved RMS VAD). Returns PCM16 bytes.
        Blocks inside context manager. Falls back to fixed max_duration if threshold not met.
        """
        if self.closed:
            raise RuntimeError("MicrophoneStream must be used as context manager")
        start = time.time()
        last_voice_time = start
        collected: List[bytes] = []
        speech_detected = False
        energy_history = []
        avg_energy = 0.0
        consecutive_silence = 0
        
        print(f"🎤 VAD: threshold={energy_threshold:.1f}, silence={silence_duration}s")
        
        for chunk in self.generator():
            collected.append(chunk)
            # Compute RMS energy
            if len(chunk) >= 2:
                samples = memoryview(chunk)
                # interpret little endian 16-bit
                count = len(samples) // 2
                energy = 0.0
                for i in range(0, count * 2, 2):
                    sample = int.from_bytes(samples[i:i+2], 'little', signed=True)
                    energy += sample * sample
                rms = math.sqrt(energy / max(count, 1))
                
                # Track energy history for adaptive threshold with smaller window
                energy_history.append(rms)
                if len(energy_history) > 10:  # Shorter history for faster adaptation
                    energy_history.pop(0)
                avg_energy = sum(energy_history) / len(energy_history)
                
                now = time.time()
                dur = now - start
                
                # More aggressive dynamic threshold
                background_noise = avg_energy * 1.8  # Lower multiplier
                dynamic_threshold = max(energy_threshold, background_noise)
                
                if rms > dynamic_threshold:
                    last_voice_time = now
                    consecutive_silence = 0
                    if not speech_detected:
                        speech_detected = True
                        print(f"🎙️ Speech detected (energy: {rms:.1f})")
                else:
                    consecutive_silence += 1
                
                silent_for = now - last_voice_time
                
                # More responsive feedback - every 0.2s
                if dur > 0.2 and int(dur * 5) % 3 == 0:
                    status = "🟢 Speaking" if rms > dynamic_threshold else "� Silent"
                    print(f"{status} | Energy: {rms:.0f} | Silent: {silent_for:.1f}s")
                
                # Early termination with consecutive silence chunks
                chunk_duration = len(chunk) / (self.rate * 2)  # Duration of this chunk
                silence_chunks_needed = int(silence_duration / chunk_duration)
                
                # Stop conditions - more aggressive
                if speech_detected and dur >= min_duration:
                    # Option 1: Traditional silence duration
                    if silent_for >= silence_duration:
                        print(f"✅ Speech ended by silence (total: {dur:.1f}s)")
                        break
                    # Option 2: Consecutive silent chunks (faster)
                    elif consecutive_silence >= silence_chunks_needed:
                        print(f"✅ Speech ended by chunk count (total: {dur:.1f}s)")
                        break
                
                if dur >= max_duration:
                    print(f"⏱️ Max duration reached ({max_duration}s)")
                    break
                    
        return b"".join(collected)


if __name__ == "__main__":
    # Simple test: prints size of audio chunks
    if pyaudio is None:
        print("pyaudio not installed", file=sys.stderr)
        sys.exit(1)
    with MicrophoneStream() as mic:
        for i, chunk in enumerate(mic.generator()):
            print("chunk", i, len(chunk))
            if i > 10:
                break
