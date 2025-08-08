<<<<<<< HEAD
# Enhanced Soldier Report System

A refactored, event-driven application for analyzing soldier performance and safety data.

## Overview

This system processes CSV data containing soldier metrics (heart rate, temperature, equipment status) and generates comprehensive reports with performance scoring and safety analysis.

## Architecture

The system follows an event-driven architecture with clear separation of concerns:

- **Event Bus**: Central communication hub using publish/subscribe pattern
- **Services**: Independent components for data processing, analysis, and reporting
- **GUI**: Separated presentation layer with controller pattern
- **Models**: Data structures and configuration objects
- **Testing**: Comprehensive unit and integration test suite

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python -m src.main
   ```

3. Run tests:
   ```bash
   pytest tests/
   ```

## Project Structure

```
enhanced_soldier_report_system/
├── src/                    # Application source code
├── tests/                  # Test suite
├── config/                 # Configuration files
├── docs/                   # Documentation
└── requirements.txt        # Dependencies
```

## Features

- **CSV Data Processing**: Flexible column mapping and validation
- **Safety Analysis**: Heart rate and temperature monitoring
- **Performance Scoring**: Configurable scoring algorithms
- **HTML Reports**: Template-based report generation
- **Event-Driven**: Loose coupling via publish/subscribe pattern
- **Testable**: Comprehensive unit and integration tests
- **Configurable**: External configuration management

## Development

This project follows modern Python development practices:

- Type hints throughout
- Comprehensive testing with pytest
- Code formatting with black
- Linting with flake8
- Documentation with sphinx

## License

[Add your license information here]
=======
# AAR System - Event-Driven After Action Review

A comprehensive, event-driven analysis system for military training exercises that provides multi-level insights across individual soldier performance, squad effectiveness, and platoon-wide operations assessment.

## 🚀 Features

### Multi-Domain Analysis
- **Soldier Safety Analysis** (REQ-SAFETY-001 to REQ-SAFETY-008)
- **Network Performance Analysis** (REQ-NETWORK-001 to REQ-NETWORK-008)
- **Soldier Activity Analysis** (REQ-ACTIVITY-001 to REQ-ACTIVITY-008)
- **Equipment Management Analysis** (REQ-EQUIPMENT-001 to REQ-EQUIPMENT-008)
- **Environmental Monitoring**
- **Combat Effectiveness Analysis**

### Multi-Level Reporting
- **Individual Soldier Level** (REQ-SOLDIER-001 to REQ-SOLDIER-005)
- **Squad Level** (REQ-SQUAD-001 to REQ-SQUAD-008)
- **Platoon Level** (REQ-PLATOON-001 to REQ-PLATOON-008)

### Event-Driven Architecture
- Modular, extensible design
- Real-time alert system
- Configurable analysis domains
- Customizable report generation

## 📁 Project Structure

```
aar_system/
├── core/                   # Core event system and models
├── engines/               # Analysis engines by domain
├── services/              # Orchestration and management services
├── reports/               # Report generators and templates
├── ui/                    # User interface components
├── config/                # Configuration files and schemas
├── data/                  # Data processing and validation
├── utils/                 # Utilities and helpers
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## 🛠️ Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure System
```bash
# Copy default configuration
cp config/templates/safety_thresholds.json config/safety_thresholds.json
cp config/templates/network_thresholds.json config/network_thresholds.json

# Edit configuration files as needed
```

### 3. Run Application
```bash
python main.py
```

## 📊 Usage

### Quick Start
1. Load training data CSV file
2. Select analysis domains
3. Configure thresholds
4. Run analysis
5. Generate reports

### Data Format
The system expects CSV files with the following columns:
- `callsign`: Unit identifier
- `processedtimegmt`: Timestamp
- `latitude`, `longitude`: Position data
- `casualtystate`: Health status
- `falldetected`: Fall detection flag
- `battery`: Battery level
- `rssi`: Signal strength
- `nexthop`: Network routing
- And more...

## 🔧 Extending the System

### Adding New Analysis Engines
```python
from core.models import AnalysisEngine, AnalysisDomain

class CustomAnalysisEngine(AnalysisEngine):
    def __init__(self, event_bus):
        super().__init__(AnalysisDomain.CUSTOM)
        self.event_bus = event_bus
    
    def analyze(self, data, config):
        # Your analysis logic here
        pass
```

### Adding New Report Generators
```python
from core.models import ReportGenerator

class CustomReportGenerator(ReportGenerator):
    def can_handle_config(self, config):
        return config.custom_criteria
    
    def generate_report(self, config, results):
        # Your report generation logic here
        pass
```

## 📚 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [User Guide](docs/USER_GUIDE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Contributing Guide](docs/CONTRIBUTING.md)

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aar_system

# Run specific test category
pytest tests/unit/
pytest tests/integration/
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Email: aar-support@example.com
- Documentation: [docs/](docs/)
>>>>>>> dae0a8cb6feadc2779506d88360bd7bf01476064
