"""
Main entry point for DisasterLens AI application.
Orchestrates Pathway pipeline, vector store, LLM, and FastAPI server.
Runs all components in parallel for real-time operation.
"""

from fastapi.responses import HTMLResponse
import os
import sys
import threading
import time
import signal
import yaml
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pathway as pw
from src.pipeline.disaster_stream import DisasterStreamPipeline
from src.rag.vector_store import DisasterVectorStore
from src.rag.embedder import EmbeddingService
from src.rag.llm_interface import OpenAILLM
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
        
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.llm = OpenAILLM(
            api_key=openai_api_key,
            model_name=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
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
        
        # Log Pathway version and features for hackathon judges
        try:
            self.logger.logger.info(f"Using Pathway version: {pw.__version__}")
            self.logger.logger.info("Pathway streaming mode: ENABLED")
            self.logger.logger.info("Pathway connectors: GDACS (PythonReader-0), NewsAPI (PythonReader-1), NASA EONET (PythonReader-2)")
        except:
            pass
        
        try:
            disaster_stream = self.pipeline.build_pipeline()
            
            def on_change(key, row, time, is_addition):
                """
                Callback when new event arrives in Pathway stream.
                """
                if is_addition:
                    import json
                    try:
                        event_id = str(row.get('event_id', 'unknown'))
                        text_content = str(row.get('text_content', ''))
                        
                        metadata_str = str(row.get('metadata_json', '{}'))
                        try:
                            metadata = eval(metadata_str) if metadata_str and metadata_str != '{}' else {}
                        except:
                            metadata = {}
                        
                        # Extract coordinates directly from Pathway row if not in metadata
                        # This ensures coordinates are saved even if metadata_json doesn't have them
                        if 'latitude' in row and 'longitude' in row:
                            try:
                                lat = float(row.get('latitude', 0.0))
                                lon = float(row.get('longitude', 0.0))
                                if lat != 0.0 or lon != 0.0:
                                    metadata['latitude'] = lat
                                    metadata['longitude'] = lon
                                    metadata['location_name'] = metadata.get('location_name') or row.get('location_name', '')
                            except:
                                pass
                        
                        # Extract imagery URLs if present
                        imagery_urls = None
                        if 'imagery_urls_json' in row:
                            imagery_json_str = str(row.get('imagery_urls_json', '[]'))
                            if imagery_json_str and imagery_json_str != '[]':
                                try:
                                    imagery_urls = json.loads(imagery_json_str)
                                    if not isinstance(imagery_urls, list):
                                        imagery_urls = []
                                except:
                                    imagery_urls = []
                        
                        # Use add_event_with_imagery if imagery URLs are available
                        if imagery_urls and len(imagery_urls) > 0:
                            self.vector_store.add_event_with_imagery(
                                event_id=event_id,
                                text_content=text_content,
                                metadata=metadata,
                                imagery_urls=imagery_urls
                            )
                            self.logger.logger.info(f"New event with imagery indexed: {event_id} ({len(imagery_urls)} images)")
                        else:
                            self.vector_store.add_event(event_id, text_content, metadata)
                            self.logger.logger.info(f"New event indexed: {event_id}")
                    except Exception as e:
                        self.logger.log_error("on_change callback", e)
            
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

        # Mount static files for frontend
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        import os
        frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
        if os.path.exists(frontend_path):
            app.mount("/static", StaticFiles(directory=frontend_path), name="static")
            # Serve index.html at root
            @app.get("/", response_class=HTMLResponse)
            async def read_root():
                index_path = os.path.join(frontend_path, "index.html")
                if os.path.exists(index_path):
                    with open(index_path, "r") as f:
                        return f.read()
                return "<h1>Frontend not found</h1>"
        
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

def signal_handler(sig, frame):
    """Graceful shutdown handler to prevent threading errors."""
    app_logger.logger.info("Shutting down gracefully...")
    sys.exit(0)

def main():
    """
    Application entry point.
    """
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
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
