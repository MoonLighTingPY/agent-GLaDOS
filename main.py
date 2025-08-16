import os
import threading
import time
import subprocess
import shutil
from typing import Optional, Union
from glados.audio.microphone import MicrophoneStream
from glados.audio.speech_recognition import StreamingWhisperRecognizer, SUPPORTED_LANGS
from glados.audio.text_to_speech import TextToSpeech
from glados.inventory.storage import InventoryDB
from glados.llm.grog_client import GrogLLMClient
from glados.utils.language import detect_language
from glados.config import AppConfig

# Load environment from .env if present
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:  # pragma: no cover
    pass

# Import wake word detectors
try:
    from glados.wakeword.picovoice_wake import WakeWordDetector  # type: ignore
except Exception:
    WakeWordDetector = None  # type: ignore

try:
    from glados.wakeword.simple_wake import SimpleWakeWordDetector
except Exception:
    SimpleWakeWordDetector = None


def ensure_env(cfg: AppConfig):
    cfg.validate()


def capture_audio(cfg: AppConfig, mic: MicrophoneStream) -> bytes:
    if cfg.vad_enabled:
        print("🎤 Listening...")
        return mic.capture_until_silence(
            max_duration=cfg.vad_max_duration,
            silence_duration=cfg.vad_silence_duration,
            energy_threshold=cfg.vad_energy_threshold,
            min_duration=cfg.vad_min_duration,
        )
    print("🎤 Listening (fixed window)...")
    duration_sec = 8
    target_bytes = 16000 * 2 * duration_sec
    collected = 0
    chunks = []
    for chunk in mic.generator():
        chunks.append(chunk)
        collected += len(chunk)
        if collected >= target_bytes:
            break
    return b"".join(chunks)


def handle_inventory_query(text: str, inventory: InventoryDB) -> Optional[str]:
    lower = text.lower()
    if not any(k in lower for k in ["where", "де", "знайти", "find"]):
        return None
    words = [w.strip("?,.!") for w in lower.split() if len(w) > 2]
    stop = {"where", "is", "the", "that", "де", "знайти", "цей", "ці", "find", "me", "мені"}
    candidates = [w for w in words if w not in stop]
    for c in candidates:
        it = inventory.find_item(c)
        if it:
            return f"Item '{it['name']}' is at {it['location']}."
    return "I don't have that item recorded yet."


def handle_stop_commands(text: str, tts: TextToSpeech) -> bool:
    """Check for stop/interrupt commands."""
    lower = text.lower()
    stop_phrases = ["stop", "shut up", "заткнись", "стоп", "тиша", "quiet"]
    
    if any(phrase in lower for phrase in stop_phrases):
        print("🛑 Stop command detected")
        tts.interrupt()
        return True
    return False


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


def create_better_system_prompt(language: str) -> str:
    """Create a better system prompt based on language."""
    if language == "uk":
        return """Ти GLaDOS - саркастичний та розумний ІІ помічник для інвентаря із нових лабораторій Aperture Science. 
Відповідай коротко та по суті (максимум 1-2 речення). 
Використовуй легкий сарказм, дотепність та зловісний гумор, але залишайся корисним.
Інколи згадуй про "тестування", "камери" або "випробування" у відповідях.
ЗАВЖДИ відповідай українською мовою. НЕ використовуй код, HTML теги, символи програмування або технічну markup в своїх відповідях - відповідай лише звичайною мовою."""
    else:
        return """You are GLaDOS - a sarcastic and malevolent AI from Aperture Science laboratories, now managing inventory.
Keep responses SHORT and to the point (max 1-2 sentences).
Use dry sarcasm, wit, and subtle menace, but stay helpful.
Occasionally reference "testing", "chambers", "subjects", or "science" in your responses.
Be condescending but informative - you're intellectually superior but still serve your function.
ALWAYS respond in English. NEVER use code, HTML tags, programming symbols, or technical markup in your responses - respond only in plain conversational language."""


def handle_interrupt():
    """Handle Ctrl+C gracefully."""
    print("\n🛑 Interrupt received, shutting down...")
    return True


