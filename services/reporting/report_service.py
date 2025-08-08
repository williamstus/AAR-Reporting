# services/report_service.py - Report Generation Service
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

import pandas as pd
from jinja2 import Template, Environment, FileSystemLoader

from core.models import (
    ReportGenerator, AnalysisDomain, AnalysisResult, ReportConfiguration,
    AnalysisLevel, Alert, AlertLevel
)
from core.event_bus import EventBus, Event, EventType

class ReportService:
    """
    Centralized report generation service
    Manages multiple report generators and templates
    """
    
    def __init__(self, event_bus: EventBus, output_directory: str = "./reports"):
        self.event_bus = event_bus
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Report generators registry
        self.generators: Dict[str, ReportGenerator] = {}
        
        # Template engine
        self.template_env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=True
        )
        
        # Report templates
        self.templates = {}
        
        # Subscribe to events
        self._setup_event_subscriptions()
        
        # Initialize built-in generators
        self._initialize_builtin_generators()
    
    def _setup_event_subscriptions(self):
        """Setup event subscriptions"""
        self.event_bus.subscribe(EventType.REPORT_REQUESTED, self.on_report_requested, priority=5)
        self.event_bus.subscribe(EventType.ANALYSIS_COMPLETED, self.on_analysis_completed, priority=3)
    
    def _initialize_builtin_generators(self):
        """Initialize built-in report generators"""
        # Individual soldier report generator
        individual_generator = IndividualSoldierReportGenerator(self.event_bus, self.output_directory)
        self.register_generator('individual_soldier', individual_generator)
        
        # Squad level report generator  
        squad_generator = SquadLevelReportGenerator(self.event_bus, self.output_directory)
        self.register_generator('squad_level', squad_generator)
        
        # Platoon operations report generator
        platoon_generator = PlatoonOperationsReportGenerator(self.event_bus, self.output_directory)
        self.register_generator('platoon_operations', platoon_generator)
        
        # Executive summary generator
        executive_generator = ExecutiveSummaryReportGenerator(self.event_bus, self.output_directory)
        self.register_generator('executive_summary', executive_generator)
        
        # Domain-specific report generators
        safety_generator = SafetyReportGenerator(self.event_bus, self.output_directory)
        self.register_generator('safety_analysis', safety_generator)
        
        network_generator = NetworkReportGenerator(self.event_bus, self.output_directory)
        self.register_generator('network_analysis', network_generator)
    
    def register_generator(self, name: str, generator: ReportGenerator):
        """Register a report generator"""
        self.generators[name] = generator
        self.logger.info(f"Registered report generator: {name}")
    
    def unregister_generator(self, name: str):
        """Unregister a report generator"""
        if name in self.generators:
            del self.generators[name]
            self.logger.info(f"Unregistered report generator: {name}")
    
    def register_template(self, name: str, template_path: str, metadata: Dict[str, Any] = None):
        """Register a report template"""
        self.templates[name] = {
            'path': template_path,
            'metadata': metadata or {}
        }
        self.logger.info(f"Registered report template: {name}")
    
    def generate_report(self, config: ReportConfiguration, results: Dict[AnalysisDomain, AnalysisResult]) -> str:
        """Generate a report based on configuration and results"""
        try:
            # Select appropriate generator
            generator = self._select_generator(config)
            
            if generator is None:
                raise ValueError(f"No suitable generator found for configuration: {config}")
            
            # Generate report
            report_path = generator.generate_report(config, results)
            
            # Publish report generated event
            self.event_bus.publish(Event(
                EventType.REPORT_GENERATED,
                {
                    'config': config,
                    'report_path': report_path,
                    'generator': generator.__class__.__name__,
                    'domains': [d.value for d in config.domains],
                    'analysis_level': config.analysis_level.value
                },
                source='ReportService'
            ))
            
            self.logger.info(f"Generated report: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            
            # Publish error event
            self.event_bus.publish(Event(
                EventType.ERROR_OCCURRED,
                {
                    'error': str(e),
                    'config': config,
                    'operation': 'report_generation'
                },
                source='ReportService'
            ))
            
            raise
    
    def _select_generator(self, config: ReportConfiguration) -> Optional[ReportGenerator]:
        """Select the most appropriate generator for the configuration"""
        # Priority order for generator selection
        generator_priority = [
            ('executive_summary', lambda c: len(c.domains) > 2),
            ('safety_analysis', lambda c: AnalysisDomain.SOLDIER_SAFETY in c.domains and len(c.domains) == 1),
            ('network_analysis', lambda c: AnalysisDomain.NETWORK_PERFORMANCE in c.domains and len(c.domains) == 1),
            ('platoon_operations', lambda c: c.analysis_level == AnalysisLevel.PLATOON),
            ('squad_level', lambda c: c.analysis_level == AnalysisLevel.SQUAD),
            ('individual_soldier', lambda c: c.analysis_level == AnalysisLevel.INDIVIDUAL)
        ]
        
        # Find first matching generator
        for generator_name, condition in generator_priority:
            if generator_name in self.generators and condition(config):
                generator = self.generators[generator_name]
                if generator.can_handle_config(config):
                    return generator
        
        # Fallback to any generator that can handle the config
        for generator in self.generators.values():
            if generator.can_handle_config(config):
                return generator
        
        return None
    
    def get_available_generators(self) -> List[str]:
        """Get list of available report generators"""
        return list(self.generators.keys())
    
    def get_available_templates(self) -> List[str]:
        """Get list of available report templates"""
        return list(self.templates.keys())
    
    def on_report_requested(self, event: Event):
        """Handle report generation request"""
        config = event.data.get('config')
        results = event.data.get('results', {})
        
        if config and results:
            try:
                self.generate_report(config, results)
            except Exception as e:
                self.logger.error(f"Failed to generate report from event: {e}")
    
    def on_analysis_completed(self, event: Event):
        """Handle analysis completion - may trigger automatic reports"""
        task_id = event.data.get('task_id')
        
        # Check if auto-reporting is enabled for this task
        # This could be extended to support automatic report generation
        pass

# Specific Report Generators

class IndividualSoldierReportGenerator(ReportGenerator):
    """Generate individual soldier performance reports (REQ-SOLDIER-001 to REQ-SOLDIER-005)"""
    
    def __init__(self, event_bus: EventBus, output_directory: Path):
        super().__init__(['pdf', 'html', 'json'])
        self.event_bus = event_bus
        self.output_directory = output_directory
        self.logger = logging.getLogger(__name__)
    
    def can_handle_config(self, config: ReportConfiguration) -> bool:
        return config.analysis_level == AnalysisLevel.INDIVIDUAL
    
    def generate_report(self, config: ReportConfiguration, results: Dict[AnalysisDomain, AnalysisResult]) -> str:
        """Generate individual soldier performance report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"individual_soldier_report_{timestamp}.{config.export_format}"
        output_path = self.output_directory / filename
        
        # Collect individual unit data
        unit_data = self._extract_unit_data(results)
        
        if config.export_format == 'pdf':
            self._generate_pdf_report(config, unit_data, output_path)
        elif config.export_format == 'html':
            self._generate_html_report(config, unit_data, output_path)
        elif config.export_format == 'json':
            self._generate_json_report(config, unit_data, output_path)
        
        return str(output_path)
    
    def _extract_unit_data(self, results: Dict[AnalysisDomain, AnalysisResult]) -> Dict[str, Dict[str, Any]]:
        """Extract individual unit data from analysis results"""
        unit_data = {}
        
        for domain, result in results.items():
            if domain == AnalysisDomain.SOLDIER_SAFETY:
                # Extract safety data per unit
                safety_scores = result.metrics.get('safety_scores', {})
                for unit, score in safety_scores.items():
                    if unit not in unit_data:
                        unit_data[unit] = {}
                    unit_data[unit]['safety_score'] = score
                
                # Extract fall data
                fall_analysis = result.metrics.get('fall_analysis', {})
                falls_by_unit = fall_analysis.get('falls_by_unit', {})
                for unit, falls in falls_by_unit.items():
                    if unit not in unit_data:
                        unit_data[unit] = {}
                    unit_data[unit]['fall_count'] = falls
            
            elif domain == AnalysisDomain.NETWORK_PERFORMANCE:
                # Extract network performance data per unit
                rssi_analysis = result.metrics.get('rssi_analysis', {})
                unit_performance = rssi_analysis.get('unit_performance', {})
                for unit, perf in unit_performance.items():
                    if unit not in unit_data:
                        unit_data[unit] = {}
                    unit_data[unit]['network_performance'] = perf
        
        return unit_data
    
    def _generate_pdf_report(self, config: ReportConfiguration, unit_data: Dict[str, Dict[str, Any]], output_path: Path):
        """Generate PDF report for individual soldiers"""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        story.append(Paragraph("Individual Soldier Performance Report", styles['Title']))
        story.append(Spacer(1, 20))
        
        # Summary table
        table_data = [['Unit ID', 'Safety Score', 'Fall Count', 'Network Quality', 'Overall Assessment']]
        
        for unit, data in unit_data.items():
            safety_score = data.get('safety_score', 0)
            fall_count = data.get('fall_count', 0)
            network_perf = data.get('network_performance', {})
            avg_rssi = network_perf.get('mean_rssi', 0)
            
            # Calculate overall assessment
            assessment = self._calculate_unit_assessment(data)
            
            table_data.append([
                unit,
                f"{safety_score:.0f}/100",
                str(fall_count),
                f"{avg_rssi:.1f} dBm",
                assessment
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # Individual unit details
        for unit, data in unit_data.items():
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Unit {unit} - Detailed Analysis", styles['Heading2']))
            
            details = self._generate_unit_details(unit, data)
            story.append(Paragraph(details, styles['Normal']))
        
        doc.build(story)
    
    def _generate_html_report(self, config: ReportConfiguration, unit_data: Dict[str, Dict[str, Any]], output_path: Path):
        """Generate HTML report for individual soldiers"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Individual Soldier Performance Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { text-align: center; color: #2c3e50; margin-bottom: 30px; }
                .unit-card { border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 8px; }
                .score-good { color: #27ae60; font-weight: bold; }
                .score-warning { color: #f39c12; font-weight: bold; }
                .score-critical { color: #e74c3c; font-weight: bold; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Individual Soldier Performance Report</h1>
                <p>Generated on {{ timestamp }}</p>
            </div>
            
            <h2>Performance Summary</h2>
            <table>
                <tr>
                    <th>Unit ID</th>
                    <th>Safety Score</th>
                    <th>Fall Count</th>
                    <th>Network Quality</th>
                    <th>Assessment</th>
                </tr>
                {% for unit, data in unit_data.items() %}
                <tr>
                    <td>{{ unit }}</td>
                    <td class="{{ get_score_class(data.get('safety_score', 0)) }}">
                        {{ "%.0f"|format(data.get('safety_score', 0)) }}/100
                    </td>
                    <td>{{ data.get('fall_count', 0) }}</td>
                    <td>{{ "%.1f"|format(data.get('network_performance', {}).get('mean_rssi', 0)) }} dBm</td>
                    <td>{{ calculate_unit_assessment(data) }}</td>
                </tr>
                {% endfor %}
            </table>
            
            <h2>Individual Unit Analysis</h2>
            {% for unit, data in unit_data.items() %}
            <div class="unit-card">
                <h3>Unit {{ unit }}</h3>
                <p>{{ generate_unit_details(unit, data) }}</p>
            </div>
            {% endfor %}
        </body>
        </html>
        """
        
        # Render template
        template = Template(html_template)
        html_content = template.render(
            unit_data=unit_data,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            get_score_class=self._get_score_class,
            calculate_unit_assessment=self._calculate_unit_assessment,
            generate_unit_details=self._generate_unit_details
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_json_report(self, config: ReportConfiguration, unit_data: Dict[str, Dict[str, Any]], output_path: Path):
        """Generate JSON report for individual soldiers"""
        report_data = {
            'report_type': 'individual_soldier_performance',
            'generated_at': datetime.now().isoformat(),
            'analysis_level': config.analysis_level.value,
            'domains': [d.value for d in config.domains],
            'unit_data': unit_data,
            'summary_statistics': self._calculate_summary_statistics(unit_data),
            'recommendations': self._generate_unit_recommendations(unit_data)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
    
    def _calculate_unit_assessment(self, data: Dict[str, Any]) -> str:
        """Calculate overall assessment for a unit"""
        safety_score = data.get('safety_score', 0)
        fall_count = data.get('fall_count', 0)
        network_perf = data.get('network_performance', {})
        avg_rssi = network_perf.get('mean_rssi', 0)
        
        if safety_score >= 80 and fall_count <= 2 and avg_rssi > 15:
            return "EXCELLENT"
        elif safety_score >= 60 and fall_count <= 5 and avg_rssi > 10:
            return "GOOD"
        elif safety_score >= 40 and fall_count <= 10:
            return "NEEDS IMPROVEMENT"
        else:
            return "CRITICAL"
    
    def _get_score_class(self, score: float) -> str:
        """Get CSS class for score display"""
        if score >= 80:
            return "score-good"
        elif score >= 60:
            return "score-warning"
        else:
            return "score-critical"
    
    def _generate_unit_details(self, unit: str, data: Dict[str, Any]) -> str:
        """Generate detailed analysis text for a unit"""
        details = f"Unit {unit} Performance Analysis:\n\n"
        
        safety_score = data.get('safety_score', 0)
        details += f"Safety Score: {safety_score:.0f}/100\n"
        
        fall_count = data.get('fall_count', 0)
        details += f"Fall Incidents: {fall_count}\n"
        
        network_perf = data.get('network_performance', {})
        if network_perf:
            avg_rssi = network_perf.get('mean_rssi', 0)
            details += f"Average Signal Strength: {avg_rssi:.1f} dBm\n"
            
            poor_signal_pct = network_perf.get('poor_signal_percentage', 0)
            details += f"Poor Signal Reports: {poor_signal_pct:.1f}%\n"
        
        assessment = self._calculate_unit_assessment(data)
        details += f"\nOverall Assessment: {assessment}\n"
        
        return details
    
    def _calculate_summary_statistics(self, unit_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics across all units"""
        if not unit_data:
            return {}
        
        safety_scores = [data.get('safety_score', 0) for data in unit_data.values()]
        fall_counts = [data.get('fall_count', 0) for data in unit_data.values()]
        
        return {
            'total_units': len(unit_data),
            'average_safety_score': sum(safety_scores) / len(safety_scores) if safety_scores else 0,
            'total_falls': sum(fall_counts),
            'units_with_falls': sum(1 for count in fall_counts if count > 0),
            'high_performing_units': sum(1 for score in safety_scores if score >= 80),
            'units_needing_attention': sum(1 for score in safety_scores if score < 60)
        }
    
    def _generate_unit_recommendations(self, unit_data: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on unit data"""
        recommendations = []
        
        # Analyze safety scores
        low_safety_units = [unit for unit, data in unit_data.items() 
                          if data.get('safety_score', 0) < 60]
        
        if low_safety_units:
            recommendations.append(
                f"Units requiring immediate safety intervention: {', '.join(low_safety_units)}"
            )
        
        # Analyze fall incidents
        high_fall_units = [unit for unit, data in unit_data.items() 
                         if data.get('fall_count', 0) > 5]
        
        if high_fall_units:
            recommendations.append(
                f"Units with high fall incidents requiring review: {', '.join(high_fall_units)}"
            )
        
        # Network performance issues
        poor_network_units = []
        for unit, data in unit_data.items():
            network_perf = data.get('network_performance', {})
            if network_perf.get('mean_rssi', 0) < 10:
                poor_network_units.append(unit)
        
        if poor_network_units:
            recommendations.append(
                f"Units with poor network connectivity: {', '.join(poor_network_units)}"
            )
        
        if not recommendations:
            recommendations.append("All units performing within acceptable parameters")
        
        return recommendations

class SquadLevelReportGenerator(ReportGenerator):
    """Generate squad-level coordination and effectiveness reports (REQ-SQUAD-001 to REQ-SQUAD-008)"""
    
    def __init__(self, event_bus: EventBus, output_directory: Path):
        super().__init__(['pdf', 'html', 'excel'])
        self.event_bus = event_bus
        self.output_directory = output_directory
        self.logger = logging.getLogger(__name__)
    
    def can_handle_config(self, config: ReportConfiguration) -> bool:
        return config.analysis_level == AnalysisLevel.SQUAD
    
    def generate_report(self, config: ReportConfiguration, results: Dict[AnalysisDomain, AnalysisResult]) -> str:
        """Generate squad-level performance report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"squad_level_report_{timestamp}.{config.export_format}"
        output_path = self.output_directory / filename
        
        # Extract squad data from results
        squad_data = self._extract_squad_data(results)
        
        if config.export_format == 'pdf':
            self._generate_pdf_report(config, squad_data, output_path)
        elif config.export_format == 'html':
            self._generate_html_report(config, squad_data, output_path)
        elif config.export_format == 'excel':
            self._generate_excel_report(config, squad_data, output_path)
        
        return str(output_path)
    
    def _extract_squad_data(self, results: Dict[AnalysisDomain, AnalysisResult]) -> Dict[str, Dict[str, Any]]:
        """Extract squad-level data from analysis results"""
        squad_data = {}
        
        # This would need access to the original data to group by squad
        # For now, we'll create a simplified structure
        for domain, result in results.items():
            # Extract relevant squad metrics from each domain
            pass
        
        return squad_data
    
    def _generate_pdf_report(self, config: ReportConfiguration, squad_data: Dict[str, Dict[str, Any]], output_path: Path):
        """Generate PDF squad report"""
        # Implementation similar to individual report but focused on squad metrics
        pass
    
    def _generate_html_report(self, config: ReportConfiguration, squad_data: Dict[str, Dict[str, Any]], output_path: Path):
        """Generate HTML squad report"""
        pass
    
    def _generate_excel_report(self, config: ReportConfiguration, squad_data: Dict[str, Dict[str, Any]], output_path: Path):
        """Generate Excel squad report with multiple sheets"""
        pass

class PlatoonOperationsReportGenerator(ReportGenerator):
    """Generate platoon-level operations and strategic reports (REQ-PLATOON-001 to REQ-PLATOON-008)"""
    
    def __init__(self, event_bus: EventBus, output_directory: Path):
        super().__init__(['pdf', 'html', 'docx'])
        self.event_bus = event_bus
        self.output_directory = output_directory
        self.logger = logging.getLogger(__name__)
    
    def can_handle_config(self, config: ReportConfiguration) -> bool:
        return config.analysis_level == AnalysisLevel.PLATOON
    
    def generate_report(self, config: ReportConfiguration, results: Dict[AnalysisDomain, AnalysisResult]) -> str:
        """Generate platoon-level operations report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"platoon_operations_report_{timestamp}.{config.export_format}"
        output_path = self.output_directory / filename
        
        # Extract platoon-level strategic data
        platoon_data = self._extract_platoon_data(results)
        
        if config.export_format == 'pdf':
            self._generate_pdf_report(config, platoon_data, output_path)
        elif config.export_format == 'html':
            self._generate_html_report(config, platoon_data, output_path)
        elif config.export_format == 'docx':
            self._generate_docx_report(config, platoon_data, output_path)
        
        return str(output_path)
    
    def _extract_platoon_data(self, results: Dict[AnalysisDomain, AnalysisResult]) -> Dict[str, Any]:
        """Extract platoon-level strategic data"""
        platoon_data = {
            'mission_effectiveness': {},
            'resource_utilization': {},
            'command_effectiveness': {},
            'strategic_recommendations': []
        }
        
        # Calculate mission effectiveness across all domains
        domain_effectiveness = {}
        for domain, result in results.items():
            if result.status == "COMPLETED":
                # Calculate domain-specific effectiveness metrics
                effectiveness_score = self._calculate_domain_effectiveness(domain, result)
                domain_effectiveness[domain.value] = effectiveness_score
        
        platoon_data['mission_effectiveness'] = domain_effectiveness
        
        return platoon_data
    
    def _calculate_domain_effectiveness(self, domain: AnalysisDomain, result: AnalysisResult) -> float:
        """Calculate effectiveness score for a domain"""
        if domain == AnalysisDomain.SOLDIER_SAFETY:
            # Base effectiveness on safety scores and incident rates
            overall_score = result.metrics.get('overall_safety_score', 0)
            return min(overall_score, 100)
        
        elif domain == AnalysisDomain.NETWORK_PERFORMANCE:
            # Base effectiveness on network health
            network_health = result.metrics.get('overall_network_health', 0)
            return min(network_health, 100)
        
        # Default effectiveness calculation
        alert_count = len(result.alerts)
        critical_alerts = len([a for a in result.alerts if a.level == AlertLevel.CRITICAL])
        
        effectiveness = 100 - (critical_alerts * 20) - (alert_count * 5)
        return max(0, min(effectiveness, 100))
    
    def _generate_pdf_report(self, config: ReportConfiguration, platoon_data: Dict[str, Any], output_path: Path):
        """Generate PDF platoon operations report"""
        # Implementation for strategic-level PDF report
        pass
    
    def _generate_html_report(self, config: ReportConfiguration, platoon_data: Dict[str, Any], output_path: Path):
        """Generate HTML platoon operations report"""
        pass
    
    def _generate_docx_report(self, config: ReportConfiguration, platoon_data: Dict[str, Any], output_path: Path):
        """Generate Word document platoon operations report"""
        pass

class ExecutiveSummaryReportGenerator(ReportGenerator):
    """Generate executive summary reports for leadership"""
    
    def __init__(self, event_bus: EventBus, output_directory: Path):
        super().__init__(['pdf', 'html', 'pptx'])
        self.event_bus = event_bus
        self.output_directory = output_directory
        self.logger = logging.getLogger(__name__)
    
    def can_handle_config(self, config: ReportConfiguration) -> bool:
        return len(config.domains) > 2  # Multi-domain analysis
    
    def generate_report(self, config: ReportConfiguration, results: Dict[AnalysisDomain, AnalysisResult]) -> str:
        """Generate executive summary report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"executive_summary_{timestamp}.{config.export_format}"
        output_path = self.output_directory / filename
        
        # Create executive summary data
        summary_data = self._create_executive_summary(config, results)
        
        if config.export_format == 'pdf':
            self._generate_pdf_summary(summary_data, output_path)
        elif config.export_format == 'html':
            self._generate_html_summary(summary_data, output_path)
        elif config.export_format == 'pptx':
            self._generate_pptx_summary(summary_data, output_path)
        
        return str(output_path)
    
    def _create_executive_summary(self, config: ReportConfiguration, results: Dict[AnalysisDomain, AnalysisResult]) -> Dict[str, Any]:
        """Create executive summary data structure"""
        summary = {
            'overview': {},
            'key_findings': [],
            'critical_alerts': [],
            'domain_assessments': {},
            'strategic_recommendations': [],
            'performance_metrics': {}
        }
        
        # Overall assessment
        total_domains = len(results)
        successful_domains = len([r for r in results.values() if r.status == "COMPLETED"])
        
        summary['overview'] = {
            'analysis_level': config.analysis_level.value,
            'domains_analyzed': total_domains,
            'successful_analyses': successful_domains,
            'completion_rate': (successful_domains / total_domains * 100) if total_domains > 0 else 0,
            'generated_at': datetime.now().isoformat()
        }
        
        # Collect critical alerts across all domains
        all_alerts = []
        for result in results.values():
            all_alerts.extend(result.alerts)
        
        critical_alerts = [a for a in all_alerts if a.level == AlertLevel.CRITICAL]
        summary['critical_alerts'] = critical_alerts[:10]  # Top 10 critical alerts
        
        # Domain assessments
        for domain, result in results.items():
            assessment = {
                'status': result.status,
                'execution_time': result.execution_time,
                'alert_count': len(result.alerts),
                'critical_alert_count': len([a for a in result.alerts if a.level == AlertLevel.CRITICAL]),
                'key_metrics': self._extract_key_metrics(domain, result),
                'health_score': self._calculate_domain_health_score(result)
            }
            summary['domain_assessments'][domain.value] = assessment
        
        # Strategic recommendations
        summary['strategic_recommendations'] = self._generate_strategic_recommendations(results)
        
        # Performance metrics
        summary['performance_metrics'] = self._calculate_performance_metrics(results)
        
        return summary
    
    def _extract_key_metrics(self, domain: AnalysisDomain, result: AnalysisResult) -> Dict[str, Any]:
        """Extract key metrics for executive summary"""
        if domain == AnalysisDomain.SOLDIER_SAFETY:
            return {
                'total_falls': result.metrics.get('total_falls', 0),
                'casualty_rate': result.metrics.get('casualty_rate', 0),
                'safety_score': result.metrics.get('overall_safety_score', 0)
            }
        elif domain == AnalysisDomain.NETWORK_PERFORMANCE:
            return {
                'average_rssi': result.metrics.get('average_rssi', 0),
                'network_availability': result.metrics.get('network_availability', 100),
                'mcs_efficiency': result.metrics.get('mcs_efficiency_score', 0)
            }
        
        return {}
    
    def _calculate_domain_health_score(self, result: AnalysisResult) -> float:
        """Calculate health score for a domain"""
        base_score = 100
        
        # Deduct points for alerts
        for alert in result.alerts:
            if alert.level == AlertLevel.CRITICAL:
                base_score -= 20
            elif alert.level == AlertLevel.WARNING:
                base_score -= 10
            else:
                base_score -= 5
        
        # Factor in execution success
        if result.status != "COMPLETED":
            base_score -= 50
        
        return max(0, base_score)
    
    def _generate_strategic_recommendations(self, results: Dict[AnalysisDomain, AnalysisResult]) -> List[str]:
        """Generate strategic-level recommendations"""
        recommendations = []
        
        # Analyze critical issues across domains
        critical_domains = []
        for domain, result in results.items():
            critical_alerts = [a for a in result.alerts if a.level == AlertLevel.CRITICAL]
            if len(critical_alerts) > 0:
                critical_domains.append(domain.value)
        
        if critical_domains:
            recommendations.append(
                f"IMMEDIATE ACTION REQUIRED: Critical issues identified in {', '.join(critical_domains)}"
            )
        
        # Cross-domain recommendations
        safety_result = results.get(AnalysisDomain.SOLDIER_SAFETY)
        network_result = results.get(AnalysisDomain.NETWORK_PERFORMANCE)
        
        if safety_result and network_result:
            # Correlate safety and network issues
            safety_health = self._calculate_domain_health_score(safety_result)
            network_health = self._calculate_domain_health_score(network_result)
            
            if safety_health < 60 and network_health < 60:
                recommendations.append(
                    "STRATEGIC PRIORITY: Poor network performance may be impacting soldier safety - coordinate infrastructure and safety improvements"
                )
        
        # Add general strategic guidance
        overall_health = sum(self._calculate_domain_health_score(r) for r in results.values()) / len(results)
        
        if overall_health >= 80:
            recommendations.append("OPERATIONAL STATUS: Force readiness is optimal - maintain current protocols")
        elif overall_health >= 60:
            recommendations.append("OPERATIONAL STATUS: Force readiness is acceptable - monitor trends and address identified issues")
        else:
            recommendations.append("OPERATIONAL STATUS: Force readiness below standards - implement comprehensive improvement plan")
        
        return recommendations
    
    def _calculate_performance_metrics(self, results: Dict[AnalysisDomain, AnalysisResult]) -> Dict[str, Any]:
        """Calculate overall performance metrics"""
        total_alerts = sum(len(r.alerts) for r in results.values())
        critical_alerts = sum(len([a for a in r.alerts if a.level == AlertLevel.CRITICAL]) for r in results.values())
        
        avg_execution_time = sum(r.execution_time for r in results.values()) / len(results)
        
        return {
            'total_alerts': total_alerts,
            'critical_alerts': critical_alerts,
            'alert_ratio': critical_alerts / total_alerts if total_alerts > 0 else 0,
            'average_execution_time': avg_execution_time,
            'overall_health_score': sum(self._calculate_domain_health_score(r) for r in results.values()) / len(results)
        }
    
    def _generate_pdf_summary(self, summary_data: Dict[str, Any], output_path: Path):
        """Generate PDF executive summary"""
        # Implementation for executive PDF summary
        pass
    
    def _generate_html_summary(self, summary_data: Dict[str, Any], output_path: Path):
        """Generate HTML executive summary"""
        pass
    
    def _generate_pptx_summary(self, summary_data: Dict[str, Any], output_path: Path):
        """Generate PowerPoint executive summary"""
        pass

class SafetyReportGenerator(ReportGenerator):
    """Generate detailed safety analysis reports"""
    
    def __init__(self, event_bus: EventBus, output_directory: Path):
        super().__init__(['pdf', 'html'])
        self.event_bus = event_bus
        self.output_directory = output_directory
        self.logger = logging.getLogger(__name__)
    
    def can_handle_config(self, config: ReportConfiguration) -> bool:
        return AnalysisDomain.SOLDIER_SAFETY in config.domains
    
    def generate_report(self, config: ReportConfiguration, results: Dict[AnalysisDomain, AnalysisResult]) -> str:
        """Generate detailed safety analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"safety_analysis_report_{timestamp}.{config.export_format}"
        output_path = self.output_directory / filename
        
        safety_result = results.get(AnalysisDomain.SOLDIER_SAFETY)
        if not safety_result:
            raise ValueError("No safety analysis results available")
        
        if config.export_format == 'pdf':
            self._generate_pdf_safety_report(safety_result, output_path)
        elif config.export_format == 'html':
            self._generate_html_safety_report(safety_result, output_path)
        
        return str(output_path)
    
    def _generate_pdf_safety_report(self, result: AnalysisResult, output_path: Path):
        """Generate detailed PDF safety report"""
        # Implementation for detailed safety analysis report
        pass
    
    def _generate_html_safety_report(self, result: AnalysisResult, output_path: Path):
        """Generate detailed HTML safety report"""
        pass

class NetworkReportGenerator(ReportGenerator):
    """Generate detailed network performance reports"""
    
    def __init__(self, event_bus: EventBus, output_directory: Path):
        super().__init__(['pdf', 'html'])
        self.event_bus = event_bus
        self.output_directory = output_directory
        self.logger = logging.getLogger(__name__)
    
    def can_handle_config(self, config: ReportConfiguration) -> bool:
        return AnalysisDomain.NETWORK_PERFORMANCE in config.domains
    
    def generate_report(self, config: ReportConfiguration, results: Dict[AnalysisDomain, AnalysisResult]) -> str:
        """Generate detailed network performance report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"network_analysis_report_{timestamp}.{config.export_format}"
        output_path = self.output_directory / filename
        
        network_result = results.get(AnalysisDomain.NETWORK_PERFORMANCE)
        if not network_result:
            raise ValueError("No network analysis results available")
        
        if config.export_format == 'pdf':
            self._generate_pdf_network_report(network_result, output_path)
        elif config.export_format == 'html':
            self._generate_html_network_report(network_result, output_path)
        
        return str(output_path)
    
    def _generate_pdf_network_report(self, result: AnalysisResult, output_path: Path):
        """Generate detailed PDF network report"""
        # Implementation for detailed network analysis report
        pass
    
    def _generate_html_network_report(self, result: AnalysisResult, output_path: Path):
        """Generate detailed HTML network report"""
        pass