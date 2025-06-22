"""
GLaDOS AI Assistant - Main Application

A modular AI assistant designed for IoT applications with smart inventory management.
"""

import os
from dotenv import load_dotenv
from modules.ai_assistant.ai_assistant_core import AIAssistantCore, AIProvider
from modules.text_to_speech import TTSCore, VoiceSettings, TTSEngine

def main():
    """Main application entry point"""
    # Load environment variables
    load_dotenv()
    
    print("🤖 GLaDOS AI Assistant Starting...")
    print("=" * 50)
    
    try:
        # Initialize AI Assistant
        assistant = AIAssistantCore(provider=AIProvider.GROQ)
        print("✅ AI Assistant Core initialized successfully!")
        print(f"🔧 Using model: {assistant.model}")
        
        # Initialize TTS with language from environment
        tts_language = os.getenv('TTS_LANGUAGE', 'auto')
        voice_settings = VoiceSettings(engine=TTSEngine.AUTO, language=tts_language)
        tts = TTSCore(voice_settings)
        print("🎤 Text-to-Speech initialized successfully!")
        print(f"🔧 Using TTS engine: {tts.current_engine}")
        print(f"🌍 Language setting: {tts_language}")
        print("=" * 50)
        
        # Interactive chat loop
        print("💬 Chat with GLaDOS (type 'quit' to exit, 'clear' to reset conversation)")
        print("📝 Type 'summary' to see conversation history")
        print("🎯 Type 'voice on/off' to toggle voice output")
        print("🤖 Type 'glados on/off' to toggle GLaDOS voice effects")
        print("🌍 Type 'lang uk/en/ru' to change language")
        print("-" * 50)
        
        voice_enabled = True
        glados_mode = True
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    if voice_enabled:
                        tts.speak("Goodbye! GLaDOS shutting down...", use_vocoder=glados_mode)
                    print("👋 Goodbye! GLaDOS shutting down...")
                    break
                
                if user_input.lower() == 'clear':
                    assistant.clear_conversation()
                    print("🗑️ Conversation cleared!")
                    continue
                
                if user_input.lower() == 'summary':
                    print("\n📊 " + assistant.get_conversation_summary())
                    continue
                
                if user_input.lower() in ['voice on', 'voice off']:
                    voice_enabled = 'on' in user_input.lower()
                    status = "enabled" if voice_enabled else "disabled"
                    print(f"🎤 Voice output {status}")
                    continue
                
                if user_input.lower() in ['glados on', 'glados off']:
                    glados_mode = 'on' in user_input.lower()
                    status = "enabled" if glados_mode else "disabled"
                    print(f"🤖 GLaDOS voice effects {status}")
                    continue
                
                if user_input.lower().startswith('lang '):
                    new_lang = user_input.lower().replace('lang ', '').strip()
                    if new_lang in ['uk', 'en', 'ru', 'auto']:
                        tts.set_language(new_lang)
                        print(f"🌍 Language changed to: {new_lang}")
                    else:
                        print("❌ Supported languages: uk, en, ru, auto")
                    continue
                
                if not user_input:
                    continue
                
                print("🤔 GLaDOS is thinking...")
                
                # Generate response
                response = assistant.generate_response(user_input)
                
                if response.success:
                    print(f"🎯 GLaDOS: {response.content}")
                    
                    # Speak response if voice is enabled
                    if voice_enabled:
                        print("🗣️ GLaDOS is speaking...")
                        tts.speak(response.content, use_vocoder=glados_mode)
                    
                    # Show usage stats if available
                    if response.usage_stats:
                        tokens = response.usage_stats.get('total_tokens', 'N/A')
                        print(f"📊 Tokens used: {tokens}")
                else:
                    print(f"❌ Error: {response.error_message}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. GLaDOS shutting down...")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
    
    except Exception as e:
        print(f"❌ Failed to initialize AI Assistant: {e}")
        print("🔧 Please check your configuration in .env file")

if __name__ == "__main__":
    main()