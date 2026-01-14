import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

def setup_logging(log_level: str = "INFO"):
    """Setup application logging"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('codeclarity.log')
        ]
    )

def create_cache_key(data: Any) -> str:
    """Create cache key from data"""
    data_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(data_str.encode()).hexdigest()

def ensure_directory(path: Path) -> None:
    """Ensure directory exists"""
    path.mkdir(parents=True, exist_ok=True)

def safe_filename(filename: str) -> str:
    """Create safe filename by removing invalid characters"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"

def validate_github_url(url: str) -> bool:
    """Validate GitHub repository URL"""
    if not url:
        return False
    
    # Basic GitHub URL patterns
    github_patterns = [
        'github.com/',
        'https://github.com/',
        'http://github.com/',
        'git@github.com:'
    ]
    
    return any(pattern in url.lower() for pattern in github_patterns)
