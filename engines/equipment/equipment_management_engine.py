"""
Equipment Management Analysis Engine - FIXED VERSION
Implements REQ-EQUIPMENT-001 through REQ-EQUIPMENT-008
Fixed class name: EquipmentManagementAnalysisEngine
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import json

from core.models import AnalysisEngine, AnalysisResult, Alert, AnalysisDomain, AlertLevel
from core.event_bus import EventBus


class BatteryStatus(Enum):
    CRITICAL = "critical"    # < 20%
    LOW = "low"             # 20-40%
    MODERATE = "moderate"    # 40-70%
    GOOD = "good"           # 70-90%
    EXCELLENT = "excellent"  # > 90%


class EquipmentReliability(Enum):
    EXCELLENT = "excellent"  # > 95%
    GOOD = "good"           # 85-95%
    FAIR = "fair"           # 70-85%
    POOR = "poor"           # < 70%


@dataclass
class BatteryMetrics:
    """Battery performance metrics for a soldier"""
    soldier_id: str
    current_level: float
    min_level: float
    max_level: float
    avg_level: float
    depletion_rate: float  # % per hour
    estimated_remaining_hours: float
    critical_periods: int
    status: BatteryStatus


@dataclass
class EquipmentMetrics:
    """Comprehensive equipment metrics for a soldier"""
    soldier_id: str
    battery_metrics: BatteryMetrics
    power_consumption_patterns: Dict[str, float]
    equipment_reliability_score: float
    malfunction_incidents: List[Dict[str, Any]]
    usage_patterns: Dict[str, Any]
    maintenance_recommendations: List[str]
    load_optimization_score: float


class EquipmentManagementAnalysisEngine(AnalysisEngine):
    """
    Analysis engine for equipment management and optimization
    Covers battery management, equipment reliability, and load-out optimization
    """
    
    def __init__(self, event_bus: EventBus):
        super().__init__(AnalysisDomain.EQUIPMENT)
        self.event_bus = event_bus
        
        # Configuration thresholds (REQ-EQUIPMENT-001)
        self.battery_thresholds = {
            'critical': 20,
            'low': 40,
            'moderate': 70,
            'good': 90,
            'mission_critical': 40  # Minimum for mission sustainability
        }
        
        # Power consumption baselines
        self.power_consumption_baselines = {
            'low_activity': 5,      # % per hour during low activity
            'moderate_activity': 8,  # % per hour during moderate activity
            'high_activity': 12,    # % per hour during high activity
            'critical_ops': 20      # % per hour during critical operations
        }
        
        # Equipment reliability thresholds
        self.reliability_thresholds = {
            'excellent': 95,
            'good': 85,
            'fair': 70,
            'poor': 0
        }

    def get_required_columns(self) -> List[str]:
        """Return columns required for equipment analysis"""
        return [
            'Unit', 'Timestamp', 'BatteryLevel', 'Steps', 'CasualtyState',
            'Posture', 'RSSI', 'MCS', 'NetworkHops'
        ]

    def analyze(self, data: pd.DataFrame, config: Dict[str, Any] = None) -> AnalysisResult:
        """
        Perform comprehensive equipment management analysis
        
        Args:
            data: Training exercise data
            config: Analysis configuration parameters
            
        Returns:
            AnalysisResult with equipment analysis findings
        """
        try:
            # Initialize results
            alerts = []
            metrics = {}
            recommendations = []
            
            # Convert timestamp to datetime
            data['Timestamp'] = pd.to_datetime(data['Timestamp'])
            
            # Analyze equipment for each soldier
            soldier_metrics = {}
            for unit in data['Unit'].unique():
                unit_data = data[data['Unit'] == unit].copy()
                equipment_analysis = self._analyze_soldier_equipment(unit_data, unit)
                soldier_metrics[unit] = equipment_analysis
                
                # Generate alerts for this soldier
                unit_alerts = self._generate_equipment_alerts(equipment_analysis, unit)
                alerts.extend(unit_alerts)
            
            # Generate overall equipment analysis
            overall_metrics = self._calculate_overall_metrics(soldier_metrics)
            
            # Generate recommendations
            recommendations = self._generate_equipment_recommendations(
                soldier_metrics, overall_metrics
            )
            
            # Compile results
            metrics = {
                'soldier_metrics': {k: self._serialize_metrics(v) for k, v in soldier_metrics.items()},
                'overall_metrics': overall_metrics,
                'summary_statistics': self._calculate_summary_stats(data)
            }
            
            # Publish analysis completion event
            self.event_bus.publish({
                'type': 'analysis_completed',
                'domain': 'equipment',
                'metrics_count': len(soldier_metrics),
                'alerts_generated': len(alerts)
            })
            
            return AnalysisResult(
                domain=self.domain,
                metrics=metrics,
                alerts=alerts,
                recommendations=recommendations,
                confidence_score=0.93,
                analysis_timestamp=datetime.now()
            )
            
        except Exception as e:
            self.event_bus.publish({
                'type': 'analysis_error',
                'domain': 'equipment',
                'error': str(e)
            })
            raise

    def _serialize_metrics(self, metrics: EquipmentMetrics) -> Dict[str, Any]:
        """Convert EquipmentMetrics to serializable dict"""
        return {
            'soldier_id': metrics.soldier_id,
            'battery_metrics': {
                'soldier_id': metrics.battery_metrics.soldier_id,
                'current_level': metrics.battery_metrics.current_level,
                'min_level': metrics.battery_metrics.min_level,
                'max_level': metrics.battery_metrics.max_level,
                'avg_level': metrics.battery_metrics.avg_level,
                'depletion_rate': metrics.battery_metrics.depletion_rate,
                'estimated_remaining_hours': metrics.battery_metrics.estimated_remaining_hours,
                'critical_periods': metrics.battery_metrics.critical_periods,
                'status': metrics.battery_metrics.status.value
            },
            'power_consumption_patterns': metrics.power_consumption_patterns,
            'equipment_reliability_score': metrics.equipment_reliability_score,
            'malfunction_incidents': metrics.malfunction_incidents,
            'usage_patterns': metrics.usage_patterns,
            'maintenance_recommendations': metrics.maintenance_recommendations,
            'load_optimization_score': metrics.load_optimization_score
        }

    def _analyze_soldier_equipment(self, unit_data: pd.DataFrame, unit_id: str) -> EquipmentMetrics:
        """Analyze equipment performance for a single soldier"""
        
        # REQ-EQUIPMENT-001: Battery level monitoring and predictive analysis
        battery_metrics = self._analyze_battery_performance(unit_data, unit_id)
        
        # REQ-EQUIPMENT-002: Power consumption pattern analysis
        power_patterns = self._analyze_power_consumption_patterns(unit_data)
        
        # Equipment reliability analysis
        reliability_score = self._calculate_equipment_reliability(unit_data)
        
        # Detect malfunction incidents
        malfunctions = self._detect_equipment_malfunctions(unit_data)
        
        # Analyze usage patterns
        usage_patterns = self._analyze_usage_patterns(unit_data)
        
        # Generate maintenance recommendations
        maintenance_recs = self._generate_maintenance_recommendations(
            battery_metrics, power_patterns, reliability_score
        )
        
        # REQ-EQUIPMENT-008: Load-out optimization
        load_optimization = self._calculate_load_optimization_score(unit_data, power_patterns)
        
        return EquipmentMetrics(
            soldier_id=unit_id,
            battery_metrics=battery_metrics,
            power_consumption_patterns=power_patterns,
            equipment_reliability_score=reliability_score,
            malfunction_incidents=malfunctions,
            usage_patterns=usage_patterns,
            maintenance_recommendations=maintenance_recs,
            load_optimization_score=load_optimization
        )

    def _analyze_battery_performance(self, data: pd.DataFrame, unit_id: str) -> BatteryMetrics:
        """REQ-EQUIPMENT-001: Analyze battery performance and predict depletion"""
        
        # Handle missing battery data
        valid_battery = data['BatteryLevel'].dropna()
        if len(valid_battery) == 0:
            return BatteryMetrics(
                soldier_id=unit_id,
                current_level=0,
                min_level=0,
                max_level=0,
                avg_level=0,
                depletion_rate=0,
                estimated_remaining_hours=0,
                critical_periods=0,
                status=BatteryStatus.CRITICAL
            )
        
        # Calculate basic battery statistics
        current_level = valid_battery.iloc[-1] if len(valid_battery) > 0 else 0
        min_level = valid_battery.min()
        max_level = valid_battery.max()
        avg_level = valid_battery.mean()
        
        # Calculate depletion rate
        depletion_rate = self._calculate_depletion_rate(data)
        
        # Estimate remaining mission time
        estimated_hours = self._estimate_remaining_battery_life(current_level, depletion_rate)
        
        # Count critical periods (below 40%)
        critical_periods = (valid_battery < self.battery_thresholds['mission_critical']).sum()
        
        # Determine battery status
        status = self._classify_battery_status(current_level)
        
        return BatteryMetrics(
            soldier_id=unit_id,
            current_level=current_level,
            min_level=min_level,
            max_level=max_level,
            avg_level=avg_level,
            depletion_rate=depletion_rate,
            estimated_remaining_hours=estimated_hours,
            critical_periods=critical_periods,
            status=status
        )

    def _calculate_depletion_rate(self, data: pd.DataFrame) -> float:
        """Calculate battery depletion rate in % per hour"""
        
        valid_data = data.dropna(subset=['BatteryLevel', 'Timestamp'])
        if len(valid_data) < 2:
            return 0
        
        # Calculate time differences and battery changes
        time_diffs = []
        battery_changes = []
        
        for i in range(1, len(valid_data)):
            prev_row = valid_data.iloc[i-1]
            curr_row = valid_data.iloc[i]
            
            time_diff_hours = (curr_row['Timestamp'] - prev_row['Timestamp']).total_seconds() / 3600
            battery_change = prev_row['BatteryLevel'] - curr_row['BatteryLevel']  # Positive = depletion
            
            if time_diff_hours > 0 and battery_change >= 0:  # Only count depletion, not charging
                time_diffs.append(time_diff_hours)
                battery_changes.append(battery_change)
        
        if not time_diffs:
            return 0
        
        # Calculate weighted average depletion rate
        total_time = sum(time_diffs)
        total_depletion = sum(battery_changes)
        
        depletion_rate = total_depletion / total_time if total_time > 0 else 0
        
        return max(0, depletion_rate)  # Ensure non-negative

    def _estimate_remaining_battery_life(self, current_level: float, depletion_rate: float) -> float:
        """Estimate remaining battery life in hours"""
        
        if depletion_rate <= 0:
            return float('inf')  # No depletion detected
        
        # Calculate hours until critical level (20%)
        usable_capacity = max(0, current_level - self.battery_thresholds['critical'])
        remaining_hours = usable_capacity / depletion_rate
        
        return remaining_hours

    def _classify_battery_status(self, level: float) -> BatteryStatus:
        """Classify battery status based on current level"""
        
        if level >= self.battery_thresholds['good']:
            return BatteryStatus.EXCELLENT
        elif level >= self.battery_thresholds['moderate']:
            return BatteryStatus.GOOD
        elif level >= self.battery_thresholds['low']:
            return BatteryStatus.MODERATE
        elif level >= self.battery_thresholds['critical']:
            return BatteryStatus.LOW
        else:
            return BatteryStatus.CRITICAL

    def _analyze_power_consumption_patterns(self, data: pd.DataFrame) -> Dict[str, float]:
        """REQ-EQUIPMENT-002: Analyze power consumption by activity type"""
        
        patterns = {}
        
        # Correlate power consumption with activity levels
        if 'Steps' in data.columns:
            # Define activity levels
            data_with_activity = data.copy()
            data_with_activity['ActivityLevel'] = pd.cut(
                data['Steps'].fillna(0),
                bins=[0, 100, 200, 300, float('inf')],
                labels=['low', 'moderate', 'high', 'extreme']
            )
            
            # Calculate power consumption for each activity level
            for activity_level in ['low', 'moderate', 'high', 'extreme']:
                activity_data = data_with_activity[data_with_activity['ActivityLevel'] == activity_level]
                if len(activity_data) > 1:
                    consumption = self._calculate_power_consumption_for_period(activity_data)
                    patterns[f'{activity_level}_activity'] = consumption
                else:
                    patterns[f'{activity_level}_activity'] = 0
        
        # Analyze consumption during different operational states
        if 'CasualtyState' in data.columns:
            operational_data = data[data['CasualtyState'] == 'GOOD']
            casualty_data = data[data['CasualtyState'].isin(['KILLED', 'WOUNDED'])]
            
            patterns['operational_consumption'] = self._calculate_power_consumption_for_period(operational_data)
            patterns['casualty_consumption'] = self._calculate_power_consumption_for_period(casualty_data)
        
        return patterns

    def _calculate_power_consumption_for_period(self, data: pd.DataFrame) -> float:
        """Calculate power consumption rate for a specific period"""
        
        if len(data) < 2 or 'BatteryLevel' not in data.columns:
            return 0
        
        valid_data = data.dropna(subset=['BatteryLevel', 'Timestamp']).sort_values('Timestamp')
        if len(valid_data) < 2:
            return 0
        
        # Calculate total consumption and time
        start_battery = valid_data['BatteryLevel'].iloc[0]
        end_battery = valid_data['BatteryLevel'].iloc[-1]
        consumption = max(0, start_battery - end_battery)  # Only count depletion
        
        time_hours = (valid_data['Timestamp'].iloc[-1] - valid_data['Timestamp'].iloc[0]).total_seconds() / 3600
        
        if time_hours > 0:
            return consumption / time_hours
        else:
            return 0

    def _calculate_equipment_reliability(self, data: pd.DataFrame) -> float:
        """Calculate overall equipment reliability score"""
        
        reliability_factors = []
        
        # Battery reliability (based on data consistency)
        if 'BatteryLevel' in data.columns:
            battery_data = data['BatteryLevel'].dropna()
            if len(battery_data) > 0:
                # Check for impossible values
                impossible_values = ((battery_data < 0) | (battery_data > 101)).sum()
                battery_reliability = max(0, 100 - (impossible_values / len(battery_data)) * 100)
                reliability_factors.append(battery_reliability)
        
        # Network equipment reliability
        if all(col in data.columns for col in ['RSSI', 'MCS']):
            network_data = data.dropna(subset=['RSSI', 'MCS'])
            if len(network_data) > 0:
                # Check for reasonable ranges
                rssi_ok = ((network_data['RSSI'] >= -100) & (network_data['RSSI'] <= 0)).sum()
                mcs_ok = ((network_data['MCS'] >= 0) & (network_data['MCS'] <= 10)).sum()
                
                network_reliability = (rssi_ok + mcs_ok) / (len(network_data) * 2) * 100
                reliability_factors.append(network_reliability)
        
        # Overall reliability
        if reliability_factors:
            return np.mean(reliability_factors)
        else:
            return 50.0  # Neutral score if no data

    def _detect_equipment_malfunctions(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect potential equipment malfunction incidents"""
        
        malfunctions = []
        
        # Battery sensor malfunctions
        if 'BatteryLevel' in data.columns:
            battery_data = data.dropna(subset=['BatteryLevel', 'Timestamp']).sort_values('Timestamp')
            
            for i in range(1, len(battery_data)):
                prev_row = battery_data.iloc[i-1]
                curr_row = battery_data.iloc[i]
                
                # Check for sudden large changes
                battery_change = abs(curr_row['BatteryLevel'] - prev_row['BatteryLevel'])
                time_diff_minutes = (curr_row['Timestamp'] - prev_row['Timestamp']).total_seconds() / 60
                
                if battery_change > 30 and time_diff_minutes < 5:  # >30% change in <5 minutes
                    malfunctions.append({
                        'type': 'battery_sensor_malfunction',
                        'timestamp': curr_row['Timestamp'],
                        'severity': 'high',
                        'description': f"Sudden battery level change: {battery_change:.1f}% in {time_diff_minutes:.1f} minutes",
                        'values': {
                            'prev_level': prev_row['BatteryLevel'],
                            'curr_level': curr_row['BatteryLevel'],
                            'change': battery_change
                        }
                    })
        
        return malfunctions

    def _analyze_usage_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze equipment usage patterns"""
        
        patterns = {}
        
        # Time-based usage patterns
        if 'Timestamp' in data.columns:
            data_with_time = data.copy()
            data_with_time['Hour'] = data_with_time['Timestamp'].dt.hour
            
            # Usage by hour of day
            hourly_usage = data_with_time.groupby('Hour').size().to_dict()
            patterns['hourly_usage'] = hourly_usage
        
        # Activity-based usage
        if 'Steps' in data.columns:
            high_activity_periods = (data['Steps'] > 200).sum()
            total_periods = len(data.dropna(subset=['Steps']))
            
            patterns['high_activity_ratio'] = high_activity_periods / total_periods if total_periods > 0 else 0
        
        return patterns

    def _generate_maintenance_recommendations(self, battery_metrics: BatteryMetrics, 
                                           power_patterns: Dict[str, float],
                                           reliability_score: float) -> List[str]:
        """Generate maintenance recommendations based on analysis"""
        
        recommendations = []
        
        # Battery maintenance recommendations
        if battery_metrics.status in [BatteryStatus.CRITICAL, BatteryStatus.LOW]:
            recommendations.append(
                f"URGENT: Replace battery for {battery_metrics.soldier_id}. "
                f"Current level: {battery_metrics.current_level:.1f}%"
            )
        
        if battery_metrics.depletion_rate > 15:  # >15% per hour
            recommendations.append(
                f"Investigate high power consumption for {battery_metrics.soldier_id}. "
                f"Depletion rate: {battery_metrics.depletion_rate:.1f}%/hour"
            )
        
        # Equipment reliability recommendations
        if reliability_score < 80:
            recommendations.append(
                f"Schedule equipment inspection for {battery_metrics.soldier_id}. "
                f"Reliability score: {reliability_score:.1f}%"
            )
        
        return recommendations

    def _calculate_load_optimization_score(self, data: pd.DataFrame, 
                                         power_patterns: Dict[str, float]) -> float:
        """REQ-EQUIPMENT-008: Calculate load-out optimization score"""
        
        optimization_factors = []
        
        # Power efficiency factor
        avg_consumption = np.mean(list(power_patterns.values())) if power_patterns else 0
        if avg_consumption > 0:
            power_efficiency = max(0, 1 - (avg_consumption / 20))  # 20%/hour = poor efficiency
            optimization_factors.append(power_efficiency)
        
        # Equipment utilization factor
        if 'Steps' in data.columns:
            activity_data = data['Steps'].dropna()
            if len(activity_data) > 0:
                # Higher activity suggests good equipment utilization
                avg_activity = activity_data.mean()
                utilization_score = min(1.0, avg_activity / 300)  # 300 steps = good utilization
                optimization_factors.append(utilization_score)
        
        # Calculate composite optimization score
        if optimization_factors:
            return np.mean(optimization_factors)
        else:
            return 0.5  # Neutral score if no data

    def _generate_equipment_alerts(self, metrics: EquipmentMetrics, unit_id: str) -> List[Alert]:
        """Generate alerts based on equipment analysis"""
        
        alerts = []
        battery = metrics.battery_metrics
        
        # Critical battery alert
        if battery.status == BatteryStatus.CRITICAL:
            alerts.append(Alert(
                level=AlertLevel.CRITICAL,
                message=f"Unit {unit_id}: CRITICAL battery level ({battery.current_level:.1f}%)",
                domain=self.domain,
                timestamp=datetime.now(),
                details={
                    'current_level': battery.current_level,
                    'estimated_remaining_hours': battery.estimated_remaining_hours
                }
            ))
        
        # Low battery alert
        elif battery.status == BatteryStatus.LOW:
            alerts.append(Alert(
                level=AlertLevel.HIGH,
                message=f"Unit {unit_id}: Low battery level ({battery.current_level:.1f}%)",
                domain=self.domain,
                timestamp=datetime.now(),
                details={
                    'current_level': battery.current_level,
                    'estimated_remaining_hours': battery.estimated_remaining_hours
                }
            ))
        
        # High depletion rate alert
        if battery.depletion_rate > 15:  # >15% per hour
            alerts.append(Alert(
                level=AlertLevel.MEDIUM,
                message=f"Unit {unit_id}: High power consumption detected ({battery.depletion_rate:.1f}%/hour)",
                domain=self.domain,
                timestamp=datetime.now(),
                details={'depletion_rate': battery.depletion_rate}
            ))
        
        return alerts

    def _calculate_overall_metrics(self, soldier_metrics: Dict[str, EquipmentMetrics]) -> Dict[str, Any]:
        """Calculate overall equipment metrics across all soldiers"""
        
        if not soldier_metrics:
            return {}
        
        # Battery statistics
        battery_levels = [m.battery_metrics.current_level for m in soldier_metrics.values()]
        depletion_rates = [m.battery_metrics.depletion_rate for m in soldier_metrics.values()]
        
        # Equipment reliability statistics
        reliability_scores = [m.equipment_reliability_score for m in soldier_metrics.values()]
        
        # Status distribution
        status_distribution = {}
        for status in BatteryStatus:
            count = sum(1 for m in soldier_metrics.values() if m.battery_metrics.status == status)
            status_distribution[status.value] = count
        
        # Critical metrics
        critical_battery_count = sum(1 for m in soldier_metrics.values() 
                                   if m.battery_metrics.status == BatteryStatus.CRITICAL)
        
        return {
            'total_units': len(soldier_metrics),
            'battery_statistics': {
                'avg_level': np.mean(battery_levels),
                'min_level': np.min(battery_levels),
                'max_level': np.max(battery_levels),
                'avg_depletion_rate': np.mean(depletion_rates),
                'status_distribution': status_distribution
            },
            'reliability_statistics': {
                'avg_reliability': np.mean(reliability_scores),
                'min_reliability': np.min(reliability_scores),
                'units_below_threshold': sum(1 for score in reliability_scores if score < 80)
            },
            'fleet_status': {
                'critical_battery_units': critical_battery_count,
                'mission_ready_percentage': ((len(soldier_metrics) - critical_battery_count) / len(soldier_metrics)) * 100
            }
        }

    def _generate_equipment_recommendations(self, soldier_metrics: Dict[str, EquipmentMetrics],
                                          overall_metrics: Dict[str, Any]) -> List[str]:
        """Generate comprehensive equipment recommendations"""
        
        recommendations = []
        
        # Fleet-level recommendations
        fleet_status = overall_metrics.get('fleet_status', {})
        mission_ready_percentage = fleet_status.get('mission_ready_percentage', 100)
        
        if mission_ready_percentage < 80:
            recommendations.append(
                f"FLEET CRITICAL: Only {mission_ready_percentage:.1f}% of units mission-ready. "
                "Immediate equipment intervention required."
            )
        
        # Battery management recommendations
        battery_stats = overall_metrics.get('battery_statistics', {})
        avg_level = battery_stats.get('avg_level', 100)
        
        if avg_level < 50:
            recommendations.append(
                "FLEET BATTERY: Average battery level critically low. "
                "Implement emergency charging protocols."
            )
        
        # Individual unit recommendations
        critical_units = []
        for unit_id, metrics in soldier_metrics.items():
            if metrics.battery_metrics.status == BatteryStatus.CRITICAL:
                critical_units.append(unit_id)
        
        if critical_units:
            recommendations.append(
                f"IMMEDIATE ACTION: Replace batteries for units {', '.join(critical_units)}. "
                "Mission capability severely compromised."
            )
        
        return recommendations

    def _calculate_summary_stats(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics for the dataset"""
        
        return {
            'total_records': len(data),
            'unique_soldiers': data['Unit'].nunique(),
            'exercise_duration_minutes': len(data) / 60,
            'data_quality': {
                'battery_data_completeness': (1 - data['BatteryLevel'].isna().sum() / len(data)) * 100,
                'network_data_completeness': (1 - data[['RSSI', 'MCS']].isna().any(axis=1).sum() / len(data)) * 100,
                'sensor_data_completeness': (1 - data[['Steps', 'Posture']].isna().any(axis=1).sum() / len(data)) * 100
            },
            'battery_statistics': {
                'fleet_avg_level': data['BatteryLevel'].mean() if 'BatteryLevel' in data else 0,
                'fleet_min_level': data['BatteryLevel'].min() if 'BatteryLevel' in data else 0,
                'fleet_max_level': data['BatteryLevel'].max() if 'BatteryLevel' in data else 0,
                'critical_readings': (data['BatteryLevel'] < 20).sum() if 'BatteryLevel' in data else 0
            }
        }