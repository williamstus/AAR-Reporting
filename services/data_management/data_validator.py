# services/data_management/data_validation.py - Event-Driven Data Validation Service
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import re
from abc import ABC, abstractmethod

from core.event_bus import EventBus, Event, EventType
from core.models import (
    AnalysisDomain, DataQualityMetrics, SystemConfiguration, Alert, AlertLevel
)

class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ValidationRuleType(Enum):
    """Types of validation rules"""
    REQUIRED_COLUMN = "required_column"
    DATA_TYPE = "data_type"
    VALUE_RANGE = "value_range"
    PATTERN_MATCH = "pattern_match"
    BUSINESS_RULE = "business_rule"
    REFERENTIAL_INTEGRITY = "referential_integrity"
    DATA_CONSISTENCY = "data_consistency"
    TEMPORAL_VALIDATION = "temporal_validation"

@dataclass
class ValidationRule:
    """Data validation rule definition"""
    rule_id: str
    rule_type: ValidationRuleType
    severity: ValidationSeverity
    description: str
    column: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    domain: Optional[AnalysisDomain] = None

@dataclass
class ValidationIssue:
    """Individual validation issue"""
    rule_id: str
    severity: ValidationSeverity
    message: str
    column: Optional[str] = None
    row_indices: List[int] = field(default_factory=list)
    affected_count: int = 0
    suggested_fix: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationResult:
    """Complete validation result"""
    request_id: str
    total_records: int
    validation_time: float
    overall_score: float
    issues: List[ValidationIssue] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    data_quality_metrics: Optional[DataQualityMetrics] = None

class ValidationRuleEngine(ABC):
    """Abstract base class for validation rule engines"""
    
    @abstractmethod
    def validate(self, data: pd.DataFrame, rule: ValidationRule) -> List[ValidationIssue]:
        """Execute validation rule on data"""
        pass

class RequiredColumnValidator(ValidationRuleEngine):
    """Validates required columns are present"""
    
    def validate(self, data: pd.DataFrame, rule: ValidationRule) -> List[ValidationIssue]:
        issues = []
        required_columns = rule.parameters.get('columns', [])
        
        for col in required_columns:
            if col not in data.columns:
                issues.append(ValidationIssue(
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    message=f"Required column '{col}' is missing",
                    column=col,
                    affected_count=len(data),
                    suggested_fix=f"Add column '{col}' to data source"
                ))
        
        return issues

class DataTypeValidator(ValidationRuleEngine):
    """Validates data types for columns"""
    
    def validate(self, data: pd.DataFrame, rule: ValidationRule) -> List[ValidationIssue]:
        issues = []
        column = rule.column
        expected_type = rule.parameters.get('type')
        
        if column not in data.columns:
            return issues
        
        # Check data type
        if expected_type == 'datetime':
            try:
                pd.to_datetime(data[column], errors='raise')
            except:
                invalid_rows = []
                for idx, val in data[column].items():
                    try:
                        pd.to_datetime(val)
                    except:
                        invalid_rows.append(idx)
                
                if invalid_rows:
                    issues.append(ValidationIssue(
                        rule_id=rule.rule_id,
                        severity=rule.severity,
                        message=f"Column '{column}' contains invalid datetime values",
                        column=column,
                        row_indices=invalid_rows,
                        affected_count=len(invalid_rows),
                        suggested_fix=f"Convert '{column}' to valid datetime format"
                    ))
        
        elif expected_type in ['int', 'float', 'numeric']:
            non_numeric = []
            for idx, val in data[column].items():
                if pd.notna(val):
                    try:
                        float(val)
                    except (ValueError, TypeError):
                        non_numeric.append(idx)
            
            if non_numeric:
                issues.append(ValidationIssue(
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    message=f"Column '{column}' contains non-numeric values",
                    column=column,
                    row_indices=non_numeric,
                    affected_count=len(non_numeric),
                    suggested_fix=f"Convert '{column}' to numeric format"
                ))
        
        return issues

class ValueRangeValidator(ValidationRuleEngine):
    """Validates values are within acceptable ranges"""
    
    def validate(self, data: pd.DataFrame, rule: ValidationRule) -> List[ValidationIssue]:
        issues = []
        column = rule.column
        min_val = rule.parameters.get('min')
        max_val = rule.parameters.get('max')
        
        if column not in data.columns:
            return issues
        
        # Check range violations
        out_of_range = []
        for idx, val in data[column].items():
            if pd.notna(val):
                try:
                    num_val = float(val)
                    if (min_val is not None and num_val < min_val) or \
                       (max_val is not None and num_val > max_val):
                        out_of_range.append(idx)
                except (ValueError, TypeError):
                    pass  # Handle in data type validation
        
        if out_of_range:
            range_desc = f"[{min_val}, {max_val}]" if min_val is not None and max_val is not None else \
                        f">= {min_val}" if min_val is not None else f"<= {max_val}"
            
            issues.append(ValidationIssue(
                rule_id=rule.rule_id,
                severity=rule.severity,
                message=f"Column '{column}' has {len(out_of_range)} values outside valid range {range_desc}",
                column=column,
                row_indices=out_of_range,
                affected_count=len(out_of_range),
                suggested_fix=f"Ensure '{column}' values are within range {range_desc}"
            ))
        
        return issues

