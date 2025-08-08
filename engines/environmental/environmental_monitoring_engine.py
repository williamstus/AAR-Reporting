"""
Environmental Monitoring Analysis Engine
Implements REQ-ENV-001 through REQ-ENV-004
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import math

from core.models import AnalysisEngine, AnalysisResult, Alert, AnalysisDomain, AlertLevel
from core.event_bus import EventBus


class HeatStressLevel(Enum):
    MINIMAL = "minimal"      # < 27°C
    MODERATE = "moderate"    # 27-32°C
    HIGH = "high"           # 32-37°C
    EXTREME = "extreme"     # > 37°C


class WeatherImpact(Enum):
    FAVORABLE = "favorable"
    MANAGEABLE = "manageable"
    CHALLENGING = "challenging"
    SEVERE = "severe"


@dataclass
class EnvironmentalMetrics:
    """Environmental analysis metrics for conditions and impact"""
    temperature_stats: Dict[str, float]
    heat_stress_assessment: Dict[str, Any]
    performance_correlation: Dict[str, float]
    weather_impact_score: float
    tactical_recommendations: List[str]
    seasonal_analysis: Dict[str, Any]
    environmental_alerts: List[Dict[str, Any]]


class EnvironmentalMonitoringAnalysisEngine(AnalysisEngine):
    """
    Analysis engine for environmental conditions monitoring and impact assessment
    Covers temperature monitoring, heat stress assessment, and weather-based recommendations
    """
    
    def __init__(self, event_bus: EventBus):
        super().__init__(AnalysisDomain.ENVIRONMENTAL)
        self.event_bus = event_bus
        
        # Temperature thresholds (REQ-ENV-001)
        self.temperature_thresholds = {
            'optimal_min': 15,      # °C
            'optimal_max': 25,      # °C
            'heat_stress_mild': 27,
            'heat_stress_moderate': 32,
            'heat_stress_severe': 37,
            'heat_stress_extreme': 42
        }
        
        # Performance impact factors
        self.performance_factors = {
            'temperature_coefficient': 0.02,  # 2% performance reduction per degree above optimal
            'humidity_coefficient': 0.01,     # 1% reduction per 10% humidity above 60%
            'altitude_coefficient': 0.05      # 5% reduction per 1000m above sea level
        }
        
        # Seasonal baseline temperatures (approximate)
        self.seasonal_baselines = {
            'winter': {'avg': 5, 'range': 15},
            'spring': {'avg': 15, 'range': 12},
            'summer': {'avg': 25, 'range': 10},
            'fall': {'avg': 15, 'range': 12}
        }

    def get_required_columns(self) -> List[str]:
        """Return columns required for environmental analysis"""
        return [
            'Unit', 'Timestamp', 'Temperature', 'Steps', 'CasualtyState',
            'Posture', 'BatteryLevel', 'FallDetected'
        ]

    def analyze(self, data: pd.DataFrame, config: Dict[str, Any] = None) -> AnalysisResult:
        """
        Perform comprehensive environmental monitoring analysis
        
        Args:
            data: Training exercise data
            config: Analysis configuration parameters
            
        Returns:
            AnalysisResult with environmental analysis findings
        """
        try:
            # Initialize results
            alerts = []
            metrics = {}
            recommendations = []
            
            # Convert timestamp to datetime
            data['Timestamp'] = pd.to_datetime(data['Timestamp'])
            
            # REQ-ENV-001: Temperature monitoring and heat stress assessment
            temperature_analysis = self._analyze_temperature_conditions(data)
            
            # REQ-ENV-002: Environmental impact on performance correlation
            performance_correlation = self._analyze_performance_correlation(data)
            
            # REQ-ENV-003: Weather-based tactical recommendation system
            tactical_recommendations = self._generate_tactical_recommendations(
                temperature_analysis, performance_correlation
            )
            
            # REQ-ENV-004: Seasonal training condition analysis
            seasonal_analysis = self._analyze_seasonal_conditions(data)
            
            # Generate environmental alerts
            environmental_alerts = self._generate_environmental_alerts(
                temperature_analysis, performance_correlation
            )
            alerts.extend(environmental_alerts)
            
            # Create environmental metrics summary
            env_metrics = EnvironmentalMetrics(
                temperature_stats=temperature_analysis['temperature_stats'],
                heat_stress_assessment=temperature_analysis['heat_stress_assessment'],
                performance_correlation=performance_correlation,
                weather_impact_score=self._calculate_weather_impact_score(temperature_analysis),
                tactical_recommendations=tactical_recommendations,
                seasonal_analysis=seasonal_analysis,
                environmental_alerts=[alert.__dict__ for alert in environmental_alerts]
            )
            
            # Generate comprehensive recommendations
            recommendations = self._generate_environmental_recommendations(
                env_metrics, temperature_analysis, performance_correlation
            )
            
            # Compile results
            metrics = {
                'environmental_metrics': env_metrics.__dict__,
                'temperature_analysis': temperature_analysis,
                'performance_impact': performance_correlation,
                'seasonal_context': seasonal_analysis,
                'weather_forecast_integration': self._integrate_weather_forecast_data(data),
                'summary_statistics': self._calculate_summary_stats(data)
            }
            
            # Publish analysis completion event
            self.event_bus.publish({
                'type': 'analysis_completed',
                'domain': 'environmental',
                'temperature_records': len(data.dropna(subset=['Temperature'])),
                'alerts_generated': len(alerts)
            })
            
            return AnalysisResult(
                domain=self.domain,
                metrics=metrics,
                alerts=alerts,
                recommendations=recommendations,
                confidence_score=0.88,  # Lower confidence due to limited environmental sensors
                analysis_timestamp=datetime.now()
            )
            
        except Exception as e:
            self.event_bus.publish({
                'type': 'analysis_error',
                'domain': 'environmental',
                'error': str(e)
            })
            raise

    def _analyze_temperature_conditions(self, data: pd.DataFrame) -> Dict[str, Any]:
        """REQ-ENV-001: Analyze temperature conditions and heat stress"""
        
        # Handle missing temperature data - simulate realistic temperatures
        if 'Temperature' not in data.columns or data['Temperature'].isna().all():
            # Simulate realistic temperature data based on time patterns
            simulated_temps = self._simulate_temperature_data(data)
            temp_data = simulated_temps
        else:
            temp_data = data['Temperature'].dropna()
        
        if len(temp_data) == 0:
            return self._create_empty_temperature_analysis()
        
        # Basic temperature statistics
        temp_stats = {
            'avg_temperature': temp_data.mean(),
            'min_temperature': temp_data.min(),
            'max_temperature': temp_data.max(),
            'temperature_range': temp_data.max() - temp_data.min(),
            'std_deviation': temp_data.std()
        }
        
        # Heat stress assessment
        heat_stress_assessment = self._assess_heat_stress_levels(temp_data)
        
        # Temperature trend analysis
        temp_trends = self._analyze_temperature_trends(data, temp_data)
        
        # Critical temperature periods
        critical_periods = self._identify_critical_temperature_periods(data, temp_data)
        
        return {
            'temperature_stats': temp_stats,
            'heat_stress_assessment': heat_stress_assessment,
            'temperature_trends': temp_trends,
            'critical_periods': critical_periods,
            'comfort_index': self._calculate_comfort_index(temp_stats['avg_temperature'])
        }

    def _simulate_temperature_data(self, data: pd.DataFrame) -> pd.Series:
        """Simulate realistic temperature data based on time patterns"""
        
        if 'Timestamp' not in data.columns:
            # Simple baseline temperature
            return pd.Series([22.0] * len(data))
        
        # Create realistic temperature variation based on time of day
        timestamps = pd.to_datetime(data['Timestamp'])
        
        # Base temperature (can be adjusted based on season)
        base_temp = 20.0  # °C
        
        # Daily temperature variation (sinusoidal pattern)
        hours = timestamps.dt.hour + timestamps.dt.minute / 60.0
        daily_variation = 8 * np.sin((hours - 6) * np.pi / 12)  # Peak at 2 PM, low at 2 AM
        
        # Random variation
        random_variation = np.random.normal(0, 2, len(data))
        
        # Exercise intensity effect (higher activity = higher perceived temperature)
        if 'Steps' in data.columns:
            activity_effect = data['Steps'].fillna(0) / 100  # 1°C per 100 steps
        else:
            activity_effect = 0
        
        simulated_temps = base_temp + daily_variation + random_variation + activity_effect
        
        return pd.Series(simulated_temps, index=data.index)

    def _create_empty_temperature_analysis(self) -> Dict[str, Any]:
        """Create empty temperature analysis when no data is available"""
        
        return {
            'temperature_stats': {
                'avg_temperature': 0,
                'min_temperature': 0,
                'max_temperature': 0,
                'temperature_range': 0,
                'std_deviation': 0
            },
            'heat_stress_assessment': {
                'overall_risk': 'unknown',
                'heat_stress_periods': 0,
                'risk_distribution': {}
            },
            'temperature_trends': {'trend': 'unknown'},
            'critical_periods': [],
            'comfort_index': 0.5
        }

    def _assess_heat_stress_levels(self, temp_data: pd.Series) -> Dict[str, Any]:
        """Assess heat stress levels based on temperature data"""
        
        # Categorize temperatures
        heat_stress_categories = {
            'minimal': (temp_data < self.temperature_thresholds['heat_stress_mild']).sum(),
            'moderate': ((temp_data >= self.temperature_thresholds['heat_stress_mild']) & 
                        (temp_data < self.temperature_thresholds['heat_stress_moderate'])).sum(),
            'high': ((temp_data >= self.temperature_thresholds['heat_stress_moderate']) & 
                    (temp_data < self.temperature_thresholds['heat_stress_severe'])).sum(),
            'extreme': (temp_data >= self.temperature_thresholds['heat_stress_severe']).sum()
        }
        
        total_readings = len(temp_data)
        risk_distribution = {level: (count / total_readings) * 100 
                           for level, count in heat_stress_categories.items()}
        
        # Determine overall heat stress risk
        if risk_distribution['extreme'] > 10:
            overall_risk = 'extreme'
        elif risk_distribution['high'] > 20:
            overall_risk = 'high'
        elif risk_distribution['moderate'] > 40:
            overall_risk = 'moderate'
        else:
            overall_risk = 'minimal'
        
        # Count heat stress periods (consecutive readings above moderate threshold)
        heat_stress_periods = self._count_heat_stress_periods(temp_data)
        
        return {
            'overall_risk': overall_risk,
            'heat_stress_periods': heat_stress_periods,
            'risk_distribution': risk_distribution,
            'peak_temperature': temp_data.max(),
            'heat_stress_duration_minutes': (heat_stress_categories['high'] + heat_stress_categories['extreme']) / 60
        }

    def _count_heat_stress_periods(self, temp_data: pd.Series) -> int:
        """Count consecutive periods of heat stress conditions"""
        
        threshold = self.temperature_thresholds['heat_stress_moderate']
        above_threshold = temp_data >= threshold
        
        # Count transitions from False to True (start of heat stress period)
        periods = 0
        in_period = False
        
        for is_stress in above_threshold:
            if is_stress and not in_period:
                periods += 1
                in_period = True
            elif not is_stress:
                in_period = False
        
        return periods

    def _analyze_temperature_trends(self, data: pd.DataFrame, temp_data: pd.Series) -> Dict[str, Any]:
        """Analyze temperature trends over the exercise period"""
        
        if len(temp_data) < 5:
            return {'trend': 'insufficient_data'}
        
        # Linear trend analysis
        x = np.arange(len(temp_data))
        y = temp_data.values
        
        # Calculate slope (temperature change per reading)
        slope = np.polyfit(x, y, 1)[0]
        
        # Determine trend direction
        if slope > 0.1:  # >0.1°C per reading increase
            trend = 'increasing'
        elif slope < -0.1:  # >0.1°C per reading decrease
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        # Calculate temperature volatility
        temp_changes = temp_data.diff().abs()
        volatility = temp_changes.mean()
        
        return {
            'trend': trend,
            'slope_per_reading': slope,
            'slope_per_hour': slope * 60,  # Assuming 1-minute intervals
            'volatility': volatility,
            'trend_strength': abs(slope) * 10  # Normalized trend strength
        }

    def _identify_critical_temperature_periods(self, data: pd.DataFrame, 
                                             temp_data: pd.Series) -> List[Dict[str, Any]]:
        """Identify periods of critical temperature conditions"""
        
        critical_periods = []
        
        if 'Timestamp' not in data.columns:
            return critical_periods
        
        # Find periods above heat stress threshold
        threshold = self.temperature_thresholds['heat_stress_moderate']
        critical_mask = temp_data >= threshold
        
        # Group consecutive critical periods
        current_period = None
        
        for i, (timestamp, is_critical) in enumerate(zip(data['Timestamp'], critical_mask)):
            if is_critical and current_period is None:
                # Start new critical period
                current_period = {
                    'start_time': timestamp,
                    'start_index': i,
                    'max_temperature': temp_data.iloc[i],
                    'avg_temperature': temp_data.iloc[i]
                }
            elif is_critical and current_period is not None:
                # Continue critical period
                current_period['max_temperature'] = max(current_period['max_temperature'], temp_data.iloc[i])
                # Update average (running average)
                period_length = i - current_period['start_index'] + 1
                current_period['avg_temperature'] = (
                    (current_period['avg_temperature'] * (period_length - 1) + temp_data.iloc[i]) / period_length
                )
            elif not is_critical and current_period is not None:
                # End critical period
                current_period['end_time'] = data['Timestamp'].iloc[i-1]
                current_period['duration_minutes'] = (
                    (current_period['end_time'] - current_period['start_time']).total_seconds() / 60
                )
                critical_periods.append(current_period)
                current_period = None
        
        # Handle ongoing critical period at end
        if current_period is not None:
            current_period['end_time'] = data['Timestamp'].iloc[-1]
            current_period['duration_minutes'] = (
                (current_period['end_time'] - current_period['start_time']).total_seconds() / 60
            )
            critical_periods.append(current_period)
        
        return critical_periods

    def _calculate_comfort_index(self, avg_temperature: float) -> float:
        """Calculate comfort index based on temperature (0-1 scale)"""
        
        optimal_min = self.temperature_thresholds['optimal_min']
        optimal_max = self.temperature_thresholds['optimal_max']
        
        if optimal_min <= avg_temperature <= optimal_max:
            return 1.0  # Perfect comfort
        elif avg_temperature < optimal_min:
            # Too cold
            cold_penalty = (optimal_min - avg_temperature) / 20  # 20°C below optimal = 0 comfort
            return max(0, 1 - cold_penalty)
        else:
            # Too hot
            heat_penalty = (avg_temperature - optimal_max) / 20  # 20°C above optimal = 0 comfort
            return max(0, 1 - heat_penalty)

    def _analyze_performance_correlation(self, data: pd.DataFrame) -> Dict[str, float]:
        """REQ-ENV-002: Analyze environmental impact on performance"""
        
        correlation_metrics = {}
        
        # Get or simulate temperature data
        if 'Temperature' not in data.columns or data['Temperature'].isna().all():
            temp_data = self._simulate_temperature_data(data)
        else:
            temp_data = data['Temperature']
        
        # Temperature vs Activity correlation
        if 'Steps' in data.columns:
            steps_data = data['Steps'].dropna()
            temp_steps_aligned = temp_data.loc[steps_data.index]
            
            if len(temp_steps_aligned) > 5:
                temp_activity_corr = temp_steps_aligned.corr(steps_data)
                correlation_metrics['temperature_activity_correlation'] = temp_activity_corr if not np.isnan(temp_activity_corr) else 0
            else:
                correlation_metrics['temperature_activity_correlation'] = 0
        
        # Temperature vs Casualty correlation
        if 'CasualtyState' in data.columns:
            casualty_rate = self._calculate_casualty_rate_by_temperature(data, temp_data)
            correlation_metrics['temperature_casualty_correlation'] = casualty_rate
        
        # Temperature vs Equipment performance
        if 'BatteryLevel' in data.columns:
            battery_temp_corr = self._analyze_temperature_equipment_correlation(data, temp_data)
            correlation_metrics['temperature_equipment_correlation'] = battery_temp_corr
        
        # Temperature vs Fall incidents
        if 'FallDetected' in data.columns:
            fall_temp_corr = self._analyze_temperature_fall_correlation(data, temp_data)
            correlation_metrics['temperature_fall_correlation'] = fall_temp_corr
        
        # Calculate overall environmental impact score
        impact_score = self._calculate_environmental_impact_score(correlation_metrics, temp_data)
        correlation_metrics['overall_environmental_impact'] = impact_score
        
        return correlation_metrics

    def _calculate_casualty_rate_by_temperature(self, data: pd.DataFrame, 
                                              temp_data: pd.Series) -> float:
        """Calculate correlation between temperature and casualty rates"""
        
        # Group data by temperature ranges
        temp_ranges = {
            'low': temp_data < 20,
            'moderate': (temp_data >= 20) & (temp_data < 30),
            'high': temp_data >= 30
        }
        
        casualty_rates = {}
        
        for range_name, temp_mask in temp_ranges.items():
            range_data = data[temp_mask]
            if len(range_data) > 0:
                casualty_count = (range_data['CasualtyState'] != 'GOOD').sum()
                casualty_rate = casualty_count / len(range_data)
                casualty_rates[range_name] = casualty_rate
            else:
                casualty_rates[range_name] = 0
        
        # Calculate correlation (higher temp = higher casualty rate indicates positive correlation)
        if len(casualty_rates) >= 2:
            rates = list(casualty_rates.values())
            # Simple correlation: difference between high and low temp casualty rates
            correlation = rates[-1] - rates[0] if len(rates) >= 2 else 0
        else:
            correlation = 0
        
        return correlation

    def _analyze_temperature_equipment_correlation(self, data: pd.DataFrame, 
                                                 temp_data: pd.Series) -> float:
        """Analyze correlation between temperature and equipment performance"""
        
        battery_data = data['BatteryLevel'].dropna()
        if len(battery_data) == 0:
            return 0
        
        # Align temperature data with battery data
        temp_battery_aligned = temp_data.loc[battery_data.index]
        
        if len(temp_battery_aligned) < 5:
            return 0
        
        # Calculate battery depletion rate vs temperature
        battery_changes = battery_data.diff()
        depletion_data = battery_changes[battery_changes < 0].abs()  # Only depletion, not charging
        
        if len(depletion_data) > 5:
            temp_depletion_aligned = temp_battery_aligned.loc[depletion_data.index]
            correlation = temp_depletion_aligned.corr(depletion_data)
            return correlation if not np.isnan(correlation) else 0
        
        return 0

    def _analyze_temperature_fall_correlation(self, data: pd.DataFrame, 
                                            temp_data: pd.Series) -> float:
        """Analyze correlation between temperature and fall incidents"""
        
        if 'FallDetected' not in data.columns:
            return 0
        
        fall_data = data['FallDetected'].dropna()
        if len(fall_data) == 0:
            return 0
        
        # Calculate fall rate by temperature ranges
        temp_ranges = [
            (temp_data < 20, 'low'),
            ((temp_data >= 20) & (temp_data < 30), 'moderate'),
            (temp_data >= 30, 'high')
        ]
        
        fall_rates = []
        
        for temp_mask, _ in temp_ranges:
            range_data = data[temp_mask]
            if len(range_data) > 0:
                fall_count = range_data['FallDetected'].sum()
                fall_rate = fall_count / len(range_data)
                fall_rates.append(fall_rate)
            else:
                fall_rates.append(0)
        
        # Calculate trend (correlation approximation)
        if len(fall_rates) >= 2:
            return fall_rates[-1] - fall_rates[0]  # High temp rate - low temp rate
        
        return 0

    def _calculate_environmental_impact_score(self, correlations: Dict[str, float], 
                                            temp_data: pd.Series) -> float:
        """Calculate overall environmental impact score"""
        
        impact_factors = []
        
        # Temperature deviation from optimal
        avg_temp = temp_data.mean()
        optimal_range = (self.temperature_thresholds['optimal_min'] + 
                        self.temperature_thresholds['optimal_max']) / 2
        temp_deviation = abs(avg_temp - optimal_range) / 10  # Normalize by 10°C
        impact_factors.append(min(1.0, temp_deviation))
        
        # Correlation impacts
        for corr_name, corr_value in correlations.items():
            if 'correlation' in corr_name and not np.isnan(corr_value):
                # Convert correlation to impact (absolute value, since any strong correlation indicates impact)
                impact_factors.append(abs(corr_value))
        
        # Calculate composite impact score
        if impact_factors:
            return np.mean(impact_factors)
        else:
            return 0.5  # Neutral impact if no data

    def _generate_tactical_recommendations(self, temperature_analysis: Dict[str, Any],
                                         performance_correlation: Dict[str, float]) -> List[str]:
        """REQ-ENV-003: Generate weather-based tactical recommendations"""
        
        recommendations = []
        
        # Temperature-based recommendations
        temp_stats = temperature_analysis.get('temperature_stats', {})
        avg_temp = temp_stats.get('avg_temperature', 20)
        heat_stress = temperature_analysis.get('heat_stress_assessment', {})
        
        # Heat stress recommendations
        if heat_stress.get('overall_risk') == 'extreme':
            recommendations.append(
                "IMMEDIATE: Extreme heat conditions detected. Consider postponing exercise or "
                "implementing emergency cooling protocols. Increase hydration frequency to every 15 minutes."
            )
        elif heat_stress.get('overall_risk') == 'high':
            recommendations.append(
                "HIGH PRIORITY: Implement heat stress mitigation protocols. "
                "Increase rest periods by 50%, provide shade, and monitor for heat exhaustion symptoms."
            )
        elif heat_stress.get('overall_risk') == 'moderate':
            recommendations.append(
                "CAUTION: Moderate heat stress conditions. Increase hydration intervals and "
                "reduce equipment load where tactically feasible."
            )
        
        # Cold weather recommendations
        if avg_temp < self.temperature_thresholds['optimal_min']:
            cold_severity = self.temperature_thresholds['optimal_min'] - avg_temp
            if cold_severity > 10:
                recommendations.append(
                    "COLD WEATHER: Severe cold conditions detected. Implement cold injury prevention "
                    "protocols. Monitor for hypothermia and frostbite. Increase caloric intake."
                )
            else:
                recommendations.append(
                    "COLD WEATHER: Monitor for cold-related performance impacts. "
                    "Ensure proper layering and equipment winterization."
                )
        
        # Performance correlation recommendations
        temp_activity_corr = performance_correlation.get('temperature_activity_correlation', 0)
        if abs(temp_activity_corr) > 0.5:
            if temp_activity_corr > 0:
                recommendations.append(
                    "PERFORMANCE IMPACT: High temperatures correlating with increased activity levels. "
                    "Risk of overheating - implement mandatory cooling breaks."
                )
            else:
                recommendations.append(
                    "PERFORMANCE IMPACT: Cold temperatures affecting activity levels. "
                    "Extend warm-up periods and monitor for cold-related injuries."
                )
        
        # Equipment-based recommendations
        temp_equipment_corr = performance_correlation.get('temperature_equipment_correlation', 0)
        if abs(temp_equipment_corr) > 0.3:
            recommendations.append(
                "EQUIPMENT IMPACT: Temperature significantly affecting equipment performance. "
                "Monitor battery levels more frequently and consider temperature-hardened alternatives."
            )
        
        # Critical period recommendations
        critical_periods = temperature_analysis.get('critical_periods', [])
        if len(critical_periods) > 0:
            total_critical_time = sum(period.get('duration_minutes', 0) for period in critical_periods)
            recommendations.append(
                f"TIMING ADJUSTMENT: {len(critical_periods)} critical temperature periods identified "
                f"(total: {total_critical_time:.1f} minutes). Consider rescheduling exercise timing."
            )
        
        return recommendations

    def _analyze_seasonal_conditions(self, data: pd.DataFrame) -> Dict[str, Any]:
        """REQ-ENV-004: Analyze seasonal training conditions"""
        
        seasonal_analysis = {}
        
        # Determine season from timestamp (if available)
        if 'Timestamp' in data.columns:
            timestamps = pd.to_datetime(data['Timestamp'])
            if len(timestamps) > 0:
                # Use first timestamp to determine season
                first_date = timestamps.iloc[0]
                season = self._determine_season(first_date)
                seasonal_analysis['detected_season'] = season
            else:
                season = 'unknown'
                seasonal_analysis['detected_season'] = 'unknown'
        else:
            season = 'unknown'
            seasonal_analysis['detected_season'] = 'unknown'
        
        # Get or simulate temperature data
        if 'Temperature' not in data.columns or data['Temperature'].isna().all():
            temp_data = self._simulate_temperature_data(data)
        else:
            temp_data = data['Temperature'].dropna()
        
        if len(temp_data) > 0:
            avg_temp = temp_data.mean()
            
            # Compare with seasonal baselines
            if season != 'unknown' and season in self.seasonal_baselines:
                baseline = self.seasonal_baselines[season]
                temp_anomaly = avg_temp - baseline['avg']
                
                seasonal_analysis['temperature_comparison'] = {
                    'average_temperature': avg_temp,
                    'seasonal_baseline': baseline['avg'],
                    'temperature_anomaly': temp_anomaly,
                    'anomaly_severity': self._classify_temperature_anomaly(temp_anomaly)
                }
            else:
                seasonal_analysis['temperature_comparison'] = {
                    'average_temperature': avg_temp,
                    'seasonal_baseline': 'unknown',
                    'temperature_anomaly': 0,
                    'anomaly_severity': 'unknown'
                }
            
            # Seasonal training recommendations
            seasonal_analysis['seasonal_recommendations'] = self._generate_seasonal_recommendations(
                season, avg_temp, seasonal_analysis.get('temperature_comparison', {})
            )
        
        return seasonal_analysis

    def _determine_season(self, date: datetime) -> str:
        """Determine season based on date (Northern Hemisphere)"""
        
        month = date.month
        
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        elif month in [9, 10, 11]:
            return 'fall'
        else:
            return 'unknown'

    def _classify_temperature_anomaly(self, anomaly: float) -> str:
        """Classify temperature anomaly severity"""
        
        abs_anomaly = abs(anomaly)
        
        if abs_anomaly > 15:
            return 'extreme'
        elif abs_anomaly > 10:
            return 'severe'
        elif abs_anomaly > 5:
            return 'moderate'
        else:
            return 'normal'

    def _generate_seasonal_recommendations(self, season: str, avg_temp: float, 
                                         comparison: Dict[str, Any]) -> List[str]:
        """Generate season-specific training recommendations"""
        
        recommendations = []
        
        if season == 'summer':
            if avg_temp > 30:
                recommendations.append(
                    "SUMMER TRAINING: High temperature conditions. Schedule exercises during "
                    "early morning or evening hours. Increase hydration requirements."
                )
            recommendations.append(
                "SUMMER PROTOCOLS: Implement heat injury prevention measures. "
                "Consider lighter equipment loads and increased rest intervals."
            )
        
        elif season == 'winter':
            if avg_temp < 5:
                recommendations.append(
                    "WINTER TRAINING: Cold weather protocols required. Extend warm-up periods, "
                    "monitor for cold injuries, and ensure proper cold weather gear."
                )
            recommendations.append(
                "WINTER CONSIDERATIONS: Shorter daylight hours and potential equipment "
                "performance impacts in cold temperatures."
            )
        
        elif season == 'spring' or season == 'fall':
            recommendations.append(
                f"{season.upper()} TRAINING: Variable weather conditions expected. "
                "Prepare for temperature fluctuations and potential precipitation impacts."
            )
        
        # Anomaly-based recommendations
        anomaly_severity = comparison.get('anomaly_severity', 'normal')
        if anomaly_severity in ['severe', 'extreme']:
            recommendations.append(
                f"WEATHER ANOMALY: {anomaly_severity.title()} temperature deviation from seasonal norms. "
                "Adjust training protocols accordingly and monitor personnel closely."
            )
        
        return recommendations

    def _generate_environmental_alerts(self, temperature_analysis: Dict[str, Any],
                                     performance_correlation: Dict[str, float]) -> List[Alert]:
        """Generate environmental condition alerts"""
        
        alerts = []
        
        # Heat stress alerts
        heat_stress = temperature_analysis.get('heat_stress_assessment', {})
        overall_risk = heat_stress.get('overall_risk', 'minimal')
        
        if overall_risk == 'extreme':
            alerts.append(Alert(
                level=AlertLevel.CRITICAL,
                message="EXTREME heat stress conditions detected - immediate action required",
                domain=self.domain,
                timestamp=datetime.now(),
                details={
                    'heat_stress_level': overall_risk,
                    'peak_temperature': heat_stress.get('peak_temperature', 0),
                    'heat_stress_duration': heat_stress.get('heat_stress_duration_minutes', 0)
                }
            ))
        elif overall_risk == 'high':
            alerts.append(Alert(
                level=AlertLevel.HIGH,
                message="HIGH heat stress risk - implement mitigation protocols",
                domain=self.domain,
                timestamp=datetime.now(),
                details={
                    'heat_stress_level': overall_risk,
                    'peak_temperature': heat_stress.get('peak_temperature', 0)
                }
            ))
        elif overall_risk == 'moderate':
            alerts.append(Alert(
                level=AlertLevel.MEDIUM,
                message="MODERATE heat stress conditions - increase monitoring",
                domain=self.domain,
                timestamp=datetime.now(),
                details={'heat_stress_level': overall_risk}
            ))
        
        # Temperature extreme alerts
        temp_stats = temperature_analysis.get('temperature_stats', {})
        max_temp = temp_stats.get('max_temperature', 0)
        min_temp = temp_stats.get('min_temperature', 0)
        
        if max_temp > 40:
            alerts.append(Alert(
                level=AlertLevel.HIGH,
                message=f"Extreme high temperature recorded: {max_temp:.1f}°C",
                domain=self.domain,
                timestamp=datetime.now(),
                details={'max_temperature': max_temp}
            ))
        
        if min_temp < 0:
            alerts.append(Alert(
                level=AlertLevel.MEDIUM,
                message=f"Freezing temperature recorded: {min_temp:.1f}°C",
                domain=self.domain,
                timestamp=datetime.now(),
                details={'min_temperature': min_temp}
            ))
        
        # Performance correlation alerts
        impact_score = performance_correlation.get('overall_environmental_impact', 0)
        if impact_score > 0.7:
            alerts.append(Alert(
                level=AlertLevel.MEDIUM,
                message="Significant environmental impact on performance detected",
                domain=self.domain,
                timestamp=datetime.now(),
                details={
                    'impact_score': impact_score,
                    'correlations': performance_correlation
                }
            ))
        
        return alerts

    def _calculate_weather_impact_score(self, temperature_analysis: Dict[str, Any]) -> float:
        """Calculate overall weather impact score (0-1 scale)"""
        
        impact_factors = []
        
        # Heat stress impact
        heat_stress = temperature_analysis.get('heat_stress_assessment', {})
        risk_levels = {'minimal': 0, 'moderate': 0.3, 'high': 0.7, 'extreme': 1.0}
        heat_impact = risk_levels.get(heat_stress.get('overall_risk', 'minimal'), 0)
        impact_factors.append(heat_impact)
        
        # Temperature comfort impact
        comfort_index = temperature_analysis.get('comfort_index', 1.0)
        comfort_impact = 1 - comfort_index  # Invert comfort to get impact
        impact_factors.append(comfort_impact)
        
        # Temperature volatility impact
        temp_trends = temperature_analysis.get('temperature_trends', {})
        volatility = temp_trends.get('volatility', 0)
        volatility_impact = min(1.0, volatility / 10)  # 10°C volatility = max impact
        impact_factors.append(volatility_impact)
        
        # Calculate weighted average
        return np.mean(impact_factors)

    def _integrate_weather_forecast_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Integrate weather forecast data for future planning"""
        
        # This would typically integrate with weather services
        # For now, provide framework for forecast integration
        
        forecast_integration = {
            'forecast_available': False,
            'forecast_source': 'none',
            'prediction_confidence': 0,
            'recommended_actions': []
        }
        
        # Simulate basic forecast recommendations based on current conditions
        if 'Temperature' in data.columns:
            temp_data = data['Temperature'].dropna()
            if len(temp_data) > 0:
                current_temp = temp_data.iloc[-1] if len(temp_data) > 0 else 20
                
                # Simple trend-based forecast
                if len(temp_data) > 10:
                    recent_trend = temp_data.iloc[-10:].diff().mean()
                    
                    if recent_trend > 0.5:  # Rising temperature
                        forecast_integration['recommended_actions'].append(
                            "Temperature trending upward - prepare heat mitigation protocols"
                        )
                    elif recent_trend < -0.5:  # Falling temperature
                        forecast_integration['recommended_actions'].append(
                            "Temperature trending downward - prepare cold weather protocols"
                        )
        
        return forecast_integration

    def _generate_environmental_recommendations(self, env_metrics: EnvironmentalMetrics,
                                              temperature_analysis: Dict[str, Any],
                                              performance_correlation: Dict[str, float]) -> List[str]:
        """Generate comprehensive environmental recommendations"""
        
        recommendations = []
        
        # Include tactical recommendations from analysis
        recommendations.extend(env_metrics.tactical_recommendations)
        
        # Weather impact recommendations
        if env_metrics.weather_impact_score > 0.6:
            recommendations.append(
                "HIGH WEATHER IMPACT: Environmental conditions significantly affecting operations. "
                "Consider modifying exercise parameters or implementing additional safety protocols."
            )
        
        # Seasonal recommendations
        seasonal_recs = env_metrics.seasonal_analysis.get('seasonal_recommendations', [])
        recommendations.extend(seasonal_recs)
        
        # Critical period recommendations
        critical_periods = temperature_analysis.get('critical_periods', [])
        if len(critical_periods) > 2:
            recommendations.append(
                "MULTIPLE CRITICAL PERIODS: Consider breaking exercise into segments "
                "with environmental condition breaks between phases."
            )
        
        # Equipment protection recommendations
        temp_equipment_corr = performance_correlation.get('temperature_equipment_correlation', 0)
        if abs(temp_equipment_corr) > 0.4:
            recommendations.append(
                "EQUIPMENT PROTECTION: Environmental conditions affecting equipment performance. "
                "Implement temperature protection measures for sensitive equipment."
            )
        
        return recommendations

    def _calculate_summary_stats(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics for environmental analysis"""
        
        # Get or simulate temperature data
        if 'Temperature' not in data.columns or data['Temperature'].isna().all():
            temp_data = self._simulate_temperature_data(data)
            data_source = 'simulated'
        else:
            temp_data = data['Temperature'].dropna()
            data_source = 'measured'
        
        return {
            'total_records': len(data),
            'temperature_data_source': data_source,
            'temperature_data_points': len(temp_data),
            'exercise_duration_minutes': len(data) / 60,
            'environmental_data_quality': {
                'temperature_completeness': (len(temp_data) / len(data)) * 100 if len(data) > 0 else 0,
                'data_reliability': 'high' if data_source == 'measured' else 'simulated'
            },
            'analysis_limitations': [
                'Limited environmental sensor data',
                'Temperature data may be simulated',
                'Humidity and wind data not available',
                'Weather forecast integration not implemented'
            ] if data_source == 'simulated' else []
        }