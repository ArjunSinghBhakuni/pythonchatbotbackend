from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import os
import glob
from datetime import datetime
import hashlib

from simple_database import simple_db_manager
from gemini_embedding_service import gemini_embedding_service
from ollama_service import ollama_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Chatbot & Risk Assessment", version="2.0.0")

# Simple response cache for faster responses
response_cache = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOADS_FOLDER = "uploads"

@app.on_event("startup")
async def startup_event():
    try:
        simple_db_manager.test_connection()
        simple_db_manager.create_tables()
        
        # Create uploads folder if it doesn't exist (kept for backward compatibility)
        os.makedirs(UPLOADS_FOLDER, exist_ok=True)
        
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

async def auto_train_from_uploads():
    """Deprecated: PDF auto-training removed. No-op."""
    logger.info("auto_train_from_uploads is deprecated and has been disabled.")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/chat")
async def chat(
    message: str = Form(...),
    db: Session = Depends(simple_db_manager.get_db)
):
    """Simple chat endpoint - no session required"""
    try:
        # Check cache first for faster responses
        cache_key = hashlib.md5(message.lower().strip().encode()).hexdigest()
        if cache_key in response_cache:
            logger.info(f"Cache hit for query: '{message}'")
            return response_cache[cache_key]
        
        # Generate embedding at request time using Gemini
        query_embedding = gemini_embedding_service.generate_embedding(message)
        
        # Search all knowledge base with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # First, let's check if we have any data in the database
                count_result = db.execute(text("SELECT COUNT(*) FROM embeddings WHERE session_name = 'knowledge_base'"))
                total_count = count_result.scalar()
                logger.info(f"Total embeddings in knowledge_base: {total_count}")
                
                if total_count == 0:
                    logger.warning("No embeddings found in knowledge_base")
                    chunks = []
                    break
                
                result = db.execute(text(f"""
                    SELECT content, 
                           1 - (embedding <=> '{query_embedding}'::vector) AS similarity
                    FROM embeddings
                    WHERE session_name = 'knowledge_base'
                    ORDER BY embedding <=> '{query_embedding}'::vector
                    LIMIT 3
                """))
                
                chunks = []
                for row in result:
                    chunks.append({
                        "content": row[0],
                        "similarity": float(row[1])
                    })
                
                logger.info(f"Found {len(chunks)} relevant chunks for query: '{message}'")
                break
                
            except Exception as db_error:
                logger.warning(f"Database query attempt {attempt + 1} failed: {db_error}")
                if attempt == max_retries - 1:
                    raise db_error
                # Wait before retry
                import time
                time.sleep(1)
        
        context = "\n\n".join([chunk["content"] for chunk in chunks])
        
        if not chunks:
            response = "I don't have any knowledge to answer your question. Please add PDF files to the uploads folder and restart the server."
            result = {
                "response": response,
                "sources": []
            }
        else:
            # Simple, concise response
            response = ollama_service.generate_response(message, context, [])
            result = {
                "response": response,
                "sources": chunks
            }
        
        # Cache the response for faster future queries
        response_cache[cache_key] = result
        
        return result
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return {
            "response": "I'm sorry, I'm having trouble connecting to my knowledge base right now. Please try again in a moment.",
            "sources": []
        }

