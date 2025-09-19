#!/usr/bin/env python3

import sys
sys.path.append('.')
from simple_database import SimpleDatabaseManager
from sqlalchemy import text

def check_chunks():
    db_manager = SimpleDatabaseManager()
    db = next(db_manager.get_db())
    
    try:
        # Get some sample chunks
        result = db.execute(text("SELECT content FROM embeddings WHERE session_name = 'knowledge_base' LIMIT 5"))
        
        print("=== SAMPLE CHUNKS ===")
        for i, row in enumerate(result):
            print(f"\nChunk {i+1}:")
            print(f"Length: {len(row[0])} characters")
            print(f"Content: {row[0][:300]}...")
            print("-" * 50)
        
        # Check for DPDP-related content
        result = db.execute(text("SELECT content FROM embeddings WHERE session_name = 'knowledge_base' AND content ILIKE '%DPDP%' LIMIT 3"))
        
        print("\n=== DPDP-RELATED CHUNKS ===")
        for i, row in enumerate(result):
            print(f"\nDPDP Chunk {i+1}:")
            print(f"Content: {row[0][:400]}...")
            print("-" * 50)
            
    finally:
        db.close()

if __name__ == "__main__":
    check_chunks()






