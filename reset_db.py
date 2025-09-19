#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_database import simple_db_manager
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    try:
        # Get database session
        db = next(simple_db_manager.get_db())
        
        try:
            # Clear all embeddings
            logger.info("Clearing all embeddings...")
            db.execute(text("DELETE FROM embeddings"))
            db.commit()
            logger.info("Database cleared successfully")
            
            # Check count
            count_result = db.execute(text("SELECT COUNT(*) FROM embeddings"))
            total_count = count_result.scalar()
            logger.info(f"Remaining embeddings: {total_count}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_database()






