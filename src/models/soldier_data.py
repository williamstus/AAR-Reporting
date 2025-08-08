"""
Soldier Data Models
Defines data structures for soldier information and datasets.
Part of the Enhanced Soldier Report System refactoring.

This module follows the refactored architecture principles:
- Separation of concerns
- Strong typing with enums
- Immutable data structures where appropriate
- Clear validation methods
- No business logic mixed with data models
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path


class CasualtyStatus(Enum):
    """Standardized casualty status values"""
    GOOD = "GOOD"
    WOUNDED = "WOUNDED"
    KILL = "KILL"
    KIA = "KIA"
    UNKNOWN = "UNKNOWN"


class PostureType(Enum):
    """Standardized posture types"""
    STANDING = "standing"
    PRONE = "prone"
    KNEELING = "kneeling"
    CROUCHING = "crouching"
    MOVING = "moving"
    UNKNOWN = "unknown"


class CommunicationQuality(Enum):
    """Communication quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"


class DataQualityLevel(Enum):
    """Data quality assessment levels"""
    EXCELLENT = "excellent"    # >95% complete, no major issues
    GOOD = "good"             # >85% complete, minor issues
    FAIR = "fair"             # >70% complete, some issues
    POOR = "poor"             # <70% complete, major issues


@dataclass(frozen=True)
class SoldierIdentity:
    """Immutable soldier identification information"""
    callsign: str
    player_id: Optional[str] = None
    squad: Optional[str] = None
    platoon: Optional[str] = None
    
    def __post_init__(self):
        if not self.callsign:
            raise ValueError("Callsign is required")


@dataclass
class PhysicalMetrics:
    """Physical performance and activity metrics"""
    # Step count metrics
    total_steps: int = 0
    avg_steps_per_reading: float = 0.0
    max_steps_in_reading: int = 0
    min_steps_in_reading: int = 0
    step_count_readings: int = 0
    
    # Movement and posture
    posture_distribution: Dict[PostureType, int] = field(default_factory=dict)
    dominant_posture: PostureType = PostureType.UNKNOWN
    posture_changes: int = 0
    posture_readings: int = 0
    
    # Fall detection
    fall_incidents: int = 0
    fall_detection_readings: int = 0
    
    # Mission duration and activity level
    mission_duration_minutes: Optional[float] = None
    activity_level: str = "unknown"  # Will be calculated: inactive, low, moderate, excellent
    
    @property
    def posture_stability_rating(self) -> str:
        """Calculate posture stability rating"""
        if self.posture_readings == 0:
            return "unknown"
        
        change_rate = self.posture_changes / self.posture_readings
        if change_rate < 0.1:
            return "excellent"
        elif change_rate < 0.2:
            return "good"
        else:
            return "fair"
    
    @property
    def steps_per_minute(self) -> Optional[float]:
        """Calculate average steps per minute if mission duration available"""
        if self.mission_duration_minutes and self.mission_duration_minutes > 0:
            return self.total_steps / self.mission_duration_minutes
        return None


@dataclass
class PhysiologicalMetrics:
    """Physiological monitoring metrics"""
    # Heart rate statistics
    min_heart_rate: float = 0.0
    avg_heart_rate: float = 0.0
    max_heart_rate: float = 0.0
    heart_rate_readings: int = 0
    
    # Heart rate zones (count of readings in each zone)
    hr_zones: Dict[str, int] = field(default_factory=lambda: {
        'rest': 0,        # < 60 BPM
        'normal': 0,      # 60-100 BPM
        'elevated': 0,    # 100-150 BPM
        'high': 0,        # 150-180 BPM
        'extreme': 0,     # 180-190 BPM
        'critical': 0     # > 190 BPM
    })
    
    # Abnormal readings
    abnormal_hr_low_count: int = 0   # < 60 BPM
    abnormal_hr_high_count: int = 0  # > 190 BPM
    
    # Temperature metrics
    min_temperature: float = 0.0
    avg_temperature: float = 0.0
    max_temperature: float = 0.0
    temperature_readings: int = 0
    
    # Temperature stress incidents
    heat_stress_incidents: int = 0    # > 104°F
    cold_stress_incidents: int = 0    # < 95°F
    
    @property
    def has_abnormal_heart_rate(self) -> bool:
        """Check if any abnormal heart rate readings exist"""
        return self.abnormal_hr_low_count > 0 or self.abnormal_hr_high_count > 0
    
    @property
    def heart_rate_data_quality(self) -> DataQualityLevel:
        """Assess heart rate data quality"""
        if self.heart_rate_readings == 0:
            return DataQualityLevel.POOR
        
        # Simple quality assessment based on reading count
        # This could be enhanced with additional criteria
        if self.heart_rate_readings >= 100:
            return DataQualityLevel.EXCELLENT
        elif self.heart_rate_readings >= 50:
            return DataQualityLevel.GOOD
        elif self.heart_rate_readings >= 20:
            return DataQualityLevel.FAIR
        else:
            return DataQualityLevel.POOR


