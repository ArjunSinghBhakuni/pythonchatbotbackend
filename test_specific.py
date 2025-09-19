#!/usr/bin/env python3

import sys
sys.path.append('.')
from embedding_service import EmbeddingService
from simple_database import SimpleDatabaseManager
from ollama_service import OllamaService
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_specific_questions():
    # Initialize services
    embedding_service = EmbeddingService()
    db_manager = SimpleDatabaseManager()
    ollama_service = OllamaService()
    
    questions = [
        "What is DPDP Act 2023?",
        "What is the Digital Personal Data Protection Act?",
        "What is a data principal?",
        "What are the rights of data principals?"
    ]
    
    for question in questions:
        print(f"\n{'='*60}")
        print(f"QUESTION: {question}")
        print('='*60)
        
        try:
            # Generate query embedding
            query_embedding = embedding_service.generate_embedding(question)
            logger.info(f"Generated query embedding with {len(query_embedding)} dimensions")
            
            # Search database
            db = next(db_manager.get_db())
            try:
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
                
                logger.info(f"Found {len(chunks)} relevant chunks")
                
                if chunks:
                    print(f"\nTOP CHUNKS:")
                    for i, chunk in enumerate(chunks):
                        print(f"{i+1}. Similarity: {chunk['similarity']:.4f}")
                        print(f"   Content: {chunk['content'][:200]}...")
                        print()
                    
                    # Generate response
                    context = "\n\n".join([chunk["content"] for chunk in chunks])
                    response = ollama_service.generate_response(question, context)
                    
                    print(f"AI RESPONSE:")
                    print(f"{response}")
                else:
                    print("No relevant chunks found")
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error processing question '{question}': {e}")
            print(f"Error: {e}")

if __name__ == "__main__":
    test_specific_questions()