class PatternMatchValidator(ValidationRuleEngine):
    """Validates values match expected patterns"""
    
    def validate(self, data: pd.DataFrame, rule: ValidationRule) -> List[ValidationIssue]:
        issues = []
        column = rule.column
        pattern = rule.parameters.get('pattern')
        
        if column not in data.columns or not pattern:
            return issues
        
        # Check pattern matches
        regex = re.compile(pattern)
        invalid_patterns = []
        
        for idx, val in data[column].items():
            if pd.notna(val) and not regex.match(str(val)):
                invalid_patterns.append(idx)
        
        if invalid_patterns:
            issues.append(ValidationIssue(
                rule_id=rule.rule_id,
                severity=rule.severity,
                message=f"Column '{column}' has {len(invalid_patterns)} values that don't match pattern {pattern}",
                column=column,
                row_indices=invalid_patterns,
                affected_count=len(invalid_patterns),
                suggested_fix=f"Ensure '{column}' values match pattern: {pattern}"
            ))
        
        return issues

class BusinessRuleValidator(ValidationRuleEngine):
    """Validates business-specific rules"""
    
    def validate(self, data: pd.DataFrame, rule: ValidationRule) -> List[ValidationIssue]:
        issues = []
        business_rule = rule.parameters.get('rule')
        
        if business_rule == 'casualty_state_transitions':
            issues.extend(self._validate_casualty_transitions(data, rule))
        elif business_rule == 'fall_casualty_correlation':
            issues.extend(self._validate_fall_casualty_correlation(data, rule))
        elif business_rule == 'battery_depletion_rate':
            issues.extend(self._validate_battery_depletion(data, rule))
        elif business_rule == 'network_connectivity_consistency':
            issues.extend(self._validate_network_consistency(data, rule))
        
        return issues
    
    def _validate_casualty_transitions(self, data: pd.DataFrame, rule: ValidationRule) -> List[ValidationIssue]:
        """Validate casualty state transitions follow logical sequence"""
        issues = []
        
        if not all(col in data.columns for col in ['callsign', 'casualtystate', 'processedtimegmt']):
            return issues
        
        # Valid state transitions
        valid_transitions = {
            'GOOD': ['KILLED', 'FALL ALERT'],
            'KILLED': ['RESURRECTED'],
            'FALL ALERT': ['GOOD', 'KILLED'],
            'RESURRECTED': ['GOOD', 'KILLED']
        }
        
        invalid_transitions = []
        
        for callsign, unit_data in data.groupby('callsign'):
            sorted_data = unit_data.sort_values('processedtimegmt')
            prev_state = None
            
            for idx, row in sorted_data.iterrows():
                current_state = row['casualtystate']
                
                if prev_state and current_state != prev_state:
                    if current_state not in valid_transitions.get(prev_state, []):
                        invalid_transitions.append(idx)
                
                prev_state = current_state
        
        if invalid_transitions:
            issues.append(ValidationIssue(
                rule_id=rule.rule_id,
                severity=rule.severity,
                message=f"Found {len(invalid_transitions)} invalid casualty state transitions",
                column='casualtystate',
                row_indices=invalid_transitions,
                affected_count=len(invalid_transitions),
                suggested_fix="Review casualty state transition logic"
            ))
        
        return issues
    
    def _validate_fall_casualty_correlation(self, data: pd.DataFrame, rule: ValidationRule) -> List[ValidationIssue]:
        """Validate correlation between falls and casualty states"""
        issues = []
        
        if not all(col in data.columns for col in ['callsign', 'falldetected', 'casualtystate']):
            return issues
        
        suspicious_cases = []
        
        for callsign, unit_data in data.groupby('callsign'):
            falls = len(unit_data[unit_data['falldetected'] == 'Yes'])
            casualties = len(unit_data[unit_data['casualtystate'].isin(['KILLED', 'FALL ALERT'])])
            
            # High falls with no casualties might indicate sensor issues
            if falls > 20 and casualties == 0:
                suspicious_cases.append(callsign)
        
        if suspicious_cases:
            issues.append(ValidationIssue(
                rule_id=rule.rule_id,
                severity=ValidationSeverity.WARNING,
                message=f"Units with high falls but no casualties: {', '.join(suspicious_cases)}",
                column='falldetected',
                affected_count=len(suspicious_cases),
                suggested_fix="Review fall detection calibration for these units"
            ))
        
        return issues
    
    def _validate_battery_depletion(self, data: pd.DataFrame, rule: ValidationRule) -> List[ValidationIssue]:
        """Validate battery depletion rates are realistic"""
        issues = []
        
        if not all(col in data.columns for col in ['callsign', 'battery', 'processedtimegmt']):
            return issues
        
        abnormal_depletion = []
        
        for callsign, unit_data in data.groupby('callsign'):
            if len(unit_data) < 2:
                continue
            
            sorted_data = unit_data.sort_values('processedtimegmt')
            battery_changes = sorted_data['battery'].diff().dropna()
            
            # Check for unrealistic battery level jumps
            large_increases = battery_changes[battery_changes > 50]  # Battery increased by >50%
            rapid_decreases = battery_changes[battery_changes < -50]  # Battery decreased by >50%
            
            if not large_increases.empty or not rapid_decreases.empty:
                abnormal_depletion.append(callsign)
        
        if abnormal_depletion:
            issues.append(ValidationIssue(
                rule_id=rule.rule_id,
                severity=ValidationSeverity.WARNING,
                message=f"Units with abnormal battery depletion: {', '.join(abnormal_depletion)}",
                column='battery',
                affected_count=len(abnormal_depletion),
                suggested_fix="Review battery sensor calibration"
            ))
        
        return issues
    
    def _validate_network_consistency(self, data: pd.DataFrame, rule: ValidationRule) -> List[ValidationIssue]:
        """Validate network metrics are consistent"""
        issues = []
        
        if not all(col in data.columns for col in ['rssi', 'mcs', 'nexthop']):
            return issues
        
        inconsistent_records = []
        
        for idx, row in data.iterrows():
            rssi = row.get('rssi', 0)
            mcs = row.get('mcs', 0)
            nexthop = row.get('nexthop', '')
            
            # High MCS with poor RSSI is inconsistent
            if rssi < 10 and mcs > 7:
                inconsistent_records.append(idx)
            
            # Good RSSI but no nexthop is suspicious
            if rssi > 20 and nexthop == 'Unavailable':
                inconsistent_records.append(idx)
        
        if inconsistent_records:
            issues.append(ValidationIssue(
                rule_id=rule.rule_id,
                severity=ValidationSeverity.WARNING,
                message=f"Found {len(inconsistent_records)} records with inconsistent network metrics",
                column='rssi',
                row_indices=inconsistent_records,
                affected_count=len(inconsistent_records),
                suggested_fix="Review network metric correlation"
            ))
        
        return issues

