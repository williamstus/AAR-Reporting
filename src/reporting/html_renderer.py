"""
HTML Report Renderer (Updated for Core Integration)
Handles HTML template rendering and report formatting.
Updated to integrate with the provided core services.
"""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
import json
from dataclasses import asdict

# Template engine imports
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from jinja2.exceptions import TemplateError, TemplateNotFound

# Updated imports to use provided core services
from src.core.exceptions import ReportGenerationError, SoldierReportSystemError
from src.core.event_bus import EventBus, Event
from src.core.events import EventType, StatusUpdateEvent, ErrorEvent
from src.models.analysis_results import SoldierAnalysisResult, PerformanceScore, PerformanceRating
from src.models.report_config import ReportConfig, SectionType, MetricDisplayConfig


class HTMLRenderer:
    """
    HTML report renderer using Jinja2 templates.
    Updated to integrate with the event bus system.
    """
    
    def __init__(self, template_directory: Path, event_bus: Optional[EventBus] = None):
        """
        Initialize HTML renderer with template directory and event bus.
        
        Args:
            template_directory: Path to directory containing Jinja2 templates
            event_bus: Optional event bus for status updates
        """
        self.template_directory = template_directory
        self.event_bus = event_bus
        self.template_env = None
        self._setup_template_environment()
        
        # Register custom filters and functions
        self._register_template_filters()
        
        # Component identifier for event sourcing
        self.component_id = "HTMLRenderer"
    
    def _setup_template_environment(self) -> None:
        """Setup Jinja2 template environment with security settings"""
        try:
            self.template_env = Environment(
                loader=FileSystemLoader(str(self.template_directory)),
                autoescape=select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True
            )
            
            self._publish_status("Template environment initialized")
            
        except Exception as e:
            error = ReportGenerationError(f"Failed to setup template environment: {e}")
            self._publish_error(error, "template_environment_setup")
            raise error
    
    def _register_template_filters(self) -> None:
        """Register custom Jinja2 filters for report rendering"""
        if not self.template_env:
            return
        
        try:
            # Number formatting filters
            self.template_env.filters['format_number'] = self._format_number
            self.template_env.filters['format_percentage'] = self._format_percentage
            self.template_env.filters['format_decimal'] = self._format_decimal
            
            # Status and color filters
            self.template_env.filters['performance_color'] = self._get_performance_color
            self.template_env.filters['risk_color'] = self._get_risk_color
            self.template_env.filters['status_badge'] = self._get_status_badge
            
            # Date formatting filters
            self.template_env.filters['format_datetime'] = self._format_datetime
            self.template_env.filters['format_duration'] = self._format_duration
            
            # Chart and visualization filters
            self.template_env.filters['to_chart_data'] = self._to_chart_data
            self.template_env.filters['safe_json'] = self._safe_json
            
            self._publish_status("Custom template filters registered")
            
        except Exception as e:
            error = ReportGenerationError(f"Failed to register template filters: {e}")
            self._publish_error(error, "filter_registration")
            raise error
    
    def render_soldier_report(
        self,
        analysis_result: SoldierAnalysisResult,
        config: ReportConfig,
        template_name: Optional[str] = None
    ) -> str:
        """
        Render complete soldier report to HTML.
        
        Args:
            analysis_result: Complete soldier analysis results
            config: Report configuration
            template_name: Optional template override
            
        Returns:
            Rendered HTML string
            
        Raises:
            ReportGenerationError: If rendering fails
        """
        try:
            self._publish_status(f"Starting HTML render for {analysis_result.callsign}")
            
            # Use template from config or parameter
            template_name = template_name or config.template_config.template_name
            template = self._load_template(template_name)
            
            # Prepare template context
            context = self._prepare_soldier_context(analysis_result, config)
            
            # Render template
            html_content = template.render(**context)
            
            self._publish_status(f"Successfully rendered HTML for {analysis_result.callsign}")
            return html_content
            
        except Exception as e:
            error = ReportGenerationError(f"Failed to render soldier report: {e}")
            self._publish_error(error, f"soldier_report_render_{analysis_result.callsign}")
            raise error
    
    def render_section(
        self,
        section_type: SectionType,
        data: Dict[str, Any],
        config: ReportConfig
    ) -> str:
        """
        Render individual report section.
        
        Args:
            section_type: Type of section to render
            data: Section-specific data
            config: Report configuration
            
        Returns:
            Rendered HTML section
        """
        try:
            self._publish_status(f"Rendering section: {section_type.value}")
            
            # Get section configuration
            section_config = config.get_section_by_type(section_type)
            if not section_config or not section_config.enabled:
                self._publish_status(f"Section {section_type.value} disabled, skipping")
                return ""
            
            # Determine template name
            template_name = (section_config.template_override or 
                           f"sections/{section_type.value}.html")
            
            template = self._load_template(template_name)
            
            # Prepare section context
            context = {
                'section_config': section_config,
                'data': data,
                'config': config
            }
            
            rendered_section = template.render(**context)
            self._publish_status(f"Successfully rendered section: {section_type.value}")
            return rendered_section
            
        except Exception as e:
            error = ReportGenerationError(f"Failed to render section {section_type.value}: {e}")
            self._publish_error(error, f"section_render_{section_type.value}")
            raise error
    
    def render_performance_summary(
        self,
        performance_score: PerformanceScore,
        config: ReportConfig
    ) -> str:
        """Render performance summary section"""
        try:
            self._publish_status("Rendering performance summary")
            template = self._load_template("sections/performance_summary.html")
            
            context = {
                'performance_score': performance_score,
                'rating': performance_score.performance_rating,
                'status': performance_score.performance_status,
                'breakdown': performance_score.__dict__,
                'config': config
            }
            
            rendered_content = template.render(**context)
            self._publish_status("Performance summary rendered successfully")
            return rendered_content
            
        except Exception as e:
            error = ReportGenerationError(f"Failed to render performance summary: {e}")
            self._publish_error(error, "performance_summary_render")
            raise error
    
    def render_heart_rate_analysis(
        self,
        heart_rate_data: Dict[str, Any],
        config: ReportConfig
    ) -> str:
        """Render heart rate analysis section with charts"""
        try:
            self._publish_status("Rendering heart rate analysis")
            template = self._load_template("sections/heart_rate_analysis.html")
            
            # Prepare chart data for heart rate zones
            chart_data = self._prepare_heart_rate_chart_data(heart_rate_data)
            
            context = {
                'heart_rate_data': heart_rate_data,
                'chart_data': chart_data,
                'config': config,
                'include_charts': config.chart_config.interactive
            }
            
            rendered_content = template.render(**context)
            self._publish_status("Heart rate analysis rendered successfully")
            return rendered_content
            
        except Exception as e:
            error = ReportGenerationError(f"Failed to render heart rate analysis: {e}")
            self._publish_error(error, "heart_rate_analysis_render")
            raise error
    
    def render_metrics_grid(
        self,
        metrics: Dict[str, Any],
        config: ReportConfig
    ) -> str:
        """Render metrics in a responsive grid layout"""
        try:
            self._publish_status(f"Rendering metrics grid with {len(metrics)} metrics")
            template = self._load_template("components/metrics_grid.html")
            
            # Format metrics according to configuration
            formatted_metrics = []
            for metric_name, value in metrics.items():
                metric_config = config.get_metric_config(metric_name)
                formatted_metric = self._format_metric(metric_name, value, metric_config)
                formatted_metrics.append(formatted_metric)
            
            context = {
                'metrics': formatted_metrics,
                'config': config
            }
            
            rendered_content = template.render(**context)
            self._publish_status("Metrics grid rendered successfully")
            return rendered_content
            
        except Exception as e:
            error = ReportGenerationError(f"Failed to render metrics grid: {e}")
            self._publish_error(error, "metrics_grid_render")
            raise error
    
    def _load_template(self, template_name: str) -> Template:
        """Load Jinja2 template with error handling"""
        try:
            template = self.template_env.get_template(template_name)
            self._publish_status(f"Loaded template: {template_name}")
            return template
            
        except TemplateNotFound:
            error = ReportGenerationError(f"Template not found: {template_name}")
            self._publish_error(error, f"template_not_found_{template_name}")
            raise error
            
        except TemplateError as e:
            error = ReportGenerationError(f"Template error in {template_name}: {e}")
            self._publish_error(error, f"template_error_{template_name}")
            raise error
    
    def _prepare_soldier_context(
        self,
        analysis_result: SoldierAnalysisResult,
        config: ReportConfig
    ) -> Dict[str, Any]:
        """Prepare template context for soldier report"""
        try:
            # Convert analysis result to dictionary for template
            context = {
                'soldier': analysis_result,
                'callsign': analysis_result.callsign,
                'config': config,
                'generation_timestamp': datetime.now(),
                'template_config': config.template_config,
                'chart_config': config.chart_config,
                'security_config': config.security_config
            }
            
            # Add formatted metrics
            if analysis_result.performance_score:
                context['performance_score'] = analysis_result.performance_score
                context['performance_rating'] = analysis_result.performance_score.performance_rating
            
            # Add analysis components
            if analysis_result.heart_rate_analysis:
                context['heart_rate_analysis'] = analysis_result.heart_rate_analysis
            
            if analysis_result.safety_analysis:
                context['safety_analysis'] = analysis_result.safety_analysis
            
            if analysis_result.physical_performance:
                context['physical_performance'] = analysis_result.physical_performance
            
            if analysis_result.equipment_analysis:
                context['equipment_analysis'] = analysis_result.equipment_analysis
            
            return context
            
        except Exception as e:
            error = ReportGenerationError(f"Failed to prepare soldier context: {e}")
            self._publish_error(error, "context_preparation")
            raise error
    
    def _prepare_heart_rate_chart_data(self, heart_rate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare heart rate data for chart visualization"""
        try:
            chart_data = {}
            
            # Heart rate zones data
            if 'hr_zones' in heart_rate_data:
                zones = heart_rate_data['hr_zones']
                chart_data['zones'] = {
                    'labels': list(zones.keys()),
                    'data': list(zones.values()),
                    'backgroundColor': [
                        '#2196f3',  # rest
                        '#4caf50',  # normal
                        '#ff9800',  # elevated
                        '#f44336',  # high
                        '#9c27b0',  # extreme
                        '#f44336'   # critical
                    ]
                }
            
            return chart_data
            
        except Exception as e:
            self._publish_error(
                ReportGenerationError(f"Failed to prepare chart data: {e}"),
                "chart_data_preparation"
            )
            return {}
    
    def _format_metric(
        self,
        metric_name: str,
        value: Any,
        config: Optional[MetricDisplayConfig]
    ) -> Dict[str, Any]:
        """Format a metric according to its configuration"""
        try:
            if not config:
                return {
                    'name': metric_name,
                    'display_name': metric_name.replace('_', ' ').title(),
                    'value': str(value),
                    'formatted_value': str(value),
                    'unit': None
                }
            
            # Format value according to type
            if config.format_type == 'percentage':
                formatted_value = f"{value:.{config.decimal_places}f}%"
            elif config.format_type == 'number':
                if isinstance(value, (int, float)):
                    formatted_value = f"{value:.{config.decimal_places}f}"
                else:
                    formatted_value = str(value)
            else:
                formatted_value = str(value)
            
            # Add unit if specified
            if config.unit:
                formatted_value += f" {config.unit}"
            
            return {
                'name': metric_name,
                'display_name': config.display_name,
                'value': value,
                'formatted_value': formatted_value,
                'unit': config.unit,
                'color_coding': config.color_coding,
                'thresholds': config.thresholds
            }
            
        except Exception as e:
            self._publish_error(
                ReportGenerationError(f"Failed to format metric {metric_name}: {e}"),
                f"metric_formatting_{metric_name}"
            )
            # Return basic formatted metric on error
            return {
                'name': metric_name,
                'display_name': metric_name.replace('_', ' ').title(),
                'value': value,
                'formatted_value': str(value),
                'unit': None
            }
    
    # Event publishing methods
    def _publish_status(self, message: str, level: str = "info") -> None:
        """Publish status update event"""
        if self.event_bus:
            event = StatusUpdateEvent(message, level, self.component_id)
            self.event_bus.publish(event)
    
    def _publish_error(self, error: Exception, context: str = None) -> None:
        """Publish error event"""
        if self.event_bus:
            event = ErrorEvent(error, context, self.component_id)
            self.event_bus.publish(event)
    
    # Template filter functions (unchanged from previous version)
    def _format_number(self, value: Union[int, float], decimal_places: int = 1) -> str:
        """Format number with specified decimal places"""
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.{decimal_places}f}"
        except (ValueError, TypeError):
            return str(value)
    
    def _format_percentage(self, value: Union[int, float], decimal_places: int = 1) -> str:
        """Format value as percentage"""
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.{decimal_places}f}%"
        except (ValueError, TypeError):
            return str(value)
    
    def _format_decimal(self, value: Union[int, float], places: int = 2) -> str:
        """Format decimal with fixed places"""
        return self._format_number(value, places)
    
    def _get_performance_color(self, score: Union[int, float]) -> str:
        """Get color class based on performance score"""
        try:
            score = float(score)
            if score >= 90:
                return "#27ae60"  # Green
            elif score >= 80:
                return "#f39c12"  # Orange
            elif score >= 70:
                return "#e67e22"  # Dark orange
            elif score >= 60:
                return "#e74c3c"  # Red
            else:
                return "#c0392b"  # Dark red
        except (ValueError, TypeError):
            return "#95a5a6"  # Gray for invalid values
    
    def _get_risk_color(self, risk_level: str) -> str:
        """Get color based on risk level"""
        risk_colors = {
            'low': '#27ae60',      # Green
            'moderate': '#f39c12',  # Orange
            'high': '#e74c3c',     # Red
            'critical': '#c0392b'   # Dark red
        }
        return risk_colors.get(risk_level.lower(), '#95a5a6')
    
    def _get_status_badge(self, status: str) -> str:
        """Get HTML badge for status"""
        color = self._get_risk_color(status)
        return f'<span style="background-color: {color}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{status.upper()}</span>'
    
    def _format_datetime(self, dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime object"""
        if not dt:
            return "N/A"
        try:
            return dt.strftime(format_str)
        except (AttributeError, ValueError):
            return str(dt)
    
    def _format_duration(self, minutes: Optional[float]) -> str:
        """Format duration in minutes to human readable format"""
        if minutes is None or minutes <= 0:
            return "N/A"
        
        try:
            minutes = float(minutes)
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            
            if hours > 0:
                return f"{hours}h {mins}m"
            else:
                return f"{mins}m"
        except (ValueError, TypeError):
            return "N/A"
    
    def _to_chart_data(self, data: Dict[str, Any]) -> str:
        """Convert data to JSON for chart visualization"""
        return self._safe_json(data)
    
    def _safe_json(self, data: Any) -> str:
        """Safely convert data to JSON string"""
        try:
            return json.dumps(data, default=str, ensure_ascii=False)
        except (TypeError, ValueError):
            return "{}"


# Additional specialized renderers remain the same but with event integration
class SectionRenderer:
    """
    Specialized renderer for individual report sections.
    Updated to integrate with event system.
    """
    
    def __init__(self, html_renderer: HTMLRenderer, event_bus: Optional[EventBus] = None):
        """
        Initialize section renderer with HTML renderer and event bus.
        
        Args:
            html_renderer: Main HTML renderer instance
            event_bus: Optional event bus for status updates
        """
        self.html_renderer = html_renderer
        self.event_bus = event_bus
        self.component_id = "SectionRenderer"
    
    def render_header_section(self, soldier_data: Dict[str, Any], config: ReportConfig) -> str:
        """Render report header section"""
        try:
            self._publish_status("Rendering header section")
            result = self.html_renderer.render_section(
                SectionType.HEADER,
                soldier_data,
                config
            )
            self._publish_status("Header section rendered successfully")
            return result
        except Exception as e:
            self._publish_error(e, "header_section_render")
            raise
    
    def render_performance_section(self, performance_data: Dict[str, Any], config: ReportConfig) -> str:
        """Render performance summary section"""
        try:
            self._publish_status("Rendering performance section")
            result = self.html_renderer.render_section(
                SectionType.PERFORMANCE_SUMMARY,
                performance_data,
                config
            )
            self._publish_status("Performance section rendered successfully")
            return result
        except Exception as e:
            self._publish_error(e, "performance_section_render")
            raise
    
    def render_safety_section(self, safety_data: Dict[str, Any], config: ReportConfig) -> str:
        """Render safety analysis section"""
        try:
            self._publish_status("Rendering safety section")
            result = self.html_renderer.render_section(
                SectionType.SAFETY_ANALYSIS,
                safety_data,
                config
            )
            self._publish_status("Safety section rendered successfully")
            return result
        except Exception as e:
            self._publish_error(e, "safety_section_render")
            raise
    
    def render_medical_section(self, medical_data: Dict[str, Any], config: ReportConfig) -> str:
        """Render medical recommendations section"""
        try:
            self._publish_status("Rendering medical section")
            result = self.html_renderer.render_section(
                SectionType.MEDICAL_RECOMMENDATIONS,
                medical_data,
                config
            )
            self._publish_status("Medical section rendered successfully")
            return result
        except Exception as e:
            self._publish_error(e, "medical_section_render")
            raise
    
    def render_equipment_section(self, equipment_data: Dict[str, Any], config: ReportConfig) -> str:
        """Render equipment status section"""
        try:
            self._publish_status("Rendering equipment section")
            result = self.html_renderer.render_section(
                SectionType.EQUIPMENT_STATUS,
                equipment_data,
                config
            )
            self._publish_status("Equipment section rendered successfully")
            return result
        except Exception as e:
            self._publish_error(e, "equipment_section_render")
            raise
    
    def _publish_status(self, message: str, level: str = "info") -> None:
        """Publish status update event"""
        if self.event_bus:
            event = StatusUpdateEvent(message, level, self.component_id)
            self.event_bus.publish(event)
    
    def _publish_error(self, error: Exception, context: str = None) -> None:
        """Publish error event"""
        if self.event_bus:
            event = ErrorEvent(error, context, self.component_id)
            self.event_bus.publish(event)


class ChartRenderer:
    """
    Specialized renderer for charts and visualizations.
    Updated to integrate with event system.
    """
    
    def __init__(self, chart_library: str = "plotly", event_bus: Optional[EventBus] = None):
        """
        Initialize chart renderer.
        
        Args:
            chart_library: Chart library to use (plotly, chartjs, etc.)
            event_bus: Optional event bus for status updates
        """
        self.chart_library = chart_library
        self.event_bus = event_bus
        self.component_id = "ChartRenderer"
    
    def render_heart_rate_zones_chart(self, zones_data: Dict[str, int]) -> str:
        """Render heart rate zones pie chart"""
        try:
            self._publish_status(f"Rendering heart rate zones chart using {self.chart_library}")
            
            if self.chart_library == "plotly":
                result = self._render_plotly_pie_chart(zones_data, "Heart Rate Zones")
            elif self.chart_library == "chartjs":
                result = self._render_chartjs_pie_chart(zones_data, "Heart Rate Zones")
            else:
                result = self._render_simple_bar_chart(zones_data)
            
            self._publish_status("Heart rate zones chart rendered successfully")
            return result
            
        except Exception as e:
            self._publish_error(e, "heart_rate_zones_chart")
            return self._render_simple_bar_chart(zones_data)  # Fallback
    
    def render_performance_gauge(self, score: float, max_score: float = 100) -> str:
        """Render performance score as gauge chart"""
        try:
            self._publish_status(f"Rendering performance gauge for score {score}")
            
            if self.chart_library == "plotly":
                result = self._render_plotly_gauge(score, max_score)
            else:
                result = self._render_simple_gauge(score, max_score)
            
            self._publish_status("Performance gauge rendered successfully")
            return result
            
        except Exception as e:
            self._publish_error(e, "performance_gauge")
            return self._render_simple_gauge(score, max_score)  # Fallback
    
    # Chart rendering methods remain the same but with error handling
    def _render_plotly_pie_chart(self, data: Dict[str, int], title: str) -> str:
        """Render pie chart using Plotly"""
        chart_id = f"chart_{hash(title)}"
        return f"""
        <div id="{chart_id}" style="width:100%;height:400px;"></div>
        <script>
            var data = [{
                values: {list(data.values())},
                labels: {list(data.keys())},
                type: 'pie'
            }];
            var layout = {{title: '{title}'}};
            Plotly.newPlot('{chart_id}', data, layout);
        </script>
        """
    
    def _render_chartjs_pie_chart(self, data: Dict[str, int], title: str) -> str:
        """Render pie chart using Chart.js"""
        chart_id = f"chart_{hash(title)}"
        return f"""
        <canvas id="{chart_id}" width="400" height="400"></canvas>
        <script>
            var ctx = document.getElementById('{chart_id}').getContext('2d');
            var chart = new Chart(ctx, {{
                type: 'pie',
                data: {{
                    labels: {list(data.keys())},
                    datasets: [{{
                        data: {list(data.values())},
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'
                        ]
                    }}]
                }},
                options: {{
                    responsive: true,
                    title: {{
                        display: true,
                        text: '{title}'
                    }}
                }}
            }});
        </script>
        """
    
    def _render_simple_bar_chart(self, data: Dict[str, int]) -> str:
        """Render simple HTML/CSS bar chart"""
        if not data:
            return '<div class="no-chart">No chart data available</div>'
            
        max_value = max(data.values())
        
        html = '<div class="simple-chart">'
        for label, value in data.items():
            width_percent = (value / max_value) * 100 if max_value > 0 else 0
            html += f"""
            <div class="chart-row">
                <span class="chart-label">{label}</span>
                <div class="chart-bar" style="width: {width_percent}%"></div>
                <span class="chart-value">{value}</span>
            </div>
            """
        html += '</div>'
        
        return html
    
    def _render_plotly_gauge(self, score: float, max_score: float) -> str:
        """Render gauge chart using Plotly"""
        chart_id = f"gauge_{hash(str(score))}"
        return f"""
        <div id="{chart_id}" style="width:100%;height:400px;"></div>
        <script>
            var data = [{{
                domain: {{ x: [0, 1], y: [0, 1] }},
                value: {score},
                title: {{ text: "Performance Score" }},
                type: "indicator",
                mode: "gauge+number",
                gauge: {{ axis: {{ range: [null, {max_score}] }} }}
            }}];
            var layout = {{ width: 400, height: 400 }};
            Plotly.newPlot('{chart_id}', data, layout);
        </script>
        """
    
    def _render_simple_gauge(self, score: float, max_score: float) -> str:
        """Render simple CSS-based gauge"""
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        return f"""
        <div class="gauge-container">
            <div class="gauge">
                <div class="gauge-fill" style="transform: rotate({percentage * 1.8}deg);"></div>
            </div>
            <div class="gauge-score">{score:.1f}</div>
        </div>
        """
    
    def _publish_status(self, message: str, level: str = "info") -> None:
        """Publish status update event"""
        if self.event_bus:
            event = StatusUpdateEvent(message, level, self.component_id)
            self.event_bus.publish(event)
    
    def _publish_error(self, error: Exception, context: str = None) -> None:
        """Publish error event"""
        if self.event_bus:
            event = ErrorEvent(error, context, self.component_id)
            self.event_bus.publish(event)
