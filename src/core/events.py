# File: src/core/events.py
"""Event definitions for the Enhanced Soldier Report System"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional, Dict
import time
import uuid


class EventType(Enum):
    """Enumeration of all event types in the system"""
    
    # Data events
    FILE_SELECTED = "file_selected"
    DATA_LOADED = "data_loaded"
    DATA_LOAD_FAILED = "data_load_failed"
    DATA_VALIDATED = "data_validated"
    DATA_VALIDATION_FAILED = "data_validation_failed"
    
    # Analysis events
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_PROGRESS = "analysis_progress"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    
    # UI events
    SOLDIER_SELECTED = "soldier_selected"
    SOLDIERS_SELECTED = "soldiers_selected"
    REPORT_GENERATION_REQUESTED = "report_generation_requested"
    OUTPUT_DIRECTORY_CHANGED = "output_directory_changed"
    
    # Report events
    REPORT_STARTED = "report_started"
    REPORT_PROGRESS = "report_progress"
    REPORT_COMPLETED = "report_completed"
    REPORT_FAILED = "report_failed"
    BATCH_REPORT_STARTED = "batch_report_started"
    BATCH_REPORT_COMPLETED = "batch_report_completed"
    
    # Status events
    STATUS_UPDATE = "status_update"
    ERROR_OCCURRED = "error_occurred"
    WARNING_ISSUED = "warning_issued"
    
    # Application events
    APPLICATION_STARTED = "application_started"
    APPLICATION_SHUTDOWN = "application_shutdown"


@dataclass
class Event:
    """Base event class for all system events"""
    
    type: str
    data: Any = None
    source: str = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate event after initialization"""
        if not self.type:
            raise ValueError("Event type cannot be empty")


@dataclass
class FileSelectedEvent(Event):
    """Event for when a file is selected"""
    
    def __init__(self, file_path: str, source: str = None):
        super().__init__(
            type=EventType.FILE_SELECTED.value,
            data={'file_path': file_path},
            source=source
        )


@dataclass
class DataLoadedEvent(Event):
    """Event for when data is successfully loaded"""
    
    def __init__(self, dataset, file_path: str, source: str = None):
        super().__init__(
            type=EventType.DATA_LOADED.value,
            data={
                'dataset': dataset,
                'file_path': file_path,
                'record_count': len(dataset.data) if hasattr(dataset, 'data') else 0
            },
            source=source
        )


@dataclass
class AnalysisCompletedEvent(Event):
    """Event for when analysis is completed"""
    
    def __init__(self, results, analysis_type: str, source: str = None):
        super().__init__(
            type=EventType.ANALYSIS_COMPLETED.value,
            data={
                'results': results,
                'analysis_type': analysis_type
            },
            source=source
        )


@dataclass
class ReportGenerationRequestedEvent(Event):
    """Event for when report generation is requested"""
    
    def __init__(self, soldier_callsigns: list, output_directory: str, source: str = None):
        super().__init__(
            type=EventType.REPORT_GENERATION_REQUESTED.value,
            data={
                'soldier_callsigns': soldier_callsigns,
                'output_directory': output_directory,
                'count': len(soldier_callsigns)
            },
            source=source
        )


@dataclass
class StatusUpdateEvent(Event):
    """Event for status updates"""
    
    def __init__(self, message: str, level: str = "info", source: str = None):
        super().__init__(
            type=EventType.STATUS_UPDATE.value,
            data={
                'message': message,
                'level': level
            },
            source=source
        )


@dataclass
class ErrorEvent(Event):
    """Event for error conditions"""
    
    def __init__(self, error: Exception, context: str = None, source: str = None):
        super().__init__(
            type=EventType.ERROR_OCCURRED.value,
            data={
                'error': error,
                'error_message': str(error),
                'error_type': type(error).__name__,
                'context': context
            },
            source=source
        )