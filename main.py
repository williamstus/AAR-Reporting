<<<<<<< HEAD
# File: src/main.py
"""Main application entry point for Enhanced Soldier Report System"""

import sys
import logging
import signal
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.core.event_bus import EventBus
from src.core.events import EventType
from src.config.settings import Settings
from src.services.data_loader import DataLoader
from src.services.analysis_engine import AnalysisEngine
from src.reporting.report_generator import ReportGenerator
from src.reporting.html_renderer import HTMLRenderer
from src.gui.main_window import MainWindow
from src.utils.logging_config import setup_logging


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
        
        # HTML renderer - create with default template directory if not specified in settings
        try:
            # Try to get template_directory from settings
            template_dir = getattr(self.settings, 'template_directory', None)
            if template_dir is None:
                # Create default template directory
                template_dir = Path('templates')
                template_dir.mkdir(exist_ok=True)
            html_renderer = HTMLRenderer(template_dir, self.event_bus)
        except Exception as e:
            # If HTMLRenderer fails, create a mock object to prevent crashes
            self.logger.warning(f"HTMLRenderer initialization failed: {e}, using mock renderer")
            html_renderer = None
        
        # Report generator - now compatible with original main.py
        self.report_generator = ReportGenerator(self.event_bus, html_renderer)
        
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
=======
#!/usr/bin/env python3
"""
AAR System Main Entry Point - Fixed Version
"""

import sys
import os
import traceback

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

def main():
    """Main entry point for AAR System"""
    print("🚀 Starting AAR System v2.0 (Fixed)...")
    print("=" * 50)
    
    try:
        # Try to import the fixed main application
        print("📦 Loading main application...")
        
        # Try the fixed version first
        try:
            from ui.main_application_fixed import AARMainApplication
            print("✅ Loaded fixed main application")
            app_class = AARMainApplication
        except ImportError:
            # Fall back to original if it has the right class
            try:
                from ui.main_application import AARMainApplication
                print("✅ Loaded original main application")
                app_class = AARMainApplication
            except ImportError:
                # Try any available class in main_application
                import ui.main_application as main_app
                
                # Look for any suitable class
                app_classes = [getattr(main_app, name) for name in dir(main_app) 
                             if isinstance(getattr(main_app, name), type) and 
                             name not in ['tk', 'ttk', 'messagebox']]
                
                if app_classes:
                    app_class = app_classes[0]
                    print(f"✅ Using available class: {app_class.__name__}")
                else:
                    raise ImportError("No suitable application class found")
        
        # Create and run the application
        print("🎯 Initializing application...")
        app = app_class()
        
        print("✅ AAR System loaded successfully!")
        print("🚀 Starting user interface...")
        
        app.run()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\n🔧 Possible solutions:")
        print("1. Run the diagnostic fix: python aar_diagnostic_fix.py")
        print("2. Check that ui/main_application.py contains AARMainApplication class")
        print("3. Use the fixed version: python -c \"from ui.main_application_fixed import AARMainApplication; AARMainApplication().run()\"")
        
        # Try to provide a minimal fallback
        try:
            print("\n🆘 Attempting minimal fallback...")
            create_minimal_fallback()
        except Exception as fallback_error:
            print(f"❌ Fallback failed: {fallback_error}")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("\n📋 Full error details:")
        traceback.print_exc()
        print("\n🔧 Try running: python aar_diagnostic_fix.py")

def create_minimal_fallback():
    """Create a minimal fallback application"""
    import tkinter as tk
    from tkinter import ttk, messagebox
    
    root = tk.Tk()
    root.title("AAR System - Minimal Mode")
    root.geometry("800x600")
    
    # Create simple interface
    ttk.Label(root, text="AAR System - Minimal Mode", font=("Arial", 16, "bold")).pack(pady=20)
    ttk.Label(root, text="The main application had import issues.").pack()
    ttk.Label(root, text="This is a minimal fallback interface.").pack(pady=10)
    
    def test_reports():
        try:
            from ui.components.reports_tab import ReportsTab
            reports_window = tk.Toplevel(root)
            reports_window.title("AAR Reports")
            reports_window.geometry("1000x700")
            ReportsTab(reports_window)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load reports: {e}")
    
    ttk.Button(root, text="Test Reports Functionality", command=test_reports).pack(pady=10)
    ttk.Button(root, text="Exit", command=root.quit).pack(pady=5)
    
    print("✅ Minimal fallback interface started")
    root.mainloop()

if __name__ == "__main__":
    main()
>>>>>>> dae0a8cb6feadc2779506d88360bd7bf01476064
