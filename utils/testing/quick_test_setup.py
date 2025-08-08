# quick_test_setup.py - Quick Setup for Testing Data Management Services
"""
Quick setup script to test the data management services.
Run this script to verify everything works correctly.
"""

import os
import sys
import pandas as pd
import tempfile
from pathlib import Path
import logging

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_minimal_test_data():
    """Create minimal test data for quick testing"""
    data = {
        'callsign': ['Unit_108', 'Unit_134', 'Unit_156', 'Unit_178'],
        'processedtimegmt': [
            '2025-01-01 10:00:00',
            '2025-01-01 10:00:30',
            '2025-01-01 10:01:00',
            '2025-01-01 10:01:30'
        ],
        'latitude': [40.7128, 40.7130, 40.7125, 40.7135],
        'longitude': [-74.0060, -74.0062, -74.0058, -74.0065],
        'temp': [25.5, 26.0, 24.8, 25.2],
        'battery': [95, 87, 92, 88],
        'falldetected': ['No', 'Yes', 'No', 'No'],
        'casualtystate': ['GOOD', 'FALL ALERT', 'GOOD', 'GOOD'],
        'rssi': [22, 18, 25, 20],
        'mcs': [6, 5, 7, 6],
        'nexthop': ['Router_1', 'Router_2', 'Router_1', 'Router_3'],
        'steps': [150, 200, 180, 170],
        'posture': ['Standing', 'Prone', 'Standing', 'Standing'],
        'squad': ['Alpha', 'Alpha', 'Bravo', 'Bravo']
    }
    return pd.DataFrame(data)

def quick_test_data_loader():
    """Quick test of data loader functionality"""
    print("🔄 Testing Data Loader...")
    
    try:
        # Import required modules
        from core.event_bus import EventBus
        from core.models import SystemConfiguration, AnalysisDomain
        from services.data_management.data_loader import DataLoader, create_csv_load_request
        
        # Setup
        event_bus = EventBus()
        config = SystemConfiguration()
        loader = DataLoader(event_bus, config)
        
        # Create test data
        test_data = create_minimal_test_data()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            test_data.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            # Create load request
            request = create_csv_load_request(
                request_id="quick_test_001",
                file_path=temp_file,
                analysis_domain=AnalysisDomain.SOLDIER_SAFETY
            )
            
            # Test loading
            loaded_data = loader._load_csv_data(request)
            
            # Verify results
            assert len(loaded_data) == 4
            assert 'callsign' in loaded_data.columns
            assert 'falldetected' in loaded_data.columns
            
            print("✅ Data Loader test passed!")
            return True
            
        finally:
            Path(temp_file).unlink()
    
    except Exception as e:
        print(f"❌ Data Loader test failed: {e}")
        return False

def quick_test_data_validator():
    """Quick test of data validator functionality"""
    print("🔍 Testing Data Validator...")
    
    try:
        # Import required modules
        from core.event_bus import EventBus
        from core.models import SystemConfiguration, AnalysisDomain
        from services.data_management.data_validation import DataValidator
        
        # Setup
        event_bus = EventBus()
        config = SystemConfiguration()
        validator = DataValidator(event_bus, config)
        
        # Create test data with some issues
        test_data = pd.DataFrame({
            'callsign': ['Unit_100', 'Unit_101', 'Unit_102'],
            'processedtimegmt': ['2025-01-01 10:00:00', 'invalid_date', '2025-01-01 10:01:00'],
            'latitude': [40.7128, 91.0, 40.7125],  # Invalid latitude
            'longitude': [-74.0060, -74.0062, -181.0],  # Invalid longitude
            'temp': [25.5, 80.0, 24.8],  # Invalid temperature
            'battery': [95, 150, 92],  # Invalid battery
            'falldetected': ['No', 'Maybe', 'No'],  # Invalid value
            'casualtystate': ['GOOD', 'INVALID', 'GOOD'],  # Invalid state
            'rssi': [22, 200, 25],  # Invalid RSSI
            'mcs': [6, 15, 7]  # Invalid MCS
        })
        
        # Test validation
        result = validator.validate_data(test_data, request_id="quick_test_validation")
        
        # Verify results
        assert result.total_records == 3
        assert len(result.issues) > 0  # Should find validation issues
        assert result.overall_score < 100  # Should be less than perfect
        
        print(f"✅ Data Validator test passed! Found {len(result.issues)} issues")
        return True
        
    except Exception as e:
        print(f"❌ Data Validator test failed: {e}")
        return False

