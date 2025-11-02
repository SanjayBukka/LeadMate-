"""
Ollama LLM Service for document processing
"""
import ollama
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class OllamaService:
    """Service for interacting with Ollama LLM"""
    
    def __init__(self, model: str = "llama3.2:3b"):
        """
        Initialize Ollama service with specified model
        Using llama3.2:3b as it's the smallest and fastest
        """
        self.model = model
        # For CrewAI/litellm, we need to prefix with 'ollama/'
        self.crewai_model = f"ollama/{model}"
        self.client = ollama
        self._llm_instance = None
        
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

            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            extracted_content = response['message']['content']
            logger.info(f"Successfully extracted content from {filename} using {self.model}")
            return extracted_content.strip()
            
        except Exception as e:
            logger.error(f"Error extracting content with Ollama: {e}")
            # Return original text if LLM fails
            return f"**Original Document Content:**\n\n{text}"
    
    def get_llm(self):
        """
        Get LangChain-compatible LLM instance for CrewAI
        
        Returns:
            Ollama LLM instance compatible with LangChain/CrewAI
        """
        if self._llm_instance is None:
            try:
                import os
                # Disable litellm for CrewAI to use direct LLM
                os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'
                
                # Try different import methods
                try:
                    from langchain_ollama import ChatOllama
                    logger.info("Using langchain_ollama.ChatOllama")
                    
                    # Create LLM instance with ChatOllama (preferred for CrewAI)
                    self._llm_instance = ChatOllama(
                        model=self.model,
                        base_url="http://localhost:11434",
                        temperature=0.7,
                        num_predict=2000  # Max tokens to generate
                    )
                except ImportError:
                    try:
                        from langchain_community.llms import Ollama as OllamaLLM
                        logger.info("Using langchain_community.llms.Ollama")
                        
                        # Create LLM instance
                        self._llm_instance = OllamaLLM(
                            model=self.model,
                            base_url="http://localhost:11434",
                            temperature=0.7
                        )
                    except ImportError:
                        from langchain.llms import Ollama as OllamaLLM
                        logger.info("Using langchain.llms.Ollama")
                        
                        self._llm_instance = OllamaLLM(
                            model=self.model,
                            base_url="http://localhost:11434",
                            temperature=0.7
                        )
                
                logger.info(f"Created LLM instance with model: {self.model}")
                logger.info(f"LLM type: {type(self._llm_instance).__name__}")
                
            except Exception as e:
                logger.error(f"Error creating LLM instance: {e}")
                raise RuntimeError(f"Failed to initialize Ollama LLM: {e}")
        
        return self._llm_instance
    
    def check_model_availability(self) -> bool:
        """Check if the specified model is available"""
        try:
            models = self.client.list()
            available_models = [model['name'] for model in models.get('models', [])]
            is_available = any(self.model in model for model in available_models)
            
            if is_available:
                logger.info(f"Model {self.model} is available")
            else:
                logger.warning(f"Model {self.model} not found. Available models: {available_models}")
            
            return is_available
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False


# Global instance
ollama_service = OllamaService()

