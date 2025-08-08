"""
Report Configuration Models
Defines data structures for report generation configuration and settings.
Part of the Enhanced Soldier Report System refactoring.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pathlib import Path
from datetime import datetime


class ReportFormat(Enum):
    """Supported report output formats"""
    HTML = "html"
    PDF = "pdf"
    EXCEL = "xlsx"
    CSV = "csv"
    JSON = "json"


class ReportType(Enum):
    """Types of reports that can be generated"""
    INDIVIDUAL_SOLDIER = "individual_soldier"
    SQUAD_SUMMARY = "squad_summary"
    BATTLE_ANALYSIS = "battle_analysis"
    SAFETY_REPORT = "safety_report"
    PERFORMANCE_COMPARISON = "performance_comparison"


class SectionType(Enum):
    """Available report sections"""
    HEADER = "header"
    PERFORMANCE_SUMMARY = "performance_summary"
    HEART_RATE_ANALYSIS = "heart_rate_analysis"
    PHYSICAL_PERFORMANCE = "physical_performance"
    EQUIPMENT_STATUS = "equipment_status"
    POSTURE_ANALYSIS = "posture_analysis"
    SAFETY_ANALYSIS = "safety_analysis"
    MEDICAL_RECOMMENDATIONS = "medical_recommendations"
    FOOTER = "footer"


@dataclass
class TemplateConfig:
    """Configuration for HTML template rendering"""
    template_name: str
    template_path: Path
    css_styles: Dict[str, str] = field(default_factory=dict)
    custom_javascript: Optional[str] = None
    include_charts: bool = True
    responsive_design: bool = True


@dataclass
class SectionConfig:
    """Configuration for individual report sections"""
    section_type: SectionType
    title: str
    enabled: bool = True
    order: int = 0
    template_override: Optional[str] = None
    custom_data_fields: List[str] = field(default_factory=list)
    formatting_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricDisplayConfig:
    """Configuration for how metrics are displayed"""
    metric_name: str
    display_name: str
    unit: Optional[str] = None
    decimal_places: int = 1
    format_type: str = "number"  # number, percentage, currency, time
    color_coding: bool = False
    thresholds: Dict[str, float] = field(default_factory=dict)
    chart_type: Optional[str] = None  # bar, line, pie, gauge


@dataclass
class OutputConfig:
    """Configuration for report output settings"""
    output_directory: Path
    filename_template: str = "{callsign}_{timestamp}"
    include_timestamp: bool = True
    compression: bool = False
    watermark: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityConfig:
    """Security and privacy configuration for reports"""
    classification_level: str = "FOR OFFICIAL USE ONLY"
    redact_personal_info: bool = False
    encrypt_reports: bool = False
    access_control: Dict[str, List[str]] = field(default_factory=dict)
    retention_policy: Optional[str] = None


@dataclass
class ChartConfig:
    """Configuration for charts and visualizations"""
    chart_library: str = "plotly"  # plotly, chartjs, d3
    default_width: int = 800
    default_height: int = 400
    color_scheme: List[str] = field(default_factory=lambda: [
        "#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6"
    ])
    interactive: bool = True
    export_formats: List[str] = field(default_factory=lambda: ["png", "svg"])


@dataclass
class LocalizationConfig:
    """Configuration for report localization"""
    language: str = "en-US"
    timezone: str = "UTC"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    number_format: str = "US"
    unit_system: str = "imperial"  # imperial, metric


@dataclass
class ReportConfig:
    """Main configuration class for report generation"""
    
    # Basic identification
    config_name: str
    config_version: str = "1.0"
    created_timestamp: datetime = field(default_factory=datetime.now)
    
    # Report settings
    report_type: ReportType = ReportType.INDIVIDUAL_SOLDIER
    output_format: ReportFormat = ReportFormat.HTML
    
    # Template and styling
    template_config: TemplateConfig = field(default_factory=lambda: TemplateConfig(
        template_name="default_soldier_report",
        template_path=Path("templates/base_report.html")
    ))
    
    # Sections configuration
    sections: List[SectionConfig] = field(default_factory=list)
    
    # Metrics display
    metric_configs: List[MetricDisplayConfig] = field(default_factory=list)
    
    # Output settings
    output_config: OutputConfig = field(default_factory=lambda: OutputConfig(
        output_directory=Path("reports/enhanced")
    ))
    
    # Charts and visualization
    chart_config: ChartConfig = field(default_factory=ChartConfig)
    
    # Security settings
    security_config: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Localization
    localization_config: LocalizationConfig = field(default_factory=LocalizationConfig)
    
    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def get_section_by_type(self, section_type: SectionType) -> Optional[SectionConfig]:
        """Get section configuration by type"""
        for section in self.sections:
            if section.section_type == section_type:
                return section
        return None
    
    def get_metric_config(self, metric_name: str) -> Optional[MetricDisplayConfig]:
        """Get metric configuration by name"""
        for metric in self.metric_configs:
            if metric.metric_name == metric_name:
                return metric
        return None
    
    def get_enabled_sections(self) -> List[SectionConfig]:
        """Get list of enabled sections sorted by order"""
        enabled_sections = [s for s in self.sections if s.enabled]
        return sorted(enabled_sections, key=lambda x: x.order)
    
    def add_section(self, section_config: SectionConfig) -> None:
        """Add a new section configuration"""
        # Remove existing section of same type
        self.sections = [s for s in self.sections if s.section_type != section_config.section_type]
        self.sections.append(section_config)
    
    def add_metric_config(self, metric_config: MetricDisplayConfig) -> None:
        """Add a new metric configuration"""
        # Remove existing config for same metric
        self.metric_configs = [m for m in self.metric_configs if m.metric_name != metric_config.metric_name]
        self.metric_configs.append(metric_config)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Check required fields
        if not self.config_name:
            errors.append("config_name is required")
        
        # Check template path exists
        if not self.template_config.template_path.exists():
            errors.append(f"Template path does not exist: {self.template_config.template_path}")
        
        # Check output directory is valid
        try:
            self.output_config.output_directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create output directory: {e}")
        
        # Check section orders are unique
        orders = [s.order for s in self.sections if s.enabled]
        if len(orders) != len(set(orders)):
            errors.append("Section orders must be unique")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        return {
            "config_name": self.config_name,
            "config_version": self.config_version,
            "created_timestamp": self.created_timestamp.isoformat(),
            "report_type": self.report_type.value,
            "output_format": self.output_format.value,
            "template_config": {
                "template_name": self.template_config.template_name,
                "template_path": str(self.template_config.template_path),
                "css_styles": self.template_config.css_styles,
                "custom_javascript": self.template_config.custom_javascript,
                "include_charts": self.template_config.include_charts,
                "responsive_design": self.template_config.responsive_design
            },
            "sections": [
                {
                    "section_type": s.section_type.value,
                    "title": s.title,
                    "enabled": s.enabled,
                    "order": s.order,
                    "template_override": s.template_override,
                    "custom_data_fields": s.custom_data_fields,
                    "formatting_rules": s.formatting_rules
                } for s in self.sections
            ],
            "metric_configs": [
                {
                    "metric_name": m.metric_name,
                    "display_name": m.display_name,
                    "unit": m.unit,
                    "decimal_places": m.decimal_places,
                    "format_type": m.format_type,
                    "color_coding": m.color_coding,
                    "thresholds": m.thresholds,
                    "chart_type": m.chart_type
                } for m in self.metric_configs
            ],
            "output_config": {
                "output_directory": str(self.output_config.output_directory),
                "filename_template": self.output_config.filename_template,
                "include_timestamp": self.output_config.include_timestamp,
                "compression": self.output_config.compression,
                "watermark": self.output_config.watermark,
                "metadata": self.output_config.metadata
            },
            "chart_config": {
                "chart_library": self.chart_config.chart_library,
                "default_width": self.chart_config.default_width,
                "default_height": self.chart_config.default_height,
                "color_scheme": self.chart_config.color_scheme,
                "interactive": self.chart_config.interactive,
                "export_formats": self.chart_config.export_formats
            },
            "security_config": {
                "classification_level": self.security_config.classification_level,
                "redact_personal_info": self.security_config.redact_personal_info,
                "encrypt_reports": self.security_config.encrypt_reports,
                "access_control": self.security_config.access_control,
                "retention_policy": self.security_config.retention_policy
            },
            "localization_config": {
                "language": self.localization_config.language,
                "timezone": self.localization_config.timezone,
                "date_format": self.localization_config.date_format,
                "number_format": self.localization_config.number_format,
                "unit_system": self.localization_config.unit_system
            },
            "custom_settings": self.custom_settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportConfig':
        """Create configuration from dictionary"""
        config = cls(
            config_name=data["config_name"],
            config_version=data.get("config_version", "1.0"),
            created_timestamp=datetime.fromisoformat(data.get("created_timestamp", datetime.now().isoformat())),
            report_type=ReportType(data.get("report_type", "individual_soldier")),
            output_format=ReportFormat(data.get("output_format", "html"))
        )
        
        # Load template config
        if "template_config" in data:
            tc_data = data["template_config"]
            config.template_config = TemplateConfig(
                template_name=tc_data["template_name"],
                template_path=Path(tc_data["template_path"]),
                css_styles=tc_data.get("css_styles", {}),
                custom_javascript=tc_data.get("custom_javascript"),
                include_charts=tc_data.get("include_charts", True),
                responsive_design=tc_data.get("responsive_design", True)
            )
        
        # Load sections
        if "sections" in data:
            config.sections = [
                SectionConfig(
                    section_type=SectionType(s["section_type"]),
                    title=s["title"],
                    enabled=s.get("enabled", True),
                    order=s.get("order", 0),
                    template_override=s.get("template_override"),
                    custom_data_fields=s.get("custom_data_fields", []),
                    formatting_rules=s.get("formatting_rules", {})
                ) for s in data["sections"]
            ]
        
        # Load metric configs
        if "metric_configs" in data:
            config.metric_configs = [
                MetricDisplayConfig(
                    metric_name=m["metric_name"],
                    display_name=m["display_name"],
                    unit=m.get("unit"),
                    decimal_places=m.get("decimal_places", 1),
                    format_type=m.get("format_type", "number"),
                    color_coding=m.get("color_coding", False),
                    thresholds=m.get("thresholds", {}),
                    chart_type=m.get("chart_type")
                ) for m in data["metric_configs"]
            ]
        
        # Load other configs (output, chart, security, localization)
        if "output_config" in data:
            oc_data = data["output_config"]
            config.output_config = OutputConfig(
                output_directory=Path(oc_data["output_directory"]),
                filename_template=oc_data.get("filename_template", "{callsign}_{timestamp}"),
                include_timestamp=oc_data.get("include_timestamp", True),
                compression=oc_data.get("compression", False),
                watermark=oc_data.get("watermark"),
                metadata=oc_data.get("metadata", {})
            )
        
        # Load custom settings
        config.custom_settings = data.get("custom_settings", {})
        
        return config


def create_default_soldier_report_config() -> ReportConfig:
    """Create a default configuration for individual soldier reports"""
    config = ReportConfig(
        config_name="default_soldier_report",
        config_version="1.0",
        report_type=ReportType.INDIVIDUAL_SOLDIER,
        output_format=ReportFormat.HTML
    )
    
    # Add default sections in order
    sections = [
        SectionConfig(SectionType.HEADER, "Report Header", order=0),
        SectionConfig(SectionType.PERFORMANCE_SUMMARY, "Performance Summary", order=1),
        SectionConfig(SectionType.HEART_RATE_ANALYSIS, "Heart Rate Analysis", order=2),
        SectionConfig(SectionType.PHYSICAL_PERFORMANCE, "Physical Performance", order=3),
        SectionConfig(SectionType.EQUIPMENT_STATUS, "Equipment & Communication", order=4),
        SectionConfig(SectionType.POSTURE_ANALYSIS, "Posture & Movement Analysis", order=5),
        SectionConfig(SectionType.SAFETY_ANALYSIS, "Safety Analysis", order=6),
        SectionConfig(SectionType.MEDICAL_RECOMMENDATIONS, "Medical Recommendations", order=7),
        SectionConfig(SectionType.FOOTER, "Report Footer", order=8)
    ]
    
    for section in sections:
        config.add_section(section)
    
    # Add default metric configurations
    metrics = [
        MetricDisplayConfig("total_records", "Total Data Points", format_type="number"),
        MetricDisplayConfig("total_steps", "Total Steps", format_type="number"),
        MetricDisplayConfig("avg_heart_rate", "Average Heart Rate", "BPM", format_type="number"),
        MetricDisplayConfig("performance_score", "Performance Score", format_type="percentage", 
                           color_coding=True, thresholds={"good": 80, "excellent": 90}),
        MetricDisplayConfig("avg_battery", "Average Battery", "%", format_type="percentage",
                           color_coding=True, thresholds={"warning": 20, "critical": 10})
    ]
    
    for metric in metrics:
        config.add_metric_config(metric)
    
    return config


def create_safety_report_config() -> ReportConfig:
    """Create a configuration focused on safety analysis"""
    config = ReportConfig(
        config_name="safety_focused_report",
        config_version="1.0",
        report_type=ReportType.SAFETY_REPORT,
        output_format=ReportFormat.HTML
    )
    
    # Safety-focused sections
    sections = [
        SectionConfig(SectionType.HEADER, "Safety Report Header", order=0),
        SectionConfig(SectionType.HEART_RATE_ANALYSIS, "Physiological Monitoring", order=1),
        SectionConfig(SectionType.SAFETY_ANALYSIS, "Safety Analysis", order=2),
        SectionConfig(SectionType.MEDICAL_RECOMMENDATIONS, "Medical Recommendations", order=3),
        SectionConfig(SectionType.EQUIPMENT_STATUS, "Equipment Safety", order=4),
        SectionConfig(SectionType.FOOTER, "Report Footer", order=5)
    ]
    
    for section in sections:
        config.add_section(section)
    
    return config
