import google.generativeai as genai
from typing import List, Dict, Any, Optional
import logging
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiAIService:
    def __init__(self):
        # Support both env var names
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Gemini AI Service initialized")
    
    def generate_response(self, prompt: str, context: str = "", conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate response using Gemini"""
        try:
            # Prepare the full prompt with context
            full_prompt = self._prepare_prompt(prompt, context, conversation_history)
            
            response = self.model.generate_content(full_prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating response with Gemini: {e}")
            return "Sorry, I encountered an error while processing your request."
    
    def generate_risk_assessment(self, prompt: str, context: str = "") -> str:
        """Generate detailed risk assessment response"""
        try:
            # Prepare the full prompt with context
            full_prompt = self._prepare_risk_prompt(prompt, context)
            
            response = self.model.generate_content(full_prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating risk assessment with Gemini: {e}")
            return "Sorry, I encountered an error while processing your risk assessment request."
    
    def _prepare_risk_prompt(self, query: str, context: str = "") -> str:
        """Prepare detailed risk assessment prompt"""
        system_prompt = """You are a data protection and privacy risk assessment expert. You MUST use the provided knowledge base context to analyze risks.

IMPORTANT: Use ONLY the information from the knowledge base context below. Do not make up information.

Query: {query}

Knowledge Base Context:
{context}

Based on the knowledge base context above, provide a comprehensive risk assessment in this EXACT JSON format (no additional text before or after):

{{
    "analysis": "Detailed analysis based on the knowledge base context",
    "risk_level": "HIGH/MEDIUM/LOW",
    "risks": ["Specific risk 1 from context", "Specific risk 2 from context", "Specific risk 3 from context"],
    "legal_implications": ["Legal implication 1 from context", "Legal implication 2 from context"],
    "technical_considerations": ["Technical consideration 1 from context", "Technical consideration 2 from context"],
    "recommendations": ["Recommendation 1 based on context", "Recommendation 2 based on context", "Recommendation 3 based on context"]
}}

Focus on DPDP Act 2023, GDPR, and data protection compliance. Use specific information from the knowledge base."""
        
        if context:
            full_prompt = system_prompt.format(context=context, query=query)
        else:
            full_prompt = f"""You are a data protection risk assessment expert.

Query: {query}

Since no knowledge base context is provided, provide a general risk assessment in this EXACT JSON format:

{{
    "analysis": "General risk assessment - no specific context available",
    "risk_level": "MEDIUM",
    "risks": ["Data collection without consent", "Inadequate privacy protection", "Regulatory non-compliance"],
    "legal_implications": ["Potential DPDP Act violations", "Regulatory penalties"],
    "technical_considerations": ["Data security vulnerabilities", "Access control issues"],
    "recommendations": ["Implement proper consent mechanisms", "Review privacy policies", "Conduct compliance audit"]
}}"""
        
        return full_prompt
    
    def _prepare_prompt(self, query: str, context: str = "", conversation_history: Optional[List[Dict]] = None) -> str:
        """Prepare the prompt with context and conversation history"""
        system_prompt = """You are a DPDP Act 2023 assistant. Answer briefly and clearly.

RULES:
1. Use ONLY the context provided
2. Keep answers SHORT (1-2 sentences max)
3. If no info in context, say "Not found in DPDP Act"
4. Be direct and concise

CONTEXT: {context}

Q: {query}
A:"""
        
        if context:
            full_prompt = system_prompt.format(context=context, query=query)
        else:
            full_prompt = f"""You are a DPDP Act 2023 legal assistant. 

QUESTION: {query}

ANSWER: I could not find this information in the DPDP Act 2023. Please ensure the relevant documents are uploaded."""
        
        return full_prompt

# Global Gemini AI service instance
gemini_ai_service = GeminiAIService()

