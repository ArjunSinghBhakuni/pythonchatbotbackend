import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SimpleDatabaseManager:
    def __init__(self):
        # Database configuration (uses provided Neon URL by default; env can override)
        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql://neondb_owner:npg_vu96xtNThwRn@ep-fancy-dream-adb1zo00-pooler.c-2.us-east-1.aws.neon.tech:5432/dpcDB?sslmode=require&channel_binding=require"
        )
        self.engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10,
            echo=False
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def create_tables(self, drop_existing: bool = False):
        """Create simple tables with option to drop existing"""
        try:
            with self.engine.connect() as conn:
                # Enable pgvector extension
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                
                if drop_existing:
                    # Drop existing tables
                    conn.execute(text("DROP TABLE IF EXISTS embeddings CASCADE"))
                    conn.execute(text("DROP TABLE IF EXISTS compliance_embeddings CASCADE"))
                    conn.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
                    logger.info("Dropped existing tables")
                
                # Create simple embeddings table with Gemini embedding dimensions (768)
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS embeddings (
                        id BIGSERIAL PRIMARY KEY,
                        session_name TEXT NOT NULL,
                        content TEXT NOT NULL,
                        embedding VECTOR(768),
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                
                # Create index for fast similarity search
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS embeddings_idx 
                    ON embeddings USING ivfflat (embedding vector_cosine_ops) 
                    WITH (lists = 100)
                """))
                
                conn.commit()
                logger.info("Simple database tables created successfully")
                
        except Exception as e:
            logger.error(f"Error creating simple tables: {e}")
            raise
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("Database connection successful")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

# Global database manager instance
simple_db_manager = SimpleDatabaseManager()
