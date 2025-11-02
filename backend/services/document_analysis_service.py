"""
Document Analysis Service
Handles automatic document summarization and stack analysis
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import requests
import json

logger = logging.getLogger(__name__)


class DocumentAnalysisService:
    """Service for automatic document analysis and summarization"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
    
    async def analyze_document(self, project_id: str, company_id: str, lead_id: str, document_content: str, filename: str) -> Dict:
        """
        Analyze uploaded document and generate summary + stack analysis
        
        Args:
            project_id: Project ID
            company_id: Company ID  
            lead_id: Lead ID
            document_content: Extracted document content
            filename: Original filename
            
        Returns:
            Dict with summary and stack analysis
        """
        try:
            # Generate document summary
            summary = await self._generate_document_summary(document_content, filename)
            
            # Generate stack analysis
            stack_analysis = await self._generate_stack_analysis(document_content, filename)
            
            # Store analysis results
            analysis_result = {
                "project_id": project_id,
                "company_id": company_id,
                "lead_id": lead_id,
                "filename": filename,
                "summary": summary,
                "stack_analysis": stack_analysis,
                "analyzed_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
            logger.info(f"Document analysis completed for {filename}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing document {filename}: {e}")
            return {
                "project_id": project_id,
                "company_id": company_id,
                "lead_id": lead_id,
                "filename": filename,
                "summary": f"Error analyzing document: {str(e)}",
                "stack_analysis": f"Error analyzing document: {str(e)}",
                "analyzed_at": datetime.utcnow().isoformat(),
                "status": "error"
            }
    
    async def _generate_document_summary(self, content: str, filename: str) -> str:
        """Generate document summary using Document Agent"""
        try:
            # Use Document Agent to generate summary
            response = requests.post(
                f"{self.base_url}/api/agents/doc/chat",
                json={
                    "message": f"Please provide a comprehensive summary of this document: {filename}\n\nContent: {content[:2000]}...",
                    "company_id": "analysis",
                    "lead_id": "summary"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Summary generation failed')
            else:
                return f"Failed to generate summary: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Error generating summary: {str(e)}"
    
    async def _generate_stack_analysis(self, content: str, filename: str) -> str:
        """Generate stack analysis using Stack Agent"""
        try:
            # Use Stack Agent to analyze tech stack
            response = requests.post(
                f"{self.base_url}/api/agents/stack/chat",
                json={
                    "message": f"Analyze the technology stack and requirements from this document: {filename}\n\nContent: {content[:2000]}...",
                    "company_id": "analysis",
                    "lead_id": "stack"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Stack analysis failed')
            else:
                return f"Failed to generate stack analysis: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error generating stack analysis: {e}")
            return f"Error generating stack analysis: {str(e)}"
    
    async def get_document_analysis(self, project_id: str) -> List[Dict]:
        """Get all document analyses for a project"""
        try:
            from database import get_database
            db = get_database()
            
            analyses = db.document_analyses.find({"project_id": project_id}).sort("analyzed_at", -1)
            return list(analyses)
            
        except Exception as e:
            logger.error(f"Error getting document analyses: {e}")
            return []
    
    async def store_analysis(self, analysis_data: Dict) -> bool:
        """Store analysis results in database"""
        try:
            from database import get_database
            db = get_database()
            
            result = db.document_analyses.insert_one(analysis_data)
            return result.inserted_id is not None
            
        except Exception as e:
            logger.error(f"Error storing analysis: {e}")
            return False


# Global instance
document_analysis_service = DocumentAnalysisService()
