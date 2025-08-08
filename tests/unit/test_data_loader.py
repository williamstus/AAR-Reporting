# File: tests/unit/test_data_loader.py
"""Unit tests for the data loader service"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
import tempfile

from src.services.data_loader import DataLoader
from src.core.events import EventType, FileSelectedEvent
from src.core.exceptions import DataLoadError, DataValidationError


class TestDataLoader:
    """Test the DataLoader service"""
    
    def test_initialization(self, event_bus, test_settings):
        """Test data loader initialization"""
        loader = DataLoader(event_bus, test_settings)
        
        assert loader.event_bus == event_bus
        assert loader.settings == test_settings
        assert loader.column_mapping == test_settings.column_mapping
    
    def test_load_valid_csv(self, event_bus, test_settings, sample_soldier_data, tmp_path):
        """Test loading valid CSV data"""
        # Create temporary CSV file
        csv_path = tmp_path / "test_data.csv"
        
        # Use original column names (before mapping)
        original_data = sample_soldier_data.rename(columns={
            'Callsign': 'callsign',
            'Heart_Rate': 'heartrate',
            'Step_Count': 'stepcount'
        })
        original_data.to_csv(csv_path, index=False)
        
        # Load data
        loader = DataLoader(event_bus, test_settings)
        dataset = loader.load_data(str(csv_path))
        
        # Verify dataset
        assert dataset.total_records > 0
        assert dataset.total_soldiers == 3
        assert 'Callsign' in dataset.data.columns  # Should be mapped
        assert dataset.file_path == str(csv_path)
    
    def test_file_not_found(self, event_bus, test_settings):
        """Test handling of non-existent file"""
        loader = DataLoader(event_bus, test_settings)
        
        with pytest.raises(DataLoadError, match="File not found"):
            loader.load_data("nonexistent_file.csv")
    
    def test_empty_file(self, event_bus, test_settings, tmp_path):
        """Test handling of empty CSV file"""
        # Create empty file
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("")
        
        loader = DataLoader(event_bus, test_settings)
        
        with pytest.raises(DataLoadError, match="Failed to parse CSV file"):
            loader.load_data(str(csv_path))
    
    def test_missing_required_columns(self, event_bus, test_settings, tmp_path):
        """Test handling of CSV with missing required columns"""
        # Create CSV without required columns
        csv_path = tmp_path / "invalid.csv"
        invalid_data = pd.DataFrame({'not_callsign': ['A', 'B']})
        invalid_data.to_csv(csv_path, index=False)
        
        loader = DataLoader(event_bus, test_settings)
        
        with pytest.raises(DataValidationError, match="Missing required columns"):
            loader.load_data(str(csv_path))
    
    def test_column_mapping(self, event_bus, test_settings, tmp_path):
        """Test column mapping functionality"""
        # Create CSV with original column names
        csv_path = tmp_path / "mapping_test.csv"
        data = pd.DataFrame({
            'callsign': ['ALPHA1', 'BRAVO2'],
            'heartrate': [75, 80],
            'stepcount': [100, 150]
        })
        data.to_csv(csv_path, index=False)
        
        loader = DataLoader(event_bus, test_settings)
        dataset = loader.load_data(str(csv_path))
        
        # Verify mapping was applied
        assert 'Callsign' in dataset.data.columns
        assert 'Heart_Rate' in dataset.data.columns
        assert 'Step_Count' in dataset.data.columns
        assert 'callsign' not in dataset.data.columns
        
        # Verify mapping record
        expected_mapping = {
            'callsign': 'Callsign',
            'heartrate': 'Heart_Rate',
            'stepcount': 'Step_Count'
        }
        assert dataset.column_mapping_applied == expected_mapping
    
    def test_data_cleaning(self, event_bus, test_settings, tmp_path):
        """Test data cleaning functionality"""
        # Create CSV with data that needs cleaning
        csv_path = tmp_path / "cleaning_test.csv"
        data = pd.DataFrame({
            'callsign': ['ALPHA1', 'BRAVO2'],
            'heartrate': ['75', '80'],  # String numbers
            'falldetected': ['No', 'Yes'],  # Text values
            'processedtimegmt': ['2023-01-01 10:00:00', '2023-01-01 10:01:00']
        })
        data.to_csv(csv_path, index=False)
        
        loader = DataLoader(event_bus, test_settings)
        dataset = loader.load_data(str(csv_path))
        
        # Verify cleaning
        assert dataset.data['Heart_Rate'].dtype in ['int64', 'float64']
        assert dataset.data['Fall_Detection'].tolist() == [0, 1]
        assert pd.api.types.is_datetime64_any_dtype(dataset.data['Time_Step'])
    
    def test_data_quality_validation(self, event_bus, test_settings, tmp_path):
        """Test data quality validation"""
        # Create CSV with quality issues
        csv_path = tmp_path / "quality_test.csv"
        data = pd.DataFrame({
            'callsign': ['ALPHA1', None, 'CHARLIE3'],  # Missing callsign
            'heartrate': [75, 300, 80],  # Extreme heart rate
        })
        data.to_csv(csv_path, index=False)
        
        loader = DataLoader(event_bus, test_settings)
        dataset = loader.load_data(str(csv_path))
        
        # Should identify quality issues
        assert len(dataset.data_quality_issues) > 0
        assert any('missing callsign' in issue for issue in dataset.data_quality_issues)
        assert any('extreme heart rate' in issue for issue in dataset.data_quality_issues)
    
    def test_file_selected_event_handling(self, event_bus, test_settings, sample_soldier_data, tmp_path):
        """Test handling of file selected events"""
        # Create CSV file
        csv_path = tmp_path / "event_test.csv"
        sample_soldier_data.to_csv(csv_path, index=False)
        
        # Setup event handler to capture data loaded event
        data_loaded_events = []
        
        def capture_data_loaded(event):
            data_loaded_events.append(event)
        
        event_bus.subscribe(EventType.DATA_LOADED.value, capture_data_loaded)
        
        # Create loader (subscribes to file selected events)
        loader = DataLoader(event_bus, test_settings)
        
        # Publish file selected event
        file_event = FileSelectedEvent(str(csv_path), "TestSuite")
        event_bus.publish_sync(file_event)
        
        # Verify data loaded event was published
        assert len(data_loaded_events) == 1
        loaded_event = data_loaded_events[0]
        assert loaded_event.type == EventType.DATA_LOADED.value
        assert 'dataset' in loaded_event.data
        assert loaded_event.data['file_path'] == str(csv_path)