"""
Base Analysis Engine Template
Template for creating new analysis engines
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
import pandas as pd
from core.models import AnalysisEngine, AnalysisDomain, AnalysisResult

class BaseAnalysisEngineTemplate(AnalysisEngine):
    """Template for creating new analysis engines"""
    
    def __init__(self, domain: AnalysisDomain, event_bus=None):
        super().__init__(domain)
        self.event_bus = event_bus
    
    def get_required_columns(self) -> List[str]:
        """Override to specify required columns"""
        return ["callsign", "processedtimegmt"]
    
    def get_optional_columns(self) -> List[str]:
        """Override to specify optional columns"""
        return []
    
    def get_default_thresholds(self) -> Dict[str, Any]:
        """Override to specify default thresholds"""
        return {}
    
    def validate_data(self, data: pd.DataFrame):
        """Override to implement data validation"""
        pass
    
    def analyze(self, data: pd.DataFrame, config: Dict[str, Any] = None) -> AnalysisResult:
        """Override to implement analysis logic"""
        pass
