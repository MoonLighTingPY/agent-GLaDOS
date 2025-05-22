import pyttsx3
import threading

class TextToSpeech:
    def __init__(self, voice_name="Zira"):
        # only store voice_name; defer engine creation to each speak call
        self.voice_name = voice_name

    def speak(self, text):
        print(f"[TTS] speak() start: '{text}'", flush=True)
        threading.Thread(target=self._background_speak, args=(text,), daemon=True).start()

    def _background_speak(self, text):
        try:
            engine = pyttsx3.init()
            # select desired voice
            for v in engine.getProperty("voices"):
                if self.voice_name.lower() in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
            engine.say(text)
            engine.runAndWait()
            print(f"[TTS] speak() done: '{text}'", flush=True)
        except Exception as e:
            print(f"[TTS] speak() error: {e}", flush=True)