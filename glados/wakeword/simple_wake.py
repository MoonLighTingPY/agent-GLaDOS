import os
import time
import threading
import wave
import struct
from typing import Callable, Optional
import tempfile

# Simple wake word detection using keyword matching in transcribed audio
# This is a basic implementation - for production use Porcupine or similar

class SimpleWakeWordDetector:
    """Simple wake word detector that transcribes short audio clips and checks for keywords."""
    
    def __init__(self, keywords: list = None, sensitivity: float = 0.7):
        self.keywords = keywords or ["hey glados", "гей глендос", "слухай", "listen"]
        self.sensitivity = sensitivity
        self.running = False
        self.paused = False  # Add pause functionality
        self._asr = None
        
    def set_asr(self, asr):
        """Set the ASR engine for transcription."""
        self._asr = asr
        
    def pause(self):
        """Pause wake word detection."""
        self.paused = True
        
    def resume(self):
        """Resume wake word detection."""
        self.paused = False
        
    def _play_beep(self, frequency: int = 800, duration: float = 0.2):
        """Play a simple beep sound to signal wake word detection."""
        try:
            import pyaudio
            import numpy as np
            
            p = pyaudio.PyAudio()
            
            # Generate beep
            sample_rate = 44100
            frames = int(sample_rate * duration)
            wave_array = np.sin(2 * np.pi * frequency * np.linspace(0, duration, frames))
            wave_array = (wave_array * 32767).astype(np.int16)
            
            stream = p.open(format=pyaudio.paInt16,
                          channels=1,
                          rate=sample_rate,
                          output=True)
            
            stream.write(wave_array.tobytes())
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            # Fallback: just print
            print("🔊 BEEP! (wake word detected)")
            
    def listen_for_wake_word(self, mic_stream, on_wake: Callable[[], None]):
        """Listen continuously for wake word in short audio clips."""
        if not self._asr:
            raise RuntimeError("ASR not set. Call set_asr() first.")
            
        self.running = True
        print("👂 Listening for wake word...")
        
        while self.running:
            try:
                # Skip if paused
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                # Capture short clip (0.5 seconds to be more responsive)
                audio_data = []
                target_bytes = 16000 * 2 * 1  # 1 second  
                collected = 0
                
                # Use timeout to allow checking running status
                start_time = time.time()
                timeout = 1.0  # 1 second timeout
                
                try:
                    for chunk in mic_stream.generator():
                        if not self.running or self.paused:
                            break
                        if time.time() - start_time > timeout:
                            break
                        audio_data.append(chunk)
                        collected += len(chunk)
                        if collected >= target_bytes:
                            break
                except Exception as e:
                    if self.running:
                        print(f"[Wake] Generator error: {e}")
                    break
                
                if not self.running or self.paused:
                    continue
                
                pcm = b"".join(audio_data)
                if len(pcm) < 1000:  # Too short
                    continue
                    
                try:
                    # Transcribe
                    text = self._asr._run_once(pcm, language=None)
                    text_lower = text.lower().strip()
                    
                    # Check for wake words
                    for keyword in self.keywords:
                        if keyword.lower() in text_lower:
                            print(f"🎯 Wake word detected: '{text}' (matched: '{keyword}')")
                            self._play_beep()
                            
                            # Pause detection temporarily to avoid re-triggering
                            self.pause()
                            on_wake()
                            time.sleep(0.5)  # Brief pause before resuming
                            self.resume()
                            break
                except Exception as e:
                    if self.running:
                        print(f"[Wake] ASR error: {e}")
                        
            except Exception as e:
                if self.running:
                    print(f"[Wake] Loop error: {e}")
                time.sleep(0.1)
                
    def stop(self):
        """Stop wake word detection."""
        self.running = False
