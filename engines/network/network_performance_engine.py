# engines/network_performance_engine.py - Network Performance Analysis Engine
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging
import networkx as nx

from core.models import (
    AnalysisEngine, AnalysisDomain, AnalysisResult, Alert, AlertLevel,
    DataQualityMetrics, AnalysisLevel
)
from core.event_bus import EventBus, Event, EventType

class NetworkPerformanceAnalysisEngine(AnalysisEngine):
    """
    Network Performance Analysis Engine
    Implements REQ-NETWORK-001 through REQ-NETWORK-008
    """
    
    def __init__(self, event_bus: EventBus = None):
        super().__init__(AnalysisDomain.NETWORK_PERFORMANCE)
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Network topology graph
        self.network_graph = nx.DiGraph()
        
        # Subscribe to events
        if self.event_bus:
            self.event_bus.subscribe(EventType.CONFIG_CHANGED, self.on_config_changed)
    
    def get_required_columns(self) -> List[str]:
        """Required columns for network performance analysis"""
        return [
            'callsign',
            'processedtimegmt'
        ]
    
    def get_optional_columns(self) -> List[str]:
        """Optional columns that enhance network analysis"""
        return [
            'rssi',
            'mcs', 
            'nexthop',
            'ip',
            'latitude',
            'longitude'
        ]
    
    def get_default_thresholds(self) -> Dict[str, Any]:
        """Default thresholds for network performance analysis"""
        return {
            'rssi_excellent': 30,      # dBm
            'rssi_good': 20,           # dBm  
            'rssi_poor': 10,           # dBm
            'rssi_critical': 5,        # dBm
            'mcs_optimal_min': 5,      # Optimal MCS range
            'mcs_optimal_max': 7,
            'mcs_minimum': 3,          # Minimum acceptable MCS
            'blackout_duration_warning': 30,    # seconds
            'blackout_duration_critical': 60,   # seconds
            'packet_loss_warning': 0.05,        # 5%
            'packet_loss_critical': 0.15,       # 15%
            'network_utilization_warning': 0.8,  # 80%
            'network_utilization_critical': 0.95 # 95%
        }
    
    def validate_data(self, data: pd.DataFrame) -> DataQualityMetrics:
        """Validate data quality for network performance analysis"""
        metrics = DataQualityMetrics()
        metrics.total_records = len(data)
        
        # Check data availability
        missing_data = {}
        for col in self.required_columns + self.optional_columns:
            if col in data.columns:
                missing_count = data[col].isna().sum()
                missing_data[col] = (missing_count / len(data)) * 100
            else:
                missing_data[col] = 100.0
        
        metrics.missing_data_percentage = missing_data
        
        # Validate RSSI values
        if 'rssi' in data.columns:
            rssi_data = data['rssi'][data['rssi'] >= 0]  # Valid RSSI readings
            if len(rssi_data) < len(data) * 0.5:
                metrics.validation_errors.append("Less than 50% valid RSSI readings")
            
            # Check for reasonable RSSI range
            if not rssi_data.empty:
                if rssi_data.max() > 100 or rssi_data.min() < -120:
                    metrics.validation_errors.append("RSSI values outside reasonable range")
        
        # Validate MCS values
        if 'mcs' in data.columns:
            mcs_data = data['mcs'][data['mcs'] >= 0]
            if not mcs_data.empty:
                if mcs_data.max() > 11 or mcs_data.min() < 0:
                    metrics.validation_errors.append("MCS values outside valid range (0-11)")
        
        # Calculate overall completeness
        network_columns = ['rssi', 'mcs', 'nexthop', 'ip']
        available_network_data = [col for col in network_columns if col in data.columns]
        
        if len(available_network_data) == 0:
            metrics.data_completeness = 0
            metrics.validation_errors.append("No network performance data available")
        else:
            network_completeness = []
            for col in available_network_data:
                if col in missing_data:
                    network_completeness.append(100 - missing_data[col])
            metrics.data_completeness = np.mean(network_completeness) if network_completeness else 0
        
        return metrics
    
    def analyze(self, data: pd.DataFrame, config: Dict[str, Any] = None) -> AnalysisResult:
        """Perform comprehensive network performance analysis"""
        start_time = datetime.now()
        config = config or {}
        
        # Update thresholds if provided
        if 'thresholds' in config:
            self.update_thresholds(config['thresholds'])
        
        try:
            # Validate data
            data_quality = self.validate_data(data)
            
            if data_quality.data_completeness < 30:
                self.logger.warning(f"Low network data completeness: {data_quality.data_completeness:.1f}%")
            
            # Perform analysis components
            results = {}
            alerts = []
            recommendations = []
            
            # REQ-NETWORK-001: RSSI performance monitoring
            if 'rssi' in data.columns:
                rssi_analysis = self._analyze_rssi_performance(data)
                results['rssi_analysis'] = rssi_analysis
                alerts.extend(rssi_analysis.get('alerts', []))
            
            # REQ-NETWORK-002: MCS efficiency tracking
            if 'mcs' in data.columns:
                mcs_analysis = self._analyze_mcs_efficiency(data)
                results['mcs_analysis'] = mcs_analysis
                alerts.extend(mcs_analysis.get('alerts', []))
            
            # REQ-NETWORK-003: Network hop analysis
            if 'nexthop' in data.columns:
                nexthop_analysis = self._analyze_nexthop_patterns(data)
                results['nexthop_analysis'] = nexthop_analysis
                alerts.extend(nexthop_analysis.get('alerts', []))
            
            # REQ-NETWORK-004: Communication blackout identification
            blackout_analysis = self._analyze_communication_blackouts(data)
            results['blackout_analysis'] = blackout_analysis
            alerts.extend(blackout_analysis.get('alerts', []))
            
            # REQ-NETWORK-005: Data transmission quality
            if 'rssi' in data.columns or 'mcs' in data.columns:
                transmission_analysis = self._analyze_transmission_quality(data)
                results['transmission_analysis'] = transmission_analysis
                alerts.extend(transmission_analysis.get('alerts', []))
            
            # REQ-NETWORK-006: Network coverage analysis
            if all(col in data.columns for col in ['latitude', 'longitude', 'rssi']):
                coverage_analysis = self._analyze_network_coverage(data)
                results['coverage_analysis'] = coverage_analysis
                alerts.extend(coverage_analysis.get('alerts', []))
            
            # Build network topology
            if 'nexthop' in data.columns and 'ip' in data.columns:
                topology = self._build_network_topology(data)
                results['network_topology'] = topology
            
            # Generate recommendations
            recommendations = self._generate_network_recommendations(results)
            
            # Calculate overall metrics
            overall_metrics = self._calculate_overall_metrics(results, data)
            
            # Publish alerts
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
            self.logger.error(f"Error in network performance analysis: {e}")
            if self.event_bus:
                self.event_bus.publish(Event(
                    EventType.ERROR_OCCURRED,
                    {'domain': self.domain.value, 'error': str(e)},
                    source='NetworkPerformanceAnalysisEngine'
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
    
    def _analyze_rssi_performance(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        REQ-NETWORK-001: Monitor RSSI performance
        """
        rssi_data = data['rssi'][data['rssi'] >= 0]  # Valid readings only
        
        analysis = {
            'overall_statistics': {},
            'unit_performance': {},
            'signal_quality_distribution': {},
            'temporal_patterns': {},
            'alerts': []
        }
        
        if not rssi_data.empty:
            # Overall statistics
            analysis['overall_statistics'] = {
                'mean_rssi': rssi_data.mean(),
                'median_rssi': rssi_data.median(),
                'min_rssi': rssi_data.min(),
                'max_rssi': rssi_data.max(),
                'std_rssi': rssi_data.std(),
                'total_measurements': len(rssi_data)
            }
            
            # Signal quality classification
            excellent_count = len(rssi_data[rssi_data >= self.thresholds['rssi_excellent']])
            good_count = len(rssi_data[(rssi_data >= self.thresholds['rssi_good']) & 
                                     (rssi_data < self.thresholds['rssi_excellent'])])
            poor_count = len(rssi_data[(rssi_data >= self.thresholds['rssi_poor']) & 
                                     (rssi_data < self.thresholds['rssi_good'])])
            critical_count = len(rssi_data[rssi_data < self.thresholds['rssi_poor']])
            
            analysis['signal_quality_distribution'] = {
                'excellent': excellent_count,
                'good': good_count,
                'poor': poor_count,
                'critical': critical_count,
                'excellent_percentage': (excellent_count / len(rssi_data)) * 100,
                'poor_percentage': (poor_count / len(rssi_data)) * 100,
                'critical_percentage': (critical_count / len(rssi_data)) * 100
            }
            
            # Per-unit RSSI analysis
            for callsign, unit_data in data.groupby('callsign'):
                unit_rssi = unit_data['rssi'][unit_data['rssi'] >= 0]
                if not unit_rssi.empty:
                    unit_poor_count = len(unit_rssi[unit_rssi < self.thresholds['rssi_poor']])
                    unit_critical_count = len(unit_rssi[unit_rssi < self.thresholds['rssi_critical']])
                    
                    analysis['unit_performance'][callsign] = {
                        'mean_rssi': unit_rssi.mean(),
                        'min_rssi': unit_rssi.min(),
                        'max_rssi': unit_rssi.max(),
                        'measurements': len(unit_rssi),
                        'poor_signal_percentage': (unit_poor_count / len(unit_rssi)) * 100,
                        'critical_signal_percentage': (unit_critical_count / len(unit_rssi)) * 100
                    }
            
            # Generate alerts
            critical_percentage = analysis['signal_quality_distribution']['critical_percentage']
            poor_percentage = analysis['signal_quality_distribution']['poor_percentage']
            
            if critical_percentage > 10:  # More than 10% critical signals
                analysis['alerts'].append(Alert(
                    alert_type='CRITICAL_SIGNAL_QUALITY',
                    level=AlertLevel.CRITICAL,
                    message=f'Critical signal quality: {critical_percentage:.1f}% of measurements below {self.thresholds["rssi_critical"]} dBm',
                    metric_value=critical_percentage,
                    threshold=10
                ))
            elif poor_percentage > 25:  # More than 25% poor signals
                analysis['alerts'].append(Alert(
                    alert_type='POOR_SIGNAL_QUALITY',
                    level=AlertLevel.WARNING,
                    message=f'Poor signal quality: {poor_percentage:.1f}% of measurements below {self.thresholds["rssi_poor"]} dBm',
                    metric_value=poor_percentage,
                    threshold=25
                ))
            
            # Unit-specific alerts
            units_with_poor_signal = [
                unit for unit, perf in analysis['unit_performance'].items()
                if perf['critical_signal_percentage'] > 20
            ]
            
            if units_with_poor_signal:
                analysis['alerts'].append(Alert(
                    alert_type='UNITS_WITH_POOR_SIGNAL',
                    level=AlertLevel.WARNING,
                    message=f'Units with consistently poor signal: {", ".join(units_with_poor_signal)}',
                    affected_units=units_with_poor_signal
                ))
        
        return analysis
    
    def _analyze_mcs_efficiency(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        REQ-NETWORK-002: Track MCS efficiency
        """
        mcs_data = data['mcs'][data['mcs'] >= 0]
        
        analysis = {
            'efficiency_statistics': {},
            'mcs_distribution': {},
            'unit_efficiency': {},
            'optimization_potential': {},
            'alerts': []
        }
        
        if not mcs_data.empty:
            # Overall efficiency statistics
            optimal_count = len(mcs_data[(mcs_data >= self.thresholds['mcs_optimal_min']) & 
                                       (mcs_data <= self.thresholds['mcs_optimal_max'])])
            suboptimal_count = len(mcs_data[mcs_data < self.thresholds['mcs_minimum']])
            
            analysis['efficiency_statistics'] = {
                'mean_mcs': mcs_data.mean(),
                'median_mcs': mcs_data.median(),
                'mode_mcs': mcs_data.mode().iloc[0] if not mcs_data.empty else 0,
                'efficiency_score': (optimal_count / len(mcs_data)) * 100,
                'suboptimal_percentage': (suboptimal_count / len(mcs_data)) * 100
            }
            
            # MCS distribution
            mcs_counts = mcs_data.value_counts().sort_index().to_dict()
            analysis['mcs_distribution'] = mcs_counts
            
            # Per-unit MCS efficiency
            for callsign, unit_data in data.groupby('callsign'):
                unit_mcs = unit_data['mcs'][unit_data['mcs'] >= 0]
                if not unit_mcs.empty:
                    unit_optimal = len(unit_mcs[(unit_mcs >= self.thresholds['mcs_optimal_min']) & 
                                              (unit_mcs <= self.thresholds['mcs_optimal_max'])])
                    unit_efficiency = (unit_optimal / len(unit_mcs)) * 100
                    
                    analysis['unit_efficiency'][callsign] = {
                        'mean_mcs': unit_mcs.mean(),
                        'efficiency_percentage': unit_efficiency,
                        'measurements': len(unit_mcs),
                        'dominant_mcs': unit_mcs.mode().iloc[0] if not unit_mcs.empty else 0
                    }
            
            # Optimization analysis
            current_efficiency = analysis['efficiency_statistics']['efficiency_score']
            potential_improvement = 100 - current_efficiency
            
            analysis['optimization_potential'] = {
                'current_efficiency': current_efficiency,
                'improvement_potential': potential_improvement,
                'recommended_actions': []
            }
            
            # Generate alerts
            if current_efficiency < 50:  # Less than 50% efficiency
                analysis['alerts'].append(Alert(
                    alert_type='LOW_MCS_EFFICIENCY',
                    level=AlertLevel.CRITICAL,
                    message=f'Low MCS efficiency: {current_efficiency:.1f}% of transmissions in optimal range',
                    metric_value=current_efficiency,
                    threshold=50
                ))
            elif current_efficiency < 70:  # Less than 70% efficiency
                analysis['alerts'].append(Alert(
                    alert_type='SUBOPTIMAL_MCS_EFFICIENCY',
                    level=AlertLevel.WARNING,
                    message=f'Suboptimal MCS efficiency: {current_efficiency:.1f}% of transmissions in optimal range',
                    metric_value=current_efficiency,
                    threshold=70
                ))
            
            # Unit-specific efficiency alerts
            low_efficiency_units = [
                unit for unit, eff in analysis['unit_efficiency'].items()
                if eff['efficiency_percentage'] < 40
            ]
            
            if low_efficiency_units:
                analysis['alerts'].append(Alert(
                    alert_type='UNITS_LOW_MCS_EFFICIENCY',
                    level=AlertLevel.WARNING,
                    message=f'Units with low MCS efficiency: {", ".join(low_efficiency_units)}',
                    affected_units=low_efficiency_units
                ))
        
        return analysis
    
    def _analyze_nexthop_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        REQ-NETWORK-003: Network hop analysis and redundancy assessment
        """
        analysis = {
            'nexthop_usage': {},
            'load_distribution': {},
            'redundancy_assessment': {},
            'routing_efficiency': {},
            'alerts': []
        }
        
        if 'nexthop' in data.columns:
            # Filter out unavailable nexthops
            valid_nexthop_data = data[data['nexthop'] != 'Unavailable']
            
            if not valid_nexthop_data.empty:
                # Nexthop usage statistics
                nexthop_counts = valid_nexthop_data['nexthop'].value_counts().to_dict()
                analysis['nexthop_usage'] = nexthop_counts
                
                total_nexthops = len(nexthop_counts)
                total_traffic = sum(nexthop_counts.values())
                
                # Load distribution analysis
                for nexthop, count in nexthop_counts.items():
                    nexthop_data = valid_nexthop_data[valid_nexthop_data['nexthop'] == nexthop]
                    unique_units = nexthop_data['callsign'].nunique()
                    
                    analysis['load_distribution'][nexthop] = {
                        'total_reports': count,
                        'unique_units': unique_units,
                        'traffic_percentage': (count / total_traffic) * 100,
                        'utilization_score': unique_units / data['callsign'].nunique() * 100,
                        'reports_per_unit': count / unique_units if unique_units > 0 else 0
                    }
                
                # Redundancy assessment per unit
                for callsign, unit_data in data.groupby('callsign'):
                    unit_nexthops = unit_data['nexthop'][unit_data['nexthop'] != 'Unavailable']
                    unique_nexthops = unit_nexthops.nunique()
                    
                    if unique_nexthops > 0:
                        redundancy_level = 'High' if unique_nexthops > 2 else 'Medium' if unique_nexthops == 2 else 'Low'
                        analysis['redundancy_assessment'][callsign] = {
                            'nexthop_count': unique_nexthops,
                            'redundancy_level': redundancy_level,
                            'primary_nexthop': unit_nexthops.mode().iloc[0] if not unit_nexthops.empty else None,
                            'nexthop_distribution': unit_nexthops.value_counts().to_dict()
                        }
                
                # Routing efficiency analysis
                avg_nexthops_per_unit = np.mean([
                    data['nexthop_count'] for data in analysis['redundancy_assessment'].values()
                ])
                
                load_balance_score = 100 - (np.std(list(nexthop_counts.values())) / np.mean(list(nexthop_counts.values())) * 100)
                load_balance_score = max(0, min(100, load_balance_score))
                
                analysis['routing_efficiency'] = {
                    'total_nexthops': total_nexthops,
                    'avg_nexthops_per_unit': avg_nexthops_per_unit,
                    'load_balance_score': load_balance_score,
                    'single_point_failures': sum(1 for level in analysis['redundancy_assessment'].values() 
                                                if level['redundancy_level'] == 'Low')
                }
                
                # Generate alerts
                if load_balance_score < 60:
                    analysis['alerts'].append(Alert(
                        alert_type='POOR_LOAD_DISTRIBUTION',
                        level=AlertLevel.WARNING,
                        message=f'Poor nexthop load distribution: {load_balance_score:.1f}% balance score',
                        metric_value=load_balance_score,
                        threshold=60
                    ))
                
                single_point_failures = analysis['routing_efficiency']['single_point_failures']
                if single_point_failures > 0:
                    analysis['alerts'].append(Alert(
                        alert_type='SINGLE_POINT_FAILURES',
                        level=AlertLevel.WARNING,
                        message=f'{single_point_failures} units have single nexthop dependency',
                        metric_value=single_point_failures
                    ))
        
        return analysis
    
    def _analyze_communication_blackouts(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        REQ-NETWORK-004: Communication blackout identification and duration tracking
        """
        analysis = {
            'blackout_summary': {},
            'unit_blackouts': {},
            'temporal_patterns': {},
            'impact_assessment': {},
            'alerts': []
        }
        
        total_blackouts = 0
        total_blackout_duration = 0
        units_affected = []
        
        # Analyze blackouts per unit
        for callsign, unit_data in data.groupby('callsign'):
            sorted_data = unit_data.sort_values('processedtimegmt')
            
            blackout_periods = []
            in_blackout = False
            blackout_start = None
            
            for _, row in sorted_data.iterrows():
                # Define blackout conditions
                is_blackout = self._is_communication_blackout(row)
                current_time = pd.to_datetime(row['processedtimegmt'])
                
                if is_blackout and not in_blackout:
                    blackout_start = current_time
                    in_blackout = True
                elif not is_blackout and in_blackout:
                    if blackout_start:
                        duration = (current_time - blackout_start).total_seconds()
                        blackout_periods.append({
                            'start': blackout_start,
                            'end': current_time,
                            'duration': duration
                        })
                        total_blackout_duration += duration
                    in_blackout = False
            
            # Handle ongoing blackout at end of data
            if in_blackout and blackout_start:
                final_time = pd.to_datetime(sorted_data.iloc[-1]['processedtimegmt'])
                duration = (final_time - blackout_start).total_seconds()
                blackout_periods.append({
                    'start': blackout_start,
                    'end': final_time,
                    'duration': duration
                })
                total_blackout_duration += duration
            
            if blackout_periods:
                units_affected.append(callsign)
                total_blackouts += len(blackout_periods)
                
                analysis['unit_blackouts'][callsign] = {
                    'blackout_count': len(blackout_periods),
                    'total_duration': sum(p['duration'] for p in blackout_periods),
                    'average_duration': np.mean([p['duration'] for p in blackout_periods]),
                    'max_duration': max(p['duration'] for p in blackout_periods),
                    'blackout_periods': blackout_periods
                }
        
        # Overall blackout summary
        analysis['blackout_summary'] = {
            'total_blackouts': total_blackouts,
            'units_affected': len(units_affected),
            'total_duration': total_blackout_duration,
            'average_duration': total_blackout_duration / total_blackouts if total_blackouts > 0 else 0,
            'units_affected_list': units_affected
        }
        
        # Temporal pattern analysis
        if total_blackouts > 0:
            all_blackouts = []
            for unit_blackouts in analysis['unit_blackouts'].values():
                all_blackouts.extend(unit_blackouts['blackout_periods'])
            
            # Group by hour
            hourly_blackouts = {}
            for blackout in all_blackouts:
                hour = blackout['start'].hour
                hourly_blackouts[hour] = hourly_blackouts.get(hour, 0) + 1
            
            analysis['temporal_patterns'] = {
                'hourly_distribution': hourly_blackouts,
                'peak_blackout_hour': max(hourly_blackouts.items(), key=lambda x: x[1]) if hourly_blackouts else None
            }
        
        # Impact assessment
        total_units = data['callsign'].nunique()
        blackout_impact = (len(units_affected) / total_units) * 100 if total_units > 0 else 0
        
        analysis['impact_assessment'] = {
            'percentage_units_affected': blackout_impact,
            'network_availability': 100 - blackout_impact,
            'average_blackout_duration': analysis['blackout_summary']['average_duration'],
            'severity_classification': self._classify_blackout_severity(blackout_impact, analysis['blackout_summary']['average_duration'])
        }
        
        # Generate alerts
        if analysis['blackout_summary']['average_duration'] > self.thresholds['blackout_duration_critical']:
            analysis['alerts'].append(Alert(
                alert_type='CRITICAL_BLACKOUT_DURATION',
                level=AlertLevel.CRITICAL,
                message=f'Critical blackout duration: {analysis["blackout_summary"]["average_duration"]:.1f}s average',
                metric_value=analysis['blackout_summary']['average_duration'],
                threshold=self.thresholds['blackout_duration_critical']
            ))
        elif analysis['blackout_summary']['average_duration'] > self.thresholds['blackout_duration_warning']:
            analysis['alerts'].append(Alert(
                alert_type='LONG_BLACKOUT_DURATION',
                level=AlertLevel.WARNING,
                message=f'Long blackout duration: {analysis["blackout_summary"]["average_duration"]:.1f}s average',
                metric_value=analysis['blackout_summary']['average_duration'],
                threshold=self.thresholds['blackout_duration_warning']
            ))
        
        if blackout_impact > 25:  # More than 25% of units affected
            analysis['alerts'].append(Alert(
                alert_type='WIDESPREAD_BLACKOUTS',
                level=AlertLevel.CRITICAL,
                message=f'Widespread communication blackouts: {blackout_impact:.1f}% of units affected',
                affected_units=units_affected,
                metric_value=blackout_impact,
                threshold=25
            ))
        
        return analysis
    
    def _is_communication_blackout(self, row: pd.Series) -> bool:
        """Determine if a data point represents a communication blackout"""
        # Define blackout as combination of poor/missing network indicators
        blackout_indicators = 0
        
        if 'rssi' in row.index and (pd.isna(row['rssi']) or row['rssi'] < 0):
            blackout_indicators += 1
        
        if 'nexthop' in row.index and (pd.isna(row['nexthop']) or row['nexthop'] == 'Unavailable'):
            blackout_indicators += 1
        
        if 'mcs' in row.index and (pd.isna(row['mcs']) or row['mcs'] < 0):
            blackout_indicators += 1
        
        # Consider it a blackout if multiple indicators suggest no communication
        return blackout_indicators >= 2
    
    def _classify_blackout_severity(self, impact_percentage: float, avg_duration: float) -> str:
        """Classify the severity of communication blackouts"""
        if impact_percentage > 50 or avg_duration > 120:
            return 'CRITICAL'
        elif impact_percentage > 25 or avg_duration > 60:
            return 'HIGH'
        elif impact_percentage > 10 or avg_duration > 30:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _analyze_transmission_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        REQ-NETWORK-005: Real-time data loss and latency analysis
        """
        analysis = {
            'quality_metrics': {},
            'packet_loss_estimation': {},
            'latency_analysis': {},
            'alerts': []
        }
        
        # Estimate packet loss based on missing data patterns
        total_expected_reports = self._estimate_expected_reports(data)
        actual_reports = len(data)
        estimated_packet_loss = max(0, (total_expected_reports - actual_reports) / total_expected_reports) if total_expected_reports > 0 else 0
        
        # Quality score based on RSSI and MCS
        quality_scores = []
        for _, row in data.iterrows():
            score = 100
            
            if 'rssi' in row.index and pd.notna(row['rssi']) and row['rssi'] >= 0:
                if row['rssi'] < self.thresholds['rssi_poor']:
                    score -= 40
                elif row['rssi'] < self.thresholds['rssi_good']:
                    score -= 20
            
            if 'mcs' in row.index and pd.notna(row['mcs']) and row['mcs'] >= 0:
                if row['mcs'] < self.thresholds['mcs_minimum']:
                    score -= 30
                elif row['mcs'] < self.thresholds['mcs_optimal_min']:
                    score -= 15
            
            quality_scores.append(max(0, score))
        
        avg_quality_score = np.mean(quality_scores) if quality_scores else 0
        
        analysis['quality_metrics'] = {
            'average_quality_score': avg_quality_score,
            'estimated_packet_loss': estimated_packet_loss * 100,  # Convert to percentage
            'transmission_reliability': 100 - (estimated_packet_loss * 100),
            'quality_consistency': 100 - (np.std(quality_scores) if quality_scores else 0)
        }
        
        # Generate alerts for transmission quality
        if estimated_packet_loss > self.thresholds['packet_loss_critical']:
            analysis['alerts'].append(Alert(
                alert_type='CRITICAL_PACKET_LOSS',
                level=AlertLevel.CRITICAL,
                message=f'Critical packet loss detected: {estimated_packet_loss*100:.1f}%',
                metric_value=estimated_packet_loss * 100,
                threshold=self.thresholds['packet_loss_critical'] * 100
            ))
        elif estimated_packet_loss > self.thresholds['packet_loss_warning']:
            analysis['alerts'].append(Alert(
                alert_type='HIGH_PACKET_LOSS',
                level=AlertLevel.WARNING,
                message=f'High packet loss detected: {estimated_packet_loss*100:.1f}%',
                metric_value=estimated_packet_loss * 100,
                threshold=self.thresholds['packet_loss_warning'] * 100
            ))
        
        if avg_quality_score < 60:
            analysis['alerts'].append(Alert(
                alert_type='POOR_TRANSMISSION_QUALITY',
                level=AlertLevel.WARNING,
                message=f'Poor transmission quality: {avg_quality_score:.1f}% average score',
                metric_value=avg_quality_score,
                threshold=60
            ))
        
        return analysis
    
    def _estimate_expected_reports(self, data: pd.DataFrame) -> int:
        """Estimate expected number of reports based on time span and units"""
        if 'processedtimegmt' in data.columns:
            time_span = (pd.to_datetime(data['processedtimegmt']).max() - 
                        pd.to_datetime(data['processedtimegmt']).min()).total_seconds()
            num_units = data['callsign'].nunique()
            expected_interval = 30  # Assume 30-second reporting interval
            
            return int((time_span / expected_interval) * num_units)
        return len(data)
    
    def _analyze_network_coverage(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        REQ-NETWORK-007: Network coverage gap identification through GPS correlation
        """
        analysis = {
            'coverage_statistics': {},
            'coverage_gaps': {},
            'geographic_analysis': {},
            'alerts': []
        }
        
        # Analyze signal strength by geographic location
        location_data = data.dropna(subset=['latitude', 'longitude', 'rssi'])
        
        if not location_data.empty:
            # Grid-based coverage analysis
            lat_bins = 10  # Divide area into grid
            lon_bins = 10
            
            lat_min, lat_max = location_data['latitude'].min(), location_data['latitude'].max()
            lon_min, lon_max = location_data['longitude'].min(), location_data['longitude'].max()
            
            coverage_grid = {}
            gap_areas = []
            
            for i in range(lat_bins):
                for j in range(lon_bins):
                    lat_start = lat_min + (lat_max - lat_min) * i / lat_bins
                    lat_end = lat_min + (lat_max - lat_min) * (i + 1) / lat_bins
                    lon_start = lon_min + (lon_max - lon_min) * j / lon_bins
                    lon_end = lon_min + (lon_max - lon_min) * (j + 1) / lon_bins
                    
                    grid_data = location_data[
                        (location_data['latitude'] >= lat_start) & (location_data['latitude'] < lat_end) &
                        (location_data['longitude'] >= lon_start) & (location_data['longitude'] < lon_end)
                    ]
                    
                    if not grid_data.empty:
                        avg_rssi = grid_data['rssi'].mean()
                        coverage_grid[f'{i}_{j}'] = {
                            'lat_range': (lat_start, lat_end),
                            'lon_range': (lon_start, lon_end),
                            'avg_rssi': avg_rssi,
                            'measurement_count': len(grid_data),
                            'coverage_quality': 'Good' if avg_rssi > self.thresholds['rssi_good'] else 'Poor'
                        }
                        
                        if avg_rssi < self.thresholds['rssi_poor']:
                            gap_areas.append({
                                'grid_id': f'{i}_{j}',
                                'center_lat': (lat_start + lat_end) / 2,
                                'center_lon': (lon_start + lon_end) / 2,
                                'avg_rssi': avg_rssi
                            })
            
            # Coverage statistics
            good_coverage_areas = sum(1 for area in coverage_grid.values() if area['coverage_quality'] == 'Good')
            total_areas = len(coverage_grid)
            coverage_percentage = (good_coverage_areas / total_areas * 100) if total_areas > 0 else 0
            
            analysis['coverage_statistics'] = {
                'total_coverage_areas': total_areas,
                'good_coverage_areas': good_coverage_areas,
                'coverage_percentage': coverage_percentage,
                'gap_areas_count': len(gap_areas)
            }
            
            analysis['coverage_gaps'] = gap_areas
            analysis['geographic_analysis'] = coverage_grid
            
            # Generate coverage alerts
            if coverage_percentage < 70:
                analysis['alerts'].append(Alert(
                    alert_type='POOR_NETWORK_COVERAGE',
                    level=AlertLevel.WARNING,
                    message=f'Poor network coverage: {coverage_percentage:.1f}% of areas have good signal',
                    metric_value=coverage_percentage,
                    threshold=70
                ))
            
            if len(gap_areas) > 0:
                analysis['alerts'].append(Alert(
                    alert_type='COVERAGE_GAPS_DETECTED',
                    level=AlertLevel.WARNING,
                    message=f'{len(gap_areas)} coverage gap areas identified',
                    metric_value=len(gap_areas)
                ))
        
        return analysis
    
    def _build_network_topology(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Build network topology graph from nexthop data"""
        self.network_graph.clear()
        
        topology = {
            'nodes': {},
            'edges': {},
            'statistics': {},
            'connectivity_analysis': {}
        }
        
        # Add nodes and edges
        for _, row in data.iterrows():
            if pd.notna(row['ip']) and pd.notna(row['nexthop']) and row['nexthop'] != 'Unavailable':
                station = row['callsign']
                nexthop = row['nexthop']
                
                # Add nodes
                self.network_graph.add_node(station, type='station', ip=row['ip'])
                self.network_graph.add_node(nexthop, type='nexthop')
                
                # Add/update edge
                if self.network_graph.has_edge(station, nexthop):
                    self.network_graph[station][nexthop]['weight'] += 1
                else:
                    self.network_graph.add_edge(station, nexthop, weight=1)
        
        # Analyze topology
        topology['statistics'] = {
            'total_nodes': self.network_graph.number_of_nodes(),
            'total_edges': self.network_graph.number_of_edges(),
            'station_nodes': len([n for n, d in self.network_graph.nodes(data=True) if d.get('type') == 'station']),
            'nexthop_nodes': len([n for n, d in self.network_graph.nodes(data=True) if d.get('type') == 'nexthop']),
            'isolated_nodes': len(list(nx.isolates(self.network_graph)))
        }
        
        # Connectivity analysis
        if self.network_graph.number_of_nodes() > 0:
            topology['connectivity_analysis'] = {
                'is_connected': nx.is_weakly_connected(self.network_graph),
                'number_of_components': nx.number_weakly_connected_components(self.network_graph),
                'average_degree': sum(dict(self.network_graph.degree()).values()) / self.network_graph.number_of_nodes()
            }
        
        return topology
    
    def _generate_network_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate network performance recommendations"""
        recommendations = []
        
        # RSSI-based recommendations
        rssi_analysis = results.get('rssi_analysis', {})
        if rssi_analysis.get('signal_quality_distribution', {}).get('critical_percentage', 0) > 10:
            recommendations.append(
                "CRITICAL: Investigate and resolve signal quality issues - over 10% of measurements are critical"
            )
        
        # MCS efficiency recommendations
        mcs_analysis = results.get('mcs_analysis', {})
        if mcs_analysis.get('efficiency_statistics', {}).get('efficiency_score', 100) < 60:
            recommendations.append(
                "Optimize MCS settings and review adaptive modulation algorithms"
            )
        
        # Nexthop recommendations
        nexthop_analysis = results.get('nexthop_analysis', {})
        if nexthop_analysis.get('routing_efficiency', {}).get('load_balance_score', 100) < 60:
            recommendations.append(
                "Rebalance nexthop load distribution to improve network efficiency"
            )
        
        # Blackout recommendations
        blackout_analysis = results.get('blackout_analysis', {})
        if blackout_analysis.get('blackout_summary', {}).get('total_blackouts', 0) > 0:
            recommendations.append(
                "Implement redundant communication pathways to prevent blackouts"
            )
        
        # Coverage recommendations
        coverage_analysis = results.get('coverage_analysis', {})
        if coverage_analysis.get('coverage_statistics', {}).get('coverage_percentage', 100) < 80:
            recommendations.append(
                "Expand network infrastructure to address coverage gaps"
            )
        
        if not recommendations:
            recommendations.append(
                "Network performance within acceptable parameters - continue monitoring"
            )
        
        return recommendations
    
    def _calculate_overall_metrics(self, results: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate overall network performance metrics"""
        metrics = {
            'total_units': data['callsign'].nunique(),
            'analysis_timestamp': datetime.now().isoformat(),
            'data_timespan_hours': 0
        }
        
        # Calculate data timespan
        if 'processedtimegmt' in data.columns:
            time_data = pd.to_datetime(data['processedtimegmt'])
            metrics['data_timespan_hours'] = (time_data.max() - time_data.min()).total_seconds() / 3600
        
        # RSSI metrics
        rssi_analysis = results.get('rssi_analysis', {})
        if rssi_analysis:
            metrics.update({
                'average_rssi': rssi_analysis.get('overall_statistics', {}).get('mean_rssi', 0),
                'signal_quality_score': 100 - rssi_analysis.get('signal_quality_distribution', {}).get('critical_percentage', 0)
            })
        
        # MCS metrics
        mcs_analysis = results.get('mcs_analysis', {})
        if mcs_analysis:
            metrics['mcs_efficiency_score'] = mcs_analysis.get('efficiency_statistics', {}).get('efficiency_score', 0)
        
        # Network availability
        blackout_analysis = results.get('blackout_analysis', {})
        if blackout_analysis:
            metrics['network_availability'] = blackout_analysis.get('impact_assessment', {}).get('network_availability', 100)
        
        # Overall network health score
        health_components = []
        if 'signal_quality_score' in metrics:
            health_components.append(metrics['signal_quality_score'])
        if 'mcs_efficiency_score' in metrics:
            health_components.append(metrics['mcs_efficiency_score'])
        if 'network_availability' in metrics:
            health_components.append(metrics['network_availability'])
        
        metrics['overall_network_health'] = np.mean(health_components) if health_components else 0
        
        return metrics
    
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
                source='NetworkPerformanceAnalysisEngine'
            ))
    
    def on_config_changed(self, event: Event):
        """Handle configuration changes"""
        config_data = event.data
        if 'network_thresholds' in config_data:
            self.update_thresholds(config_data['network_thresholds'])
            self.logger.info("Network analysis thresholds updated")
    
    def get_analysis_capabilities(self) -> Dict[str, Any]:
        """Return capabilities for this analysis engine"""
        capabilities = super().get_analysis_capabilities()
        capabilities.update({
            'supported_levels': [level.value for level in [AnalysisLevel.INDIVIDUAL, AnalysisLevel.SQUAD, AnalysisLevel.PLATOON]],
            'real_time_capable': True,
            'alert_types': [
                'CRITICAL_SIGNAL_QUALITY',
                'POOR_SIGNAL_QUALITY',
                'UNITS_WITH_POOR_SIGNAL',
                'LOW_MCS_EFFICIENCY',
                'SUBOPTIMAL_MCS_EFFICIENCY',
                'UNITS_LOW_MCS_EFFICIENCY',
                'POOR_LOAD_DISTRIBUTION',
                'SINGLE_POINT_FAILURES',
                'CRITICAL_BLACKOUT_DURATION',
                'LONG_BLACKOUT_DURATION',
                'WIDESPREAD_BLACKOUTS',
                'CRITICAL_PACKET_LOSS',
                'HIGH_PACKET_LOSS',
                'POOR_TRANSMISSION_QUALITY',
                'POOR_NETWORK_COVERAGE',
                'COVERAGE_GAPS_DETECTED'
            ],
            'metrics_provided': [
                'rssi_statistics',
                'mcs_efficiency',
                'nexthop_utilization',
                'blackout_duration',
                'packet_loss',
                'network_coverage',
                'topology_metrics'
            ],
            'dependencies': []
        })
        return capabilities