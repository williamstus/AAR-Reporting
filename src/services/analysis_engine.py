"""Analysis engine for soldier performance data"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.event_bus import EventBus, Event
from src.core.events import EventType
from src.models.soldier_data import SoldierDataset, SoldierDataRecord
from src.models.analysis_results import (
    SoldierAnalysisResult, BatchAnalysisResult, AnalysisStatus,
    HeartRateAnalysis, PhysicalPerformanceAnalysis, EquipmentAnalysis,
    SafetyAnalysis, PerformanceScore, CombatAnalysis, StatisticalSummary
)
from src.services.statistics_calculator import StatisticsCalculator

class AnalysisEngine:
    """Engine for analyzing soldier performance data"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self.stats_calculator = StatisticsCalculator()
        
        # Subscribe to analysis requests
        self.event_bus.subscribe(
            EventType.ANALYSIS_STARTED.value,
            self._handle_analysis_request
        )
    
    def _handle_analysis_request(self, event: Event):
        """Handle analysis request event"""
        dataset = event.data.get('dataset')
        if dataset:
            self.analyze_dataset(dataset)
    
    def analyze_dataset(self, dataset: SoldierDataset) -> BatchAnalysisResult:
        """Analyze entire dataset"""
        self.logger.info("Starting batch analysis...")
        
        batch_result = BatchAnalysisResult(
            analysis_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            analysis_status=AnalysisStatus.IN_PROGRESS
        )
        
        try:
            # Get unique callsigns
            if 'Callsign' in dataset.raw_dataframe.columns:
                callsigns = dataset.raw_dataframe['Callsign'].unique()
                
                for callsign in callsigns:
                    soldier_data = dataset.raw_dataframe[
                        dataset.raw_dataframe['Callsign'] == callsign
                    ]
                    
                    # Analyze individual soldier
                    soldier_result = self.analyze_soldier(callsign, soldier_data)
                    batch_result.add_soldier_result(soldier_result)
                
                # Calculate aggregate statistics
                batch_result.calculate_aggregate_statistics()
                batch_result.analysis_status = AnalysisStatus.COMPLETED
                
                self.logger.info(f"Completed analysis for {len(callsigns)} soldiers")
            
            else:
                self.logger.warning("No 'Callsign' column found in dataset")
                batch_result.analysis_status = AnalysisStatus.FAILED
                batch_result.errors.append("Missing Callsign column")
        
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            batch_result.analysis_status = AnalysisStatus.FAILED
            batch_result.errors.append(str(e))
        
        # Publish completion event
        self.event_bus.publish(Event(
            type=EventType.ANALYSIS_COMPLETED.value,
            data={'batch_result': batch_result},
            source='AnalysisEngine'
        ))
        
        return batch_result
    
    def analyze_soldier(self, callsign: str, soldier_data: Any) -> SoldierAnalysisResult:
        """Analyze individual soldier data"""
        result = SoldierAnalysisResult(
            callsign=callsign,
            analysis_id=f"soldier_{callsign}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            analysis_status=AnalysisStatus.IN_PROGRESS,
            total_records=len(soldier_data) if hasattr(soldier_data, '__len__') else 0
        )
        
        try:
            # Analyze heart rate if available
            if hasattr(soldier_data, 'columns') and 'HR' in soldier_data.columns:
                hr_values = soldier_data['HR'].dropna().tolist()
                if hr_values:
                    hr_stats = self.stats_calculator.calculate_summary(hr_values)
                    zones = self.stats_calculator.calculate_heart_rate_zones(hr_values)
                    
                    result.heart_rate_analysis = HeartRateAnalysis(
                        statistics=hr_stats,
                        zones=zones
                    )
            
            # Analyze physical performance
            if hasattr(soldier_data, 'columns') and 'Step_Count' in soldier_data.columns:
                step_values = soldier_data['Step_Count'].dropna().tolist()
                if step_values:
                    step_stats = self.stats_calculator.calculate_summary(step_values)
                    total_steps = sum(step_values)
                    
                    result.physical_performance = PhysicalPerformanceAnalysis(
                        step_statistics=step_stats,
                        total_steps=total_steps,
                        activity_level="moderate"  # Could be calculated based on steps
                    )
            
            # Create a basic performance score
            result.performance_score = PerformanceScore(
                final_score=85.0,  # Placeholder calculation
                starting_score=100.0,
                total_deductions=15.0
            )
            
            result.analysis_status = AnalysisStatus.COMPLETED
            
        except Exception as e:
            self.logger.error(f"Failed to analyze soldier {callsign}: {e}")
            result.analysis_status = AnalysisStatus.FAILED
            result.analysis_errors.append(str(e))
        
        return result
