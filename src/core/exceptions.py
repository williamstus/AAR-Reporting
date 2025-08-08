# File: src/core/exceptions.py
"""Custom exceptions for the Enhanced Soldier Report System"""


class SoldierReportSystemError(Exception):
    """Base exception for all system errors"""
    pass


class DataLoadError(SoldierReportSystemError):
    """Raised when data loading fails"""
    pass


class DataValidationError(SoldierReportSystemError):
    """Raised when data validation fails"""
    pass


class AnalysisError(SoldierReportSystemError):
    """Raised when analysis fails"""
    pass


class ReportGenerationError(SoldierReportSystemError):
    """Raised when report generation fails"""
    pass


class ConfigurationError(SoldierReportSystemError):
    """Raised when configuration is invalid"""
    pass


class EventBusError(SoldierReportSystemError):
    """Raised when event bus operations fail"""
    pass