import requests
import json
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "gemma:2b"  # Very small model that fits in 2GB RAM
    
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama service not available: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    def generate_response(self, prompt: str, context: str = "", conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate response using Ollama"""
        try:
            # Prepare the full prompt with context
            full_prompt = self._prepare_prompt(prompt, context, conversation_history)
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "max_tokens": 200,
                    "num_predict": 100
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', '').strip()
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return "Sorry, I'm having trouble generating a response right now."
                
        except Exception as e:
            logger.error(f"Error generating response with Ollama: {e}")
            return "Sorry, I encountered an error while processing your request."
    
    def generate_risk_assessment(self, prompt: str, context: str = "") -> str:
        """Generate detailed risk assessment response with longer timeout and more tokens"""
        try:
            # Prepare the full prompt with context
            full_prompt = self._prepare_risk_prompt(prompt, context)
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1000,
                    "num_predict": 500
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # Longer timeout for complex analysis
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', '').strip()
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return "Sorry, I'm having trouble generating a risk assessment right now."
                
        except Exception as e:
            logger.error(f"Error generating risk assessment with Ollama: {e}")
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
    
    def stream_response(self, prompt: str, context: str = "") -> str:
        """Generate streaming response (for future use)"""
        try:
            full_prompt = self._prepare_prompt(prompt, context)
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=60
            )
            
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if 'response' in data:
                                full_response += data['response']
                        except json.JSONDecodeError:
                            continue
                return full_response.strip()
            else:
                return "Error generating response"
                
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            return "Error generating response"

# Global Ollama service instance
ollama_service = OllamaService()

