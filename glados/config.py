from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class AppConfig:
    grog_api_key: str
    grog_base_url: str = "https://api.grog.cloud/v1"
    grog_model: str = "llama-3.1-8b-instant"
    whisper_model: str = "tiny"
    wake_keyword_path: Optional[str] = None
    picovoice_access_key: Optional[str] = None
    piper_en_voice: Optional[str] = None
    piper_uk_voice: Optional[str] = None
    piper_sample_rate: int = 16000
    auto_play_tts: bool = True
    tts_voice_gender: str = "female"  # female/male
    tts_style: str = "friendly"       # friendly/excited/serious/calm
    enable_interruption: bool = True
    use_simple_wake_word: bool = True
    wake_words: str = "hey glados,гей глендос,слухай,listen"
    vad_enabled: bool = True
    vad_energy_threshold: float = 200.0      # Lower threshold for better sensitivity  
    vad_silence_duration: float = 0.5        # Much shorter silence duration for faster response
    vad_min_duration: float = 0.3            # Shorter minimum duration
    vad_max_duration: float = 10.0           # Max duration for complete thoughts
    llm_max_tokens: int = 150            # shorter responses

    @staticmethod
    def load() -> "AppConfig":
        def getenv_bool(name: str, default: bool) -> bool:
            v = os.getenv(name)
            if v is None:
                return default
            return v.strip().lower() in {"1", "true", "yes", "on"}
        return AppConfig(
            grog_api_key=os.getenv("GROG_CLOUD_API_KEY", ""),
            grog_base_url=os.getenv("GROG_API_URL", "https://api.groq.com/openai/v1/chat/completions"),
            grog_model=os.getenv("GROG_MODEL", "llama-3.1-8b-instant"),
            whisper_model=os.getenv("WHISPER_MODEL", "tiny"),
            wake_keyword_path=os.getenv("WAKEWORD_KEYWORD_PATH"),
            picovoice_access_key=os.getenv("PICOVOICE_ACCESS_KEY"),
            piper_en_voice=os.getenv("PIPER_EN_VOICE"),
            piper_uk_voice=os.getenv("PIPER_UK_VOICE"),
            piper_sample_rate=int(os.getenv("PIPER_SAMPLE_RATE", "16000")),
            auto_play_tts=getenv_bool("AUTO_PLAY_TTS", True),
            tts_voice_gender=os.getenv("TTS_VOICE_GENDER", "female"),
            tts_style=os.getenv("TTS_STYLE", "friendly"),
            enable_interruption=getenv_bool("ENABLE_INTERRUPTION", True),
            use_simple_wake_word=getenv_bool("USE_SIMPLE_WAKE_WORD", True),
            wake_words=os.getenv("WAKE_WORDS", "hey glados,гей глендос,слухай,listen"),
            vad_enabled=getenv_bool("VAD_ENABLED", True),
            vad_energy_threshold=float(os.getenv("VAD_ENERGY_THRESHOLD", "200")),
            vad_silence_duration=float(os.getenv("VAD_SILENCE_DURATION", "0.5")),
            vad_min_duration=float(os.getenv("VAD_MIN_DURATION", "0.3")),
            vad_max_duration=float(os.getenv("VAD_MAX_DURATION", "12.0")),
            llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", "150")),
        )

    def validate(self):
        if not self.grog_api_key:
            raise SystemExit("GROG_CLOUD_API_KEY missing in environment/.env")
