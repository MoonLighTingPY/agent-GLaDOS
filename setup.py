#!/usr/bin/env python3
"""
Setup script for GLaDOS Agent - Smart Inventory Assistant
Run this after installing dependencies to set up the demo.
"""
import os
import sys
from pathlib import Path

def main():
    print("🤖 GLaDOS Agent Setup")
    print("===================")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check .env file
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found")
        print("📝 Please copy .env.example to .env and fill in your API keys")
        return False
    
    print("✅ .env file found")
    
    # Check critical dependencies
    try:
        import whisper
        print("✅ Whisper for speech recognition")
    except ImportError:
        print("❌ OpenAI Whisper not installed")
        print("📦 Run: pip install openai-whisper")
        return False
    
    try:
        import pyttsx3
        print("✅ TTS (Windows SAPI)")
    except ImportError:
        print("⚠️  pyttsx3 not found - TTS may not work")
    
    try:
        import requests
        print("✅ Requests for API calls")
    except ImportError:
        print("❌ Requests not installed")
        return False
    
    # Setup demo inventory
    try:
        from glados.inventory.storage import InventoryDB
        db = InventoryDB()
        
        # Add demo items if inventory is empty
        items = db.list_items()
        if len(items) == 0:
            print("📦 Setting up demo inventory...")
            from setup_inventory import setup_demo_inventory
            setup_demo_inventory()
        else:
            print(f"✅ Inventory has {len(items)} items")
    except Exception as e:
        print(f"❌ Failed to setup inventory: {e}")
        return False
    
    print("\n🎉 Setup complete!")
    print("\n🚀 To start GLaDOS:")
    print("   python main.py")
    print("\n💡 Tips:")
    print("   - Say 'where is [item]' to search inventory")
    print("   - Use 'exit' or Ctrl+C to quit")
    print("   - Check README.md for configuration options")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
