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
import os
import shutil
import re
from src.rag.embedder import EmbeddingService
from src.utils.logger import app_logger

class DisasterVectorStore:
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "disaster_events",
        embedding_service: Optional[EmbeddingService] = None
    ):
        # Convert to absolute path to avoid relative path issues
        if not os.path.isabs(persist_directory):
            persist_directory = os.path.abspath(persist_directory)
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
        Handles schema mismatches by deleting the database file directly.
        """
        
        try:
            self.logger.logger.info(f"Initializing ChromaDB vector store at: {self.persist_directory}")
            
            # Ensure parent directory exists and is writable
            parent_dir = os.path.dirname(self.persist_directory)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            # Ensure the persist directory exists and is writable
            os.makedirs(self.persist_directory, exist_ok=True)
            os.chmod(self.persist_directory, 0o755)
            
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            try:
                # Try to get existing collection
                self.collection = self.client.get_collection(name=self.collection_name)
                self.logger.logger.info(f"Loaded existing collection: {self.collection_name}")
                
                # Test if collection is accessible by counting
                _ = self.collection.count()
                
            except Exception as get_error:
                # Check if it's a schema error (not just "collection doesn't exist")
                error_str = str(get_error).lower()
                
                # Distinguish between "collection doesn't exist" (normal) vs schema errors
                # Normal case: "Collection [disaster_events] does not exist" - just create it
                # Corruption case: "Collection [842ac9cc-6818-4892-8c43-06d2b6575442] does not exist" - UUID reference
                # Check if error mentions a UUID (long string with hyphens in brackets)
                is_uuid_corruption = False
                if "collection [" in error_str and "does not exist" in error_str:
                    try:
                        bracket_content = error_str.split("collection [")[1].split("]")[0]
                        # UUIDs are ~36 chars with hyphens, collection names are usually < 30 chars
                        if len(bracket_content) > 30 and "-" in bracket_content:
                            is_uuid_corruption = True
                    except:
                        pass
                
                # Schema errors are: column errors, SQLite errors, or UUID corruption
                # "collection does not exist" WITHOUT UUID corruption is NOT a schema error
                is_schema_error = (("no such column" in error_str or "schema" in error_str or 
                                 "operationalerror" in error_str or "sqlite" in error_str) and
                                 not "collection" in error_str) or is_uuid_corruption
                
                # Normal "collection does not exist" - this is expected for new databases
                is_collection_not_found = (("does not exist" in error_str or "notfound" in error_str) and 
                                         not is_uuid_corruption)
                
                if is_schema_error:
                    # This is a real schema error - need to reset database
                    self.logger.logger.warning(f"Database schema mismatch detected: {str(get_error)[:100]}")
                    self.logger.logger.warning("Deleting database files to reset schema...")
                    
                    # Close client before deleting files
                    try:
                        del self.client
                    except:
                        pass
                    
                    # Delete the entire database directory to reset schema
                    if os.path.exists(self.persist_directory):
                        try:
                            # Remove directory and all contents
                            shutil.rmtree(self.persist_directory)
                            self.logger.logger.info(f"Deleted database directory: {self.persist_directory}")
                            
                            # Wait a moment for file system to sync
                            import time
                            time.sleep(0.5)
                            
                        except Exception as del_error:
                            self.logger.logger.error(f"Failed to delete database directory: {del_error}")
                            raise
                    
                    # Ensure parent directory exists and is writable
                    parent_dir = os.path.dirname(self.persist_directory) if os.path.dirname(self.persist_directory) else '.'
                    os.makedirs(parent_dir, exist_ok=True)
                    
                    # Recreate the directory with proper permissions BEFORE creating client
                    os.makedirs(self.persist_directory, exist_ok=True)
                    os.chmod(self.persist_directory, 0o755)
                    
                    # Use a small delay to ensure filesystem is ready
                    import time
                    time.sleep(0.3)
                    
                    # Recreate client
                    self.client = chromadb.PersistentClient(
                        path=self.persist_directory,
                        settings=Settings(
                            anonymized_telemetry=False,
                            allow_reset=True
                        )
                    )
                    self.collection = self.client.create_collection(
                        name=self.collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )
                    self.logger.logger.info(f"Created new collection after schema reset: {self.collection_name}")
                elif is_collection_not_found:
                    # Collection simply doesn't exist - this is normal for a new database
                    # Just create it without deleting anything
                    self.collection = self.client.create_collection(
                        name=self.collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )
                    self.logger.logger.info(f"Created new collection: {self.collection_name}")
                else:
                    # Unknown error - try to create collection anyway
                    self.logger.logger.warning(f"Unexpected error getting collection: {str(get_error)[:100]}")
                    try:
                        self.collection = self.client.create_collection(
                            name=self.collection_name,
                            metadata={"hnsw:space": "cosine"}
                        )
                        self.logger.logger.info(f"Created new collection: {self.collection_name}")
                    except Exception as create_error:
                        self.logger.log_error("DisasterVectorStore._initialize_client (create collection)", create_error)
                        raise
            
            self.logger.logger.info(
                f"Vector store initialized. Collection: {self.collection_name}, "
                f"Count: {self.collection.count()}"
            )
        
        except Exception as e:
            error_str = str(e).lower()
            # Final fallback - delete database files if schema error persists
            if "no such column" in error_str or "schema" in error_str or "operationalerror" in error_str:
                self.logger.logger.warning("Critical schema error - deleting database files as final fallback...")
                try:
                    if os.path.exists(self.persist_directory):
                        shutil.rmtree(self.persist_directory)
                        self.logger.logger.info("Database directory deleted. Please restart the application.")
                    raise RuntimeError(
                        f"Database schema was incompatible and has been deleted. "
                        f"Please restart the application. Original error: {str(e)[:200]}"
                    )
                except Exception as final_error:
                    self.logger.log_error("DisasterVectorStore._initialize_client (final fallback)", final_error)
                    raise
            else:
                self.logger.log_error("DisasterVectorStore._initialize_client", e)
                raise
    
    def _reset_database(self):
        """
        Helper method to completely reset the database directory.
        Used when UUID corruption or schema errors are detected.
        """
        try:
            # Close client before deleting
            try:
                del self.client
            except:
                pass
            
            # Delete entire database directory
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
                import time
                time.sleep(0.5)
            
            # Recreate with proper permissions
            os.makedirs(self.persist_directory, exist_ok=True)
            os.chmod(self.persist_directory, 0o755)
            
            # Recreate client
            self.client = chromadb.PersistentClient(
                path=os.path.abspath(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Create collection
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            self.logger.logger.info(f"Database reset complete. Created new collection: {self.collection_name}")
        except Exception as e:
            self.logger.log_error("DisasterVectorStore._reset_database", e)
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
            # Always get a fresh collection reference to avoid stale UUID issues
            self.collection = self.client.get_collection(name=self.collection_name)
            
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
            
            # Always get a fresh collection reference to avoid stale UUID issues
            self.collection = self.client.get_collection(name=self.collection_name)
            
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
            # Always get a fresh collection reference to avoid stale UUID issues
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
            except Exception as get_error:
                error_msg = str(get_error)
                error_str = error_msg.lower()
                
                # Check for UUID corruption - if so, reset database
                # Error format could be: "Collection [UUID] does not exist" or "Error getting collection: Collection [UUID] does not exist"
                # Log error details to help debug
                self.logger.logger.warning(f"get_collection failed in search. Error type: {type(get_error).__name__}, Message: {error_msg[:200]}")
                
                if "collection [" in error_str and "does not exist" in error_str:
                    try:
                        # Extract content between brackets using regex-like approach
                        # Try to find pattern like "Collection [...]" or "collection [...]"
                        bracket_match = re.search(r'[Cc]ollection\s+\[([^\]]+)\]', error_msg)
                        if bracket_match:
                            bracket_content = bracket_match.group(1)
                        else:
                            bracket_content = ""
                        
                        # UUIDs are ~36 chars with hyphens (4+ segments), collection names are usually < 30 chars
                        if bracket_content and len(bracket_content) > 30 and "-" in bracket_content:
                            hyphen_parts = bracket_content.split("-")
                            if len(hyphen_parts) >= 4:
                                # This is UUID corruption - reset database
                                self.logger.logger.warning(f"UUID corruption detected in search: {bracket_content[:50]}. Resetting database...")
                                self._reset_database()
                                self.collection = self.client.get_collection(name=self.collection_name)
                            else:
                                self.logger.log_error("DisasterVectorStore.search (get_collection)", get_error)
                                return []
                        else:
                            self.logger.log_error("DisasterVectorStore.search (get_collection)", get_error)
                            return []
                    except Exception as parse_error:
                        self.logger.log_error("DisasterVectorStore.search (parse error)", parse_error)
                        self.logger.log_error("DisasterVectorStore.search (get_collection)", get_error)
                        return []
                else:
                    self.logger.log_error("DisasterVectorStore.search (get_collection)", get_error)
                    return []
            
            self.logger.logger.info(f"Searching for: '{query}' (top_k={top_k})")
            
            query_embedding = self.embedding_service.embed_text(query)
            
            where_clause = None
            if filters:
                where_clause = filters
            
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=where_clause
            )
            
            self.logger.logger.info(f"ChromaDB returned {len(results.get('ids', [[]])[0])} results")
            
            formatted_results = []
            if results and 'ids' in results and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i] if i < len(results['documents'][0]) else '',
                        'metadata': results['metadatas'][0][i] if i < len(results['metadatas'][0]) else {},
                        'distance': results['distances'][0][i] if 'distances' in results and i < len(results['distances'][0]) else 0.0
                    })
            
            self.logger.logger.info(f"Returning {len(formatted_results)} formatted results")
            
            return formatted_results
        
        except Exception as e:
            # Check if this is a UUID corruption error from query operation
            error_msg = str(e)
            error_str = error_msg.lower()
            
            # DEBUG: Always log the error to see what we're getting
            self.logger.logger.warning(f"search exception caught. Error type: {type(e).__name__}, Message: {error_msg[:200]}")
            
            if "collection [" in error_str and "does not exist" in error_str:
                try:
                    bracket_match = re.search(r'[Cc]ollection\s+\[([^\]]+)\]', error_msg)
                    if bracket_match:
                        bracket_content = bracket_match.group(1)
                        if bracket_content and len(bracket_content) > 30 and "-" in bracket_content:
                            hyphen_parts = bracket_content.split("-")
                            if len(hyphen_parts) >= 4:
                                # UUID corruption - reset and retry
                                self.logger.logger.warning(f"UUID corruption detected during query in search: {bracket_content[:50]}. Resetting database...")
                                self._reset_database()
                                # Retry the query with fresh collection
                                try:
                                    self.collection = self.client.get_collection(name=self.collection_name)
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
                                except:
                                    return []  # Return empty if retry fails
                except:
                    pass
            
            self.logger.log_error("DisasterVectorStore.search", e)
            return []
    
    def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific event by ID.
        """
        try:
            # Always get a fresh collection reference to avoid stale UUID issues
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
            except Exception as get_error:
                self.logger.log_error("DisasterVectorStore.get_event_by_id (get_collection)", get_error)
                return None
            
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
            # Always get a fresh collection reference to avoid stale UUID issues
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
            except Exception as get_error:
                error_msg = str(get_error)
                error_str = error_msg.lower()
                
                # DEBUG: Log to see what error we're getting
                self.logger.logger.warning(f"get_all_events get_collection failed. Type: {type(get_error).__name__}, Message: '{error_msg[:150]}'")
                
                # Check for UUID corruption - if so, reset database
                # Error format: "Error getting collection: Collection [UUID] does not exist" or "Collection [UUID] does not exist"
                if "collection [" in error_str and "does not exist" in error_str:
                    self.logger.logger.warning(f"Matched collection error pattern. Checking for UUID...")
                    try:
                        # Extract content between brackets using regex-like approach
                        # Try to find pattern like "Collection [...]" or "collection [...]"
                        bracket_match = re.search(r'[Cc]ollection\s+\[([^\]]+)\]', error_msg)
                        if bracket_match:
                            bracket_content = bracket_match.group(1)
                        else:
                            bracket_content = ""
                        
                        # UUIDs are ~36 chars with hyphens (4+ segments), collection names are usually < 30 chars
                        if bracket_content and len(bracket_content) > 30 and "-" in bracket_content:
                            hyphen_parts = bracket_content.split("-")
                            if len(hyphen_parts) >= 4:
                                # This is UUID corruption - reset database
                                self.logger.logger.warning(f"UUID corruption detected in get_all_events: {bracket_content[:50]}. Resetting database...")
                                self._reset_database()
                                self.collection = self.client.get_collection(name=self.collection_name)
                            else:
                                self.logger.log_error("DisasterVectorStore.get_all_events (get_collection)", get_error)
                                return []
                        else:
                            self.logger.log_error("DisasterVectorStore.get_all_events (get_collection)", get_error)
                            return []
                    except Exception as parse_error:
                        self.logger.log_error("DisasterVectorStore.get_all_events (parse error)", parse_error)
                        self.logger.log_error("DisasterVectorStore.get_all_events (get_collection)", get_error)
                        return []
                else:
                    self.logger.log_error("DisasterVectorStore.get_all_events (get_collection)", get_error)
                    return []
            
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
            # Check if this is a UUID corruption error from get operation
            error_msg = str(e)
            error_str = error_msg.lower()
            
            # DEBUG: Always log the error to see what we're getting
            self.logger.logger.warning(f"get_all_events exception caught. Error type: {type(e).__name__}, Message: {error_msg[:200]}")
            
            if "collection [" in error_str and "does not exist" in error_str:
                try:
                    bracket_match = re.search(r'[Cc]ollection\s+\[([^\]]+)\]', error_msg)
                    if bracket_match:
                        bracket_content = bracket_match.group(1)
                        if bracket_content and len(bracket_content) > 30 and "-" in bracket_content:
                            hyphen_parts = bracket_content.split("-")
                            if len(hyphen_parts) >= 4:
                                # UUID corruption - reset and retry
                                self.logger.logger.warning(f"UUID corruption detected during get in get_all_events: {bracket_content[:50]}. Resetting database...")
                                self._reset_database()
                                # Retry with fresh collection
                                try:
                                    self.collection = self.client.get_collection(name=self.collection_name)
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
                                except:
                                    return []  # Return empty if retry fails
                except:
                    pass
            
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
    
    def add_event_with_imagery(
        self,
        event_id: str,
        text_content: str,
        metadata: Dict[str, Any],
        imagery_urls: Optional[List[str]] = None,
        vision_analysis: Optional[Dict[str, Any]] = None
    ):
        """
        Add or update a disaster event with imagery support.
        Creates combined text+image embedding for multi-modal retrieval.
        
        Args:
            event_id: Unique event identifier
            text_content: Text representation for embedding
            metadata: Event metadata (disaster_type, severity, etc.)
            imagery_urls: Optional list of image URLs
            vision_analysis: Optional GPT-4 Vision analysis results
        """
        try:
            # Generate text embedding
            text_embedding = self.embedding_service.embed_text(text_content)
            
            # If imagery URLs provided, try to generate image embeddings
            if imagery_urls and hasattr(self.embedding_service, 'embed_image'):
                image_embeddings = []
                for img_url in imagery_urls[:3]:  # Limit to 3 images
                    img_emb = self.embedding_service.embed_image(img_url)
                    if img_emb is not None:
                        image_embeddings.append(img_emb)
                
                # Combine text and image embeddings (average if multiple images)
                if image_embeddings:
                    # Average image embeddings
                    avg_image_emb = np.mean(image_embeddings, axis=0)
                    
                    # Combine text and image embeddings
                    # Normalize to same dimension if needed
                    if text_embedding.shape[0] != avg_image_emb.shape[0]:
                        # If dimensions differ, use text embedding only or pad
                        # For now, use text embedding with image metadata
                        final_embedding = text_embedding
                    else:
                        # Weighted combination: 70% text, 30% image
                        final_embedding = 0.7 * text_embedding + 0.3 * avg_image_emb
                    
                    # Add imagery URLs to metadata
                    metadata = metadata.copy()
                    metadata['imagery_urls'] = json.dumps(imagery_urls[:3])
                    metadata['has_imagery'] = True
                    # Add vision analysis if provided
                    if vision_analysis:
                        metadata['vision_analysis'] = vision_analysis
                else:
                    # Image embeddings failed, but still add imagery URLs to metadata
                    metadata = metadata.copy()
                    if imagery_urls:
                        metadata['imagery_urls'] = json.dumps(imagery_urls[:3])
                        metadata['has_imagery'] = True
                    final_embedding = text_embedding
            else:
                    final_embedding = text_embedding
            
            # Always get a fresh collection reference to avoid stale UUID issues
            self.collection = self.client.get_collection(name=self.collection_name)
            
            self.collection.upsert(
                ids=[event_id],
                embeddings=[final_embedding.tolist()],
                documents=[text_content],
                metadatas=[metadata]
            )
            
            self.logger.logger.debug(
                f"Added event with imagery to vector store: {event_id} "
                f"(imagery: {bool(imagery_urls)})"
            )
        
        except Exception as e:
            self.logger.log_error("DisasterVectorStore.add_event_with_imagery", e)
            # Fallback to regular add_event
            self.add_event(event_id, text_content, metadata)
    
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
