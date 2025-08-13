"""
Setup Script for AAR Analysis Engines
Creates the necessary directory structure and files for the new analysis engines
"""

import os
import shutil

def create_directory_structure():
    """Create the required directory structure"""
    
    directories = [
        "engines/activity",
        "engines/equipment", 
        "engines/environmental"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"[SUCCESS] Created directory: {directory}")
        else:
            print(f"[EXISTS] Directory exists: {directory}")
        
        # Create __init__.py files
        init_file = os.path.join(directory, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('# Analysis engine module\n')
            print(f"[SUCCESS] Created __init__.py in {directory}")

def copy_engine_files():
    """Instructions for copying engine files"""
    
    print("\n[NEXT STEPS]")
    print("=" * 50)
    
    engine_files = [
        ("soldier_activity_engine", "engines/activity/soldier_activity_engine.py"),
        ("equipment_management_engine", "engines/equipment/equipment_management_engine.py"),
        ("environmental_monitoring_engine", "engines/environmental/environmental_monitoring_engine.py")
    ]
    
    for artifact_name, target_path in engine_files:
        print(f"\n[COPY] Copy content from '{artifact_name}' artifact to:")
        print(f"       -> {target_path}")
    
    print(f"\n[COPY] Replace your analysis orchestrator with:")
    print(f"       -> services/orchestration/analysis_orchestrator.py")
    print(f"       (Use 'updated_analysis_orchestrator' artifact)")
    
    print(f"\n[COPY] Update your main application:")
    print(f"       -> ui/main_application.py")
    print(f"       (Use 'updated_main_application' artifact)")

def check_existing_files():
    """Check which files already exist"""
    
    print("\n[FILE STATUS]")
    print("=" * 30)
    
    required_files = [
        "core/event_bus.py",
        "core/models.py", 
        "engines/safety/soldier_safety_engine.py",
        "engines/network/network_performance_engine.py",
        "engines/activity/soldier_activity_engine.py",
        "engines/equipment/equipment_management_engine.py",
        "engines/environmental/environmental_monitoring_engine.py",
        "services/orchestration/analysis_orchestrator.py",
        "services/reporting/report_service.py",
        "ui/main_application.py"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"[OK] {file_path}")
        else:
            print(f"[MISSING] {file_path}")

def create_sample_test_script():
    """Create a sample test script"""
    
    test_script = '''#!/usr/bin/env python3
"""
Test script for AAR Analysis Engines
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Test data creation
def create_test_data():
    """Create sample test data"""
    
    # Create 1000 records for 4 units over 23 minutes
    np.random.seed(42)
    
    records = []
    start_time = datetime(2025, 7, 17, 10, 0, 0)
    
    units = ['Unit_108', 'Unit_134', 'Unit_142', 'Unit_156']
    
    for i in range(1000):
        timestamp = start_time + timedelta(seconds=i * 1.38)  # ~23 minutes total
        unit = np.random.choice(units)
        
        record = {
            'Unit': unit,
            'Timestamp': timestamp,
            'Steps': np.random.randint(0, 400),
            'BatteryLevel': max(0, 100 - (i * 0.05) + np.random.normal(0, 5)),
            'Posture': np.random.choice(['Standing', 'Prone', 'Unknown']),
            'CasualtyState': np.random.choice(['GOOD', 'KILLED', 'RESURRECTED'], p=[0.8, 0.15, 0.05]),
            'FallDetected': np.random.choice([0, 1], p=[0.9, 0.1]),
            'RSSI': np.random.normal(20, 10),
            'MCS': np.random.randint(1, 8),
            'NetworkHops': np.random.randint(1, 5),
            'Lat': 39.0 + np.random.normal(0, 0.001),
            'Long': -77.0 + np.random.normal(0, 0.001),
            'Temperature': 22 + np.random.normal(0, 3)
        }
        
        records.append(record)
    
    return pd.DataFrame(records)

def test_engines():
    """Test the analysis engines"""
    
    try:
        from core.event_bus import EventBus
        from engines.activity.soldier_activity_engine import SoldierActivityAnalysisEngine
        from engines.equipment.equipment_management_engine import EquipmentManagementAnalysisEngine
        from engines.environmental.environmental_monitoring_engine import EnvironmentalMonitoringAnalysisEngine
        
        print("[SUCCESS] All engines imported successfully")
        
        # Create test data
        data = create_test_data()
        print(f"[SUCCESS] Created test data: {len(data)} records")
        
        # Initialize event bus
        event_bus = EventBus()
        
        # Test each engine
        engines = [
            ("Activity", SoldierActivityAnalysisEngine(event_bus)),
            ("Equipment", EquipmentManagementAnalysisEngine(event_bus)),
            ("Environmental", EnvironmentalMonitoringAnalysisEngine(event_bus))
        ]
        
        for name, engine in engines:
            try:
                print(f"\\n[TEST] Testing {name} Engine...")
                result = engine.analyze(data)
                print(f"  [SUCCESS] Analysis completed")
                print(f"  [METRICS] Metrics keys: {len(result.metrics)}")
                print(f"  [ALERTS] Alerts generated: {len(result.alerts)}")
                print(f"  [RECOMMENDATIONS] Recommendations: {len(result.recommendations)}")
                print(f"  [CONFIDENCE] Confidence: {result.confidence_score:.2f}")
                
            except Exception as e:
                print(f"  [ERROR] Error: {e}")
        
        print("\\n[COMPLETE] All tests completed!")
        
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        print("Make sure all engine files are in place")

if __name__ == "__main__":
    test_engines()
'''
    
    # Use UTF-8 encoding to avoid Unicode issues
    try:
        with open("test_engines.py", "w", encoding='utf-8') as f:
            f.write(test_script)
        print(f"\n[SUCCESS] Created test script: test_engines.py")
        print("   Run with: python test_engines.py")
    except Exception as e:
        print(f"[ERROR] Could not create test script: {e}")

def main():
    """Main setup function"""
    
    print("AAR Analysis Engine Setup")
    print("=" * 40)
    
    # Create directories
    create_directory_structure()
    
    # Check existing files
    check_existing_files()
    
    # Copy instructions
    copy_engine_files()
    
    # Create test script
    create_sample_test_script()
    
    print(f"\n[COMPLETE] Setup Complete!")
    print("Follow the copy instructions above to complete the installation.")

if __name__ == "__main__":
    main()