import requests
import json
import logging
from typing import Optional, Dict, Any, List
from config import OLLAMA_CONFIG

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self):
        self.base_url = OLLAMA_CONFIG.base_url
        self.models = OLLAMA_CONFIG.models
        self.timeout = OLLAMA_CONFIG.timeout
        self._available_models = None
    
    def check_availability(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        if self._available_models is not None:
            return self._available_models
            
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self._available_models = [model['name'] for model in data.get('models', [])]
                return self._available_models
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get available models: {e}")
        
        return []
    
    def select_model(self, task_type: str = "balanced") -> str:
        """Select appropriate model based on task type"""
        available = self.get_available_models()
        
        # Priority order based on task type
        if task_type == "quick":
            priority = ["quick", "balanced", "fallback", "detailed"]
        elif task_type == "detailed":
            priority = ["detailed", "balanced", "quick", "fallback"]
        else:
            priority = ["balanced", "quick", "detailed", "fallback"]
        
        for model_type in priority:
            model_name = self.models.get(model_type)
            if model_name and model_name in available:
                return model_name
        
        # Fallback to first available model
        return available[0] if available else self.models["fallback"]
    
    def generate(self, prompt: str, model: Optional[str] = None, task_type: str = "balanced") -> Optional[str]:
        """Generate text using Ollama"""
        if not model:
            model = self.select_model(task_type)
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to generate text: {e}")
            return None