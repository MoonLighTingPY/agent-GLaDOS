"""
Text-to-Speech Module

Provides TTS functionality with GLaDOS voice effects for the AI assistant.
"""

from .tts_core import TTSCore, TTSEngine, VoiceSettings, TTSResult, VoiceGender
from .vocoder_core import GLaDOSVocoder

__all__ = [
    'TTSCore',
    'TTSEngine', 
    'VoiceSettings',
    'TTSResult',
    'VoiceGender',
    'GLaDOSVocoder'
]