def quick_test_integration():
    """Quick test of integration between services"""
    print("🔄 Testing Integration...")
    
    try:
        # Import required modules
        from core.event_bus import EventBus, Event, EventType
        from core.models import SystemConfiguration, AnalysisDomain
        from services.data_management.data_loader import DataLoader
        from services.data_management.data_validation import DataValidator
        
        # Setup
        event_bus = EventBus()
        config = SystemConfiguration()
        loader = DataLoader(event_bus, config)
        validator = DataValidator(event_bus, config)
        
        # Track events
        events_received = []
        
        def event_tracker(event):
            events_received.append(event)
        
        # Subscribe to events
        event_bus.subscribe(EventType.DATA_VALIDATION_COMPLETED, event_tracker)
        
        # Create test data
        test_data = create_minimal_test_data()
        
        # Trigger validation via event
        event_bus.publish(Event(
            EventType.DATA_VALIDATION_REQUESTED,
            {
                'request_id': 'integration_test_001',
                'data': test_data,
                'domain': AnalysisDomain.SOLDIER_SAFETY
            },
            source='QuickTest'
        ))
        
        # Give time for event processing
        import time
        time.sleep(0.5)
        
        # Verify events were processed
        assert len(events_received) > 0
        
        print("✅ Integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are available"""
    print("📦 Checking Dependencies...")
    
    required_modules = [
        'pandas',
        'numpy',
        'datetime',
        'pathlib',
        'logging',
        'threading',
        'json',
        'tempfile'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing dependencies: {', '.join(missing_modules)}")
        print("Please install missing dependencies with: pip install pandas numpy")
        return False
    
    print("✅ All dependencies available!")
    return True

def check_project_structure():
    """Check if project structure is correct"""
    print("📁 Checking Project Structure...")
    
    required_paths = [
        'core/',
        'core/event_bus.py',
        'core/models.py',
        'services/',
        'services/data_management/',
        'services/data_management/data_loader.py',
        'services/data_management/data_validation.py'
    ]
    
    missing_paths = []
    
    for path in required_paths:
        if not Path(path).exists():
            missing_paths.append(path)
    
    if missing_paths:
        print(f"❌ Missing project files: {', '.join(missing_paths)}")
        print("Please ensure all required files are in place.")
        return False
    
    print("✅ Project structure looks good!")
    return True

def create_sample_config():
    """Create a sample configuration file"""
    print("⚙️ Creating Sample Configuration...")
    
    config_content = """
# config/data_management_config.py - Sample Configuration
class DataManagementConfig:
    # Data Loader Settings
    MAX_CONCURRENT_LOADS = 5
    DEFAULT_CHUNK_SIZE = 1000
    LOAD_TIMEOUT = 300  # seconds
    
    # Data Validator Settings
    VALIDATION_TIMEOUT = 60  # seconds
    AUTO_VALIDATION = True
    
    # Performance Settings
    ENABLE_PERFORMANCE_MONITORING = True
    LOG_LEVEL = 'INFO'
    
    # Domain-Specific Settings
    SAFETY_VALIDATION_STRICT = True
    NETWORK_VALIDATION_STRICT = False
    
    # File Paths
    DATA_DIRECTORY = 'data/'
    LOG_DIRECTORY = 'logs/'
    TEMP_DIRECTORY = 'temp/'
"""
    
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / 'data_management_config.py'
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Sample configuration created at: {config_file}")
    return True

def create_sample_data():
    """Create sample data files for testing"""
    print("📊 Creating Sample Data Files...")
    
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Create valid training data
    valid_data = create_minimal_test_data()
    valid_file = data_dir / 'sample_training_data.csv'
    valid_data.to_csv(valid_file, index=False)
    
    # Create problematic data
    problematic_data = pd.DataFrame({
        'callsign': ['Unit_100', 'Unit_101', 'Unit_102'],
        'processedtimegmt': ['2025-01-01 10:00:00', 'invalid_date', '2025-01-01 10:01:00'],
        'latitude': [40.7128, 91.0, 40.7125],
        'longitude': [-74.0060, -74.0062, -181.0],
        'temp': [25.5, 80.0, 24.8],
        'battery': [95, 150, 92],
        'falldetected': ['No', 'Maybe', 'No'],
        'casualtystate': ['GOOD', 'INVALID', 'GOOD'],
        'rssi': [22, 200, 25],
        'mcs': [6, 15, 7]
    })
    
    problematic_file = data_dir / 'problematic_data.csv'
    problematic_data.to_csv(problematic_file, index=False)
    
    print(f"✅ Sample data files created:")
    print(f"  - {valid_file}")
    print(f"  - {problematic_file}")
    
    return True

def run_performance_benchmark():
    """Run a quick performance benchmark"""
    print("⚡ Running Performance Benchmark...")
    
    try:
        from core.event_bus import EventBus
        from core.models import SystemConfiguration
        from services.data_management.data_loader import DataLoader
        from services.data_management.data_validation import DataValidator
        import time
        
        # Setup
        event_bus = EventBus()
        config = SystemConfiguration()
        validator = DataValidator(event_bus, config)
        
        # Create larger dataset for benchmarking
        import numpy as np
        
        benchmark_data = pd.DataFrame({
            'callsign': [f'Unit_{i % 10}' for i in range(1000)],
            'processedtimegmt': [
                f'2025-01-01 10:{i//60:02d}:{i%60:02d}' 
                for i in range(1000)
            ],
            'latitude': np.random.uniform(40.7, 40.8, 1000),
            'longitude': np.random.uniform(-74.1, -74.0, 1000),
            'temp': np.random.normal(25, 3, 1000),
            'battery': np.random.randint(50, 101, 1000),
            'falldetected': np.random.choice(['Yes', 'No'], 1000),
            'casualtystate': np.random.choice(['GOOD', 'KILLED'], 1000),
            'rssi': np.random.randint(-50, 50, 1000),
            'mcs': np.random.randint(3, 8, 1000)
        })
        
        # Benchmark validation
        start_time = time.time()
        result = validator.validate_data(benchmark_data, request_id="benchmark_test")
        end_time = time.time()
        
        validation_time = end_time - start_time
        records_per_second = len(benchmark_data) / validation_time
        
        print(f"✅ Performance Benchmark Results:")
        print(f"  - Dataset size: {len(benchmark_data)} records")
        print(f"  - Validation time: {validation_time:.2f} seconds")
        print(f"  - Records per second: {records_per_second:.0f}")
        print(f"  - Issues found: {len(result.issues)}")
        print(f"  - Overall score: {result.overall_score:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance benchmark failed: {e}")
        return False

def create_quick_start_guide():
    """Create a quick start guide"""
    print("📖 Creating Quick Start Guide...")
    
    guide_content = """# Data Management Services Quick Start Guide

## Overview
The data management services provide data loading and validation capabilities for the AAR system.

## Quick Test Commands

### 1. Run Quick Tests
```bash
python quick_test_setup.py
```

### 2. Run Full Demo
```bash
python examples/data_management_example.py
```

### 3. Run Unit Tests
```bash
python -m pytest tests/test_data_management.py -v
```

## Basic Usage

### Data Loading
```python
from services.data_management.data_loader import DataLoader, create_csv_load_request
from core.event_bus import EventBus
from core.models import SystemConfiguration, AnalysisDomain

# Setup
event_bus = EventBus()
config = SystemConfiguration()
loader = DataLoader(event_bus, config)

# Create load request
request = create_csv_load_request(
    request_id="my_load_001",
    file_path="data/training_data.csv",
    analysis_domain=AnalysisDomain.SOLDIER_SAFETY
)

# Load data
request_id = loader.load_data(request)
```

### Data Validation
```python
from services.data_management.data_validation import DataValidator

# Setup
validator = DataValidator(event_bus, config)

# Validate data
result = validator.validate_data(
    data=my_dataframe,
    request_id="my_validation_001",
    domain=AnalysisDomain.SOLDIER_SAFETY
)

# Check results
print(f"Overall score: {result.overall_score}%")
print(f"Issues found: {len(result.issues)}")
```

## Sample Data Files
- `data/sample_training_data.csv` - Valid training data
- `data/problematic_data.csv` - Data with validation issues

## Configuration
Edit `config/data_management_config.py` to customize settings.

## Troubleshooting
1. Check dependencies: `pip install pandas numpy`
2. Verify project structure matches requirements
3. Check logs for detailed error messages
4. Run tests to identify specific issues

## Next Steps
1. Integrate with your existing AAR system
2. Customize validation rules for your specific requirements
3. Add domain-specific data loading logic
4. Configure performance settings for your environment
"""
    
    guide_file = Path('QUICK_START_GUIDE.md')
    with open(guide_file, 'w') as f:
        f.write(guide_content)
    
    print(f"✅ Quick start guide created: {guide_file}")
    return True

def main():
    """Main entry point for quick test setup"""
    print("🚀 Data Management Services Quick Test Setup")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run checks and tests
    checks_passed = 0
    total_checks = 8
    
    if check_dependencies():
        checks_passed += 1
    
    if check_project_structure():
        checks_passed += 1
    
    if create_sample_config():
        checks_passed += 1
    
    if create_sample_data():
        checks_passed += 1
    
    if quick_test_data_loader():
        checks_passed += 1
    
    if quick_test_data_validator():
        checks_passed += 1
    
    if quick_test_integration():
        checks_passed += 1
    
    if run_performance_benchmark():
        checks_passed += 1
    
    # Create helpful resources
    create_quick_start_guide()
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("✅ All tests passed! Your data management services are ready to use.")
        print("\nNext steps:")
        print("1. Run the full demo: python examples/data_management_example.py")
        print("2. Integrate with your AAR system")
        print("3. Customize validation rules as needed")
        print("4. Check QUICK_START_GUIDE.md for more information")
    else:
        print("❌ Some tests failed. Please address the issues above.")
        print("Check the error messages and ensure all dependencies are installed.")
    
    print("\n📁 Created files:")
    print("- config/data_management_config.py")
    print("- data/sample_training_data.csv")
    print("- data/problematic_data.csv")
    print("- QUICK_START_GUIDE.md")

if __name__ == "__main__":
    main()
