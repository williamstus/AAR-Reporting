#!/usr/bin/env python3
"""
Simple script to test if all imports are working correctly
"""

print("Testing imports...")

try:
    from core.models import (
        AnalysisDomain, AnalysisLevel, ReportConfiguration, SystemConfiguration,
        AnalysisTask, Alert, AlertLevel
    )
    print("✓ Core models imported successfully")
    print(f"✓ AnalysisLevel values: {[level.value for level in AnalysisLevel]}")
    print(f"✓ AnalysisDomain values: {[domain.value for domain in AnalysisDomain]}")
except Exception as e:
    print(f"✗ Error importing core models: {e}")
    exit(1)

try:
    from core.event_bus import EventBus, Event, EventType
    print("✓ Event bus imported successfully")
except Exception as e:
    print(f"✗ Error importing event bus: {e}")
    exit(1)

try:
    from services.orchestration.analysis_orchestrator import AnalysisOrchestrator
    print("✓ Analysis orchestrator imported successfully")
except Exception as e:
    print(f"✗ Error importing analysis orchestrator: {e}")
    print(f"   This might indicate the import issue is in analysis_orchestrator.py")
    exit(1)

try:
    from services.reporting.report_service import ReportService
    print("✓ Report service imported successfully")
except Exception as e:
    print(f"✗ Error importing report service: {e}")
    print(f"   This might indicate the import issue is in report_service.py")
    exit(1)

try:
    from engines.safety.soldier_safety_engine import SoldierSafetyAnalysisEngine
    print("✓ Safety engine imported successfully")
except Exception as e:
    print(f"✗ Error importing safety engine: {e}")
    exit(1)

try:
    from engines.network.network_performance_engine import NetworkPerformanceAnalysisEngine
    print("✓ Network engine imported successfully")
except Exception as e:
    print(f"✗ Error importing network engine: {e}")
    exit(1)

print("\n🎉 All imports successful! The AAR system should work correctly.")
print("Try running: python main.py")
