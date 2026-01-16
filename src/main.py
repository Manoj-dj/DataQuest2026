"""
Main entry point for DisasterLens AI application.
Orchestrates Pathway pipeline, vector store, LLM, and FastAPI server.
Runs all components in parallel for real-time operation.
"""

import os
import sys
import threading
import time
import yaml
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

import pathway as pw
from src.pipeline.disaster_stream import DisasterStreamPipeline
from src.rag.vector_store import DisasterVectorStore
from src.rag.embedder import EmbeddingService
from src.rag.llm_interface import GeminiLLM
from src.api.server import create_app
from src.api.websocket_handler import websocket_endpoint, broadcast_new_event
from src.utils.logger import app_logger

load_dotenv()

class DisasterLensApp:
    def __init__(self):
        self.logger = app_logger
        self.config = self._load_config()
        
        self._initialize_components()
    
    def _load_config(self) -> dict:
        """
        Load application configuration from YAML.
        """
        config_path = "config/config.yaml"
        
        if not os.path.exists(config_path):
            self.logger.logger.warning(f"Config file not found: {config_path}. Using defaults.")
            return self._get_default_config()
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.logger.logger.info("Configuration loaded successfully")
        return config
    
    def _get_default_config(self) -> dict:
        """
        Fallback configuration if YAML not found.
        """
        return {
            'application': {'name': 'DisasterLens AI', 'version': '1.0.0'},
            'pathway': {'polling_interval_sec': 120, 'persistence_enabled': True},
            'data_sources': {
                'gdacs': {
                    'enabled': True,
                    'url': os.getenv('GDACS_RSS_URL', 'https://www.gdacs.org/xml/rss.xml'),
                    'polling_interval': 120
                },
                'newsapi': {
                    'enabled': True,
                    'query': os.getenv('NEWSAPI_QUERY', 'disaster earthquake wildfire flood'),
                    'polling_interval': 180
                }
            },
            'vector_store': {'collection_name': 'disaster_events'},
            'llm': {'temperature': 0.2, 'max_tokens': 1000},
            'risk_scoring': {
                'severity_weights': {'Red': 10, 'Orange': 7, 'Green': 3},
                'disaster_type_multipliers': {
                    'earthquake': 1.2, 'tsunami': 1.5, 'wildfire': 1.1,
                    'flood': 1.0, 'cyclone': 1.3, 'volcano': 1.4
                }
            }
        }
    
    def _initialize_components(self):
        """
        Initialize all system components.
        """
        self.logger.logger.info("Initializing DisasterLens AI components...")
        
        self.embedding_service = EmbeddingService(
            model_name=os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        )
        
        self.vector_store = DisasterVectorStore(
            persist_directory=os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_db'),
            collection_name=self.config['vector_store']['collection_name'],
            embedding_service=self.embedding_service
        )
        
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.llm = GeminiLLM(
            api_key=gemini_api_key,
            model_name=os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp'),
            temperature=self.config['llm']['temperature'],
            max_tokens=self.config['llm']['max_tokens']
        )
        
        self.pipeline = DisasterStreamPipeline(self.config)
        
        self.logger.logger.info("All components initialized successfully")
    
    def run_pathway_pipeline(self):
        """
        Start Pathway streaming pipeline in background thread.
        """
        self.logger.logger.info("Starting Pathway streaming pipeline...")
        
        try:
            disaster_stream = self.pipeline.build_pipeline()
            
            def on_change(key, row, time, is_addition):
                """
                Callback when new event arrives in Pathway stream.
                """
                if is_addition:
                    event_id = str(row['event_id'])
                    text_content = str(row['text_content'])
                    
                    metadata_str = str(row['metadata_json'])
                    metadata = eval(metadata_str) if metadata_str else {}
                    
                    self.vector_store.add_event(event_id, text_content, metadata)
                    
                    self.logger.logger.info(f"New event indexed: {event_id}")
            
            pw.io.subscribe(disaster_stream, on_change)
            
            pw.run()
        
        except Exception as e:
            self.logger.log_error("run_pathway_pipeline", e)
            raise
    
    def run_api_server(self):
        """
        Start FastAPI server.
        """
        self.logger.logger.info("Starting FastAPI server...")
        
        app = create_app(self.vector_store, self.llm)
        
        app.add_api_websocket_route("/ws", websocket_endpoint)
        
        host = os.getenv('APP_HOST', '0.0.0.0')
        port = int(os.getenv('APP_PORT', 8080))
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
    
    def run(self):
        """
        Main application entry point.
        Runs Pathway pipeline and API server in parallel.
        """
        self.logger.logger.info("=" * 60)
        self.logger.logger.info("DisasterLens AI - Real-Time Climate Emergency Intelligence")
        self.logger.logger.info("Version: 1.0.0")
        self.logger.logger.info("=" * 60)
        
        pipeline_thread = threading.Thread(target=self.run_pathway_pipeline, daemon=True)
        pipeline_thread.start()
        
        time.sleep(5)
        
        self.run_api_server()

def main():
    """
    Application entry point.
    """
    try:
        app = DisasterLensApp()
        app.run()
    except KeyboardInterrupt:
        app_logger.logger.info("Application stopped by user")
        sys.exit(0)
    except Exception as e:
        app_logger.log_error("main", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
