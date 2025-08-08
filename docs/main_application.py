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
            self.logger.info("🎖️ Enhanced Individual Soldier Report System - Starting...")
            
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
            
            self.logger.info("✅ Application initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize application: {e}")
            return False
    
    def _initialize_services(self):
        """Initialize all application services"""
        self.logger.info("🔧 Initializing services...")
        
        # Data loading service
        self.data_loader = DataLoader(self.event_bus, self.settings)
        
        # Analysis engine
        self.analysis_engine = AnalysisEngine(self.event_bus)
        
        # Report generator
        self.report_generator = ReportGenerator(self.event_bus, self.settings)
        
        self.logger.info("✅ Services initialized")
    
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
            self.logger.info("🚀 Starting GUI...")
            self.main_window.run()
            
        except KeyboardInterrupt:
            self.logger.info("👋 Application interrupted by user")
        except Exception as e:
            self.logger.error(f"💥 Application error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the application gracefully"""
        self.logger.info("🛑 Shutting down application...")
        
        if self.event_bus:
            self.event_bus.stop(timeout=5.0)
        
        if self.main_window:
            self.main_window.destroy()
        
        self.logger.info("👋 Application shutdown complete")
    
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


# File: src/utils/logging_config.py
"""Logging configuration for the application"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> None:
    """Setup comprehensive logging configuration"""
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    log_file = log_path / f"soldier_report_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_file = log_path / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # Component-specific loggers
    setup_component_loggers()


def setup_component_loggers():
    """Setup loggers for specific components"""
    
    # Event bus logger
    event_logger = logging.getLogger('src.core.event_bus')
    event_logger.setLevel(logging.INFO)
    
    # Data loader logger
    data_logger = logging.getLogger('src.services.data_loader')
    data_logger.setLevel(logging.INFO)
    
    # Analysis engine logger
    analysis_logger = logging.getLogger('src.services.analysis_engine')
    analysis_logger.setLevel(logging.INFO)
    
    # GUI logger
    gui_logger = logging.getLogger('src.gui')
    gui_logger.setLevel(logging.INFO)


# File: deployment/docker/Dockerfile
"""Docker configuration for containerized deployment"""

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY tests/ ./tests/

# Create necessary directories
RUN mkdir -p logs reports

# Set environment variables
ENV PYTHONPATH=/app/src
ENV DISPLAY=:0

# Expose any necessary ports (if web interface is added later)
EXPOSE 8080

# Run tests
RUN python -m pytest tests/ -v

# Default command
CMD ["python", "src/main.py"]


# File: deployment/scripts/install.sh
#!/bin/bash
"""Installation script for Linux/macOS systems"""

set -e

echo "🎖️ Enhanced Individual Soldier Report System - Installation"
echo "============================================================"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs reports config

# Copy default configuration if it doesn't exist
if [ ! -f "config/default_settings.json" ]; then
    echo "⚙️ Creating default configuration..."
    cat > config/default_settings.json << 'EOF'
{
  "column_mapping": {
    "callsign": "Callsign",
    "squad": "Platoon",
    "casualtystate": "Casualty_State",
    "processedtimegmt": "Time_Step",
    "heartrate": "Heart_Rate",
    "stepcount": "Step_Count",
    "temp": "Temperature",
    "battery": "Battery",
    "rssi": "RSSI"
  },
  "performance": {
    "activity_weight": 0.3,
    "casualty_penalties": {
      "WOUNDED": 10,
      "KIA": 20
    },
    "battery_thresholds": {
      "critical": 10,
      "low": 20
    }
  },
  "reporting": {
    "output_directory": "reports/enhanced",
    "max_concurrent_reports": 4
  },
  "log_level": "INFO",
  "max_workers": 4
}
EOF
fi

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v --cov=src --cov-report=term-missing

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "🚀 To start the application:"
echo "   source venv/bin/activate"
echo "   python src/main.py"
echo ""
echo "📊 To run tests:"
echo "   python -m pytest tests/ -v"
echo ""
echo "📁 Reports will be saved to: reports/enhanced/"


# File: deployment/scripts/run_tests.sh
#!/bin/bash
"""Test runner script"""

set -e

echo "🧪 Enhanced Soldier Report System - Test Suite"
echo "=============================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing..."
    pip install pytest pytest-cov
fi

# Create test reports directory
mkdir -p test_reports

# Run unit tests
echo "🔬 Running unit tests..."
python -m pytest tests/unit/ -v \
    --cov=src \
    --cov-report=html:test_reports/coverage_html \
    --cov-report=xml:test_reports/coverage.xml \
    --cov-report=term-missing \
    --junit-xml=test_reports/junit.xml

# Run integration tests
echo "🔗 Running integration tests..."
python -m pytest tests/integration/ -v \
    --junit-xml=test_reports/integration_junit.xml

# Performance tests (if any)
if [ -d "tests/performance" ]; then
    echo "⚡ Running performance tests..."
    python -m pytest tests/performance/ -v \
        --junit-xml=test_reports/performance_junit.xml
fi

echo ""
echo "✅ All tests completed!"
echo "📊 Coverage report: test_reports/coverage_html/index.html"
echo "📋 Test results: test_reports/junit.xml"


# File: docs/DEPLOYMENT_GUIDE.md
"""Deployment guide for the refactored system"""

# Enhanced Soldier Report System - Deployment Guide

## Prerequisites

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 1GB free space minimum
- **Display**: GUI requires display/X11 forwarding for remote deployments

### Python Dependencies
```bash
pandas>=1.5.0
numpy>=1.20.0
pytest>=7.0.0
pytest-cov>=4.0.0
```

## Installation Methods

### Method 1: Standard Installation
```bash
# Clone or extract the project
cd enhanced_soldier_report_system_refactored

# Run installation script
chmod +x deployment/scripts/install.sh
./deployment/scripts/install.sh
```

### Method 2: Manual Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p logs reports config

# Copy configuration
cp config/default_settings.json config/settings.json
```

### Method 3: Docker Deployment
```bash
# Build Docker image
docker build -t soldier-report-system deployment/docker/

# Run container (requires X11 forwarding for GUI)
docker run -it \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  -v $(pwd)/reports:/app/reports \
  soldier-report-system
```

## Configuration

### Configuration File Structure
The system uses JSON configuration files located in `config/`:

```json
{
  "column_mapping": {
    "callsign": "Callsign",
    "heartrate": "Heart_Rate"
  },
  "performance": {
    "activity_weight": 0.3,
    "casualty_penalties": {
      "WOUNDED": 10,
      "KIA": 20
    }
  },
  "reporting": {
    "output_directory": "reports/enhanced",
    "max_concurrent_reports": 4
  }
}
```

### Environment Variables
- `PYTHONPATH`: Set to `/path/to/src` for proper imports
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `CONFIG_PATH`: Path to configuration file (default: config/default_settings.json)

## Running the Application

### Command Line
```bash
# Activate virtual environment
source venv/bin/activate

# Start application
python src/main.py

# With custom config
CONFIG_PATH=config/custom_settings.json python src/main.py
```

### Testing
```bash
# Run all tests
./deployment/scripts/run_tests.sh

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v

# With coverage
python -m pytest tests/ -v --cov=src --cov-report=html
```

## Architecture Overview

### Event-Driven Design
- **Event Bus**: Central communication hub
- **Services**: Independent, loosely-coupled components
- **GUI**: Reactive interface responding to events
- **Configuration**: External, runtime-configurable settings

### Key Components
1. **Data Loader**: CSV file processing and validation
2. **Analysis Engine**: Coordinates statistical analysis
3. **Safety Analyzer**: Medical and safety assessments
4. **Performance Scorer**: Configurable scoring algorithms
5. **Report Generator**: HTML report creation
6. **GUI**: Tkinter-based user interface

## Troubleshooting

### Common Issues

**GUI Not Starting**
```bash
# Check display
echo $DISPLAY

# Install tkinter (Linux)
sudo apt-get install python3-tk

# For remote sessions
ssh -X user@host
```

**Import Errors**
```bash
# Set Python path
export PYTHONPATH=/path/to/enhanced_soldier_report_system_refactored/src

# Or add to .bashrc
echo 'export PYTHONPATH=/path/to/project/src' >> ~/.bashrc
```

**Permission Issues**
```bash
# Make scripts executable
chmod +x deployment/scripts/*.sh

# Fix file permissions
chmod -R 755 src/
```

### Log Files
- **Application logs**: `logs/soldier_report_YYYYMMDD.log`
- **Error logs**: `logs/errors_YYYYMMDD.log`
- **Test logs**: `test_reports/`

### Performance Tuning
- **Event Bus Workers**: Adjust `max_workers` in configuration
- **Memory Usage**: Set `chunk_size` for large datasets
- **Concurrent Reports**: Tune `max_concurrent_reports`

## Maintenance

### Regular Tasks
- **Log Rotation**: Logs rotate automatically at 10MB
- **Test Execution**: Run tests before deployments
- **Configuration Backup**: Version control settings files
- **Performance Monitoring**: Review event bus statistics

### Updates
1. Backup current configuration
2. Update source code
3. Run migration scripts if needed
4. Execute full test suite
5. Deploy with monitoring

## Security Considerations

### File Permissions
- Configuration files: 640 (owner read/write, group read)
- Log files: 644 (owner read/write, others read)
- Scripts: 755 (executable)

### Data Protection
- Reports contain sensitive military data
- Implement access controls as needed
- Consider encryption for sensitive deployments
- Audit log access and modifications

## Support

### Getting Help
1. Check log files for error details
2. Run diagnostics: `python src/main.py --debug`
3. Review test output for component issues
4. Consult architecture documentation

### Development
- **Adding Features**: Follow event-driven patterns
- **New Analysis Types**: Extend analysis engine
- **Custom Reports**: Create new report templates
- **UI Components**: Add to gui/components/