@dataclass
class EquipmentMetrics:
    """Equipment status and communication metrics"""
    # Battery metrics
    min_battery_level: float = 0.0
    avg_battery_level: float = 0.0
    max_battery_level: float = 0.0
    battery_readings: int = 0
    
    # Battery incidents
    low_battery_incidents: int = 0      # < 20%
    critical_battery_incidents: int = 0  # < 10%
    
    # Communication metrics
    avg_rssi: float = 0.0
    min_rssi: float = 0.0
    max_rssi: float = 0.0
    rssi_readings: int = 0
    communication_quality: CommunicationQuality = CommunicationQuality.UNKNOWN
    
    # Equipment identification
    primary_weapon: Optional[str] = None
    equipment_failures: List[str] = field(default_factory=list)
    
    @property
    def battery_risk_level(self) -> str:
        """Assess battery risk level"""
        if self.critical_battery_incidents > 0:
            return "CRITICAL"
        elif self.low_battery_incidents > 5:
            return "HIGH"
        elif self.avg_battery_level < 30:
            return "MODERATE"
        else:
            return "LOW"


@dataclass
class CombatMetrics:
    """Combat-related metrics and events"""
    final_casualty_status: CasualtyStatus = CasualtyStatus.UNKNOWN
    casualty_status_changes: int = 0
    
    # Combat engagement data
    total_combat_engagements: int = 0
    unique_shooters_engaged: int = 0
    shots_taken: int = 0
    hits_received: int = 0
    
    # Weapon and munition data
    primary_weapon: Optional[str] = None
    munitions_used: List[str] = field(default_factory=list)
    hit_zones: List[str] = field(default_factory=list)
    
    # Combat effectiveness (derived metrics)
    survival_rate: bool = True  # True if not KIA/KILL
    engagement_intensity: str = "low"  # low, moderate, high
    
    def __post_init__(self):
        """Calculate derived combat metrics"""
        self.survival_rate = self.final_casualty_status not in [CasualtyStatus.KILL, CasualtyStatus.KIA]
        
        # Simple engagement intensity calculation
        if self.total_combat_engagements >= 10:
            self.engagement_intensity = "high"
        elif self.total_combat_engagements >= 5:
            self.engagement_intensity = "moderate"
        else:
            self.engagement_intensity = "low"


@dataclass
class DataQualityMetrics:
    """Data quality assessment for soldier dataset"""
    total_expected_readings: int = 0
    total_actual_readings: int = 0
    missing_data_count: int = 0
    null_percentage: float = 0.0
    
    # Per-column quality
    column_completeness: Dict[str, float] = field(default_factory=dict)
    column_quality_issues: Dict[str, List[str]] = field(default_factory=dict)
    
    # Time coverage
    time_coverage_start: Optional[datetime] = None
    time_coverage_end: Optional[datetime] = None
    time_gaps: List[Dict[str, datetime]] = field(default_factory=list)
    
    # Overall assessment
    overall_quality: DataQualityLevel = DataQualityLevel.FAIR
    quality_issues: List[str] = field(default_factory=list)
    quality_score: float = 0.0  # 0-100
    
    def calculate_quality_score(self) -> float:
        """Calculate overall data quality score (0-100)"""
        if self.total_expected_readings == 0:
            return 0.0
        
        # Base score from completeness
        completeness_score = (self.total_actual_readings / self.total_expected_readings) * 100
        
        # Adjust for specific quality issues
        penalty = len(self.quality_issues) * 5  # 5 point penalty per issue
        
        self.quality_score = max(0.0, min(100.0, completeness_score - penalty))
        return self.quality_score
    
    def assess_overall_quality(self) -> DataQualityLevel:
        """Assess overall data quality level"""
        score = self.calculate_quality_score()
        
        if score >= 95:
            self.overall_quality = DataQualityLevel.EXCELLENT
        elif score >= 85:
            self.overall_quality = DataQualityLevel.GOOD
        elif score >= 70:
            self.overall_quality = DataQualityLevel.FAIR
        else:
            self.overall_quality = DataQualityLevel.POOR
        
        return self.overall_quality


