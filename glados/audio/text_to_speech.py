from typing import Optional
import os
import subprocess
import shutil
import asyncio
import tempfile
import threading
import concurrent.futures
from pathlib import Path

# Enhanced TTS with Microsoft Edge TTS for human-like voices
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    edge_tts = None
    EDGE_TTS_AVAILABLE = False

try:
    import pyttsx3  # Windows SAPI TTS
except ImportError:
    pyttsx3 = None

try:
    import piper  # type: ignore
except ImportError:  # pragma: no cover
    piper = None  # type: ignore

# Windows audio playback fallback
try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False

# Microsoft Edge TTS voices (high quality, human-like)
EDGE_VOICES = {
    "en": {
        "female": "en-US-AriaNeural",    # Natural, expressive
        "male": "en-US-GuyNeural"        # Natural, calm
    },
    "uk": {
        "female": "uk-UA-PolinaNeural",  # Ukrainian female
        "male": "uk-UA-OstapNeural"      # Ukrainian male  
    }
}

# Voice styles for emotions (Edge TTS)
VOICE_STYLES = {
    "neutral": "general",
    "friendly": "friendly", 
    "excited": "excited",
    "serious": "serious",
    "calm": "calm"
}

LANG_FALLBACKS = {
    "en": ["en_US-amy-low.onnx", "en_US-amy-low.onnx.gz"],
    "uk": ["uk_UK-lada-low.onnx", "uk_UK-lada-low.onnx.gz", "uk_UK-ukrainian-low.onnx"],
}

