"""
Analysis Results Models
Defines data structures for storing and managing analysis results.
Part of the Enhanced Soldier Report System refactoring.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime, timedelta
import numpy as np


class AnalysisStatus(Enum):
    """Status of analysis operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class PerformanceRating(Enum):
    """Performance assessment ratings"""
    EXCELLENT = "excellent"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    NEEDS_IMPROVEMENT = "needs_improvement"
    CRITICAL = "critical"


@dataclass
class StatisticalSummary:
    """Statistical summary for a metric"""
    count: int
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentile_25: float
    percentile_75: float
    null_count: int = 0
    
    @classmethod
    def from_values(cls, values: List[Union[int, float]]) -> 'StatisticalSummary':
        """Create statistical summary from list of values"""
        # Filter out None values
        clean_values = [v for v in values if v is not None]
        null_count = len(values) - len(clean_values)
        
        if not clean_values:
            return cls(
                count=0, mean=0, median=0, std_dev=0,
                min_value=0, max_value=0, percentile_25=0, percentile_75=0,
                null_count=null_count
            )
        
        np_values = np.array(clean_values)
        
        return cls(
            count=len(clean_values),
            mean=float(np.mean(np_values)),
            median=float(np.median(np_values)),
            std_dev=float(np.std(np_values)),
            min_value=float(np.min(np_values)),
            max_value=float(np.max(np_values)),
            percentile_25=float(np.percentile(np_values, 25)),
            percentile_75=float(np.percentile(np_values, 75)),
            null_count=null_count
        )