@dataclass
class SoldierDataRecord:
    """Complete data record for a single soldier"""
    
    # Core identification
    identity: SoldierIdentity
    
    # Metrics categories
    physical_metrics: PhysicalMetrics = field(default_factory=PhysicalMetrics)
    physiological_metrics: PhysiologicalMetrics = field(default_factory=PhysiologicalMetrics)
    equipment_metrics: EquipmentMetrics = field(default_factory=EquipmentMetrics)
    combat_metrics: CombatMetrics = field(default_factory=CombatMetrics)
    
    # Data quality assessment
    data_quality: DataQualityMetrics = field(default_factory=DataQualityMetrics)
    
    # Metadata
    total_raw_records: int = 0
    first_reading_time: Optional[datetime] = None
    last_reading_time: Optional[datetime] = None
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    
    # Custom metrics (extensible)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def mission_duration(self) -> Optional[timedelta]:
        """Calculate mission duration from timestamps"""
        if self.first_reading_time and self.last_reading_time:
            return self.last_reading_time - self.first_reading_time
        return None
    
    @property
    def mission_duration_minutes(self) -> Optional[float]:
        """Get mission duration in minutes"""
        duration = self.mission_duration
        if duration:
            return duration.total_seconds() / 60
        return None
    
    @property
    def callsign(self) -> str:
        """Convenience property for callsign access"""
        return self.identity.callsign
    
    def validate(self) -> List[str]:
        """Validate soldier data record and return list of issues"""
        issues = []
        
        # Basic validation
        if not self.identity.callsign:
            issues.append("Missing callsign")
        
        if self.total_raw_records == 0:
            issues.append("No raw data records")
        
        # Data quality validation
        if self.data_quality.overall_quality == DataQualityLevel.POOR:
            issues.append("Poor data quality detected")
        
        # Heart rate validation
        if (self.physiological_metrics.max_heart_rate > 0 and 
            self.physiological_metrics.max_heart_rate > 250):
            issues.append("Implausible maximum heart rate")
        
        # Battery validation
        if (self.equipment_metrics.max_battery_level > 100 or 
            self.equipment_metrics.min_battery_level < 0):
            issues.append("Invalid battery level readings")
        
        return issues
    
    def get_summary_dict(self) -> Dict[str, Any]:
        """Get summary dictionary for quick overview"""
        return {
            "callsign": self.callsign,
            "squad": self.identity.squad,
            "total_records": self.total_raw_records,
            "data_quality": self.data_quality.overall_quality.value,
            "mission_duration_minutes": self.mission_duration_minutes,
            "final_status": self.combat_metrics.final_casualty_status.value,
            "avg_heart_rate": self.physiological_metrics.avg_heart_rate,
            "total_steps": self.physical_metrics.total_steps,
            "avg_battery": self.equipment_metrics.avg_battery_level,
            "analysis_timestamp": self.analysis_timestamp.isoformat()
        }


@dataclass
class DatasetMetadata:
    """Metadata for the entire dataset"""
    file_path: Path
    original_filename: str
    file_size_bytes: int
    loaded_timestamp: datetime = field(default_factory=datetime.now)
    
    # Column mapping applied during loading
    column_mappings_applied: Dict[str, str] = field(default_factory=dict)
    original_column_names: List[str] = field(default_factory=list)
    standardized_column_names: List[str] = field(default_factory=list)
    
    # Data transformation log
    transformations_applied: List[str] = field(default_factory=list)
    data_cleaning_log: List[str] = field(default_factory=list)
    
    # Overall dataset statistics
    total_raw_rows: int = 0
    total_processed_rows: int = 0
    rows_excluded: int = 0
    exclusion_reasons: Dict[str, int] = field(default_factory=dict)


