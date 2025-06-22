"""
AI Assistant Core Module

This module provides the core functionality for interacting with LLM services.
Designed to be modular and easily switchable between different AI providers.
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class AIProvider(Enum):
    """Supported AI providers"""
    GROQ = "groq"
    OPENAI = "openai"
    LOCAL = "local"


@dataclass
class AIMessage:
    """Represents a message in the conversation"""
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: Optional[str] = None


@dataclass
class AIResponse:
    """Standardized response from AI assistant"""
    content: str
    success: bool
    error_message: Optional[str] = None
    usage_stats: Optional[Dict[str, Any]] = None


class AIAssistantCore:
    """
    Core AI Assistant class for handling LLM interactions.
    
    This class provides a unified interface for different AI providers
    and maintains conversation context for multi-turn interactions.
    """
    
    def __init__(self, provider: AIProvider = AIProvider.GROQ):
        self.provider = provider
        self.conversation_history: List[AIMessage] = []
        self.system_prompt = os.getenv("SYSTEM_PROMPT", "You are a helpful AI assistant.")
        
        # Initialize provider-specific settings
        self._init_provider_config()
        
        # Add system message to conversation
        self.add_system_message(self.system_prompt)
    
    def _init_provider_config(self):
        """Initialize configuration for the selected AI provider"""
        if self.provider == AIProvider.GROQ:
            self.api_key = os.getenv("GROG_CLOUD_API_KEY")
            self.model = os.getenv("GROG_MODEL", "llama-3.1-8b-instant")
            self.api_url = os.getenv("GROG_API_URL", "https://api.groq.com/openai/v1/chat/completions")
            
            if not self.api_key:
                raise ValueError("GROG_CLOUD_API_KEY not found in environment variables")
        
        # Future providers can be added here
        elif self.provider == AIProvider.OPENAI:
            # self.api_key = os.getenv("OPENAI_API_KEY")
            # self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            raise NotImplementedError("OpenAI provider not yet implemented")
        
        elif self.provider == AIProvider.LOCAL:
            raise NotImplementedError("Local provider not yet implemented")
    
    def add_system_message(self, content: str):
        """Add or update the system message"""
        # Remove existing system message if present
        self.conversation_history = [msg for msg in self.conversation_history if msg.role != "system"]
        
        # Add new system message at the beginning
        system_msg = AIMessage(role="system", content=content)
        self.conversation_history.insert(0, system_msg)
    
    def add_user_message(self, content: str):
        """Add a user message to the conversation"""
        user_msg = AIMessage(role="user", content=content)
        self.conversation_history.append(user_msg)
    
    def add_assistant_message(self, content: str):
        """Add an assistant message to the conversation"""
        assistant_msg = AIMessage(role="assistant", content=content)
        self.conversation_history.append(assistant_msg)
    
    def clear_conversation(self, keep_system: bool = True):
        """Clear conversation history, optionally keeping system message"""
        if keep_system:
            system_messages = [msg for msg in self.conversation_history if msg.role == "system"]
            self.conversation_history = system_messages
        else:
            self.conversation_history = []
    
    def _prepare_messages_for_api(self) -> List[Dict[str, str]]:
        """Convert conversation history to API format"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.conversation_history
        ]
    
    def _make_groq_request(self, messages: List[Dict[str, str]]) -> AIResponse:
        """Make request to Groq API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage_stats = data.get("usage", {})
            
            return AIResponse(
                content=content,
                success=True,
                usage_stats=usage_stats
            )
            
        except requests.exceptions.RequestException as e:
            return AIResponse(
                content="",
                success=False,
                error_message=f"Request failed: {str(e)}"
            )
        except (KeyError, IndexError) as e:
            return AIResponse(
                content="",
                success=False,
                error_message=f"Invalid response format: {str(e)}"
            )
    
    def generate_response(self, user_input: str) -> AIResponse:
        """
        Generate AI response for user input.
        
        Args:
            user_input: The user's message
            
        Returns:
            AIResponse object containing the AI's response
        """
        # Add user message to conversation
        self.add_user_message(user_input)
        
        # Prepare messages for API
        messages = self._prepare_messages_for_api()
        
        # Make API request based on provider
        if self.provider == AIProvider.GROQ:
            response = self._make_groq_request(messages)
        else:
            response = AIResponse(
                content="",
                success=False,
                error_message=f"Provider {self.provider} not implemented"
            )
        
        # If successful, add assistant response to conversation
        if response.success:
            self.add_assistant_message(response.content)
        
        return response
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation"""
        if not self.conversation_history:
            return "No conversation history"
        
        summary = f"Conversation with {len(self.conversation_history)} messages:\n"
        for i, msg in enumerate(self.conversation_history):
            role_emoji = {"system": "🤖", "user": "👤", "assistant": "🎯"}.get(msg.role, "❓")
            preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            summary += f"{i+1}. {role_emoji} {msg.role}: {preview}\n"
        
        return summary