"""Statistics calculation service for soldier data analysis"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Union
from src.models.analysis_results import StatisticalSummary

class StatisticsCalculator:
    """Service for calculating statistical summaries and metrics"""
    
    def __init__(self):
        self.name = "StatisticsCalculator"
    
    def calculate_summary(self, values: List[Union[int, float]]) -> StatisticalSummary:
        """Calculate statistical summary from list of values"""
        return StatisticalSummary.from_values(values)
    
    def calculate_heart_rate_zones(self, heart_rates: List[float]) -> Dict[str, int]:
        """Calculate heart rate zone distribution"""
        zones = {
            'rest': 0,        # < 60 BPM
            'normal': 0,      # 60-100 BPM
            'elevated': 0,    # 100-150 BPM
            'high': 0,        # 150-180 BPM
            'extreme': 0,     # 180-190 BPM
            'critical': 0     # > 190 BPM
        }
        
        for hr in heart_rates:
            if hr < 60:
                zones['rest'] += 1
            elif hr < 100:
                zones['normal'] += 1
            elif hr < 150:
                zones['elevated'] += 1
            elif hr < 180:
                zones['high'] += 1
            elif hr < 190:
                zones['extreme'] += 1
            else:
                zones['critical'] += 1
        
        return zones
    
    def calculate_percentiles(self, values: List[float], percentiles: List[float] = None) -> Dict[str, float]:
        """Calculate percentiles for a list of values"""
        if percentiles is None:
            percentiles = [25, 50, 75, 90, 95]
        
        if not values:
            return {f"p{p}": 0.0 for p in percentiles}
        
        np_values = np.array(values)
        return {f"p{p}": float(np.percentile(np_values, p)) for p in percentiles}
    
    def calculate_moving_average(self, values: List[float], window_size: int = 5) -> List[float]:
        """Calculate moving average with specified window size"""
        if len(values) < window_size:
            return values
        
        return [float(np.mean(values[i:i+window_size])) 
                for i in range(len(values) - window_size + 1)]
    
    def detect_outliers(self, values: List[float], method: str = "iqr") -> List[int]:
        """Detect outliers using IQR or z-score method"""
        if not values or len(values) < 4:
            return []
        
        np_values = np.array(values)
        outlier_indices = []
        
        if method == "iqr":
            q1 = np.percentile(np_values, 25)
            q3 = np.percentile(np_values, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outlier_indices = [i for i, val in enumerate(values) 
                             if val < lower_bound or val > upper_bound]
        
        elif method == "zscore":
            mean = np.mean(np_values)
            std = np.std(np_values)
            z_scores = np.abs((np_values - mean) / std)
            outlier_indices = [i for i, z in enumerate(z_scores) if z > 3]
        
        return outlier_indices
    
    def calculate_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate correlation coefficient between two series"""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0
        
        correlation_matrix = np.corrcoef(x_values, y_values)
        return float(correlation_matrix[0, 1]) if not np.isnan(correlation_matrix[0, 1]) else 0.0