@dataclass
class HeartRateAnalysis:
    """Heart rate analysis results"""
    statistics: StatisticalSummary
    zones: Dict[str, int] = field(default_factory=dict)
    abnormal_readings: Dict[str, int] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    medical_flags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate heart rate zones and risk assessment"""
        if self.statistics.count > 0:
            self._calculate_zones()
            self._assess_risk()
    
    def _calculate_zones(self):
        """Calculate heart rate zones based on readings"""
        # This would be populated by the analysis service
        # Zones: rest (<60), normal (60-100), elevated (100-150), 
        # high (150-180), extreme (180-190), critical (>190)
        pass
    
    def _assess_risk(self):
        """Assess overall heart rate risk level"""
        if self.statistics.max_value > 190:
            self.risk_level = RiskLevel.CRITICAL
            self.alerts.append(f"CRITICAL: Maximum heart rate {self.statistics.max_value:.0f} BPM")
        elif self.statistics.max_value > 180:
            self.risk_level = RiskLevel.HIGH
            self.alerts.append(f"HIGH: Elevated heart rate {self.statistics.max_value:.0f} BPM")
        elif self.statistics.min_value < 60 and self.statistics.min_value > 0:
            if self.risk_level == RiskLevel.LOW:
                self.risk_level = RiskLevel.MODERATE
            self.alerts.append(f"MODERATE: Low heart rate detected {self.statistics.min_value:.0f} BPM")


@dataclass
class PhysicalPerformanceAnalysis:
    """Physical performance analysis results"""
    step_statistics: Optional[StatisticalSummary] = None
    total_steps: int = 0
    activity_level: str = "unknown"
    movement_patterns: Dict[str, Any] = field(default_factory=dict)
    fall_incidents: int = 0
    posture_analysis: Dict[str, Any] = field(default_factory=dict)
    mission_duration: Optional[float] = None  # minutes
    performance_rating: PerformanceRating = PerformanceRating.SATISFACTORY
    
    def assess_activity_level(self) -> str:
        """Assess activity level based on step statistics"""
        if not self.step_statistics or self.step_statistics.mean == 0:
            return "inactive"
        elif self.step_statistics.mean >= 100:
            return "excellent"
        elif self.step_statistics.mean >= 50:
            return "moderate"
        else:
            return "low"


@dataclass
class EquipmentAnalysis:
    """Equipment status analysis results"""
    battery_statistics: Optional[StatisticalSummary] = None
    communication_quality: Dict[str, Any] = field(default_factory=dict)
    rssi_statistics: Optional[StatisticalSummary] = None
    equipment_failures: List[str] = field(default_factory=list)
    low_battery_incidents: int = 0
    critical_battery_incidents: int = 0
    comm_quality_rating: str = "unknown"
    risk_level: RiskLevel = RiskLevel.LOW
    
    def assess_equipment_risk(self) -> RiskLevel:
        """Assess overall equipment risk level"""
        if self.critical_battery_incidents > 0:
            return RiskLevel.CRITICAL
        elif self.low_battery_incidents > 5:
            return RiskLevel.HIGH
        elif self.comm_quality_rating == "poor":
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW


@dataclass
class SafetyAnalysis:
    """Safety analysis results"""
    overall_safety_score: float = 100.0
    temperature_risk: RiskLevel = RiskLevel.LOW
    physiological_stress: RiskLevel = RiskLevel.LOW
    equipment_risk: RiskLevel = RiskLevel.LOW
    environmental_risk: RiskLevel = RiskLevel.LOW
    
    # Specific safety metrics
    temperature_statistics: Optional[StatisticalSummary] = None
    heat_stress_incidents: int = 0
    cold_stress_incidents: int = 0
    
    # Medical alerts and recommendations
    medical_alerts: List[str] = field(default_factory=list)
    safety_recommendations: List[str] = field(default_factory=list)
    immediate_actions: List[str] = field(default_factory=list)
    
    def calculate_overall_score(self) -> float:
        """Calculate overall safety score based on risk factors"""
        score = 100.0
        
        # Deduct points based on risk levels
        risk_deductions = {
            RiskLevel.LOW: 0,
            RiskLevel.MODERATE: 10,
            RiskLevel.HIGH: 25,
            RiskLevel.CRITICAL: 40
        }
        
        score -= risk_deductions[self.temperature_risk]
        score -= risk_deductions[self.physiological_stress]
        score -= risk_deductions[self.equipment_risk]
        score -= risk_deductions[self.environmental_risk]
        
        # Additional deductions for incidents
        score -= (self.heat_stress_incidents * 5)
        score -= (self.cold_stress_incidents * 3)
        
        self.overall_safety_score = max(0.0, score)
        return self.overall_safety_score


@dataclass
class PerformanceScore:
    """Performance scoring results"""
    final_score: float
    starting_score: float = 100.0
    total_deductions: float = 0.0
    total_bonuses: float = 0.0
    
    # Detailed breakdown
    deduction_details: List[str] = field(default_factory=list)
    bonus_details: List[str] = field(default_factory=list)
    
    # Performance factors
    activity_score: float = 0.0
    casualty_penalty: float = 0.0
    equipment_score: float = 0.0
    communication_score: float = 0.0
    engagement_bonus: float = 0.0
    safety_penalty: float = 0.0
    
    @property
    def performance_rating(self) -> PerformanceRating:
        """Get performance rating based on final score"""
        if self.final_score >= 90:
            return PerformanceRating.EXCELLENT
        elif self.final_score >= 80:
            return PerformanceRating.GOOD
        elif self.final_score >= 70:
            return PerformanceRating.SATISFACTORY
        elif self.final_score >= 60:
            return PerformanceRating.NEEDS_IMPROVEMENT
        else:
            return PerformanceRating.CRITICAL
    
    @property
    def performance_status(self) -> str:
        """Get descriptive status based on rating"""
        rating_descriptions = {
            PerformanceRating.EXCELLENT: "EXCELLENT - Exemplary performance",
            PerformanceRating.GOOD: "GOOD - Above average performance",
            PerformanceRating.SATISFACTORY: "SATISFACTORY - Meets requirements",
            PerformanceRating.NEEDS_IMPROVEMENT: "NEEDS IMPROVEMENT - Below standard",
            PerformanceRating.CRITICAL: "CRITICAL - Immediate attention required"
        }
        return rating_descriptions[self.performance_rating]


@dataclass
class CombatAnalysis:
    """Combat-related analysis results"""
    final_casualty_status: str = "GOOD"
    casualty_events: int = 0
    combat_engagements: int = 0
    unique_shooters: int = 0
    primary_weapon: Optional[str] = None
    hit_zones: List[str] = field(default_factory=list)
    munitions_used: List[str] = field(default_factory=list)
    engagement_effectiveness: float = 0.0
    
    @property
    def survival_status(self) -> bool:
        """Check if soldier survived the engagement"""
        return self.final_casualty_status not in ["KILL", "KIA"]


@dataclass
class SoldierAnalysisResult:
    """Complete analysis results for an individual soldier"""
    
    # Identification
    callsign: str
    analysis_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    analysis_status: AnalysisStatus = AnalysisStatus.PENDING
    
    # Data quality metrics
    total_records: int = 0
    data_quality_score: float = 0.0
    missing_data_percentage: float = 0.0
    
    # Core analysis components
    heart_rate_analysis: Optional[HeartRateAnalysis] = None
    physical_performance: Optional[PhysicalPerformanceAnalysis] = None
    equipment_analysis: Optional[EquipmentAnalysis] = None
    safety_analysis: Optional[SafetyAnalysis] = None
    combat_analysis: Optional[CombatAnalysis] = None
    performance_score: Optional[PerformanceScore] = None
    
    # Mission context
    mission_duration: Optional[float] = None
    squad_assignment: Optional[str] = None
    mission_phase: Optional[str] = None
    
    # Analysis metadata
    analysis_duration: Optional[float] = None  # seconds
    analysis_errors: List[str] = field(default_factory=list)
    analysis_warnings: List[str] = field(default_factory=list)
    
    # Custom metrics (extensible)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def overall_risk_level(self) -> RiskLevel:
        """Calculate overall risk level from all analysis components"""
        risk_levels = []
        
        if self.heart_rate_analysis:
            risk_levels.append(self.heart_rate_analysis.risk_level)
        
        if self.safety_analysis:
            risk_levels.append(self.safety_analysis.temperature_risk)
            risk_levels.append(self.safety_analysis.physiological_stress)
            risk_levels.append(self.safety_analysis.equipment_risk)
        
        if self.equipment_analysis:
            risk_levels.append(self.equipment_analysis.risk_level)
        
        # Return highest risk level found
        if RiskLevel.CRITICAL in risk_levels:
            return RiskLevel.CRITICAL
        elif RiskLevel.HIGH in risk_levels:
            return RiskLevel.HIGH
        elif RiskLevel.MODERATE in risk_levels:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    @property
    def requires_medical_attention(self) -> bool:
        """Check if soldier requires immediate medical attention"""
        if self.overall_risk_level == RiskLevel.CRITICAL:
            return True
        
        if self.heart_rate_analysis and self.heart_rate_analysis.medical_flags:
            return True
        
        if self.safety_analysis and self.safety_analysis.immediate_actions:
            return True
        
        return False
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get key summary metrics for quick overview"""
        summary = {
            "callsign": self.callsign,
            "analysis_status": self.analysis_status.value,
            "total_records": self.total_records,
            "overall_risk_level": self.overall_risk_level.value,
            "requires_medical_attention": self.requires_medical_attention
        }
        
        if self.performance_score:
            summary["performance_score"] = self.performance_score.final_score
            summary["performance_rating"] = self.performance_score.performance_rating.value
        
        if self.heart_rate_analysis:
            summary["avg_heart_rate"] = self.heart_rate_analysis.statistics.mean
            summary["max_heart_rate"] = self.heart_rate_analysis.statistics.max_value
        
        if self.physical_performance:
            summary["total_steps"] = self.physical_performance.total_steps
            summary["activity_level"] = self.physical_performance.activity_level
        
        if self.combat_analysis:
            summary["final_status"] = self.combat_analysis.final_casualty_status
            summary["combat_engagements"] = self.combat_analysis.combat_engagements
        
        return summary
    
    def validate(self) -> List[str]:
        """Validate analysis results and return list of issues"""
        issues = []
        
        if not self.callsign:
            issues.append("Missing callsign")
        
        if self.total_records == 0:
            issues.append("No data records analyzed")
        
        if self.analysis_status == AnalysisStatus.COMPLETED:
            if not self.performance_score:
                issues.append("Missing performance score for completed analysis")
            
            if not self.safety_analysis:
                issues.append("Missing safety analysis for completed analysis")
        
        # Validate data consistency
        if self.heart_rate_analysis and self.heart_rate_analysis.statistics.count == 0:
            issues.append("Heart rate analysis shows no valid readings")
        
        return issues


