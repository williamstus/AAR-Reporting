# File: src/main.py
"""Main application entry point for Enhanced Soldier Report System"""

import sys
import logging
import signal
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.event_bus import EventBus
from core.events import EventType
from config.settings import Settings
from services.data_loader import DataLoader
from services.analysis_engine import AnalysisEngine
from reporting.report_generator import ReportGenerator
from gui.main_window import MainWindow
from utils.logging_config import setup_logging


class EnhancedSoldierReportApplication:
    """Main application class"""
    
    def __init__(self):
        self.event_bus: Optional[EventBus] = None
        self.main_window: Optional[MainWindow] = None
        self.settings: Optional[Settings] = None
        self.logger = logging.getLogger(__name__)
        
        # Services
        self.data_loader: Optional[DataLoader] = None
        self.analysis_engine: Optional[AnalysisEngine] = None
        self.report_generator: Optional[ReportGenerator] = None
    
    def initialize(self) -> bool:
        """Initialize the application"""
        try:
            # Setup logging
            setup_logging()
            self.logger.info("Enhanced Individual Soldier Report System - Starting...")
            
            # Load configuration
            config_path = Path("config/default_settings.json")
            self.settings = Settings.load_from_file(config_path)
            
            # Initialize event bus
            self.event_bus = EventBus(
                max_workers=self.settings.max_workers,
                queue_size=self.settings.event_queue_size
            )
            
            # Initialize services
            self._initialize_services()
            
            # Initialize GUI
            self.main_window = MainWindow(self.event_bus)
            
            # Setup signal handlers
            self._setup_signal_handlers()
            
            # Start event bus
            self.event_bus.start()
            
            self.logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            return False
    
    def _initialize_services(self):
        """Initialize all application services"""
        self.logger.info("Initializing services...")
        
        # Data loading service
        self.data_loader = DataLoader(self.event_bus, self.settings)
        
        # Analysis engine
        self.analysis_engine = AnalysisEngine(self.event_bus)
        
        # Report generator
        self.report_generator = ReportGenerator(self.event_bus, self.settings)
        
        self.logger.info("Services initialized")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def run(self):
        """Run the application"""
        if not self.initialize():
            sys.exit(1)
        
        try:
            self.logger.info("Starting GUI...")
            self.main_window.run()
            
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the application gracefully"""
        self.logger.info("Shutting down application...")
        
        if self.event_bus:
            self.event_bus.stop(timeout=5.0)
        
        if self.main_window:
            self.main_window.destroy()
        
        self.logger.info("Application shutdown complete")
    
    def get_stats(self) -> dict:
        """Get application statistics"""
        stats = {
            'application': 'Enhanced Soldier Report System',
            'version': '2.0.0',
            'architecture': 'Event-Driven',
        }
        
        if self.event_bus:
            stats['event_bus'] = self.event_bus.get_stats()
        
        return stats


def main():
    """Main entry point"""
    app = EnhancedSoldierReportApplication()
    app.run()


if __name__ == "__main__":
    main()