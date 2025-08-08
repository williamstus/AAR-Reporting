#!/usr/bin/env python3
"""
Safety Analyzer Service for Enhanced Individual Soldier Report System
Event-driven service that handles all safety-specific analysis and medical monitoring
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging
import asyncio
from dataclasses import dataclass
from enum import Enum
import time
from datetime import datetime

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
        SAFETY_ANALYSIS_REQUESTED = "safety_analysis_requested"
        SAFETY_ANALYSIS_COMPLETED = "safety_analysis_completed"
        SAFETY_ANALYSIS_FAILED = "safety_analysis_failed"
        MEDICAL_ALERT_TRIGGERED = "medical_alert_triggered"
        SAFETY_THRESHOLD_EXCEEDED = "safety_threshold_exceeded"


class SafetyRiskLevel(Enum):
    """Safety risk level enumeration"""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MedicalAlertType(Enum):
    """Medical alert type enumeration"""
    HEART_RATE_HIGH = "heart_rate_high"
    HEART_RATE_LOW = "heart_rate_low"
    TEMPERATURE_HIGH = "temperature_high"
    TEMPERATURE_LOW = "temperature_low"
    EQUIPMENT_FAILURE = "equipment_failure"
    FALL_DETECTED = "fall_detected"


@dataclass
class SafetyAnalysisRequest:
    """Request for safety analysis"""
    callsign: str
    soldier_data: pd.DataFrame
    request_id: Optional[str] = None
    analysis_type: str = "comprehensive"  # comprehensive, real_time, periodic
    custom_thresholds: Optional[Dict[str, Any]] = None


@dataclass
class MedicalAlert:
    """Medical alert data structure"""
    alert_type: MedicalAlertType
    severity: SafetyRiskLevel
    message: str
    value: float
    threshold: float
    timestamp: Optional[datetime] = None
    requires_immediate_action: bool = False


@dataclass
class SafetyAnalysisResult:
    """Result of safety analysis"""
    callsign: str
    overall_safety_score: int
    risk_level: SafetyRiskLevel
    medical_alerts: List[MedicalAlert]
    safety_metrics: Dict[str, Any]
    recommendations: List[str]
    request_id: Optional[str] = None
    analysis_timestamp: Optional[datetime] = None
    error: Optional[str] = None


class SafetyAnalyzer:
    """
    Event-driven service that handles safety analysis and medical monitoring for soldiers.
    Provides real-time medical alerts and comprehensive safety assessments.
    """
    
    def __init__(self, event_bus: EventBus, settings: Optional[Dict[str, Any]] = None):
        """
        Initialize the safety analyzer service with event bus integration
        
        Args:
            event_bus: Central event dispatcher for the application
            settings: Optional configuration settings override
        """
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self._is_running = False
        self._pending_requests: Dict[str, SafetyAnalysisRequest] = {}
        self._alert_history: List[MedicalAlert] = []
        
        # Initialize safety configuration with medical thresholds
        self.safety_config = {
            'heart_rate_thresholds': {
                'critical_high': 190,  # Immediate medical attention
                'high': 180,          # Monitor closely
                'normal_high': 150,   # Elevated but acceptable
                'normal_low': 60,     # Normal resting lower bound
                'low': 50,            # Bradycardia concern
                'critical_low': 40    # Emergency
            },
            'temperature_thresholds': {
                'critical_high': 104.0,  # Heat stroke risk (°F)
                'high': 102.0,          # Heat exhaustion
                'normal_high': 100.4,   # Fever
                'normal_low': 97.0,     # Normal range lower
                'low': 95.0,            # Hypothermia risk
                'critical_low': 90.0    # Severe hypothermia
            },
            'equipment_thresholds': {
                'battery_critical': 10,  # Critical battery level
                'battery_low': 20,       # Low battery warning
                'signal_poor': -80       # Poor communication signal (dBm)
            },
            'physiological_monitoring': {
                'fall_detection_enabled': True,
                'continuous_monitoring': True,
                'alert_escalation_time': 300,  # 5 minutes
                'medical_review_required': True
            },
            'safety_scoring': {
                'base_score': 100,
                'critical_alert_penalty': 25,
                'high_alert_penalty': 15,
                'moderate_alert_penalty': 5,
                'equipment_failure_penalty': 20
            }
        }
        
        # Override with provided settings
        if settings:
            self._update_config_from_settings(settings)
        
        # Register event handlers
        self._register_event_handlers()
        
        self.logger.info("SafetyAnalyzer service initialized")
    
    def _update_config_from_settings(self, settings: Dict[str, Any]) -> None:
        """Update configuration from external settings"""
        if 'safety' in settings:
            safety_settings = settings['safety']
            
            for config_section in ['heart_rate_thresholds', 'temperature_thresholds', 
                                 'equipment_thresholds', 'physiological_monitoring', 'safety_scoring']:
                if config_section in safety_settings:
                    self.safety_config[config_section].update(safety_settings[config_section])
    
    def _register_event_handlers(self) -> None:
        """Register event handlers with the event bus"""
        self.event_bus.subscribe(
            EventType.SAFETY_ANALYSIS_REQUESTED.value,
            self._handle_safety_analysis_request
        )
        
        # Subscribe to real-time data events for immediate alerts
        self.event_bus.subscribe("real_time_data_received", self._handle_real_time_data)
        
        self.logger.debug("Event handlers registered")
    
    async def start_service(self) -> None:
        """Start the safety analyzer service"""
        self._is_running = True
        self.logger.info("SafetyAnalyzer service started")
        
        # Start background monitoring tasks
        asyncio.create_task(self._background_monitoring())
        
        # Publish service started event
        self.event_bus.publish(Event(
            type="service_started",
            data={"service": "SafetyAnalyzer"},
            source="SafetyAnalyzer"
        ))
    
    async def stop_service(self) -> None:
        """Stop the safety analyzer service"""
        self._is_running = False
        self._pending_requests.clear()
        self.logger.info("SafetyAnalyzer service stopped")
        
        # Publish service stopped event
        self.event_bus.publish(Event(
            type="service_stopped",
            data={"service": "SafetyAnalyzer"},
            source="SafetyAnalyzer"
        ))
    
    async def _background_monitoring(self) -> None:
        """Background task for continuous safety monitoring"""
        while self._is_running:
            try:
                # Clean up old alerts (older than 24 hours)
                cutoff_time = time.time() - (24 * 3600)
                self._alert_history = [
                    alert for alert in self._alert_history 
                    if alert.timestamp and alert.timestamp.timestamp() > cutoff_time
                ]
                
                # Check for escalation of existing alerts
                await self._check_alert_escalation()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in background monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _check_alert_escalation(self) -> None:
        """Check if any alerts need escalation"""
        # Implementation for alert escalation logic
        # This would check if critical alerts haven't been addressed
        pass
    
    def _handle_safety_analysis_request(self, event: Event) -> None:
        """
        Handle safety analysis request events from the event bus
        
        Args:
            event: Event containing safety analysis request data
        """
        try:
            if not self._is_running:
                self.logger.warning("Received safety analysis request while service is stopped")
                return
            
            # Extract request data
            request_data = event.data
            callsign = request_data.get('callsign')
            soldier_data = request_data.get('soldier_data')
            request_id = request_data.get('request_id')
            analysis_type = request_data.get('analysis_type', 'comprehensive')
            custom_thresholds = request_data.get('custom_thresholds')
            
            if not callsign or soldier_data is None:
                raise ValueError("Missing required fields: callsign or soldier_data")
            
            # Create safety analysis request
            safety_request = SafetyAnalysisRequest(
                callsign=callsign,
                soldier_data=soldier_data,
                request_id=request_id,
                analysis_type=analysis_type,
                custom_thresholds=custom_thresholds
            )
            
            # Process the request asynchronously
            asyncio.create_task(self._process_safety_analysis_request(safety_request))
            
        except Exception as e:
            self.logger.error(f"Error handling safety analysis request: {e}")
            self._publish_safety_analysis_error(event.data.get('request_id'), str(e))
    
    def _handle_real_time_data(self, event: Event) -> None:
        """Handle real-time data for immediate safety alerts"""
        try:
            data = event.data
            callsign = data.get('callsign')
            
            # Check for immediate safety concerns
            alerts = self._check_immediate_safety_alerts(data)
            
            if alerts:
                for alert in alerts:
                    self._publish_medical_alert(callsign, alert)
                    
        except Exception as e:
            self.logger.error(f"Error handling real-time data: {e}")
    
    async def _process_safety_analysis_request(self, request: SafetyAnalysisRequest) -> None:
        """
        Process a safety analysis request asynchronously
        
        Args:
            request: Safety analysis request to process
        """
        try:
            if request.request_id:
                self._pending_requests[request.request_id] = request
            
            self.logger.info(f"Processing safety analysis for soldier: {request.callsign}")
            
            # Apply custom thresholds if provided
            original_config = self.safety_config.copy()
            if request.custom_thresholds:
                self._apply_custom_thresholds(request.custom_thresholds)
            
            try:
                # Perform comprehensive safety analysis
                result = self._analyze_soldier_safety_comprehensive(request)
                
                # Publish success event
                self._publish_safety_analysis_success(result)
                
            finally:
                # Restore original configuration
                if request.custom_thresholds:
                    self.safety_config = original_config
            
            # Remove from pending requests
            if request.request_id and request.request_id in self._pending_requests:
                del self._pending_requests[request.request_id]
                
            self.logger.info(f"Completed safety analysis for soldier: {request.callsign}")
            
        except Exception as e:
            self.logger.error(f"Error processing safety analysis for {request.callsign}: {e}")
            self._publish_safety_analysis_error(request.request_id, str(e), request.callsign)
            
            # Remove from pending requests on error
            if request.request_id and request.request_id in self._pending_requests:
                del self._pending_requests[request.request_id]
    
    def _analyze_soldier_safety_comprehensive(self, request: SafetyAnalysisRequest) -> SafetyAnalysisResult:
        """Perform comprehensive safety analysis"""
        callsign = request.callsign
        soldier_data = request.soldier_data
        
        # Initialize result
        safety_metrics = {}
        medical_alerts = []
        recommendations = []
        overall_score = self.safety_config['safety_scoring']['base_score']
        
        # Heart rate analysis
        hr_metrics, hr_alerts = self._analyze_heart_rate(soldier_data)
        safety_metrics.update(hr_metrics)
        medical_alerts.extend(hr_alerts)
        
        # Temperature analysis
        temp_metrics, temp_alerts = self._analyze_temperature(soldier_data)
        safety_metrics.update(temp_metrics)
        medical_alerts.extend(temp_alerts)
        
        # Equipment safety analysis
        equipment_metrics, equipment_alerts = self._analyze_equipment_safety(soldier_data)
        safety_metrics.update(equipment_metrics)
        medical_alerts.extend(equipment_alerts)
        
        # Fall detection analysis
        fall_metrics, fall_alerts = self._analyze_fall_detection(soldier_data)
        safety_metrics.update(fall_metrics)
        medical_alerts.extend(fall_alerts)
        
        # Calculate overall safety score
        overall_score = self._calculate_safety_score(medical_alerts, overall_score)
        
        # Determine risk level
        risk_level = self._determine_risk_level(medical_alerts, overall_score)
        
        # Generate recommendations
        recommendations = self._generate_safety_recommendations(medical_alerts, safety_metrics)
        
        # Store alerts in history
        for alert in medical_alerts:
            alert.timestamp = datetime.now()
            self._alert_history.append(alert)
        
        return SafetyAnalysisResult(
            callsign=callsign,
            overall_safety_score=overall_score,
            risk_level=risk_level,
            medical_alerts=medical_alerts,
            safety_metrics=safety_metrics,
            recommendations=recommendations,
            request_id=request.request_id,
            analysis_timestamp=datetime.now()
        )
    
    def _analyze_heart_rate(self, soldier_data: pd.DataFrame) -> Tuple[Dict[str, Any], List[MedicalAlert]]:
        """Analyze heart rate data for safety concerns"""
        metrics = {}
        alerts = []
        
        if 'Heart_Rate' not in soldier_data.columns:
            return metrics, alerts
        
        hr_data = soldier_data['Heart_Rate'].dropna()
        if len(hr_data) == 0:
            return metrics, alerts
        
        # Basic statistics
        metrics.update({
            'min_heart_rate': hr_data.min(),
            'avg_heart_rate': hr_data.mean(),
            'max_heart_rate': hr_data.max(),
            'hr_std_deviation': hr_data.std()
        })
        
        # Threshold checks
        thresholds = self.safety_config['heart_rate_thresholds']
        max_hr = hr_data.max()
        min_hr = hr_data.min()
        
        # High heart rate alerts
        if max_hr >= thresholds['critical_high']:
            alerts.append(MedicalAlert(
                alert_type=MedicalAlertType.HEART_RATE_HIGH,
                severity=SafetyRiskLevel.CRITICAL,
                message=f"CARDIAC EMERGENCY: Heart rate {max_hr:.0f} BPM exceeds critical threshold",
                value=max_hr,
                threshold=thresholds['critical_high'],
                requires_immediate_action=True
            ))
        elif max_hr >= thresholds['high']:
            alerts.append(MedicalAlert(
                alert_type=MedicalAlertType.HEART_RATE_HIGH,
                severity=SafetyRiskLevel.HIGH,
                message=f"Elevated heart rate detected: {max_hr:.0f} BPM",
                value=max_hr,
                threshold=thresholds['high']
            ))
        
        # Low heart rate alerts
        if min_hr <= thresholds['critical_low']:
            alerts.append(MedicalAlert(
                alert_type=MedicalAlertType.HEART_RATE_LOW,
                severity=SafetyRiskLevel.CRITICAL,
                message=f"CARDIAC EMERGENCY: Heart rate {min_hr:.0f} BPM below critical threshold",
                value=min_hr,
                threshold=thresholds['critical_low'],
                requires_immediate_action=True
            ))
        elif min_hr <= thresholds['low']:
            alerts.append(MedicalAlert(
                alert_type=MedicalAlertType.HEART_RATE_LOW,
                severity=SafetyRiskLevel.HIGH,
                message=f"Bradycardia detected: {min_hr:.0f} BPM",
                value=min_hr,
                threshold=thresholds['low']
            ))
        
        # Additional analysis
        metrics['hr_variability'] = hr_data.std()
        metrics['hr_above_normal'] = len(hr_data[hr_data > thresholds['normal_high']])
        metrics['hr_below_normal'] = len(hr_data[hr_data < thresholds['normal_low']])
        
        return metrics, alerts
    
    def _analyze_temperature(self, soldier_data: pd.DataFrame) -> Tuple[Dict[str, Any], List[MedicalAlert]]:
        """Analyze temperature data for safety concerns"""
        metrics = {}
        alerts = []
        
        if 'Temperature' not in soldier_data.columns:
            return metrics, alerts
        
        temp_data = soldier_data['Temperature'].dropna()
        if len(temp_data) == 0:
            return metrics, alerts
        
        # Basic statistics
        metrics.update({
            'min_temperature': temp_data.min(),
            'avg_temperature': temp_data.mean(),
            'max_temperature': temp_data.max(),
            'temp_std_deviation': temp_data.std()
        })
        
        # Threshold checks
        thresholds = self.safety_config['temperature_thresholds']
        max_temp = temp_data.max()
        min_temp = temp_data.min()
        
        # High temperature alerts
        if max_temp >= thresholds['critical_high']:
            alerts.append(MedicalAlert(
                alert_type=MedicalAlertType.TEMPERATURE_HIGH,
                severity=SafetyRiskLevel.CRITICAL,
                message=f"HEAT EMERGENCY: Temperature {max_temp:.1f}°F - Immediate cooling required",
                value=max_temp,
                threshold=thresholds['critical_high'],
                requires_immediate_action=True
            ))
        elif max_temp >= thresholds['high']:
            alerts.append(MedicalAlert(
                alert_type=MedicalAlertType.TEMPERATURE_HIGH,
                severity=SafetyRiskLevel.HIGH,
                message=f"Heat stress detected: {max_temp:.1f}°F",
                value=max_temp,
                threshold=thresholds['high']
            ))
        
        # Low temperature alerts
        if min_temp <= thresholds['critical_low']:
            alerts.append(MedicalAlert(
                alert_type=MedicalAlertType.TEMPERATURE_LOW,
                severity=SafetyRiskLevel.CRITICAL,
                message=f"HYPOTHERMIA EMERGENCY: Temperature {min_temp:.1f}°F",
                value=min_temp,
                threshold=thresholds['critical_low'],
                requires_immediate_action=True
            ))
        elif min_temp <= thresholds['low']:
            alerts.append(MedicalAlert(
                alert_type=MedicalAlertType.TEMPERATURE_LOW,
                severity=SafetyRiskLevel.HIGH,
                message=f"Cold stress detected: {min_temp:.1f}°F",
                value=min_temp,
                threshold=thresholds['low']
            ))
        
        return metrics, alerts
    
    def _analyze_equipment_safety(self, soldier_data: pd.DataFrame) -> Tuple[Dict[str, Any], List[MedicalAlert]]:
        """Analyze equipment status for safety implications"""
        metrics = {}
        alerts = []
        
        # Battery analysis
        if 'Battery' in soldier_data.columns:
            battery_data = soldier_data['Battery'].dropna()
            if len(battery_data) > 0:
                min_battery = battery_data.min()
                avg_battery = battery_data.mean()
                
                metrics.update({
                    'min_battery': min_battery,
                    'avg_battery': avg_battery,
                    'battery_critical_incidents': len(battery_data[battery_data < 10])
                })
                
                thresholds = self.safety_config['equipment_thresholds']
                
                if min_battery <= thresholds['battery_critical']:
                    alerts.append(MedicalAlert(
                        alert_type=MedicalAlertType.EQUIPMENT_FAILURE,
                        severity=SafetyRiskLevel.HIGH,
                        message=f"Critical equipment failure risk - Battery: {min_battery}%",
                        value=min_battery,
                        threshold=thresholds['battery_critical']
                    ))
        
        # Communication signal analysis
        if 'RSSI' in soldier_data.columns:
            rssi_data = soldier_data['RSSI'].dropna()
            if len(rssi_data) > 0:
                min_rssi = rssi_data.min()
                avg_rssi = rssi_data.mean()
                
                metrics.update({
                    'min_rssi': min_rssi,
                    'avg_rssi': avg_rssi,
                    'signal_quality': 'Good' if avg_rssi > -70 else 'Poor'
                })
                
                if min_rssi < self.safety_config['equipment_thresholds']['signal_poor']:
                    alerts.append(MedicalAlert(
                        alert_type=MedicalAlertType.EQUIPMENT_FAILURE,
                        severity=SafetyRiskLevel.MODERATE,
                        message=f"Communication failure risk - Signal: {min_rssi} dBm",
                        value=min_rssi,
                        threshold=self.safety_config['equipment_thresholds']['signal_poor']
                    ))
        
        return metrics, alerts
    
    def _analyze_fall_detection(self, soldier_data: pd.DataFrame) -> Tuple[Dict[str, Any], List[MedicalAlert]]:
        """Analyze fall detection data"""
        metrics = {}
        alerts = []
        
        if 'Fall_Detection' not in soldier_data.columns:
            return metrics, alerts
        
        fall_data = soldier_data['Fall_Detection'].dropna()
        if len(fall_data) == 0:
            return metrics, alerts
        
        total_falls = fall_data.sum()
        metrics['total_falls'] = total_falls
        
        if total_falls > 0:
            alerts.append(MedicalAlert(
                alert_type=MedicalAlertType.FALL_DETECTED,
                severity=SafetyRiskLevel.HIGH if total_falls > 2 else SafetyRiskLevel.MODERATE,
                message=f"Fall detection: {total_falls} incident(s) detected",
                value=total_falls,
                threshold=0,
                requires_immediate_action=total_falls > 2
            ))
        
        return metrics, alerts
    
    def _check_immediate_safety_alerts(self, data: Dict[str, Any]) -> List[MedicalAlert]:
        """Check real-time data for immediate safety alerts"""
        alerts = []
        
        # Heart rate check
        if 'heart_rate' in data:
            hr = data['heart_rate']
            thresholds = self.safety_config['heart_rate_thresholds']
            
            if hr >= thresholds['critical_high'] or hr <= thresholds['critical_low']:
                alerts.append(MedicalAlert(
                    alert_type=MedicalAlertType.HEART_RATE_HIGH if hr >= thresholds['critical_high'] else MedicalAlertType.HEART_RATE_LOW,
                    severity=SafetyRiskLevel.CRITICAL,
                    message=f"IMMEDIATE CARDIAC ALERT: Heart rate {hr:.0f} BPM",
                    value=hr,
                    threshold=thresholds['critical_high'] if hr >= thresholds['critical_high'] else thresholds['critical_low'],
                    requires_immediate_action=True
                ))
        
        # Temperature check
        if 'temperature' in data:
            temp = data['temperature']
            thresholds = self.safety_config['temperature_thresholds']
            
            if temp >= thresholds['critical_high'] or temp <= thresholds['critical_low']:
                alerts.append(MedicalAlert(
                    alert_type=MedicalAlertType.TEMPERATURE_HIGH if temp >= thresholds['critical_high'] else MedicalAlertType.TEMPERATURE_LOW,
                    severity=SafetyRiskLevel.CRITICAL,
                    message=f"IMMEDIATE TEMPERATURE ALERT: {temp:.1f}°F",
                    value=temp,
                    threshold=thresholds['critical_high'] if temp >= thresholds['critical_high'] else thresholds['critical_low'],
                    requires_immediate_action=True
                ))
        
        # Fall detection check
        if data.get('fall_detected', False):
            alerts.append(MedicalAlert(
                alert_type=MedicalAlertType.FALL_DETECTED,
                severity=SafetyRiskLevel.HIGH,
                message="FALL DETECTED - Immediate assessment required",
                value=1,
                threshold=0,
                requires_immediate_action=True
            ))
        
        return alerts
    
    def _calculate_safety_score(self, alerts: List[MedicalAlert], base_score: int) -> int:
        """Calculate overall safety score based on alerts"""
        score = base_score
        scoring = self.safety_config['safety_scoring']
        
        for alert in alerts:
            if alert.severity == SafetyRiskLevel.CRITICAL:
                score -= scoring['critical_alert_penalty']
            elif alert.severity == SafetyRiskLevel.HIGH:
                score -= scoring['high_alert_penalty']
            elif alert.severity == SafetyRiskLevel.MODERATE:
                score -= scoring['moderate_alert_penalty']
        
        return max(0, min(100, score))
    
    def _determine_risk_level(self, alerts: List[MedicalAlert], safety_score: int) -> SafetyRiskLevel:
        """Determine overall risk level"""
        # Check for critical alerts
        if any(alert.severity == SafetyRiskLevel.CRITICAL for alert in alerts):
            return SafetyRiskLevel.CRITICAL
        
        # Check for high severity alerts
        if any(alert.severity == SafetyRiskLevel.HIGH for alert in alerts):
            return SafetyRiskLevel.HIGH
        
        # Based on safety score
        if safety_score < 70:
            return SafetyRiskLevel.HIGH
        elif safety_score < 85:
            return SafetyRiskLevel.MODERATE
        else:
            return SafetyRiskLevel.LOW
    
    def _generate_safety_recommendations(self, alerts: List[MedicalAlert], metrics: Dict[str, Any]) -> List[str]:
        """Generate safety recommendations based on analysis"""
        recommendations = []
        
        # Critical alerts require immediate action
        critical_alerts = [alert for alert in alerts if alert.requires_immediate_action]
        if critical_alerts:
            recommendations.append("🚨 IMMEDIATE ACTION REQUIRED - Medical evaluation needed")
            recommendations.append("📞 Contact medical personnel immediately")
        
        # Heart rate recommendations
        hr_alerts = [alert for alert in alerts if alert.alert_type in [MedicalAlertType.HEART_RATE_HIGH, MedicalAlertType.HEART_RATE_LOW]]
        if hr_alerts:
            recommendations.append("❤️ Cardiac monitoring recommended - Check for underlying conditions")
        
        # Temperature recommendations
        temp_alerts = [alert for alert in alerts if alert.alert_type in [MedicalAlertType.TEMPERATURE_HIGH, MedicalAlertType.TEMPERATURE_LOW]]
        if temp_alerts:
            recommendations.append("🌡️ Temperature management protocols - Adjust environmental conditions")
        
        # Equipment recommendations
        equipment_alerts = [alert for alert in alerts if alert.alert_type == MedicalAlertType.EQUIPMENT_FAILURE]
        if equipment_alerts:
            recommendations.append("🔧 Equipment maintenance required - Check batteries and connections")
        
        # Fall recommendations
        fall_alerts = [alert for alert in alerts if alert.alert_type == MedicalAlertType.FALL_DETECTED]
        if fall_alerts:
            recommendations.append("🏃 Injury assessment required - Check for trauma or mobility issues")
        
        # General recommendations
        if not alerts:
            recommendations.append("✅ Continue current safety protocols - All metrics within normal ranges")
        else:
            recommendations.append("📊 Increase monitoring frequency until all alerts are resolved")
        
        return recommendations
    
    def _apply_custom_thresholds(self, custom_thresholds: Dict[str, Any]) -> None:
        """Apply custom safety thresholds for specific analysis"""
        for threshold_category in ['heart_rate_thresholds', 'temperature_thresholds', 'equipment_thresholds']:
            if threshold_category in custom_thresholds:
                self.safety_config[threshold_category].update(custom_thresholds[threshold_category])
    
    def _publish_safety_analysis_success(self, result: SafetyAnalysisResult) -> None:
        """Publish safety analysis success event"""
        self.event_bus.publish(Event(
            type=EventType.SAFETY_ANALYSIS_COMPLETED.value,
            data={
                'result': result,
                'callsign': result.callsign,
                'risk_level': result.risk_level.value,
                'alert_count': len(result.medical_alerts),
                'request_id': result.request_id
            },
            source="SafetyAnalyzer"
        ))
        
        # Publish individual medical alerts
        for alert in result.medical_alerts:
            if alert.requires_immediate_action:
                self._publish_medical_alert(result.callsign, alert)
    
    def _publish_medical_alert(self, callsign: str, alert: MedicalAlert) -> None:
        """Publish medical alert event"""
        self.event_bus.publish(Event(
            type=EventType.MEDICAL_ALERT_TRIGGERED.value,
            data={
                'callsign': callsign,
                'alert_type': alert.alert_type.value,
                'severity': alert.severity.value,
                'message': alert.message,
                'value': alert.value,
                'threshold': alert.threshold,
                'requires_immediate_action': alert.requires_immediate_action
            },
            source="SafetyAnalyzer"
        ))
    
    def _publish_safety_analysis_error(self, request_id: Optional[str], error: str, callsign: Optional[str] = None) -> None:
        """Publish safety analysis error event"""
        self.event_bus.publish(Event(
            type=EventType.SAFETY_ANALYSIS_FAILED.value,
            data={
                'error': error,
                'request_id': request_id,
                'callsign': callsign
            },
            source="SafetyAnalyzer"
        ))
    
    # Service status and monitoring methods
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            'is_running': self._is_running,
            'pending_requests': len(self._pending_requests),
            'alert_history_count': len(self._alert_history),
            'config_loaded': bool(self.safety_config),
            'monitoring_enabled': self.safety_config['physiological_monitoring']['continuous_monitoring']
        }
    
    def get_alert_history(self, hours: int = 24) -> List[MedicalAlert]:
        """Get medical alert history for specified hours"""
        cutoff_time = time.time() - (hours * 3600)
        return [
            alert for alert in self._alert_history 
            if alert.timestamp and alert.timestamp.timestamp() > cutoff_time
        ]
    
    def get_safety_thresholds(self) -> Dict[str, Any]:
        """Get current safety thresholds"""
        return {
            'heart_rate': self.safety_config['heart_rate_thresholds'],
            'temperature': self.safety_config['temperature_thresholds'],
            'equipment': self.safety_config['equipment_thresholds']
        }
    
    # Public API methods for external use (non-event driven)
    def analyze_soldier_safety_sync(self, callsign: str, soldier_data: pd.DataFrame, 
                                  custom_thresholds: Optional[Dict[str, Any]] = None) -> SafetyAnalysisResult:
        """
        Synchronous safety analysis method for direct API usage
        
        Args:
            callsign: Soldier callsign
            soldier_data: Soldier data DataFrame
            custom_thresholds: Optional custom safety thresholds
            
        Returns:
            SafetyAnalysisResult with comprehensive safety analysis
        """
        try:
            # Create request
            request = SafetyAnalysisRequest(
                callsign=callsign,
                soldier_data=soldier_data,
                analysis_type="comprehensive",
                custom_thresholds=custom_thresholds
            )
            
            # Apply custom thresholds if provided
            original_config = None
            if custom_thresholds:
                original_config = self.safety_config.copy()
                self._apply_custom_thresholds(custom_thresholds)
            
            try:
                return self._analyze_soldier_safety_comprehensive(request)
            finally:
                # Restore original configuration
                if original_config:
                    self.safety_config = original_config
                    
        except Exception as e:
            return SafetyAnalysisResult(
                callsign=callsign,
                overall_safety_score=0,
                risk_level=SafetyRiskLevel.CRITICAL,
                medical_alerts=[],
                safety_metrics={},
                recommendations=["Error in safety analysis - Manual review required"],
                error=str(e),
                analysis_timestamp=datetime.now()
            )


def main():
    """Main function for testing the SafetyAnalyzer service"""
    import pandas as pd
    
    # Create sample data for testing
    sample_data = pd.DataFrame({
        'Callsign': ['ALPHA1'] * 100,
        'Heart_Rate': np.concatenate([
            np.random.randint(70, 150, 95),  # Normal range
            [200, 195, 192, 45, 35]  # Some critical values
        ]),
        'Temperature': np.concatenate([
            np.random.uniform(98, 102, 97),  # Normal range
            [105.2, 106.1, 93.5]  # Some critical values
        ]),
        'Battery': np.random.randint(30, 100, 100),
        'Fall_Detection': [0] * 98 + [1, 1]  # Two falls
    })
    
    # Test the service
    event_bus = EventBus()
    analyzer = SafetyAnalyzer(event_bus)
    result = analyzer.analyze_soldier_safety_sync('ALPHA1', sample_data)
    
    print("🛡️ SafetyAnalyzer Test Results")
    print("=" * 50)
    print(f"Soldier: {result.callsign}")
    print(f"Safety Score: {result.overall_safety_score}/100")
    print(f"Risk Level: {result.risk_level.value}")
    print(f"Medical Alerts: {len(result.medical_alerts)}")
    
    for alert in result.medical_alerts:
        print(f"  - {alert.severity.value}: {alert.message}")
    
    print(f"Recommendations: {len(result.recommendations)}")
    for rec in result.recommendations:
        print(f"  • {rec}")


if __name__ == "__main__":
    main()