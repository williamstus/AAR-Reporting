# File: src/config/settings.py
"""Configuration management for the Enhanced Soldier Report System"""

import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class PerformanceSettings:
    """Performance scoring configuration"""
    activity_weight: float = 0.3
    casualty_penalties: Dict[str, int] = field(default_factory=lambda: {
        'WOUNDED': 10,
        'KIA': 20,
        'KILL': 20
    })
    battery_thresholds: Dict[str, int] = field(default_factory=lambda: {
        'critical': 10,
        'low': 20,
        'good': 60
    })
    heart_rate_zones: Dict[str, tuple] = field(default_factory=lambda: {
        'rest': (0, 60),
        'normal': (60, 100),
        'elevated': (100, 150),
        'high': (150, 180),
        'extreme': (180, 190),
        'critical': (190, 300)
    })
    medical_alert_penalty: int = 3  # Reduced from 5
    safety_score_weight: float = 0.2


@dataclass
class DataProcessingSettings:
    """Data processing configuration"""
    chunk_size: int = 10000
    required_columns: list = field(default_factory=lambda: ['Callsign'])
    numeric_columns: list = field(default_factory=lambda: [
        'Heart_Rate', 'Step_Count', 'Temperature', 'Battery', 'RSSI'
    ])
    fall_detection_mapping: Dict[str, int] = field(default_factory=lambda: {
        'No': 0, 'Yes': 1, 'FALSE': 0, 'TRUE': 1
    })


@dataclass
class ReportingSettings:
    """Report generation configuration"""
    output_directory: str = "reports/enhanced"
    template_directory: str = "templates"
    batch_size: int = 10
    max_concurrent_reports: int = 4
    include_debug_info: bool = False
    
    html_template: str = "base_report.html"
    performance_template: str = "performance_section.html"
    safety_template: str = "safety_section.html"


@dataclass
class UISettings:
    """User interface configuration"""
    window_title: str = "🎖️ Enhanced Individual Soldier Report System"
    window_size: str = "1200x900"
    theme_colors: Dict[str, str] = field(default_factory=lambda: {
        'primary': '#2c3e50',
        'secondary': '#3498db',
        'success': '#27ae60',
        'warning': '#f39c12',
        'danger': '#e74c3c',
        'background': '#ecf0f1'
    })
    font_family: str = "Arial"
    status_update_interval: int = 100  # milliseconds


@dataclass
class Settings:
    """Main configuration class"""
    
    # Column mapping for CSV files
    column_mapping: Dict[str, str] = field(default_factory=lambda: {
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
        'weapon': 'Weapon',
        'shootercallsign': 'Shooter_Callsign',
        'munition': 'Munition',
        'hitzone': 'Hit_Zone',
        'mcs': 'MCS',
        'nexthop': 'Next_Hop',
        'ip': 'IP_Address',
        'playerid': 'Player_ID'
    })
    
    # Component settings
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)
    data_processing: DataProcessingSettings = field(default_factory=DataProcessingSettings)
    reporting: ReportingSettings = field(default_factory=ReportingSettings)
    ui: UISettings = field(default_factory=UISettings)
    
    # System settings
    log_level: str = "INFO"
    debug_mode: bool = False
    max_workers: int = 4
    event_queue_size: int = 1000
    
    @classmethod
    def load_from_file(cls, config_path: Path) -> 'Settings':
        """Load settings from JSON configuration file"""
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Create settings instance
            settings = cls()
            
            # Update with loaded data
            settings._update_from_dict(config_data)
            
            logging.info(f"Loaded configuration from {config_path}")
            return settings
            
        except FileNotFoundError:
            logging.warning(f"Config file not found: {config_path}, using defaults")
            return cls()
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in config file: {e}")
            return cls()
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            return cls()
    
    def save_to_file(self, config_path: Path) -> None:
        """Save current settings to JSON file"""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = self._to_dict()
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            logging.info(f"Saved configuration to {config_path}")
            
        except Exception as e:
            logging.error(f"Error saving config: {e}")
            raise
    
    def _update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update settings from dictionary"""
        if 'column_mapping' in data:
            self.column_mapping.update(data['column_mapping'])
        
        if 'performance' in data:
            self._update_performance_settings(data['performance'])
        
        if 'data_processing' in data:
            self._update_data_processing_settings(data['data_processing'])
        
        if 'reporting' in data:
            self._update_reporting_settings(data['reporting'])
        
        if 'ui' in data:
            self._update_ui_settings(data['ui'])
        
        # Update top-level settings
        for key in ['log_level', 'debug_mode', 'max_workers', 'event_queue_size']:
            if key in data:
                setattr(self, key, data[key])
    
    def _update_performance_settings(self, data: Dict[str, Any]) -> None:
        """Update performance settings"""
        for key, value in data.items():
            if hasattr(self.performance, key):
                setattr(self.performance, key, value)
    
    def _update_data_processing_settings(self, data: Dict[str, Any]) -> None:
        """Update data processing settings"""
        for key, value in data.items():
            if hasattr(self.data_processing, key):
                setattr(self.data_processing, key, value)
    
    def _update_reporting_settings(self, data: Dict[str, Any]) -> None:
        """Update reporting settings"""
        for key, value in data.items():
            if hasattr(self.reporting, key):
                setattr(self.reporting, key, value)
    
    def _update_ui_settings(self, data: Dict[str, Any]) -> None:
        """Update UI settings"""
        for key, value in data.items():
            if hasattr(self.ui, key):
                setattr(self.ui, key, value)
    
    def _to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return {
            'column_mapping': self.column_mapping,
            'performance': {
                'activity_weight': self.performance.activity_weight,
                'casualty_penalties': self.performance.casualty_penalties,
                'battery_thresholds': self.performance.battery_thresholds,
                'heart_rate_zones': self.performance.heart_rate_zones,
                'medical_alert_penalty': self.performance.medical_alert_penalty,
                'safety_score_weight': self.performance.safety_score_weight
            },
            'data_processing': {
                'chunk_size': self.data_processing.chunk_size,
                'required_columns': self.data_processing.required_columns,
                'numeric_columns': self.data_processing.numeric_columns,
                'fall_detection_mapping': self.data_processing.fall_detection_mapping
            },
            'reporting': {
                'output_directory': self.reporting.output_directory,
                'template_directory': self.reporting.template_directory,
                'batch_size': self.reporting.batch_size,
                'max_concurrent_reports': self.reporting.max_concurrent_reports,
                'include_debug_info': self.reporting.include_debug_info,
                'html_template': self.reporting.html_template,
                'performance_template': self.reporting.performance_template,
                'safety_template': self.reporting.safety_template
            },
            'ui': {
                'window_title': self.ui.window_title,
                'window_size': self.ui.window_size,
                'theme_colors': self.ui.theme_colors,
                'font_family': self.ui.font_family,
                'status_update_interval': self.ui.status_update_interval
            },
            'log_level': self.log_level,
            'debug_mode': self.debug_mode,
            'max_workers': self.max_workers,
            'event_queue_size': self.event_queue_size
        }