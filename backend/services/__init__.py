"""
Services package for backend utilities
"""
from .document_extractor import document_extractor
from .gemini_service import gemini_service
from .ollama_service import ollama_service  # Keep for backward compatibility

__all__ = ['document_extractor', 'gemini_service', 'ollama_service']

