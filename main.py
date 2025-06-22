"""
GLaDOS AI Assistant - Main Application

A modular AI assistant designed for IoT applications with smart inventory management.
"""

import os
from dotenv import load_dotenv
from modules.ai_assistant.ai_assistant_core import AIAssistantCore, AIProvider

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
        print("=" * 50)
        
        # Interactive chat loop
        print("💬 Chat with GLaDOS (type 'quit' to exit, 'clear' to reset conversation)")
        print("📝 Type 'summary' to see conversation history")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye! GLaDOS shutting down...")
                    break
                
                if user_input.lower() == 'clear':
                    assistant.clear_conversation()
                    print("🗑️ Conversation cleared!")
                    continue
                
                if user_input.lower() == 'summary':
                    print("\n📊 " + assistant.get_conversation_summary())
                    continue
                
                if not user_input:
                    continue
                
                print("🤔 GLaDOS is thinking...")
                
                # Generate response
                response = assistant.generate_response(user_input)
                
                if response.success:
                    print(f"🎯 GLaDOS: {response.content}")
                    
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