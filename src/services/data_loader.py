# File: src/services/data_loader.py
"""Data loading and validation service"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from src.core.event_bus import EventBus, Event
from src.core.events import EventType, DataLoadedEvent, ErrorEvent, StatusUpdateEvent
from src.core.exceptions import DataLoadError, DataValidationError
from src.models.soldier_data import SoldierDataset, DatasetMetadata
from src.config.settings import Settings


class DataLoader:
    """Service for loading and validating soldier data from CSV files"""
    
    def __init__(self, event_bus: EventBus, settings: Settings):
        self.event_bus = event_bus
        self.settings = settings
        self.column_mapping = settings.column_mapping
        self._logger = logging.getLogger(__name__)
        
        # Subscribe to file selection events
        self.event_bus.subscribe(
            EventType.FILE_SELECTED.value, 
            self._handle_file_selected
        )
    
    def _handle_file_selected(self, event: Event) -> None:
        """Handle file selection event"""
        file_path = event.data['file_path']
        
        try:
            self.event_bus.publish(StatusUpdateEvent(
                f"Loading data from {Path(file_path).name}...",
                source="DataLoader"
            ))
            
            dataset = self.load_data(file_path)
            
            self.event_bus.publish(DataLoadedEvent(
                dataset=dataset,
                file_path=file_path,
                source="DataLoader"
            ))
            
            self.event_bus.publish(StatusUpdateEvent(
                f"Successfully loaded {len(dataset.raw_dataframe):,} records for {dataset.total_soldiers} soldiers",
                source="DataLoader"
            ))
            
        except Exception as e:
            self._logger.error(f"Failed to load data from {file_path}: {e}")
            self.event_bus.publish(ErrorEvent(
                error=e,
                context=f"Loading data from {file_path}",
                source="DataLoader"
            ))
    
    def load_data(self, file_path: str) -> SoldierDataset:
        """
        Load and validate CSV data file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            SoldierDataset with loaded and validated data
            
        Raises:
            DataLoadError: If file cannot be loaded
            DataValidationError: If data validation fails
        """
        try:
            # Load CSV file
            self._logger.info(f"Loading CSV file: {file_path}")
            data = pd.read_csv(file_path)
            
            # Apply column mapping
            mapped_data, mapping_applied = self._apply_column_mapping(data)
            
            # Validate required columns
            self._validate_required_columns(mapped_data)
            
            # Clean and transform data
            cleaned_data = self._clean_data(mapped_data)
            
            # Create metadata
            file_path_obj = Path(file_path)
            metadata = DatasetMetadata(
                file_path=file_path_obj,
                original_filename=file_path_obj.name,
                file_size_bytes=file_path_obj.stat().st_size if file_path_obj.exists() else 0,
                column_mappings_applied=mapping_applied,
                original_column_names=list(data.columns),
                standardized_column_names=list(cleaned_data.columns),
                total_raw_rows=len(data),
                total_processed_rows=len(cleaned_data)
            )
            
            # Create dataset with correct constructor arguments
            dataset = SoldierDataset(
                raw_dataframe=cleaned_data,
                metadata=metadata
            )
            
            # Validate data quality
            quality_issues = self._validate_data_quality(dataset)
            if hasattr(dataset, 'data_quality_issues'):
                dataset.data_quality_issues = quality_issues
            
            if quality_issues:
                self._logger.warning(f"Data quality issues found: {quality_issues}")
            
            return dataset
            
        except FileNotFoundError:
            raise DataLoadError(f"File not found: {file_path}")
        except pd.errors.EmptyDataError:
            raise DataLoadError(f"File is empty: {file_path}")
        except pd.errors.ParserError as e:
            raise DataLoadError(f"Failed to parse CSV file: {e}")
        except Exception as e:
            raise DataLoadError(f"Unexpected error loading data: {e}")
    
    def _apply_column_mapping(self, data: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, str]]:
        """Apply column mapping to standardize column names"""
        mapping_applied = {}
        
        for original_col, standard_col in self.column_mapping.items():
            if original_col in data.columns:
                data = data.rename(columns={original_col: standard_col})
                mapping_applied[original_col] = standard_col
        
        self._logger.info(f"Applied column mapping: {mapping_applied}")
        return data, mapping_applied
    
    def _validate_required_columns(self, data: pd.DataFrame) -> None:
        """Validate that required columns are present"""
        required_columns = ['Callsign']  # Minimum required columns
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            raise DataValidationError(f"Missing required columns: {missing_columns}")
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and transform data"""
        cleaned_data = data.copy()
        
        # Convert Fall_Detection to numeric (No=0, Yes=1)
        if 'Fall_Detection' in cleaned_data.columns:
            cleaned_data['Fall_Detection'] = cleaned_data['Fall_Detection'].map({
                'No': 0, 'Yes': 1
            }).fillna(0)
        
        # Convert timestamps if possible
        if 'Time_Step' in cleaned_data.columns:
            try:
                cleaned_data['Time_Step'] = pd.to_datetime(cleaned_data['Time_Step'])
                start_time = cleaned_data['Time_Step'].min()
                cleaned_data['Time_Step_Numeric'] = (
                    cleaned_data['Time_Step'] - start_time
                ).dt.total_seconds() / 60
            except Exception:
                self._logger.warning("Could not convert time format, using original values")
        
        # Clean numeric columns
        numeric_columns = ['Heart_Rate', 'Step_Count', 'Temperature', 'Battery', 'RSSI']
        for col in numeric_columns:
            if col in cleaned_data.columns:
                cleaned_data[col] = pd.to_numeric(cleaned_data[col], errors='coerce')
        
        return cleaned_data
    
    def _validate_data_quality(self, dataset: SoldierDataset) -> List[str]:
        """Validate data quality and return list of issues"""
        issues = []
        data = dataset.raw_dataframe
        
        # Check for empty dataset
        if len(data) == 0:
            issues.append("Dataset is empty")
            return issues
        
        # Check callsign coverage
        if 'Callsign' in data.columns:
            null_callsigns = data['Callsign'].isnull().sum()
            if null_callsigns > 0:
                issues.append(f"{null_callsigns} records missing callsign")
        
        # Check heart rate data quality
        if 'Heart_Rate' in data.columns:
            hr_data = data['Heart_Rate'].dropna()
            if len(hr_data) == 0:
                issues.append("No valid heart rate data")
            else:
                # Check for unrealistic values
                extreme_hr = len(hr_data[(hr_data < 30) | (hr_data > 250)])
                if extreme_hr > 0:
                    issues.append(f"{extreme_hr} extreme heart rate values detected")
        
        # Check for duplicate records
        if 'Callsign' in data.columns and 'Time_Step' in data.columns:
            duplicates = data.duplicated(subset=['Callsign', 'Time_Step']).sum()
            if duplicates > 0:
                issues.append(f"{duplicates} duplicate time records detected")
        
        return issues