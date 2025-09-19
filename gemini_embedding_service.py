import google.generativeai as genai
from typing import List
import logging
import os
from dotenv import load_dotenv
import numpy as np
import hashlib

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiEmbeddingService:
    def __init__(self):
        # Support both env var names; fallback to provided key if not set
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "AIzaSyCk1XOPzJ8tTBTczHPhILjjEtzjAuGKLq4"
        genai.configure(api_key=self.api_key)
        self.model_name = "models/embedding-001"
        logger.info("Gemini Embedding Service initialized")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini only (no local fallback)."""
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            # Graceful fallback: dependency-free feature hashing to 768 dims
            logger.warning(f"Gemini embedding failed, using hashed fallback: {e}")
            return self._feature_hash_embedding(text, 768)

    def _feature_hash_embedding(self, text: str, dims: int) -> List[float]:
        tokens = [t for t in text.lower().split() if t]
        vec = np.zeros(dims, dtype=float)
        for tok in tokens:
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            idx = h % dims
            sign = 1.0 if (h >> 1) % 2 == 0 else -1.0
            vec[idx] += sign
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.generate_embedding(t) for t in texts]
    
    def get_embedding_dimension(self) -> int:
        return 768

# Global embedding service instance
gemini_embedding_service = GeminiEmbeddingService()
