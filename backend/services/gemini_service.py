"""
Gemini LLM Service with fallback to Ollama
Tries Gemini API keys, falls back to Ollama if Gemini fails
"""
import os
import logging
from typing import Optional, Union
from config import settings

logger = logging.getLogger(__name__)

# Try importing Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")

# Try importing Ollama for fallback
try:
    import ollama
    from langchain_ollama import ChatOllama
    from langchain_community.llms import Ollama as OllamaLLM
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama not available for fallback")


class GeminiService:
    """Service for interacting with Gemini API with Ollama fallback"""
    
    def __init__(self):
        """Initialize Gemini service with API key fallback logic"""
        # Load API keys with the following priority order:
        # 1) GOOGLE_API_KEY env (primary for litellm/google)
        # 2) GEMINI_API_KEY env (legacy)
        # 3) GEMINI_API_KEYS env (comma-separated)
        # 4) settings.GEMINI_API_KEYS (comma-separated)
        # 5) settings.GEMINI_API_KEY_1 / settings.GEMINI_API_KEY_2
        keys: list[str] = []
        env_primary = os.getenv("GOOGLE_API_KEY", "").strip()
        env_legacy = os.getenv("GEMINI_API_KEY", "").strip()
        env_multi = os.getenv("GEMINI_API_KEYS", "").strip()
        if env_primary:
            keys.append(env_primary)
        if env_legacy:
            keys.append(env_legacy)
        if env_multi:
            keys.extend([k.strip() for k in env_multi.split(",") if k.strip()])
        # Add keys from settings as fallbacks
        settings_multi = getattr(settings, "GEMINI_API_KEYS", None)
        if settings_multi:
            keys.extend([k.strip() for k in str(settings_multi).split(",") if k.strip()])
        if getattr(settings, "GEMINI_API_KEY_1", None):
            keys.append(settings.GEMINI_API_KEY_1)
        if getattr(settings, "GEMINI_API_KEY_2", None):
            keys.append(settings.GEMINI_API_KEY_2)
        # De-duplicate while preserving order
        seen = set()
        self.api_keys = [k for k in keys if not (k in seen or seen.add(k))]
        if not self.api_keys:
            logger.warning("No Gemini API keys found in environment or settings. Gemini may fail.")
            self.api_keys = []
        self.current_api_key_index = 0
        self.llm_type = None  # 'gemini' or 'ollama'
        self._llm_instance = None
        self.gemini_model = None
        self.ollama_model = "llama3.2:3b"
        self._initialize_llm()
    
    def _try_key_and_set_model(self, api_key: str) -> bool:
        """Configure Gemini with api_key, set a working model, and validate with a tiny request."""
        if not GEMINI_AVAILABLE:
            return False
        try:
            genai.configure(api_key=api_key)
            # Choose an available model
            try:
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                self.gemini_model_name = 'gemini-2.5-flash'
            except Exception:
                try:
                    self.gemini_model = genai.GenerativeModel('gemini-2.5-pro')
                    self.gemini_model_name = 'gemini-2.5-pro'
                except Exception:
                    try:
                        self.gemini_model = genai.GenerativeModel('gemini-flash-latest')
                        self.gemini_model_name = 'gemini-flash-latest'
                    except Exception:
                        self.gemini_model = genai.GenerativeModel('gemini-pro-latest')
                        self.gemini_model_name = 'gemini-pro-latest'
            # Minimal validation
            resp = self.gemini_model.generate_content("ping")
            if resp and hasattr(resp, 'text'):
                return True
        except Exception as e:
            logger.warning(f"Gemini key validation failed: {e}")
        return False
    
    def _initialize_llm(self):
        """Initialize LLM, trying Gemini first, then Ollama"""
        # Try Gemini first
        if GEMINI_AVAILABLE and self.api_keys:
            for i, api_key in enumerate(self.api_keys):
                if self._try_key_and_set_model(api_key):
                    self.current_api_key_index = i
                    self.llm_type = 'gemini'
                    logger.info(f"✅ Gemini API initialized successfully with API key {i+1}")
                    return
        
        # Fallback to Ollama
        if OLLAMA_AVAILABLE:
            try:
                # Test Ollama connection
                import ollama
                models = ollama.list()
                # Check if our model is available
                model_names = [m.get('name', '') for m in models.get('models', [])]
                if any(self.ollama_model in name for name in model_names):
                    self.llm_type = 'ollama'
                    logger.info(f"🔄 Falling back to Ollama with model: {self.ollama_model}")
                else:
                    logger.warning(f"⚠️ Ollama model {self.ollama_model} not found. Available: {model_names}")
                    # Still set to ollama, will try at runtime
                    self.llm_type = 'ollama'
            except Exception as e:
                logger.error(f"❌ Ollama fallback also failed: {e}")
                self.llm_type = 'ollama'  # Still try at runtime
        else:
            logger.error("❌ Neither Gemini nor Ollama is available!")
            # Don't raise here, let get_llm() handle it
            self.llm_type = 'ollama'  # Default fallback
    
    def get_llm(self):
        """
        Get LLM instance or model name for CrewAI
        
        Returns:
            For CrewAI: string model name (e.g., "gemini/gemini-pro" or "ollama/llama3.2:3b")
            For direct use: LangChain LLM instance
        """
        # Try Gemini first
        if GEMINI_AVAILABLE and self.api_keys:
            # Ensure the current key still works; if not, rotate through all
            start_idx = self.current_api_key_index if 0 <= self.current_api_key_index < len(self.api_keys) else 0
            indices = list(range(start_idx, len(self.api_keys))) + list(range(0, start_idx))
            for i in indices:
                if self._try_key_and_set_model(self.api_keys[i]):
                    self.current_api_key_index = i
                    os.environ['GOOGLE_API_KEY'] = self.api_keys[i]
                    model_name = f"gemini/{self.gemini_model_name if hasattr(self, 'gemini_model_name') else 'gemini-2.5-flash'}"
                    self.llm_type = 'gemini'
                    logger.info(f"Using Gemini LLM with key {i+1}: {model_name}")
                    return model_name
            logger.warning("All Gemini keys failed at runtime; falling back to Ollama if available.")
        
        # Fallback to Ollama
        if OLLAMA_AVAILABLE:
            try:
                # For CrewAI, return model name string (litellm format)
                model_name = f"ollama/{self.ollama_model}"
                self.llm_type = 'ollama'
                logger.info(f"Using Ollama LLM: {model_name}")
                return model_name
            except Exception as e:
                logger.error(f"Error with Ollama: {e}")
                raise RuntimeError(f"Failed to initialize Ollama LLM: {e}")
        
        raise RuntimeError("No LLM provider available")
    
    def get_langchain_llm(self):
        """
        Get LangChain-compatible LLM instance (for direct use, not CrewAI)
        
        Returns:
            LangChain LLM instance
        """
        if self._llm_instance is not None:
            return self._llm_instance
        
        # Try Gemini first - use ChatGoogleGenerativeAI for LangChain
        if GEMINI_AVAILABLE and self.api_keys:
            try:
                # Ensure we have a working key; rotate if necessary
                model_str = self.get_llm()
                # If get_llm() returns a gemini model string, we can try to build a LC instance
                if model_str.startswith('gemini/'):
                    os.environ['GOOGLE_API_KEY'] = self.api_keys[self.current_api_key_index]
                    try:
                        from langchain_google_genai import ChatGoogleGenerativeAI
                        model_name = self.gemini_model_name if hasattr(self, 'gemini_model_name') else 'gemini-2.5-flash'
                        self._llm_instance = ChatGoogleGenerativeAI(
                            model=model_name,
                            temperature=0.7
                        )
                        logger.info(f"Using ChatGoogleGenerativeAI for Gemini: {model_name}")
                        return self._llm_instance
                    except ImportError:
                        # Fallback: use string model name with litellm
                        self._llm_instance = model_str
                        return self._llm_instance
            except Exception as e:
                logger.error(f"Error creating Gemini LLM instance: {e}")
                # Fall through to Ollama
        
        # Fallback to Ollama
        if OLLAMA_AVAILABLE:
            try:
                self._llm_instance = ChatOllama(
                    model=self.ollama_model,
                    base_url="http://localhost:11434",
                    temperature=0.7,
                    num_predict=2000
                )
                self.llm_type = 'ollama'
                logger.info(f"Using ChatOllama: {self.ollama_model}")
                return self._llm_instance
            except ImportError:
                try:
                    self._llm_instance = OllamaLLM(
                        model=self.ollama_model,
                        base_url="http://localhost:11434",
                        temperature=0.7
                    )
                    self.llm_type = 'ollama'
                    logger.info(f"Using OllamaLLM: {self.ollama_model}")
                    return self._llm_instance
                except Exception as e:
                    logger.error(f"Error creating Ollama LLM instance: {e}")
                    raise RuntimeError(f"Failed to initialize Ollama LLM: {e}")
        
        raise RuntimeError("No LLM provider available")
    
    @property
    def crewai_model(self) -> str:
        """Get model name for CrewAI (with provider prefix)"""
        if self.llm_type == 'gemini':
            model_name = self.gemini_model_name if hasattr(self, 'gemini_model_name') else 'gemini-2.5-flash'
            return f"gemini/{model_name}"
        elif self.llm_type == 'ollama':
            return f"ollama/{self.ollama_model}"
        else:
            return f"ollama/{self.ollama_model}"  # Default fallback
    
    @property
    def model(self) -> str:
        """Get current model name"""
        if self.llm_type == 'gemini':
            return self.gemini_model_name if hasattr(self, 'gemini_model_name') else 'gemini-2.5-flash'
        else:
            return self.ollama_model
    
    def extract_document_content(self, text: str, filename: str) -> str:
        """
        Extract and structure content from document text
        Returns the text as-is without summarization
        """
        try:
            prompt = f"""You are a document content extractor. 
Your task is to extract and present the content from this document EXACTLY as it appears, preserving all important information.

Document: {filename}

Content:
{text}

Instructions:
- Extract ALL the content from the document
- Preserve the original structure and formatting as much as possible
- DO NOT summarize or reduce the content
- Present everything that's important in the document
- Keep all details, numbers, dates, and specific information
- If there are sections or headings, preserve them

Extracted Content:"""

            if self.llm_type == 'gemini' and GEMINI_AVAILABLE:
                response = self.gemini_model.generate_content(prompt)
                extracted_content = response.text
                logger.info(f"Successfully extracted content from {filename} using Gemini")
            else:
                # Fallback to Ollama
                import ollama
                response = ollama.chat(
                    model=self.ollama_model,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                extracted_content = response['message']['content']
                logger.info(f"Successfully extracted content from {filename} using Ollama")
            
            return extracted_content.strip()
            
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            # Return original text if LLM fails
            return f"**Original Document Content:**\n\n{text}"
    
    def chat(self, model: str, messages: list) -> dict:
        """
        Chat interface compatible with Ollama format
        """
        if self.llm_type == 'gemini' and GEMINI_AVAILABLE:
            # Convert messages format
            prompt = ""
            for msg in messages:
                if msg.get('role') == 'user':
                    prompt += msg.get('content', '')
            
            response = self.gemini_model.generate_content(prompt)
            return {
                'message': {
                    'content': response.text
                }
            }
        else:
            # Fallback to Ollama
            import ollama
            return ollama.chat(model=model, messages=messages)


# Global instance
gemini_service = GeminiService()

