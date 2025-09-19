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
from gemini_ai_service import gemini_ai_service
from pdf_processor import PDFProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Chatbot & Risk Assessment - Gemini", version="3.0.0")

# Simple response cache for faster responses
response_cache = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pdf_processor = PDFProcessor()
UPLOADS_FOLDER = "uploads"

@app.on_event("startup")
async def startup_event():
    try:
        simple_db_manager.test_connection()
        # Drop and recreate tables on first startup
        simple_db_manager.create_tables(drop_existing=True)
        
        # Create uploads folder if it doesn't exist
        os.makedirs(UPLOADS_FOLDER, exist_ok=True)
        
        # Auto-train from uploads folder
        await auto_train_from_uploads()
        
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

async def auto_train_from_uploads():
    """Automatically train AI from all PDFs in uploads folder and delete them after processing"""
    try:
        pdf_files = glob.glob(os.path.join(UPLOADS_FOLDER, "*.pdf"))
        
        if not pdf_files:
            logger.info("No PDF files found in uploads folder")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            try:
                logger.info(f"Processing: {pdf_file}")
                
                # Extract text from PDF
                with open(pdf_file, 'rb') as f:
                    content = f.read()
                text_content = pdf_processor.extract_text_from_pdf_content(content)
                
                if not text_content.strip():
                    logger.warning(f"No text extracted from {pdf_file}")
                    # Delete the file even if no text was extracted
                    os.remove(pdf_file)
                    continue
                
                # Split into chunks
                chunks = pdf_processor.chunk_text(text_content)
                
                # Store chunks in database
                db = next(simple_db_manager.get_db())
                try:
                    for chunk in chunks:
                        embedding = gemini_embedding_service.generate_embedding(chunk)
                        
                        # Convert embedding to proper format for PostgreSQL vector
                        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                        
                        # Use f-string to avoid parameter binding issues
                        db.execute(text(f"""
                            INSERT INTO embeddings (session_name, content, embedding)
                            VALUES ('knowledge_base', :content, '{embedding_str}'::vector)
                        """), {
                            "content": chunk
                        })
                    
                    db.commit()
                    logger.info(f"Successfully processed {pdf_file}: {len(chunks)} chunks")
                    
                finally:
                    db.close()
                
                # Delete the PDF file after successful processing
                os.remove(pdf_file)
                logger.info(f"Deleted processed PDF: {pdf_file}")
                    
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
                # Delete the file even if processing failed to avoid reprocessing
                try:
                    os.remove(pdf_file)
                    logger.info(f"Deleted failed PDF: {pdf_file}")
                except:
                    pass
                continue
                
    except Exception as e:
        logger.error(f"Error in auto_train_from_uploads: {e}")

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
                "response": response
            }
        else:
            # Simple, concise response
            response = gemini_ai_service.generate_response(message, context, [])
            result = {
                "response": response
            }
        
        # Cache the response for faster future queries
        response_cache[cache_key] = result
        
        return result
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return {
            "response": "I'm sorry, I'm having trouble connecting to my knowledge base right now. Please try again in a moment."
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
        # Handle file upload if provided
        additional_context = ""
        if file:
            if file.filename.endswith('.pdf'):
                content = await file.read()
                additional_context = pdf_processor.extract_text_from_pdf_content(content)
            else:
                # For images, we'll just note that an image was provided
                additional_context = f"[Image file provided: {file.filename}]"
        
        if text_content:
            additional_context += f"\n\nAdditional text: {text_content}"
        
        # Get relevant knowledge base content
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
                "recommendations": []
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
            
            response = gemini_ai_service.generate_risk_assessment(risk_prompt, context)
            
            # Try to parse JSON response, fallback to structured response if parsing fails
            try:
                import json
                import re
                
                logger.info(f"Raw Gemini response: {response[:200]}...")
                
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
                    "recommendations": parsed_response.get("recommendations", ["Recommendations provided"])
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
                    "recommendations": ["Implement proper consent mechanisms", "Review data handling practices", "Conduct compliance audit"]
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
    """Manually retrain from uploads folder"""
    try:
        # Clear existing knowledge base
        db = next(simple_db_manager.get_db())
        try:
            db.execute(text("DELETE FROM embeddings WHERE session_name = 'knowledge_base'"))
            db.commit()
        finally:
            db.close()
        
        # Retrain from uploads
        await auto_train_from_uploads()
        
        return {"message": "Retraining completed successfully"}
        
    except Exception as e:
        logger.error(f"Error in retrain: {e}")
        raise HTTPException(status_code=500, detail="Error during retraining")

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a single PDF file"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save file to uploads folder
        file_path = os.path.join(UPLOADS_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the file immediately
        text_content = pdf_processor.extract_text_from_pdf_content(content)
        
        if not text_content.strip():
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF")
        
        # Split into chunks
        chunks = pdf_processor.chunk_text(text_content)
        
        # Store chunks in database
        db = next(simple_db_manager.get_db())
        try:
            for chunk in chunks:
                embedding = gemini_embedding_service.generate_embedding(chunk)
                
                # Convert embedding to proper format for PostgreSQL vector
                embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                
                db.execute(text(f"""
                    INSERT INTO embeddings (session_name, content, embedding)
                    VALUES ('knowledge_base', :content, '{embedding_str}'::vector)
                """), {
                    "content": chunk
                })
            
            db.commit()
            logger.info(f"Successfully processed {file.filename}: {len(chunks)} chunks")
            
        finally:
            db.close()
        
        # Delete the PDF file after successful processing
        os.remove(file_path)
        logger.info(f"Deleted processed PDF: {file_path}")
        
        return {
            "message": f"PDF processed successfully. {len(chunks)} chunks added to knowledge base.",
            "chunks_processed": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Error processing PDF upload: {e}")
        # Clean up file if it exists
        try:
            file_path = os.path.join(UPLOADS_FOLDER, file.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        raise HTTPException(status_code=500, detail="Error processing PDF file")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




