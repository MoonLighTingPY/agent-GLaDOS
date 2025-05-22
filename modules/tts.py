import pyttsx3
import threading

class TextToSpeech:
    def __init__(self, voice_name="Zira"):
        # only store voice_name; defer engine creation to each speak call
        self.voice_name = voice_name

    def speak(self, text, blocking=False):
        print(f"[TTS] speak() start: '{text}'", flush=True)
        if blocking:
            # synchronous speech to avoid ASR picking up TTS audio
            self._background_speak(text)
        else:
            # asynchronous speech for non-critical notifications
            threading.Thread(target=self._background_speak, args=(text,), daemon=True).start()

    def _background_speak(self, text):
        try:
            # initialize COM on Windows for pyttsx3 to avoid CoInitialize error
            import sys
            if sys.platform.startswith('win'):
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except ImportError:
                    pass
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