@dataclass
class SoldierDataset:
    """Complete dataset containing all soldier data and metadata"""
    
    # Core data
    raw_dataframe: pd.DataFrame
    processed_soldiers: Dict[str, SoldierDataRecord] = field(default_factory=dict)
    
    # Dataset metadata
    metadata: DatasetMetadata = field(default_factory=DatasetMetadata)
    
    # Dataset-level statistics
    total_soldiers: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    
    # Time range of data
    dataset_start_time: Optional[datetime] = None
    dataset_end_time: Optional[datetime] = None
    
    # Squad/unit organization
    squad_assignments: Dict[str, List[str]] = field(default_factory=dict)  # squad -> callsigns
    platoon_assignments: Dict[str, List[str]] = field(default_factory=dict)  # platoon -> callsigns
    
    # Dataset quality assessment
    overall_data_quality: DataQualityLevel = DataQualityLevel.FAIR
    dataset_issues: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate derived metrics after initialization"""
        if not self.raw_dataframe.empty:
            self.metadata.total_raw_rows = len(self.raw_dataframe)
            
            # Extract time range if time column exists
            if 'Time_Step' in self.raw_dataframe.columns:
                try:
                    if pd.api.types.is_datetime64_any_dtype(self.raw_dataframe['Time_Step']):
                        self.dataset_start_time = self.raw_dataframe['Time_Step'].min()
                        self.dataset_end_time = self.raw_dataframe['Time_Step'].max()
                except Exception as e:
                    self.dataset_issues.append(f"Time extraction failed: {str(e)}")
    
    def add_soldier_record(self, soldier_record: SoldierDataRecord) -> None:
        """Add a processed soldier record to the dataset"""
        self.processed_soldiers[soldier_record.callsign] = soldier_record
        self.total_soldiers = len(self.processed_soldiers)
        
        # Update squad assignments
        if soldier_record.identity.squad:
            squad = soldier_record.identity.squad
            if squad not in self.squad_assignments:
                self.squad_assignments[squad] = []
            if soldier_record.callsign not in self.squad_assignments[squad]:
                self.squad_assignments[squad].append(soldier_record.callsign)
    
    def get_soldier_by_callsign(self, callsign: str) -> Optional[SoldierDataRecord]:
        """Get soldier record by callsign"""
        return self.processed_soldiers.get(callsign)
    
    def get_soldiers_by_squad(self, squad: str) -> List[SoldierDataRecord]:
        """Get all soldier records for a specific squad"""
        if squad not in self.squad_assignments:
            return []
        
        return [self.processed_soldiers[callsign] 
                for callsign in self.squad_assignments[squad]
                if callsign in self.processed_soldiers]
    
    def get_high_quality_soldiers(self) -> List[SoldierDataRecord]:
        """Get soldiers with good or excellent data quality"""
        return [soldier for soldier in self.processed_soldiers.values()
                if soldier.data_quality.overall_quality in 
                [DataQualityLevel.GOOD, DataQualityLevel.EXCELLENT]]
    
    def calculate_dataset_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive dataset statistics"""
        if not self.processed_soldiers:
            return {}
        
        soldiers = list(self.processed_soldiers.values())
        
        # Aggregate statistics
        total_heart_rate_readings = sum(s.physiological_metrics.heart_rate_readings for s in soldiers)
        total_steps = sum(s.physical_metrics.total_steps for s in soldiers)
        avg_performance = sum(s.equipment_metrics.avg_battery_level for s in soldiers) / len(soldiers)
        
        # Quality statistics
        quality_distribution = {}
        for level in DataQualityLevel:
            quality_distribution[level.value] = sum(
                1 for s in soldiers if s.data_quality.overall_quality == level
            )
        
        return {
            "total_soldiers": self.total_soldiers,
            "total_squads": len(self.squad_assignments),
            "total_heart_rate_readings": total_heart_rate_readings,
            "total_steps_all_soldiers": total_steps,
            "average_battery_level": avg_performance,
            "data_quality_distribution": quality_distribution,
            "dataset_time_span_hours": self._get_time_span_hours(),
            "successful_analyses": self.successful_analyses,
            "failed_analyses": self.failed_analyses
        }
    
    def _get_time_span_hours(self) -> Optional[float]:
        """Calculate dataset time span in hours"""
        if self.dataset_start_time and self.dataset_end_time:
            delta = self.dataset_end_time - self.dataset_start_time
            return delta.total_seconds() / 3600
        return None
    
    def validate_dataset(self) -> List[str]:
        """Validate entire dataset and return list of issues"""
        issues = []
        
        if self.raw_dataframe.empty:
            issues.append("Empty dataset")
        
        if self.total_soldiers == 0:
            issues.append("No soldiers processed")
        
        if self.failed_analyses > self.successful_analyses:
            issues.append("More failed analyses than successful")
        
        # Check for required columns in raw data
        required_columns = ['Callsign']
        missing_columns = [col for col in required_columns 
                          if col not in self.raw_dataframe.columns]
        if missing_columns:
            issues.extend([f"Missing required column: {col}" for col in missing_columns])
        
        return issues


# Factory functions for creating instances
def create_soldier_identity(callsign: str, squad: str = None, player_id: str = None) -> SoldierIdentity:
    """Factory function to create soldier identity"""
    return SoldierIdentity(
        callsign=callsign,
        squad=squad,
        player_id=player_id
    )


def create_empty_dataset(file_path: str) -> SoldierDataset:
    """Factory function to create empty dataset with metadata"""
    metadata = DatasetMetadata(
        file_path=Path(file_path),
        original_filename=Path(file_path).name,
        file_size_bytes=0
    )
    
    return SoldierDataset(
        raw_dataframe=pd.DataFrame(),
        metadata=metadata
    )
