import os
from dotenv import load_dotenv
import time
import sys
import signal
import threading
import sounddevice as sd
from modules.wake_word import WakeWordDetector
from modules.asr import SpeechRecognizer
from modules.tts import TextToSpeech
from modules.assistant import Assistant


def on_wake():
    print("Wake word detected!", flush=True)
    # Stop wake detection to process command
    wake.stop()
    # Ensure audio streams are closed
    try:
        sd.stop()
    except Exception:
        pass
    # Give the OS time to release audio device
    time.sleep(0.1)
    # Prompt user and process command
    try:
        tts.speak("Yes? How can I help?")
    except Exception as e:
        print(f"on_wake: tts.speak() raised: {e}", flush=True)

    try:
        assistant.process()
    except Exception as e:
        print(f"on_wake: assistant.process() raised: {e}", flush=True)

    # restart wake word detection
    wake.start(on_wake)

if __name__ == "__main__":
    load_dotenv()
    # Debug: print loaded environment configuration
    keyword_env = os.getenv("PORCUPINE_KEYWORD_PATH")
    model_env = os.getenv("VOSK_MODEL_PATH")
    print(f"PORCUPINE_KEYWORD_PATH: {keyword_env}")
    print(f"VOSK_MODEL_PATH: {model_env}")
    print(f"VOICE_NAME: {os.getenv('VOICE_NAME')}")
    print(f"SYSTEM_PROMPT: {os.getenv('SYSTEM_PROMPT')}")

    # Load configuration from environment
    keyword = os.path.join(os.getcwd(), keyword_env)
    print(f"Using keyword file at: {keyword}, exists: {os.path.exists(keyword)}")
    wake = WakeWordDetector(keyword_path=keyword)
    vosk_path = os.path.join(os.getcwd(), model_env)
    print(f"Using VOSK model at: {vosk_path}, exists: {os.path.exists(vosk_path)}")
    recognizer = SpeechRecognizer(model_path=vosk_path)
    tts = TextToSpeech(voice_name=os.getenv("VOICE_NAME", "Zira"))
    assistant = Assistant(tts, recognizer, system_prompt=os.getenv("SYSTEM_PROMPT"))
    # Custom SIGINT handler removed to avoid unexpected exits

    wake.start(on_wake)
    # Keep running until interrupted
    while True:
        time.sleep(1)
