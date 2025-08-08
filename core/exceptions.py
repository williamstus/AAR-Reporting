"""
AAR System Custom Exceptions
"""

class AARSystemError(Exception):
    """Base exception for AAR system"""
    pass

class DataValidationError(AARSystemError):
    """Raised when data validation fails"""
    pass

class AnalysisEngineError(AARSystemError):
    """Raised when analysis engine encounters an error"""
    pass

class ReportGenerationError(AARSystemError):
    """Raised when report generation fails"""
    pass

class ConfigurationError(AARSystemError):
    """Raised when configuration is invalid"""
    pass

class EventBusError(AARSystemError):
    """Raised when event bus encounters an error"""
    pass

class TaskExecutionError(AARSystemError):
    """Raised when task execution fails"""
    pass
