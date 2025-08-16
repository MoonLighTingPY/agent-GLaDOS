# Agent GLaDOS

🤖 **Smart Inventory Assistant** - Local voice-controlled assistant for finding items using AI

Embedded/local voice assistant prototype for smart inventory (Raspberry Pi friendly).

## ✨ Current Features (MVP)
- 🎤 **Speech Recognition**: English + Ukrainian using OpenAI Whisper
- 🔊 **Text-to-Speech**: Windows SAPI (testing) / Piper voices (production)
- 🎯 **Inventory Search**: "Where is the [item]?" natural language queries  
- 🧠 **AI Assistant**: Groq Cloud LLM (llama-3.1-8b-instant) for general conversation
- 📱 **Lightweight**: Runs on Raspberry Pi 4 with tiny Whisper model
- 🌍 **Multilingual**: Auto-detects language and responds accordingly

## 🎯 Demo Usage
```
User: "Where is that green board that converts high voltage to low voltage?"
Agent: "Item 'buck converter' is at shelf A2, electronics section."

User: "Де знайти мультиметр?" (Ukrainian: Where to find multimeter?)
Agent: "Item 'multimeter' is at workbench, drawer 2."
```

## 🚀 Quick Start

### 1. **Install Dependencies**
```powershell
# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install Python packages
pip install -r requirements.txt
```

### 2. **Configure API Keys**
```powershell
# Copy template and edit with your keys
copy .env.example .env
# Edit .env with your Groq API key
```

### 3. **Run Setup**
```powershell
python setup.py  # Checks dependencies and creates demo inventory
```

### 4. **Start Agent**
```powershell
python main.py
```

## 🔧 Configuration (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `GROG_CLOUD_API_KEY` | **Required** - Get from [Groq Console](https://console.groq.com) | `gsk_xxx...` |
| `GROG_MODEL` | LLM model name | `llama-3.1-8b-instant` |
| `WHISPER_MODEL` | Speech model size (`tiny`, `base`, `small`) | `tiny` (for Pi) |
| `PIPER_EN_VOICE` | Path to English Piper voice model | `models/en_US-amy-low.onnx` |
| `PIPER_UK_VOICE` | Path to Ukrainian Piper voice model | `models/uk_UK-lada-low.onnx` |

## 🎛️ Hardware Targets

- **Development**: Windows/Mac/Linux with microphone
- **Production**: Raspberry Pi 4 (2GB+ RAM recommended)  
- **Storage**: ~2GB for models (tiny Whisper + voice files)

## 📦 Optional Enhancements

### Wake Word (Picovoice Porcupine)
1. Get free access key from [Picovoice Console](https://console.picovoice.ai/)
2. Train custom keyword and download `.ppn` file
3. Set `PICOVOICE_ACCESS_KEY` and `WAKEWORD_KEYWORD_PATH` in `.env`

### Better TTS (Piper Voices)
1. Download voices from [Rhasspy Piper](https://github.com/rhasspy/piper#pre-built-models)
2. Place `.onnx` files in `models/` folder
3. Set voice paths in `.env`

## 🔍 Inventory Management

**Add Items:**
```python
from glados.inventory.storage import InventoryDB
db = InventoryDB()
db.upsert_item("item name", "location", {"metadata": "optional"})
```

**Search Examples:**
- "Where is the Arduino?"
- "Де знайти резистори?" (Ukrainian)
- "Where is that thing for measuring voltage?"

## 🧪 Development Status

### ✅ Working
- [x] Speech recognition (EN/UK)
- [x] LLM integration (Groq)
- [x] Inventory search
- [x] Text-to-speech
- [x] Language detection
- [x] Basic setup/demo

### 🔄 Planned
- [ ] Continuous listening with VAD
- [ ] Camera-based item recognition
- [ ] Laser pointer for item location
- [ ] Better intent parsing
- [ ] Web interface for inventory management
- [ ] Multiple inventory rooms/zones

## 🛠️ Technical Notes

**Performance Tips:**
- Use `WHISPER_MODEL=tiny` on Raspberry Pi for speed
- Whisper auto-selects CPU optimizations (int8 quantization)  
- Piper voices (ONNX) are faster than system TTS on ARM

**Dependencies:**
- `openai-whisper`: Speech recognition
- `pyttsx3`: Windows TTS fallback  
- `requests`: API calls to Groq
- `pyaudio`: Microphone capture
- `python-dotenv`: Environment config

## 📄 License

MIT License - Feel free to modify and distribute!
