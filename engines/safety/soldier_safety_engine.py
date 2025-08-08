# engines/soldier_safety_engine.py - Soldier Safety Analysis Engine
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging


from core.models import (
    AnalysisEngine, AnalysisDomain, AnalysisLevel, AnalysisResult, Alert, AlertLevel,
    DataQualityMetrics, UnitPerformance
)
from core.event_bus import EventBus, Event, EventType

class SoldierSafetyAnalysisEngine(AnalysisEngine):
    """
    Soldier Safety Analysis Engine
    Implements REQ-SAFETY-001 through REQ-SAFETY-008
    """
    
    def __init__(self, event_bus: EventBus = None):
        super().__init__(AnalysisDomain.SOLDIER_SAFETY)
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Subscribe to events if event bus is provided
        if self.event_bus:
            self.event_bus.subscribe(EventType.CONFIG_CHANGED, self.on_config_changed)
    
    def get_required_columns(self) -> List[str]:
        """Required columns for soldier safety analysis"""
        return [
            'callsign',
            'falldetected', 
            'casualtystate',
            'processedtimegmt'
        ]
    
    def get_optional_columns(self) -> List[str]:
        """Optional columns that enhance safety analysis"""
        return [
            'temp',
            'latitude',
            'longitude',
            'posture',
            'battery',
            'squad'
        ]
    
    def get_default_thresholds(self) -> Dict[str, Any]:
        """Default thresholds for safety analysis"""
        return {
            'high_fall_risk_threshold': 5,  # falls per unit
            'critical_fall_risk_threshold': 10,
            'heat_stress_threshold': 35,  # degrees Celsius
            'safety_score_critical': 50,
            'safety_score_warning': 70,
            'casualty_rate_warning': 0.15,  # 15%
            'casualty_rate_critical': 0.25,  # 25%
            'survival_time_minimum': 60  # seconds
        }
    
    def validate_data(self, data: pd.DataFrame) -> DataQualityMetrics:
        """Validate data quality for safety analysis"""
        metrics = DataQualityMetrics()
        metrics.total_records = len(data)
        
        # Check required columns
        missing_data = {}
        for col in self.required_columns:
            if col in data.columns:
                missing_count = data[col].isna().sum()
                missing_data[col] = (missing_count / len(data)) * 100
            else:
                missing_data[col] = 100.0
                metrics.validation_errors.append(f"Required column '{col}' is missing")
        
        metrics.missing_data_percentage = missing_data
        metrics.data_completeness = 100 - np.mean(list(missing_data.values()))
        
        # Validate data types and values
        if 'falldetected' in data.columns:
            valid_fall_values = {'Yes', 'No'}
            invalid_falls = ~data['falldetected'].isin(valid_fall_values)
            if invalid_falls.any():
                metrics.validation_errors.append(f"Invalid fall detection values found")
        
        if 'casualtystate' in data.columns:
            valid_casualty_states = {'GOOD', 'KILLED', 'FALL ALERT', 'RESURRECTED'}
            invalid_states = ~data['casualtystate'].isin(valid_casualty_states)
            if invalid_states.any():
                metrics.validation_errors.append(f"Invalid casualty states found")
        
        return metrics
    
    def analyze(self, data: pd.DataFrame, config: Dict[str, Any] = None) -> AnalysisResult:
        """
        Perform comprehensive soldier safety analysis
        """
        start_time = datetime.now()
        config = config or {}
        
        # Update thresholds if provided
        if 'thresholds' in config:
            self.update_thresholds(config['thresholds'])
        
        try:
            # Validate data
            data_quality = self.validate_data(data)
            
            if data_quality.data_completeness < 50:
                self.logger.warning(f"Low data completeness: {data_quality.data_completeness:.1f}%")
            
            # Perform analysis components
            results = {}
            alerts = []
            recommendations = []
            
            # REQ-SAFETY-001: Fall detection and response
            fall_analysis = self._analyze_falls(data)
            results['fall_analysis'] = fall_analysis
            alerts.extend(fall_analysis.get('alerts', []))
            
            # REQ-SAFETY-005: Casualty state transitions
            casualty_analysis = self._analyze_casualties(data)
            results['casualty_analysis'] = casualty_analysis
            alerts.extend(casualty_analysis.get('alerts', []))
            
            # REQ-SAFETY-003: Safety score calculation
            safety_scores = self._calculate_safety_scores(data)
            results['safety_scores'] = safety_scores
            alerts.extend(safety_scores.get('alerts', []))
            
            # REQ-SAFETY-008: Environmental correlation
            if 'temp' in data.columns:
                env_analysis = self._analyze_environmental_correlation(data)
                results['environmental_analysis'] = env_analysis
                alerts.extend(env_analysis.get('alerts', []))
            
            # REQ-SAFETY-007: Generate safety recommendations
            recommendations = self._generate_safety_recommendations(results)
            
            # Calculate overall metrics
            overall_metrics = self._calculate_overall_metrics(results, data)
            
            # Publish alerts if event bus is available
            if self.event_bus:
                for alert in alerts:
                    self._publish_alert(alert)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AnalysisResult(
                domain=self.domain,
                status="COMPLETED",
                metrics=overall_metrics,
                alerts=alerts,
                recommendations=recommendations,
                execution_time=execution_time,
                data_quality_score=data_quality.data_completeness
            )
            
        except Exception as e:
            self.logger.error(f"Error in soldier safety analysis: {e}")
            if self.event_bus:
                self.event_bus.publish(Event(
                    EventType.ERROR_OCCURRED,
                    {'domain': self.domain.value, 'error': str(e)},
                    source='SoldierSafetyAnalysisEngine'
                ))
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return AnalysisResult(
                domain=self.domain,
                status="FAILED",
                metrics={},
                alerts=[],
                recommendations=[],
                execution_time=execution_time
            )
    
    def _analyze_falls(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        REQ-SAFETY-001, REQ-SAFETY-002, REQ-SAFETY-004
        Fall detection monitoring and pattern analysis
        """
        fall_data = data[data['falldetected'] == 'Yes'] if 'falldetected' in data.columns else pd.DataFrame()
        
        analysis = {
            'total_falls': len(fall_data),
            'units_with_falls': fall_data['callsign'].nunique() if not fall_data.empty else 0,
            'fall_rate': len(fall_data) / len(data) * 100 if len(data) > 0 else 0,
            'falls_by_unit': {},
            'fall_casualty_correlation': {},
            'temporal_patterns': {},
            'alerts': []
        }
        
        if not fall_data.empty:
            # Falls by unit
            falls_by_unit = fall_data['callsign'].value_counts().to_dict()
            analysis['falls_by_unit'] = falls_by_unit
            
            # Correlate falls with casualty states
            for callsign in fall_data['callsign'].unique():
                unit_data = data[data['callsign'] == callsign]
                unit_falls = len(unit_data[unit_data['falldetected'] == 'Yes'])
                unit_casualties = len(unit_data[unit_data['casualtystate'].isin(['KILLED', 'FALL ALERT'])])
                
                analysis['fall_casualty_correlation'][callsign] = {
                    'falls': unit_falls,
                    'casualties': unit_casualties,
                    'correlation_ratio': unit_casualties / unit_falls if unit_falls > 0 else 0
                }
            
            # Temporal pattern analysis
            if 'processedtimegmt' in fall_data.columns:
                fall_data_copy = fall_data.copy()
                fall_data_copy['hour'] = pd.to_datetime(fall_data_copy['processedtimegmt']).dt.hour
                hourly_falls = fall_data_copy['hour'].value_counts().to_dict()
                analysis['temporal_patterns'] = {
                    'hourly_distribution': hourly_falls,
                    'peak_hour': max(hourly_falls.items(), key=lambda x: x[1]) if hourly_falls else None
                }
            
            # Generate alerts for high-risk units
            high_risk_units = [
                unit for unit, count in falls_by_unit.items() 
                if count >= self.thresholds['high_fall_risk_threshold']
            ]
            
            critical_risk_units = [
                unit for unit, count in falls_by_unit.items() 
                if count >= self.thresholds['critical_fall_risk_threshold']
            ]
            
            if critical_risk_units:
                analysis['alerts'].append(Alert(
                    alert_type='CRITICAL_FALL_RISK',
                    level=AlertLevel.CRITICAL,
                    message=f'Critical fall risk detected for units: {", ".join(critical_risk_units)}',
                    affected_units=critical_risk_units,
                    metric_value=max([falls_by_unit[unit] for unit in critical_risk_units]),
                    threshold=self.thresholds['critical_fall_risk_threshold']
                ))
            elif high_risk_units:
                analysis['alerts'].append(Alert(
                    alert_type='HIGH_FALL_RISK',
                    level=AlertLevel.WARNING,
                    message=f'High fall risk detected for units: {", ".join(high_risk_units)}',
                    affected_units=high_risk_units,
                    metric_value=max([falls_by_unit[unit] for unit in high_risk_units]),
                    threshold=self.thresholds['high_fall_risk_threshold']
                ))
        
        return analysis
    
    def _analyze_casualties(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        REQ-SAFETY-005, REQ-SAFETY-006, REQ-SAFETY-007
        Casualty state transitions and survival analysis
        """
        analysis = {
            'status_distribution': {},
            'transitions': {},
            'survival_times': {},
            'casualty_rate': 0,
            'resurrection_rate': 0,
            'alerts': []
        }
        
        if 'casualtystate' in data.columns:
            # Status distribution
            status_counts = data['casualtystate'].value_counts().to_dict()
            analysis['status_distribution'] = status_counts
            
            total_records = len(data)
            killed_records = status_counts.get('KILLED', 0)
            resurrected_records = status_counts.get('RESURRECTED', 0)
            
            analysis['casualty_rate'] = killed_records / total_records if total_records > 0 else 0
            analysis['resurrection_rate'] = resurrected_records / max(killed_records, 1)
            
            # Analyze state transitions per unit
            for callsign, unit_data in data.groupby('callsign'):
                sorted_data = unit_data.sort_values('processedtimegmt')
                transitions = []
                survival_periods = []
                
                prev_state = None
                state_start_time = None
                
                for _, row in sorted_data.iterrows():
                    current_state = row['casualtystate']
                    current_time = pd.to_datetime(row['processedtimegmt'])
                    
                    if prev_state != current_state:
                        if prev_state is not None:
                            transitions.append((prev_state, current_state, current_time))
                            
                            # Calculate survival time for GOOD -> KILLED transitions
                            if prev_state == 'GOOD' and current_state == 'KILLED' and state_start_time:
                                survival_time = (current_time - state_start_time).total_seconds()
                                survival_periods.append(survival_time)
                        
                        prev_state = current_state
                        state_start_time = current_time
                
                if transitions:
                    analysis['transitions'][callsign] = transitions
                
                if survival_periods:
                    analysis['survival_times'][callsign] = {
                        'mean': np.mean(survival_periods),
                        'min': min(survival_periods),
                        'max': max(survival_periods),
                        'count': len(survival_periods)
                    }
            
            # Generate alerts based on casualty rates
            if analysis['casualty_rate'] >= self.thresholds['casualty_rate_critical']:
                analysis['alerts'].append(Alert(
                    alert_type='CRITICAL_CASUALTY_RATE',
                    level=AlertLevel.CRITICAL,
                    message=f'Critical casualty rate: {analysis["casualty_rate"]*100:.1f}%',
                    metric_value=analysis['casualty_rate'],
                    threshold=self.thresholds['casualty_rate_critical']
                ))
            elif analysis['casualty_rate'] >= self.thresholds['casualty_rate_warning']:
                analysis['alerts'].append(Alert(
                    alert_type='HIGH_CASUALTY_RATE',
                    level=AlertLevel.WARNING,
                    message=f'High casualty rate: {analysis["casualty_rate"]*100:.1f}%',
                    metric_value=analysis['casualty_rate'],
                    threshold=self.thresholds['casualty_rate_warning']
                ))
            
            # Alert for low survival times
            avg_survival_times = [
                data['mean'] for data in analysis['survival_times'].values()
            ]
            if avg_survival_times:
                overall_avg_survival = np.mean(avg_survival_times)
                if overall_avg_survival < self.thresholds['survival_time_minimum']:
                    analysis['alerts'].append(Alert(
                        alert_type='LOW_SURVIVAL_TIME',
                        level=AlertLevel.WARNING,
                        message=f'Low average survival time: {overall_avg_survival:.1f}s',
                        metric_value=overall_avg_survival,
                        threshold=self.thresholds['survival_time_minimum']
                    ))
        
        return analysis
    
    def _calculate_safety_scores(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        REQ-SAFETY-003
        Calculate comprehensive safety scores for each unit
        """
        scores = {
            'unit_scores': {},
            'overall_score': 0,
            'score_distribution': {},
            'alerts': []
        }
        
        unit_scores = {}
        
        for callsign, unit_data in data.groupby('callsign'):
            score = 100  # Start with perfect score
            
            # Deduct for falls
            if 'falldetected' in unit_data.columns:
                falls = len(unit_data[unit_data['falldetected'] == 'Yes'])
                score -= min(falls * 5, 30)  # Max 30 point deduction for falls
            
            # Deduct for casualties
            if 'casualtystate' in unit_data.columns:
                casualties = len(unit_data[unit_data['casualtystate'].isin(['KILLED', 'FALL ALERT'])])
                score -= min(casualties * 10, 40)  # Max 40 point deduction for casualties
            
            # Deduct for environmental risks
            if 'temp' in unit_data.columns:
                temp_data = unit_data['temp'][unit_data['temp'] > -1]
                if not temp_data.empty and temp_data.mean() > self.thresholds['heat_stress_threshold']:
                    score -= 15  # Heat stress penalty
            
            # Deduct for equipment issues
            if 'battery' in unit_data.columns:
                battery_data = unit_data['battery'][unit_data['battery'] >= 0]
                if not battery_data.empty and battery_data.mean() < 20:
                    score -= 10  # Low battery penalty
            
            final_score = max(score, 0)
            unit_scores[callsign] = final_score
        
        scores['unit_scores'] = unit_scores
        
        if unit_scores:
            scores['overall_score'] = np.mean(list(unit_scores.values()))
            
            # Score distribution
            score_ranges = {'Excellent (90-100)': 0, 'Good (70-89)': 0, 'Fair (50-69)': 0, 'Poor (0-49)': 0}
            for score in unit_scores.values():
                if score >= 90:
                    score_ranges['Excellent (90-100)'] += 1
                elif score >= 70:
                    score_ranges['Good (70-89)'] += 1
                elif score >= 50:
                    score_ranges['Fair (50-69)'] += 1
                else:
                    score_ranges['Poor (0-49)'] += 1
            
            scores['score_distribution'] = score_ranges
            
            # Generate alerts for low safety scores
            critical_units = [unit for unit, score in unit_scores.items() 
                            if score <= self.thresholds['safety_score_critical']]
            warning_units = [unit for unit, score in unit_scores.items() 
                           if self.thresholds['safety_score_critical'] < score <= self.thresholds['safety_score_warning']]
            
            if critical_units:
                scores['alerts'].append(Alert(
                    alert_type='CRITICAL_SAFETY_SCORE',
                    level=AlertLevel.CRITICAL,
                    message=f'Critical safety scores for units: {", ".join(critical_units)}',
                    affected_units=critical_units,
                    threshold=self.thresholds['safety_score_critical']
                ))
            
            if warning_units:
                scores['alerts'].append(Alert(
                    alert_type='LOW_SAFETY_SCORE',
                    level=AlertLevel.WARNING,
                    message=f'Low safety scores for units: {", ".join(warning_units)}',
                    affected_units=warning_units,
                    threshold=self.thresholds['safety_score_warning']
                ))
        
        return scores
    
    def _analyze_environmental_correlation(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        REQ-SAFETY-008
        Analyze environmental factors affecting safety
        """
        analysis = {
            'temperature_analysis': {},
            'environmental_alerts': [],
            'correlations': {},
            'alerts': []
        }
        
        if 'temp' in data.columns:
            temp_data = data[data['temp'] > -1]  # Valid temperature readings
            
            if not temp_data.empty:
                analysis['temperature_analysis'] = {
                    'mean_temp': temp_data['temp'].mean(),
                    'max_temp': temp_data['temp'].max(),
                    'min_temp': temp_data['temp'].min(),
                    'heat_stress_records': len(temp_data[temp_data['temp'] > self.thresholds['heat_stress_threshold']])
                }
                
                # Correlate temperature with casualties and falls
                if 'casualtystate' in data.columns:
                    casualty_temps = temp_data[temp_data['casualtystate'] == 'KILLED']['temp']
                    normal_temps = temp_data[temp_data['casualtystate'] == 'GOOD']['temp']
                    
                    if len(casualty_temps) > 0 and len(normal_temps) > 0:
                        correlation = np.corrcoef(
                            temp_data['temp'], 
                            temp_data['casualtystate'].map({'GOOD': 0, 'KILLED': 1, 'FALL ALERT': 0.5, 'RESURRECTED': 0})
                        )[0, 1]
                        analysis['correlations']['temp_casualty'] = correlation
                
                # Heat stress alert
                if analysis['temperature_analysis']['heat_stress_records'] > 0:
                    analysis['alerts'].append(Alert(
                        alert_type='HEAT_STRESS_DETECTED',
                        level=AlertLevel.WARNING,
                        message=f'Heat stress conditions detected: {analysis["temperature_analysis"]["heat_stress_records"]} records above {self.thresholds["heat_stress_threshold"]}°C',
                        metric_value=analysis['temperature_analysis']['max_temp'],
                        threshold=self.thresholds['heat_stress_threshold']
                    ))
        
        return analysis
    
    def _generate_safety_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """
        REQ-SAFETY-007
        Generate safety recommendations based on analysis
        """
        recommendations = []
        
        # Fall-based recommendations
        fall_analysis = results.get('fall_analysis', {})
        if fall_analysis.get('total_falls', 0) > 10:
            recommendations.append(
                "PRIORITY: Implement enhanced fall prevention training and safety protocols"
            )
        
        # Casualty-based recommendations
        casualty_analysis = results.get('casualty_analysis', {})
        if casualty_analysis.get('casualty_rate', 0) > 0.2:
            recommendations.append(
                "CRITICAL: Review tactical procedures to reduce casualty rates"
            )
        
        # Environmental recommendations
        env_analysis = results.get('environmental_analysis', {})
        if env_analysis.get('temperature_analysis', {}).get('heat_stress_records', 0) > 0:
            recommendations.append(
                "Implement heat stress mitigation protocols and hydration schedules"
            )
        
        # Safety score recommendations
        safety_scores = results.get('safety_scores', {})
        if safety_scores.get('overall_score', 100) < 70:
            recommendations.append(
                "Conduct comprehensive safety review and implement corrective measures"
            )
        
        if not recommendations:
            recommendations.append(
                "Safety performance within acceptable parameters - continue current protocols"
            )
        
        return recommendations
    
    def _calculate_overall_metrics(self, results: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate overall safety metrics for the domain"""
        return {
            'total_units': data['callsign'].nunique(),
            'total_falls': results.get('fall_analysis', {}).get('total_falls', 0),
            'casualty_rate': results.get('casualty_analysis', {}).get('casualty_rate', 0),
            'overall_safety_score': results.get('safety_scores', {}).get('overall_score', 0),
            'high_risk_units': len([
                unit for unit, score in results.get('safety_scores', {}).get('unit_scores', {}).items()
                if score < self.thresholds['safety_score_warning']
            ]),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _publish_alert(self, alert: Alert):
        """Publish alert through event bus"""
        if self.event_bus:
            self.event_bus.publish(Event(
                EventType.ALERT_TRIGGERED,
                {
                    'domain': self.domain.value,
                    'alert_type': alert.alert_type,
                    'level': alert.level.value,
                    'message': alert.message,
                    'affected_units': alert.affected_units,
                    'metric_value': alert.metric_value,
                    'threshold': alert.threshold
                },
                source='SoldierSafetyAnalysisEngine'
            ))
    
    def on_config_changed(self, event: Event):
        """Handle configuration changes"""
        config_data = event.data
        if 'safety_thresholds' in config_data:
            self.update_thresholds(config_data['safety_thresholds'])
            self.logger.info("Safety analysis thresholds updated")
    
    def get_analysis_capabilities(self) -> Dict[str, Any]:
        """Return capabilities for this analysis engine"""
        capabilities = super().get_analysis_capabilities()
        capabilities.update({
            'supported_levels': [level.value for level in [AnalysisLevel.INDIVIDUAL, AnalysisLevel.SQUAD, AnalysisLevel.PLATOON]],
            'real_time_capable': True,
            'alert_types': [
                'HIGH_FALL_RISK',
                'CRITICAL_FALL_RISK', 
                'HIGH_CASUALTY_RATE',
                'CRITICAL_CASUALTY_RATE',
                'LOW_SURVIVAL_TIME',
                'CRITICAL_SAFETY_SCORE',
                'LOW_SAFETY_SCORE',
                'HEAT_STRESS_DETECTED'
            ],
            'metrics_provided': [
                'fall_count',
                'casualty_rate',
                'safety_score',
                'survival_time',
                'environmental_risk'
            ]
        })
        return capabilities