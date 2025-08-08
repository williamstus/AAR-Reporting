"""
Soldier Activity Analysis Engine
Implements REQ-ACTIVITY-001 through REQ-ACTIVITY-008
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import math
from datetime import datetime, timedelta

from core.models import AnalysisEngine, AnalysisResult, Alert, AnalysisDomain, AlertLevel
from core.event_bus import EventBus


class ActivityLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXCESSIVE = "excessive"


class PostureType(Enum):
    STANDING = "Standing"
    PRONE = "Prone"
    UNKNOWN = "Unknown"


@dataclass
class ActivityMetrics:
    """Comprehensive activity metrics for a soldier"""
    soldier_id: str
    total_steps: int
    avg_steps_per_minute: float
    max_steps_per_minute: int
    activity_level: ActivityLevel
    posture_distribution: Dict[str, float]
    movement_patterns: Dict[str, Any]
    endurance_score: float
    recovery_metrics: Dict[str, float]
    rate_of_motion: float
    fitness_baseline: Dict[str, float]


class SoldierActivityAnalysisEngine(AnalysisEngine):
    """
    Analysis engine for soldier activity and performance tracking
    Covers movement analysis, posture monitoring, and physical performance
    """
    
    def __init__(self, event_bus: EventBus):
        super().__init__(AnalysisDomain.ACTIVITY)
        self.event_bus = event_bus
        
        # Configuration thresholds (REQ-ACTIVITY-001)
        self.step_thresholds = {
            'normal_min': 100,
            'normal_max': 400,
            'high_activity': 300,
            'excessive': 500
        }
        
        # Activity level classification
        self.activity_levels = {
            'low': (0, 150),
            'moderate': (150, 300),
            'high': (300, 450),
            'excessive': (450, float('inf'))
        }
        
        # Performance baselines
        self.fitness_benchmarks = {
            'steps_per_minute_good': 15,
            'endurance_threshold': 0.7,
            'recovery_time_max': 300  # seconds
        }

    def get_required_columns(self) -> List[str]:
        """Return columns required for activity analysis"""
        return [
            'Unit', 'Timestamp', 'Steps', 'Posture', 
            'Lat', 'Long', 'CasualtyState', 'ActivityPattern'
        ]

    def analyze(self, data: pd.DataFrame, config: Dict[str, Any] = None) -> AnalysisResult:
        """
        Perform comprehensive activity analysis
        
        Args:
            data: Training exercise data
            config: Analysis configuration parameters
            
        Returns:
            AnalysisResult with activity analysis findings
        """
        try:
            # Initialize results
            alerts = []
            metrics = {}
            recommendations = []
            
            # Convert timestamp to datetime
            data['Timestamp'] = pd.to_datetime(data['Timestamp'])
            
            # Analyze each soldier
            soldier_metrics = {}
            for unit in data['Unit'].unique():
                unit_data = data[data['Unit'] == unit].copy()
                soldier_analysis = self._analyze_soldier_activity(unit_data, unit)
                soldier_metrics[unit] = soldier_analysis
                
                # Generate alerts for this soldier
                unit_alerts = self._generate_activity_alerts(soldier_analysis, unit)
                alerts.extend(unit_alerts)
            
            # Generate overall activity analysis
            overall_metrics = self._calculate_overall_metrics(soldier_metrics)
            
            # Generate comparative analysis (REQ-ACTIVITY-008)
            comparative_analysis = self._perform_comparative_analysis(soldier_metrics)
            
            # Generate recommendations
            recommendations = self._generate_activity_recommendations(
                soldier_metrics, overall_metrics
            )
            
            # Compile results
            metrics = {
                'soldier_metrics': soldier_metrics,
                'overall_metrics': overall_metrics,
                'comparative_analysis': comparative_analysis,
                'summary_statistics': self._calculate_summary_stats(data)
            }
            
            # Publish analysis completion event
            self.event_bus.publish({
                'type': 'analysis_completed',
                'domain': 'activity',
                'metrics_count': len(soldier_metrics),
                'alerts_generated': len(alerts)
            })
            
            return AnalysisResult(
                domain=self.domain,
                metrics=metrics,
                alerts=alerts,
                recommendations=recommendations,
                confidence_score=0.95,
                analysis_timestamp=datetime.now()
            )
            
        except Exception as e:
            self.event_bus.publish({
                'type': 'analysis_error',
                'domain': 'activity',
                'error': str(e)
            })
            raise

    def _analyze_soldier_activity(self, unit_data: pd.DataFrame, unit_id: str) -> ActivityMetrics:
        """Analyze activity patterns for a single soldier"""
        
        # REQ-ACTIVITY-001: Step count and movement analysis
        step_analysis = self._analyze_step_patterns(unit_data)
        
        # REQ-ACTIVITY-002: Posture monitoring
        posture_analysis = self._analyze_posture_patterns(unit_data)
        
        # REQ-ACTIVITY-003: Rate of motion calculation
        motion_analysis = self._calculate_rate_of_motion(unit_data)
        
        # REQ-ACTIVITY-004: Activity correlation with mission timeline
        mission_correlation = self._correlate_with_mission_timeline(unit_data)
        
        # REQ-ACTIVITY-005: Endurance assessment
        endurance_score = self._assess_endurance(unit_data)
        
        # REQ-ACTIVITY-006: Recovery time analysis
        recovery_metrics = self._analyze_recovery_patterns(unit_data)
        
        # REQ-ACTIVITY-007: Fitness baseline establishment
        fitness_baseline = self._establish_fitness_baseline(unit_data)
        
        # Determine overall activity level
        avg_steps = step_analysis['avg_steps_per_minute']
        activity_level = self._classify_activity_level(avg_steps)
        
        return ActivityMetrics(
            soldier_id=unit_id,
            total_steps=step_analysis['total_steps'],
            avg_steps_per_minute=step_analysis['avg_steps_per_minute'],
            max_steps_per_minute=step_analysis['max_steps_per_minute'],
            activity_level=activity_level,
            posture_distribution=posture_analysis,
            movement_patterns=mission_correlation,
            endurance_score=endurance_score,
            recovery_metrics=recovery_metrics,
            rate_of_motion=motion_analysis['avg_rate'],
            fitness_baseline=fitness_baseline
        )

    def _analyze_step_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """REQ-ACTIVITY-001: Analyze step count and movement patterns"""
        
        # Handle missing step data
        valid_steps = data['Steps'].dropna()
        if len(valid_steps) == 0:
            return {
                'total_steps': 0,
                'avg_steps_per_minute': 0,
                'max_steps_per_minute': 0,
                'step_variance': 0,
                'movement_consistency': 0
            }
        
        # Calculate step statistics
        total_steps = valid_steps.sum()
        duration_minutes = len(data) / 60  # Assuming 1-second intervals
        avg_steps_per_minute = total_steps / duration_minutes if duration_minutes > 0 else 0
        max_steps_per_minute = valid_steps.max()
        step_variance = valid_steps.var()
        
        # Movement consistency (lower variance = more consistent)
        movement_consistency = 1 / (1 + step_variance) if step_variance > 0 else 1
        
        return {
            'total_steps': int(total_steps),
            'avg_steps_per_minute': avg_steps_per_minute,
            'max_steps_per_minute': int(max_steps_per_minute),
            'step_variance': step_variance,
            'movement_consistency': movement_consistency
        }

    def _analyze_posture_patterns(self, data: pd.DataFrame) -> Dict[str, float]:
        """REQ-ACTIVITY-002: Analyze posture distribution and tactical positions"""
        
        posture_counts = data['Posture'].value_counts()
        total_records = len(data)
        
        # Calculate percentage distribution
        posture_distribution = {}
        for posture in ['Standing', 'Prone', 'Unknown']:
            count = posture_counts.get(posture, 0)
            percentage = (count / total_records) * 100 if total_records > 0 else 0
            posture_distribution[posture] = percentage
        
        # Add tactical assessment
        prone_percentage = posture_distribution.get('Prone', 0)
        posture_distribution['tactical_readiness'] = prone_percentage  # Higher prone = more tactical
        
        return posture_distribution

    def _calculate_rate_of_motion(self, data: pd.DataFrame) -> Dict[str, float]:
        """REQ-ACTIVITY-003: Calculate rate of motion from GPS coordinates"""
        
        if 'Lat' not in data.columns or 'Long' not in data.columns:
            return {'avg_rate': 0, 'max_rate': 0, 'total_distance': 0}
        
        # Remove invalid GPS coordinates
        valid_gps = data.dropna(subset=['Lat', 'Long'])
        if len(valid_gps) < 2:
            return {'avg_rate': 0, 'max_rate': 0, 'total_distance': 0}
        
        # Calculate distances between consecutive points
        distances = []
        rates = []
        
        for i in range(1, len(valid_gps)):
            prev_row = valid_gps.iloc[i-1]
            curr_row = valid_gps.iloc[i]
            
            # Calculate distance using Haversine formula
            distance = self._haversine_distance(
                prev_row['Lat'], prev_row['Long'],
                curr_row['Lat'], curr_row['Long']
            )
            distances.append(distance)
            
            # Calculate time difference
            time_diff = (curr_row['Timestamp'] - prev_row['Timestamp']).total_seconds()
            if time_diff > 0:
                rate = distance / time_diff  # meters per second
                rates.append(rate)
        
        total_distance = sum(distances)
        avg_rate = np.mean(rates) if rates else 0
        max_rate = np.max(rates) if rates else 0
        
        return {
            'avg_rate': avg_rate,
            'max_rate': max_rate,
            'total_distance': total_distance
        }

    def _correlate_with_mission_timeline(self, data: pd.DataFrame) -> Dict[str, Any]:
        """REQ-ACTIVITY-004: Correlate activity with mission objectives"""
        
        # Analyze activity patterns over time
        data_sorted = data.sort_values('Timestamp')
        
        # Divide mission into phases (beginning, middle, end)
        total_duration = len(data_sorted)
        phase_size = total_duration // 3
        
        phases = {
            'initial': data_sorted.iloc[:phase_size],
            'middle': data_sorted.iloc[phase_size:2*phase_size],
            'final': data_sorted.iloc[2*phase_size:]
        }
        
        phase_analysis = {}
        for phase_name, phase_data in phases.items():
            if len(phase_data) > 0:
                avg_steps = phase_data['Steps'].mean() if 'Steps' in phase_data else 0
                casualty_events = (phase_data['CasualtyState'] != 'GOOD').sum()
                
                phase_analysis[phase_name] = {
                    'avg_activity': avg_steps,
                    'casualty_events': casualty_events,
                    'duration_minutes': len(phase_data) / 60
                }
        
        # Calculate mission progression patterns
        progression_trend = self._calculate_activity_trend(data_sorted)
        
        return {
            'phase_analysis': phase_analysis,
            'progression_trend': progression_trend,
            'mission_intensity': self._calculate_mission_intensity(data_sorted)
        }

    def _assess_endurance(self, data: pd.DataFrame) -> float:
        """REQ-ACTIVITY-005: Assess endurance through sustained activity periods"""
        
        valid_steps = data['Steps'].dropna()
        if len(valid_steps) == 0:
            return 0.0
        
        # Find sustained high-activity periods
        high_activity_threshold = self.activity_levels['high'][0]
        sustained_periods = []
        current_period = 0
        
        for steps in valid_steps:
            if steps >= high_activity_threshold:
                current_period += 1
            else:
                if current_period > 0:
                    sustained_periods.append(current_period)
                current_period = 0
        
        # Add final period if it was ongoing
        if current_period > 0:
            sustained_periods.append(current_period)
        
        # Calculate endurance score
        if not sustained_periods:
            return 0.0
        
        max_sustained = max(sustained_periods)
        avg_sustained = np.mean(sustained_periods)
        
        # Normalize to 0-1 scale (higher is better endurance)
        endurance_score = min(1.0, (max_sustained * 0.6 + avg_sustained * 0.4) / 100)
        
        return endurance_score

    def _analyze_recovery_patterns(self, data: pd.DataFrame) -> Dict[str, float]:
        """REQ-ACTIVITY-006: Analyze recovery time between high-activity phases"""
        
        valid_steps = data['Steps'].dropna()
        if len(valid_steps) == 0:
            return {'avg_recovery_time': 0, 'recovery_efficiency': 0}
        
        high_threshold = self.activity_levels['high'][0]
        low_threshold = self.activity_levels['low'][1]
        
        recovery_times = []
        in_recovery = False
        recovery_start = 0
        
        for i, steps in enumerate(valid_steps):
            if steps >= high_threshold and in_recovery:
                # End of recovery period
                recovery_time = i - recovery_start
                recovery_times.append(recovery_time)
                in_recovery = False
            elif steps <= low_threshold and not in_recovery:
                # Start of recovery period
                recovery_start = i
                in_recovery = True
        
        if recovery_times:
            avg_recovery = np.mean(recovery_times)
            # Efficiency: faster recovery is better (inverse relationship)
            recovery_efficiency = 1 / (1 + avg_recovery / 60)  # Convert to minutes
        else:
            avg_recovery = 0
            recovery_efficiency = 0
        
        return {
            'avg_recovery_time': avg_recovery,
            'recovery_efficiency': recovery_efficiency,
            'recovery_periods': len(recovery_times)
        }

    def _establish_fitness_baseline(self, data: pd.DataFrame) -> Dict[str, float]:
        """REQ-ACTIVITY-007: Establish individual fitness baseline"""
        
        valid_steps = data['Steps'].dropna()
        if len(valid_steps) == 0:
            return {
                'baseline_steps_per_minute': 0,
                'peak_performance': 0,
                'consistency_score': 0,
                'fitness_level': 0
            }
        
        # Calculate baseline metrics
        baseline_steps = valid_steps.median()  # Use median for stability
        peak_performance = valid_steps.quantile(0.9)  # 90th percentile
        consistency_score = 1 - (valid_steps.std() / valid_steps.mean()) if valid_steps.mean() > 0 else 0
        
        # Overall fitness level (0-1 scale)
        fitness_level = min(1.0, (baseline_steps / 200 + peak_performance / 400 + consistency_score) / 3)
        
        return {
            'baseline_steps_per_minute': baseline_steps,
            'peak_performance': peak_performance,
            'consistency_score': max(0, consistency_score),
            'fitness_level': fitness_level
        }

    def _classify_activity_level(self, avg_steps: float) -> ActivityLevel:
        """Classify activity level based on average steps per minute"""
        
        for level, (min_val, max_val) in self.activity_levels.items():
            if min_val <= avg_steps < max_val:
                return ActivityLevel(level)
        
        return ActivityLevel.LOW

    def _generate_activity_alerts(self, metrics: ActivityMetrics, unit_id: str) -> List[Alert]:
        """Generate alerts based on activity analysis"""
        
        alerts = []
        
        # Low activity alert
        if metrics.activity_level == ActivityLevel.LOW:
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                message=f"Unit {unit_id}: Low activity level detected ({metrics.avg_steps_per_minute:.1f} steps/min)",
                domain=self.domain,
                timestamp=datetime.now(),
                details={'avg_steps': metrics.avg_steps_per_minute, 'threshold': self.activity_levels['low'][1]}
            ))
        
        # Excessive activity alert
        if metrics.activity_level == ActivityLevel.EXCESSIVE:
            alerts.append(Alert(
                level=AlertLevel.HIGH,
                message=f"Unit {unit_id}: Excessive activity detected - monitor for fatigue",
                domain=self.domain,
                timestamp=datetime.now(),
                details={'avg_steps': metrics.avg_steps_per_minute}
            ))
        
        # Poor endurance alert
        if metrics.endurance_score < 0.3:
            alerts.append(Alert(
                level=AlertLevel.MEDIUM,
                message=f"Unit {unit_id}: Low endurance score ({metrics.endurance_score:.2f})",
                domain=self.domain,
                timestamp=datetime.now(),
                details={'endurance_score': metrics.endurance_score}
            ))
        
        # Recovery efficiency alert
        if metrics.recovery_metrics['recovery_efficiency'] < 0.5:
            alerts.append(Alert(
                level=AlertLevel.MEDIUM,
                message=f"Unit {unit_id}: Slow recovery between high-activity periods",
                domain=self.domain,
                timestamp=datetime.now(),
                details=metrics.recovery_metrics
            ))
        
        return alerts

    def _calculate_overall_metrics(self, soldier_metrics: Dict[str, ActivityMetrics]) -> Dict[str, Any]:
        """Calculate overall activity metrics across all soldiers"""
        
        if not soldier_metrics:
            return {}
        
        # Aggregate metrics
        total_steps = sum(m.total_steps for m in soldier_metrics.values())
        avg_activity = np.mean([m.avg_steps_per_minute for m in soldier_metrics.values()])
        avg_endurance = np.mean([m.endurance_score for m in soldier_metrics.values()])
        
        # Activity level distribution
        activity_distribution = {}
        for level in ActivityLevel:
            count = sum(1 for m in soldier_metrics.values() if m.activity_level == level)
            activity_distribution[level.value] = count
        
        return {
            'total_soldiers': len(soldier_metrics),
            'total_steps_all': total_steps,
            'avg_activity_level': avg_activity,
            'avg_endurance_score': avg_endurance,
            'activity_distribution': activity_distribution,
            'unit_performance_ranking': self._rank_unit_performance(soldier_metrics)
        }

    def _perform_comparative_analysis(self, soldier_metrics: Dict[str, ActivityMetrics]) -> Dict[str, Any]:
        """REQ-ACTIVITY-008: Perform comparative analysis within unit structures"""
        
        if len(soldier_metrics) < 2:
            return {'insufficient_data': True}
        
        # Performance comparisons
        step_values = [m.avg_steps_per_minute for m in soldier_metrics.values()]
        endurance_values = [m.endurance_score for m in soldier_metrics.values()]
        
        # Statistical analysis
        step_stats = {
            'mean': np.mean(step_values),
            'std': np.std(step_values),
            'min': np.min(step_values),
            'max': np.max(step_values),
            'range': np.max(step_values) - np.min(step_values)
        }
        
        # Identify outliers (soldiers significantly above/below average)
        step_mean = step_stats['mean']
        step_std = step_stats['std']
        
        high_performers = []
        low_performers = []
        
        for unit_id, metrics in soldier_metrics.items():
            z_score = (metrics.avg_steps_per_minute - step_mean) / step_std if step_std > 0 else 0
            
            if z_score > 1.5:  # Above 1.5 standard deviations
                high_performers.append({
                    'unit_id': unit_id,
                    'performance': metrics.avg_steps_per_minute,
                    'z_score': z_score
                })
            elif z_score < -1.5:  # Below 1.5 standard deviations
                low_performers.append({
                    'unit_id': unit_id,
                    'performance': metrics.avg_steps_per_minute,
                    'z_score': z_score
                })
        
        return {
            'performance_statistics': step_stats,
            'high_performers': high_performers,
            'low_performers': low_performers,
            'unit_rankings': self._rank_unit_performance(soldier_metrics),
            'performance_variance': step_std / step_mean if step_mean > 0 else 0
        }

    def _generate_activity_recommendations(self, soldier_metrics: Dict[str, ActivityMetrics], 
                                         overall_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on activity analysis"""
        
        recommendations = []
        
        # Overall activity level recommendations
        avg_activity = overall_metrics.get('avg_activity_level', 0)
        if avg_activity < self.activity_levels['moderate'][0]:
            recommendations.append(
                "UNIT RECOMMENDATION: Increase overall physical activity intensity. "
                "Current average activity level is below optimal training standards."
            )
        
        # Individual soldier recommendations
        for unit_id, metrics in soldier_metrics.items():
            if metrics.activity_level == ActivityLevel.LOW:
                recommendations.append(
                    f"INDIVIDUAL ({unit_id}): Implement additional physical conditioning. "
                    f"Current activity level ({metrics.avg_steps_per_minute:.1f} steps/min) below standards."
                )
            
            if metrics.endurance_score < 0.4:
                recommendations.append(
                    f"INDIVIDUAL ({unit_id}): Focus on endurance training. "
                    f"Endurance score of {metrics.endurance_score:.2f} indicates need for improvement."
                )
            
            if metrics.recovery_metrics['recovery_efficiency'] < 0.5:
                recommendations.append(
                    f"INDIVIDUAL ({unit_id}): Improve recovery protocols. "
                    "Consider additional rest intervals and hydration strategies."
                )
        
        # Tactical recommendations based on posture analysis
        for unit_id, metrics in soldier_metrics.items():
            prone_percentage = metrics.posture_distribution.get('Prone', 0)
            if prone_percentage < 20:  # Less than 20% in tactical positions
                recommendations.append(
                    f"TACTICAL ({unit_id}): Increase tactical positioning awareness. "
                    f"Only {prone_percentage:.1f}% time in prone position during exercise."
                )
        
        return recommendations

    def _rank_unit_performance(self, soldier_metrics: Dict[str, ActivityMetrics]) -> List[Dict[str, Any]]:
        """Rank units by overall performance"""
        
        rankings = []
        for unit_id, metrics in soldier_metrics.items():
            # Composite performance score
            performance_score = (
                metrics.avg_steps_per_minute / 200 * 0.3 +  # Activity level (30%)
                metrics.endurance_score * 0.3 +               # Endurance (30%)
                metrics.recovery_metrics['recovery_efficiency'] * 0.2 +  # Recovery (20%)
                metrics.fitness_baseline['fitness_level'] * 0.2  # Overall fitness (20%)
            )
            
            rankings.append({
                'unit_id': unit_id,
                'performance_score': performance_score,
                'activity_level': metrics.activity_level.value,
                'endurance_score': metrics.endurance_score
            })
        
        # Sort by performance score (highest first)
        rankings.sort(key=lambda x: x['performance_score'], reverse=True)
        
        # Add ranks
        for i, ranking in enumerate(rankings):
            ranking['rank'] = i + 1
        
        return rankings

    def _calculate_summary_stats(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics for the dataset"""
        
        return {
            'total_records': len(data),
            'unique_soldiers': data['Unit'].nunique(),
            'exercise_duration_minutes': len(data) / 60,  # Assuming 1-second intervals
            'data_quality': {
                'step_data_completeness': (1 - data['Steps'].isna().sum() / len(data)) * 100,
                'gps_data_completeness': (1 - data[['Lat', 'Long']].isna().any(axis=1).sum() / len(data)) * 100,
                'posture_data_completeness': (1 - data['Posture'].isna().sum() / len(data)) * 100
            }
        }

    # Helper methods
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates using Haversine formula"""
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in meters
        r = 6371000
        
        return c * r

    def _calculate_activity_trend(self, data: pd.DataFrame) -> str:
        """Calculate whether activity is increasing, decreasing, or stable over time"""
        
        if len(data) < 2:
            return "insufficient_data"
        
        # Calculate trend using linear regression on step counts
        valid_data = data.dropna(subset=['Steps'])
        if len(valid_data) < 2:
            return "insufficient_data"
        
        x = np.arange(len(valid_data))
        y = valid_data['Steps'].values
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 5:
            return "increasing"
        elif slope < -5:
            return "decreasing"
        else:
            return "stable"

    def _calculate_mission_intensity(self, data: pd.DataFrame) -> float:
        """Calculate overall mission intensity based on activity and casualty patterns"""
        
        # Factors contributing to mission intensity
        avg_steps = data['Steps'].mean() if 'Steps' in data else 0
        casualty_rate = (data['CasualtyState'] != 'GOOD').sum() / len(data) if len(data) > 0 else 0
        
        # Normalize to 0-1 scale
        activity_intensity = min(1.0, avg_steps / 300)  # 300 steps = high intensity
        casualty_intensity = min(1.0, casualty_rate * 2)  # 50% casualty rate = max intensity
        
        # Combined intensity score
        mission_intensity = (activity_intensity * 0.7 + casualty_intensity * 0.3)
        
        return mission_intensity