@app.post("/risk-assessment")
async def risk_assessment(
    query: str = Form(...),
    file: UploadFile = File(None),
    text_content: str = Form(None),
    db: Session = Depends(simple_db_manager.get_db)
):
    """Complex risk assessment endpoint"""
    try:
        # PDF processing removed; only consider optional text_content
        additional_context = ""
        
        if text_content:
            additional_context += f"\n\nAdditional text: {text_content}"
        
        # Get relevant knowledge base content
        # Generate embedding at request time using Gemini
        query_embedding = gemini_embedding_service.generate_embedding(query)
        
        result = db.execute(text(f"""
            SELECT content, 
                   1 - (embedding <=> '{query_embedding}'::vector) AS similarity
            FROM embeddings
            WHERE session_name = 'knowledge_base'
            ORDER BY embedding <=> '{query_embedding}'::vector
            LIMIT 10
        """))
        
        chunks = []
        for row in result:
            chunks.append({
                "content": row[0],
                "similarity": float(row[1])
            })
        
        context = "\n\n".join([chunk["content"] for chunk in chunks])
        
        # Add additional context if provided
        if additional_context:
            context += f"\n\nAdditional Information:\n{additional_context}"
        
        if not chunks and not additional_context:
            return {
                "analysis": "I don't have sufficient knowledge to perform risk assessment. Please add PDF files to the uploads folder and restart the server.",
                "risk_level": "UNKNOWN",
                "risks": [],
                "legal_implications": [],
                "technical_considerations": [],
                "recommendations": [],
                "sources": []
            }
        else:
            # Complex risk assessment prompt
            risk_prompt = f"""
            You are a risk assessment expert. Analyze the following query and provide a structured risk assessment.
            
            Query: {query}
            
            Context: {context}
            
            Provide your response in this exact JSON format:
            {{
                "analysis": "Brief summary of the risk assessment",
                "risk_level": "HIGH/MEDIUM/LOW",
                "risks": ["Risk 1", "Risk 2", "Risk 3"],
                "legal_implications": ["Legal implication 1", "Legal implication 2"],
                "technical_considerations": ["Technical consideration 1", "Technical consideration 2"],
                "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
            }}
            
            Be thorough, professional, and provide actionable insights. Focus on DPDP Act 2023 compliance and data protection risks.
            """
            
            response = ollama_service.generate_risk_assessment(risk_prompt, context)
            
            # Try to parse JSON response, fallback to structured response if parsing fails
            try:
                import json
                import re
                
                logger.info(f"Raw Ollama response: {response[:200]}...")
                
                # Clean the response - remove any leading/trailing whitespace
                response = response.strip()
                
                # Try to extract JSON from the response if it's wrapped in text
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    logger.info(f"Extracted JSON: {json_str[:100]}...")
                    parsed_response = json.loads(json_str)
                else:
                    # Try to parse the entire response as JSON
                    parsed_response = json.loads(response)
                
                # Validate that we have the required fields
                if not isinstance(parsed_response, dict):
                    raise ValueError("Response is not a dictionary")
                
                return {
                    "analysis": parsed_response.get("analysis", "Risk assessment completed based on knowledge base"),
                    "risk_level": parsed_response.get("risk_level", "MEDIUM"),
                    "risks": parsed_response.get("risks", ["Risk assessment completed"]),
                    "legal_implications": parsed_response.get("legal_implications", ["Legal implications identified"]),
                    "technical_considerations": parsed_response.get("technical_considerations", ["Technical considerations noted"]),
                    "recommendations": parsed_response.get("recommendations", ["Recommendations provided"]),
                    "sources": chunks
                }
            except Exception as parse_error:
                logger.warning(f"JSON parsing failed: {parse_error}")
                logger.warning(f"Response that failed to parse: {response}")
                
                # Create a structured response based on the knowledge base chunks
                analysis_text = f"Based on the knowledge base analysis: {response[:300]}..." if len(response) > 300 else response
                
                # Extract risk level from response if possible
                risk_level = "MEDIUM"
                if "high" in response.lower():
                    risk_level = "HIGH"
                elif "low" in response.lower():
                    risk_level = "LOW"
                
                return {
                    "analysis": analysis_text,
                    "risk_level": risk_level,
                    "risks": ["Data privacy violations", "Regulatory non-compliance", "Security vulnerabilities"],
                    "legal_implications": ["DPDP Act violations", "Potential fines and penalties"],
                    "technical_considerations": ["Data security gaps", "Access control issues"],
                    "recommendations": ["Implement proper consent mechanisms", "Review data handling practices", "Conduct compliance audit"],
                    "sources": chunks
                }
        
    except Exception as e:
        logger.error(f"Error in risk assessment: {e}")
        raise HTTPException(status_code=500, detail="Error processing risk assessment")

@app.get("/knowledge-stats")
async def knowledge_stats(db: Session = Depends(simple_db_manager.get_db)):
    """Get knowledge base statistics"""
    try:
        result = db.execute(text("""
            SELECT COUNT(*) as total_chunks
            FROM embeddings
            WHERE session_name = 'knowledge_base'
        """))
        
        total_chunks = result.fetchone()[0]
        
        return {
            "total_chunks": total_chunks,
            "knowledge_base_size": f"{total_chunks} knowledge chunks",
            "status": "ready" if total_chunks > 0 else "empty"
        }
        
    except Exception as e:
        logger.error(f"Error getting knowledge stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving knowledge statistics")

@app.post("/retrain")
async def retrain():
    """Deprecated: Retraining disabled (no PDF processing)."""
    return {"message": "Retraining is disabled. Upload-based training has been removed."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
