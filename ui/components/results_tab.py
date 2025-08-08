# ui/components/results_tab.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from core.event_bus import EventBus, Event, EventType
from core.models import AnalysisDomain, AnalysisResult, Alert, AlertLevel


class ResultsTab(ttk.Frame):
    """
    Analysis Results Tab - displays analysis results, alerts, and visualizations
    """
    
    def __init__(self, parent, event_bus: EventBus):
        super().__init__(parent)
        self.event_bus = event_bus
        
        # Results storage
        self.analysis_results: Dict[AnalysisDomain, AnalysisResult] = {}
        self.current_alerts: List[Alert] = []
        self.result_history: List[Dict[str, Any]] = []
        
        # UI state
        self.selected_domain = None
        self.selected_metric = None
        
        # Setup event subscriptions
        self._setup_event_subscriptions()
        
        # Create UI
        self._create_ui()
    
    def _setup_event_subscriptions(self):
        """Setup event subscriptions for results updates"""
        self.event_bus.subscribe(EventType.ANALYSIS_COMPLETED, self._on_analysis_completed)
        self.event_bus.subscribe(EventType.ALERT_TRIGGERED, self._on_alert_triggered)
        self.event_bus.subscribe(EventType.ANALYSIS_PROGRESS, self._on_analysis_progress)
    
    def _create_ui(self):
        """Create the results display interface"""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main paned window
        main_paned = ttk.PanedWindow(self, orient='horizontal')
        main_paned.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Left panel - Results navigation
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Right panel - Results display
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)
        
        # Create left panel components
        self._create_navigation_panel(left_frame)
        
        # Create right panel components
        self._create_results_panel(right_frame)
    
    def _create_navigation_panel(self, parent):
        """Create navigation panel for results"""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        
        # Header
        ttk.Label(parent, text="Analysis Results", 
                 font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Domain selection
        domain_frame = ttk.LabelFrame(parent, text="Analysis Domains", padding="5")
        domain_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        domain_frame.grid_columnconfigure(0, weight=1)
        
        self.domain_listbox = tk.Listbox(domain_frame, height=6)
        self.domain_listbox.grid(row=0, column=0, sticky="ew", pady=5)
        self.domain_listbox.bind('<<ListboxSelect>>', self._on_domain_selected)
        
        # Alerts panel
        alerts_frame = ttk.LabelFrame(parent, text="Active Alerts", padding="5")
        alerts_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        alerts_frame.grid_columnconfigure(0, weight=1)
        alerts_frame.grid_rowconfigure(0, weight=1)
        
        # Alerts tree
        self.alerts_tree = ttk.Treeview(alerts_frame, 
                                      columns=('Level', 'Domain', 'Message'),
                                      show='headings', height=10)
        
        self.alerts_tree.heading('Level', text='Level')
        self.alerts_tree.heading('Domain', text='Domain')
        self.alerts_tree.heading('Message', text='Message')
        
        self.alerts_tree.column('Level', width=80)
        self.alerts_tree.column('Domain', width=100)
        self.alerts_tree.column('Message', width=200)
        
        alerts_scroll = ttk.Scrollbar(alerts_frame, orient='vertical', command=self.alerts_tree.yview)
        self.alerts_tree.configure(yscrollcommand=alerts_scroll.set)
        
        self.alerts_tree.grid(row=0, column=0, sticky="nsew")
        alerts_scroll.grid(row=0, column=1, sticky="ns")
        
        # Alert control buttons
        alert_buttons = ttk.Frame(alerts_frame)
        alert_buttons.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        
        ttk.Button(alert_buttons, text="Clear All", command=self._clear_alerts).pack(side="left")
        ttk.Button(alert_buttons, text="Export Alerts", command=self._export_alerts).pack(side="left", padx=(5, 0))
        
        # Analysis history
        history_frame = ttk.LabelFrame(parent, text="Analysis History", padding="5")
        history_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        
        self.history_listbox = tk.Listbox(history_frame, height=4)
        self.history_listbox.pack(fill="x", pady=5)
        self.history_listbox.bind('<<ListboxSelect>>', self._on_history_selected)
        
        ttk.Button(history_frame, text="Clear History", command=self._clear_history).pack(pady=5)
    
    def _create_results_panel(self, parent):
        """Create results display panel"""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        
        # Results notebook
        self.results_notebook = ttk.Notebook(parent)
        self.results_notebook.grid(row=0, column=0, sticky="nsew")
        
        # Overview tab
        self._create_overview_tab()
        
        # Detailed results tab
        self._create_detailed_tab()
        
        # Visualizations tab
        self._create_visualizations_tab()
        
        # Recommendations tab
        self._create_recommendations_tab()
        
        # Raw data tab
        self._create_raw_data_tab()
        
        # Export controls
        export_frame = ttk.Frame(parent)
        export_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        ttk.Button(export_frame, text="Export Results", command=self._export_results).pack(side="left")
        ttk.Button(export_frame, text="Generate Report", command=self._generate_report).pack(side="left", padx=(5, 0))
        ttk.Button(export_frame, text="Refresh", command=self._refresh_results).pack(side="left", padx=(5, 0))
    
    def _create_overview_tab(self):
        """Create overview tab"""
        overview_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(overview_frame, text="Overview")
        
        # Summary statistics
        summary_frame = ttk.LabelFrame(overview_frame, text="Analysis Summary", padding="10")
        summary_frame.pack(fill="x", padx=10, pady=5)
        
        self.summary_text = tk.Text(summary_frame, height=8, wrap="word")
        summary_scroll = ttk.Scrollbar(summary_frame, orient='vertical', command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scroll.set)
        
        self.summary_text.pack(side="left", fill="both", expand=True)
        summary_scroll.pack(side="right", fill="y")
        
        # Key metrics
        metrics_frame = ttk.LabelFrame(overview_frame, text="Key Metrics", padding="10")
        metrics_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Metrics tree
        self.metrics_tree = ttk.Treeview(metrics_frame, 
                                       columns=('Domain', 'Metric', 'Value', 'Status'),
                                       show='headings', height=12)
        
        self.metrics_tree.heading('Domain', text='Domain')
        self.metrics_tree.heading('Metric', text='Metric')
        self.metrics_tree.heading('Value', text='Value')
        self.metrics_tree.heading('Status', text='Status')
        
        self.metrics_tree.column('Domain', width=150)
        self.metrics_tree.column('Metric', width=200)
        self.metrics_tree.column('Value', width=100)
        self.metrics_tree.column('Status', width=100)
        
        metrics_scroll = ttk.Scrollbar(metrics_frame, orient='vertical', command=self.metrics_tree.yview)
        self.metrics_tree.configure(yscrollcommand=metrics_scroll.set)
        
        self.metrics_tree.pack(side="left", fill="both", expand=True)
        metrics_scroll.pack(side="right", fill="y")
    
    def _create_detailed_tab(self):
        """Create detailed results tab"""
        detailed_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(detailed_frame, text="Detailed Results")
        
        # Domain-specific results
        domain_frame = ttk.LabelFrame(detailed_frame, text="Domain Analysis", padding="10")
        domain_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.detailed_text = tk.Text(domain_frame, wrap="word", font=("Courier", 10))
        detailed_scroll = ttk.Scrollbar(domain_frame, orient='vertical', command=self.detailed_text.yview)
        self.detailed_text.configure(yscrollcommand=detailed_scroll.set)
        
        self.detailed_text.pack(side="left", fill="both", expand=True)
        detailed_scroll.pack(side="right", fill="y")
        
        # Domain selection for detailed view
        detail_control_frame = ttk.Frame(detailed_frame)
        detail_control_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(detail_control_frame, text="Select Domain:").pack(side="left")
        self.detailed_domain_var = tk.StringVar()
        self.detailed_domain_combo = ttk.Combobox(detail_control_frame, textvariable=self.detailed_domain_var, 
                                                state="readonly", width=30)
        self.detailed_domain_combo.pack(side="left", padx=(5, 0))
        self.detailed_domain_combo.bind('<<ComboboxSelected>>', self._on_detailed_domain_selected)
        
        ttk.Button(detail_control_frame, text="Refresh", 
                  command=self._refresh_detailed_results).pack(side="left", padx=(5, 0))
    
    def _create_visualizations_tab(self):
        """Create visualizations tab"""
        viz_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(viz_frame, text="Visualizations")
        
        # Visualization controls
        viz_control_frame = ttk.Frame(viz_frame)
        viz_control_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(viz_control_frame, text="Visualization Type:").pack(side="left")
        self.viz_type_var = tk.StringVar(value="Summary Dashboard")
        viz_type_combo = ttk.Combobox(viz_control_frame, textvariable=self.viz_type_var,
                                    values=["Summary Dashboard", "Safety Metrics", "Network Performance", 
                                           "Alert Timeline", "Unit Comparison"],
                                    state="readonly", width=20)
        viz_type_combo.pack(side="left", padx=(5, 0))
        viz_type_combo.bind('<<ComboboxSelected>>', self._on_viz_type_selected)
        
        ttk.Button(viz_control_frame, text="Generate", 
                  command=self._generate_visualization).pack(side="left", padx=(5, 0))
        ttk.Button(viz_control_frame, text="Export Chart", 
                  command=self._export_visualization).pack(side="left", padx=(5, 0))
        
        # Visualization canvas
        self.viz_frame = ttk.Frame(viz_frame)
        self.viz_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Placeholder for matplotlib canvas
        self.viz_canvas = None
        self.viz_figure = None
    
    def _create_recommendations_tab(self):
        """Create recommendations tab"""
        rec_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(rec_frame, text="Recommendations")
        
        # Recommendations by domain
        rec_notebook = ttk.Notebook(rec_frame)
        rec_notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Safety recommendations
        safety_rec_frame = ttk.Frame(rec_notebook)
        rec_notebook.add(safety_rec_frame, text="Safety")
        
        self.safety_rec_text = tk.Text(safety_rec_frame, wrap="word", height=15)
        safety_rec_scroll = ttk.Scrollbar(safety_rec_frame, orient='vertical', command=self.safety_rec_text.yview)
        self.safety_rec_text.configure(yscrollcommand=safety_rec_scroll.set)
        
        self.safety_rec_text.pack(side="left", fill="both", expand=True)
        safety_rec_scroll.pack(side="right", fill="y")
        
        # Network recommendations
        network_rec_frame = ttk.Frame(rec_notebook)
        rec_notebook.add(network_rec_frame, text="Network")
        
        self.network_rec_text = tk.Text(network_rec_frame, wrap="word", height=15)
        network_rec_scroll = ttk.Scrollbar(network_rec_frame, orient='vertical', command=self.network_rec_text.yview)
        self.network_rec_text.configure(yscrollcommand=network_rec_scroll.set)
        
        self.network_rec_text.pack(side="left", fill="both", expand=True)
        network_rec_scroll.pack(side="right", fill="y")
        
        # Action plan
        action_frame = ttk.LabelFrame(rec_frame, text="Action Plan", padding="10")
        action_frame.pack(fill="x", padx=10, pady=5)
        
        self.action_text = tk.Text(action_frame, height=6, wrap="word")
        action_scroll = ttk.Scrollbar(action_frame, orient='vertical', command=self.action_text.yview)
        self.action_text.configure(yscrollcommand=action_scroll.set)
        
        self.action_text.pack(side="left", fill="both", expand=True)
        action_scroll.pack(side="right", fill="y")
        
        # Generate action plan button
        ttk.Button(action_frame, text="Generate Action Plan", 
                  command=self._generate_action_plan).pack(pady=5)
    
    def _create_raw_data_tab(self):
        """Create raw data tab"""
        raw_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(raw_frame, text="Raw Data")
        
        # Raw data display
        raw_tree_frame = ttk.Frame(raw_frame)
        raw_tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.raw_tree = ttk.Treeview(raw_tree_frame, show='headings', height=20)
        
        raw_v_scroll = ttk.Scrollbar(raw_tree_frame, orient='vertical', command=self.raw_tree.yview)
        raw_h_scroll = ttk.Scrollbar(raw_tree_frame, orient='horizontal', command=self.raw_tree.xview)
        self.raw_tree.configure(yscrollcommand=raw_v_scroll.set, xscrollcommand=raw_h_scroll.set)
        
        self.raw_tree.grid(row=0, column=0, sticky="nsew")
        raw_v_scroll.grid(row=0, column=1, sticky="ns")
        raw_h_scroll.grid(row=1, column=0, sticky="ew")
        
        raw_tree_frame.grid_columnconfigure(0, weight=1)
        raw_tree_frame.grid_rowconfigure(0, weight=1)
        
        # Raw data controls
        raw_control_frame = ttk.Frame(raw_frame)
        raw_control_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(raw_control_frame, text="Display:").pack(side="left")
        self.raw_display_var = tk.StringVar(value="Analysis Results")
        raw_display_combo = ttk.Combobox(raw_control_frame, textvariable=self.raw_display_var,
                                       values=["Analysis Results", "Alert Details", "Metrics Only"],
                                       state="readonly", width=15)
        raw_display_combo.pack(side="left", padx=(5, 0))
        raw_display_combo.bind('<<ComboboxSelected>>', self._on_raw_display_selected)
        
        ttk.Button(raw_control_frame, text="Export Raw Data", 
                  command=self._export_raw_data).pack(side="left", padx=(5, 0))
    
    def _update_domain_list(self):
        """Update domain list with available results"""
        self.domain_listbox.delete(0, tk.END)
        self.detailed_domain_combo['values'] = []
        
        domain_values = []
        for domain in self.analysis_results.keys():
            domain_name = domain.value
            self.domain_listbox.insert(tk.END, domain_name)
            domain_values.append(domain_name)
        
        self.detailed_domain_combo['values'] = domain_values
        
        # Select first domain if available
        if domain_values:
            self.detailed_domain_combo.set(domain_values[0])
    
    def _update_alerts_display(self):
        """Update alerts display"""
        # Clear existing alerts
        for item in self.alerts_tree.get_children():
            self.alerts_tree.delete(item)
        
        # Add current alerts
        for alert in self.current_alerts:
            level_color = self._get_alert_color(alert.level)
            item = self.alerts_tree.insert('', 'end', values=(
                alert.level.value,
                alert.alert_type,
                alert.message[:50] + "..." if len(alert.message) > 50 else alert.message
            ))
            
            # Color code by alert level
            if alert.level == AlertLevel.CRITICAL:
                self.alerts_tree.set(item, 'Level', '🔴 ' + alert.level.value)
            elif alert.level == AlertLevel.WARNING:
                self.alerts_tree.set(item, 'Level', '🟡 ' + alert.level.value)
            else:
                self.alerts_tree.set(item, 'Level', '🟢 ' + alert.level.value)
    
    def _get_alert_color(self, level: AlertLevel) -> str:
        """Get color for alert level"""
        if level == AlertLevel.CRITICAL:
            return '#ff4444'
        elif level == AlertLevel.WARNING:
            return '#ffaa00'
        else:
            return '#44ff44'
    
    def _update_summary(self):
        """Update summary display"""
        if not self.analysis_results:
            summary_text = "No analysis results available.\nRun analysis to see results here."
        else:
            summary_text = f"Analysis Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            summary_text += "=" * 60 + "\n\n"
            
            # Overall statistics
            total_alerts = len(self.current_alerts)
            critical_alerts = sum(1 for alert in self.current_alerts if alert.level == AlertLevel.CRITICAL)
            warning_alerts = sum(1 for alert in self.current_alerts if alert.level == AlertLevel.WARNING)
            
            summary_text += f"Domains Analyzed: {len(self.analysis_results)}\n"
            summary_text += f"Total Alerts: {total_alerts} (Critical: {critical_alerts}, Warning: {warning_alerts})\n\n"
            
            # Domain-specific summaries
            for domain, result in self.analysis_results.items():
                summary_text += f"{domain.value} Analysis:\n"
                summary_text += f"  Status: {result.status}\n"
                summary_text += f"  Execution Time: {result.execution_time:.2f}s\n"
                summary_text += f"  Data Quality: {result.data_quality_score:.1f}%\n"
                summary_text += f"  Alerts Generated: {len(result.alerts)}\n"
                summary_text += f"  Recommendations: {len(result.recommendations)}\n\n"
        
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary_text)
    
    def _update_metrics_display(self):
        """Update metrics display"""
        # Clear existing metrics
        for item in self.metrics_tree.get_children():
            self.metrics_tree.delete(item)
        
        # Add metrics from each domain
        for domain, result in self.analysis_results.items():
            if result.metrics:
                for metric_name, metric_value in result.metrics.items():
                    # Format metric value
                    if isinstance(metric_value, float):
                        formatted_value = f"{metric_value:.2f}"
                    else:
                        formatted_value = str(metric_value)
                    
                    # Determine status based on metric
                    status = self._get_metric_status(domain, metric_name, metric_value)
                    
                    self.metrics_tree.insert('', 'end', values=(
                        domain.value,
                        metric_name.replace('_', ' ').title(),
                        formatted_value,
                        status
                    ))
    
    def _get_metric_status(self, domain: AnalysisDomain, metric_name: str, value: Any) -> str:
        """Get status for a metric"""
        if domain == AnalysisDomain.SOLDIER_SAFETY:
            if metric_name == 'overall_safety_score':
                if value >= 80:
                    return "Good"
                elif value >= 60:
                    return "Fair"
                else:
                    return "Poor"
            elif metric_name == 'casualty_rate':
                if value <= 0.1:
                    return "Good"
                elif value <= 0.2:
                    return "Fair"
                else:
                    return "Poor"
        elif domain == AnalysisDomain.NETWORK_PERFORMANCE:
            if metric_name == 'overall_network_health':
                if value >= 80:
                    return "Good"
                elif value >= 60:
                    return "Fair"
                else:
                    return "Poor"
            elif metric_name == 'network_availability':
                if value >= 95:
                    return "Good"
                elif value >= 85:
                    return "Fair"
                else:
                    return "Poor"
        
        return "Unknown"
    
    def _update_detailed_results(self):
        """Update detailed results display"""
        selected_domain = self.detailed_domain_var.get()
        
        if not selected_domain:
            self.detailed_text.delete(1.0, tk.END)
            self.detailed_text.insert(tk.END, "Select a domain to view detailed results")
            return
        
        # Find the domain result
        domain_result = None
        for domain, result in self.analysis_results.items():
            if domain.value == selected_domain:
                domain_result = result
                break
        
        if not domain_result:
            self.detailed_text.delete(1.0, tk.END)
            self.detailed_text.insert(tk.END, f"No results available for {selected_domain}")
            return
        
        # Format detailed results
        detailed_text = f"Detailed Results - {selected_domain}\n"
        detailed_text += "=" * 60 + "\n\n"
        
        # Basic information
        detailed_text += f"Analysis Status: {domain_result.status}\n"
        detailed_text += f"Execution Time: {domain_result.execution_time:.2f} seconds\n"
        detailed_text += f"Data Quality Score: {domain_result.data_quality_score:.1f}%\n\n"
        
        # Metrics
        detailed_text += "METRICS:\n"
        detailed_text += "-" * 30 + "\n"
        if domain_result.metrics:
            for metric_name, metric_value in domain_result.metrics.items():
                detailed_text += f"{metric_name}: {metric_value}\n"
        else:
            detailed_text += "No metrics available\n"
        
        detailed_text += "\n"
        
        # Alerts
        detailed_text += "ALERTS:\n"
        detailed_text += "-" * 30 + "\n"
        if domain_result.alerts:
            for i, alert in enumerate(domain_result.alerts, 1):
                detailed_text += f"{i}. [{alert.level.value}] {alert.alert_type}\n"
                detailed_text += f"   Message: {alert.message}\n"
                if alert.affected_units:
                    detailed_text += f"   Affected Units: {', '.join(alert.affected_units)}\n"
                if alert.metric_value is not None:
                    detailed_text += f"   Metric Value: {alert.metric_value}\n"
                if alert.threshold is not None:
                    detailed_text += f"   Threshold: {alert.threshold}\n"
                detailed_text += "\n"
        else:
            detailed_text += "No alerts generated\n"
        
        detailed_text += "\n"
        
        # Recommendations
        detailed_text += "RECOMMENDATIONS:\n"
        detailed_text += "-" * 30 + "\n"
        if domain_result.recommendations:
            for i, rec in enumerate(domain_result.recommendations, 1):
                detailed_text += f"{i}. {rec}\n"
        else:
            detailed_text += "No recommendations available\n"
        
        self.detailed_text.delete(1.0, tk.END)
        self.detailed_text.insert(tk.END, detailed_text)
    
    def _update_recommendations(self):
        """Update recommendations display"""
        # Safety recommendations
        safety_recs = []
        if AnalysisDomain.SOLDIER_SAFETY in self.analysis_results:
            safety_recs = self.analysis_results[AnalysisDomain.SOLDIER_SAFETY].recommendations
        
        safety_text = "SOLDIER SAFETY RECOMMENDATIONS:\n"
        safety_text += "=" * 40 + "\n\n"
        
        if safety_recs:
            for i, rec in enumerate(safety_recs, 1):
                safety_text += f"{i}. {rec}\n\n"
        else:
            safety_text += "No safety recommendations available.\n"
        
        self.safety_rec_text.delete(1.0, tk.END)
        self.safety_rec_text.insert(tk.END, safety_text)
        
        # Network recommendations
        network_recs = []
        if AnalysisDomain.NETWORK_PERFORMANCE in self.analysis_results:
            network_recs = self.analysis_results[AnalysisDomain.NETWORK_PERFORMANCE].recommendations
        
        network_text = "NETWORK PERFORMANCE RECOMMENDATIONS:\n"
        network_text += "=" * 40 + "\n\n"
        
        if network_recs:
            for i, rec in enumerate(network_recs, 1):
                network_text += f"{i}. {rec}\n\n"
        else:
            network_text += "No network recommendations available.\n"
        
        self.network_rec_text.delete(1.0, tk.END)
        self.network_rec_text.insert(tk.END, network_text)
    
    def _update_raw_data(self):
        """Update raw data display"""
        display_type = self.raw_display_var.get()
        
        # Clear existing data
        for item in self.raw_tree.get_children():
            self.raw_tree.delete(item)
        
        if display_type == "Analysis Results":
            # Display analysis results in tabular format
            columns = ['Domain', 'Status', 'Execution Time', 'Data Quality', 'Alerts', 'Recommendations']
            self.raw_tree.configure(columns=columns)
            
            for col in columns:
                self.raw_tree.heading(col, text=col)
                self.raw_tree.column(col, width=120)
            
            for domain, result in self.analysis_results.items():
                self.raw_tree.insert('', 'end', values=(
                    domain.value,
                    result.status,
                    f"{result.execution_time:.2f}s",
                    f"{result.data_quality_score:.1f}%",
                    len(result.alerts),
                    len(result.recommendations)
                ))
        
        elif display_type == "Alert Details":
            # Display alert details
            columns = ['Level', 'Type', 'Message', 'Affected Units', 'Metric Value', 'Threshold']
            self.raw_tree.configure(columns=columns)
            
            for col in columns:
                self.raw_tree.heading(col, text=col)
                self.raw_tree.column(col, width=150)
            
            for alert in self.current_alerts:
                self.raw_tree.insert('', 'end', values=(
                    alert.level.value,
                    alert.alert_type,
                    alert.message[:100] + "..." if len(alert.message) > 100 else alert.message,
                    ', '.join(alert.affected_units) if alert.affected_units else 'N/A',
                    alert.metric_value if alert.metric_value is not None else 'N/A',
                    alert.threshold if alert.threshold is not None else 'N/A'
                ))
        
        elif display_type == "Metrics Only":
            # Display metrics only
            columns = ['Domain', 'Metric', 'Value', 'Type']
            self.raw_tree.configure(columns=columns)
            
            for col in columns:
                self.raw_tree.heading(col, text=col)
                self.raw_tree.column(col, width=150)
            
            for domain, result in self.analysis_results.items():
                if result.metrics:
                    for metric_name, metric_value in result.metrics.items():
                        self.raw_tree.insert('', 'end', values=(
                            domain.value,
                            metric_name,
                            metric_value,
                            type(metric_value).__name__
                        ))
    
    def _generate_visualization(self):
        """Generate visualization based on selected type"""
        viz_type = self.viz_type_var.get()
        
        # Clear existing visualization
        if self.viz_canvas:
            self.viz_canvas.destroy()
        
        # Create new figure
        self.viz_figure = plt.figure(figsize=(12, 8))
        
        if viz_type == "Summary Dashboard":
            self._create_summary_dashboard()
        elif viz_type == "Safety Metrics":
            self._create_safety_visualization()
        elif viz_type == "Network Performance":
            self._create_network_visualization()
        elif viz_type == "Alert Timeline":
            self._create_alert_timeline()
        elif viz_type == "Unit Comparison":
            self._create_unit_comparison()
        
        # Create canvas
        self.viz_canvas = FigureCanvasTkAgg(self.viz_figure, self.viz_frame)
        self.viz_canvas.draw()
        self.viz_canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def _create_summary_dashboard(self):
        """Create summary dashboard visualization"""
        if not self.analysis_results:
            ax = self.viz_figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No analysis results available', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=16)
            return
        
        # Create subplots
        gs = self.viz_figure.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Alert summary pie chart
        ax1 = self.viz_figure.add_subplot(gs[0, 0])
        if self.current_alerts:
            alert_counts = {}
            for alert in self.current_alerts:
                alert_counts[alert.level.value] = alert_counts.get(alert.level.value, 0) + 1
            
            colors = {'CRITICAL': '#ff4444', 'WARNING': '#ffaa00', 'INFO': '#44ff44'}
            ax1.pie(alert_counts.values(), labels=alert_counts.keys(), autopct='%1.1f%%',
                   colors=[colors.get(level, '#cccccc') for level in alert_counts.keys()])
            ax1.set_title('Alert Distribution')
        else:
            ax1.text(0.5, 0.5, 'No alerts', ha='center', va='center')
            ax1.set_title('Alert Distribution')
        
        # Domain completion status
        ax2 = self.viz_figure.add_subplot(gs[0, 1])
        domains = [domain.value for domain in self.analysis_results.keys()]
        statuses = [result.status for result in self.analysis_results.values()]
        
        status_colors = {'COMPLETED': '#44ff44', 'FAILED': '#ff4444', 'RUNNING': '#ffaa00'}
        bar_colors = [status_colors.get(status, '#cccccc') for status in statuses]
        
        ax2.bar(domains, [1] * len(domains), color=bar_colors)
        ax2.set_title('Domain Analysis Status')
        ax2.set_ylabel('Status')
        ax2.tick_params(axis='x', rotation=45)
        
        # Execution time comparison
        ax3 = self.viz_figure.add_subplot(gs[1, 0])
        exec_times = [result.execution_time for result in self.analysis_results.values()]
        ax3.bar(domains, exec_times)
        ax3.set_title('Execution Time by Domain')
        ax3.set_ylabel('Time (seconds)')
        ax3.tick_params(axis='x', rotation=45)
        
        # Data quality scores
        ax4 = self.viz_figure.add_subplot(gs[1, 1])
        quality_scores = [result.data_quality_score for result in self.analysis_results.values()]
        ax4.bar(domains, quality_scores)
        ax4.set_title('Data Quality Scores')
        ax4.set_ylabel('Quality Score (%)')
        ax4.tick_params(axis='x', rotation=45)
        ax4.set_ylim(0, 100)
    
    def _create_safety_visualization(self):
        """Create safety-specific visualization"""
        if AnalysisDomain.SOLDIER_SAFETY not in self.analysis_results:
            ax = self.viz_figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No safety analysis results available', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=16)
            return
        
        safety_result = self.analysis_results[AnalysisDomain.SOLDIER_SAFETY]
        
        # Create subplots for safety metrics
        gs = self.viz_figure.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Safety score gauge
        ax1 = self.viz_figure.add_subplot(gs[0, 0])
        safety_score = safety_result.metrics.get('overall_safety_score', 0)
        self._create_gauge_chart(ax1, safety_score, 'Safety Score', 0, 100)
        
        # Casualty rate
        ax2 = self.viz_figure.add_subplot(gs[0, 1])
        casualty_rate = safety_result.metrics.get('casualty_rate', 0) * 100
        self._create_gauge_chart(ax2, casualty_rate, 'Casualty Rate (%)', 0, 50)
        
        # Total falls
        ax3 = self.viz_figure.add_subplot(gs[1, 0])
        total_falls = safety_result.metrics.get('total_falls', 0)
        ax3.bar(['Total Falls'], [total_falls], color='#ff6666')
        ax3.set_title('Fall Detection Results')
        ax3.set_ylabel('Number of Falls')
        
        # High risk units
        ax4 = self.viz_figure.add_subplot(gs[1, 1])
        high_risk_units = safety_result.metrics.get('high_risk_units', 0)
        total_units = safety_result.metrics.get('total_units', 1)
        safe_units = total_units - high_risk_units
        
        ax4.pie([safe_units, high_risk_units], labels=['Safe Units', 'High Risk Units'], 
               autopct='%1.1f%%', colors=['#66ff66', '#ff6666'])
        ax4.set_title('Unit Risk Distribution')
    
    def _create_network_visualization(self):
        """Create network performance visualization"""
        if AnalysisDomain.NETWORK_PERFORMANCE not in self.analysis_results:
            ax = self.viz_figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No network analysis results available', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=16)
            return
        
        network_result = self.analysis_results[AnalysisDomain.NETWORK_PERFORMANCE]
        
        # Create subplots for network metrics
        gs = self.viz_figure.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Network health gauge
        ax1 = self.viz_figure.add_subplot(gs[0, 0])
        network_health = network_result.metrics.get('overall_network_health', 0)
        self._create_gauge_chart(ax1, network_health, 'Network Health', 0, 100)
        
        # Network availability
        ax2 = self.viz_figure.add_subplot(gs[0, 1])
        availability = network_result.metrics.get('network_availability', 0)
        self._create_gauge_chart(ax2, availability, 'Network Availability (%)', 0, 100)
        
        # Signal quality
        ax3 = self.viz_figure.add_subplot(gs[1, 0])
        signal_quality = network_result.metrics.get('signal_quality_score', 0)
        ax3.bar(['Signal Quality'], [signal_quality], color='#66b3ff')
        ax3.set_title('Signal Quality Score')
        ax3.set_ylabel('Quality Score')
        ax3.set_ylim(0, 100)
        
        # MCS efficiency
        ax4 = self.viz_figure.add_subplot(gs[1, 1])
        mcs_efficiency = network_result.metrics.get('mcs_efficiency_score', 0)
        ax4.bar(['MCS Efficiency'], [mcs_efficiency], color='#66ff99')
        ax4.set_title('MCS Efficiency Score')
        ax4.set_ylabel('Efficiency Score')
        ax4.set_ylim(0, 100)
    
    def _create_gauge_chart(self, ax, value, title, min_val, max_val):
        """Create a gauge chart"""
        # Create semicircle
        theta = np.linspace(0, np.pi, 100)
        x = np.cos(theta)
        y = np.sin(theta)
        
        # Background arc
        ax.plot(x, y, 'k-', linewidth=8, alpha=0.3)
        
        # Value arc
        value_theta = np.linspace(0, np.pi * (value - min_val) / (max_val - min_val), 100)
        value_x = np.cos(value_theta)
        value_y = np.sin(value_theta)
        
        # Color based on value
        if value >= 80:
            color = '#44ff44'
        elif value >= 60:
            color = '#ffaa00'
        else:
            color = '#ff4444'
        
        ax.plot(value_x, value_y, color=color, linewidth=8)
        
        # Add value text
        ax.text(0, -0.1, f'{value:.1f}', ha='center', va='center', fontsize=16, weight='bold')
        ax.text(0, -0.3, title, ha='center', va='center', fontsize=12)
        
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-0.5, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')
    
    def _create_alert_timeline(self):
        """Create alert timeline visualization"""
        if not self.current_alerts:
            ax = self.viz_figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No alerts to display', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=16)
            return
        
        ax = self.viz_figure.add_subplot(111)
        
        # Group alerts by type and level
        alert_data = {}
        for alert in self.current_alerts:
            key = f"{alert.alert_type} ({alert.level.value})"
            if key not in alert_data:
                alert_data[key] = []
            alert_data[key].append(alert)
        
        # Create timeline
        y_pos = 0
        colors = {'CRITICAL': '#ff4444', 'WARNING': '#ffaa00', 'INFO': '#44ff44'}
        
        for alert_type, alerts in alert_data.items():
            level = alerts[0].level.value
            color = colors.get(level, '#cccccc')
            
            # Plot alert as a point
            ax.scatter([0], [y_pos], c=color, s=100, alpha=0.7)
            ax.text(0.1, y_pos, f"{alert_type} ({len(alerts)})", va='center')
            
            y_pos += 1
        
        ax.set_xlim(-0.5, 2)
        ax.set_ylim(-0.5, y_pos + 0.5)
        ax.set_title('Alert Summary')
        ax.set_xlabel('Timeline')
        ax.grid(True, alpha=0.3)
    
    def _create_unit_comparison(self):
        """Create unit comparison visualization"""
        # This would require unit-specific data from analysis results
        ax = self.viz_figure.add_subplot(111)
        ax.text(0.5, 0.5, 'Unit comparison visualization\nrequires unit-specific analysis data', 
               horizontalalignment='center', verticalalignment='center',
               transform=ax.transAxes, fontsize=16)
    
    def _generate_action_plan(self):
        """Generate action plan based on analysis results"""
        if not self.analysis_results:
            action_text = "No analysis results available to generate action plan."
        else:
            action_text = "CONSOLIDATED ACTION PLAN\n"
            action_text += "=" * 40 + "\n\n"
            
            # Priority actions based on critical alerts
            critical_alerts = [alert for alert in self.current_alerts if alert.level == AlertLevel.CRITICAL]
            
            if critical_alerts:
                action_text += "IMMEDIATE ACTIONS (Critical Priority):\n"
                action_text += "-" * 30 + "\n"
                
                for i, alert in enumerate(critical_alerts, 1):
                    action_text += f"{i}. Address {alert.alert_type}: {alert.message}\n"
                    if alert.affected_units:
                        action_text += f"   Focus on units: {', '.join(alert.affected_units)}\n"
                    action_text += "\n"
            
            # Medium priority actions
            warning_alerts = [alert for alert in self.current_alerts if alert.level == AlertLevel.WARNING]
            
            if warning_alerts:
                action_text += "MEDIUM PRIORITY ACTIONS:\n"
                action_text += "-" * 30 + "\n"
                
                for i, alert in enumerate(warning_alerts, 1):
                    action_text += f"{i}. Monitor {alert.alert_type}: {alert.message}\n"
                    action_text += "\n"
            
            # Long-term recommendations
            action_text += "LONG-TERM IMPROVEMENTS:\n"
            action_text += "-" * 30 + "\n"
            
            all_recommendations = []
            for result in self.analysis_results.values():
                all_recommendations.extend(result.recommendations)
            
            for i, rec in enumerate(all_recommendations, 1):
                action_text += f"{i}. {rec}\n"
            
            if not all_recommendations:
                action_text += "Continue current operational procedures.\n"
        
        self.action_text.delete(1.0, tk.END)
        self.action_text.insert(tk.END, action_text)
    
    # Event handlers
    def _on_domain_selected(self, event):
        """Handle domain selection"""
        selection = self.domain_listbox.curselection()
        if selection:
            domain_name = self.domain_listbox.get(selection[0])
            self.selected_domain = domain_name
            self.detailed_domain_var.set(domain_name)
            self._update_detailed_results()
    
    def _on_detailed_domain_selected(self, event):
        """Handle detailed domain selection"""
        self._update_detailed_results()
    
    def _on_viz_type_selected(self, event):
        """Handle visualization type selection"""
        pass  # Visualization will be generated when user clicks Generate button
    
    def _on_raw_display_selected(self, event):
        """Handle raw display selection"""
        self._update_raw_data()
    
    def _on_history_selected(self, event):
        """Handle history selection"""
        selection = self.history_listbox.curselection()
        if selection:
            # Load historical results
            pass  # Implement if needed
    
    # Control methods
    def _clear_alerts(self):
        """Clear all alerts"""
        if messagebox.askyesno("Clear Alerts", "Clear all alerts?"):
            self.current_alerts.clear()
            self._update_alerts_display()
    
    def _export_alerts(self):
        """Export alerts to file"""
        if not self.current_alerts:
            messagebox.showwarning("Warning", "No alerts to export")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Alerts",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv")]
            )
            
            if filename:
                alert_data = []
                for alert in self.current_alerts:
                    alert_data.append({
                        'level': alert.level.value,
                        'type': alert.alert_type,
                        'message': alert.message,
                        'affected_units': alert.affected_units,
                        'metric_value': alert.metric_value,
                        'threshold': alert.threshold,
                        'timestamp': datetime.now().isoformat()
                    })
                
                if filename.endswith('.json'):
                    with open(filename, 'w') as f:
                        json.dump(alert_data, f, indent=2)
                elif filename.endswith('.csv'):
                    df = pd.DataFrame(alert_data)
                    df.to_csv(filename, index=False)
                
                messagebox.showinfo("Success", f"Alerts exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error exporting alerts: {str(e)}")
    
    def _clear_history(self):
        """Clear analysis history"""
        if messagebox.askyesno("Clear History", "Clear analysis history?"):
            self.result_history.clear()
            self.history_listbox.delete(0, tk.END)
    
    def _export_results(self):
        """Export analysis results"""
        if not self.analysis_results:
            messagebox.showwarning("Warning", "No results to export")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Results",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("Excel files", "*.xlsx")]
            )
            
            if filename:
                export_data = {
                    'timestamp': datetime.now().isoformat(),
                    'domains': {}
                }
                
                for domain, result in self.analysis_results.items():
                    export_data['domains'][domain.value] = {
                        'status': result.status,
                        'execution_time': result.execution_time,
                        'data_quality_score': result.data_quality_score,
                        'metrics': result.metrics,
                        'alerts': [
                            {
                                'level': alert.level.value,
                                'type': alert.alert_type,
                                'message': alert.message,
                                'affected_units': alert.affected_units,
                                'metric_value': alert.metric_value,
                                'threshold': alert.threshold
                            } for alert in result.alerts
                        ],
                        'recommendations': result.recommendations
                    }
                
                if filename.endswith('.json'):
                    with open(filename, 'w') as f:
                        json.dump(export_data, f, indent=2)
                elif filename.endswith('.xlsx'):
                    # Create multiple sheets for Excel export
                    with pd.ExcelWriter(filename) as writer:
                        # Summary sheet
                        summary_data = []
                        for domain, result in self.analysis_results.items():
                            summary_data.append({
                                'Domain': domain.value,
                                'Status': result.status,
                                'Execution Time': result.execution_time,
                                'Data Quality': result.data_quality_score,
                                'Alerts': len(result.alerts),
                                'Recommendations': len(result.recommendations)
                            })
                        
                        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                        
                        # Alerts sheet
                        alert_data = []
                        for domain, result in self.analysis_results.items():
                            for alert in result.alerts:
                                alert_data.append({
                                    'Domain': domain.value,
                                    'Level': alert.level.value,
                                    'Type': alert.alert_type,
                                    'Message': alert.message,
                                    'Affected Units': ', '.join(alert.affected_units) if alert.affected_units else '',
                                    'Metric Value': alert.metric_value,
                                    'Threshold': alert.threshold
                                })
                        
                        if alert_data:
                            pd.DataFrame(alert_data).to_excel(writer, sheet_name='Alerts', index=False)
                
                messagebox.showinfo("Success", f"Results exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error exporting results: {str(e)}")
    
    def _generate_report(self):
        """Generate comprehensive report"""
        if not self.analysis_results:
            messagebox.showwarning("Warning", "No results available for report generation")
            return
        
        # Publish report generation event
        self.event_bus.publish(Event(
            EventType.REPORT_REQUESTED,
            {
                'results': self.analysis_results,
                'alerts': self.current_alerts,
                'timestamp': datetime.now().isoformat()
            },
            source='ResultsTab'
        ))
        
        messagebox.showinfo("Report Generation", "Report generation request submitted")
    
    def _refresh_results(self):
        """Refresh all results displays"""
        self._update_domain_list()
        self._update_alerts_display()
        self._update_summary()
        self._update_metrics_display()
        self._update_detailed_results()
        self._update_recommendations()
        self._update_raw_data()
    
    def _refresh_detailed_results(self):
        """Refresh detailed results display"""
        self._update_detailed_results()
    
    def _export_visualization(self):
        """Export current visualization"""
        if not self.viz_figure:
            messagebox.showwarning("Warning", "No visualization to export")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Visualization",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("SVG files", "*.svg")]
            )
            
            if filename:
                self.viz_figure.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Visualization exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error exporting visualization: {str(e)}")
    
    def _export_raw_data(self):
        """Export raw data"""
        # Get current tree data
        tree_data = []
        for item in self.raw_tree.get_children():
            values = self.raw_tree.item(item)['values']
            tree_data.append(values)
        
        if not tree_data:
            messagebox.showwarning("Warning", "No data to export")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Raw Data",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
            )
            
            if filename:
                columns = [self.raw_tree.heading(col)['text'] for col in self.raw_tree['columns']]
                df = pd.DataFrame(tree_data, columns=columns)
                
                if filename.endswith('.csv'):
                    df.to_csv(filename, index=False)
                elif filename.endswith('.xlsx'):
                    df.to_excel(filename, index=False)
                
                messagebox.showinfo("Success", f"Raw data exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error exporting raw data: {str(e)}")
    
    # Event handlers
    def _on_analysis_completed(self, event: Event):
        """Handle analysis completion"""
        data = event.data
        if 'results' in data:
            result = data['results']
            if hasattr(result, 'domain'):
                self.analysis_results[result.domain] = result
                
                # Add to history
                self.result_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'domain': result.domain.value,
                    'status': result.status
                })
                
                # Update history listbox
                self.history_listbox.insert(0, f"{datetime.now().strftime('%H:%M:%S')} - {result.domain.value}")
                
                # Refresh displays
                self._refresh_results()
    
    def _on_alert_triggered(self, event: Event):
        """Handle alert events"""
        data = event.data
        if 'alert' in data:
            alert = data['alert']
            if isinstance(alert, Alert):
                self.current_alerts.append(alert)
                self._update_alerts_display()
    
    def _on_analysis_progress(self, event: Event):
        """Handle analysis progress updates"""
        # Could show progress in results tab if needed
        pass
    
    def update_results(self, results_data: Dict[str, Any]):
        """Update results from external source"""
        if 'results' in results_data:
            result = results_data['results']
            if hasattr(result, 'domain'):
                self.analysis_results[result.domain] = result
                self._refresh_results()
    
    def clear_results(self):
        """Clear all results"""
        if messagebox.askyesno("Clear Results", "Clear all analysis results?"):
            self.analysis_results.clear()
            self.current_alerts.clear()
            self._refresh_results()