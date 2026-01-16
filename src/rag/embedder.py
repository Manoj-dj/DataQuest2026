"""
Embedding service using sentence-transformers for vector generation.
Provides efficient text-to-vector conversion for RAG retrieval.
Uses all-MiniLM-L6-v2 model (384 dimensions, fast inference).
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
from src.utils.logger import app_logger

class EmbeddingService:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.logger = app_logger
        self._load_model()
    
    def _load_model(self):
        """
        Load sentence-transformer model with error handling.
        """
        try:
            self.logger.logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            self.logger.logger.info(
                f"Embedding model loaded. Dimension: {self.embedding_dim}"
            )
        except Exception as e:
            self.logger.log_error("EmbeddingService", e)
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for single text string.
        
        Args:
            text: Input text to embed
            
        Returns:
            numpy array of shape (embedding_dim,)
        """
        try:
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            return embedding
        except Exception as e:
            self.logger.log_error("EmbeddingService.embed_text", e)
            return np.zeros(self.embedding_dim)
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of text strings
            batch_size: Batch processing size
            
        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            return embeddings
        except Exception as e:
            self.logger.log_error("EmbeddingService.embed_batch", e)
            return np.zeros((len(texts), self.embedding_dim))
    
    def get_embedding_dimension(self) -> int:
        """
        Return the dimensionality of embeddings.
        """
        return self.embedding_dim
