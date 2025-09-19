#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def test_database():
    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_vu96xtNThwRn@ep-fancy-dream-adb1zo00-pooler.c-2.us-east-1.aws.neon.tech:5432/dpcDB?sslmode=require&sslcert=&sslkey=&sslrootcert=")
    
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("✅ Database connection successful!")
        
        # Check if embeddings table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'embeddings'
            );
        """)
        table_exists = cursor.fetchone()[0]
        print(f"📊 Embeddings table exists: {table_exists}")
        
        if table_exists:
            # Count total embeddings
            cursor.execute("SELECT COUNT(*) FROM embeddings")
            total_count = cursor.fetchone()[0]
            print(f"📈 Total embeddings: {total_count}")
            
            # Count embeddings by session
            cursor.execute("SELECT session_name, COUNT(*) FROM embeddings GROUP BY session_name")
            session_counts = cursor.fetchall()
            print("📋 Embeddings by session:")
            for session, count in session_counts:
                print(f"   - {session}: {count}")
            
            # Show sample content
            cursor.execute("SELECT content FROM embeddings WHERE session_name = 'knowledge_base' LIMIT 3")
            samples = cursor.fetchall()
            print("📝 Sample content:")
            for i, (content,) in enumerate(samples, 1):
                print(f"   {i}. {content[:100]}...")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_database()


