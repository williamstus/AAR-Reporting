#!/usr/bin/env python3
"""
Report Controller for Enhanced Individual Soldier Report System
Handles report generation coordination, batch processing, and output management
"""

import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

# Import core system components (would be actual imports in real implementation)
from event_bus import EventBus, EventType
from events import (
    Event, StatusUpdateEvent, ErrorEvent
)
from exceptions import (
    SoldierReportSystemError, ReportGenerationError, 
    DataValidationError
)
from analysis_results import SoldierAnalysisResult, BatchAnalysisResult
from report_config import ReportConfig, ReportFormat, ReportType
from html_renderer import HTMLRenderer
from performance_scorer import PerformanceScorer
from safety_analyzer import SafetyAnalyzer


@dataclass
class ReportGenerationRequest:
    """Request for report generation"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    callsigns: List[str] = field(default_factory=list)
    output_directory: Path = field(default_factory=lambda: Path("reports"))
    dataset: Any = None
    config: Optional[ReportConfig] = None
    custom_config: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ReportGenerationResult:
    """Result of report generation"""
    request_id: str
    callsign: str
    success: bool
    report_path: Optional[Path] = None
    error_message: Optional[str] = None
    generation_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BatchReportSession:
    """Active batch report generation session"""
    session_id: str
    callsigns: List[str]
    config: Optional[ReportConfig] = None
    start_time: datetime = field(default_factory=datetime.now)
    completed_reports: List[ReportGenerationResult] = field(default_factory=list)
    failed_reports: List[ReportGenerationResult] = field(default_factory=list)
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, FAILED, CANCELLED
    
    @property
    def duration_seconds(self) -> Optional[float]:
        if self.status in ['COMPLETED', 'FAILED']:
            return (datetime.now() - self.start_time).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        total = len(self.completed_reports) + len(self.failed_reports)
        if total == 0:
            return 0.0
        return len(self.completed_reports) / total


class ReportController:
    """
    Report Controller - Manages report generation workflow and coordination
    
    Responsibilities:
    - Report generation request processing
    - Batch report coordination
    - Progress tracking and status reporting
    - Output directory management
    - Template and configuration management
    """
    
    def __init__(self, event_bus: EventBus, html_renderer: HTMLRenderer = None):
        self.event_bus = event_bus
        self.component_id = "ReportController"
        
        # Core components
        self.html_renderer = html_renderer or HTMLRenderer()
        self.performance_scorer = PerformanceScorer(event_bus)
        self.safety_analyzer = SafetyAnalyzer(event_bus)
        
        # Session management
        self.active_sessions: Dict[str, BatchReportSession] = {}
        self.generation_history: List[ReportGenerationResult] = []
        
        # Configuration
        self.default_config = self._create_default_report_config()
        self.max_concurrent_reports = 5
        self.chunk_size = 10
        
        # Statistics
        self.stats = {
            'reports_generated': 0,
            'reports_failed': 0,
            'batch_reports_generated': 0,
            'active_sessions': 0,
            'average_generation_time': 0.0
        }
        
        # Setup event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Subscribe to relevant system events"""
        
        # Report generation requests
        self.event_bus.subscribe(
            EventType.REPORT_GENERATION_REQUESTED.value,
            self._handle_report_generation_request,
            priority=10,
            handler_id=f"{self.component_id}_generation_request"
        )
        
        # Analysis completion events
        self.event_bus.subscribe(
            EventType.ANALYSIS_COMPLETED.value,
            self._handle_analysis_completed,
            priority=5,
            handler_id=f"{self.component_id}_analysis_completed"
        )
        
        # Scoring and safety analysis completion
        self.event_bus.subscribe(
            EventType.SCORING_COMPLETED.value,
            self._handle_scoring_completed,
            priority=5,
            handler_id=f"{self.component_id}_scoring_completed"
        )
        
        self.event_bus.subscribe(
            EventType.SAFETY_ANALYSIS_COMPLETED.value,
            self._handle_safety_analysis_completed,
            priority=5,
            handler_id=f"{self.component_id}_safety_analysis_completed"
        )
    
    def _create_default_report_config(self) -> ReportConfig:
        """Create default report configuration"""
        return ReportConfig(
            report_type=ReportType.INDIVIDUAL_SOLDIER,
            report_format=ReportFormat.HTML,
            template_name="enhanced_soldier_report",
            include_performance_breakdown=True,
            include_safety_analysis=True,
            include_medical_recommendations=True,
            include_charts=True,
            classification_level="FOR_OFFICIAL_USE_ONLY"
        )
    
    async def generate_individual_report(
        self, 
        analysis_result: SoldierAnalysisResult,
        config: ReportConfig,
        output_path: Path
    ) -> Path:
        """
        Generate individual soldier report
        
        Args:
            analysis_result: Complete analysis results for soldier
            config: Report configuration
            output_path: Output file path
            
        Returns:
            Path to generated report
            
        Raises:
            ReportGenerationError: If report generation fails
        """
        try:
            start_time = time.time()
            
            # Validate inputs
            self._validate_generation_inputs(analysis_result, config, output_path)
            
            # Generate report based on format
            if config.report_format == ReportFormat.HTML:
                report_path = await self._generate_html_report(
                    analysis_result, config, output_path
                )
            elif config.report_format == ReportFormat.PDF:
                report_path = await self._generate_pdf_report(
                    analysis_result, config, output_path
                )
            elif config.report_format == ReportFormat.JSON:
                report_path = await self._generate_json_report(
                    analysis_result, config, output_path
                )
            else:
                raise ReportGenerationError(f"Unsupported format: {config.report_format}")
            
            # Update statistics
            generation_time = time.time() - start_time
            self._update_generation_stats(generation_time)
            
            # Publish completion event
            self._publish_report_completed(
                analysis_result.soldier_identity.callsign,
                str(report_path),
                generation_time
            )
            
            return report_path
            
        except Exception as e:
            self._publish_error(
                ReportGenerationError(f"Failed to generate report: {e}"),
                f"individual_report_{analysis_result.soldier_identity.callsign}"
            )
            raise
    
    async def generate_batch_reports(
        self,
        batch_results: BatchAnalysisResult,
        config: ReportConfig,
        output_directory: Path,
        progress_callback: Optional[Callable] = None
    ) -> List[Path]:
        """
        Generate batch reports for multiple soldiers
        
        Args:
            batch_results: Complete batch analysis results
            config: Report configuration
            output_directory: Output directory for reports
            progress_callback: Optional progress callback function
            
        Returns:
            List of paths to generated reports
        """
        session_id = str(uuid.uuid4())
        callsigns = [result.soldier_identity.callsign for result in batch_results.soldier_results]
        
        # Create session
        session = BatchReportSession(
            session_id=session_id,
            callsigns=callsigns,
            config=config,
            status="IN_PROGRESS"
        )
        self.active_sessions[session_id] = session
        self.stats['active_sessions'] += 1
        
        try:
            # Publish batch start event
            self._publish_batch_report_started(session_id, len(callsigns))
            
            # Create reports directory
            reports_dir = output_directory / "enhanced_individual_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Process reports in chunks with concurrency control
            generated_reports = []
            successful_count = 0
            failed_count = 0
            
            # Use semaphore to control concurrency
            semaphore = asyncio.Semaphore(self.max_concurrent_reports)
            
            async def process_single_report(soldier_result: SoldierAnalysisResult) -> Optional[Path]:
                async with semaphore:
                    try:
                        callsign = soldier_result.soldier_identity.callsign
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"enhanced_soldier_report_{callsign}_{timestamp}.html"
                        report_path = reports_dir / filename
                        
                        # Generate individual report
                        result_path = await self.generate_individual_report(
                            soldier_result, config, report_path
                        )
                        
                        # Track success
                        session.completed_reports.append(
                            ReportGenerationResult(
                                request_id=session_id,
                                callsign=callsign,
                                success=True,
                                report_path=result_path
                            )
                        )
                        
                        return result_path
                        
                    except Exception as e:
                        # Track failure
                        session.failed_reports.append(
                            ReportGenerationResult(
                                request_id=session_id,
                                callsign=soldier_result.soldier_identity.callsign,
                                success=False,
                                error_message=str(e)
                            )
                        )
                        
                        self._publish_status(
                            f"Failed to generate report for {soldier_result.soldier_identity.callsign}: {e}",
                            "error"
                        )
                        return None
            
            # Process all soldiers concurrently
            tasks = [
                process_single_report(soldier_result)
                for soldier_result in batch_results.soldier_results
            ]
            
            # Track progress
            completed_tasks = 0
            for task in asyncio.as_completed(tasks):
                result = await task
                completed_tasks += 1
                
                if result:
                    successful_count += 1
                    generated_reports.append(result)
                else:
                    failed_count += 1
                
                # Report progress
                if progress_callback:
                    progress_callback(completed_tasks, len(tasks), f"Generated {completed_tasks}/{len(tasks)} reports")
                
                # Publish progress event
                self._publish_progress(completed_tasks, len(tasks), f"Generating reports...")
            
            # Update session status
            session.status = "COMPLETED"
            
            # Publish batch completion event
            self._publish_batch_report_completed(
                session_id, successful_count, failed_count, str(reports_dir)
            )
            
            self.stats['batch_reports_generated'] += 1
            
            return generated_reports
            
        except Exception as e:
            session.status = "FAILED"
            self._publish_error(
                ReportGenerationError(f"Batch report generation failed: {e}"),
                f"batch_generation_{session_id}"
            )
            raise
            
        finally:
            # Clean up session
            self.stats['active_sessions'] -= 1
            if session_id in self.active_sessions:
                # Keep session for history but mark as inactive
                session.status = session.status or "COMPLETED"
    
    async def _generate_html_report(
        self,
        analysis_result: SoldierAnalysisResult,
        config: ReportConfig,
        output_path: Path
    ) -> Path:
        """Generate HTML format report"""
        try:
            # Use HTML renderer to generate report
            html_content = self.html_renderer.render_soldier_report(
                analysis_result, config, config.template_name or "enhanced_soldier_report"
            )
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return output_path
            
        except Exception as e:
            raise ReportGenerationError(f"HTML generation failed: {e}")
    
    async def _generate_pdf_report(
        self,
        analysis_result: SoldierAnalysisResult,
        config: ReportConfig,
        output_path: Path
    ) -> Path:
        """Generate PDF format report (extensible)"""
        try:
            # First generate HTML
            html_content = self.html_renderer.render_soldier_report(
                analysis_result, config, config.template_name or "enhanced_soldier_report"
            )
            
            # Convert HTML to PDF (would use actual PDF library in implementation)
            # For now, save as HTML with .pdf extension for demonstration
            pdf_path = output_path.with_suffix('.pdf')
            
            # In real implementation, would use libraries like:
            # - weasyprint
            # - pdfkit
            # - reportlab
            # Here we'll just save the HTML content as a placeholder
            
            with open(pdf_path, 'w', encoding='utf-8') as f:
                f.write(f"<!-- PDF version would be generated here -->\n{html_content}")
            
            return pdf_path
            
        except Exception as e:
            raise ReportGenerationError(f"PDF generation failed: {e}")
    
    async def _generate_json_report(
        self,
        analysis_result: SoldierAnalysisResult,
        config: ReportConfig,
        output_path: Path
    ) -> Path:
        """Generate JSON format report"""
        try:
            import json
            
            # Convert analysis result to JSON-serializable format
            report_data = {
                'soldier_identity': {
                    'callsign': analysis_result.soldier_identity.callsign,
                    'player_id': analysis_result.soldier_identity.player_id,
                    'squad': analysis_result.soldier_identity.squad,
                    'platoon': analysis_result.soldier_identity.platoon
                },
                'generation_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'config': {
                        'report_type': config.report_type.value if config.report_type else None,
                        'report_format': config.report_format.value if config.report_format else None,
                        'template_name': config.template_name,
                        'classification_level': config.classification_level
                    }
                },
                'analysis_results': {
                    # Would include serialized analysis results
                    'performance_score': getattr(analysis_result, 'performance_score', None),
                    'safety_analysis': getattr(analysis_result, 'safety_analysis', None),
                    'statistics': getattr(analysis_result, 'comprehensive_stats', {})
                }
            }
            
            # Write JSON file
            json_path = output_path.with_suffix('.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            return json_path
            
        except Exception as e:
            raise ReportGenerationError(f"JSON generation failed: {e}")
    
    def _validate_generation_inputs(
        self,
        analysis_result: SoldierAnalysisResult,
        config: ReportConfig,
        output_path: Path
    ) -> None:
        """Validate report generation inputs"""
        if not analysis_result:
            raise DataValidationError("Analysis result is required")
        
        if not config:
            raise DataValidationError("Report configuration is required")
        
        if not output_path:
            raise DataValidationError("Output path is required")
        
        # Validate output directory exists or can be created
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise DataValidationError(f"Cannot create output directory: {e}")
    
    def _update_generation_stats(self, generation_time: float):
        """Update generation statistics"""
        self.stats['reports_generated'] += 1
        
        # Update average generation time
        current_avg = self.stats['average_generation_time']
        count = self.stats['reports_generated']
        self.stats['average_generation_time'] = (
            (current_avg * (count - 1) + generation_time) / count
        )
    
    # Event Handlers
    def _handle_report_generation_request(self, event: Event):
        """Handle report generation request events"""
        try:
            data = event.data
            callsigns = data.get('callsigns', [])
            output_directory = Path(data.get('output_directory', 'reports'))
            dataset = data.get('dataset')
            
            if not callsigns:
                raise DataValidationError("No callsigns specified for report generation")
            
            # Create generation request
            request = ReportGenerationRequest(
                callsigns=callsigns,
                output_directory=output_directory,
                dataset=dataset,
                config=self.default_config
            )
            
            # Start generation in background thread
            def run_generation():
                try:
                    # This would integrate with the analysis engine to get results
                    # For now, we'll simulate the process
                    self._simulate_report_generation(request)
                except Exception as e:
                    self._publish_error(e, f"report_generation_{request.request_id}")
            
            threading.Thread(target=run_generation, daemon=True).start()
            
        except Exception as e:
            self._publish_error(e, "report_generation_request")
    
    def _handle_analysis_completed(self, event: Event):
        """Handle analysis completion events"""
        # This would coordinate with the analysis engine to prepare for report generation
        self._publish_status("Analysis completed - Ready for report generation", "info")
    
    def _handle_scoring_completed(self, event: Event):
        """Handle performance scoring completion"""
        # Update internal state based on scoring results
        result = event.data.get('result')
        if result:
            callsign = result.get('callsign')
            score = result.get('performance_score')
            self._publish_status(f"Performance scoring completed for {callsign}: {score}/100", "info")
    
    def _handle_safety_analysis_completed(self, event: Event):
        """Handle safety analysis completion"""
        # Update internal state based on safety analysis
        result = event.data.get('result')
        if result:
            risk_level = result.get('risk_level', 'Unknown')
            alert_count = result.get('alert_count', 0)
            self._publish_status(f"Safety analysis completed - Risk: {risk_level}, Alerts: {alert_count}", "info")
    
    def _simulate_report_generation(self, request: ReportGenerationRequest):
        """Simulate report generation process (for demonstration)"""
        try:
            self._publish_status(f"Starting report generation for {len(request.callsigns)} soldiers", "info")
            
            # Create output directory
            reports_dir = request.output_directory / "enhanced_individual_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            successful = 0
            failed = 0
            
            for callsign in request.callsigns:
                try:
                    # Simulate report generation
                    time.sleep(0.5)  # Simulate processing time
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"enhanced_soldier_report_{callsign}_{timestamp}.html"
                    report_path = reports_dir / filename
                    
                    # Create simple report content
                    report_content = self._create_sample_report(callsign)
                    
                    with open(report_path, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                    
                    # Publish individual completion
                    self._publish_report_completed(callsign, str(report_path), 0.5)
                    successful += 1
                    
                except Exception as e:
                    self._publish_status(f"Failed to generate report for {callsign}: {e}", "error")
                    failed += 1
            
            # Publish batch completion
            self._publish_batch_report_completed(
                request.request_id, successful, failed, str(reports_dir)
            )
            
        except Exception as e:
            self._publish_error(e, f"simulation_{request.request_id}")
    
    def _create_sample_report(self, callsign: str) -> str:
        """Create sample report content"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Soldier Report - {callsign}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f0f2f5; }}
        .container {{ background: white; padding: 30px; border-radius: 10px; max-width: 800px; margin: 0 auto; }}
        .header {{ background: #3498db; color: white; padding: 20px; text-align: center; border-radius: 8px; margin-bottom: 20px; }}
        .metric {{ background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #3498db; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎖️ Enhanced Soldier Report</h1>
            <h2>{callsign}</h2>
            <p>Generated: {timestamp}</p>
        </div>
        
        <div class="metric">
            <h3>📊 Performance Summary</h3>
            <p><strong>Performance Score:</strong> 85/100</p>
            <p><strong>Status:</strong> GOOD - Above average performance</p>
        </div>
        
        <div class="metric">
            <h3>❤️ Safety Analysis</h3>
            <p><strong>Safety Score:</strong> 95/100</p>
            <p><strong>Medical Alerts:</strong> None</p>
        </div>
        
        <div class="metric">
            <h3>🎯 Assessment Summary</h3>
            <p>This soldier's performance meets military standards with excellent safety metrics.</p>
        </div>
        
        <footer style="text-align: center; margin-top: 30px; padding: 20px; background: #34495e; color: white; border-radius: 8px;">
            <p><strong>🎖️ Enhanced Individual Soldier Report System</strong></p>
            <p>Report ID: {callsign}-{timestamp.replace(' ', '_').replace(':', '')}</p>
        </footer>
    </div>
</body>
</html>
        """
    
    # Event Publishing Methods
    def _publish_report_completed(self, callsign: str, report_path: str, generation_time: float):
        """Publish report completion event"""
        self.event_bus.publish(Event(
            type=EventType.REPORT_COMPLETED.value,
            data={
                'callsign': callsign,
                'report_path': report_path,
                'generation_time': generation_time
            },
            source=self.component_id
        ))
    
    def _publish_batch_report_started(self, session_id: str, total_reports: int):
        """Publish batch report start event"""
        self.event_bus.publish(Event(
            type=EventType.BATCH_REPORT_STARTED.value,
            data={
                'session_id': session_id,
                'total_reports': total_reports
            },
            source=self.component_id
        ))
    
    def _publish_batch_report_completed(
        self, 
        session_id: str, 
        successful: int, 
        failed: int, 
        reports_dir: str
    ):
        """Publish batch report completion event"""
        self.event_bus.publish(Event(
            type=EventType.BATCH_REPORT_COMPLETED.value,
            data={
                'session_id': session_id,
                'successful': successful,
                'failed': failed,
                'reports_dir': reports_dir
            },
            source=self.component_id
        ))
    
    def _publish_progress(self, current: int, total: int, message: str = None):
        """Publish progress update event"""
        self.event_bus.publish(Event(
            type=EventType.REPORT_PROGRESS.value,
            data={
                'current': current,
                'total': total,
                'percentage': (current / total) * 100 if total > 0 else 0,
                'message': message
            },
            source=self.component_id
        ))
    
    def _publish_status(self, message: str, level: str = "info"):
        """Publish status update event"""
        self.event_bus.publish(StatusUpdateEvent(message, level, self.component_id))
    
    def _publish_error(self, error: Exception, context: str = None):
        """Publish error event"""
        self.event_bus.publish(ErrorEvent(error, context, self.component_id))
    
    # Public Interface Methods
    def get_active_sessions(self) -> Dict[str, BatchReportSession]:
        """Get all active report generation sessions"""
        return {k: v for k, v in self.active_sessions.items() if v.status == "IN_PROGRESS"}
    
    def get_session_status(self, session_id: str) -> Optional[BatchReportSession]:
        """Get status of specific session"""
        return self.active_sessions.get(session_id)
    
    def cancel_session(self, session_id: str) -> bool:
        """Cancel active report generation session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if session.status == "IN_PROGRESS":
                session.status = "CANCELLED"
                self.stats['active_sessions'] -= 1
                self._publish_status(f"Report generation session {session_id} cancelled", "warning")
                return True
        return False
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get report generation statistics"""
        return {
            **self.stats,
            'active_sessions_count': len(self.get_active_sessions()),
            'total_sessions': len(self.active_sessions),
            'recent_failures': len([
                r for r in self.generation_history[-50:]  # Last 50 reports
                if not r.success and (datetime.now() - r.timestamp).total_seconds() < 3600  # Last hour
            ])
        }
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old completed sessions"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        sessions_to_remove = []
        for session_id, session in self.active_sessions.items():
            if (session.status in ['COMPLETED', 'FAILED', 'CANCELLED'] and 
                session.start_time < cutoff_time):
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
        
        if sessions_to_remove:
            self._publish_status(f"Cleaned up {len(sessions_to_remove)} old sessions", "info")
    
    def get_report_templates(self) -> List[str]:
        """Get available report templates"""
        # This would integrate with the template manager
        return [
            "enhanced_soldier_report",
            "medical_focus_report", 
            "tactical_assessment_report",
            "safety_monitoring_report"
        ]
    
    def validate_template(self, template_name: str) -> List[str]:
        """Validate report template"""
        # This would integrate with the template manager
        issues = []
        
        if not template_name:
            issues.append("Template name is required")
        elif template_name not in self.get_report_templates():
            issues.append(f"Template '{template_name}' not found")
        
        return issues
    
    def create_custom_config(
        self,
        report_type: ReportType = None,
        report_format: ReportFormat = None,
        template_name: str = None,
        custom_sections: List[str] = None,
        **kwargs
    ) -> ReportConfig:
        """Create custom report configuration"""
        
        config = ReportConfig(
            report_type=report_type or self.default_config.report_type,
            report_format=report_format or self.default_config.report_format,
            template_name=template_name or self.default_config.template_name,
            include_performance_breakdown=kwargs.get('include_performance_breakdown', True),
            include_safety_analysis=kwargs.get('include_safety_analysis', True),
            include_medical_recommendations=kwargs.get('include_medical_recommendations', True),
            include_charts=kwargs.get('include_charts', True),
            classification_level=kwargs.get('classification_level', "FOR_OFFICIAL_USE_ONLY"),
            custom_metrics=kwargs.get('custom_metrics', {}),
            custom_sections=custom_sections or []
        )
        
        return config
    
    async def generate_sample_report(
        self,
        callsign: str,
        output_path: Path,
        config: ReportConfig = None
    ) -> Path:
        """Generate a sample report for testing purposes"""
        try:
            config = config or self.default_config
            
            # Create mock analysis result
            from soldier_data import SoldierIdentity
            from analysis_results import SoldierAnalysisResult
            
            mock_identity = SoldierIdentity(
                callsign=callsign,
                player_id=f"P{callsign}",
                squad="ALPHA",
                platoon="1ST"
            )
            
            # Create minimal analysis result for demonstration
            mock_result = SoldierAnalysisResult(
                soldier_identity=mock_identity,
                performance_score=85,
                comprehensive_stats={
                    'total_records': 150,
                    'avg_heart_rate': 145,
                    'total_steps': 2500,
                    'final_status': 'GOOD'
                },
                safety_analysis={
                    'overall_safety_score': 95,
                    'medical_alerts': [],
                    'temperature_risk': 'LOW'
                }
            )
            
            # Generate report
            return await self.generate_individual_report(
                mock_result, config, output_path
            )
            
        except Exception as e:
            raise ReportGenerationError(f"Sample report generation failed: {e}")
    
    def export_session_report(self, session_id: str, export_path: Path) -> Path:
        """Export session summary report"""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        try:
            summary_data = {
                'session_info': {
                    'session_id': session.session_id,
                    'start_time': session.start_time.isoformat(),
                    'status': session.status,
                    'duration_seconds': session.duration_seconds,
                    'success_rate': session.success_rate
                },
                'soldiers': {
                    'total': len(session.callsigns),
                    'successful': len(session.completed_reports),
                    'failed': len(session.failed_reports),
                    'callsigns': session.callsigns
                },
                'completed_reports': [
                    {
                        'callsign': r.callsign,
                        'report_path': str(r.report_path) if r.report_path else None,
                        'generation_time': r.generation_time,
                        'timestamp': r.timestamp.isoformat()
                    }
                    for r in session.completed_reports
                ],
                'failed_reports': [
                    {
                        'callsign': r.callsign,
                        'error_message': r.error_message,
                        'timestamp': r.timestamp.isoformat()
                    }
                    for r in session.failed_reports
                ]
            }
            
            import json
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            self._publish_status(f"Session report exported to {export_path}", "info")
            return export_path
            
        except Exception as e:
            raise ReportGenerationError(f"Session export failed: {e}")
    
    def get_recent_generation_history(self, limit: int = 50) -> List[ReportGenerationResult]:
        """Get recent report generation history"""
        return self.generation_history[-limit:] if self.generation_history else []
    
    def clear_generation_history(self):
        """Clear report generation history"""
        self.generation_history.clear()
        self._publish_status("Report generation history cleared", "info")


class ReportBatchProcessor:
    """
    Specialized batch processor for large-scale report generation
    Handles concurrent processing with resource management
    """
    
    def __init__(
        self, 
        report_controller: ReportController,
        max_concurrent: int = 5,
        chunk_size: int = 10
    ):
        self.report_controller = report_controller
        self.max_concurrent = max_concurrent
        self.chunk_size = chunk_size
        self.component_id = "ReportBatchProcessor"
    
    async def process_large_batch(
        self,
        batch_results: BatchAnalysisResult,
        config: ReportConfig,
        output_directory: Path,
        progress_callback: Optional[Callable] = None
    ) -> List[Path]:
        """
        Process large batch of reports with optimized resource management
        
        Args:
            batch_results: Complete batch analysis results
            config: Report configuration
            output_directory: Output directory
            progress_callback: Progress callback function
            
        Returns:
            List of generated report paths
        """
        
        total_soldiers = len(batch_results.soldier_results)
        chunks = [
            batch_results.soldier_results[i:i + self.chunk_size]
            for i in range(0, total_soldiers, self.chunk_size)
        ]
        
        all_generated_reports = []
        processed_count = 0
        
        # Process chunks sequentially to manage memory
        for chunk_idx, chunk in enumerate(chunks):
            chunk_reports = await self._process_chunk_with_semaphore(
                chunk, config, output_directory
            )
            
            all_generated_reports.extend([r for r in chunk_reports if r])
            processed_count += len(chunk)
            
            # Report progress
            if progress_callback:
                progress_callback(
                    processed_count, 
                    total_soldiers,
                    f"Processed chunk {chunk_idx + 1}/{len(chunks)}"
                )
        
        return all_generated_reports
    
    async def _process_chunk_with_semaphore(
        self,
        soldier_results: List[SoldierAnalysisResult],
        config: ReportConfig,
        output_directory: Path
    ) -> List[Optional[Path]]:
        """Process a chunk of soldiers with concurrency control"""
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_single_with_semaphore(soldier_result: SoldierAnalysisResult) -> Optional[Path]:
            async with semaphore:
                try:
                    callsign = soldier_result.soldier_identity.callsign
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"report_{callsign}_{timestamp}.html"
                    report_path = output_directory / filename
                    
                    return await self.report_controller.generate_individual_report(
                        soldier_result, config, report_path
                    )
                    
                except Exception as e:
                    print(f"Failed to generate report for {soldier_result.soldier_identity.callsign}: {e}")
                    return None
        
        # Process all soldiers in chunk concurrently
        tasks = [process_single_with_semaphore(result) for result in soldier_results]
        return await asyncio.gather(*tasks, return_exceptions=False)


def create_report_controller_with_dependencies(event_bus: EventBus) -> ReportController:
    """Factory function for creating report controller with all dependencies"""
    
    # Create HTML renderer
    html_renderer = HTMLRenderer()
    
    # Create report controller
    controller = ReportController(event_bus, html_renderer)
    
    return controller


# Example usage and testing
def main():
    """Example usage of ReportController"""
    
    # Create event bus
    event_bus = EventBus(max_workers=4, queue_size=1000)
    event_bus.start()
    
    try:
        # Create report controller
        controller = create_report_controller_with_dependencies(event_bus)
        
        # Example: Generate sample report
        import asyncio
        
        async def test_sample_report():
            output_path = Path("test_reports/sample_ALPHA-01.html")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            report_path = await controller.generate_sample_report(
                callsign="ALPHA-01",
                output_path=output_path
            )
            
            print(f"✅ Sample report generated: {report_path}")
        
        # Run test
        asyncio.run(test_sample_report())
        
        # Print statistics
        stats = controller.get_generation_stats()
        print(f"📊 Generation stats: {stats}")
        
    except Exception as e:
        print(f"❌ Error in report controller: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        event_bus.stop(timeout=2.0)


if __name__ == "__main__":
    main()