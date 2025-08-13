#!/usr/bin/env python3
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
                print(f"\n[TEST] Testing {name} Engine...")
                result = engine.analyze(data)
                print(f"  [SUCCESS] Analysis completed")
                print(f"  [METRICS] Metrics keys: {len(result.metrics)}")
                print(f"  [ALERTS] Alerts generated: {len(result.alerts)}")
                print(f"  [RECOMMENDATIONS] Recommendations: {len(result.recommendations)}")
                print(f"  [CONFIDENCE] Confidence: {result.confidence_score:.2f}")
                
            except Exception as e:
                print(f"  [ERROR] Error: {e}")
        
        print("\n[COMPLETE] All tests completed!")
        
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        print("Make sure all engine files are in place")

if __name__ == "__main__":
    test_engines()
