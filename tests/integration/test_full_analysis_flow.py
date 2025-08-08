# File: tests/integration/test_full_analysis_flow.py
"""Integration tests for complete analysis workflow"""

import pytest
import time
from unittest.mock import Mock

from src.core.events import EventType, FileSelectedEvent
from src.services.data_loader import DataLoader
from src.services.analysis_engine import AnalysisEngine
from src.services.safety_analyzer import SafetyAnalyzer
from src.services.performance_scorer import PerformanceScorer
from src.services.statistics_calculator import StatisticsCalculator


class TestFullAnalysisFlow:
    """Test complete analysis workflow from file to results"""
    
    def test_complete_analysis_workflow(self, event_bus, test_settings, sample_soldier_data, tmp_path):
        """Test complete workflow from CSV file to analysis results"""
        # Create CSV file
        csv_path = tmp_path / "integration_test.csv"
        sample_soldier_data.to_csv(csv_path, index=False)
        
        # Setup event handlers to track workflow
        events_received = []
        
        def track_events(event):
            events_received.append(event.type)
        
        # Subscribe to all relevant events
        for event_type in [
            EventType.DATA_LOADED.value,
            EventType.ANALYSIS_STARTED.value,
            EventType.ANALYSIS_COMPLETED.value
        ]:
            event_bus.subscribe(event_type, track_events)
        
        # Initialize services
        data_loader = DataLoader(event_bus, test_settings)
        analysis_engine = AnalysisEngine(event_bus)
        
        # Start workflow by selecting file
        file_event = FileSelectedEvent(str(csv_path), "IntegrationTest")
        event_bus.publish_sync(file_event)
        
        # Wait a moment for processing
        time.sleep(0.1)
        
        # Manually trigger analysis
        from src.core.events import Event
        analysis_event = Event(
            type=EventType.ANALYSIS_STARTED.value,
            source="IntegrationTest"
        )
        event_bus.publish_sync(analysis_event)
        
        # Verify workflow completed
        assert EventType.DATA_LOADED.value in events_received
        assert EventType.ANALYSIS_COMPLETED.value in events_received
        
        # Verify analysis results
        results = analysis_engine.get_current_results()
        assert results is not None
        assert len(results.soldier_stats) == 3  # Should have 3 soldiers
        assert len(results.performance_scores) == 3
        assert len(results.safety_analyses) == 3
        assert results.battle_analysis['total_soldiers'] == 3
    
    def test_error_handling_in_workflow(self, event_bus, test_settings, tmp_path):
        """Test error handling throughout the workflow"""
        # Setup error tracking
        errors_received = []
        
        def track_errors(event):
            errors_received.append(event)
        
        event_bus.subscribe(EventType.ERROR_OCCURRED.value, track_errors)
        
        # Initialize services
        data_loader = DataLoader(event_bus, test_settings)
        
        # Try to load non-existent file
        file_event = FileSelectedEvent("nonexistent.csv", "ErrorTest")
        event_bus.publish_sync(file_event)
        
        # Should receive error event
        assert len(errors_received) > 0
        error_event = errors_received[0]
        assert "File not found" in error_event.data['error_message']
    
    def test_performance_measurement(self, event_bus, test_settings, sample_soldier_data, tmp_path):
        """Test performance measurement of analysis workflow"""
        # Create larger dataset for performance testing
        large_data = sample_soldier_data
        for i in range(10):  # Duplicate data to make it larger
            large_data = pd.concat([large_data, sample_soldier_data], ignore_index=True)
        
        csv_path = tmp_path / "performance_test.csv"
        large_data.to_csv(csv_path, index=False)
        
        # Initialize services
        data_loader = DataLoader(event_bus, test_settings)
        analysis_engine = AnalysisEngine(event_bus)
        
        # Time the workflow
        start_time = time.time()
        
        # Load data
        file_event = FileSelectedEvent(str(csv_path), "PerformanceTest")
        event_bus.publish_sync(file_event)
        
        # Run analysis
        from src.core.events import Event
        analysis_event = Event(
            type=EventType.ANALYSIS_STARTED.value,
            source="PerformanceTest"
        )
        event_bus.publish_sync(analysis_event)
        
        end_time = time.time()
        
        # Verify reasonable performance (should complete in reasonable time)
        total_time = end_time - start_time
        assert total_time < 10.0  # Should complete in under 10 seconds
        
        # Verify results
        results = analysis_engine.get_current_results()
        assert results is not None
        assert results.analysis_duration > 0
