"""
Text-to-Speech Core Module

Provides unified interface for lightweight TTS engines optimized for Raspberry Pi.
Supports pyttsx3 and gTTS with automatic fallbacks and multi-language support.
"""

import os
import tempfile
import pygame
import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Import TTS engines with fallbacks
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
    logging.info("pyttsx3 is available")
except ImportError:
    PYTTSX3_AVAILABLE = False
    logging.warning("pyttsx3 not available")

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
    logging.info("gTTS is available")
except ImportError:
    GTTS_AVAILABLE = False
    logging.warning("gTTS not available")

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    logging.warning("soundfile not available - some features may not work")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("numpy not available - GLaDOS effects may not work")


class TTSEngine(Enum):
    """Supported lightweight TTS engines"""
    PYTTSX3 = "pyttsx3"    # Offline, lightweight, fast
    GTTS = "gtts"          # Online, good quality
    AUTO = "auto"          # Auto-select best available


class VoiceGender(Enum):
    """Voice gender options"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


@dataclass
class VoiceSettings:
    """Voice configuration settings"""
    engine: TTSEngine = TTSEngine.AUTO
    language: str = "auto"   # Auto-detect language or use specific code like "uk", "en", "ru"
    speed: float = 1.0       # Speech speed multiplier
    volume: float = 0.9      # Volume level (0.0 to 1.0)
    voice_name: Optional[str] = None  # Specific voice name
    gender: VoiceGender = VoiceGender.FEMALE


@dataclass
class TTSResult:
    """Result of TTS operation"""
    success: bool
    audio_file_path: Optional[str] = None
    audio_data: Optional[np.ndarray] = None
    sample_rate: Optional[int] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None


class TTSCore:
    """
    Lightweight Text-to-Speech class optimized for Raspberry Pi.
    
    Focuses on fast, efficient TTS engines with GLaDOS voice effects
    applied via post-processing for better performance.
    Supports multiple languages including Ukrainian.
    """
    
    def __init__(self, settings: Optional[VoiceSettings] = None):
        self.settings = settings or VoiceSettings()
        self.temp_dir = Path(tempfile.gettempdir()) / "glados_tts"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Language detection patterns
        self.language_patterns = {
            'uk': re.compile(r'[а-яіїєґ]', re.IGNORECASE),  # Ukrainian
            'ru': re.compile(r'[а-яё]', re.IGNORECASE),     # Russian
            'en': re.compile(r'[a-z]', re.IGNORECASE),      # English
        }
        
        # Initialize pygame mixer for audio playbook
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            logging.info("Pygame mixer initialized successfully")
        except pygame.error as e:
            logging.warning(f"Pygame mixer init failed: {e}")
        
        # Initialize engines
        self.engines = {}
        self._init_engines()
        
        # Select best engine
        self.current_engine = self._select_engine()
        logging.info(f"TTS Core initialized with engine: {self.current_engine}")
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of the input text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code (uk, ru, en) or 'en' as fallback
        """
        if not text.strip():
            return 'en'
        
        # Count characters for each language
        lang_scores = {}
        for lang_code, pattern in self.language_patterns.items():
            matches = pattern.findall(text)
            lang_scores[lang_code] = len(matches)
        
        # Return language with most matches
        detected_lang = max(lang_scores, key=lang_scores.get)
        
        # If no clear winner or very few characters, default to English
        if lang_scores[detected_lang] < 3:
            detected_lang = 'en'
        
        logging.info(f"Detected language: {detected_lang} (scores: {lang_scores})")
        return detected_lang
    
    def _init_engines(self):
        """Initialize available lightweight TTS engines"""
        # Initialize pyttsx3 (offline, fast, lightweight)
        if PYTTSX3_AVAILABLE:
            try:
                engine = pyttsx3.init()
                if engine:
                    self.engines[TTSEngine.PYTTSX3] = engine
                    self._configure_pyttsx3(engine)
                    logging.info("pyttsx3 initialized successfully")
            except Exception as e:
                logging.warning(f"pyttsx3 init failed: {e}")
        
        # gTTS (online, good quality, but requires internet)
        if GTTS_AVAILABLE:
            self.engines[TTSEngine.GTTS] = True
            logging.info("gTTS available")
    
    def _select_engine(self) -> TTSEngine:
        """Select the best available engine"""
        if self.settings.engine != TTSEngine.AUTO:
            if self.settings.engine in self.engines:
                return self.settings.engine
            else:
                logging.warning(f"Requested engine {self.settings.engine} not available, falling back")
        
        # Auto-select priority: gTTS > pyttsx3 (gTTS has better Ukrainian support)
        if TTSEngine.GTTS in self.engines:
            return TTSEngine.GTTS
        elif TTSEngine.PYTTSX3 in self.engines:
            return TTSEngine.PYTTSX3
        else:
            raise RuntimeError("No TTS engines available!")
    
    def _configure_pyttsx3(self, engine):
        """Configure pyttsx3 engine settings for optimal Pi performance"""
        try:
            # Set voice - prioritize system voices for speed
            voices = engine.getProperty('voices')
            if voices:
                voice_name = os.getenv('VOICE_NAME', self.settings.voice_name)
                
                # First try to find specific voice
                if voice_name:
                    for voice in voices:
                        if voice_name.lower() in voice.name.lower():
                            engine.setProperty('voice', voice.id)
                            logging.info(f"Selected voice: {voice.name}")
                            break
                # Otherwise find by gender
                elif self.settings.gender == VoiceGender.FEMALE:
                    female_voices = [v for v in voices if 'female' in v.name.lower() 
                                   or 'zira' in v.name.lower() or 'hazel' in v.name.lower()]
                    if female_voices:
                        engine.setProperty('voice', female_voices[0].id)
                        logging.info(f"Selected female voice: {female_voices[0].name}")
                elif self.settings.gender == VoiceGender.MALE:
                    male_voices = [v for v in voices if 'male' in v.name.lower() 
                                 or 'david' in v.name.lower() or 'mark' in v.name.lower()]
                    if male_voices:
                        engine.setProperty('voice', male_voices[0].id)
                        logging.info(f"Selected male voice: {male_voices[0].name}")
            
            # Optimize speech rate for Pi (faster processing)
            rate = engine.getProperty('rate')
            # GLaDOS speaks methodically, so slightly slower base rate
            optimal_rate = int(rate * self.settings.speed * 0.85)  
            engine.setProperty('rate', optimal_rate)
            
            # Set volume
            engine.setProperty('volume', self.settings.volume)
            
            logging.info(f"pyttsx3 configured: rate={optimal_rate}, volume={self.settings.volume}")
            
        except Exception as e:
            logging.warning(f"pyttsx3 configuration failed: {e}")
    
    def synthesize_to_file(self, text: str, output_path: Optional[str] = None, language: Optional[str] = None) -> TTSResult:
        """
        Synthesize text to audio file using lightweight engines.
        
        Args:
            text: Text to synthesize
            output_path: Output file path (auto-generated if None)
            language: Language code override (if None, will auto-detect or use settings)
            
        Returns:
            TTSResult with file path and audio data
        """
        if not output_path:
            output_path = self.temp_dir / f"tts_{hash(text)}.wav"
        
        # Determine language
        if language:
            target_language = language
        elif self.settings.language == "auto":
            target_language = self.detect_language(text)
        else:
            target_language = self.settings.language
        
        logging.info(f"Synthesizing text in language: {target_language}")
        
        try:
            if self.current_engine == TTSEngine.PYTTSX3:
                return self._pyttsx3_synthesize(text, str(output_path), target_language)
            elif self.current_engine == TTSEngine.GTTS:
                return self._gtts_synthesize(text, str(output_path), target_language)
            else:
                return TTSResult(success=False, error_message="No engine selected")
        
        except Exception as e:
            return TTSResult(success=False, error_message=f"Synthesis failed: {e}")
    
    def _pyttsx3_synthesize(self, text: str, output_path: str, language: str) -> TTSResult:
        """Synthesize using pyttsx3 - optimized for speed (limited language support)"""
        try:
            engine = self.engines[TTSEngine.PYTTSX3]
            
            # Clean up text for better synthesis
            clean_text = self._clean_text_for_synthesis(text, language)
            
            # Note: pyttsx3 has limited language support, mostly depends on system voices
            if language in ['uk', 'ru'] and language != 'en':
                logging.warning(f"pyttsx3 has limited support for language '{language}'. Consider using gTTS for better quality.")
            
            # Save to file
            engine.save_to_file(clean_text, output_path)
            engine.runAndWait()
            
            # Verify file was created
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                return TTSResult(success=False, error_message="pyttsx3 failed to generate audio file")
            
            # Load audio data if soundfile is available
            audio_data = None
            sample_rate = None
            duration = None
            
            if SOUNDFILE_AVAILABLE:
                try:
                    audio_data, sample_rate = sf.read(output_path)
                    duration = len(audio_data) / sample_rate if len(audio_data) > 0 else 0
                except Exception as e:
                    logging.warning(f"Failed to load audio metadata: {e}")
            
            return TTSResult(
                success=True,
                audio_file_path=output_path,
                audio_data=audio_data,
                sample_rate=sample_rate,
                duration=duration
            )
        
        except Exception as e:
            return TTSResult(success=False, error_message=f"pyttsx3 synthesis failed: {e}")
    
    def _gtts_synthesize(self, text: str, output_path: str, language: str) -> TTSResult:
        """Synthesize using gTTS - requires internet but supports many languages including Ukrainian"""
        try:
            # Clean up text for better synthesis
            clean_text = self._clean_text_for_synthesis(text, language)
            
            # Map language codes for gTTS
            gtts_lang_map = {
                'uk': 'uk',  # Ukrainian
                'ru': 'ru',  # Russian  
                'en': 'en',  # English
            }
            
            gtts_lang = gtts_lang_map.get(language, 'en')
            logging.info(f"Using gTTS with language: {gtts_lang}")
            
            # Create gTTS object with optimized settings
            tts = gTTS(
                text=clean_text, 
                lang=gtts_lang, 
                slow=False,  # Fast speech for GLaDOS
                tld='com'    # Use .com for consistency
            )
            
            # Save to temporary mp3, then convert to wav if possible
            mp3_path = output_path.replace('.wav', '.mp3')
            tts.save(mp3_path)
            
            # If soundfile is available, convert to wav for consistency
            if SOUNDFILE_AVAILABLE:
                try:
                    audio_data, sample_rate = sf.read(mp3_path)
                    sf.write(output_path, audio_data, sample_rate)
                    os.remove(mp3_path)  # Clean up mp3
                    
                    return TTSResult(
                        success=True,
                        audio_file_path=output_path,
                        audio_data=audio_data,
                        sample_rate=sample_rate,
                        duration=len(audio_data) / sample_rate
                    )
                except Exception as e:
                    logging.warning(f"WAV conversion failed, using MP3: {e}")
            
            # Fall back to mp3 if wav conversion fails
            return TTSResult(
                success=True,
                audio_file_path=mp3_path,
                audio_data=None,
                sample_rate=None,
                duration=None
            )
        
        except Exception as e:
            return TTSResult(success=False, error_message=f"gTTS synthesis failed: {e}")
    
    def _clean_text_for_synthesis(self, text: str, language: str) -> str:
        """Clean and optimize text for TTS synthesis based on language"""
        # Remove or replace problematic characters
        clean_text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Language-specific text cleaning
        if language == 'uk':  # Ukrainian
            # Ukrainian-specific abbreviations and replacements
            abbreviations = {
                'др.': 'доктор',
                'пан.': 'пан',
                'п.': 'пан',
                'проф.': 'професор',
                'тощо': 'і так далі',
            }
        elif language == 'ru':  # Russian
            # Russian-specific abbreviations
            abbreviations = {
                'др.': 'доктор',
                'г-н': 'господин',
                'проф.': 'профессор',
                'и т.д.': 'и так далее',
            }
        else:  # English and others
            abbreviations = {
                'Dr.': 'Doctor',
                'Mr.': 'Mister',
                'Mrs.': 'Missus',
                'Ms.': 'Miss',
                'Prof.': 'Professor',
                'etc.': 'etcetera',
                'vs.': 'versus',
                'e.g.': 'for example',
                'i.e.': 'that is',
            }
        
        for abbr, full in abbreviations.items():
            clean_text = clean_text.replace(abbr, full)
        
        # Limit length for better processing on Pi
        if len(clean_text) > 500:
            # Split by sentences (different punctuation for different languages)
            if language in ['uk', 'ru']:
                sentences = clean_text.split('. ')
            else:
                sentences = clean_text.split('. ')
            
            if len(sentences) > 1:
                clean_text = '. '.join(sentences[:3]) + '.'  # Keep first 3 sentences
        
        return clean_text.strip()
    
    def speak(self, text: str, use_vocoder: bool = False, language: Optional[str] = None) -> bool:
        """
        Speak text immediately (synthesize and play).
        
        Args:
            text: Text to speak
            use_vocoder: Apply GLaDOS vocoder effect
            language: Language code override
            
        Returns:
            True if successful, False otherwise
        """
        result = self.synthesize_to_file(text, language=language)
        
        if not result.success:
            logging.error(f"TTS synthesis failed: {result.error_message}")
            return False
        
        try:
            audio_file = result.audio_file_path
            
            # Apply GLaDOS vocoder if requested
            if use_vocoder and NUMPY_AVAILABLE and SOUNDFILE_AVAILABLE:
                try:
                    from .vocoder_core import GLaDOSVocoder
                    vocoder = GLaDOSVocoder()
                    vocoded_path = vocoder.apply_glados_effect(audio_file)
                    if vocoded_path:
                        audio_file = vocoded_path
                        logging.info("GLaDOS vocoder effect applied successfully")
                except ImportError:
                    logging.warning("GLaDOS vocoder not available, playing without effects")
                except Exception as e:
                    logging.warning(f"GLaDOS vocoder failed: {e}, playing without effects")
            elif use_vocoder:
                logging.warning("Vocoder dependencies not available, playing without effects")
            
            # Play audio
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.wait(50)  # Smaller wait interval for responsiveness
            
            return True
        
        except Exception as e:
            logging.error(f"Audio playback failed: {e}")
            return False
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices for current engine"""
        voices = []
        
        try:
            if self.current_engine == TTSEngine.PYTTSX3:
                engine = self.engines[TTSEngine.PYTTSX3]
                voice_objects = engine.getProperty('voices')
                if voice_objects:
                    voices = [f"{voice.name} ({voice.id})" for voice in voice_objects]
            elif self.current_engine == TTSEngine.GTTS:
                voices = ["Google TTS (online) - Supports: Ukrainian, Russian, English, and 100+ languages"]
        
        except Exception as e:
            logging.warning(f"Failed to get voices: {e}")
        
        return voices
    
    def change_voice(self, voice_name: str):
        """Change the voice for the current engine"""
        self.settings.voice_name = voice_name
        
        if self.current_engine == TTSEngine.PYTTSX3:
            try:
                engine = self.engines[TTSEngine.PYTTSX3]
                voices = engine.getProperty('voices')
                for voice in voices:
                    if voice_name.lower() in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        logging.info(f"Voice changed to: {voice.name}")
                        return
                logging.warning(f"Voice '{voice_name}' not found")
            except Exception as e:
                logging.error(f"Failed to change voice: {e}")
    
    def set_language(self, language: str):
        """Set the default language for TTS"""
        self.settings.language = language
        logging.info(f"TTS language set to: {language}")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about current TTS engine"""
        info = {
            "engine": self.current_engine.value,
            "available_engines": [engine.value for engine in self.engines.keys()],
            "offline_capable": self.current_engine == TTSEngine.PYTTSX3,
            "internet_required": self.current_engine == TTSEngine.GTTS,
            "vocoder_available": NUMPY_AVAILABLE and SOUNDFILE_AVAILABLE,
            "current_language": self.settings.language,
            "supported_languages": {
                "pyttsx3": ["en", "system dependent"],
                "gtts": ["uk", "ru", "en", "and 100+ others"]
            }
        }
        
        if self.current_engine == TTSEngine.PYTTSX3:
            try:
                engine = self.engines[TTSEngine.PYTTSX3]
                info.update({
                    "current_rate": engine.getProperty('rate'),
                    "current_volume": engine.getProperty('volume'),
                    "voice_count": len(engine.getProperty('voices') or [])
                })
            except:
                pass
        
        return info