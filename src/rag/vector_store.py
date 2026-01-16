"""
ChromaDB-based vector store for disaster event retrieval.
Manages real-time indexing and similarity search for RAG pipeline.
Supports incremental updates as new events stream in.
"""

import chromadb
from chromadb.config import Settings
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from src.rag.embedder import EmbeddingService
from src.utils.logger import app_logger

class DisasterVectorStore:
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "disaster_events",
        embedding_service: Optional[EmbeddingService] = None
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.logger = app_logger
        
        if embedding_service is None:
            self.embedding_service = EmbeddingService()
        else:
            self.embedding_service = embedding_service
        
        self._initialize_client()
    
    def _initialize_client(self):
        """
        Initialize ChromaDB client and collection.
        """
        try:
            self.logger.logger.info("Initializing ChromaDB vector store...")
            
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            self.logger.logger.info(
                f"Vector store initialized. Collection: {self.collection_name}, "
                f"Count: {self.collection.count()}"
            )
        
        except Exception as e:
            self.logger.log_error("DisasterVectorStore._initialize_client", e)
            raise
    
    def add_event(self, event_id: str, text_content: str, metadata: Dict[str, Any]):
        """
        Add or update a single disaster event in the vector store.
        
        Args:
            event_id: Unique event identifier
            text_content: Text representation for embedding
            metadata: Event metadata (disaster_type, severity, etc.)
        """
        try:
            embedding = self.embedding_service.embed_text(text_content)
            
            self.collection.upsert(
                ids=[event_id],
                embeddings=[embedding.tolist()],
                documents=[text_content],
                metadatas=[metadata]
            )
            
            self.logger.logger.debug(f"Added event to vector store: {event_id}")
        
        except Exception as e:
            self.logger.log_error("DisasterVectorStore.add_event", e)
    
    def add_events_batch(
        self,
        event_ids: List[str],
        text_contents: List[str],
        metadatas: List[Dict[str, Any]]
    ):
        """
        Batch add multiple events for efficiency.
        """
        try:
            if not event_ids:
                return
            
            embeddings = self.embedding_service.embed_batch(text_contents)
            
            self.collection.upsert(
                ids=event_ids,
                embeddings=embeddings.tolist(),
                documents=text_contents,
                metadatas=metadatas
            )
            
            self.logger.logger.info(f"Batch added {len(event_ids)} events to vector store")
        
        except Exception as e:
            self.logger.log_error("DisasterVectorStore.add_events_batch", e)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for relevant disaster events.
        
        Args:
            query: Natural language query
            top_k: Number of results to return
            filters: Metadata filters (e.g., {"disaster_type": "earthquake"})
            
        Returns:
            List of dicts with 'id', 'text', 'metadata', 'distance'
        """
        try:
            query_embedding = self.embedding_service.embed_text(query)
            
            where_clause = None
            if filters:
                where_clause = filters
            
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=where_clause
            )
            
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else 0.0
                })
            
            return formatted_results
        
        except Exception as e:
            self.logger.log_error("DisasterVectorStore.search", e)
            return []
    
    def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific event by ID.
        """
        try:
            result = self.collection.get(ids=[event_id], include=['documents', 'metadatas'])
            
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'text': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            return None
        
        except Exception as e:
            self.logger.log_error("DisasterVectorStore.get_event_by_id", e)
            return None
    
    def get_all_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve all events (for display/monitoring).
        """
        try:
            results = self.collection.get(
                limit=limit,
                include=['documents', 'metadatas']
            )
            
            events = []
            for i in range(len(results['ids'])):
                events.append({
                    'id': results['ids'][i],
                    'text': results['documents'][i],
                    'metadata': results['metadatas'][i]
                })
            
            return events
        
        except Exception as e:
            self.logger.log_error("DisasterVectorStore.get_all_events", e)
            return []
    
    def delete_event(self, event_id: str):
        """
        Remove event from vector store.
        """
        try:
            self.collection.delete(ids=[event_id])
            self.logger.logger.debug(f"Deleted event: {event_id}")
        except Exception as e:
            self.logger.log_error("DisasterVectorStore.delete_event", e)
    
    def count(self) -> int:
        """
        Get total number of events in store.
        """
        return self.collection.count()
    
    def reset(self):
        """
        Clear all data from collection.
        """
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.logger.logger.warning("Vector store reset - all data cleared")
        except Exception as e:
            self.logger.log_error("DisasterVectorStore.reset", e)