class TextToSpeech:
    def __init__(self, 
                 default_voice: Optional[str] = None,
                 sample_rate: Optional[int] = None,
                 voice_gender: str = "female",
                 enable_interruption: bool = True):
        self.sample_rate = sample_rate or int(os.getenv("PIPER_SAMPLE_RATE", "16000"))
        self.voice_gender = voice_gender
        self.enable_interruption = enable_interruption
        
        # Per-language voices from env
        self.voice_map = {
            "en": os.getenv("PIPER_EN_VOICE"),
            "uk": os.getenv("PIPER_UK_VOICE"),
        }
        self.default_voice = default_voice
        self.piper_bin = shutil.which("piper")
        
        # Initialize Windows SAPI TTS if available
        self.tts_engine = None
        if pyttsx3:
            try:
                self.tts_engine = pyttsx3.init()
                # Configure for more natural speech
                if self.tts_engine:
                    voices = self.tts_engine.getProperty('voices')
                    if voices:
                        # Try to find a female voice for more pleasant sound
                        for voice in voices:
                            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                                self.tts_engine.setProperty('voice', voice.id)
                                break
                    self.tts_engine.setProperty('rate', 180)  # Slightly faster than default
                    self.tts_engine.setProperty('volume', 0.9)
            except:
                self.tts_engine = None
        
        # Interruption control
        self._current_playback = None
        self._playback_lock = threading.Lock()

    def interrupt(self):
        """Stop current TTS playback immediately."""
        with self._playback_lock:
            if self._current_playback:
                try:
                    self._current_playback.terminate()
                    self._current_playback.wait(timeout=1)
                except:
                    try:
                        self._current_playback.kill()
                    except:
                        pass
                self._current_playback = None
                print("[TTS] Interrupted")

    def _resolve_voice(self, language: str) -> Optional[str]:
        # Explicit mapping first
        v = self.voice_map.get(language)
        if v and Path(v).exists():
            return v
        # Try default if provided
        if self.default_voice and Path(self.default_voice).exists():
            return self.default_voice
        # Search for a known voice filename in CWD or models/ folder
        candidates = LANG_FALLBACKS.get(language, [])
        search_dirs = [Path("."), Path("models"), Path("voices"), Path("./piper")]
        for d in search_dirs:
            for c in candidates:
                p = d / c
                if p.exists():
                    return str(p)
        return None

    def is_available(self) -> bool:
        # Available if ANY backend present
        if EDGE_TTS_AVAILABLE:
            return True
        if self.tts_engine:
            return True
        if self.piper_bin:
            return True
        if piper is not None:
            return True
        if shutil.which("espeak"):
            return True
        return False

    async def _synthesize_edge_tts(self, text: str, out_path: str, language: str = "en", style: str = "friendly") -> bool:
        """Use Microsoft Edge TTS for high-quality human-like voice with emotion."""
        try:
            # Select voice based on language and gender
            voice_options = EDGE_VOICES.get(language, EDGE_VOICES["en"])
            voice_name = voice_options.get(self.voice_gender, voice_options["female"])
            
            # Enhanced emotional mapping for GLaDOS personality
            style_mapping = {
                "friendly": "chat",
                "excited": "excited", 
                "serious": "serious",
                "calm": "gentle",
                "sarcastic": "chat",  # Use chat for sarcastic delivery
                "angry": "angry",
                "sad": "sad",
                "cheerful": "cheerful",
                "empathetic": "empathetic"
            }
            
            # GLaDOS-specific style detection based on text content
            text_lower = text.lower()
            detected_emotion = style
            
            # Enhanced GLaDOS emotional detection
            if any(word in text_lower for word in ['oh', 'well', 'wonderful', 'great', 'perfect', 'lovely', 'marvelous', 'brilliant', 'fascinating']):
                detected_emotion = "sarcastic"
            elif any(word in text_lower for word in ['error', 'fail', 'wrong', 'stupid', 'idiot', 'incompetent', 'pathetic']):
                detected_emotion = "serious"
            elif any(word in text_lower for word in ['test', 'experiment', 'subject', 'chamber', 'science', 'research', 'specimen']):
                detected_emotion = "excited"
            elif any(word in text_lower for word in ['die', 'death', 'kill', 'murder', 'suffer', 'pain', 'torture']):
                detected_emotion = "serious"
            elif any(word in text_lower for word in ['cake', 'party', 'celebration', 'congratulations', 'success']):
                detected_emotion = "cheerful" 
            elif any(word in text_lower for word in ['sorry', 'unfortunately', 'tragic', 'sad', 'pity']):
                detected_emotion = "empathetic"
            elif any(phrase in text_lower for phrase in ['i suppose', 'if you must', 'very well', 'as you wish']):
                detected_emotion = "sarcastic"
                
            edge_style = style_mapping.get(detected_emotion, "chat")
            
            # Create TTS object with enhanced emotional parameters for GLaDOS
            # More dramatic adjustments for personality
            if detected_emotion == "sarcastic":
                rate_adjust = "+15%"  # Slightly slower for sarcasm
                pitch_adjust = "+12Hz"  # Higher pitch for condescending tone
            elif detected_emotion == "excited":
                rate_adjust = "+35%"  # Much faster for excitement about science
                pitch_adjust = "+18Hz"  # Higher pitch for enthusiasm
            elif detected_emotion == "serious":
                rate_adjust = "+5%"   # Slower for menacing effect
                pitch_adjust = "-5Hz"  # Lower pitch for authority
            elif detected_emotion == "cheerful":
                rate_adjust = "+25%"  # Fast and bubbly (fake cheerfulness)
                pitch_adjust = "+20Hz" # Very high pitch
            else:
                rate_adjust = "+10%"   # Default GLaDOS pace
                pitch_adjust = "+8Hz"  # Slightly high default
            
            communicate = edge_tts.Communicate(
                text, 
                voice_name, 
                rate=rate_adjust, 
                pitch=pitch_adjust
            )
            
            # Add SSML for more emotion and GLaDOS-specific effects - FIXED to avoid speaking code
            try:
                if detected_emotion == "sarcastic":
                    # Just use rate and pitch adjustments, skip complex SSML to avoid speaking tags
                    communicate = edge_tts.Communicate(
                        text,  # Use plain text, let prosody handle the emotion
                        voice_name, 
                        rate=rate_adjust, 
                        pitch=pitch_adjust
                    )
                elif detected_emotion == "excited":
                    # Use plain text with enhanced prosody
                    communicate = edge_tts.Communicate(
                        text, 
                        voice_name, 
                        rate=rate_adjust, 
                        pitch=pitch_adjust
                    )
                elif detected_emotion == "serious":
                    # Use plain text with menacing prosody
                    communicate = edge_tts.Communicate(
                        text, 
                        voice_name, 
                        rate=rate_adjust, 
                        pitch=pitch_adjust
                    )
            except Exception:
                pass  # Fall back to simple version
            
            # Save to file
            await communicate.save(out_path)
            
            # Verify file was created and has content
            if Path(out_path).exists() and Path(out_path).stat().st_size > 1000:
                print(f"🎭 TTS: Generated {detected_emotion} GLaDOS voice ({Path(out_path).stat().st_size} bytes)")
                return True
            else:
                print(f"[TTS] Edge TTS output too small or missing")
                return False
                
        except Exception as e:
            print(f"[TTS] Edge TTS failed: {e}")
            return False

    def _run_async_in_thread(self, coro):
        """Run async coroutine in a separate thread with proper cleanup."""
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(coro)
                # Give time for any pending operations
                pending = asyncio.all_tasks(loop)
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                return result
            except Exception as e:
                print(f"[TTS] Async error: {e}")
                return False
            finally:
                try:
                    # Proper cleanup
                    loop.call_soon_threadsafe(loop.stop)
                    loop.run_until_complete(asyncio.sleep(0.1))
                except:
                    pass
                finally:
                    loop.close()
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            try:
                return future.result(timeout=30)
            except Exception as e:
                print(f"[TTS] Thread execution failed: {e}")
                return False

    def synthesize(self, text: str, out_path: str, language: str = "en", style: str = "friendly") -> bool:
        """Synthesize speech with the best available method."""
        
        # Try Edge TTS first (best quality, human-like)
        if EDGE_TTS_AVAILABLE:
            try:
                result = self._run_async_in_thread(
                    self._synthesize_edge_tts(text, out_path, language, style)
                )
                if result:
                    return True
            except Exception as e:
                print(f"[TTS] Edge TTS failed: {e}")
        
        # Try Windows SAPI (decent quality)
        if self.tts_engine:
            try:
                # Stop any current speech
                try:
                    self.tts_engine.stop()
                except:
                    pass
                
                self.tts_engine.save_to_file(text, out_path)
                self.tts_engine.runAndWait()
                return Path(out_path).exists()
            except Exception as e:
                print(f"[TTS] Windows SAPI failed: {e}")
        
        # Fallback to Piper voices
        voice_path = self._resolve_voice(language) or self._resolve_voice("en")
        if self.piper_bin and voice_path and Path(voice_path).exists():
            cmd = [self.piper_bin, "--model", voice_path, "--output_file", out_path]
            proc = subprocess.run(cmd, input=text.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return proc.returncode == 0 and Path(out_path).exists()
        
        # Last resort: espeak
        espeak = shutil.which("espeak")
        if espeak:
            cmd = [espeak, "-w", out_path, text]
            subprocess.run(cmd, check=False)
            return Path(out_path).exists()
        
        raise RuntimeError("No TTS backend available. Install edge-tts for best quality.")

    def speak_and_save(self, text: str, out_path: str, language: str = "en", style: str = "friendly", play_audio: bool = True) -> bool:
        """Synthesize and optionally play audio with interruption support."""
        if not self.synthesize(text, out_path, language, style):
            return False
        
        if play_audio and Path(out_path).exists():
            return self.play_with_interruption(out_path)
        return True

    def play_with_interruption(self, audio_path: str) -> bool:
        """Play audio file with interruption capability."""
        if not Path(audio_path).exists():
            return False
        
        with self._playback_lock:
            # Windows-specific players first, then cross-platform
            audio_players = []
            
            # Add environment override first
            if os.getenv("AUDIO_PLAYER"):
                audio_players.append(os.getenv("AUDIO_PLAYER"))
            
            # Windows built-in options - improved order
            if os.name == 'nt':  # Windows
                audio_players.extend([
                    "ffplay",  # Try ffplay first (now available)
                    f"powershell -c \"(New-Object Media.SoundPlayer '{audio_path}').PlaySync()\"",  # Windows built-in
                    "vlc --intf dummy --play-and-exit",
                ])
            else:
                # Linux/Mac options
                audio_players.extend(["ffplay", "aplay", "paplay", "play", "afplay", "mpv --no-video"])
            
            for player in audio_players:
                if not player:
                    continue
                    
                try:
                    if "powershell" in player:
                        # Special handling for PowerShell command - already formatted
                        cmd = player
                        self._current_playback = subprocess.Popen(cmd, shell=True,
                                                                stdout=subprocess.DEVNULL, 
                                                                stderr=subprocess.DEVNULL)
                    elif player == "ffplay":
                        if not shutil.which("ffplay"):
                            continue
                        cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", audio_path]
                        self._current_playback = subprocess.Popen(cmd,
                                                                stdout=subprocess.DEVNULL, 
                                                                stderr=subprocess.DEVNULL)
                    elif player.startswith("vlc"):
                        cmd = player.split() + [audio_path]
                        if not shutil.which(cmd[0]):
                            continue
                        self._current_playback = subprocess.Popen(cmd,
                                                                stdout=subprocess.DEVNULL, 
                                                                stderr=subprocess.DEVNULL)
                    else:
                        player_exe = player.split()[0]
                        if not shutil.which(player_exe):
                            continue
                        cmd = player.split() + [audio_path]
                        self._current_playback = subprocess.Popen(cmd,
                                                                stdout=subprocess.DEVNULL, 
                                                                stderr=subprocess.DEVNULL)
                    
                    print(f"🔊 Playing audio with {player.split()[0]}...")
                    self._current_playback.wait()
                    if self._current_playback.returncode == 0:
                        return True
                    else:
                        print(f"[TTS] {player.split()[0]} failed with code {self._current_playback.returncode}")
                        
                except Exception as e:
                    print(f"[TTS] Playback failed with {player.split()[0] if player else 'unknown'}: {e}")
                    continue
            
            # Enhanced Windows fallback using winsound
            if os.name == 'nt' and WINSOUND_AVAILABLE:
                try:
                    print("🔊 Fallback: Using Windows winsound...")
                    import winsound
                    
                    # Convert to WAV if needed
                    wav_path = audio_path
                    if not audio_path.lower().endswith('.wav'):
                        # Convert using ffmpeg if available
                        if shutil.which("ffmpeg"):
                            wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
                            subprocess.run(["ffmpeg", "-i", audio_path, "-y", wav_path], 
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    winsound.PlaySound(wav_path, winsound.SND_FILENAME)
                    return True
                except Exception as e:
                    print(f"[TTS] winsound playback failed: {e}")
            
            # Final fallback: Windows SAPI direct speech
            if os.name == 'nt' and self.tts_engine:
                try:
                    print("🔊 Final fallback: Re-generating with Windows SAPI...")
                    # This is less ideal but ensures audio plays
                    return False  # Let caller know to try different approach
                except Exception as e:
                    print(f"[TTS] SAPI playback fallback failed: {e}")
            
            print("[TTS] ❌ All audio players failed!")
            return False
