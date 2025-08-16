import os
from typing import Optional, List
import requests

class GrogLLMClient:
    """Groq Cloud API client for fast LLM inference."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key or os.getenv("GROG_CLOUD_API_KEY")
        self.base_url = base_url or os.getenv("GROG_API_URL", "https://api.groq.com/openai/v1/chat/completions")
        self.model = model or os.getenv("GROG_MODEL", "llama-3.1-8b-instant")
        if not self.api_key:
            raise RuntimeError("GROG_CLOUD_API_KEY not set in env")

    def chat(self, messages: List[dict], temperature: float = 0.7, max_tokens: int = 150) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        resp = requests.post(self.base_url, json=payload, timeout=60, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
