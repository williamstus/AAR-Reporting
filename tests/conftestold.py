# File: tests/conftest.py
"""Pytest configuration and shared fixtures"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import json
from datetime import datetime, timedelta

from src.core.event_bus import EventBus
from src.models.soldier_data import SoldierDataset, SoldierStats, SafetyAnalysis
from src.config.settings import Settings


@pytest.fixture
def event_bus():
    """Create a fresh event bus for each test"""
    bus = EventBus()
    bus.start()
    yield bus
    bus.stop()


@pytest.fixture
def test_settings():
    """Create test settings configuration"""
    return Settings(
        column_mapping={
            'callsign': 'Callsign',
            'squad': 'Platoon',
            'casualtystate': 'Casualty_State',
            'processedtimegmt': 'Time_Step',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'posture': 'Posture',
            'heartrate': 'Heart_Rate',
            'stepcount': 'Step_Count',
            'temp': 'Temperature',
            'falldetected': 'Fall_Detection',
            'battery': 'Battery',
            'rssi': 'RSSI',
            'weapon': 'Weapon'
        },
        performance_scoring={
            'activity_weight': 0.3,
            'casualty_penalty': {'WOUNDED': 10, 'KIA': 20},
            'battery_thresholds': {'critical': 10, 'low': 20}
        }
    )


@pytest.fixture
def sample_soldier_data():
    """Create sample soldier data for testing"""
    base_time = datetime.now()
    
    data = []
    callsigns = ['ALPHA1', 'BRAVO2', 'CHARLIE3']
    
    for i, callsign in enumerate(callsigns):
        for j in range(50):  # 50 records per soldier
            record = {
                'Callsign': callsign,
                'Platoon': f'SQUAD{i+1}',
                'Time_Step': base_time + timedelta(minutes=j),
                'Heart_Rate': 70 + (i * 10) + (j % 20),  # Varying heart rates
                'Step_Count': 100 + (j * 2),
                'Temperature': 98.6 + (j * 0.1),
                'Battery': 100 - (j * 1.5),  # Decreasing battery
                'RSSI': -60 - (j * 0.5),
                'Posture': ['Standing', 'Crouching', 'Prone'][j % 3],
                'Casualty_State': 'GOOD' if j < 45 else ('WOUNDED' if i == 0 else 'GOOD'),
                'Fall_Detection': 0,
                'Latitude': 40.7128 + (i * 0.001),
                'Longitude': -74.0060 + (i * 0.001),
                'Weapon': 'M4A1'
            }
            data.append(record)
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_dataset(sample_soldier_data, tmp_path):
    """Create a sample SoldierDataset for testing"""
    csv_path = tmp_path / "test_data.csv"
    sample_soldier_data.to_csv(csv_path, index=False)
    
    return SoldierDataset(
        data=sample_soldier_data,
        file_path=str(csv_path),
        total_soldiers=3,
        total_records=150
    )


@pytest.fixture
def sample_soldier_stats():
    """Create sample soldier statistics"""
    return SoldierStats(
        callsign='ALPHA1',
        total_records=50,
        total_steps=5000,
        avg_steps=100,
        min_heart_rate=70,
        avg_heart_rate=85,
        max_heart_rate=120,
        avg_battery=75,
        final_status='WOUNDED',
        mission_duration=49.0
    )


@pytest.fixture
def sample_safety_analysis():
    """Create sample safety analysis"""
    return SafetyAnalysis(
        overall_safety_score=85,
        temperature_risk='LOW',
        physiological_stress='MEDIUM',
        heart_rate_alerts=['Elevated heart rate: 120 BPM'],
        equipment_risk='LOW'
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory"""
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    return output_dir