"""
Core data models for the AAR system
Defines base classes and enums used throughout the system
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd


class AnalysisDomain(Enum):
    """Analysis domains supported by the AAR system"""
    SAFETY = "safety"
    NETWORK = "network" 
    ACTIVITY = "activity"
    EQUIPMENT = "equipment"
    ENVIRONMENTAL = "environmental"


class AnalysisLevel(Enum):
    """Level of analysis granularity"""
    INDIVIDUAL = "individual"
    SQUAD = "squad"
    PLATOON = "platoon"
    BATTALION = "battalion"


class AlertLevel(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(Enum):
    """Analysis task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Alert:
    """Alert generated during analysis"""
    level: AlertLevel
    message: str
    domain: AnalysisDomain
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


@dataclass
class AnalysisResult:
    """Result of an analysis operation"""
    domain: AnalysisDomain
    metrics: Dict[str, Any]
    alerts: List[Alert]
    recommendations: List[str]
    confidence_score: float
    analysis_timestamp: datetime


@dataclass
class ReportConfiguration:
    """Configuration for report generation"""
    report_type: str
    output_format: str
    include_charts: bool = True
    include_raw_data: bool = False
    analysis_domains: List[AnalysisDomain] = None
    analysis_level: AnalysisLevel = AnalysisLevel.INDIVIDUAL
    custom_fields: Dict[str, Any] = None


@dataclass
class AnalysisTask:
    """Task for analysis execution"""
    task_id: str
    domain: AnalysisDomain
    data: pd.DataFrame
    config: Dict[str, Any]
    priority: int
    created_at: datetime
    status: TaskStatus = TaskStatus.PENDING
    
    def __lt__(self, other):
        """Less than comparison for priority queue"""
        if not isinstance(other, AnalysisTask):
            return NotImplemented
        
        # Lower priority number = higher priority (processed first)
        if self.priority != other.priority:
            return self.priority < other.priority
        
        # If same priority, compare by creation time (FIFO)
        return self.created_at < other.created_at
    
    def __eq__(self, other):
        """Equality comparison"""
        if not isinstance(other, AnalysisTask):
            return NotImplemented
        return self.task_id == other.task_id
    
    def __hash__(self):
        """Hash for use in sets/dicts"""
        return hash(self.task_id)
    
    def __repr__(self):
        """String representation for debugging"""
        return f"AnalysisTask(id={self.task_id[:8]}..., domain={self.domain.value}, priority={self.priority})"


