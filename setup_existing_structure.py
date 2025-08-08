#!/usr/bin/env python3
"""
Setup script for existing file structure
Works with files already in src/models
"""

import os
import re
from pathlib import Path

def ensure_directory_structure():
    """Ensure all necessary directories exist"""
    directories = [
        "src",
        "src/models",
        "src/config", 
        "src/core",
        "src/services",
        "src/reporting",
        "src/gui",
        "src/utils"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py files
        init_file = Path(directory) / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created: {init_file}")

def check_existing_files():
    """Check what files already exist"""
    print("Checking existing files...")
    
    # Check for model files
    model_files = [
        "src/models/soldier_data.py",
        "src/models/analysis_results.py", 
        "src/models/report_config.py"
    ]
    
    existing_models = []
    for file_path in model_files:
        if Path(file_path).exists():
            existing_models.append(file_path)
            print(f"✅ Found: {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
    
    return existing_models

def fix_import_issues():
    """Fix specific import issues in existing files"""
    
    # Files and their import fixes
    fixes = {
        "src/services/analysis_engine.py": [
            ("from models.soldier_data import SoldierDataset, AnalysisResults", 
             "from models.soldier_data import SoldierDataset\nfrom models.analysis_results import SoldierAnalysisResult, BatchAnalysisResult"),
        ],
        "src/services/performance_scorer.py": [
            ("from models.analysis_results import AnalysisResults",
             "from models.analysis_results import SoldierAnalysisResult"),
        ],
        "src/services/safety_analyzer.py": [
            ("from models.analysis_results import AnalysisResults",
             "from models.analysis_results import SoldierAnalysisResult"),
        ],
        "src/reporting/report_generator.py": [
            ("from models.report_config import ReportConfig",
             "from models.report_config import ReportConfig"),
            ("from reporting.html_renderer import HtmlRenderer", 
             "from reporting.html_renderer import HtmlRenderer"),
        ],
        "src/core/event_bus.py": [
            ("from events import Event, EventType",
             "from core.events import Event, EventType"),
        ],
    }
    
    fixed_count = 0
    for file_path, file_fixes in fixes.items():
        if Path(file_path).exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                for old_import, new_import in file_fixes:
                    content = content.replace(old_import, new_import)
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Fixed imports in: {file_path}")
                    fixed_count += 1
                else:
                    print(f"No changes needed in: {file_path}")
                    
            except Exception as e:
                print(f"Error fixing {file_path}: {e}")
        else:
            print(f"File not found for fixing: {file_path}")
    
    return fixed_count

def create_missing_modules():
    """Create any missing core modules"""
    
    # Create config/settings.py if it doesn't exist
    settings_path = Path("src/config/settings.py")
    if not settings_path.exists():
        settings_content = '''"""Application settings and configuration"""
import json
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Settings:
    """Application settings"""
    max_workers: int = 4
    event_queue_size: int = 1000
    debug_mode: bool = False
    
    @classmethod
    def load_from_file(cls, config_path: Path) -> 'Settings':
        """Load settings from configuration file"""
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                return cls(**config_data)
            except Exception:
                pass
        return cls()  # Return default settings
'''
        with open(settings_path, 'w') as f:
            f.write(settings_content)
        print(f"Created: {settings_path}")
    
    # Create utils/logging_config.py if it doesn't exist
    logging_config_path = Path("src/utils/logging_config.py")
    if not logging_config_path.exists():
        logging_config_content = '''"""Logging configuration"""
import logging
import sys

def setup_logging(log_level: str = "INFO"):
    """Setup application logging"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
'''
        with open(logging_config_path, 'w') as f:
            f.write(logging_config_content)
        print(f"Created: {logging_config_path}")
    
    # Create core/events.py if it doesn't exist
    events_path = Path("src/core/events.py")
    if not events_path.exists():
        events_content = '''"""Event type definitions and event classes"""
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict
from datetime import datetime
import uuid

@dataclass
class Event:
    """Base event class"""
    type: str
    data: Dict[str, Any]
    source: str
    timestamp: datetime = None
    event_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.event_id is None:
            self.event_id = str(uuid.uuid4())

class EventType(Enum):
    """Enumeration of all event types"""
    FILE_SELECTED = "file_selected"
    DATA_LOADED = "data_loaded"
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    REPORT_GENERATION_REQUESTED = "report_generation_requested"
    REPORT_GENERATED = "report_generated"
    STATUS_UPDATE = "status_update"
    ERROR_OCCURRED = "error_occurred"

@dataclass
class DataLoadedEvent(Event):
    """Event published when data is successfully loaded"""
    def __init__(self, dataset, file_path: str, source: str):
        super().__init__(
            type=EventType.DATA_LOADED.value,
            data={'dataset': dataset, 'file_path': file_path},
            source=source
        )

@dataclass
class StatusUpdateEvent(Event):
    """Event for status updates"""
    def __init__(self, message: str, source: str, level: str = "info"):
        super().__init__(
            type=EventType.STATUS_UPDATE.value,
            data={'message': message, 'level': level},
            source=source
        )

@dataclass
class ErrorEvent(Event):
    """Event for error reporting"""
    def __init__(self, error: Exception, context: str, source: str):
        super().__init__(
            type=EventType.ERROR_OCCURRED.value,
            data={'error': str(error), 'context': context},
            source=source
        )
'''
        with open(events_path, 'w') as f:
            f.write(events_content)
        print(f"Created: {events_path}")
    
    # Create core/event_bus.py if it doesn't exist
    event_bus_path = Path("src/core/event_bus.py")
    if not event_bus_path.exists():
        event_bus_content = '''"""Event bus implementation for inter-component communication"""
import logging
from typing import Any, Dict, List, Callable, Optional
from threading import Lock
from core.events import Event, EventType

class EventBus:
    """Simple event bus for component communication"""
    
    def __init__(self, max_workers: int = 4, queue_size: int = 1000):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(__name__)
        self._lock = Lock()
        self.max_workers = max_workers
        self.queue_size = queue_size
        self._started = False
    
    def subscribe(self, event_type: str, handler: Callable, priority: int = 0, handler_id: str = None):
        """Subscribe to events of a specific type"""
        with self._lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(handler)
    
    def publish(self, event: Event):
        """Publish an event to subscribers"""
        with self._lock:
            if event.type in self.subscribers:
                for handler in self.subscribers[event.type]:
                    try:
                        handler(event)
                    except Exception as e:
                        self.logger.error(f"Error in event handler: {e}")
    
    def start(self):
        """Start the event bus"""
        self._started = True
        self.logger.info("Event bus started")
    
    def stop(self, timeout: float = 5.0):
        """Stop the event bus"""
        self._started = False
        self.logger.info("Event bus stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            'subscribers': len(self.subscribers),
            'started': self._started
        }
'''
        with open(event_bus_path, 'w') as f:
            f.write(event_bus_content)
        print(f"Created: {event_bus_path}")

def test_imports():
    """Test if the main imports work"""
    print("\\nTesting imports...")
    
    import sys
    src_path = Path("src").absolute()
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    try:
        from models.soldier_data import SoldierDataset, SoldierDataRecord
        print("✅ Successfully imported soldier_data models")
    except ImportError as e:
        print(f"❌ Failed to import soldier_data: {e}")
        return False
    
    try:
        from models.analysis_results import SoldierAnalysisResult, BatchAnalysisResult
        print("✅ Successfully imported analysis_results models")
    except ImportError as e:
        print(f"❌ Failed to import analysis_results: {e}")
        return False
    
    try:
        from models.report_config import ReportConfig, create_default_soldier_report_config
        print("✅ Successfully imported report_config models")
    except ImportError as e:
        print(f"❌ Failed to import report_config: {e}")
        return False
    
    try:
        from core.event_bus import EventBus
        from core.events import EventType
        print("✅ Successfully imported core modules")
    except ImportError as e:
        print(f"❌ Failed to import core modules: {e}")
        return False
    
    try:
        from config.settings import Settings
        print("✅ Successfully imported settings")
    except ImportError as e:
        print(f"❌ Failed to import settings: {e}")
        return False
    
    print("\\n🎉 All core imports working!")
    return True

def main():
    """Main setup function"""
    print("Setting up Enhanced Soldier Report System...")
    print(f"Working directory: {Path.cwd()}")
    
    # Step 1: Check what we have
    print("\\n1. Checking existing files...")
    existing_models = check_existing_files()
    
    if len(existing_models) < 3:
        print("\\n❌ Not all model files found. Expected files in src/models/:")
        print("  - soldier_data.py")
        print("  - analysis_results.py") 
        print("  - report_config.py")
        return 1
    
    # Step 2: Create directory structure
    print("\\n2. Ensuring directory structure...")
    ensure_directory_structure()
    
    # Step 3: Create missing modules
    print("\\n3. Creating missing core modules...")
    create_missing_modules()
    
    # Step 4: Fix import issues
    print("\\n4. Fixing import issues...")
    fixed_count = fix_import_issues()
    
    # Step 5: Test imports
    print("\\n5. Testing imports...")
    if test_imports():
        print("\\n✅ Setup completed successfully!")
        print("\\nYour sophisticated data models are ready to use!")
        print("\\nNow you can run:")
        print("python -m src.main")
        print("\\nOr use the working main application:")
        print("python working_main_with_models.py")
    else:
        print("\\n❌ Setup incomplete - some imports still failing")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