class DataValidator:
    """
    Event-driven data validation service for the AAR system
    Implements REQ-TECH-005 through REQ-TECH-008 requirements
    """
    
    def __init__(self, event_bus: EventBus, config: SystemConfiguration):
        self.event_bus = event_bus
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Validation engines
        self.validators = {
            ValidationRuleType.REQUIRED_COLUMN: RequiredColumnValidator(),
            ValidationRuleType.DATA_TYPE: DataTypeValidator(),
            ValidationRuleType.VALUE_RANGE: ValueRangeValidator(),
            ValidationRuleType.PATTERN_MATCH: PatternMatchValidator(),
            ValidationRuleType.BUSINESS_RULE: BusinessRuleValidator()
        }
        
        # Validation rules
        self.validation_rules = []
        self._initialize_default_rules()
        
        # Validation statistics
        self.validation_stats = {
            'total_validations': 0,
            'total_issues_found': 0,
            'critical_issues': 0,
            'average_validation_time': 0.0,
            'most_common_issues': {}
        }
        
        # Setup event subscriptions
        self._setup_event_subscriptions()
        
        self.logger.info("DataValidator service initialized with event-driven architecture")
    
    def _setup_event_subscriptions(self):
        """Setup event subscriptions for validation requests"""
        self.event_bus.subscribe(EventType.DATA_VALIDATION_REQUESTED, self.handle_validation_request, priority=1)
        self.event_bus.subscribe(EventType.DATA_LOAD_COMPLETED, self.handle_auto_validation, priority=2)
        self.event_bus.subscribe(EventType.CONFIG_CHANGED, self.handle_config_change, priority=3)
    
    def _initialize_default_rules(self):
        """Initialize default validation rules for AAR system"""
        
        # Required column rules
        self.validation_rules.extend([
            ValidationRule(
                rule_id="REQ_COLS_SAFETY",
                rule_type=ValidationRuleType.REQUIRED_COLUMN,
                severity=ValidationSeverity.ERROR,
                description="Required columns for safety analysis",
                parameters={'columns': ['callsign', 'falldetected', 'casualtystate', 'processedtimegmt']},
                domain=AnalysisDomain.SOLDIER_SAFETY
            ),
            ValidationRule(
                rule_id="REQ_COLS_NETWORK",
                rule_type=ValidationRuleType.REQUIRED_COLUMN,
                severity=ValidationSeverity.ERROR,
                description="Required columns for network analysis",
                parameters={'columns': ['callsign', 'processedtimegmt']},
                domain=AnalysisDomain.NETWORK_PERFORMANCE
            )
        ])
        
        # Data type rules
        self.validation_rules.extend([
            ValidationRule(
                rule_id="DT_TIMESTAMP",
                rule_type=ValidationRuleType.DATA_TYPE,
                severity=ValidationSeverity.ERROR,
                description="Timestamp must be valid datetime",
                column="processedtimegmt",
                parameters={'type': 'datetime'}
            ),
            ValidationRule(
                rule_id="DT_NUMERIC_FIELDS",
                rule_type=ValidationRuleType.DATA_TYPE,
                severity=ValidationSeverity.ERROR,
                description="Numeric fields must be numeric",
                column="temp",
                parameters={'type': 'numeric'}
            )
        ])
        
        # Value range rules (from requirements document)
        self.validation_rules.extend([
            ValidationRule(
                rule_id="VR_LATITUDE",
                rule_type=ValidationRuleType.VALUE_RANGE,
                severity=ValidationSeverity.ERROR,
                description="Latitude must be between -90 and 90",
                column="latitude",
                parameters={'min': -90, 'max': 90}
            ),
            ValidationRule(
                rule_id="VR_LONGITUDE",
                rule_type=ValidationRuleType.VALUE_RANGE,
                severity=ValidationSeverity.ERROR,
                description="Longitude must be between -180 and 180",
                column="longitude",
                parameters={'min': -180, 'max': 180}
            ),
            ValidationRule(
                rule_id="VR_BATTERY",
                rule_type=ValidationRuleType.VALUE_RANGE,
                severity=ValidationSeverity.WARNING,
                description="Battery level should be between 0 and 101%",
                column="battery",
                parameters={'min': 0, 'max': 101}
            ),
            ValidationRule(
                rule_id="VR_RSSI",
                rule_type=ValidationRuleType.VALUE_RANGE,
                severity=ValidationSeverity.WARNING,
                description="RSSI should be between -120 and 100 dBm",
                column="rssi",
                parameters={'min': -120, 'max': 100}
            ),
            ValidationRule(
                rule_id="VR_MCS",
                rule_type=ValidationRuleType.VALUE_RANGE,
                severity=ValidationSeverity.WARNING,
                description="MCS should be between 0 and 11",
                column="mcs",
                parameters={'min': 0, 'max': 11}
            ),
            ValidationRule(
                rule_id="VR_TEMPERATURE",
                rule_type=ValidationRuleType.VALUE_RANGE,
                severity=ValidationSeverity.WARNING,
                description="Temperature should be between -50 and 70°C",
                column="temp",
                parameters={'min': -50, 'max': 70}
            )
        ])
        
        # Pattern matching rules
        self.validation_rules.extend([
            ValidationRule(
                rule_id="PM_CALLSIGN",
                rule_type=ValidationRuleType.PATTERN_MATCH,
                severity=ValidationSeverity.WARNING,
                description="Callsign should follow standard format",
                column="callsign",
                parameters={'pattern': r'^[A-Za-z0-9_]+$'}
            ),
            ValidationRule(
                rule_id="PM_CASUALTY_STATE",
                rule_type=ValidationRuleType.PATTERN_MATCH,
                severity=ValidationSeverity.ERROR,
                description="Casualty state must be valid value",
                column="casualtystate",
                parameters={'pattern': r'^(GOOD|KILLED|FALL ALERT|RESURRECTED)$'}
            ),
            ValidationRule(
                rule_id="PM_FALL_DETECTED",
                rule_type=ValidationRuleType.PATTERN_MATCH,
                severity=ValidationSeverity.ERROR,
                description="Fall detected must be Yes or No",
                column="falldetected",
                parameters={'pattern': r'^(Yes|No)$'}
            )
        ])
        
        # Business rules
        self.validation_rules.extend([
            ValidationRule(
                rule_id="BR_CASUALTY_TRANSITIONS",
                rule_type=ValidationRuleType.BUSINESS_RULE,
                severity=ValidationSeverity.WARNING,
                description="Casualty state transitions must follow logical sequence",
                parameters={'rule': 'casualty_state_transitions'}
            ),
            ValidationRule(
                rule_id="BR_FALL_CASUALTY_CORRELATION",
                rule_type=ValidationRuleType.BUSINESS_RULE,
                severity=ValidationSeverity.WARNING,
                description="Fall events should correlate with casualty states",
                parameters={'rule': 'fall_casualty_correlation'}
            ),
            ValidationRule(
                rule_id="BR_BATTERY_DEPLETION",
                rule_type=ValidationRuleType.BUSINESS_RULE,
                severity=ValidationSeverity.WARNING,
                description="Battery depletion rates should be realistic",
                parameters={'rule': 'battery_depletion_rate'}
            ),
            ValidationRule(
                rule_id="BR_NETWORK_CONSISTENCY",
                rule_type=ValidationRuleType.BUSINESS_RULE,
                severity=ValidationSeverity.WARNING,
                description="Network metrics should be consistent",
                parameters={'rule': 'network_connectivity_consistency'}
            )
        ])
        
        self.logger.info(f"Initialized {len(self.validation_rules)} validation rules")
    
    def validate_data(self, data: pd.DataFrame, request_id: str = None, domain: AnalysisDomain = None) -> ValidationResult:
        """
        Validate data against all applicable rules
        REQ-TECH-005: Automated data quality assessment
        """
        start_time = datetime.now()
        request_id = request_id or f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Filter rules by domain if specified
            applicable_rules = [
                rule for rule in self.validation_rules 
                if rule.enabled and (domain is None or rule.domain is None or rule.domain == domain)
            ]
            
            # Execute validation rules
            all_issues = []
            
            for rule in applicable_rules:
                try:
                    validator = self.validators.get(rule.rule_type)
                    if validator:
                        issues = validator.validate(data, rule)
                        all_issues.extend(issues)
                    else:
                        self.logger.warning(f"No validator found for rule type: {rule.rule_type}")
                        
                except Exception as e:
                    self.logger.error(f"Error validating rule {rule.rule_id}: {e}")
                    all_issues.append(ValidationIssue(
                        rule_id=rule.rule_id,
                        severity=ValidationSeverity.ERROR,
                        message=f"Validation rule execution failed: {str(e)}",
                        suggested_fix="Review rule configuration"
                    ))
            
            # Calculate validation metrics
            validation_time = (datetime.now() - start_time).total_seconds()
            data_quality_metrics = self._calculate_data_quality_metrics(data, all_issues)
            overall_score = self._calculate_overall_score(all_issues, len(data))
            
            # Generate summary and recommendations
            summary = self._generate_validation_summary(all_issues, len(data))
            recommendations = self._generate_recommendations(all_issues, data)
            
            # Create validation result
            result = ValidationResult(
                request_id=request_id,
                total_records=len(data),
                validation_time=validation_time,
                overall_score=overall_score,
                issues=all_issues,
                summary=summary,
                recommendations=recommendations,
                data_quality_metrics=data_quality_metrics
            )
            
            # Update statistics
            self._update_validation_statistics(result)
            
            # Publish validation events
            self._publish_validation_events(result)
            
            self.logger.info(f"Validation completed for {len(data)} records with {len(all_issues)} issues")
            return result
            
        except Exception as e:
            self.logger.error(f"Critical error in data validation: {e}")
            
            # Return failed validation result
            return ValidationResult(
                request_id=request_id,
                total_records=len(data) if data is not None else 0,
                validation_time=(datetime.now() - start_time).total_seconds(),
                overall_score=0.0,
                issues=[ValidationIssue(
                    rule_id="SYSTEM_ERROR",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Critical validation system error: {str(e)}",
                    affected_count=len(data) if data is not None else 0
                )]
            )
    
    def _calculate_data_quality_metrics(self, data: pd.DataFrame, issues: List[ValidationIssue]) -> DataQualityMetrics:
        """Calculate comprehensive data quality metrics"""
        metrics = DataQualityMetrics()
        metrics.total_records = len(data)
        
        # Calculate missing data percentages
        missing_data = {}
        for col in data.columns:
            missing_count = data[col].isna().sum()
            missing_data[col] = (missing_count / len(data)) * 100
        
        metrics.missing_data_percentage = missing_data
        metrics.data_completeness = 100 - np.mean(list(missing_data.values()))
        
        # Extract validation errors
        metrics.validation_errors = [issue.message for issue in issues if issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]
        
        return metrics
    
    def _calculate_overall_score(self, issues: List[ValidationIssue], total_records: int) -> float:
        """Calculate overall data quality score"""
        if not issues:
            return 100.0
        
        # Weight issues by severity
        severity_weights = {
            ValidationSeverity.INFO: 0.1,
            ValidationSeverity.WARNING: 0.5,
            ValidationSeverity.ERROR: 1.0,
            ValidationSeverity.CRITICAL: 2.0
        }
        
        total_penalty = 0
        for issue in issues:
            weight = severity_weights.get(issue.severity, 1.0)
            # Penalty proportional to affected records
            penalty = (issue.affected_count / total_records) * weight * 100
            total_penalty += penalty
        
        # Cap penalty at 100 and return score
        return max(0.0, 100.0 - min(total_penalty, 100.0))
    
    def _generate_validation_summary(self, issues: List[ValidationIssue], total_records: int) -> Dict[str, Any]:
        """Generate validation summary statistics"""
        summary = {
            'total_issues': len(issues),
            'severity_breakdown': {
                'critical': len([i for i in issues if i.severity == ValidationSeverity.CRITICAL]),
                'error': len([i for i in issues if i.severity == ValidationSeverity.ERROR]),
                'warning': len([i for i in issues if i.severity == ValidationSeverity.WARNING]),
                'info': len([i for i in issues if i.severity == ValidationSeverity.INFO])
            },
            'affected_records': sum(issue.affected_count for issue in issues),
            'most_common_issues': {},
            'column_issues': {}
        }
        
        # Most common issue types
        rule_counts = {}
        for issue in issues:
            rule_counts[issue.rule_id] = rule_counts.get(issue.rule_id, 0) + 1
        
        summary['most_common_issues'] = dict(sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        
        # Issues by column
        column_issues = {}
        for issue in issues:
            if issue.column:
                column_issues[issue.column] = column_issues.get(issue.column, 0) + 1
        
        summary['column_issues'] = dict(sorted(column_issues.items(), key=lambda x: x[1], reverse=True))
        
        return summary
    
    def _generate_recommendations(self, issues: List[ValidationIssue], data: pd.DataFrame) -> List[str]:
        """Generate data quality improvement recommendations"""
        recommendations = []
        
        # Critical issues first
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            recommendations.append(f"CRITICAL: Address {len(critical_issues)} critical data quality issues immediately")
        
        # Missing data recommendations
        missing_data_issues = [i for i in issues if 'missing' in i.message.lower()]
        if missing_data_issues:
            recommendations.append("Add missing required columns to data source")
        
        # Data type issues
        type_issues = [i for i in issues if 'type' in i.message.lower() or 'format' in i.message.lower()]
        if type_issues:
            recommendations.append("Review and standardize data formats for consistency")
        
        # Range validation issues
        range_issues = [i for i in issues if 'range' in i.message.lower()]
        if range_issues:
            recommendations.append("Implement data validation at source to prevent out-of-range values")
        
        # Business rule violations
        business_issues = [i for i in issues if i.rule_id.startswith('BR_')]
        if business_issues:
            recommendations.append("Review business logic and sensor calibration")
        
        # General recommendations based on data quality
        if len(issues) > len(data) * 0.1:  # More than 10% of records have issues
            recommendations.append("Consider implementing automated data cleansing processes")
        
        if not recommendations:
            recommendations.append("Data quality is acceptable - continue monitoring")
        
        return recommendations
    
    def _update_validation_statistics(self, result: ValidationResult):
        """Update validation statistics"""
        self.validation_stats['total_validations'] += 1
        self.validation_stats['total_issues_found'] += len(result.issues)
        
        critical_issues = len([i for i in result.issues if i.severity == ValidationSeverity.CRITICAL])
        self.validation_stats['critical_issues'] += critical_issues
        
        # Update average validation time
        total_validations = self.validation_stats['total_validations']
        current_avg = self.validation_stats['average_validation_time']
        self.validation_stats['average_validation_time'] = (
            (current_avg * (total_validations - 1) + result.validation_time) / total_validations
        )
        
        # Update most common issues
        for issue in result.issues:
            rule_id = issue.rule_id
            self.validation_stats['most_common_issues'][rule_id] = \
                self.validation_stats['most_common_issues'].get(rule_id, 0) + 1
    
    def _publish_validation_events(self, result: ValidationResult):
        """Publish validation events through event bus"""
        
        # Publish validation completed event
        self.event_bus.publish(Event(
            EventType.DATA_VALIDATION_COMPLETED,
            {
                'request_id': result.request_id,
                'total_records': result.total_records,
                'validation_time': result.validation_time,
                'overall_score': result.overall_score,
                'total_issues': len(result.issues),
                'critical_issues': len([i for i in result.issues if i.severity == ValidationSeverity.CRITICAL])
            },
            source='DataValidator'
        ))
        
        # Publish alerts for critical issues
        for issue in result.issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                self.event_bus.publish(Event(
                    EventType.ALERT_TRIGGERED,
                    {
                        'alert_type': 'DATA_QUALITY_CRITICAL',
                        'level': AlertLevel.CRITICAL,
                        'message': issue.message,
                        'affected_count': issue.affected_count,
                        'rule_id': issue.rule_id,
                        'column': issue.column
                    },
                    source='DataValidator'
                ))
    
    def add_validation_rule(self, rule: ValidationRule):
        """Add a new validation rule"""
        self.validation_rules.append(rule)
        self.logger.info(f"Added validation rule: {rule.rule_id}")
    
    def remove_validation_rule(self, rule_id: str) -> bool:
        """Remove a validation rule by ID"""
        for i, rule in enumerate(self.validation_rules):
            if rule.rule_id == rule_id:
                del self.validation_rules[i]
                self.logger.info(f"Removed validation rule: {rule_id}")
                return True
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a validation rule"""
        for rule in self.validation_rules:
            if rule.rule_id == rule_id:
                rule.enabled = True
                self.logger.info(f"Enabled validation rule: {rule_id}")
                return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a validation rule"""
        for rule in self.validation_rules:
            if rule.rule_id == rule_id:
                rule.enabled = False
                self.logger.info(f"Disabled validation rule: {rule_id}")
                return True
        return False
    
    def get_validation_rules(self, domain: AnalysisDomain = None) -> List[ValidationRule]:
        """Get validation rules, optionally filtered by domain"""
        if domain:
            return [rule for rule in self.validation_rules if rule.domain == domain or rule.domain is None]
        return self.validation_rules
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation performance statistics"""
        return {
            **self.validation_stats,
            'active_rules': len([r for r in self.validation_rules if r.enabled]),
            'total_rules': len(self.validation_rules),
            'current_timestamp': datetime.now().isoformat()
        }
    
    def handle_validation_request(self, event: Event):
        """Handle validation request events"""
        request_data = event.data
        
        try:
            # Extract data from event
            data = request_data.get('data')
            if data is None:
                raise ValueError("No data provided in validation request")
            
            # Convert to DataFrame if needed
            if isinstance(data, dict):
                data = pd.DataFrame([data])
            elif isinstance(data, list):
                data = pd.DataFrame(data)
            elif not isinstance(data, pd.DataFrame):
                raise ValueError("Data must be DataFrame, dict, or list")
            
            # Perform validation
            result = self.validate_data(
                data=data,
                request_id=request_data.get('request_id'),
                domain=request_data.get('domain')
            )
            
            # Return result through event
            self.event_bus.publish(Event(
                EventType.DATA_VALIDATION_COMPLETED,
                {
                    'request_id': result.request_id,
                    'validation_result': result
                },
                source='DataValidator'
            ))
            
        except Exception as e:
            self.logger.error(f"Error handling validation request: {e}")
            self.event_bus.publish(Event(
                EventType.ERROR_OCCURRED,
                {
                    'operation': 'handle_validation_request',
                    'error': str(e),
                    'request_id': request_data.get('request_id')
                },
                source='DataValidator'
            ))
    
    def handle_auto_validation(self, event: Event):
        """Handle automatic validation after data loading"""
        try:
            # Get loaded data from event
            request_id = event.data.get('request_id')
            
            # This would typically get the data from the data loader
            # For now, we'll publish a validation request
            self.event_bus.publish(Event(
                EventType.DATA_VALIDATION_REQUESTED,
                {
                    'request_id': f"auto_validation_{request_id}",
                    'trigger': 'auto_validation_after_load',
                    'source_request_id': request_id
                },
                source='DataValidator'
            ))
            
        except Exception as e:
            self.logger.error(f"Error in auto validation: {e}")
    
    def handle_config_change(self, event: Event):
        """Handle configuration changes"""
        config_data = event.data
        
        # Update validation rules based on configuration
        if 'validation_rules' in config_data:
            rules_config = config_data['validation_rules']
            
            for rule_id, rule_config in rules_config.items():
                if 'enabled' in rule_config:
                    if rule_config['enabled']:
                        self.enable_rule(rule_id)
                    else:
                        self.disable_rule(rule_id)
        
        self.logger.info("DataValidator configuration updated")
    
    def create_validation_report(self, result: ValidationResult) -> Dict[str, Any]:
        """Create a comprehensive validation report"""
        report = {
            'validation_summary': {
                'request_id': result.request_id,
                'total_records': result.total_records,
                'validation_time': result.validation_time,
                'overall_score': result.overall_score,
                'timestamp': datetime.now().isoformat()
            },
            'data_quality_metrics': {
                'completeness': result.data_quality_metrics.data_completeness if result.data_quality_metrics else 0,
                'missing_data': result.data_quality_metrics.missing_data_percentage if result.data_quality_metrics else {},
                'validation_errors': result.data_quality_metrics.validation_errors if result.data_quality_metrics else []
            },
            'issues_analysis': {
                'total_issues': len(result.issues),
                'by_severity': result.summary.get('severity_breakdown', {}),
                'by_column': result.summary.get('column_issues', {}),
                'most_common': result.summary.get('most_common_issues', {})
            },
            'detailed_issues': [
                {
                    'rule_id': issue.rule_id,
                    'severity': issue.severity.value,
                    'message': issue.message,
                    'column': issue.column,
                    'affected_count': issue.affected_count,
                    'suggested_fix': issue.suggested_fix
                }
                for issue in result.issues
            ],
            'recommendations': result.recommendations,
            'system_statistics': self.get_validation_statistics()
        }
        
        return report
    
    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("DataValidator cleanup completed")


# Factory functions for common validation scenarios
def create_safety_validation_rules() -> List[ValidationRule]:
    """Create validation rules specific to soldier safety analysis"""
    return [
        ValidationRule(
            rule_id="SAFETY_FALL_PATTERN",
            rule_type=ValidationRuleType.BUSINESS_RULE,
            severity=ValidationSeverity.WARNING,
            description="Validate fall detection patterns",
            parameters={'rule': 'fall_casualty_correlation'},
            domain=AnalysisDomain.SOLDIER_SAFETY
        ),
        ValidationRule(
            rule_id="SAFETY_CASUALTY_FLOW",
            rule_type=ValidationRuleType.BUSINESS_RULE,
            severity=ValidationSeverity.ERROR,
            description="Validate casualty state transitions",
            parameters={'rule': 'casualty_state_transitions'},
            domain=AnalysisDomain.SOLDIER_SAFETY
        ),
        ValidationRule(
            rule_id="SAFETY_TEMP_RANGE",
            rule_type=ValidationRuleType.VALUE_RANGE,
            severity=ValidationSeverity.WARNING,
            description="Body temperature should be within normal range",
            column="temp",
            parameters={'min': 30, 'max': 45},
            domain=AnalysisDomain.SOLDIER_SAFETY
        )
    ]


def create_network_validation_rules() -> List[ValidationRule]:
    """Create validation rules specific to network performance analysis"""
    return [
        ValidationRule(
            rule_id="NETWORK_RSSI_RANGE",
            rule_type=ValidationRuleType.VALUE_RANGE,
            severity=ValidationSeverity.WARNING,
            description="RSSI values should be within expected range",
            column="rssi",
            parameters={'min': -120, 'max': 50},
            domain=AnalysisDomain.NETWORK_PERFORMANCE
        ),
        ValidationRule(
            rule_id="NETWORK_MCS_RANGE",
            rule_type=ValidationRuleType.VALUE_RANGE,
            severity=ValidationSeverity.WARNING,
            description="MCS values should be within valid range",
            column="mcs",
            parameters={'min': 0, 'max': 11},
            domain=AnalysisDomain.NETWORK_PERFORMANCE
        ),
        ValidationRule(
            rule_id="NETWORK_CONSISTENCY",
            rule_type=ValidationRuleType.BUSINESS_RULE,
            severity=ValidationSeverity.WARNING,
            description="Network metrics should be consistent",
            parameters={'rule': 'network_connectivity_consistency'},
            domain=AnalysisDomain.NETWORK_PERFORMANCE
        )
    ]


def create_activity_validation_rules() -> List[ValidationRule]:
    """Create validation rules specific to soldier activity analysis"""
    return [
        ValidationRule(
            rule_id="ACTIVITY_STEPS_RANGE",
            rule_type=ValidationRuleType.VALUE_RANGE,
            severity=ValidationSeverity.WARNING,
            description="Step count should be within reasonable range",
            column="steps",
            parameters={'min': 0, 'max': 5000},
            domain=AnalysisDomain.SOLDIER_ACTIVITY
        ),
        ValidationRule(
            rule_id="ACTIVITY_POSTURE_VALID",
            rule_type=ValidationRuleType.PATTERN_MATCH,
            severity=ValidationSeverity.WARNING,
            description="Posture should be valid value",
            column="posture",
            parameters={'pattern': r'^(Standing|Prone|Unknown)},
            domain=AnalysisDomain.SOLDIER_ACTIVITY
        )
    ]


def create_equipment_validation_rules() -> List[ValidationRule]:
    """Create validation rules specific to equipment management analysis"""
    return [
        ValidationRule(
            rule_id="EQUIPMENT_BATTERY_RANGE",
            rule_type=ValidationRuleType.VALUE_RANGE,
            severity=ValidationSeverity.WARNING,
            description="Battery level should be between 0 and 100%",
            column="battery",
            parameters={'min': 0, 'max': 100},
            domain=AnalysisDomain.EQUIPMENT_MANAGEMENT
        ),
        ValidationRule(
            rule_id="EQUIPMENT_BATTERY_DEPLETION",
            rule_type=ValidationRuleType.BUSINESS_RULE,
            severity=ValidationSeverity.WARNING,
            description="Battery depletion should be realistic",
            parameters={'rule': 'battery_depletion_rate'},
            domain=AnalysisDomain.EQUIPMENT_MANAGEMENT
        )
    ]


# Integration helper functions
def integrate_validation_with_loader(loader, validator):
    """Integrate data validation with data loader"""
    def auto_validate_loaded_data(event):
        """Automatically validate data after loading"""
        if event.event_type == EventType.DATA_LOAD_COMPLETED:
            request_id = event.data.get('request_id')
            
            # Get loaded data (this would need to be implemented in the loader)
            # For now, we'll just trigger validation
            validator.event_bus.publish(Event(
                EventType.DATA_VALIDATION_REQUESTED,
                {
                    'request_id': f"auto_val_{request_id}",
                    'trigger': 'post_load_validation',
                    'source_request_id': request_id
                },
                source='DataLoaderIntegration'
            ))
    
    # Subscribe to load completion events
    loader.event_bus.subscribe(EventType.DATA_LOAD_COMPLETED, auto_validate_loaded_data, priority=2)


def create_comprehensive_validation_config(domains: List[AnalysisDomain]) -> Dict[str, Any]:
    """Create comprehensive validation configuration for multiple domains"""
    config = {
        'validation_rules': {},
        'domain_specific_rules': {},
        'severity_thresholds': {
            'critical_threshold': 95,  # Overall score below this triggers critical alert
            'warning_threshold': 85,   # Overall score below this triggers warning
            'auto_fix_threshold': 75   # Auto-attempt fixes below this score
        },
        'performance_settings': {
            'max_validation_time': 30.0,  # Maximum time for validation in seconds
            'batch_size': 1000,           # Batch size for large datasets
            'parallel_validation': True   # Enable parallel rule execution
        }
    }
    
    # Add domain-specific rules
    for domain in domains:
        if domain == AnalysisDomain.SOLDIER_SAFETY:
            config['domain_specific_rules']['safety'] = create_safety_validation_rules()
        elif domain == AnalysisDomain.NETWORK_PERFORMANCE:
            config['domain_specific_rules']['network'] = create_network_validation_rules()
        elif domain == AnalysisDomain.SOLDIER_ACTIVITY:
            config['domain_specific_rules']['activity'] = create_activity_validation_rules()
        elif domain == AnalysisDomain.EQUIPMENT_MANAGEMENT:
            config['domain_specific_rules']['equipment'] = create_equipment_validation_rules()
    
    return config