@dataclass
class BatchAnalysisResult:
    """Results from analyzing multiple soldiers"""
    
    analysis_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    analysis_status: AnalysisStatus = AnalysisStatus.PENDING
    
    # Individual results
    soldier_results: Dict[str, SoldierAnalysisResult] = field(default_factory=dict)
    
    # Batch statistics
    total_soldiers: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    
    # Aggregate metrics
    overall_statistics: Dict[str, StatisticalSummary] = field(default_factory=dict)
    squad_summaries: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Batch metadata
    analysis_duration: Optional[float] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_soldier_result(self, result: SoldierAnalysisResult) -> None:
        """Add individual soldier result to batch"""
        self.soldier_results[result.callsign] = result
        self.total_soldiers = len(self.soldier_results)
        
        if result.analysis_status == AnalysisStatus.COMPLETED:
            self.successful_analyses += 1
        elif result.analysis_status == AnalysisStatus.FAILED:
            self.failed_analyses += 1
    
    def get_high_risk_soldiers(self) -> List[str]:
        """Get list of soldiers with high or critical risk levels"""
        high_risk = []
        for callsign, result in self.soldier_results.items():
            if result.overall_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                high_risk.append(callsign)
        return high_risk
    
    def get_medical_attention_required(self) -> List[str]:
        """Get list of soldiers requiring immediate medical attention"""
        medical_required = []
        for callsign, result in self.soldier_results.items():
            if result.requires_medical_attention:
                medical_required.append(callsign)
        return medical_required
    
    def calculate_aggregate_statistics(self) -> None:
        """Calculate aggregate statistics across all soldiers"""
        # Collect metrics from all successful analyses
        heart_rates = []
        performance_scores = []
        step_counts = []
        
        for result in self.soldier_results.values():
            if result.analysis_status == AnalysisStatus.COMPLETED:
                if result.heart_rate_analysis:
                    heart_rates.append(result.heart_rate_analysis.statistics.mean)
                
                if result.performance_score:
                    performance_scores.append(result.performance_score.final_score)
                
                if result.physical_performance:
                    step_counts.append(result.physical_performance.total_steps)
        
        # Create statistical summaries
        if heart_rates:
            self.overall_statistics["heart_rate"] = StatisticalSummary.from_values(heart_rates)
        
        if performance_scores:
            self.overall_statistics["performance_score"] = StatisticalSummary.from_values(performance_scores)
        
        if step_counts:
            self.overall_statistics["step_count"] = StatisticalSummary.from_values(step_counts)
    
    @property
    def success_rate(self) -> float:
        """Calculate analysis success rate"""
        if self.total_soldiers == 0:
            return 0.0
        return (self.successful_analyses / self.total_soldiers) * 100
