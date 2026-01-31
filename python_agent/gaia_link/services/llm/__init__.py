"""
LLM Service Module

Provides direct LLM integration without SpoonOS ChatBot limitations.
Supports Gemini and OpenAI in non-function-calling mode.
"""

from .gemini_direct import GeminiDirectService, create_gemini_service

__all__ = ["GeminiDirectService", "create_gemini_service"]
