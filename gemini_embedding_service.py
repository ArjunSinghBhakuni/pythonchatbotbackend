import google.generativeai as genai
from typing import List, Dict, Any
import logging
import os
from dotenv import load_dotenv
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiEmbeddingService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "AIzaSyCk1XOPzJ8tTBTczHPhILjjEtzjAuGKLq4")
        genai.configure(api_key=self.api_key)
        self.model_name = "models/embedding-001"
        # Local fallback model (384-dim)
        self.local_model_name = os.getenv("LOCAL_EMBED_MODEL", "all-MiniLM-L6-v2")
        self.local_model = None
        logger.info("Gemini Embedding Service initialized")
    
    def _ensure_local_model(self):
        if self.local_model is None and SentenceTransformer is not None:
            logger.info(f"Loading local embedding fallback: {self.local_model_name}")
            self.local_model = SentenceTransformer(self.local_model_name)

    def _pad_or_truncate(self, vector: List[float], target_dim: int) -> List[float]:
        arr = np.array(vector, dtype=float)
        if arr.size == target_dim:
            return arr.tolist()
        if arr.size > target_dim:
            return arr[:target_dim].tolist()
        # pad with zeros
        padded = np.zeros(target_dim, dtype=float)
        padded[:arr.size] = arr
        return padded.tolist()

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini with graceful local fallback."""
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.warning(f"Gemini embedding failed, falling back to local model: {e}")
            # Fallback to local model
            self._ensure_local_model()
            if self.local_model is None:
                # No local model available
                raise
            local_vec = self.local_model.encode(text, convert_to_tensor=False).tolist()
            return self._pad_or_truncate(local_vec, 768)
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            embeddings = []
            for text in texts:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension used for storage/search (768)."""
        return 768

# Global embedding service instance
gemini_embedding_service = GeminiEmbeddingService()
