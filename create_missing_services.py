#!/usr/bin/env python3
"""
Create missing service modules for Enhanced Soldier Report System
"""

from pathlib import Path

def create_statistics_calculator():
    """Create the StatisticsCalculator service"""
    content = '''"""Statistics calculation service for soldier data analysis"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Union
from models.analysis_results import StatisticalSummary

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
'''
    
    file_path = Path("src/services/statistics_calculator.py")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {file_path}")

def create_data_loader():
    """Create the DataLoader service"""
    content = '''"""Data loading service for soldier data files"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any

from core.event_bus import EventBus, Event
from core.events import EventType, DataLoadedEvent, ErrorEvent
from models.soldier_data import SoldierDataset, SoldierDataRecord, DatasetMetadata, create_empty_dataset

class DataLoader:
    """Service for loading and processing soldier data files"""
    
    def __init__(self, event_bus: EventBus, settings=None):
        self.event_bus = event_bus
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.current_dataset: Optional[SoldierDataset] = None
        
        # Subscribe to file selection events
        self.event_bus.subscribe(
            EventType.FILE_SELECTED.value,
            self._handle_file_selected
        )
    
    def _handle_file_selected(self, event: Event):
        """Handle file selection event"""
        file_path = event.data.get('file_path')
        if file_path:
            self.load_file(Path(file_path))
    
    def load_file(self, file_path: Path) -> Optional[SoldierDataset]:
        """Load soldier data from file"""
        try:
            self.logger.info(f"Loading data from: {file_path}")
            
            # Validate file
            if not file_path.exists():
                raise ValueError(f"File does not exist: {file_path}")
            
            # Determine file type and load accordingly
            file_ext = file_path.suffix.lower()
            
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # Create dataset metadata
            metadata = DatasetMetadata(
                file_path=file_path,
                original_filename=file_path.name,
                file_size_bytes=file_path.stat().st_size,
                original_column_names=list(df.columns),
                total_raw_rows=len(df)
            )
            
            # Create dataset
            self.current_dataset = SoldierDataset(
                raw_dataframe=df,
                metadata=metadata
            )
            
            # Publish success event
            self.event_bus.publish(DataLoadedEvent(
                dataset=self.current_dataset,
                file_path=str(file_path),
                source="DataLoader"
            ))
            
            self.logger.info(f"Successfully loaded {len(df)} records from {len(df.columns)} columns")
            return self.current_dataset
            
        except Exception as e:
            self.logger.error(f"Failed to load file {file_path}: {e}")
            self.event_bus.publish(ErrorEvent(
                error=e,
                context=f"Loading file: {file_path}",
                source="DataLoader"
            ))
            return None
    
    def get_current_dataset(self) -> Optional[SoldierDataset]:
        """Get the currently loaded dataset"""
        return self.current_dataset
    
    def get_soldier_callsigns(self) -> List[str]:
        """Get list of soldier callsigns from current dataset"""
        if self.current_dataset and not self.current_dataset.raw_dataframe.empty:
            if 'Callsign' in self.current_dataset.raw_dataframe.columns:
                return self.current_dataset.raw_dataframe['Callsign'].unique().tolist()
        return []
    
    def get_data_preview(self, num_rows: int = 5) -> Dict[str, Any]:
        """Get a preview of the loaded data"""
        if not self.current_dataset:
            return {}
        
        df = self.current_dataset.raw_dataframe
        return {
            'columns': list(df.columns),
            'total_rows': len(df),
            'sample_data': df.head(num_rows).to_dict('records'),
            'data_types': df.dtypes.to_dict()
        }
'''
    
    file_path = Path("src/services/data_loader.py")
    if not file_path.exists():  # Only create if it doesn't exist
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created: {file_path}")
    else:
        print(f"Already exists: {file_path}")

def create_analysis_engine():
    """Create the AnalysisEngine service"""
    content = '''"""Analysis engine for soldier performance data"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.event_bus import EventBus, Event
from core.events import EventType
from models.soldier_data import SoldierDataset, SoldierDataRecord
from models.analysis_results import (
    SoldierAnalysisResult, BatchAnalysisResult, AnalysisStatus,
    HeartRateAnalysis, PhysicalPerformanceAnalysis, EquipmentAnalysis,
    SafetyAnalysis, PerformanceScore, CombatAnalysis, StatisticalSummary
)
from services.statistics_calculator import StatisticsCalculator

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
'''
    
    file_path = Path("src/services/analysis_engine.py")
    if file_path.exists():
        # Backup and replace
        backup_path = file_path.with_suffix('.py.backup')
        file_path.rename(backup_path)
        print(f"Backed up existing file to: {backup_path}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {file_path}")

