<<<<<<< HEAD
import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4
import tkinter as tk

from src.core.event_bus import EventBus
#from src.models.soldier_data import SoldierDataset, SoldierStats, SafetyAnalysis
from src.config.settings import Settings
from src.models.report_config import ReportConfig, ReportFormat, ReportType
from src.models.report_generation import BatchReportSession
from src.controllers.report_controller import ReportController
from src.controllers.main_controller import MainController
from src.services.report_renderer import HTMLRenderer  # Adjust if needed

# --- Existing Fixtures (keep these) ---

@pytest.fixture
def event_bus():
    bus = EventBus()
    bus.start()
    yield bus
    bus.stop()

@pytest.fixture
def test_settings():
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
    base_time = datetime.now()
    data = []
    callsigns = ['ALPHA1', 'BRAVO2', 'CHARLIE3']
    for i, callsign in enumerate(callsigns):
        for j in range(50):
            data.append({
                'Callsign': callsign,
                'Platoon': f'SQUAD{i+1}',
                'Time_Step': base_time + timedelta(minutes=j),
                'Heart_Rate': 70 + (i * 10) + (j % 20),
                'Step_Count': 100 + (j * 2),
                'Temperature': 98.6 + (j * 0.1),
                'Battery': 100 - (j * 1.5),
                'RSSI': -60 - (j * 0.5),
                'Posture': ['Standing', 'Crouching', 'Prone'][j % 3],
                'Casualty_State': 'GOOD' if j < 45 else ('WOUNDED' if i == 0 else 'GOOD'),
                'Fall_Detection': 0,
                'Latitude': 40.7128 + (i * 0.001),
                'Longitude': -74.0060 + (i * 0.001),
                'Weapon': 'M4A1'
            })
    return pd.DataFrame(data)

@pytest.fixture
def sample_dataset(sample_soldier_data, tmp_path):
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
    return SafetyAnalysis(
        overall_safety_score=85,
        temperature_risk='LOW',
        physiological_stress='MEDIUM',
        heart_rate_alerts=['Elevated heart rate: 120 BPM'],
        equipment_risk='LOW'
    )

@pytest.fixture
def temp_output_dir(tmp_path):
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    return output_dir

# --- New Fixtures for Controller and Report Testing ---

@pytest.fixture
def report_config():
    return ReportConfig(
        report_type=ReportType.INDIVIDUAL_SOLDIER,
        report_format=ReportFormat.HTML,
        template_name="default",
        custom_sections=["summary", "performance", "safety"],
        metric_display={},
        output_settings={},
    )

@pytest.fixture
def report_generation_request(sample_dataset, report_config):
    return {
        "request_id": str(uuid4()),
        "callsigns": ["ALPHA1", "BRAVO2"],
        "output_directory": Path("test_reports"),
        "dataset": sample_dataset,
        "config": report_config,
        "timestamp": datetime.now()
    }

@pytest.fixture
def report_controller(event_bus):
    html_renderer = HTMLRenderer()
    return ReportController(event_bus=event_bus, html_renderer=html_renderer)

@pytest.fixture
def main_controller(monkeypatch):
    monkeypatch.setattr(tk, "Tk", lambda: tk.Tk())
    return MainController()

@pytest.fixture
def batch_report_session():
    return BatchReportSession(
        session_id=str(uuid4()),
        callsigns=["ALPHA1", "BRAVO2", "CHARLIE3"],
        config=None,
        completed_reports=[],
        failed_reports=[],
        status="PENDING"
    )

@pytest.fixture
def tmp_report_dir(tmp_path):
    path = tmp_path / "test_reports"
    path.mkdir()
    return path

from dataclasses import dataclass
from typing import List

@dataclass
class SoldierStats:
    callsign: str
    total_records: int
    total_steps: int
    avg_steps: float
    min_heart_rate: int
    avg_heart_rate: int
    max_heart_rate: int
    avg_battery: float
    final_status: str
    mission_duration: float

@dataclass
class SafetyAnalysis:
    overall_safety_score: int
    temperature_risk: str
    physiological_stress: str
    heart_rate_alerts: List[str]
    equipment_risk: str

=======
# Pytest configuration
>>>>>>> dae0a8cb6feadc2779506d88360bd7bf01476064
