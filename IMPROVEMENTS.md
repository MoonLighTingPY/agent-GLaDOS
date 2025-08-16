# 🚀 GLaDOS Agent v2.0 - Major Improvements

## ✨ What's New

### 1. 🎤 **Human-like Text-to-Speech**
- **Microsoft Edge TTS**: Natural, expressive voices with emotions
- **Ukrainian Support**: Native Ukrainian voices (`uk-UA-PolinaNeural`, `uk-UA-OstapNeural`)  
- **Voice Styles**: Friendly, excited, serious, calm
- **Gender Selection**: Male/female voices via `TTS_VOICE_GENDER=female/male`

### 2. 🛑 **Voice Interruption System**
- Say **"stop"**, **"shut up"**, **"заткнись"**, **"тиша"** to interrupt TTS
- Immediate audio playback termination
- Thread-safe interruption handling

### 3. 👂 **Always-On Wake Word Detection**  
- **Simple Wake Word**: Uses Whisper to detect phrases in continuous audio
- **Default wake words**: `"hey glados"`, `"гей глендос"`, `"слухай"`, `"listen"`
- **Audio feedback**: Plays beep sound when wake word detected
- **No manual pressing**: Continuous listening mode

### 4. 🇺🇦 **Improved Ukrainian Support**
- Better Whisper transcription with `language=uk` parameter
- Native Ukrainian TTS voices (Edge TTS)
- Ukrainian system prompts and responses
- Expanded Ukrainian wake words and stop commands

### 5. 📝 **Shorter, Smarter Responses**
- **Max tokens reduced**: 150 tokens vs 512 (much shorter responses)
- **Better prompts**: Language-specific system prompts
- **GLaDOS personality**: Sarcastic but helpful, 1-2 sentences max

### 6. ⏱️ **Better Listening Duration**
- **Longer max duration**: 12 seconds vs 8 seconds
- **Longer silence detection**: 1.2s vs 0.8s (waits for complete thoughts)
- **Shorter minimum**: 0.5s vs 0.8s (more responsive)
- **Complete sentence capture**: No more cutting off mid-sentence

## 🎮 Usage Examples

### Wake Word Activation:
```
User: "Hey GLaDOS"
System: 🔊 BEEP! (wake word detected)
System: 🎤 Listening...

User: "Where is the Arduino?"
GLaDOS: "Item 'arduino uno' is at drawer B1, microcontrollers."
```

### Interruption:
```
GLaDOS: "Well, if you must know, the item you're looking for is..."
User: "Stop!"
System: 🛑 Stop command detected
GLaDOS: [immediately stops talking]
```

### Ukrainian Support:
```
User: "Гей ГлеДОС"
System: 🔊 BEEP!
User: "Де знайти мультиметр?"
GLaDOS: "Річ 'multimeter' знаходиться в workbench, drawer 2."
```

## ⚙️ Configuration (.env)

```bash
# Human-like TTS
TTS_VOICE_GENDER=female
TTS_STYLE=friendly
ENABLE_INTERRUPTION=true

# Wake words (comma separated)  
USE_SIMPLE_WAKE_WORD=true
WAKE_WORDS=hey glados,гей глендос,слухай,listen

# Better listening
VAD_SILENCE_DURATION=1.2
VAD_MAX_DURATION=12.0
VAD_MIN_DURATION=0.5

# Shorter responses
LLM_MAX_TOKENS=150
```

## 🚀 Quick Start

1. **Update dependencies**: 
   ```
   pip install -r requirements.txt
   ```

2. **Copy new config**:
   ```
   copy .env.example .env
   ```

3. **Run GLaDOS**:
   ```
   python main.py
   ```

4. **Try wake words**:
   - "Hey GLaDOS, where is the Arduino?"
   - "Гей ГлеДОС, де знайти резистори?"

## 🔧 Technical Improvements

- **Microsoft Edge TTS API**: Cloud-based human voices (free)
- **Async TTS processing**: Non-blocking voice synthesis  
- **Thread-safe interruption**: Proper cleanup of audio processes
- **Better VAD parameters**: More natural conversation flow
- **Language-aware prompts**: Context-appropriate system messages
- **Expanded stop word detection**: Multiple languages

## 🎯 Solved Issues

✅ **Robot voice** → Human-like voices with emotions  
✅ **No Ukrainian** → Native Ukrainian TTS and better recognition  
✅ **Can't interrupt** → Voice interruption with stop commands  
✅ **Too verbose** → Short, witty 1-2 sentence responses  
✅ **Cuts off speech** → Longer listening duration, complete sentences  
✅ **No wake word** → Always-on detection with audio feedback  

The system now feels much more natural and responsive!