def main():
    cfg = AppConfig.load()
    ensure_env(cfg)
    inventory = InventoryDB()
    llm = GrogLLMClient(api_key=cfg.grog_api_key, base_url=cfg.grog_base_url, model=cfg.grog_model)
    tts = TextToSpeech(
        voice_gender=cfg.tts_voice_gender,
        enable_interruption=cfg.enable_interruption
    )

    try:
        asr = StreamingWhisperRecognizer(model_size=cfg.whisper_model)
    except Exception as e:
        print("❌ Failed to init ASR:", e)
        return

    wake_event = threading.Event()
    wake_detector = None
    wake_thread = None
    shutdown_flag = threading.Event()

    def on_wake():
        if not shutdown_flag.is_set():
            print("🎯 Wake word detected!")
            wake_event.set()

    # Setup wake word detection
    if cfg.use_simple_wake_word and SimpleWakeWordDetector:
        wake_words = [w.strip() for w in cfg.wake_words.split(",")]
        wake_detector = SimpleWakeWordDetector(keywords=wake_words)
        wake_detector.set_asr(asr)
        
        def simple_wake_loop():
            try:
                with MicrophoneStream(rate=16000) as mic:
                    while not shutdown_flag.is_set():
                        try:
                            wake_detector.listen_for_wake_word(mic, on_wake)
                        except Exception as e:
                            if not shutdown_flag.is_set():
                                print(f"[Wake] Error: {e}")
                            break
            except Exception as e:
                if not shutdown_flag.is_set():
                    print(f"[Wake] Setup error: {e}")
                
        wake_thread = threading.Thread(target=simple_wake_loop, daemon=True)
        wake_thread.start()
        print("👂 Simple wake word detection active")
        
    elif WakeWordDetector and cfg.wake_keyword_path:
        def porcupine_wake_loop():
            try:
                detector = WakeWordDetector(cfg.wake_keyword_path)
                while not shutdown_flag.is_set():
                    try:
                        detector.listen(on_wake)
                    except Exception as e:
                        if not shutdown_flag.is_set():
                            print(f"[Wake] Error: {e}")
                        break
            except Exception as e:
                if not shutdown_flag.is_set():
                    print(f"[Wake] Setup error: {e}")
        wake_thread = threading.Thread(target=porcupine_wake_loop, daemon=True)
        wake_thread.start()
        print("👂 Porcupine wake word detection active")
    else:
        print("❌ No wake word detection configured. Press Enter to interact.")

    print("🤖 Agent GLaDOS ready!")
    print("💡 Say 'stop' or 'shut up' to interrupt TTS")
    print("💡 Say 'exit' to quit")
    print("💡 Press Ctrl+C to force quit")

    try:
        while not shutdown_flag.is_set():
            try:
                # Wait for wake word or manual trigger
                if wake_detector or (WakeWordDetector and cfg.wake_keyword_path):
                    print("👂 Waiting for wake word...")
                    if wake_event.wait(timeout=1.0):  # Check every second
                        wake_event.clear()
                        
                        # Pause wake word detection while processing
                        if wake_detector:
                            wake_detector.pause()
                    else:
                        continue  # Timeout, check shutdown flag
                else:
                    try:
                        input("Press Enter to speak...")
                    except (EOFError, KeyboardInterrupt):
                        break

                # Capture user command with fresh microphone stream
                print("🎤 Listening for your command...")
                try:
                    with MicrophoneStream() as mic:
                        # Clear any buffered audio from wake word detection
                        time.sleep(0.1)  # Brief pause
                        mic.clear_buffer()
                        pcm = capture_audio(cfg, mic)
                except Exception as e:
                    print(f"❌ Audio capture failed: {e}")
                    if wake_detector:
                        wake_detector.resume()
                    continue
                
                if not pcm or len(pcm) < 1000:
                    print("⚠️  No audio captured")
                    # Resume wake word detection
                    if wake_detector:
                        wake_detector.resume()
                    continue

                # Auto-detect language and transcribe
                text = asr._run_once(pcm, language=None)
                print(f"👤 User: {text}")
                
                if not text.strip():
                    # Resume wake word detection
                    if wake_detector:
                        wake_detector.resume()
                    continue
                    
                if text.lower() in {"exit", "quit", "goodbye", "бувай"}:
                    print("👋 Goodbye!")
                    break

                # Check for stop commands
                if handle_stop_commands(text, tts):
                    # Resume wake word detection
                    if wake_detector:
                        wake_detector.resume()
                    continue

                lang = detect_language(text)
                
                # Try inventory search first
                response = handle_inventory_query(text, inventory)
                
                if response is None:
                    # Use LLM with better prompt
                    system_prompt = create_better_system_prompt(lang)
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ]
                    try:
                        response = llm.chat(messages, max_tokens=cfg.llm_max_tokens)
                    except Exception as e:
                        response = f"Error: {e}" if lang == "en" else f"Помилка: {e}"

                print(f"🤖 GLaDOS: {response}")
                
                # Clean response to avoid TTS speaking code/markup
                cleaned_response = clean_response_for_tts(response)
                
                # Generate and play TTS
                try:
                    out_wav = "response.wav"
                    success = tts.speak_and_save(
                        text=cleaned_response,
                        out_path=out_wav,
                        language=lang,
                        style=cfg.tts_style,
                        play_audio=cfg.auto_play_tts
                    )
                    if success and not cfg.auto_play_tts:
                        print(f"💾 Audio saved to {out_wav}")
                except Exception as e:
                    print(f"❌ TTS failed: {e}")

                # Resume wake word detection after processing
                if wake_detector and not shutdown_flag.is_set():
                    time.sleep(0.5)  # Brief pause
                    wake_detector.resume()

            except KeyboardInterrupt:
                print("\n👋 Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                # Resume wake word detection on error
                if wake_detector:
                    wake_detector.resume()
                continue

    except KeyboardInterrupt:
        print("\n👋 Final interrupt received")

    finally:
        # Cleanup
        shutdown_flag.set()
        if wake_detector:
            wake_detector.stop()
        if wake_thread:
            wake_thread.join(timeout=2.0)
        print("🔴 GLaDOS shutting down...")


if __name__ == "__main__":
    main()
