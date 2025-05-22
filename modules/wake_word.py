import pvporcupine
import sounddevice as sd

class WakeWordDetector:
    def __init__(self, keyword_path):
        # Initialize Porcupine with the keyword file
        self.porcupine = pvporcupine.create(keyword_paths=[keyword_path], access_key="zvcNpkF14eTl4mivMJuW68iJqzL52iDZ813wOtB12itBFAoH2ZL++Q==")
        self.sample_rate = self.porcupine.sample_rate
        self.frame_length = self.porcupine.frame_length

    def start(self, callback):
        """
        Start listening for the wake word; call `callback` when detected
        """
        def audio_callback(indata, frames, time, status):
            pcm = indata[:, 0]
            pcm = (pcm * 32767).astype('int16')
            result = self.porcupine.process(pcm)
            if result >= 0:
                callback()

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.frame_length,
            channels=1,
            callback=audio_callback
        )
        self.stream.start()
    def stop(self):
        """
        Stop the wake word detection stream.
        """
        try:
            self.stream.stop()
            self.stream.close()
        except Exception:
            pass
