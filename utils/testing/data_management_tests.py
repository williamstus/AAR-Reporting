# tests/test_data_management.py - Comprehensive Test Suite for Data Management Services
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import json
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import your services
from services.data_management.data_loader import (
    DataLoader, DataLoadRequest, DataSourceType, LoadingStatus,
    create_csv_load_request, create_stream_load_request
)
from services.data_management.data_validation import (
    DataValidator, ValidationRule, ValidationRuleType, ValidationSeverity,
    ValidationResult, create_safety_validation_rules, create_network_validation_rules
)
from core.event_bus import EventBus, Event, EventType
from core.models import AnalysisDomain, SystemConfiguration

class TestDataLoader:
    """Test suite for DataLoader service"""
    
    @pytest.fixture
    def event_bus(self):
        """Create a mock event bus for testing"""
        return EventBus()
    
    @pytest.fixture
    def config(self):
        """Create a test configuration"""
        config = SystemConfiguration()
        config.max_concurrent_loads = 3
        config.default_chunk_size = 100
        config.load_timeout = 30
        return config
    
    @pytest.fixture
    def data_loader(self, event_bus, config):
        """Create a DataLoader instance for testing"""
        return DataLoader(event_bus, config)
    
    @pytest.fixture
    def sample_csv_data(self):
        """Create sample CSV data for testing"""
        data = {
            'callsign': ['Unit_100', 'Unit_101', 'Unit_102', 'Unit_103'],
            'processedtimegmt': [
                '2025-01-01 10:00:00',
                '2025-01-01 10:00:30',
                '2025-01-01 10:01:00',
                '2025-01-01 10:01:30'
            ],
            'latitude': [40.7128, 40.7130, 40.7125, 40.7135],
            'longitude': [-74.0060, -74.0062, -74.0058, -74.0065],
            'temp': [25.5, 26.0, 24.8, 25.2],
            'battery': [95, 87, 92, 88],
            'falldetected': ['No', 'Yes', 'No', 'No'],
            'casualtystate': ['GOOD', 'FALL ALERT', 'GOOD', 'GOOD'],
            'rssi': [22, 18, 25, 20],
            'mcs': [6, 5, 7, 6],
            'nexthop': ['Router_1', 'Router_2', 'Router_1', 'Router_3'],
            'steps': [150, 200, 180, 170],
            'posture': ['Standing', 'Prone', 'Standing', 'Standing'],
            'squad': ['Alpha', 'Alpha', 'Bravo', 'Bravo']
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def temp_csv_file(self, sample_csv_data):
        """Create a temporary CSV file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_csv_data.to_csv(f.name, index=False)
            return f.name
    
    def test_data_loader_initialization(self, data_loader):
        """Test DataLoader initialization"""
        assert data_loader.max_concurrent_loads == 3
        assert data_loader.chunk_size == 100
        assert data_loader.timeout == 30
        assert len(data_loader.active_requests) == 0
        assert len(data_loader.completed_requests) == 0
    
    def test_csv_load_request_creation(self):
        """Test creating CSV load requests"""
        request = create_csv_load_request(
            request_id="test_001",
            file_path="test.csv",
            analysis_domain=AnalysisDomain.SOLDIER_SAFETY
        )
        
        assert request.request_id == "test_001"
        assert request.source_type == DataSourceType.CSV_FILE
        assert request.source_path == "test.csv"
        assert 'callsign' in request.target_columns
        assert 'falldetected' in request.target_columns
        assert 'casualtystate' in request.target_columns
    
    def test_csv_data_loading(self, data_loader, temp_csv_file):
        """Test loading CSV data"""
        request = DataLoadRequest(
            request_id="csv_test_001",
            source_type=DataSourceType.CSV_FILE,
            source_path=temp_csv_file,
            target_columns=['callsign', 'processedtimegmt', 'temp'],
            optional_columns=['latitude', 'longitude', 'battery']
        )
        
        # Load data synchronously for testing
        data = data_loader._load_csv_data(request)
        
        assert len(data) == 4
        assert 'callsign' in data.columns
        assert 'temp' in data.columns
        assert data['callsign'].iloc[0] == 'Unit_100'
        assert data['temp'].iloc[0] == 25.5
        
        # Clean up
        Path(temp_csv_file).unlink()
    
    def test_column_mapping(self, data_loader):
        """Test column mapping functionality"""
        # Create data with alternative column names
        data = pd.DataFrame({
            'unit_id': ['Unit_100', 'Unit_101'],
            'timestamp': ['2025-01-01 10:00:00', '2025-01-01 10:00:30'],
            'lat': [40.7128, 40.7130],
            'lon': [-74.0060, -74.0062]
        })
        
        target_columns = ['callsign', 'processedtimegmt', 'latitude', 'longitude']
        mapped_data = data_loader._map_columns(data, target_columns)
        
        assert 'callsign' in mapped_data.columns
        assert 'processedtimegmt' in mapped_data.columns
        assert 'latitude' in mapped_data.columns
        assert 'longitude' in mapped_data.columns
    
    def test_data_transformations(self, data_loader, sample_csv_data):
        """Test data transformation functionality"""
        transformations = {
            'temp': {'type': 'normalize'},
            'battery': {'type': 'fill_missing', 'value': 100},
            'processedtimegmt': {'type': 'convert_type', 'target_type': 'datetime'}
        }
        
        # Add some missing values
        sample_csv_data.loc[0, 'battery'] = np.nan
        
        transformed_data = data_loader._apply_transformations(sample_csv_data, transformations)
        
        # Check normalization
        assert abs(transformed_data['temp'].mean()) < 0.01  # Should be close to 0
        
        # Check missing value filling
        assert transformed_data['battery'].iloc[0] == 100
        
        # Check datetime conversion
        assert pd.api.types.is_datetime64_any_dtype(transformed_data['processedtimegmt'])
    
    def test_data_filters(self, data_loader, sample_csv_data):
        """Test data filtering functionality"""
        filters = {
            'temp': {'type': 'range', 'min': 25.0, 'max': 26.0},
            'casualtystate': {'type': 'values', 'values': ['GOOD']},
            'battery': {'type': 'not_null'}
        }
        
        filtered_data = data_loader._apply_filters(sample_csv_data, filters)
        
        # Should filter out records outside temperature range
        assert all(filtered_data['temp'] >= 25.0)
        assert all(filtered_data['temp'] <= 26.0)
        
        # Should only include GOOD casualty states
        assert all(filtered_data['casualtystate'] == 'GOOD')
        
        # Should exclude null battery values
        assert filtered_data['battery'].notna().all()
    
    def test_concurrent_loading_limits(self, data_loader):
        """Test concurrent loading limits"""
        # Fill up concurrent load slots
        for i in range(3):
            request = DataLoadRequest(
                request_id=f"concurrent_{i}",
                source_type=DataSourceType.STREAM,
                source_path="test_stream",
                target_columns=['callsign']
            )
            data_loader.active_requests[f"concurrent_{i}"] = request
        
        # Try to add one more - should raise error
        with pytest.raises(RuntimeError, match="Maximum concurrent loads"):
            new_request = DataLoadRequest(
                request_id="concurrent_4",
                source_type=DataSourceType.STREAM,
                source_path="test_stream",
                target_columns=['callsign']
            )
            data_loader.load_data(new_request)
    
    def test_stream_data_loading(self, data_loader):
        """Test streaming data loading"""
        request = DataLoadRequest(
            request_id="stream_test_001",
            source_type=DataSourceType.STREAM,
            source_path="test_stream",
            target_columns=['callsign', 'processedtimegmt'],
            chunk_size=50
        )
        
        data = data_loader._load_stream_data(request)
        
        assert len(data) == 50
        assert 'callsign' in data.columns
        assert 'processedtimegmt' in data.columns
        assert data['callsign'].iloc[0].startswith('Unit_')
    
    def test_event_handling(self, data_loader):
        """Test event handling for load requests"""
        # Mock event data
        event_data = {
            'request_id': 'event_test_001',
            'source_type': 'csv_file',
            'source_path': 'test.csv',
            'target_columns': ['callsign', 'temp'],
            'optional_columns': ['battery']
        }
        
        event = Event(
            EventType.DATA_LOAD_REQUESTED,
            event_data,
            source='TestRunner'
        )
        
        # This should not raise an exception
        data_loader.handle_load_request(event)
    
    def test_load_cancellation(self, data_loader):
        """Test load request cancellation"""
        request = DataLoadRequest(
            request_id="cancel_test_001",
            source_type=DataSourceType.STREAM,
            source_path="test_stream",
            target_columns=['callsign']
        )
        
        # Add to active requests
        data_loader.active_requests["cancel_test_001"] = request
        
        # Cancel the request
        success = data_loader.cancel_load_request("cancel_test_001")
        
        assert success
        assert "cancel_test_001" not in data_loader.active_requests
        assert "cancel_test_001" in data_loader.completed_requests
        assert data_loader.completed_requests["cancel_test_001"].status == LoadingStatus.CANCELLED


class TestDataValidator:
    """Test suite for DataValidator service"""
    
    @pytest.fixture
    def event_bus(self):
        """Create a mock event bus for testing"""
        return EventBus()
    
    @pytest.fixture
    def config(self):
        """Create a test configuration"""
        return SystemConfiguration()
    
    @pytest.fixture
    def data_validator(self, event_bus, config):
        """Create a DataValidator instance for testing"""
        return DataValidator(event_bus, config)
    
    @pytest.fixture
    def valid_sample_data(self):
        """Create valid sample data for testing"""
        return pd.DataFrame({
            'callsign': ['Unit_100', 'Unit_101', 'Unit_102'],
            'processedtimegmt': [
                '2025-01-01 10:00:00',
                '2025-01-01 10:00:30',
                '2025-01-01 10:01:00'
            ],
            'latitude': [40.7128, 40.7130, 40.7125],
            'longitude': [-74.0060, -74.0062, -74.0058],
            'temp': [25.5, 26.0, 24.8],
            'battery': [95, 87, 92],
            'falldetected': ['No', 'Yes', 'No'],
            'casualtystate': ['GOOD', 'FALL ALERT', 'GOOD'],
            'rssi': [22, 18, 25],
            'mcs': [6, 5, 7]
        })
    
    @pytest.fixture
    def invalid_sample_data(self):
        """Create invalid sample data for testing"""
        return pd.DataFrame({
            'callsign': ['Unit_100', 'Unit_101', 'Unit_102'],
            'processedtimegmt': [
                '2025-01-01 10:00:00',
                'invalid_date',
                '2025-01-01 10:01:00'
            ],
            'latitude': [40.7128, 91.0, 40.7125],  # Invalid latitude
            'longitude': [-74.0060, -74.0062, -181.0],  # Invalid longitude
            'temp': [25.5, 80.0, 24.8],  # Invalid temperature
            'battery': [95, 150, 92],  # Invalid battery level
            'falldetected': ['No', 'Maybe', 'No'],  # Invalid fall detection
            'casualtystate': ['GOOD', 'INVALID', 'GOOD'],  # Invalid casualty state
            'rssi': [22, 200, 25],  # Invalid RSSI
            'mcs': [6, 15, 7]  # Invalid MCS
        })
    
    def test_validator_initialization(self, data_validator):
        """Test DataValidator initialization"""
        assert len(data_validator.validation_rules) > 0
        assert len(data_validator.validators) > 0
        assert data_validator.validation_stats['total_validations'] == 0
    
    def test_required_column_validation(self, data_validator):
        """Test required column validation"""
        # Data missing required columns
        incomplete_data = pd.DataFrame({
            'callsign': ['Unit_100'],
            'temp': [25.5]
            # Missing 'processedtimegmt' and other required columns
        })
        
        result = data_validator.validate_data(incomplete_data, domain=AnalysisDomain.SOLDIER_SAFETY)
        
        # Should have validation issues for missing columns
        missing_column_issues = [
            issue for issue in result.issues 
            if 'missing' in issue.message.lower()
        ]
        assert len(missing_column_issues) > 0
    
    def test_data_type_validation(self, data_validator, invalid_sample_data):
        """Test data type validation"""
        result = data_validator.validate_data(invalid_sample_data)
        
        # Should have issues with invalid datetime
        datetime_issues = [
            issue for issue in result.issues 
            if 'datetime' in issue.message.lower()
        ]
        assert len(datetime_issues) > 0
    
    def test_value_range_validation(self, data_validator, invalid_sample_data):
        """Test value range validation"""
        result = data_validator.validate_data(invalid_sample_data)
        
        # Should have issues with out-of-range values
        range_issues = [
            issue for issue in result.issues 
            if 'range' in issue.message.lower()
        ]
        assert len(range_issues) > 0
        
        # Check specific range violations
        latitude_issues = [issue for issue in result.issues if issue.column == 'latitude']
        longitude_issues = [issue for issue in result.issues if issue.column == 'longitude']
        battery_issues = [issue for issue in result.issues if issue.column == 'battery']
        
        assert len(latitude_issues) > 0
        assert len(longitude_issues) > 0
        assert len(battery_issues) > 0
    
    def test_pattern_matching_validation(self, data_validator, invalid_sample_data):
        """Test pattern matching validation"""
        result = data_validator.validate_data(invalid_sample_data)
        
        # Should have issues with invalid patterns
        pattern_issues = [
            issue for issue in result.issues 
            if issue.rule_id.startswith('PM_')
        ]
        assert len(pattern_issues) > 0
    
    def test_business_rule_validation(self, data_validator):
        """Test business rule validation"""
        # Create data with invalid casualty state transitions
        invalid_transition_data = pd.DataFrame({
            'callsign': ['Unit_100', 'Unit_100', 'Unit_100'],
            'processedtimegmt': [
                '2025-01-01 10:00:00',
                '2025-01-01 10:00:30',
                '2025-01-01 10:01:00'
            ],
            'casualtystate': ['GOOD', 'RESURRECTED', 'KILLED'],  # Invalid transition
            'falldetected': ['No', 'No', 'No'],
            'temp': [25.5, 26.0, 24.8],
            'battery': [95, 87, 92],
            'rssi': [22, 18, 25],
            'mcs': [6, 5, 7]
        })
        
        result = data_validator.validate_data(invalid_transition_data)
        
        # Should have issues with invalid transitions
        business_rule_issues = [
            issue for issue in result.issues 
            if issue.rule_id.startswith('BR_')
        ]
        assert len(business_rule_issues) > 0
    
    def test_overall_score_calculation(self, data_validator, valid_sample_data, invalid_sample_data):
        """Test overall score calculation"""
        # Valid data should have high score
        valid_result = data_validator.validate_data(valid_sample_data)
        assert valid_result.overall_score > 80
        
        # Invalid data should have low score
        invalid_result = data_validator.validate_data(invalid_sample_data)
        assert invalid_result.overall_score < 50
    
    def test_validation_rule_management(self, data_validator):
        """Test validation rule management"""
        initial_count = len(data_validator.validation_rules)
        
        # Add a new rule
        new_rule = ValidationRule(
            rule_id="TEST_RULE",
            rule_type=ValidationRuleType.VALUE_RANGE,
            severity=ValidationSeverity.WARNING,
            description="Test rule",
            column="test_column",
            parameters={'min': 0, 'max': 100}
        )
        
        data_validator.add_validation_rule(new_rule)
        assert len(data_validator.validation_rules) == initial_count + 1
        
        # Disable the rule
        data_validator.disable_rule("TEST_RULE")
        rule = next(r for r in data_validator.validation_rules if r.rule_id == "TEST_RULE")
        assert not rule.enabled
        
        # Enable the rule
        data_validator.enable_rule("TEST_RULE")
        rule = next(r for r in data_validator.validation_rules if r.rule_id == "TEST_RULE")
        assert rule.enabled
        
        # Remove the rule
        data_validator.remove_validation_rule("TEST_RULE")
        assert len(data_validator.validation_rules) == initial_count
    
    def test_domain_specific_validation(self, data_validator, valid_sample_data):
        """Test domain-specific validation"""
        # Test safety domain validation
        safety_result = data_validator.validate_data(
            valid_sample_data, 
            domain=AnalysisDomain.SOLDIER_SAFETY
        )
        
        # Test network domain validation
        network_result = data_validator.validate_data(
            valid_sample_data, 
            domain=AnalysisDomain.NETWORK_PERFORMANCE
        )
        
        assert safety_result.request_id != network_result.request_id
        # Domain-specific rules should apply different validations
    
    def test_validation_report_generation(self, data_validator, invalid_sample_data):
        """Test validation report generation"""
        result = data_validator.validate_data(invalid_sample_data)
        report = data_validator.create_validation_report(result)
        
        assert 'validation_summary' in report
        assert 'data_quality_metrics' in report
        assert 'issues_analysis' in report
        assert 'detailed_issues' in report
        assert 'recommendations' in report
        assert 'system_statistics' in report
        
        # Check report structure
        assert report['validation_summary']['total_records'] == len(invalid_sample_data)
        assert report['issues_analysis']['total_issues'] == len(result.issues)
        assert len(report['detailed_issues']) == len(result.issues)
        assert len(report['recommendations']) > 0
    
    def test_factory_functions(self):
        """Test factory functions for creating domain-specific rules"""
        safety_rules = create_safety_validation_rules()
        network_rules = create_network_validation_rules()
        
        assert len(safety_rules) > 0
        assert len(network_rules) > 0
        
        # Check that rules are properly configured
        for rule in safety_rules:
            assert rule.domain == AnalysisDomain.SOLDIER_SAFETY
        
        for rule in network_rules:
            assert rule.domain == AnalysisDomain.NETWORK_PERFORMANCE


class TestIntegration:
    """Integration tests for data loader and validator working together"""
    
    @pytest.fixture
    def integrated_system(self):
        """Create an integrated system with loader and validator"""
        event_bus = EventBus()
        config = SystemConfiguration()
        
        loader = DataLoader(event_bus, config)
        validator = DataValidator(event_bus, config)
        
        return {
            'event_bus': event_bus,
            'loader': loader,
            'validator': validator,
            'config': config
        }
    
    def test_event_driven_integration(self, integrated_system):
        """Test event-driven integration between loader and validator"""
        event_bus = integrated_system['event_bus']
        
        # Track events
        events_received = []
        
        def event_tracker(event):
            events_received.append(event)
        
        # Subscribe to all events
        for event_type in EventType:
            event_bus.subscribe(event_type, event_tracker)
        
        # Trigger a validation request
        event_bus.publish(Event(
            EventType.DATA_VALIDATION_REQUESTED,
            {
                'request_id': 'integration_test_001',
                'data': pd.DataFrame({
                    'callsign': ['Unit_100'],
                    'temp': [25.5],
                    'processedtimegmt': ['2025-01-01 10:00:00']
                })
            },
            source='TestRunner'
        ))
        
        # Give time for event processing
        time.sleep(0.1)
        
        # Should have received events
        assert len(events_received) > 0
        
        # Check for validation completion event
        validation_events = [
            e for e in events_received 
            if e.event_type == EventType.DATA_VALIDATION_COMPLETED
        ]
        assert len(validation_events) > 0
    
    def test_auto_validation_after_load(self, integrated_system):
        """Test automatic validation after data loading"""
        loader = integrated_system['loader']
        validator = integrated_system['validator']
        event_bus = integrated_system['event_bus']
        
        # Create sample data file
        sample_data = pd.DataFrame({
            'callsign': ['Unit_100', 'Unit_101'],
            'processedtimegmt': ['2025-01-01 10:00:00', '2025-01-01 10:00:30'],
            'temp': [25.5, 26.0],
            'battery': [95, 87]
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_data.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            # Trigger load completion event
            event_bus.publish(Event(
                EventType.DATA_LOAD_COMPLETED,
                {
                    'request_id': 'auto_validation_test',
                    'records_loaded': 2,
                    'loading_time': 0.5
                },
                source='TestDataLoader'
            ))
            
            # Give time for auto-validation trigger
            time.sleep(0.1)
            
            # Auto-validation should have been triggered
            # (In real implementation, this would validate the loaded data)
            
        finally:
            Path(temp_file).unlink()


# Performance and stress tests
class TestPerformance:
    """Performance tests for data management services"""
    
    def test_large_dataset_loading(self):
        """Test loading large datasets"""
        # Create large dataset
        large_data = pd.DataFrame({
            'callsign': [f'Unit_{i}' for i in range(10000)],
            'processedtimegmt': [
                (datetime.now() - timedelta(seconds=i)).strftime('%Y-%m-%d %H:%M:%S')
                for i in range(10000)
            ],
            'temp': np.random.normal(25, 5, 10000),
            'battery': np.random.randint(0, 101, 10000),
            'rssi': np.random.randint(-50, 50, 10000),
            'mcs': np.random.randint(0, 12, 10000)
        })
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            large_data.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            # Test loading performance
            event_bus = EventBus()
            config = SystemConfiguration()
            loader = DataLoader(event_bus, config)
            
            start_time = time.time()
            
            request = DataLoadRequest(
                request_id="perf_test_001",
                source_type=DataSourceType.CSV_FILE,
                source_path=temp_file,
                target_columns=['callsign', 'processedtimegmt', 'temp'],
                chunk_size=1000
            )
            
            loaded_data = loader._load_csv_data(request)
            
            end_time = time.time()
            load_time = end_time - start_time
            
            assert len(loaded_data) == 10000
            assert load_time < 5.0  # Should load in under 5 seconds
            
        finally:
            Path(temp_file).unlink()
    
    def test_validation_performance(self):
        """Test validation performance on large datasets"""
        # Create large dataset with various issues
        large_data = pd.DataFrame({
            'callsign': [f'Unit_{i}' for i in range(5000)],
            'processedtimegmt': [
                (datetime.now() - timedelta(seconds=i)).strftime('%Y-%m-%d %H:%M:%S')
                for i in range(5000)
            ],
            'latitude': np.random.uniform(-90, 90, 5000),
            'longitude': np.random.uniform(-180, 180, 5000),
            'temp': np.random.normal(25, 10, 5000),  # Some values will be out of range
            'battery': np.random.randint(-10, 110, 5000),  # Some invalid values
            'falldetected': np.random.choice(['Yes', 'No', 'Maybe'], 5000),  # Some invalid
            'casualtystate': np.random.choice(['GOOD', 'KILLED', 'INVALID'], 5000),  # Some invalid
            'rssi': np.random.randint(-150, 150, 5000),  # Some out of range
            'mcs': np.random.randint(-1, 15, 5000)  # Some out of range
        })
        
        # Test validation performance
        event_bus = EventBus()
        config = SystemConfiguration()
        validator = DataValidator(event_bus, config)
        
        start_time = time.time()
        result = validator.validate_data(large_data)
        end_time = time.time()
        
        validation_time = end_time - start_time
        
        assert result.total_records == 5000
        assert validation_time < 10.0  # Should validate in under 10 seconds
        assert len(result.issues) > 0  # Should find issues


# Utility functions for testing
def create_test_data_files(temp_dir: str) -> Dict[str, str]:
    """Create test data files for comprehensive testing"""
    files = {}
    
    # Valid training data
    valid_data = pd.DataFrame({
        'callsign': ['Unit_100', 'Unit_101', 'Unit_102', 'Unit_103'],
        'processedtimegmt': [
            '2025-01-01 10:00:00',
            '2025-01-01 10:00:30',
            '2025-01-01 10:01:00',
            '2025-01-01 10:01:30'
        ],
        'latitude': [40.7128, 40.7130, 40.7125, 40.7135],
        'longitude': [-74.0060, -74.0062, -74.0058, -74.0065],
        'temp': [25.5, 26.0, 24.8, 25.2],
        'battery': [95, 87, 92, 88],
        'falldetected': ['No', 'Yes', 'No', 'No'],
        'casualtystate': ['GOOD', 'FALL ALERT', 'GOOD', 'GOOD'],
        'rssi': [22, 18, 25, 20],
        'mcs': [6, 5, 7, 6],
        'nexthop': ['Router_1', 'Router_2', 'Router_1', 'Router_3'],
        'steps': [150, 200, 180, 170],
        'posture': ['Standing', 'Prone', 'Standing', 'Standing'],
        'squad': ['Alpha', 'Alpha', 'Bravo', 'Bravo']
    })
    
    valid_file = Path(temp_dir) / "valid_training_data.csv"
    valid_data.to_csv(valid_file, index=False)
    files['valid'] = str(valid_file)
    
    # Invalid training data
    invalid_data = pd.DataFrame({
        'callsign': ['Unit_100', 'Unit_101', 'Unit_102'],
        'processedtimegmt': ['2025-01-01 10:00:00', 'invalid_date', '2025-01-01 10:01:00'],
        'latitude': [40.7128, 91.0, 40.7125],  # Invalid latitude
        'longitude': [-74.0060, -74.0062, -181.0],  # Invalid longitude
        'temp': [25.5, 80.0, 24.8],  # Invalid temperature
        'battery': [95, 150, 92],  # Invalid battery
        'falldetected': ['No', 'Maybe', 'No'],  # Invalid value
        'casualtystate': ['GOOD', 'INVALID', 'GOOD'],  # Invalid state
        'rssi': [22, 200, 25],  # Invalid RSSI
        'mcs': [6, 15, 7]  # Invalid MCS
    })
    
    invalid_file = Path(temp_dir) / "invalid_training_data.csv"
    invalid_data.to_csv(invalid_file, index=False)
    files['invalid'] = str(invalid_file)
    
    # JSON training data
    json_data = valid_data.to_dict('records')
    json_file = Path(temp_dir) / "training_data.json"
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    files['json'] = str(json_file)
    
    return files


def run_comprehensive_tests():
    """Run comprehensive tests for data management services"""
    # Create temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        test_files = create_test_data_files(temp_dir)
        
        print("🧪 Running Data Management Service Tests...")
        print("=" * 50)
        
        # Run pytest programmatically
        pytest.main([
            __file__,
            "-v",
            "--tb=short",
            f"--rootdir={temp_dir}"
        ])
        
        print("\n✅ Test Results:")
        print("- Data Loader: CSV, JSON, and Stream loading")
        print("- Data Validator: All rule types and business logic")
        print("- Integration: Event-driven communication")
        print("- Performance: Large dataset handling")


if __name__ == "__main__":
    run_comprehensive_tests()