def create_report_generator():
    """Create the ReportGenerator service"""
    content = '''"""Report generation service"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from core.event_bus import EventBus
from models.analysis_results import SoldierAnalysisResult, BatchAnalysisResult
from models.report_config import ReportConfig, create_default_soldier_report_config

class ReportGenerator:
    """Service for generating soldier reports"""
    
    def __init__(self, event_bus: EventBus, settings=None):
        self.event_bus = event_bus
        self.settings = settings
        self.logger = logging.getLogger(__name__)
    
    def generate_soldier_report(self, 
                              analysis_result: SoldierAnalysisResult,
                              config: ReportConfig = None) -> Path:
        """Generate a report for an individual soldier"""
        if config is None:
            config = create_default_soldier_report_config()
        
        self.logger.info(f"Generating report for {analysis_result.callsign}")
        
        # Create output directory
        output_dir = config.output_config.output_directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{analysis_result.callsign}_report_{timestamp}.html"
        output_path = output_dir / filename
        
        # Generate HTML content
        html_content = self._generate_html_report(analysis_result, config)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Report saved to: {output_path}")
        return output_path
    
    def _generate_html_report(self, 
                            analysis_result: SoldierAnalysisResult,
                            config: ReportConfig) -> str:
        """Generate HTML content for the report"""
        
        # Basic HTML template
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Soldier Report - {analysis_result.callsign}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f8f9fa; }}
        .status-good {{ color: #27ae60; }}
        .status-warning {{ color: #f39c12; }}
        .status-critical {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎖️ Enhanced Individual Soldier Report</h1>
        <h2>{analysis_result.callsign}</h2>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h3>Analysis Summary</h3>
        <div class="metric">
            <strong>Analysis Status:</strong> {analysis_result.analysis_status.value}
        </div>
        <div class="metric">
            <strong>Total Records:</strong> {analysis_result.total_records}
        </div>
        <div class="metric">
            <strong>Overall Risk Level:</strong> 
            <span class="status-{analysis_result.overall_risk_level.value}">
                {analysis_result.overall_risk_level.value.upper()}
            </span>
        </div>
    </div>
        """
        
        # Add heart rate analysis if available
        if analysis_result.heart_rate_analysis:
            hr = analysis_result.heart_rate_analysis
            html += f"""
    <div class="section">
        <h3>Heart Rate Analysis</h3>
        <div class="metric">
            <strong>Average HR:</strong> {hr.statistics.mean:.1f} BPM
        </div>
        <div class="metric">
            <strong>Max HR:</strong> {hr.statistics.max_value:.1f} BPM
        </div>
        <div class="metric">
            <strong>Min HR:</strong> {hr.statistics.min_value:.1f} BPM
        </div>
        <div class="metric">
            <strong>Total Readings:</strong> {hr.statistics.count}
        </div>
    </div>
            """
        
        # Add physical performance if available
        if analysis_result.physical_performance:
            pp = analysis_result.physical_performance
            html += f"""
    <div class="section">
        <h3>Physical Performance</h3>
        <div class="metric">
            <strong>Total Steps:</strong> {pp.total_steps:,}
        </div>
        <div class="metric">
            <strong>Activity Level:</strong> {pp.activity_level}
        </div>
    </div>
            """
        
        # Add performance score if available
        if analysis_result.performance_score:
            ps = analysis_result.performance_score
            html += f"""
    <div class="section">
        <h3>Performance Score</h3>
        <div class="metric">
            <strong>Final Score:</strong> {ps.final_score:.1f}/100
        </div>
        <div class="metric">
            <strong>Rating:</strong> {ps.performance_rating.value}
        </div>
        <div class="metric">
            <strong>Status:</strong> {ps.performance_status}
        </div>
    </div>
            """
        
        html += """
    <div class="section">
        <h3>Report Footer</h3>
        <p><small>Generated by Enhanced Soldier Report System v2.0</small></p>
        <p><small>Classification: FOR OFFICIAL USE ONLY</small></p>
    </div>
</body>
</html>
        """
        
        return html
'''
    
    file_path = Path("src/reporting/report_generator.py")
    if file_path.exists():
        # Backup and replace
        backup_path = file_path.with_suffix('.py.backup')
        file_path.rename(backup_path)
        print(f"Backed up existing file to: {backup_path}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {file_path}")

def main():
    """Create all missing service modules"""
    print("Creating missing service modules...")
    
    # Ensure services directory exists
    services_dir = Path("src/services")
    services_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py if it doesn't exist
    init_file = services_dir / "__init__.py"
    if not init_file.exists():
        init_file.touch()
    
    # Create the missing modules
    create_statistics_calculator()
    create_data_loader()
    create_analysis_engine()
    create_report_generator()
    
    print("\\n✅ All service modules created!")
    print("\\nNow try running:")
    print("python -m src.main")

if __name__ == "__main__":
    main()
