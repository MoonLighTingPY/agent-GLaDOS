import queue
import sounddevice as sd
import json
import os
from vosk import Model, KaldiRecognizer
import time

class SpeechRecognizer:
    def __init__(self, model_path, sample_rate=16000):
        # Debug: verify initial model path
        print(f"Initializing VOSK model from: {model_path}, exists: {os.path.exists(model_path)}")
        # Debug: list model directory contents
        try:
            entries = os.listdir(model_path)
            print(f"VOSK model directory entries: {entries}")
        except Exception as e:
            print(f"Error listing model directory: {e}")
        # Ensure this path contains conf/model.conf, else search nested directories
        conf_file = os.path.join(model_path, 'conf', 'model.conf')
        if not os.path.isfile(conf_file):
            for entry in os.listdir(model_path):
                subp = os.path.join(model_path, entry)
                alt_conf = os.path.join(subp, 'conf', 'model.conf')
                if os.path.isdir(subp) and os.path.isfile(alt_conf):
                    print(f"Found nested VOSK model at: {subp}")
                    model_path = subp
                    break
        try:
            self.model = Model(model_path)
        except Exception as e:
            print(f"Failed to load VOSK model from {model_path}: {e}")
            raise
        self.sample_rate = sample_rate

    def recognize(self, duration=10):
        """
        Record audio for `duration` seconds and return recognized text.
        """
        print(f"Recorder: starting recognition for {duration}s @ {self.sample_rate}Hz")
        q = queue.Queue()

        def callback(indata, frames, time_info, status):
            if status:
                print(f"[asr] Audio status: {status}")
            # we need raw 16-bit little-endian samples
            q.put(bytes(indata))

        rec = KaldiRecognizer(self.model, self.sample_rate)
        rec.SetWords(True)

        # Open a raw PCM input stream
        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000, dtype='int16',
                               channels=1, callback=callback):
            start = time.time()
            while time.time() - start < duration:
                try:
                    data = q.get(timeout=duration)
                except queue.Empty:
                    break

                # feed VOSK chunk
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    print(f"[asr] chunk result: {res.get('text')}")
                else:
                    # you can also see partial results:
                    pres = json.loads(rec.PartialResult())
                    print(f"[asr] partial: {pres.get('partial')}")

            # final result
            final = json.loads(rec.FinalResult())
            text = final.get('text', '')
            print(f"[asr] final result: '{text}'")
            return text
