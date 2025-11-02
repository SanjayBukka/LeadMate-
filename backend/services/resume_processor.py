"""
Resume Processor Service
Extracts information from resumes using LLM
"""
import logging
import json
import re
from typing import Dict, Optional
from services.document_extractor import document_extractor
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class ResumeProcessor:
    """Service to process resumes and extract structured information"""
    
    def extract_resume_info(self, file_path: str, content_type: str, filename: str) -> Dict:
        """
        Extract structured information from resume
        
        Args:
            file_path: Path to resume file
            content_type: MIME type of file
            filename: Original filename
        
        Returns:
            Dictionary with extracted information
        """
        try:
            # Extract text from resume
            logger.info(f"Extracting text from resume: {filename}")
            resume_text = document_extractor.extract_text(file_path, content_type)
            
            if not resume_text or resume_text.startswith('['):
                logger.error(f"Failed to extract text from {filename}")
                return {
                    "error": "Could not extract text from resume",
                    "filename": filename
                }
            
            # Use LLM to extract structured information
            logger.info(f"Extracting structured data using LLM from {filename}")
            extracted_info = self._extract_structured_data(resume_text, filename)
            
            return extracted_info
            
        except Exception as e:
            logger.error(f"Error processing resume {filename}: {e}")
            return {
                "error": str(e),
                "filename": filename
            }
    
    def _extract_structured_data(self, resume_text: str, filename: str) -> Dict:
        """
        Use LLM to extract structured data from resume text
        
        Args:
            resume_text: Extracted text from resume
            filename: Original filename
        
        Returns:
            Dictionary with structured information
        """
        try:
            prompt = f"""
Analyze the following resume and extract structured information in JSON format.

Resume Text:
{resume_text}

Extract and return ONLY a valid JSON object with this EXACT structure (no additional text before or after):
{{
    "name": "full name of the person",
    "email": "email address if found, otherwise null",
    "phone": "phone number if found, otherwise null",
    "role": "primary job title or role (e.g., Frontend Developer, Data Scientist)",
    "experience": "total years of experience as a string (e.g., '5 years', '3+ years')",
    "education": ["list of degrees and certifications"],
    "techStack": ["list of all technologies, programming languages, frameworks mentioned"],
    "recentProjects": ["list of project names or descriptions"],
    "skills": {{
        "programmingLanguages": ["list of programming languages"],
        "frameworks": ["list of frameworks and libraries"],
        "databases": ["list of databases"],
        "tools": ["list of tools and technologies"],
        "softSkills": ["list of soft skills like leadership, communication, etc."]
    }}
}}

Important:
- Extract ALL technologies mentioned in the resume
- For role, choose the most recent or prominent job title
- For techStack, include all technologies (languages, frameworks, tools, databases)
- For recentProjects, list the most recent or significant projects
- If information is not found, use null or empty array []
- Return ONLY valid JSON, no markdown formatting or additional text

JSON Response:"""

            # Call LLM (Gemini with Ollama fallback)
            response = gemini_service.chat(
                model=gemini_service.model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            response_text = response['message']['content']
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                extracted_data = json.loads(json_str)
                
                # Validate and clean data
                cleaned_data = self._clean_extracted_data(extracted_data)
                
                logger.info(f"Successfully extracted data from {filename}")
                return cleaned_data
            else:
                logger.error(f"Could not find JSON in LLM response for {filename}")
                return {
                    "error": "Could not parse resume data",
                    "filename": filename,
                    "name": "Unknown",
                    "role": "Unknown",
                    "email": None,
                    "techStack": [],
                    "recentProjects": []
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for {filename}: {e}")
            return {
                "error": f"JSON parsing error: {str(e)}",
                "filename": filename,
                "name": "Unknown",
                "role": "Unknown"
            }
        except Exception as e:
            logger.error(f"Error extracting structured data from {filename}: {e}")
            return {
                "error": str(e),
                "filename": filename
            }
    
    def _clean_extracted_data(self, data: Dict) -> Dict:
        """
        Clean and validate extracted data
        
        Args:
            data: Raw extracted data
        
        Returns:
            Cleaned data dictionary
        """
        # Ensure required fields exist
        cleaned = {
            "name": data.get("name", "Unknown"),
            "email": data.get("email") or None,
            "phone": data.get("phone") or None,
            "role": data.get("role", "Unknown"),
            "experience": data.get("experience") or None,
            "education": data.get("education", []),
            "techStack": data.get("techStack", []),
            "recentProjects": data.get("recentProjects", []),
            "skills": data.get("skills", {})
        }
        
        # Ensure lists are actually lists
        for key in ["education", "techStack", "recentProjects"]:
            if not isinstance(cleaned[key], list):
                cleaned[key] = []
        
        # Ensure skills is a dict
        if not isinstance(cleaned["skills"], dict):
            cleaned["skills"] = {}
        
        # Convert None strings to actual None
        for key in ["email", "phone", "experience"]:
            if cleaned[key] == "null" or cleaned[key] == "None":
                cleaned[key] = None
        
        return cleaned


# Global instance
resume_processor = ResumeProcessor()

