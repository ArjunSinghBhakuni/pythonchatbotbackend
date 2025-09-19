#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_database import simple_db_manager
from embedding_service import EmbeddingService
from ollama_service import OllamaService
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chat():
    try:
        # Initialize services
        embedding_service = EmbeddingService()
        ollama_service = OllamaService()
        
        # Test message
        message = "what is dpdp"
        logger.info(f"Testing chat with message: '{message}'")
        
        # Get database session
        db = next(simple_db_manager.get_db())
        
        try:
            # Generate query embedding
            query_embedding = embedding_service.generate_embedding(message)
            logger.info(f"Generated query embedding with {len(query_embedding)} dimensions")
            
            # Check total embeddings
            count_result = db.execute(text("SELECT COUNT(*) FROM embeddings WHERE session_name = 'knowledge_base'"))
            total_count = count_result.scalar()
            logger.info(f"Total embeddings in knowledge_base: {total_count}")
            
            if total_count == 0:
                logger.warning("No embeddings found in knowledge_base")
                return
            
            # Search for relevant chunks
            result = db.execute(text(f"""
                SELECT content, 
                       1 - (embedding <=> '{query_embedding}'::vector) AS similarity
                FROM embeddings
                WHERE session_name = 'knowledge_base'
                ORDER BY embedding <=> '{query_embedding}'::vector
                LIMIT 5
            """))
            
            chunks = []
            for row in result:
                chunks.append({
                    "content": row[0],
                    "similarity": float(row[1])
                })
            
            logger.info(f"Found {len(chunks)} relevant chunks")
            
            if chunks:
                logger.info("Top chunk similarities:")
                for i, chunk in enumerate(chunks, 1):
                    logger.info(f"  {i}. Similarity: {chunk['similarity']:.4f}")
                    logger.info(f"     Content: {chunk['content'][:100]}...")
                
                # Generate response
                context = "\n\n".join([chunk["content"] for chunk in chunks])
                response = ollama_service.generate_response(message, context, [])
                logger.info(f"Generated response: {response}")
            else:
                logger.warning("No relevant chunks found")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in test_chat: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chat()


