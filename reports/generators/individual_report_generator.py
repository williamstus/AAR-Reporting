# reports/generators/individual_report_generator.py
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd

from core.models import AnalysisDomain, AnalysisResult, ReportConfiguration
from reports.generators.base_report_generator import BaseReportGenerator


class IndividualReportGenerator(BaseReportGenerator):
    """
    Individual Soldier Report Generator
    Implements REQ-SOLDIER-001 through REQ-SOLDIER-005
    """
    
    def __init__(self, output_dir: str = "reports/output"):
        super().__init__(output_dir)
        self.report_type = "individual"
    
    def can_handle_config(self, config: ReportConfiguration) -> bool:
        """Check if this generator can handle the configuration"""
        return (
            config.analysis_level.value.lower() == "individual" and
            config.template_name in ["Individual Soldier Report", "Personal Performance Report"]
        )
    
    def generate_report(self, config: ReportConfiguration, results: Dict[AnalysisDomain, AnalysisResult]) -> str:
        """Generate individual soldier report"""
        try:
            # Extract individual soldier data
            individual_data = self._extract_individual_data(results, config)
            
            # Create report content
            report_content = self._create_individual_report_content(individual_data, config)
            
            # Format report
            if config.output_format == 'html':
                formatted_report = self._format_individual_html(report_content, config)
            elif config.output_format == 'pdf':
                formatted_report = self._format_individual_pdf(report_content, config)
            else:
                formatted_report = self._format_individual_text(report_content, config)
            
            # Save report
            filename = self._save_report(formatted_report, config)
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Error generating individual report: {e}")
            raise
    
    def _extract_individual_data(self, results: Dict[AnalysisDomain, AnalysisResult], config: ReportConfiguration) -> Dict[str, Any]:
        """Extract individual soldier data from analysis results"""
        individual_data = {
            'soldier_id': config.get('soldier_id', 'Unknown'),
            'performance_metrics': {},
            'safety_assessment': {},
            'network_performance': {},
            'alerts': [],
            'recommendations': []
        }
        
        # Extract safety data
        if AnalysisDomain.SOLDIER_SAFETY in results:
            safety_result = results[AnalysisDomain.SOLDIER_SAFETY]
            individual_data['safety_assessment'] = self._extract_individual_safety_data(safety_result)
            individual_data['alerts'].extend(self._filter_individual_alerts(safety_result.alerts, individual_data['soldier_id']))
            individual_data['recommendations'].extend(self._filter_individual_recommendations(safety_result.recommendations))
        
        # Extract network data
        if AnalysisDomain.NETWORK_PERFORMANCE in results:
            network_result = results[AnalysisDomain.NETWORK_PERFORMANCE]
            individual_data['network_performance'] = self._extract_individual_network_data(network_result)
            individual_data['alerts'].extend(self._filter_individual_alerts(network_result.alerts, individual_data['soldier_id']))
        
        # Calculate performance metrics
        individual_data['performance_metrics'] = self._calculate_individual_performance_metrics(individual_data)
        
        return individual_data
    
    def _extract_individual_safety_data(self, safety_result: AnalysisResult) -> Dict[str, Any]:
        """Extract individual safety data"""
        return {
            'safety_score': safety_result.metrics.get('overall_safety_score', 0),
            'fall_incidents': safety_result.metrics.get('total_falls', 0),
            'casualty_events': safety_result.metrics.get('casualty_rate', 0),
            'survival_time': safety_result.metrics.get('average_survival_time', 0),
            'risk_level': self._assess_individual_risk_level(safety_result.metrics)
        }
    
    def _extract_individual_network_data(self, network_result: AnalysisResult) -> Dict[str, Any]:
        """Extract individual network performance data"""
        return {
            'signal_quality': network_result.metrics.get('signal_quality_score', 0),
            'connectivity_score': network_result.metrics.get('network_availability', 0),
            'communication_effectiveness': network_result.metrics.get('mcs_efficiency_score', 0),
            'blackout_incidents': network_result.metrics.get('blackout_count', 0)
        }
    
    def _assess_individual_risk_level(self, metrics: Dict[str, Any]) -> str:
        """Assess individual risk level"""
        safety_score = metrics.get('overall_safety_score', 100)
        fall_count = metrics.get('total_falls', 0)
        casualty_rate = metrics.get('casualty_rate', 0)
        
        if safety_score < 50 or fall_count > 10 or casualty_rate > 0.3:
            return "HIGH RISK"
        elif safety_score < 70 or fall_count > 5 or casualty_rate > 0.15:
            return "MODERATE RISK"
        else:
            return "LOW RISK"
    
    def _filter_individual_alerts(self, alerts: List, soldier_id: str) -> List:
        """Filter alerts relevant to individual soldier"""
        individual_alerts = []
        for alert in alerts:
            if alert.affected_units and soldier_id in alert.affected_units:
                individual_alerts.append(alert)
        return individual_alerts
    
    def _filter_individual_recommendations(self, recommendations: List[str]) -> List[str]:
        """Filter recommendations relevant to individual"""
        individual_recs = []
        for rec in recommendations:
            if any(keyword in rec.lower() for keyword in ['individual', 'personal', 'soldier', 'training']):
                individual_recs.append(rec)
        return individual_recs
    
    def _calculate_individual_performance_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate individual performance metrics"""
        safety_score = data['safety_assessment'].get('safety_score', 0)
        network_score = data['network_performance'].get('connectivity_score', 0)
        
        return {
            'overall_performance_score': (safety_score + network_score) / 2,
            'combat_readiness': self._assess_combat_readiness(data),
            'improvement_areas': self._identify_improvement_areas(data),
            'strengths': self._identify_strengths(data)
        }
    
    def _assess_combat_readiness(self, data: Dict[str, Any]) -> str:
        """Assess combat readiness level"""
        overall_score = data['performance_metrics'].get('overall_performance_score', 0)
        risk_level = data['safety_assessment'].get('risk_level', 'UNKNOWN')
        
        if overall_score >= 85 and risk_level == 'LOW RISK':
            return "COMBAT READY"
        elif overall_score >= 70 and risk_level != 'HIGH RISK':
            return "QUALIFIED"
        else:
            return "REQUIRES TRAINING"
    
    def _identify_improvement_areas(self, data: Dict[str, Any]) -> List[str]:
        """Identify areas for improvement"""
        areas = []
        
        if data['safety_assessment'].get('safety_score', 0) < 70:
            areas.append("Safety procedures and awareness")
        
        if data['safety_assessment'].get('fall_incidents', 0) > 3:
            areas.append("Fall prevention and tactical movement")
        
        if data['network_performance'].get('signal_quality', 0) < 70:
            areas.append("Communication equipment usage")
        
        if data['network_performance'].get('connectivity_score', 0) < 70:
            areas.append("Network connectivity and positioning")
        
        return areas
    
    def _identify_strengths(self, data: Dict[str, Any]) -> List[str]:
        """Identify individual strengths"""
        strengths = []
        
        if data['safety_assessment'].get('safety_score', 0) >= 85:
            strengths.append("Excellent safety compliance")
        
        if data['safety_assessment'].get('fall_incidents', 0) == 0:
            strengths.append("No fall incidents - good tactical movement")
        
        if data['network_performance'].get('signal_quality', 0) >= 85:
            strengths.append("Strong communication signal management")
        
        if data['network_performance'].get('connectivity_score', 0) >= 85:
            strengths.append("Reliable network connectivity")
        
        return strengths
    
    def _create_individual_report_content(self, data: Dict[str, Any], config: ReportConfiguration) -> Dict[str, Any]:
        """Create individual report content structure"""
        return {
            'header': {
                'title': f"Individual Soldier Performance Report - {data['soldier_id']}",
                'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'classification': config.classification,
                'report_period': config.get('report_period', 'Current Exercise')
            },
            'executive_summary': {
                'overall_assessment': data['performance_metrics'].get('combat_readiness', 'UNKNOWN'),
                'performance_score': data['performance_metrics'].get('overall_performance_score', 0),
                'risk_level': data['safety_assessment'].get('risk_level', 'UNKNOWN'),
                'key_findings': self._generate_key_findings(data)
            },
            'performance_analysis': {
                'safety_performance': data['safety_assessment'],
                'network_performance': data['network_performance'],
                'overall_metrics': data['performance_metrics']
            },
            'alerts_and_incidents': {
                'active_alerts': data['alerts'],
                'incident_summary': self._create_incident_summary(data)
            },
            'development_plan': {
                'strengths': data['performance_metrics'].get('strengths', []),
                'improvement_areas': data['performance_metrics'].get('improvement_areas', []),
                'recommendations': data['recommendations'],
                'training_priorities': self._generate_training_priorities(data)
            },
            'appendices': {
                'detailed_metrics': data,
                'historical_comparison': self._create_historical_comparison(data)
            }
        }
    
    def _generate_key_findings(self, data: Dict[str, Any]) -> List[str]:
        """Generate key findings for individual"""
        findings = []
        
        overall_score = data['performance_metrics'].get('overall_performance_score', 0)
        findings.append(f"Overall performance score: {overall_score:.1f}/100")
        
        risk_level = data['safety_assessment'].get('risk_level', 'UNKNOWN')
        findings.append(f"Risk assessment: {risk_level}")
        
        readiness = data['performance_metrics'].get('combat_readiness', 'UNKNOWN')
        findings.append(f"Combat readiness: {readiness}")
        
        if data['alerts']:
            findings.append(f"Active alerts: {len(data['alerts'])}")
        
        return findings
    
    def _create_incident_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create incident summary"""
        return {
            'safety_incidents': data['safety_assessment'].get('fall_incidents', 0),
            'network_incidents': data['network_performance'].get('blackout_incidents', 0),
            'total_incidents': data['safety_assessment'].get('fall_incidents', 0) + data['network_performance'].get('blackout_incidents', 0),
            'severity_breakdown': self._categorize_incidents(data['alerts'])
        }
    
    def _categorize_incidents(self, alerts: List) -> Dict[str, int]:
        """Categorize incidents by severity"""
        categories = {'CRITICAL': 0, 'WARNING': 0, 'INFO': 0}
        
        for alert in alerts:
            level = alert.level.value if hasattr(alert, 'level') else 'INFO'
            categories[level] = categories.get(level, 0) + 1
        
        return categories
    
    def _generate_training_priorities(self, data: Dict[str, Any]) -> List[str]:
        """Generate training priorities"""
        priorities = []
        
        improvement_areas = data['performance_metrics'].get('improvement_areas', [])
        
        if 'Safety procedures and awareness' in improvement_areas:
            priorities.append("1. Safety protocols and hazard awareness training")
        
        if 'Fall prevention and tactical movement' in improvement_areas:
            priorities.append("2. Advanced movement techniques and fall prevention")
        
        if 'Communication equipment usage' in improvement_areas:
            priorities.append("3. Communication systems training")
        
        if 'Network connectivity and positioning' in improvement_areas:
            priorities.append("4. Tactical positioning for optimal connectivity")
        
        return priorities
    
    def _create_historical_comparison(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create historical comparison (placeholder)"""
        return {
            'previous_exercises': 'Historical data not available',
            'trend_analysis': 'Trend analysis requires multiple exercise data',
            'performance_trajectory': 'Performance trajectory analysis pending'
        }
    
    def _format_individual_html(self, content: Dict[str, Any], config: ReportConfiguration) -> str:
        """Format individual report as HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{content['header']['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 20px; }}
                .classification {{ background-color: #ffeb3b; padding: 10px; text-align: center; font-weight: bold; margin-bottom: 20px; }}
                .section {{ margin: 30px 0; }}
                .section h2 {{ color: #1976d2; border-bottom: 2px solid #1976d2; padding-bottom: 5px; }}
                .metric-box {{ background-color: #f5f5f5; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #1976d2; }}
                .performance-score {{ font-size: 24px; font-weight: bold; color: #1976d2; }}
                .risk-high {{ color: #f44336; font-weight: bold; }}
                .risk-moderate {{ color: #ff9800; font-weight: bold; }}
                .risk-low {{ color: #4caf50; font-weight: bold; }}
                .alert-critical {{ background-color: #ffebee; border-left: 4px solid #f44336; padding: 10px; margin: 10px 0; }}
                .alert-warning {{ background-color: #fff3e0; border-left: 4px solid #ff9800; padding: 10px; margin: 10px 0; }}
                .recommendation {{ background-color: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .strength {{ background-color: #e8f5e8; padding: 8px; margin: 5px 0; border-radius: 3px; }}
                .improvement {{ background-color: #fff3e0; padding: 8px; margin: 5px 0; border-radius: 3px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="classification">{content['header']['classification']}</div>
            
            <div class="header">
                <h1>{content['header']['title']}</h1>
                <p>Generated: {content['header']['generated_date']}</p>
                <p>Report Period: {content['header']['report_period']}</p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <div class="metric-box">
                    <div class="performance-score">Overall Performance: {content['executive_summary']['performance_score']:.1f}/100</div>
                    <p><strong>Combat Readiness:</strong> {content['executive_summary']['overall_assessment']}</p>
                    <p><strong>Risk Level:</strong> <span class="risk-{content['executive_summary']['risk_level'].lower().replace(' ', '-')}">{content['executive_summary']['risk_level']}</span></p>
                </div>
                
                <h3>Key Findings</h3>
                <ul>
        """
        
        for finding in content['executive_summary']['key_findings']:
            html += f"<li>{finding}</li>"
        
        html += """
                </ul>
            </div>
            
            <div class="section">
                <h2>Performance Analysis</h2>
                
                <h3>Safety Performance</h3>
                <table>
                    <tr><th>Metric</th><th>Value</th><th>Status</th></tr>
        """
        
        safety_perf = content['performance_analysis']['safety_performance']
        html += f"""
                    <tr><td>Safety Score</td><td>{safety_perf.get('safety_score', 0):.1f}/100</td><td>{'Good' if safety_perf.get('safety_score', 0) >= 70 else 'Needs Improvement'}</td></tr>
                    <tr><td>Fall Incidents</td><td>{safety_perf.get('fall_incidents', 0)}</td><td>{'Acceptable' if safety_perf.get('fall_incidents', 0) <= 3 else 'Concerning'}</td></tr>
                    <tr><td>Casualty Rate</td><td>{safety_perf.get('casualty_events', 0):.1%}</td><td>{'Good' if safety_perf.get('casualty_events', 0) <= 0.1 else 'High'}</td></tr>
        """
        
        html += """
                </table>
                
                <h3>Network Performance</h3>
                <table>
                    <tr><th>Metric</th><th>Value</th><th>Status</th></tr>
        """
        
        network_perf = content['performance_analysis']['network_performance']
        html += f"""
                    <tr><td>Signal Quality</td><td>{network_perf.get('signal_quality', 0):.1f}/100</td><td>{'Good' if network_perf.get('signal_quality', 0) >= 70 else 'Poor'}</td></tr>
                    <tr><td>Connectivity Score</td><td>{network_perf.get('connectivity_score', 0):.1f}/100</td><td>{'Reliable' if network_perf.get('connectivity_score', 0) >= 70 else 'Unstable'}</td></tr>
                    <tr><td>Communication Effectiveness</td><td>{network_perf.get('communication_effectiveness', 0):.1f}/100</td><td>{'Effective' if network_perf.get('communication_effectiveness', 0) >= 70 else 'Ineffective'}</td></tr>
        """
        
        html += """
                </table>
            </div>
        """
        
        # Alerts section
        if content['alerts_and_incidents']['active_alerts']:
            html += """
            <div class="section">
                <h2>Active Alerts</h2>
            """
            
            for alert in content['alerts_and_incidents']['active_alerts']:
                alert_class = "alert-critical" if hasattr(alert, 'level') and alert.level.value == 'CRITICAL' else "alert-warning"
                html += f"""
                <div class="{alert_class}">
                    <strong>[{alert.level.value if hasattr(alert, 'level') else 'INFO'}] {alert.alert_type if hasattr(alert, 'alert_type') else 'Alert'}</strong><br>
                    {alert.message if hasattr(alert, 'message') else 'No message'}
                </div>
                """
            
            html += "</div>"
        
        # Development plan
        html += """
            <div class="section">
                <h2>Individual Development Plan</h2>
                
                <h3>Strengths</h3>
        """
        
        for strength in content['development_plan']['strengths']:
            html += f'<div class="strength">✓ {strength}</div>'
        
        html += """
                <h3>Areas for Improvement</h3>
        """
        
        for area in content['development_plan']['improvement_areas']:
            html += f'<div class="improvement">⚠ {area}</div>'
        
        html += """
                <h3>Training Priorities</h3>
                <ol>
        """
        
        for priority in content['development_plan']['training_priorities']:
            html += f"<li>{priority}</li>"
        
        html += """
                </ol>
                
                <h3>Recommendations</h3>
        """
        
        for rec in content['development_plan']['recommendations']:
            html += f'<div class="recommendation">{rec}</div>'
        
        html += f"""
            </div>
            
            <div class="section">
                <h2>Report Summary</h2>
                <p>This individual performance report provides a comprehensive assessment of soldier performance across safety and network domains. Regular review and implementation of the recommended training priorities will enhance overall combat effectiveness.</p>
            </div>
            
            <div class="classification">{content['header']['classification']}</div>
        </body>
        </html>
        """
        
        return html
    
    def _format_individual_text(self, content: Dict[str, Any], config: ReportConfiguration) -> str:
        """Format individual report as plain text"""
        text = f"""
{content['header']['classification']}
{'=' * 80}

{content['header']['title']}
{'-' * len(content['header']['title'])}

Generated: {content['header']['generated_date']}
Report Period: {content['header']['report_period']}

EXECUTIVE SUMMARY
=================

Overall Performance: {content['executive_summary']['performance_score']:.1f}/100
Combat Readiness: {content['executive_summary']['overall_assessment']}
Risk Level: {content['executive_summary']['risk_level']}

Key Findings:
"""
        
        for finding in content['executive_summary']['key_findings']:
            text += f"• {finding}\n"
        
        text += """

PERFORMANCE ANALYSIS
====================

Safety Performance:
"""
        
        safety_perf = content['performance_analysis']['safety_performance']
        text += f"""  Safety Score: {safety_perf.get('safety_score', 0):.1f}/100
  Fall Incidents: {safety_perf.get('fall_incidents', 0)}
  Casualty Rate: {safety_perf.get('casualty_events', 0):.1%}
  Risk Level: {safety_perf.get('risk_level', 'UNKNOWN')}

Network Performance:
"""
        
        network_perf = content['performance_analysis']['network_performance']
        text += f"""  Signal Quality: {network_perf.get('signal_quality', 0):.1f}/100
  Connectivity Score: {network_perf.get('connectivity_score', 0):.1f}/100
  Communication Effectiveness: {network_perf.get('communication_effectiveness', 0):.1f}/100
  Blackout Incidents: {network_perf.get('blackout_incidents', 0)}

"""
        
        # Alerts
        if content['alerts_and_incidents']['active_alerts']:
            text += "ACTIVE ALERTS\n"
            text += "=============\n\n"
            
            for alert in content['alerts_and_incidents']['active_alerts']:
                level = alert.level.value if hasattr(alert, 'level') else 'INFO'
                alert_type = alert.alert_type if hasattr(alert, 'alert_type') else 'Alert'
                message = alert.message if hasattr(alert, 'message') else 'No message'
                text += f"[{level}] {alert_type}: {message}\n"
            
            text += "\n"
        
        # Development plan
        text += "INDIVIDUAL DEVELOPMENT PLAN\n"
        text += "===========================\n\n"
        
        text += "Strengths:\n"
        for strength in content['development_plan']['strengths']:
            text += f"  ✓ {strength}\n"
        
        text += "\nAreas for Improvement:\n"
        for area in content['development_plan']['improvement_areas']:
            text += f"  ⚠ {area}\n"
        
        text += "\nTraining Priorities:\n"
        for i, priority in enumerate(content['development_plan']['training_priorities'], 1):
            text += f"  {i}. {priority}\n"
        
        text += "\nRecommendations:\n"
        for rec in content['development_plan']['recommendations']:
            text += f"  • {rec}\n"
        
        text += f"\n\n{content['header']['classification']}\n"
        
        return text
    
    def _format_individual_pdf(self, content: Dict[str, Any], config: ReportConfiguration) -> str:
        """Format individual report as PDF (placeholder)"""
        return "PDF generation not implemented. Use HTML format for now."