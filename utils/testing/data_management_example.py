# examples/data_management_example.py - Practical Examples for Testing Data Management Services
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import json
import time
from pathlib import Path
import logging

# Import your services
from services.data_management.data_loader import (
    DataLoader, DataLoadRequest, DataSourceType, 
    create_csv_load_request, create_stream_load_request
)
from services.data_management.data_validation import (
    DataValidator, ValidationRule, ValidationRuleType, ValidationSeverity,
    create_safety_validation_rules, create_network_validation_rules,
    create_comprehensive_validation_config
)
from core.event_bus import EventBus, Event, EventType
from core.models import AnalysisDomain, SystemConfiguration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataManagementDemo:
    """Demonstration of data management services functionality"""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.config = SystemConfiguration()
        
        # Configure for testing
        self.config.max_concurrent_loads = 5
        self.config.default_chunk_size = 1000
        self.config.load_timeout = 60
        
        # Initialize services
        self.data_loader = DataLoader(self.event_bus, self.config)
        self.data_validator = DataValidator(self.event_bus, self.config)
        
        # Setup event monitoring
        self.events_received = []
        self._setup_event_monitoring()
        
        logger.info("Data Management Demo initialized")
    
    def _setup_event_monitoring(self):
        """Setup event monitoring for demonstration"""
        def event_monitor(event):
            self.events_received.append(event)
            logger.info(f"Event: {event.event_type.value} from {event.source}")
        
        # Monitor key events
        self.event_bus.subscribe(EventType.DATA_LOAD_STARTED, event_monitor)
        self.event_bus.subscribe(EventType.DATA_LOAD_COMPLETED, event_monitor)
        self.event_bus.subscribe(EventType.DATA_VALIDATION_COMPLETED, event_monitor)
        self.event_bus.subscribe(EventType.ALERT_TRIGGERED, event_monitor)
        self.event_bus.subscribe(EventType.ERROR_OCCURRED, event_monitor)
    
    def create_sample_training_data(self) -> pd.DataFrame:
        """Create realistic sample training data"""
        # Simulate 23-minute training exercise with 4 units
        num_records = 500
        units = ['Unit_108', 'Unit_134', 'Unit_156', 'Unit_178']
        
        # Base time
        base_time = datetime.now() - timedelta(minutes=23)
        
        data = []
        for i in range(num_records):
            # Unit selection with Unit_108 having more activity (as per requirements)
            if i < 200:
                unit = 'Unit_108'  # High activity unit
            else:
                unit = np.random.choice(units)
            
            # Time progression
            time_offset = (i / num_records) * 23 * 60  # 23 minutes in seconds
            timestamp = base_time + timedelta(seconds=time_offset)
            
            # Realistic data generation
            record = {
                'callsign': unit,
                'processedtimegmt': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'latitude': 40.7128 + np.random.uniform(-0.01, 0.01),
                'longitude': -74.0060 + np.random.uniform(-0.01, 0.01),
                'temp': np.random.normal(25, 3),
                'battery': max(0, 100 - (i * 0.2) + np.random.uniform(-5, 5)),
                'falldetected': 'Yes' if (unit == 'Unit_108' and np.random.random() < 0.3) else 'No',
                'casualtystate': self._generate_casualty_state(unit, i),
                'rssi': max(-50, min(50, np.random.normal(20, 10))),
                'mcs': np.random.randint(3, 8),
                'nexthop': f'Router_{np.random.randint(1, 4)}',
                'steps': np.random.randint(100, 400),
                'posture': np.random.choice(['Standing', 'Prone', 'Unknown'], p=[0.4, 0.4, 0.2]),
                'squad': 'Alpha' if unit in ['Unit_108', 'Unit_134'] else 'Bravo'
            }
            data.append(record)
        
        return pd.DataFrame(data)
    
    def _generate_casualty_state(self, unit: str, index: int) -> str:
        """Generate realistic casualty states"""
        if unit == 'Unit_108':
            # High-risk unit with casualties
            if index % 50 == 0:
                return 'KILLED'
            elif index % 25 == 0:
                return 'FALL ALERT'
            elif index % 75 == 0:
                return 'RESURRECTED'
            else:
                return 'GOOD'
        else:
            # Low-risk units
            if index % 100 == 0:
                return 'FALL ALERT'
            else:
                return 'GOOD'
    
    def create_problematic_data(self) -> pd.DataFrame:
        """Create data with various quality issues for testing validation"""
        data = {
            'callsign': ['Unit_100', 'Unit_101', 'Unit_102', 'Unit_103', 'Unit_104'],
            'processedtimegmt': [
                '2025-01-01 10:00:00',
                'invalid_timestamp',  # Invalid datetime
                '2025-01-01 10:01:00',
                '2025-01-01 10:01:30',
                '2025-01-01 10:02:00'
            ],
            'latitude': [40.7128, 91.0, 40.7125, 40.7135, np.nan],  # Invalid lat, missing value
            'longitude': [-74.0060, -74.0062, -181.0, -74.0065, -74.0070],  # Invalid lon
            'temp': [25.5, 80.0, 24.8, 25.2, -60.0],  # Invalid temperatures
            'battery': [95, 150, 92, 88, -10],  # Invalid battery levels
            'falldetected': ['No', 'Yes', 'Maybe', 'No', 'Yes'],  # Invalid value
            'casualtystate': ['GOOD', 'FALL ALERT', 'INVALID_STATE', 'KILLED', 'RESURRECTED'],
            'rssi': [22, 200, 25, 20, -200],  # Invalid RSSI values
            'mcs': [6, 15, 7, 6, -1],  # Invalid MCS values
            'nexthop': ['Router_1', 'Router_2', 'Router_1', 'Unavailable', 'Router_3'],
            'steps': [150, 200, 10000, 170, -50],  # Invalid step counts
            'posture': ['Standing', 'Prone', 'Invalid', 'Standing', 'Standing'],
            'squad': ['Alpha', 'Alpha', 'Bravo', 'Unknown', 'Alpha']
        }
        
        return pd.DataFrame(data)
    
    def demo_basic_data_loading(self):
        """Demo 1: Basic data loading functionality"""
        print("\n🔄 Demo 1: Basic Data Loading")
        print("=" * 40)
        
        # Create sample data
        sample_data = self.create_sample_training_data()
        
        # Save to temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_data.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            # Create load request for safety analysis
            request = create_csv_load_request(
                request_id="demo_load_001",
                file_path=temp_file,
                analysis_domain=AnalysisDomain.SOLDIER_SAFETY
            )
            
            print(f"Loading data from: {temp_file}")
            print(f"Target columns: {request.target_columns}")
            
            # Load data
            request_id = self.data_loader.load_data(request)
            print(f"Load request submitted: {request_id}")
            
            # Wait for completion
            time.sleep(2)
            
            # Check results
            result = self.data_loader.get_load_status(request_id)
            if result and hasattr(result, 'data') and result.data is not None:
                print(f"✅ Successfully loaded {len(result.data)} records")
                print(f"Load time: {result.loading_time:.2f}s")
                print(f"Data quality score: {result.data_quality.data_completeness:.1f}%")
            else:
                print("❌ Load failed or still in progress")
            
            # Show statistics
            stats = self.data_loader.get_load_statistics()
            print(f"Load statistics: {stats}")
            
        finally:
            Path(temp_file).unlink()
    
    def demo_data_validation(self):
        """Demo 2: Data validation functionality"""
        print("\n🔍 Demo 2: Data Validation")
        print("=" * 40)
        
        # Test with problematic data
        problematic_data = self.create_problematic_data()
        
        print(f"Validating {len(problematic_data)} records with known issues...")
        
        # Run validation
        result = self.data_validator.validate_data(
            problematic_data,
            request_id="demo_validation_001"
        )
        
        print(f"✅ Validation completed in {result.validation_time:.2f}s")
        print(f"Overall score: {result.overall_score:.1f}%")
        print(f"Total issues found: {len(result.issues)}")
        
        # Show issue breakdown
        severity_counts = {}
        for issue in result.issues:
            severity = issue.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        print("\nIssue breakdown:")
        for severity, count in severity_counts.items():
            print(f"  {severity.upper()}: {count}")
        
        # Show top issues
        print("\nTop validation issues:")
        for i, issue in enumerate(result.issues[:5]):
            print(f"  {i+1}. {issue.message} ({issue.severity.value})")
            if issue.suggested_fix:
                print(f"     Fix: {issue.suggested_fix}")
        
        # Show recommendations
        print("\nRecommendations:")
        for i, rec in enumerate(result.recommendations[:3]):
            print(f"  {i+1}. {rec}")
    
    def demo_domain_specific_validation(self):
        """Demo 3: Domain-specific validation rules"""
        print("\n🎯 Demo 3: Domain-Specific Validation")
        print("=" * 40)
        
        # Create domain-specific data
        sample_data = self.create_sample_training_data()
        
        # Test safety domain validation
        print("Testing SOLDIER_SAFETY domain validation...")
        safety_result = self.data_validator.validate_data(
            sample_data,
            request_id="demo_safety_validation",
            domain=AnalysisDomain.SOLDIER_SAFETY
        )
        
        print(f"Safety validation score: {safety_result.overall_score:.1f}%")
        print(f"Safety issues found: {len(safety_result.issues)}")
        
        # Test network domain validation
        print("\nTesting NETWORK_PERFORMANCE domain validation...")
        network_result = self.data_validator.validate_data(
            sample_data,
            request_id="demo_network_validation",
            domain=AnalysisDomain.NETWORK_PERFORMANCE
        )
        
        print(f"Network validation score: {network_result.overall_score:.1f}%")
        print(f"Network issues found: {len(network_result.issues)}")
        
        # Show domain-specific issues
        safety_issues = [i for i in safety_result.issues if i.rule_id.startswith('BR_')]
        network_issues = [i for i in network_result.issues if 'network' in i.message.lower()]
        
        if safety_issues:
            print(f"\nSafety-specific issues:")
            for issue in safety_issues[:2]:
                print(f"  - {issue.message}")
        
        if network_issues:
            print(f"\nNetwork-specific issues:")
            for issue in network_issues[:2]:
                print(f"  - {issue.message}")
    
    def demo_event_driven_integration(self):
        """Demo 4: Event-driven integration"""
        print("\n🔄 Demo 4: Event-Driven Integration")
        print("=" * 40)
        
        # Clear previous events
        self.events_received = []
        
        # Create sample data
        sample_data = self.create_sample_training_data()
        
        # Manually trigger validation request event
        print("Triggering validation request event...")
        self.event_bus.publish(Event(
            EventType.DATA_VALIDATION_REQUESTED,
            {
                'request_id': 'demo_event_integration',
                'data': sample_data,
                'domain': AnalysisDomain.SOLDIER_SAFETY
            },
            source='DemoApplication'
        ))
        
        # Wait for event processing
        time.sleep(1)
        
        # Show events received
        print(f"Events received: {len(self.events_received)}")
        for event in self.events_received[-5:]:  # Show last 5 events
            print(f"  - {event.event_type.value} from {event.source}")
        
        # Simulate data load completion triggering auto-validation
        print("\nSimulating auto-validation after data load...")
        self.event_bus.publish(Event(
            EventType.DATA_LOAD_COMPLETED,
            {
                'request_id': 'demo_auto_validation',
                'records_loaded': len(sample_data),
                'loading_time': 1.5
            },
            source='DemoDataLoader'
        ))
        
        time.sleep(0.5)
        
        print(f"Total events processed: {len(self.events_received)}")
    
    def demo_performance_testing(self):
        """Demo 5: Performance testing with large datasets"""
        print("\n⚡ Demo 5: Performance Testing")
        print("=" * 40)
        
        # Create large dataset
        print("Creating large dataset for performance testing...")
        large_data = pd.DataFrame({
            'callsign': [f'Unit_{i % 20}' for i in range(10000)],
            'processedtimegmt': [
                (datetime.now() - timedelta(seconds=i)).strftime('%Y-%m-%d %H:%M:%S')
                for i in range(10000)
            ],
            'latitude': np.random.uniform(40.7, 40.8, 10000),
            'longitude': np.random.uniform(-74.1, -74.0, 10000),
            'temp': np.random.normal(25, 3, 10000),
            'battery': np.random.randint(50, 101, 10000),
            'falldetected': np.random.choice(['Yes', 'No'], 10000, p=[0.1, 0.9]),
            'casualtystate': np.random.choice(['GOOD', 'KILLED', 'FALL ALERT'], 10000, p=[0.8, 0.1, 0.1]),
            'rssi': np.random.randint(-50, 50, 10000),
            'mcs': np.random.randint(3, 8, 10000),
            'steps': np.random.randint(100, 500, 10000)
        })
        
        print(f"Dataset size: {len(large_data)} records")
        
        # Test validation performance
        print("Testing validation performance...")
        start_time = time.time()
        
        result = self.data_validator.validate_data(
            large_data,
            request_id="performance_test_001"
        )
        
        end_time = time.time()
        validation_time = end_time - start_time
        
        print(f"✅ Validation completed in {validation_time:.2f}s")
        print(f"Records per second: {len(large_data) / validation_time:.0f}")
        print(f"Overall score: {result.overall_score:.1f}%")
        print(f"Issues found: {len(result.issues)}")
        
        # Test loading performance
        print("\nTesting loading performance...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            large_data.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            start_time = time.time()
            
            request = DataLoadRequest(
                request_id="performance_load_001",
                source_type=DataSourceType.CSV_FILE,
                source_path=temp_file,
                target_columns=['callsign', 'processedtimegmt', 'temp'],
                chunk_size=1000
            )
            
            loaded_data = self.data_loader._load_csv_data(request)
            
            end_time = time.time()
            load_time = end_time - start_time
            
            print(f"✅ Loading completed in {load_time:.2f}s")
            print(f"Records per second: {len(loaded_data) / load_time:.0f}")
            
        finally:
            Path(temp_file).unlink()
    
    def demo_validation_report_generation(self):
        """Demo 6: Comprehensive validation report generation"""
        print("\n📊 Demo 6: Validation Report Generation")
        print("=" * 40)
        
        # Create mixed quality data
        sample_data = self.create_sample_training_data()
        problematic_data = self.create_problematic_data()
        
        # Combine datasets
        combined_data = pd.concat([sample_data, problematic_data], ignore_index=True)
        
        print(f"Analyzing {len(combined_data)} records...")
        
        # Run validation
        result = self.data_validator.validate_data(
            combined_data,
            request_id="demo_report_generation"
        )
        
        # Generate comprehensive report
        report = self.data_validator.create_validation_report(result)
        
        print(f"✅ Validation report generated")
        print(f"Overall score: {report['validation_summary']['overall_score']:.1f}%")
        
        # Show report sections
        print("\nReport sections:")
        for section in report.keys():
            print(f"  - {section}")
        
        # Show detailed metrics
        print("\nData Quality Metrics:")
        metrics = report['data_quality_metrics']
        print(f"  Completeness: {metrics['completeness']:.1f}%")
        print(f"  Validation errors: {len(metrics['validation_errors'])}")
        
        # Show issues analysis
        print("\nIssues Analysis:")
        issues = report['issues_analysis']
        print(f"  Total issues: {issues['total_issues']}")
        for severity, count in issues['by_severity'].items():
            if count > 0:
                print(f"  {severity.upper()}: {count}")
        
        # Show top recommendations
        print("\nTop Recommendations:")
        for i, rec in enumerate(report['recommendations'][:3]):
            print(f"  {i+1}. {rec}")
        
        # Save report to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(report, f, indent=2, default=str)
            print(f"\nReport saved to: {f.name}")
    
    def demo_custom_validation_rules(self):
        """Demo 7: Adding custom validation rules"""
        print("\n🔧 Demo 7: Custom Validation Rules")
        print("=" * 40)
        
        # Add custom rule for military-specific validation
        custom_rule = ValidationRule(
            rule_id="CUSTOM_UNIT_NAMING",
            rule_type=ValidationRuleType.PATTERN_MATCH,
            severity=ValidationSeverity.WARNING,
            description="Unit callsigns should follow military naming convention",
            column="callsign",
            parameters={'pattern': r'^Unit_\d{3}$'}
        )
        
        print(f"Adding custom rule: {custom_rule.rule_id}")
        self.data_validator.add_validation_rule(custom_rule)
        
        # Test with data that violates the rule
        test_data = pd.DataFrame({
            'callsign': ['Unit_100', 'InvalidUnit', 'Unit_101', 'BadName'],
            'processedtimegmt': ['2025-01-01 10:00:00'] * 4,
            'temp': [25.0] * 4,
            'falldetected': ['No'] * 4,
            'casualtystate': ['GOOD'] * 4
        })
        
        print("Testing custom rule...")
        result = self.data_validator.validate_data(test_data, request_id="custom_rule_test")
        
        # Show custom rule violations
        custom_issues = [i for i in result.issues if i.rule_id == "CUSTOM_UNIT_NAMING"]
        print(f"Custom rule violations: {len(custom_issues)}")
        for issue in custom_issues:
            print(f"  - {issue.message}")
        
        # Demonstrate rule management
        print("\nRule management:")
        print(f"Total rules: {len(self.data_validator.validation_rules)}")
        
        # Disable the custom rule
        self.data_validator.disable_rule("CUSTOM_UNIT_NAMING")
        print("Custom rule disabled")
        
        # Test again
        result2 = self.data_validator.validate_data(test_data, request_id="custom_rule_test2")
        custom_issues2 = [i for i in result2.issues if i.rule_id == "CUSTOM_UNIT_NAMING"]
        print(f"Custom rule violations after disable: {len(custom_issues2)}")
        
        # Re-enable the rule
        self.data_validator.enable_rule("CUSTOM_UNIT_NAMING")
        print("Custom rule re-enabled")
    
    def run_all_demos(self):
        """Run all demonstration scenarios"""
        print("🚀 Data Management Services Demonstration")
        print("=" * 50)
        
        try:
            self.demo_basic_data_loading()
            self.demo_data_validation()
            self.demo_domain_specific_validation()
            self.demo_event_driven_integration()
            self.demo_performance_testing()
            self.demo_validation_report_generation()
            self.demo_custom_validation_rules()
            
            print("\n✅ All demonstrations completed successfully!")
            print("=" * 50)
            
            # Show final statistics
            load_stats = self.data_loader.get_load_statistics()
            validation_stats = self.data_validator.get_validation_statistics()
            
            print("\nFinal Statistics:")
            print(f"Data Loader:")
            print(f"  - Total requests: {load_stats['total_requests']}")
            print(f"  - Successful loads: {load_stats['successful_loads']}")
            print(f"  - Average load time: {load_stats['average_load_time']:.2f}s")
            
            print(f"Data Validator:")
            print(f"  - Total validations: {validation_stats['total_validations']}")
            print(f"  - Issues found: {validation_stats['total_issues_found']}")
            print(f"  - Average validation time: {validation_stats['average_validation_time']:.2f}s")
            
            print(f"\nEvent Activity:")
            print(f"  - Total events: {len(self.events_received)}")
            
        except Exception as e:
            logger.error(f"Error in demonstrations: {e}")
            raise
    
    def cleanup(self):
        """Clean up resources"""
        self.data_loader.cleanup()
        self.data_validator.cleanup()
        logger.info("Demo cleanup completed")


def main():
    """Main entry point for data management demonstration"""
    demo = DataManagementDemo()
    
    try:
        demo.run_all_demos()
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise
    finally:
        demo.cleanup()


if __name__ == "__main__":
    main()
