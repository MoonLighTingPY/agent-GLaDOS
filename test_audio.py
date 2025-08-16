# d:\Projects\agent-GLaDOS\test_audio.py
"""Quick test script for audio playback functionality."""

import os
from glados.audio.text_to_speech import TextToSpeech

def test_tts():
    print("🧪 Testing TTS and audio playback...")
    
    tts = TextToSpeech(voice_gender="female", enable_interruption=True)
    
    if not tts.is_available():
        print("❌ TTS not available")
        return
    
    print("✅ TTS is available")
    
    test_text = "Hello, this is GLaDOS testing the audio systems. If you can hear this, the audio playback is working correctly."
    output_file = "test_response.wav"
    
    print(f"🎵 Synthesizing: '{test_text[:50]}...'")
    success = tts.synthesize(test_text, output_file, language="en", style="friendly")
    
    if success:
        print("✅ Audio synthesis successful")
        print(f"📁 Audio file saved: {output_file}")
        
        print("🔊 Testing playback...")
        playback_success = tts.play_with_interruption(output_file)
        
        if playback_success:
            print("✅ Audio playback successful")
        else:
            print("❌ Audio playback failed")
            print("💡 Try restarting your terminal to use the new ffplay installation")
    else:
        print("❌ Audio synthesis failed")

if __name__ == "__main__":
    test_tts()
