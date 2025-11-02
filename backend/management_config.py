import os
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class OllamaConfig:
    """Configuration for Ollama models"""
    base_url: str = "http://localhost:11434"
    models: Dict[str, str] = None
    timeout: int = 30
    
    def __post_init__(self):
        if self.models is None:
            self.models = {
                "quick": "llama3.2:3b",      # Fast responses
                "detailed": "llama3.1:8b",   # Detailed analysis
                "balanced": "mistral:7b",    # Balanced performance
                "fallback": "llama2:latest"  # Backup option
            }

@dataclass
class AppConfig:
    """Main application configuration"""
    # Paths
    data_dir: str = "data"
    cache_dir: str = "cache"
    repos_dir: str = "repositories"
    
    # Analysis settings
    max_file_size: int = 1024 * 1024  # 1MB
    supported_extensions: List[str] = None
    max_commits_analysis: int = 100
    
    # UI settings
    page_title: str = "CodeClarity AI"
    page_icon: str = "🔍"  # Fixed emoji encoding
    
    def __post_init__(self):
        if self.supported_extensions is None:
            self.supported_extensions = ['.py', '.js', '.java', '.go', '.cpp', '.c', '.ts', '.jsx', '.tsx']
        
        # Create directories
        for directory in [self.data_dir, self.cache_dir, self.repos_dir]:
            os.makedirs(directory, exist_ok=True)

# Initialize global configs
OLLAMA_CONFIG = OllamaConfig()
APP_CONFIG = AppConfig()
