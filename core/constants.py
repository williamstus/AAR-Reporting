"""
AAR System Constants
Common constants used throughout the system
"""

# Analysis domains
ANALYSIS_DOMAINS = [
    "soldier_safety",
    "network_performance", 
    "soldier_activity",
    "equipment_management",
    "environmental_monitoring",
    "combat_effectiveness"
]

# Alert levels
ALERT_LEVELS = {
    "INFO": 0,
    "WARNING": 1,
    "CRITICAL": 2
}

# Default thresholds
DEFAULT_SAFETY_THRESHOLDS = {
    "high_fall_risk": 5,
    "critical_fall_risk": 10,
    "safety_score_warning": 70,
    "safety_score_critical": 50
}

DEFAULT_NETWORK_THRESHOLDS = {
    "rssi_excellent": 30,
    "rssi_good": 20,
    "rssi_poor": 10,
    "rssi_critical": 5
}

# File formats
SUPPORTED_INPUT_FORMATS = [".csv"]
SUPPORTED_OUTPUT_FORMATS = ["pdf", "html", "excel", "json"]

# System limits
MAX_CONCURRENT_TASKS = 10
MAX_EVENT_HISTORY = 10000
DEFAULT_TIMEOUT_SECONDS = 300