class AnalysisEngine(ABC):
    """Base class for all analysis engines"""
    
    def __init__(self, domain: AnalysisDomain):
        self.domain = domain
    
    @abstractmethod
    def get_required_columns(self) -> List[str]:
        """Return list of required column names for this analysis"""
        pass
    
    @abstractmethod
    def analyze(self, data: pd.DataFrame, config: Dict[str, Any] = None) -> AnalysisResult:
        """Perform analysis on the provided data"""
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate that data contains required columns"""
        required_columns = self.get_required_columns()
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            print(f"Warning: Missing required columns for {self.domain.value}: {missing_columns}")
            return False
        
        return True


class ReportGenerator(ABC):
    """Base class for report generators"""
    
    def __init__(self, report_type: str):
        self.report_type = report_type
    
    @abstractmethod
    def can_handle_config(self, config: ReportConfiguration) -> bool:
        """Check if this generator can handle the given configuration"""
        pass
    
    @abstractmethod
    def generate_report(self, config: ReportConfiguration, 
                       results: Dict[AnalysisDomain, AnalysisResult]) -> str:
        """Generate report content based on configuration and results"""
        pass


@dataclass
class SystemMetrics:
    """System performance and health metrics"""
    total_analyses: int
    successful_analyses: int
    failed_analyses: int
    average_execution_time: float
    active_engines: List[AnalysisDomain]
    system_uptime: datetime
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None


@dataclass
class UserPreferences:
    """User interface and analysis preferences"""
    default_analysis_domains: List[AnalysisDomain]
    auto_generate_reports: bool = True
    alert_thresholds: Dict[AlertLevel, bool] = None
    ui_theme: str = "default"
    export_format: str = "json"


class DataValidator:
    """Utility class for data validation"""
    
    @staticmethod
    def validate_timestamp_column(data: pd.DataFrame, column_name: str = 'Timestamp') -> bool:
        """Validate timestamp column format"""
        if column_name not in data.columns:
            return False
        
        try:
            pd.to_datetime(data[column_name])
            return True
        except Exception:
            return False
    
    @staticmethod
    def validate_unit_column(data: pd.DataFrame, column_name: str = 'Unit') -> bool:
        """Validate unit identifier column"""
        if column_name not in data.columns:
            return False
        
        # Check for reasonable number of unique units
        unique_units = data[column_name].nunique()
        return 1 <= unique_units <= 1000  # Reasonable range
    
    @staticmethod
    def validate_numeric_column(data: pd.DataFrame, column_name: str, 
                               min_val: float = None, max_val: float = None) -> bool:
        """Validate numeric column with optional range checking"""
        if column_name not in data.columns:
            return False
        
        try:
            numeric_data = pd.to_numeric(data[column_name], errors='coerce')
            
            # Check for too many NaN values
            if numeric_data.isna().sum() / len(data) > 0.5:  # More than 50% missing
                return False
            
            # Range validation
            if min_val is not None and numeric_data.min() < min_val:
                return False
            
            if max_val is not None and numeric_data.max() > max_val:
                return False
            
            return True
        except Exception:
            return False


class EventTypes:
    """Constants for event bus event types"""
    
    # Analysis events
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    
    # Task events
    TASK_SUBMITTED = "task_submitted"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    
    # System events
    ENGINE_REGISTERED = "engine_registered"
    ENGINE_UNREGISTERED = "engine_unregistered"
    ORCHESTRATOR_STARTED = "orchestrator_started"
    ORCHESTRATOR_STOPPED = "orchestrator_stopped"
    
    # Data events
    DATA_LOADED = "data_loaded"
    DATA_VALIDATED = "data_validated"
    DATA_EXPORT_STARTED = "data_export_started"
    DATA_EXPORT_COMPLETED = "data_export_completed"
    
    # Report events
    REPORT_GENERATED = "report_generated"
    REPORT_EXPORTED = "report_exported"
    
    # Alert events
    ALERT_GENERATED = "alert_generated"
    CRITICAL_ALERT = "critical_alert"


class ColumnMappings:
    """Standard column name mappings for data consistency"""
    
    # Core columns that should be present in most datasets
    CORE_COLUMNS = {
        'unit_id': ['Unit', 'unit_id', 'UnitID', 'unit'],
        'timestamp': ['Timestamp', 'timestamp', 'time', 'Time'],
        'latitude': ['Lat', 'latitude', 'lat', 'Latitude'],
        'longitude': ['Long', 'longitude', 'long', 'Longitude', 'lon']
    }
    
    # Domain-specific column mappings
    SAFETY_COLUMNS = {
        'casualty_state': ['CasualtyState', 'casualty_state', 'status'],
        'fall_detected': ['FallDetected', 'fall_detected', 'fall'],
        'heart_rate': ['HeartRate', 'heart_rate', 'hr']
    }
    
    NETWORK_COLUMNS = {
        'rssi': ['RSSI', 'rssi', 'signal_strength'],
        'mcs': ['MCS', 'mcs', 'modulation_coding'],
        'network_hops': ['NetworkHops', 'network_hops', 'hops']
    }
    
    ACTIVITY_COLUMNS = {
        'steps': ['Steps', 'steps', 'step_count'],
        'posture': ['Posture', 'posture', 'position']
    }
    
    EQUIPMENT_COLUMNS = {
        'battery_level': ['BatteryLevel', 'battery_level', 'battery']
    }
    
    ENVIRONMENTAL_COLUMNS = {
        'temperature': ['Temperature', 'temperature', 'temp']
    }
    
    @classmethod
    def find_column(cls, data: pd.DataFrame, standard_name: str) -> Optional[str]:
        """Find the actual column name in data that corresponds to a standard name"""
        
        # Combine all mappings
        all_mappings = {
            **cls.CORE_COLUMNS,
            **cls.SAFETY_COLUMNS,
            **cls.NETWORK_COLUMNS,
            **cls.ACTIVITY_COLUMNS,
            **cls.EQUIPMENT_COLUMNS,
            **cls.ENVIRONMENTAL_COLUMNS
        }
        
        if standard_name in all_mappings:
            for possible_name in all_mappings[standard_name]:
                if possible_name in data.columns:
                    return possible_name
        
        return None


# Utility functions
def create_alert(level: AlertLevel, message: str, domain: AnalysisDomain, 
                details: Dict[str, Any] = None) -> Alert:
    """Utility function to create an alert"""
    return Alert(
        level=level,
        message=message,
        domain=domain,
        timestamp=datetime.now(),
        details=details
    )


def validate_analysis_result(result: AnalysisResult) -> bool:
    """Validate that an analysis result is properly formed"""
    if not isinstance(result, AnalysisResult):
        return False
    
    if not isinstance(result.domain, AnalysisDomain):
        return False
    
    if not isinstance(result.metrics, dict):
        return False
    
    if not isinstance(result.alerts, list):
        return False
    
    if not isinstance(result.recommendations, list):
        return False
    
    if not isinstance(result.confidence_score, (int, float)):
        return False
    
    if not (0.0 <= result.confidence_score <= 1.0):
        return False
    
    return True


def get_default_analysis_config() -> Dict[str, Any]:
    """Get default analysis configuration"""
    return {
        'analysis_level': AnalysisLevel.INDIVIDUAL,
        'include_alerts': True,
        'include_recommendations': True,
        'confidence_threshold': 0.8,
        'alert_thresholds': {
            'safety': {
                'fall_threshold': 5,
                'casualty_threshold': 0.1
            },
            'network': {
                'rssi_threshold': -70,
                'mcs_threshold': 3
            },
            'activity': {
                'step_threshold': 100,
                'inactivity_threshold': 300
            },
            'equipment': {
                'battery_threshold': 20,
                'malfunction_threshold': 0.05
            },
            'environmental': {
                'temperature_threshold': 35
            }
        }
    }