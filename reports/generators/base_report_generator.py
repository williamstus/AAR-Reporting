# reports/generators/base_report_generator.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from datetime import datetime
import os
import logging
from pathlib import Path

from core.models import AnalysisDomain, AnalysisResult, ReportConfiguration


class BaseReportGenerator(ABC):
    """
    Base class for all report generators
    Provides common functionality for report generation
    """
    
    def __init__(self, output_dir: str = "reports/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.report_type = "base"
    
    @abstractmethod
    def can_handle_config(self, config: ReportConfiguration) -> bool:
        """Check if this generator can handle the given configuration"""
        pass
    
    @abstractmethod
    def generate_report(self, config: ReportConfiguration, results: Dict[AnalysisDomain, AnalysisResult]) -> str:
        """Generate report and return the file path"""
        pass
    
    def _save_report(self, content: str, config: ReportConfiguration) -> str:
        """Save report content to file"""
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.report_type}_{timestamp}.{self._get_file_extension(config.output_format)}"
        file_path = self.output_dir / filename
        
        # Save content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"Report saved to {file_path}")
        return str(file_path)
    
    def _get_file_extension(self, format_type: str) -> str:
        """Get file extension for format type"""
        extensions = {
            'html': 'html',
            'pdf': 'pdf',
            'word': 'docx',
            'excel': 'xlsx',
            'text': 'txt'
        }
        return extensions.get(format_type.lower(), 'txt')
    
    def _create_report_header(self, config: ReportConfiguration) -> Dict[str, Any]:
        """Create standard report header"""
        return {
            'title': config.title,
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'author': config.author,
            'classification': config.classification,
            'report_type': self.report_type,
            'analysis_level': config.analysis_level.value,
            'template_name': config.template_name
        }
    
    def _format_metric_value(self, value: Any) -> str:
        """Format metric value for display"""
        if isinstance(value, float):
            return f"{value:.2f}"
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, bool):
            return "Yes" if value else "No"
        else:
            return str(value)
    
    def _calculate_performance_grade(self, score: float) -> str:
        """Calculate performance grade from score"""
        if score >= 90:
            return "A (Excellent)"
        elif score >= 80:
            return "B (Good)"
        elif score >= 70:
            return "C (Satisfactory)"
        elif score >= 60:
            return "D (Needs Improvement)"
        else:
            return "F (Unsatisfactory)"
    
    def _get_risk_level_color(self, risk_level: str) -> str:
        """Get color code for risk level"""
        colors = {
            'LOW': '#4caf50',
            'MODERATE': '#ff9800',
            'HIGH': '#f44336',
            'CRITICAL': '#d32f2f'
        }
        return colors.get(risk_level.upper(), '#666666')
    
    def _create_metrics_table(self, metrics: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create metrics table data"""
        table_data = []
        for key, value in metrics.items():
            table_data.append({
                'metric': key.replace('_', ' ').title(),
                'value': self._format_metric_value(value),
                'status': self._get_metric_status(key, value)
            })
        return table_data
    
    def _get_metric_status(self, metric_name: str, value: Any) -> str:
        """Get status for a metric"""
        if 'score' in metric_name.lower():
            if isinstance(value, (int, float)):
                if value >= 80:
                    return "Good"
                elif value >= 60:
                    return "Fair"
                else:
                    return "Poor"
        elif 'rate' in metric_name.lower() and 'casualty' in metric_name.lower():
            if isinstance(value, (int, float)):
                if value <= 0.1:
                    return "Good"
                elif value <= 0.2:
                    return "Fair"
                else:
                    return "Poor"
        
        return "Normal"
    
    def _generate_recommendations_summary(self, recommendations: List[str]) -> Dict[str, List[str]]:
        """Categorize recommendations by priority"""
        categorized = {
            'immediate': [],
            'short_term': [],
            'long_term': []
        }
        
        for rec in recommendations:
            if any(keyword in rec.lower() for keyword in ['critical', 'immediate', 'urgent', 'priority']):
                categorized['immediate'].append(rec)
            elif any(keyword in rec.lower() for keyword in ['review', 'implement', 'enhance']):
                categorized['short_term'].append(rec)
            else:
                categorized['long_term'].append(rec)
        
        return categorized
    
    def _create_executive_summary(self, results: Dict[AnalysisDomain, AnalysisResult]) -> Dict[str, Any]:
        """Create executive summary from results"""
        summary = {
            'domains_analyzed': len(results),
            'total_alerts': sum(len(result.alerts) for result in results.values()),
            'critical_alerts': sum(
                len([alert for alert in result.alerts if alert.level.value == 'CRITICAL']) 
                for result in results.values()
            ),
            'overall_status': 'UNKNOWN',
            'key_findings': []
        }
        
        # Determine overall status
        if summary['critical_alerts'] > 0:
            summary['overall_status'] = 'CRITICAL'
        elif summary['total_alerts'] > 5:
            summary['overall_status'] = 'WARNING'
        else:
            summary['overall_status'] = 'GOOD'
        
        # Generate key findings
        for domain, result in results.items():
            if result.metrics:
                key_metric = list(result.metrics.keys())[0]
                summary['key_findings'].append(
                    f"{domain.value}: {key_metric} = {self._format_metric_value(result.metrics[key_metric])}"
                )
        
        return summary
    
    def _validate_config(self, config: ReportConfiguration) -> List[str]:
        """Validate report configuration"""
        errors = []
        
        if not config.title:
            errors.append("Report title is required")
        
        if not config.author:
            errors.append("Report author is required")
        
        if not config.domains:
            errors.append("At least one analysis domain must be selected")
        
        return errors
    
    def _get_template_sections(self, template_name: str) -> List[str]:
        """Get sections for template"""
        templates = {
            'executive_summary': ['overview', 'key_findings', 'recommendations'],
            'detailed_analysis': ['metrics', 'alerts', 'detailed_findings', 'recommendations'],
            'individual_report': ['personal_metrics', 'performance_analysis', 'development_plan'],
            'squad_report': ['team_metrics', 'coordination_analysis', 'collective_performance'],
            'platoon_report': ['strategic_overview', 'resource_utilization', 'mission_effectiveness']
        }
        
        return templates.get(template_name.lower(), ['overview', 'analysis', 'recommendations'])
    
    def get_supported_formats(self) -> List[str]:
        """Get supported output formats"""
        return ['html', 'text', 'pdf', 'word', 'excel']
    
    def get_report_capabilities(self) -> Dict[str, Any]:
        """Get report generator capabilities"""
        return {
            'report_type': self.report_type,
            'supported_formats': self.get_supported_formats(),
            'supported_levels': ['individual', 'squad', 'platoon'],
            'output_directory': str(self.output_dir)
        }