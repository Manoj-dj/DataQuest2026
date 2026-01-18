"""
Embedding service using sentence-transformers for vector generation.
Provides efficient text-to-vector conversion for RAG retrieval.
Uses all-MiniLM-L6-v2 model (384 dimensions, fast inference).
Supports CLIP embeddings for multi-modal (text + image) retrieval.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union, Optional
import requests
from io import BytesIO
from PIL import Image
from src.utils.logger import app_logger


class EmbeddingService:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        image_model_name: Optional[str] = None
    ):
        self.model_name = model_name
        self.image_model_name = image_model_name or "openai/clip-vit-base-patch32"
        self.logger = app_logger
        self.image_model = None
        self._load_model()
        self._load_image_model()
    
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
    
    def _load_image_model(self):
        """
        Load CLIP model for image embeddings (optional, lazy loaded).
        Falls back gracefully if model cannot be loaded.
        """
        try:
            # Only load if CLIP is available
            try:
                from sentence_transformers import SentenceTransformer
                import os
                
                # Set environment variable to allow loading older models
                # This helps with torch.load compatibility
                os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
                
                # CLIP models can be loaded with sentence-transformers
                self.logger.logger.info(f"Loading image embedding model: {self.image_model_name}")
                
                # Try loading with trust_remote_code if needed
                try:
                    self.image_model = SentenceTransformer(self.image_model_name, trust_remote_code=True)
                except Exception:
                    # Fallback: try without trust_remote_code
                    try:
                        self.image_model = SentenceTransformer(self.image_model_name)
                    except Exception as e2:
                        # Last resort: try to use a different CLIP model that's more compatible
                        self.logger.logger.warning(f"Failed to load {self.image_model_name}, trying alternative...")
                        # Try a different CLIP variant
                        alt_model = "sentence-transformers/clip-ViT-B-32"
                        try:
                            self.image_model = SentenceTransformer(alt_model, trust_remote_code=True)
                            self.image_model_name = alt_model  # Update model name
                        except Exception:
                            raise e2  # Raise original error
                
                self.logger.logger.info("Image embedding model loaded successfully")
            except ImportError:
                self.logger.logger.warning("CLIP/image models not available - image embedding disabled")
                self.image_model = None
            except (ValueError, RuntimeError, Exception) as ve:
                # Handle torch version compatibility issues more broadly
                error_str = str(ve)
                if any(keyword in error_str for keyword in ["torch.load", "CVE", "v2.6", "weights_only", "security"]):
                    # Try upgrading torch warning or suggest upgrade
                    self.logger.logger.warning(
                        f"Image embedding model cannot be loaded due to torch version constraints. "
                        f"Image embeddings will be disabled. Error: {error_str[:150]}"
                    )
                    self.logger.logger.warning(
                        "To enable image embeddings, upgrade PyTorch: uv pip install --upgrade torch torchvision"
                    )
                    self.image_model = None
                else:
                    # Log the actual error but don't fail completely
                    self.logger.logger.warning(f"Failed to load image model: {error_str[:150]}")
                    self.image_model = None
        except Exception as e:
            self.logger.log_error("EmbeddingService._load_image_model", e)
            self.image_model = None
            self.logger.logger.warning("Image embedding disabled - falling back to text-only embeddings")
    
    def embed_image(self, image_url: str) -> Optional[np.ndarray]:
        """
        Generate embedding vector for an image from URL.
        
        Args:
            image_url: URL to the image
            
        Returns:
            numpy array of shape (embedding_dim,) or None if failed
        """
        if self.image_model is None:
            self.logger.logger.warning("Image embedding model not available")
            return None
        
        try:
            # Download image
            response = requests.get(image_url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Load image with PIL
            img = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Generate embedding
            embedding = self.image_model.encode(img, convert_to_numpy=True, show_progress_bar=False)
            
            return embedding
        
        except Exception as e:
            self.logger.log_error("EmbeddingService.embed_image", e)
            return None
    
    def embed_images_batch(self, image_urls: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple images efficiently.
        
        Args:
            image_urls: List of image URLs
            
        Returns:
            numpy array of shape (len(image_urls), embedding_dim)
        """
        if self.image_model is None:
            return np.zeros((len(image_urls), self.embedding_dim))
        
        embeddings = []
        for url in image_urls:
            emb = self.embed_image(url)
            if emb is not None:
                embeddings.append(emb)
            else:
                # Use zero vector for failed images
                embeddings.append(np.zeros(self.image_model.get_sentence_embedding_dimension()))
        
        return np.array(embeddings)
    
    def get_image_embedding_dimension(self) -> int:
        """
        Return the dimensionality of image embeddings.
        """
        if self.image_model is None:
            return 512  # Default CLIP dimension
        return self.image_model.get_sentence_embedding_dimension()