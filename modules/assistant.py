import os
import requests
from dotenv import load_dotenv
import webbrowser
import urllib.parse
import subprocess
load_dotenv()

class Assistant:
    def __init__(self, tts, recognizer, system_prompt):
        self.tts = tts
        self.recognizer = recognizer
        # Load Grog Cloud configuration from .env
        self.api_key = os.getenv("GROG_CLOUD_API_KEY") or os.getenv("VITE_GROG_CLOUD_API_KEY")
        self.model = os.getenv("GROG_MODEL") or os.getenv("VITE_GROG_MODEL")
        self.system_prompt = system_prompt
        self.memory = []

    def process(self):
        print(">> Assistant.process() invoked")
        # announce listening
        # prompt and recognize speech
        self.tts.speak("Listening for your command.")
        print("Prompted user to speak")
        # Debug: verify Grog config
        print(f"Grog API key set: {bool(self.api_key)}, model: {self.model}")
        if not self.api_key or not self.model:
            err = "Missing Grog Cloud API key or model. Check your .env configuration."
            print(err)
            self.tts.speak(err)
            return
        text = self.recognizer.recognize()
        # Debug: print recognized user text
        print(f"Recognized text: {text}")
        # Debug: parsed command
        cmd = text.lower().strip()
        print(f"Parsed text: {cmd}")
        # Local command handling
        if "open youtube" in cmd:
            print("Local command: open youtube")
            # e.g., "open youtube how to program esp32"
            query = cmd.split("open youtube", 1)[1].strip()
            url = "https://www.youtube.com"
            if query:
                url += "/results?search_query=" + urllib.parse.quote(query)
            webbrowser.open(url)
            self.tts.speak(f"Opened YouTube{ ' and searched for ' + query if query else '' }")
            print(f"Opened YouTube with query: {query}")
            return
        if "open text document" in cmd:
            print("Local command: open text document")
            # Open or create a notes.txt in project root
            notes_path = os.path.join(os.getcwd(), "notes.txt")
            subprocess.Popen(["notepad.exe", notes_path])
            self.tts.speak("Opened text document.")
            print("Opened notes.txt in text editor")
            return
        print("No local command matched, proceeding to Grog Cloud API")
        self.memory.append({'role': 'user', 'content': text})
        # call Grog Cloud API
        url = os.getenv("GROG_API_URL", "https://api.groq.com/openai/v1/chat/completions")
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': self.system_prompt},
                *self.memory
            ]
        }
        headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': 'application/json'
        }
        try:
            resp = requests.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"Error calling Grog Cloud API: {e}")
            return
        answer = data['choices'][0]['message']['content']
        # Debug: print assistant response before speaking
        print(f"Assistant answer: {answer}")
        self.memory.append({'role': 'assistant', 'content': answer})
        # speak
        self.tts.speak(answer)
