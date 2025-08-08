#!/usr/bin/env python3
"""
Performance Scorer Service for Enhanced Individual Soldier Report System
Event-driven service that handles all performance scoring calculations and analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging
import asyncio
from dataclasses import dataclass
from enum import Enum

# Event system imports (these would be from your core module)
try:
    from core.event_bus import EventBus, Event
    from core.events import EventType
    from models.soldier_data import SoldierDataset
    from config.settings import Settings
except ImportError:
    # Fallback for standalone testing
    class EventBus:
        def subscribe(self, event_type: str, handler): pass
        def publish(self, event): pass
    
    class Event:
        def __init__(self, type, data=None, source=None): 
            self.type = type
            self.data = data
            self.source = source
    
    class EventType(Enum):
        SCORING_REQUESTED = "scoring_requested"
        SCORING_COMPLETED = "scoring_completed"
        SCORING_FAILED = "scoring_failed"


@dataclass
class ScoringRequest:
    """Request for performance scoring"""
    callsign: str
    soldier_data: pd.DataFrame
    request_id: Optional[str] = None
    custom_config: Optional[Dict[str, Any]] = None


@dataclass
class ScoringResult:
    """Result of performance scoring"""
    callsign: str
    performance_score: int
    stats: Dict[str, Any]
    safety_analysis: Dict[str, Any]
    status: str
    status_color: str
    request_id: Optional[str] = None
    error: Optional[str] = None


class PerformanceScorer:
    """
    Event-driven service that handles performance scoring and analysis for individual soldiers.
    Integrates with the event bus system for loose coupling and async processing.
    """
    
    def __init__(self, event_bus: EventBus, settings: Optional[Dict[str, Any]] = None):
        """
        Initialize the performance scorer service with event bus integration
        
        Args:
            event_bus: Central event dispatcher for the application
            settings: Optional configuration settings override
        """
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self._is_running = False
        self._pending_requests: Dict[str, ScoringRequest] = {}
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self._is_running = False
        self._pending_requests: Dict[str, ScoringRequest] = {}
        
        # Initialize scoring configuration
        self.scoring_config = {
            'base_score': 100,
            'activity_thresholds': {
                'low': 50,
                'moderate': 100,
                'high': 150
            },
            'battery_thresholds': {
                'critical': 20,
                'low': 40
            },
            'deductions': {
                'wounded': 10,
                'kia': 20,
                'low_activity': 15,
                'moderate_activity': 10,
                'critical_battery': 15,
                'low_battery': 8,
                'poor_communication': 5,
                'medical_alert': 3  # Reduced from 5 to be more fair
            },
            'bonuses': {
                'excellent_communication': 3,
                'combat_engagement': 5
            }
        }
        
        # Override with provided settings
        if settings:
            self._update_config_from_settings(settings)
        
        # Register event handlers
        self._register_event_handlers()
        
        self.logger.info("PerformanceScorer service initialized")
    
    def _update_config_from_settings(self, settings: Dict[str, Any]) -> None:
        """Update configuration from external settings"""
        if 'scoring' in settings:
            scoring_settings = settings['scoring']
            
            if 'deductions' in scoring_settings:
                self.scoring_config['deductions'].update(scoring_settings['deductions'])
            
            if 'bonuses' in scoring_settings:
                self.scoring_config['bonuses'].update(scoring_settings['bonuses'])
            
            if 'activity_thresholds' in scoring_settings:
                self.scoring_config['activity_thresholds'].update(scoring_settings['activity_thresholds'])
            
            if 'battery_thresholds' in scoring_settings:
                self.scoring_config['battery_thresholds'].update(scoring_settings['battery_thresholds'])
    
    def _register_event_handlers(self) -> None:
        """Register event handlers with the event bus"""
        self.event_bus.subscribe(
            EventType.SCORING_REQUESTED.value,
            self._handle_scoring_request
        )
        self.logger.debug("Event handlers registered")
    
    async def start_service(self) -> None:
        """Start the performance scorer service"""
        self._is_running = True
        self.logger.info("PerformanceScorer service started")
        
        # Publish service started event
        self.event_bus.publish(Event(
            type="service_started",
            data={"service": "PerformanceScorer"},
            source="PerformanceScorer"
        ))
    
    async def stop_service(self) -> None:
        """Stop the performance scorer service"""
        self._is_running = False
        self._pending_requests.clear()
        self.logger.info("PerformanceScorer service stopped")
        
        # Publish service stopped event
        self.event_bus.publish(Event(
            type="service_stopped",
            data={"service": "PerformanceScorer"},
            source="PerformanceScorer"
        ))
    
    def _handle_scoring_request(self, event: Event) -> None:
        """
        Handle scoring request events from the event bus
        
        Args:
            event: Event containing scoring request data
        """
        try:
            if not self._is_running:
                self.logger.warning("Received scoring request while service is stopped")
                return
            
            # Extract request data
            request_data = event.data
            callsign = request_data.get('callsign')
            soldier_data = request_data.get('soldier_data')
            request_id = request_data.get('request_id')
            custom_config = request_data.get('custom_config')
            
            if not callsign or soldier_data is None:
                raise ValueError("Missing required fields: callsign or soldier_data")
            
            # Create scoring request
            scoring_request = ScoringRequest(
                callsign=callsign,
                soldier_data=soldier_data,
                request_id=request_id,
                custom_config=custom_config
            )
            
            # Process the request asynchronously
            asyncio.create_task(self._process_scoring_request(scoring_request))
            
        except Exception as e:
            self.logger.error(f"Error handling scoring request: {e}")
            self._publish_scoring_error(event.data.get('request_id'), str(e))
    
    async def _process_scoring_request(self, request: ScoringRequest) -> None:
        """
        Process a scoring request asynchronously
        
        Args:
            request: Scoring request to process
        """
        try:
            if request.request_id:
                self._pending_requests[request.request_id] = request
            
            self.logger.info(f"Processing scoring request for soldier: {request.callsign}")
            
            # Apply custom configuration if provided
            original_config = self.scoring_config.copy()
            if request.custom_config:
                self._apply_custom_config(request.custom_config)
            
            try:
                # Calculate comprehensive statistics
                stats = self.calculate_comprehensive_stats(request.callsign, request.soldier_data)
                
                # Analyze safety
                safety_analysis = self.analyze_soldier_safety(request.soldier_data)
                
                # Calculate performance score
                performance_score = self.calculate_performance_score(stats, safety_analysis)
                
                # Get performance status
                status, status_color = self.get_performance_status(performance_score)
                
                # Create result
                result = ScoringResult(
                    callsign=request.callsign,
                    performance_score=performance_score,
                    stats=stats,
                    safety_analysis=safety_analysis,
                    status=status,
                    status_color=status_color,
                    request_id=request.request_id
                )
                
                # Publish success event
                self._publish_scoring_success(result)
                
            finally:
                # Restore original configuration
                if request.custom_config:
                    self.scoring_config = original_config
            
            # Remove from pending requests
            if request.request_id and request.request_id in self._pending_requests:
                del self._pending_requests[request.request_id]
                
            self.logger.info(f"Completed scoring for soldier: {request.callsign}")
            
        except Exception as e:
            self.logger.error(f"Error processing scoring request for {request.callsign}: {e}")
            self._publish_scoring_error(request.request_id, str(e), request.callsign)
            
            # Remove from pending requests on error
            if request.request_id and request.request_id in self._pending_requests:
                del self._pending_requests[request.request_id]
    
    def _apply_custom_config(self, custom_config: Dict[str, Any]) -> None:
        """Apply custom configuration for a specific request"""
        if 'deductions' in custom_config:
            self.scoring_config['deductions'].update(custom_config['deductions'])
        
        if 'bonuses' in custom_config:
            self.scoring_config['bonuses'].update(custom_config['bonuses'])
        
        if 'activity_thresholds' in custom_config:
            self.scoring_config['activity_thresholds'].update(custom_config['activity_thresholds'])
        
        if 'battery_thresholds' in custom_config:
            self.scoring_config['battery_thresholds'].update(custom_config['battery_thresholds'])
    
    def _publish_scoring_success(self, result: ScoringResult) -> None:
        """Publish scoring success event"""
        self.event_bus.publish(Event(
            type=EventType.SCORING_COMPLETED.value,
            data={
                'result': result,
                'callsign': result.callsign,
                'performance_score': result.performance_score,
                'status': result.status,
                'request_id': result.request_id
            },
            source="PerformanceScorer"
        ))
    
    def _publish_scoring_error(self, request_id: Optional[str], error: str, callsign: Optional[str] = None) -> None:
        """Publish scoring error event"""
        self.event_bus.publish(Event(
            type=EventType.SCORING_FAILED.value,
            data={
                'error': error,
                'request_id': request_id,
                'callsign': callsign
            },
            source="PerformanceScorer"
        ))
    
    # Service status and monitoring methods
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            'is_running': self._is_running,
            'pending_requests': len(self._pending_requests),
            'pending_request_ids': list(self._pending_requests.keys()),
            'config_loaded': bool(self.scoring_config)
        }
    
    def get_pending_requests(self) -> List[str]:
        """Get list of pending request IDs"""
        return list(self._pending_requests.keys())
    
    # Public API methods for external use (non-event driven)
    def score_soldier_sync(self, callsign: str, soldier_data: pd.DataFrame, 
                          custom_config: Optional[Dict[str, Any]] = None) -> ScoringResult:
        """
        Synchronous scoring method for direct API usage
        
        Args:
            callsign: Soldier callsign
            soldier_data: Soldier data DataFrame
            custom_config: Optional custom scoring configuration
            
        Returns:
            ScoringResult with performance analysis
        """
        try:
            # Apply custom configuration if provided
            original_config = None
            if custom_config:
                original_config = self.scoring_config.copy()
                self._apply_custom_config(custom_config)
            
            try:
                # Calculate comprehensive statistics
                stats = self.calculate_comprehensive_stats(callsign, soldier_data)
                
                # Analyze safety
                safety_analysis = self.analyze_soldier_safety(soldier_data)
                
                # Calculate performance score
                performance_score = self.calculate_performance_score(stats, safety_analysis)
                
                # Get performance status
                status, status_color = self.get_performance_status(performance_score)
                
                return ScoringResult(
                    callsign=callsign,
                    performance_score=performance_score,
                    stats=stats,
                    safety_analysis=safety_analysis,
                    status=status,
                    status_color=status_color
                )
                
            finally:
                # Restore original configuration
                if original_config:
                    self.scoring_config = original_config
                    
        except Exception as e:
            return ScoringResult(
                callsign=callsign,
                performance_score=0,
                stats={},
                safety_analysis={},
                status="ERROR",
                status_color="#ff0000",
                error=str(e)
            )
    
    def calculate_comprehensive_stats(self, callsign: str, soldier_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive soldier statistics"""
        stats = {
            'callsign': callsign,
            'total_records': len(soldier_data),
        }
        
        # Physical activity metrics
        stats.update(self._calculate_physical_metrics(soldier_data))
        
        # Heart rate analysis
        stats.update(self._calculate_heart_rate_metrics(soldier_data))
        
        # Temperature analysis
        stats.update(self._calculate_temperature_metrics(soldier_data))
        
        # Equipment status
        stats.update(self._calculate_equipment_metrics(soldier_data))
        
        # Posture and movement analysis
        stats.update(self._calculate_posture_metrics(soldier_data))
        
        # Combat effectiveness
        stats.update(self._calculate_combat_metrics(soldier_data))
        
        # Mission duration
        stats.update(self._calculate_mission_metrics(soldier_data))
        
        return stats
    
    def _calculate_physical_metrics(self, soldier_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate physical activity metrics"""
        metrics = {}
        
        if 'Step_Count' in soldier_data.columns:
            step_data = soldier_data['Step_Count'].dropna()
            if len(step_data) > 0:
                metrics.update({
                    'total_steps': step_data.sum(),
                    'avg_steps': step_data.mean(),
                    'max_steps': step_data.max(),
                    'min_steps': step_data.min()
                })
        
        # Fall incidents
        if 'Fall_Detection' in soldier_data.columns:
            metrics['fall_incidents'] = soldier_data['Fall_Detection'].sum()
        
        return metrics
    
    def _calculate_heart_rate_metrics(self, soldier_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate heart rate analysis metrics"""
        metrics = {}
        
        if 'Heart_Rate' in soldier_data.columns:
            hr_data = soldier_data['Heart_Rate'].dropna()
            if len(hr_data) > 0:
                metrics.update({
                    'min_heart_rate': hr_data.min(),
                    'avg_heart_rate': hr_data.mean(),
                    'max_heart_rate': hr_data.max(),
                    'abnormal_hr_low': len(hr_data[hr_data < 60]),
                    'abnormal_hr_high': len(hr_data[hr_data > 190])
                })
                
                metrics['abnormal_hr_total'] = metrics['abnormal_hr_low'] + metrics['abnormal_hr_high']
                metrics['hr_alert_triggered'] = metrics['abnormal_hr_total'] > 0
                
                # Heart rate zones
                metrics['hr_zones'] = {
                    'rest': len(hr_data[hr_data < 60]),
                    'normal': len(hr_data[(hr_data >= 60) & (hr_data < 100)]),
                    'elevated': len(hr_data[(hr_data >= 100) & (hr_data < 150)]),
                    'high': len(hr_data[(hr_data >= 150) & (hr_data < 180)]),
                    'extreme': len(hr_data[(hr_data >= 180) & (hr_data < 190)]),
                    'critical': len(hr_data[hr_data >= 190])
                }
        
        return metrics
    
    def _calculate_temperature_metrics(self, soldier_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate temperature analysis metrics"""
        metrics = {}
        
        if 'Temperature' in soldier_data.columns:
            temp_data = soldier_data['Temperature'].dropna()
            if len(temp_data) > 0:
                metrics.update({
                    'min_temperature': temp_data.min(),
                    'avg_temperature': temp_data.mean(),
                    'max_temperature': temp_data.max(),
                    'heat_stress_incidents': len(temp_data[temp_data > 104]),
                    'cold_stress_incidents': len(temp_data[temp_data < 95])
                })
        
        return metrics
    
    def _calculate_equipment_metrics(self, soldier_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate equipment status metrics"""
        metrics = {}
        
        # Battery status
        if 'Battery' in soldier_data.columns:
            battery_data = soldier_data['Battery'].dropna()
            if len(battery_data) > 0:
                metrics.update({
                    'min_battery': battery_data.min(),
                    'avg_battery': battery_data.mean(),
                    'max_battery': battery_data.max(),
                    'low_battery_incidents': len(battery_data[battery_data < 20]),
                    'critical_battery_incidents': len(battery_data[battery_data < 10])
                })
        
        # Communication quality
        if 'RSSI' in soldier_data.columns:
            rssi_data = soldier_data['RSSI'].dropna()
            if len(rssi_data) > 0:
                metrics.update({
                    'avg_rssi': rssi_data.mean(),
                    'min_rssi': rssi_data.min(),
                    'max_rssi': rssi_data.max()
                })
                
                # Communication quality rating
                avg_rssi = metrics['avg_rssi']
                if avg_rssi > -60:
                    metrics['comm_quality'] = 'Excellent'
                elif avg_rssi > -70:
                    metrics['comm_quality'] = 'Good'
                elif avg_rssi > -80:
                    metrics['comm_quality'] = 'Fair'
                else:
                    metrics['comm_quality'] = 'Poor'
        
        # Weapon information
        if 'Weapon' in soldier_data.columns:
            weapon_data = soldier_data['Weapon'].dropna()
            if len(weapon_data) > 0:
                metrics['primary_weapon'] = weapon_data.mode().iloc[0] if not weapon_data.mode().empty else 'Unknown'
        
        return metrics
    
    def _calculate_posture_metrics(self, soldier_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate posture and movement metrics"""
        metrics = {}
        
        if 'Posture' in soldier_data.columns:
            posture_data = soldier_data['Posture'].dropna()
            if len(posture_data) > 0:
                posture_counts = posture_data.value_counts()
                metrics['posture_distribution'] = posture_counts.to_dict()
                metrics['dominant_posture'] = posture_counts.index[0] if len(posture_counts) > 0 else 'Unknown'
                
                # Calculate posture changes
                posture_changes = 0
                for i in range(1, len(posture_data)):
                    if posture_data.iloc[i] != posture_data.iloc[i-1]:
                        posture_changes += 1
                metrics['posture_changes'] = posture_changes
                
                if posture_changes < 10:
                    metrics['posture_stability'] = 'Excellent'
                elif posture_changes < 20:
                    metrics['posture_stability'] = 'Good'
                else:
                    metrics['posture_stability'] = 'Fair'
        
        return metrics
    
    def _calculate_combat_metrics(self, soldier_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate combat effectiveness metrics"""
        metrics = {}
        
        # Casualty status
        if 'Casualty_State' in soldier_data.columns:
            casualty_data = soldier_data['Casualty_State'].dropna()
            if len(casualty_data) > 0:
                metrics['final_status'] = casualty_data.iloc[-1]
                
                # Count status changes
                casualty_changes = 0
                for i in range(1, len(casualty_data)):
                    if casualty_data.iloc[i] != casualty_data.iloc[i-1]:
                        casualty_changes += 1
                metrics['casualty_events'] = casualty_changes
        
        # Combat engagements
        if 'Shooter_Callsign' in soldier_data.columns:
            engagement_data = soldier_data['Shooter_Callsign'].dropna()
            metrics['combat_engagements'] = len(engagement_data)
            if len(engagement_data) > 0:
                metrics['unique_shooters'] = engagement_data.nunique()
        
        return metrics
    
    def _calculate_mission_metrics(self, soldier_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate mission duration and timing metrics"""
        metrics = {}
        
        if 'Time_Step' in soldier_data.columns:
            try:
                if pd.api.types.is_datetime64_any_dtype(soldier_data['Time_Step']):
                    start_time = soldier_data['Time_Step'].min()
                    end_time = soldier_data['Time_Step'].max()
                    metrics['mission_duration'] = (end_time - start_time).total_seconds() / 60  # minutes
            except:
                pass
        
        return metrics
    
    def analyze_soldier_safety(self, soldier_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze soldier safety metrics"""
        safety = {
            'overall_safety_score': 100,
            'temperature_risk': 'LOW',
            'physiological_stress': 'LOW',
            'heart_rate_alerts': [],
            'medical_alerts': [],
            'injury_risk': 'LOW',
            'equipment_risk': 'LOW'
        }
        
        # Temperature safety analysis
        safety.update(self._analyze_temperature_safety(soldier_data, safety))
        
        # Heart rate safety analysis
        safety.update(self._analyze_heart_rate_safety(soldier_data, safety))
        
        # Equipment safety analysis
        safety.update(self._analyze_equipment_safety(soldier_data, safety))
        
        return safety
    
    def _analyze_temperature_safety(self, soldier_data: pd.DataFrame, safety: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze temperature-related safety concerns"""
        updates = {}
        
        if 'Temperature' in soldier_data.columns:
            temp_data = soldier_data['Temperature'].dropna()
            if len(temp_data) > 0:
                max_temp = temp_data.max()
                min_temp = temp_data.min()
                
                if max_temp > 104:  # Heat stroke risk
                    updates['temperature_risk'] = 'CRITICAL'
                    safety['overall_safety_score'] -= 25
                    safety['medical_alerts'].append(f"HEAT EMERGENCY: {max_temp:.1f}°F - Immediate cooling required")
                elif max_temp > 100:
                    updates['temperature_risk'] = 'HIGH'
                    safety['overall_safety_score'] -= 15
                    safety['medical_alerts'].append(f"Heat stress detected: {max_temp:.1f}°F")
                
                if min_temp < 95:  # Hypothermia risk
                    safety['overall_safety_score'] -= 10
                    safety['medical_alerts'].append(f"Cold stress detected: {min_temp:.1f}°F")
        
        return updates
    
    def _analyze_heart_rate_safety(self, soldier_data: pd.DataFrame, safety: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze heart rate-related safety concerns"""
        updates = {}
        
        if 'Heart_Rate' in soldier_data.columns:
            hr_data = soldier_data['Heart_Rate'].dropna()
            if len(hr_data) > 0:
                max_hr = hr_data.max()
                min_hr = hr_data.min()
                
                if max_hr > 190:
                    updates['physiological_stress'] = 'CRITICAL'
                    safety['overall_safety_score'] -= 20
                    safety['heart_rate_alerts'].append(f"CARDIAC EMERGENCY: {max_hr:.0f} BPM")
                    safety['medical_alerts'].append(f"Immediate medical evaluation required - HR: {max_hr:.0f} BPM")
                elif max_hr > 180:
                    updates['physiological_stress'] = 'HIGH'
                    safety['overall_safety_score'] -= 10
                    safety['heart_rate_alerts'].append(f"Elevated heart rate: {max_hr:.0f} BPM")
                
                if min_hr < 60 and min_hr > 0:
                    safety['heart_rate_alerts'].append(f"Low heart rate detected: {min_hr:.0f} BPM")
                    safety['medical_alerts'].append(f"Bradycardia evaluation recommended - HR: {min_hr:.0f} BPM")
        
        return updates
    
    def _analyze_equipment_safety(self, soldier_data: pd.DataFrame, safety: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze equipment-related safety concerns"""
        updates = {}
        
        if 'Battery' in soldier_data.columns:
            battery_data = soldier_data['Battery'].dropna()
            if len(battery_data) > 0:
                min_battery = battery_data.min()
                if min_battery < 10:
                    updates['equipment_risk'] = 'CRITICAL'
                    safety['overall_safety_score'] -= 15
                    safety['medical_alerts'].append(f"Equipment failure risk - Battery: {min_battery}%")
                elif min_battery < 20:
                    updates['equipment_risk'] = 'HIGH'
                    safety['overall_safety_score'] -= 8
        
        return updates
    
    def calculate_performance_score(self, stats: Dict[str, Any], safety_analysis: Dict[str, Any]) -> int:
        """Calculate comprehensive performance score"""
        score = self.scoring_config['base_score']
        deductions = []
        bonuses = []
        
        # Activity performance
        if 'avg_steps' in stats:
            avg_steps = stats['avg_steps']
            if avg_steps < self.scoring_config['activity_thresholds']['low']:
                deduction = self.scoring_config['deductions']['low_activity']
                score -= deduction
                deductions.append(f"Low activity: -{deduction} points ({avg_steps:.0f} avg steps)")
            elif avg_steps < self.scoring_config['activity_thresholds']['moderate']:
                deduction = self.scoring_config['deductions']['moderate_activity']
                score -= deduction
                deductions.append(f"Moderate activity: -{deduction} points ({avg_steps:.0f} avg steps)")
        
        # Casualty status impact
        final_status = stats.get('final_status', 'GOOD')
        if final_status == 'WOUNDED':
            deduction = self.scoring_config['deductions']['wounded']
            score -= deduction
            deductions.append(f"Wounded status: -{deduction} points")
        elif final_status in ['KILL', 'KIA']:
            deduction = self.scoring_config['deductions']['kia']
            score -= deduction
            deductions.append(f"KIA status: -{deduction} points")
        
        # Equipment readiness
        if 'avg_battery' in stats:
            avg_battery = stats['avg_battery']
            if avg_battery < self.scoring_config['battery_thresholds']['critical']:
                deduction = self.scoring_config['deductions']['critical_battery']
                score -= deduction
                deductions.append(f"Critical battery: -{deduction} points ({avg_battery:.1f}%)")
            elif avg_battery < self.scoring_config['battery_thresholds']['low']:
                deduction = self.scoring_config['deductions']['low_battery']
                score -= deduction
                deductions.append(f"Low battery: -{deduction} points ({avg_battery:.1f}%)")
        
        # Communication quality
        if 'comm_quality' in stats:
            comm_quality = stats['comm_quality']
            if comm_quality == 'Poor':
                deduction = self.scoring_config['deductions']['poor_communication']
                score -= deduction
                deductions.append(f"Poor communication: -{deduction} points")
            elif comm_quality == 'Excellent':
                bonus = self.scoring_config['bonuses']['excellent_communication']
                score += bonus
                bonuses.append(f"Excellent communication: +{bonus} points")
        
        # Combat engagement bonus
        if 'combat_engagements' in stats and stats['combat_engagements'] > 0:
            bonus = min(self.scoring_config['bonuses']['combat_engagement'], stats['combat_engagements'])
            score += bonus
            bonuses.append(f"Combat engagement: +{bonus} points ({stats['combat_engagements']} engagements)")
        
        # Medical alerts (reduced penalty - safety focused)
        medical_alerts = len(safety_analysis.get('medical_alerts', []))
        if medical_alerts > 0:
            deduction = medical_alerts * self.scoring_config['deductions']['medical_alert']
            score -= deduction
            deductions.append(f"Medical alerts: -{deduction} points ({medical_alerts} alerts)")
        
        # Safety score impact (20% of deficit)
        safety_score = safety_analysis.get('overall_safety_score', 100)
        if safety_score < 100:
            deduction = int((100 - safety_score) * 0.2)
            score -= deduction
            deductions.append(f"Safety concerns: -{deduction} points")
        
        final_score = max(0, min(100, score))
        
        # Store breakdown
        stats['performance_breakdown'] = {
            'starting_score': self.scoring_config['base_score'],
            'final_score': final_score,
            'total_deductions': sum([int(d.split('-')[1].split(' ')[0]) for d in deductions if '-' in d]),
            'total_bonuses': sum([int(b.split('+')[1].split(' ')[0]) for b in bonuses if '+' in b]),
            'deduction_details': deductions,
            'bonus_details': bonuses
        }
        
        return final_score
    
    def get_performance_status(self, score: int) -> Tuple[str, str]:
        """Get performance status and color based on score"""
        if score >= 90:
            return "EXCELLENT - Exemplary performance", "#27ae60"
        elif score >= 80:
            return "GOOD - Above average performance", "#f39c12"
        elif score >= 70:
            return "SATISFACTORY - Meets requirements", "#e67e22"
        elif score >= 60:
            return "NEEDS IMPROVEMENT - Below standard", "#e74c3c"
        else:
            return "CRITICAL - Immediate attention required", "#c0392b"
    
    def update_scoring_config(self, config_updates: Dict[str, Any]) -> None:
        """Update scoring configuration with new values"""
        if 'deductions' in config_updates:
            self.scoring_config['deductions'].update(config_updates['deductions'])
        
        if 'bonuses' in config_updates:
            self.scoring_config['bonuses'].update(config_updates['bonuses'])
        
        if 'activity_thresholds' in config_updates:
            self.scoring_config['activity_thresholds'].update(config_updates['activity_thresholds'])
        
        if 'battery_thresholds' in config_updates:
            self.scoring_config['battery_thresholds'].update(config_updates['battery_thresholds'])
    
    def get_scoring_config(self) -> Dict[str, Any]:
        """Get current scoring configuration"""
        return self.scoring_config.copy()
    
    def generate_scoring_summary(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of scoring factors for transparency"""
        summary = {
            'activity_level': 'Unknown',
            'equipment_status': 'Unknown',
            'communication_quality': stats.get('comm_quality', 'Unknown'),
            'combat_participation': stats.get('combat_engagements', 0) > 0,
            'casualty_status': stats.get('final_status', 'Unknown'),
            'medical_concerns': stats.get('hr_alert_triggered', False)
        }
        
        # Activity level assessment
        if 'avg_steps' in stats:
            avg_steps = stats['avg_steps']
            if avg_steps >= self.scoring_config['activity_thresholds']['high']:
                summary['activity_level'] = 'High'
            elif avg_steps >= self.scoring_config['activity_thresholds']['moderate']:
                summary['activity_level'] = 'Moderate'
            elif avg_steps >= self.scoring_config['activity_thresholds']['low']:
                summary['activity_level'] = 'Low'
            else:
                summary['activity_level'] = 'Very Low'
        
        # Equipment status assessment
        if 'avg_battery' in stats:
            avg_battery = stats['avg_battery']
            if avg_battery >= 60:
                summary['equipment_status'] = 'Good'
            elif avg_battery >= self.scoring_config['battery_thresholds']['low']:
                summary['equipment_status'] = 'Fair'
            elif avg_battery >= self.scoring_config['battery_thresholds']['critical']:
                summary['equipment_status'] = 'Low'
            else:
                summary['equipment_status'] = 'Critical'
        
        return summary


def main():
    """Main function for testing the PerformanceScorer"""
    import pandas as pd
    
    # Create sample data for testing
    sample_data = pd.DataFrame({
        'Callsign': ['ALPHA1'] * 100,
        'Step_Count': np.random.randint(80, 120, 100),
        'Heart_Rate': np.random.randint(70, 150, 100),
        'Battery': np.random.randint(30, 100, 100),
        'Temperature': np.random.uniform(98, 102, 100),
        'RSSI': np.random.randint(-80, -50, 100),
        'Casualty_State': ['GOOD'] * 95 + ['WOUNDED'] * 5,
        'Posture': np.random.choice(['Standing', 'Kneeling', 'Prone'], 100)
    })
    
    # Test the scorer
    scorer = PerformanceScorer()
    stats = scorer.calculate_comprehensive_stats('ALPHA1', sample_data)
    safety = scorer.analyze_soldier_safety(sample_data)
    score = scorer.calculate_performance_score(stats, safety)
    status, color = scorer.get_performance_status(score)
    summary = scorer.generate_scoring_summary(stats)
    
    print("🎖️ Performance Scorer Test Results")
    print("=" * 50)
    print(f"Soldier: {stats['callsign']}")
    print(f"Performance Score: {score}/100")
    print(f"Status: {status}")
    print(f"Total Records: {stats['total_records']}")
    print(f"Average Steps: {stats.get('avg_steps', 0):.1f}")
    print(f"Average Heart Rate: {stats.get('avg_heart_rate', 0):.1f} BPM")
    print(f"Communication Quality: {stats.get('comm_quality', 'Unknown')}")
    print(f"Safety Score: {safety['overall_safety_score']}/100")
    print("\nScoring Summary:")
    for key, value in summary.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")


if __name__ == "__main__":
    main()