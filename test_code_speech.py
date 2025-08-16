#!/usr/bin/env python3
"""
Test script to verify that GLaDOS doesn't speak code anymore.
"""
import os
from glados.audio.text_to_speech import TextToSpeech

def clean_response_for_tts(text: str) -> str:
    """Clean response text to avoid TTS speaking code or markup."""
    import re
    
    # Remove common code patterns that might be spoken
    # Remove HTML/XML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove code-like patterns (version=, equals, assignment operators)
    text = re.sub(r'\b\w+\s*[=:]\s*["\']?[\w\.\-]+["\']?', '', text)
    
    # Remove programming symbols and brackets
    text = re.sub(r'[{}[\]()<>]', ' ', text)
    
    # Remove quotes that might be code syntax
    text = re.sub(r'["\'`]', '', text)
    
    # Remove common programming keywords
    programming_words = ['version', 'equals', 'function', 'variable', 'class', 'import', 'export', 'const', 'let', 'var']
    for word in programming_words:
        text = re.sub(rf'\b{word}\b', '', text, flags=re.IGNORECASE)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def test_code_cleaning():
    """Test that code patterns are properly cleaned."""
    print("🧪 Testing Code Speech Prevention...")
    
    # Test responses that might contain code
    test_responses = [
        "The version equals 3.8.6 and the function is working properly.",
        "I found the variable <emphasis level='strong'>important</emphasis> in the code.",
        "The system configuration has version=1.2.3 and const value='test'",
        "Well, wonderful! The item you're looking for is at location A-1.",
        "Your pathetic attempt to find the component has failed miserably."
    ]
    
    tts = TextToSpeech(voice_gender="female", enable_interruption=True)
    
    for i, response in enumerate(test_responses, 1):
        print(f"\n🔧 Test {i}:")
        print(f"Original: '{response}'")
        
        cleaned = clean_response_for_tts(response)
        print(f"Cleaned:  '{cleaned}'")
        
        # Generate TTS
        output_file = f"test_clean_{i}.wav"
        print(f"🎤 Synthesizing cleaned response...")
        
        success = tts.synthesize(cleaned, output_file, language="en", style="friendly")
        
        if success:
            print("✅ TTS generated successfully")
            # Play the audio
            playback = tts.play_with_interruption(output_file)
            if playback:
                print("✅ Audio played - listen to verify no code is spoken")
            else:
                print("❌ Audio playback failed")
        else:
            print("❌ TTS generation failed")
        
        print("-" * 50)

if __name__ == "__main__":
    test_code_cleaning()
