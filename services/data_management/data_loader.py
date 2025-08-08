# services/data_management/data_loader.py - Event-Driven Data Loading Service
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import logging
import threading
import asyncio
from dataclasses import dataclass
from enum import Enum
import json
import csv
from io import StringIO

from core.event_bus import EventBus, Event, EventType
from core.models import (
    AnalysisDomain, DataQualityMetrics, SystemConfiguration
)

class DataSourceType(Enum):
    """Supported data source types"""
    CSV_FILE = "csv_file"
    JSON_FILE = "json_file"
    DATABASE = "database"
    STREAM = "stream"
    API = "api"
    SENSOR = "sensor"

class LoadingStatus(Enum):
    """Data loading status"""
    PENDING = "pending"
    LOADING = "loading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class DataLoadRequest:
    """Data loading request configuration"""
    request_id: str
    source_type: DataSourceType
    source_path: str
    target_columns: List[str]
    optional_columns: List[str] = None
    filters: Dict[str, Any] = None
    transformations: Dict[str, Any] = None
    chunk_size: int = 1000
    priority: int = 1
    timeout: int = 300
    metadata: Dict[str, Any] = None

@dataclass
class DataLoadResult:
    """Result of data loading operation"""
    request_id: str
    status: LoadingStatus
    data: Optional[pd.DataFrame] = None
    records_loaded: int = 0
    loading_time: float = 0.0
    data_quality: Optional[DataQualityMetrics] = None
    errors: List[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None

class DataLoader:
    """
    Event-driven data loading service for the AAR system
    Supports REQ-TECH-001 through REQ-TECH-008 requirements
    """
    
    def __init__(self, event_bus: EventBus, config: SystemConfiguration):
        self.event_bus = event_bus
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Loading state management
        self.active_requests: Dict[str, DataLoadRequest] = {}
        self.completed_requests: Dict[str, DataLoadResult] = {}
        self.loading_threads: Dict[str, threading.Thread] = {}
        
        # Configuration
        self.max_concurrent_loads = config.max_concurrent_loads if hasattr(config, 'max_concurrent_loads') else 5
        self.chunk_size = config.default_chunk_size if hasattr(config, 'default_chunk_size') else 1000
        self.timeout = config.load_timeout if hasattr(config, 'load_timeout') else 300
        
        # Performance monitoring
        self.load_statistics = {
            'total_requests': 0,
            'successful_loads': 0,
            'failed_loads': 0,
            'total_records_loaded': 0,
            'average_load_time': 0.0,
            'peak_concurrent_loads': 0
        }
        
        # Setup event subscriptions
        self._setup_event_subscriptions()
        
        # Known column mappings for military data
        self.column_mappings = {
            'soldier_data': {
                'callsign': ['callsign', 'unit_id', 'soldier_id'],
                'processedtimegmt': ['timestamp', 'time', 'processedtimegmt'],
                'latitude': ['lat', 'latitude', 'y'],
                'longitude': ['lon', 'longitude', 'x'],
                'temp': ['temperature', 'temp', 'body_temp'],
                'battery': ['battery', 'power', 'battery_level'],
                'falldetected': ['fall_detected', 'fall', 'falldetected'],
                'casualtystate': ['casualty_state', 'status', 'casualtystate'],
                'rssi': ['rssi', 'signal_strength', 'signal'],
                'mcs': ['mcs', 'modulation', 'coding_scheme'],
                'nexthop': ['nexthop', 'next_hop', 'router'],
                'steps': ['steps', 'step_count', 'activity'],
                'posture': ['posture', 'position', 'stance'],
                'squad': ['squad', 'team', 'group']
            }
        }
        
        self.logger.info("DataLoader service initialized with event-driven architecture")
    
    def _setup_event_subscriptions(self):
        """Setup event subscriptions for data loading requests"""
        self.event_bus.subscribe(EventType.DATA_LOAD_REQUESTED, self.handle_load_request, priority=1)
        self.event_bus.subscribe(EventType.DATA_LOAD_CANCELLED, self.handle_load_cancellation, priority=1)
        self.event_bus.subscribe(EventType.CONFIG_CHANGED, self.handle_config_change, priority=3)
    
    def load_data(self, request: DataLoadRequest) -> str:
        """
        Initiate data loading operation
        REQ-TECH-001: Sub-second data ingestion capability
        """
        request_id = request.request_id
        
        # Validate request
        if request_id in self.active_requests:
            raise ValueError(f"Load request {request_id} already active")
        
        # Check concurrent load limits
        if len(self.active_requests) >= self.max_concurrent_loads:
            raise RuntimeError(f"Maximum concurrent loads ({self.max_concurrent_loads}) exceeded")
        
        # Store request
        self.active_requests[request_id] = request
        
        # Publish load started event
        self.event_bus.publish(Event(
            EventType.DATA_LOAD_STARTED,
            {
                'request_id': request_id,
                'source_type': request.source_type.value,
                'source_path': request.source_path,
                'target_columns': request.target_columns
            },
            source='DataLoader'
        ))
        
        # Start loading in background thread
        load_thread = threading.Thread(
            target=self._load_data_async,
            args=(request,),
            name=f"DataLoader-{request_id}"
        )
        load_thread.start()
        self.loading_threads[request_id] = load_thread
        
        self.load_statistics['total_requests'] += 1
        self.load_statistics['peak_concurrent_loads'] = max(
            self.load_statistics['peak_concurrent_loads'],
            len(self.active_requests)
        )
        
        return request_id
    
    def _load_data_async(self, request: DataLoadRequest):
        """Asynchronous data loading implementation"""
        start_time = datetime.now()
        request_id = request.request_id
        
        try:
            # Load data based on source type
            if request.source_type == DataSourceType.CSV_FILE:
                data = self._load_csv_data(request)
            elif request.source_type == DataSourceType.JSON_FILE:
                data = self._load_json_data(request)
            elif request.source_type == DataSourceType.STREAM:
                data = self._load_stream_data(request)
            else:
                raise ValueError(f"Unsupported source type: {request.source_type}")
            
            # Apply transformations
            if request.transformations:
                data = self._apply_transformations(data, request.transformations)
            
            # Apply filters
            if request.filters:
                data = self._apply_filters(data, request.filters)
            
            # Validate loaded data
            validation_result = self._validate_loaded_data(data, request)
            
            # Calculate loading time
            loading_time = (datetime.now() - start_time).total_seconds()
            
            # Create result
            result = DataLoadResult(
                request_id=request_id,
                status=LoadingStatus.COMPLETED,
                data=data,
                records_loaded=len(data),
                loading_time=loading_time,
                data_quality=validation_result,
                errors=[],
                warnings=validation_result.validation_errors if validation_result else [],
                metadata=request.metadata
            )
            
            # Store result
            self.completed_requests[request_id] = result
            
            # Update statistics
            self.load_statistics['successful_loads'] += 1
            self.load_statistics['total_records_loaded'] += len(data)
            self._update_average_load_time(loading_time)
            
            # Publish success event
            self.event_bus.publish(Event(
                EventType.DATA_LOAD_COMPLETED,
                {
                    'request_id': request_id,
                    'records_loaded': len(data),
                    'loading_time': loading_time,
                    'data_quality_score': validation_result.data_completeness if validation_result else 0,
                    'warnings': validation_result.validation_errors if validation_result else []
                },
                source='DataLoader'
            ))
            
            self.logger.info(f"Successfully loaded {len(data)} records for request {request_id}")
            
        except Exception as e:
            # Handle loading failure
            loading_time = (datetime.now() - start_time).total_seconds()
            
            result = DataLoadResult(
                request_id=request_id,
                status=LoadingStatus.FAILED,
                data=None,
                records_loaded=0,
                loading_time=loading_time,
                errors=[str(e)],
                metadata=request.metadata
            )
            
            self.completed_requests[request_id] = result
            self.load_statistics['failed_loads'] += 1
            
            # Publish failure event
            self.event_bus.publish(Event(
                EventType.ERROR_OCCURRED,
                {
                    'request_id': request_id,
                    'operation': 'data_load',
                    'error': str(e),
                    'loading_time': loading_time
                },
                source='DataLoader'
            ))
            
            self.logger.error(f"Failed to load data for request {request_id}: {e}")
            
        finally:
            # Cleanup
            if request_id in self.active_requests:
                del self.active_requests[request_id]
            if request_id in self.loading_threads:
                del self.loading_threads[request_id]
    
    def _load_csv_data(self, request: DataLoadRequest) -> pd.DataFrame:
        """
        Load data from CSV file
        REQ-TECH-005: Automated data quality assessment
        """
        try:
            # Determine file path
            file_path = Path(request.source_path)
            if not file_path.exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")
            
            # Load with pandas
            load_params = {
                'filepath_or_buffer': file_path,
                'low_memory': False,
                'parse_dates': ['processedtimegmt'] if 'processedtimegmt' in request.target_columns else False
            }
            
            # Add chunk processing for large files
            if request.chunk_size and request.chunk_size > 0:
                chunks = []
                for chunk in pd.read_csv(chunksize=request.chunk_size, **load_params):
                    chunks.append(chunk)
                    if len(chunks) * request.chunk_size >= 10000:  # Memory management
                        break
                data = pd.concat(chunks, ignore_index=True)
            else:
                data = pd.read_csv(**load_params)
            
            # Handle column mapping
            data = self._map_columns(data, request.target_columns)
            
            # Select required columns
            available_columns = [col for col in request.target_columns if col in data.columns]
            if request.optional_columns:
                available_columns.extend([col for col in request.optional_columns if col in data.columns])
            
            data = data[available_columns]
            
            self.logger.info(f"Loaded {len(data)} records from CSV: {file_path}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading CSV data: {e}")
            raise
    
    def _load_json_data(self, request: DataLoadRequest) -> pd.DataFrame:
        """Load data from JSON file"""
        try:
            file_path = Path(request.source_path)
            if not file_path.exists():
                raise FileNotFoundError(f"JSON file not found: {file_path}")
            
            # Load JSON data
            with open(file_path, 'r') as f:
                json_data = json.load(f)
            
            # Convert to DataFrame
            if isinstance(json_data, list):
                data = pd.DataFrame(json_data)
            elif isinstance(json_data, dict):
                # Handle nested JSON structures
                data = pd.json_normalize(json_data)
            else:
                raise ValueError("Unsupported JSON structure")
            
            # Handle column mapping
            data = self._map_columns(data, request.target_columns)
            
            self.logger.info(f"Loaded {len(data)} records from JSON: {file_path}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading JSON data: {e}")
            raise
    
    def _load_stream_data(self, request: DataLoadRequest) -> pd.DataFrame:
        """
        Load data from streaming source
        REQ-TECH-002: Stream processing capability
        """
        try:
            # Simulate streaming data loading
            # In real implementation, this would connect to actual data streams
            data_buffer = []
            
            # Mock streaming data generation for testing
            for i in range(request.chunk_size or 100):
                record = {
                    'callsign': f'Unit_{100 + i % 4}',
                    'processedtimegmt': datetime.now() - timedelta(seconds=i),
                    'latitude': 40.0 + (i % 10) * 0.001,
                    'longitude': -74.0 + (i % 10) * 0.001,
                    'temp': 20 + (i % 20),
                    'battery': 100 - (i % 50),
                    'falldetected': 'Yes' if i % 20 == 0 else 'No',
                    'casualtystate': 'GOOD' if i % 30 != 0 else 'KILLED',
                    'rssi': 20 + (i % 30),
                    'mcs': 5 + (i % 3),
                    'nexthop': f'Router_{i % 3}',
                    'steps': 100 + (i % 300),
                    'posture': 'Standing' if i % 3 == 0 else 'Prone',
                    'squad': f'Squad_{i % 2}'
                }
                data_buffer.append(record)
            
            data = pd.DataFrame(data_buffer)
            
            self.logger.info(f"Loaded {len(data)} records from stream")
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading stream data: {e}")
            raise
    
    def _map_columns(self, data: pd.DataFrame, target_columns: List[str]) -> pd.DataFrame:
        """Map column names using known mappings"""
        for target_col in target_columns:
            if target_col in data.columns:
                continue
            
            # Look for alternative column names
            for mapping_key, alternatives in self.column_mappings.get('soldier_data', {}).items():
                if mapping_key == target_col:
                    for alt_name in alternatives:
                        if alt_name in data.columns:
                            data = data.rename(columns={alt_name: target_col})
                            self.logger.debug(f"Mapped column '{alt_name}' to '{target_col}'")
                            break
                    break
        
        return data
    
    def _apply_transformations(self, data: pd.DataFrame, transformations: Dict[str, Any]) -> pd.DataFrame:
        """Apply data transformations"""
        for column, transform_config in transformations.items():
            if column not in data.columns:
                continue
            
            transform_type = transform_config.get('type')
            
            if transform_type == 'normalize':
                # Normalize numeric data
                if data[column].dtype in ['int64', 'float64']:
                    data[column] = (data[column] - data[column].mean()) / data[column].std()
            
            elif transform_type == 'fill_missing':
                # Fill missing values
                fill_value = transform_config.get('value', 0)
                data[column] = data[column].fillna(fill_value)
            
            elif transform_type == 'convert_type':
                # Convert data type
                target_type = transform_config.get('target_type')
                if target_type == 'datetime':
                    data[column] = pd.to_datetime(data[column], errors='coerce')
                elif target_type == 'numeric':
                    data[column] = pd.to_numeric(data[column], errors='coerce')
            
            elif transform_type == 'clean_text':
                # Clean text data
                data[column] = data[column].astype(str).str.strip().str.upper()
        
        return data
    
    def _apply_filters(self, data: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply data filters"""
        for column, filter_config in filters.items():
            if column not in data.columns:
                continue
            
            filter_type = filter_config.get('type')
            
            if filter_type == 'range':
                min_val = filter_config.get('min')
                max_val = filter_config.get('max')
                if min_val is not None:
                    data = data[data[column] >= min_val]
                if max_val is not None:
                    data = data[data[column] <= max_val]
            
            elif filter_type == 'values':
                allowed_values = filter_config.get('values', [])
                data = data[data[column].isin(allowed_values)]
            
            elif filter_type == 'not_null':
                data = data[data[column].notna()]
        
        return data
    
    def _validate_loaded_data(self, data: pd.DataFrame, request: DataLoadRequest) -> DataQualityMetrics:
        """Validate loaded data quality"""
        metrics = DataQualityMetrics()
        metrics.total_records = len(data)
        
        # Check required columns
        missing_data = {}
        for col in request.target_columns:
            if col in data.columns:
                missing_count = data[col].isna().sum()
                missing_data[col] = (missing_count / len(data)) * 100
            else:
                missing_data[col] = 100.0
                metrics.validation_errors.append(f"Required column '{col}' is missing")
        
        metrics.missing_data_percentage = missing_data
        metrics.data_completeness = 100 - np.mean(list(missing_data.values()))
        
        # Validate data types and ranges
        self._validate_data_types(data, metrics)
        self._validate_data_ranges(data, metrics)
        
        return metrics
    
    def _validate_data_types(self, data: pd.DataFrame, metrics: DataQualityMetrics):
        """Validate data types for known columns"""
        type_validations = {
            'callsign': str,
            'processedtimegmt': 'datetime',
            'latitude': float,
            'longitude': float,
            'temp': float,
            'battery': float,
            'rssi': float,
            'mcs': int,
            'steps': int
        }
        
        for column, expected_type in type_validations.items():
            if column in data.columns:
                if expected_type == 'datetime':
                    try:
                        pd.to_datetime(data[column], errors='raise')
                    except:
                        metrics.validation_errors.append(f"Column '{column}' contains invalid datetime values")
                elif expected_type in [int, float]:
                    non_numeric = data[column].apply(lambda x: not isinstance(x, (int, float, type(None))))
                    if non_numeric.any():
                        metrics.validation_errors.append(f"Column '{column}' contains non-numeric values")
    
    def _validate_data_ranges(self, data: pd.DataFrame, metrics: DataQualityMetrics):
        """Validate data ranges for known columns"""
        range_validations = {
            'latitude': (-90, 90),
            'longitude': (-180, 180),
            'temp': (-50, 70),
            'battery': (0, 101),
            'rssi': (-120, 100),
            'mcs': (0, 11),
            'steps': (0, 10000)
        }
        
        for column, (min_val, max_val) in range_validations.items():
            if column in data.columns:
                out_of_range = data[column].apply(lambda x: x < min_val or x > max_val if pd.notna(x) else False)
                if out_of_range.any():
                    count = out_of_range.sum()
                    metrics.validation_errors.append(f"Column '{column}' has {count} values outside valid range ({min_val}, {max_val})")
    
    def _update_average_load_time(self, load_time: float):
        """Update average load time statistic"""
        total_loads = self.load_statistics['successful_loads']
        if total_loads == 1:
            self.load_statistics['average_load_time'] = load_time
        else:
            current_avg = self.load_statistics['average_load_time']
            self.load_statistics['average_load_time'] = (current_avg * (total_loads - 1) + load_time) / total_loads
    
    def get_load_status(self, request_id: str) -> Optional[Union[LoadingStatus, DataLoadResult]]:
        """Get status of a loading request"""
        if request_id in self.active_requests:
            return LoadingStatus.LOADING
        elif request_id in self.completed_requests:
            return self.completed_requests[request_id]
        else:
            return None
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """Get loading performance statistics"""
        return {
            **self.load_statistics,
            'active_requests': len(self.active_requests),
            'completed_requests': len(self.completed_requests),
            'current_timestamp': datetime.now().isoformat()
        }
    
    def cancel_load_request(self, request_id: str) -> bool:
        """Cancel an active loading request"""
        if request_id in self.active_requests:
            # Mark as cancelled
            result = DataLoadResult(
                request_id=request_id,
                status=LoadingStatus.CANCELLED,
                data=None,
                records_loaded=0,
                loading_time=0.0,
                errors=["Request cancelled by user"]
            )
            
            self.completed_requests[request_id] = result
            del self.active_requests[request_id]
            
            # Publish cancellation event
            self.event_bus.publish(Event(
                EventType.DATA_LOAD_CANCELLED,
                {'request_id': request_id},
                source='DataLoader'
            ))
            
            return True
        return False
    
    def handle_load_request(self, event: Event):
        """Handle data load request events"""
        request_data = event.data
        
        try:
            request = DataLoadRequest(
                request_id=request_data['request_id'],
                source_type=DataSourceType(request_data['source_type']),
                source_path=request_data['source_path'],
                target_columns=request_data['target_columns'],
                optional_columns=request_data.get('optional_columns', []),
                filters=request_data.get('filters'),
                transformations=request_data.get('transformations'),
                chunk_size=request_data.get('chunk_size', self.chunk_size),
                priority=request_data.get('priority', 1),
                timeout=request_data.get('timeout', self.timeout),
                metadata=request_data.get('metadata', {})
            )
            
            self.load_data(request)
            
        except Exception as e:
            self.logger.error(f"Error handling load request: {e}")
            self.event_bus.publish(Event(
                EventType.ERROR_OCCURRED,
                {
                    'operation': 'handle_load_request',
                    'error': str(e),
                    'request_id': request_data.get('request_id')
                },
                source='DataLoader'
            ))
    
    def handle_load_cancellation(self, event: Event):
        """Handle load cancellation events"""
        request_id = event.data.get('request_id')
        if request_id:
            self.cancel_load_request(request_id)
    
    def handle_config_change(self, event: Event):
        """Handle configuration changes"""
        config_data = event.data
        
        if 'max_concurrent_loads' in config_data:
            self.max_concurrent_loads = config_data['max_concurrent_loads']
        
        if 'default_chunk_size' in config_data:
            self.chunk_size = config_data['default_chunk_size']
        
        if 'load_timeout' in config_data:
            self.timeout = config_data['load_timeout']
        
        self.logger.info("DataLoader configuration updated")
    
    def cleanup(self):
        """Cleanup resources"""
        # Cancel all active requests
        for request_id in list(self.active_requests.keys()):
            self.cancel_load_request(request_id)
        
        # Wait for threads to complete
        for thread in self.loading_threads.values():
            if thread.is_alive():
                thread.join(timeout=5)
        
        self.logger.info("DataLoader cleanup completed")


# Factory functions for common use cases
def create_csv_load_request(
    request_id: str,
    file_path: str,
    analysis_domain: AnalysisDomain,
    optional_columns: List[str] = None,
    filters: Dict[str, Any] = None
) -> DataLoadRequest:
    """Create a CSV load request for specific analysis domain"""
    
    # Define required columns by analysis domain
    domain_columns = {
        AnalysisDomain.SOLDIER_SAFETY: ['callsign', 'falldetected', 'casualtystate', 'processedtimegmt'],
        AnalysisDomain.NETWORK_PERFORMANCE: ['callsign', 'processedtimegmt', 'rssi', 'mcs', 'nexthop'],
        AnalysisDomain.SOLDIER_ACTIVITY: ['callsign', 'processedtimegmt', 'steps', 'posture'],
        AnalysisDomain.EQUIPMENT_MANAGEMENT: ['callsign', 'processedtimegmt', 'battery']
    }
    
    target_columns = domain_columns.get(analysis_domain, ['callsign', 'processedtimegmt'])
    
    # Add common optional columns
    if optional_columns is None:
        optional_columns = ['latitude', 'longitude', 'temp', 'squad']
    
    return DataLoadRequest(
        request_id=request_id,
        source_type=DataSourceType.CSV_FILE,
        source_path=file_path,
        target_columns=target_columns,
        optional_columns=optional_columns,
        filters=filters,
        metadata={'analysis_domain': analysis_domain.value}
    )


def create_stream_load_request(
    request_id: str,
    stream_config: Dict[str, Any],
    chunk_size: int = 100
) -> DataLoadRequest:
    """Create a streaming data load request"""
    
    return DataLoadRequest(
        request_id=request_id,
        source_type=DataSourceType.STREAM,
        source_path=stream_config.get('endpoint', 'stream'),
        target_columns=['callsign', 'processedtimegmt'],
        optional_columns=['latitude', 'longitude', 'temp', 'battery', 'rssi', 'mcs'],
        chunk_size=chunk_size,
        metadata={'stream_config': stream_config}
    )