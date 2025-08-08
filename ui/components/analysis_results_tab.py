"""
Fixed Analysis Results Tab Component
Handles both enum and string domain values properly
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pandas as pd
from typing import Dict, List, Any, Optional, Callable
import json
from datetime import datetime

try:
    from core.models import AnalysisDomain, AnalysisResult, AlertLevel
except ImportError:
    # Fallback if core models not available
    AnalysisDomain = None
    AnalysisResult = None
    AlertLevel = None


class AnalysisResultsTab(ttk.Frame):
    """Tab for displaying and managing analysis results"""
    
    def __init__(self, parent, event_bus, get_results_callback: Callable):
        super().__init__(parent)
        self.event_bus = event_bus
        self.get_results_callback = get_results_callback
        
        self.current_results: Dict[Any, Any] = {}
        
        self._setup_ui()
        self._setup_event_handlers()

    def _setup_ui(self):
        """Setup the UI components"""
        
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Analysis Results", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="Refresh Results", 
                  command=self.refresh_results).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="Export Results", 
                  command=self.export_results).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="Clear Results", 
                  command=self.clear_results).pack(side=tk.LEFT)
        
        # Results notebook
        self.results_notebook = ttk.Notebook(main_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs for different views
        self._create_overview_tab()
        self._create_alerts_tab()
        self._create_recommendations_tab()

    def _create_overview_tab(self):
        """Create overview tab with summary of all results"""
        
        overview_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(overview_frame, text="Overview")
        
        # Summary section
        summary_frame = ttk.LabelFrame(overview_frame, text="Analysis Summary")
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, height=6, width=80)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Domain status section
        status_frame = ttk.LabelFrame(overview_frame, text="Domain Status")
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create treeview for domain status
        columns = ('Domain', 'Status', 'Alerts', 'Recommendations', 'Confidence', 'Timestamp')
        self.status_tree = ttk.Treeview(status_frame, columns=columns, show='headings')
        
        for col in columns:
            self.status_tree.heading(col, text=col)
            self.status_tree.column(col, width=120)
        
        # Scrollbar for treeview
        status_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_tree.yview)
        self.status_tree.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

    def _create_alerts_tab(self):
        """Create alerts tab showing all alerts from all domains"""
        
        alerts_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(alerts_frame, text="Alerts")
        
        # Alert summary
        alert_summary_frame = ttk.Frame(alerts_frame)
        alert_summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.alert_summary_label = ttk.Label(alert_summary_frame, text="No alerts available")
        self.alert_summary_label.pack()
        
        # Alert list
        alert_list_frame = ttk.LabelFrame(alerts_frame, text="All Alerts")
        alert_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create treeview for alerts
        alert_columns = ('Level', 'Domain', 'Message', 'Timestamp')
        self.alert_tree = ttk.Treeview(alert_list_frame, columns=alert_columns, show='headings')
        
        for col in alert_columns:
            self.alert_tree.heading(col, text=col)
        
        self.alert_tree.column('Level', width=80)
        self.alert_tree.column('Domain', width=100)
        self.alert_tree.column('Message', width=400)
        self.alert_tree.column('Timestamp', width=150)
        
        # Alert scrollbar
        alert_scrollbar = ttk.Scrollbar(alert_list_frame, orient=tk.VERTICAL, command=self.alert_tree.yview)
        self.alert_tree.configure(yscrollcommand=alert_scrollbar.set)
        
        self.alert_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        alert_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

    def _create_recommendations_tab(self):
        """Create recommendations tab showing all recommendations"""
        
        rec_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(rec_frame, text="Recommendations")
        
        # All recommendations view
        all_rec_frame = ttk.LabelFrame(rec_frame, text="All Recommendations")
        all_rec_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.all_rec_text = scrolledtext.ScrolledText(all_rec_frame, height=20, width=80)
        self.all_rec_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _setup_event_handlers(self):
        """Setup event handlers"""
        
        def handle_analysis_completed(event_data):
            """Handle analysis completion"""
            self.after(0, self.refresh_results)
        
        self.event_bus.subscribe('analysis_completed', handle_analysis_completed)
        self.event_bus.subscribe('task_completed', handle_analysis_completed)

    def refresh_results(self):
        """Refresh the results display"""
        
        try:
            # Get current results
            self.current_results = self.get_results_callback()
            
            # Update all displays
            self._update_overview()
            self._update_alerts()
            self._update_recommendations()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh results: {str(e)}")

    def _update_overview(self):
        """Update the overview tab"""
        
        # Update summary text
        summary = self._generate_summary()
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary)
        
        # Update status tree
        for item in self.status_tree.get_children():
            self.status_tree.delete(item)
        
        for domain, result in self.current_results.items():
            # Handle both enum and string domain values
            domain_name = self._get_domain_name(domain)
            
            status = "Completed"
            alerts_count = len(result.alerts) if result and hasattr(result, 'alerts') else 0
            rec_count = len(result.recommendations) if result and hasattr(result, 'recommendations') else 0
            confidence = f"{result.confidence_score:.2f}" if result and hasattr(result, 'confidence_score') else "N/A"
            timestamp = result.analysis_timestamp.strftime("%H:%M:%S") if result and hasattr(result, 'analysis_timestamp') else "N/A"
            
            self.status_tree.insert('', tk.END, values=(
                domain_name,
                status,
                alerts_count,
                rec_count,
                confidence,
                timestamp
            ))

    def _update_alerts(self):
        """Update the alerts display"""
        
        # Clear existing alerts
        for item in self.alert_tree.get_children():
            self.alert_tree.delete(item)
        
        # Collect all alerts
        all_alerts = []
        for domain, result in self.current_results.items():
            if result and hasattr(result, 'alerts') and result.alerts:
                domain_name = self._get_domain_name(domain)
                for alert in result.alerts:
                    all_alerts.append((domain_name, alert))
        
        # Sort by alert level if possible
        try:
            if AlertLevel:
                level_order = {AlertLevel.CRITICAL: 0, AlertLevel.HIGH: 1, 
                              AlertLevel.MEDIUM: 2, AlertLevel.LOW: 3}
                all_alerts.sort(key=lambda x: level_order.get(x[1].level, 4))
        except:
            pass  # If AlertLevel not available, don't sort
        
        # Add to tree
        for domain_name, alert in all_alerts:
            level_str = self._get_alert_level_string(alert)
            message = getattr(alert, 'message', str(alert))
            timestamp = getattr(alert, 'timestamp', datetime.now()).strftime("%H:%M:%S")
            
            self.alert_tree.insert('', tk.END, values=(
                level_str,
                domain_name,
                message,
                timestamp
            ))
        
        # Update summary
        alert_count = len(all_alerts)
        try:
            critical_count = sum(1 for _, alert in all_alerts 
                               if hasattr(alert, 'level') and 
                               (alert.level == AlertLevel.CRITICAL if AlertLevel else 
                                getattr(alert.level, 'value', str(alert.level)).lower() == 'critical'))
        except:
            critical_count = 0
        
        summary = f"Total Alerts: {alert_count}"
        if critical_count > 0:
            summary += f" (Critical: {critical_count})"
        
        self.alert_summary_label.config(text=summary)

    def _update_recommendations(self):
        """Update the recommendations display"""
        
        # Clear existing recommendations
        self.all_rec_text.delete(1.0, tk.END)
        
        # Collect all recommendations
        all_recommendations = ""
        
        for domain, result in self.current_results.items():
            if result and hasattr(result, 'recommendations') and result.recommendations:
                domain_name = self._get_domain_name(domain)
                all_recommendations += f"\n{domain_name.upper()} DOMAIN RECOMMENDATIONS:\n"
                all_recommendations += "=" * 50 + "\n"
                
                for i, rec in enumerate(result.recommendations, 1):
                    all_recommendations += f"{i}. {rec}\n"
                
                all_recommendations += "\n"
        
        if not all_recommendations:
            all_recommendations = "No recommendations available.\nRun analysis to generate recommendations."
        
        self.all_rec_text.insert(1.0, all_recommendations)

    def _generate_summary(self):
        """Generate summary text"""
        
        if not self.current_results:
            return "No analysis results available.\nLoad data and run analysis to see results."
        
        summary = f"ANALYSIS SUMMARY\n"
        summary += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary += "=" * 50 + "\n\n"
        
        # Domain summary
        summary += f"Domains Analyzed: {len(self.current_results)}\n"
        
        # Alert summary
        total_alerts = 0
        critical_alerts = 0
        
        for result in self.current_results.values():
            if result and hasattr(result, 'alerts'):
                total_alerts += len(result.alerts)
                try:
                    if AlertLevel:
                        critical_alerts += sum(1 for alert in result.alerts 
                                             if hasattr(alert, 'level') and alert.level == AlertLevel.CRITICAL)
                    else:
                        critical_alerts += sum(1 for alert in result.alerts 
                                             if hasattr(alert, 'level') and 
                                             getattr(alert.level, 'value', str(alert.level)).lower() == 'critical')
                except:
                    pass
        
        summary += f"Total Alerts: {total_alerts}\n"
        if critical_alerts > 0:
            summary += f"Critical Alerts: {critical_alerts}\n"
        
        # Recommendation summary
        total_recs = sum(len(result.recommendations) for result in self.current_results.values() 
                        if result and hasattr(result, 'recommendations'))
        summary += f"Total Recommendations: {total_recs}\n\n"
        
        # Domain details
        for domain, result in self.current_results.items():
            if result:
                domain_name = self._get_domain_name(domain)
                summary += f"{domain_name.upper()}:\n"
                
                if hasattr(result, 'confidence_score'):
                    summary += f"  Confidence: {result.confidence_score:.2f}\n"
                if hasattr(result, 'alerts'):
                    summary += f"  Alerts: {len(result.alerts)}\n"
                if hasattr(result, 'recommendations'):
                    summary += f"  Recommendations: {len(result.recommendations)}\n"
                if hasattr(result, 'analysis_timestamp'):
                    summary += f"  Timestamp: {result.analysis_timestamp.strftime('%H:%M:%S')}\n"
                summary += "\n"
        
        return summary

    def _get_domain_name(self, domain) -> str:
        """Get domain name, handling both enum and string values"""
        
        if hasattr(domain, 'value'):
            return domain.value.title()
        elif hasattr(domain, 'name'):
            return domain.name.title()
        else:
            return str(domain).title()

    def _get_alert_level_string(self, alert) -> str:
        """Get alert level as string, handling different formats"""
        
        try:
            if hasattr(alert, 'level'):
                level = alert.level
                if hasattr(level, 'value'):
                    return level.value.upper()
                else:
                    return str(level).upper()
            else:
                return "UNKNOWN"
        except:
            return "UNKNOWN"

    def export_results(self):
        """Export current results"""
        
        if not self.current_results:
            messagebox.showwarning("No Results", "No results available to export.")
            return
        
        try:
            from tkinter import filedialog
            
            file_path = filedialog.asksaveasfilename(
                title="Export Analysis Results",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if file_path:
                # Prepare export data
                export_data = {}
                for domain, result in self.current_results.items():
                    domain_name = self._get_domain_name(domain)
                    
                    result_data = {
                        'domain': domain_name,
                        'confidence_score': getattr(result, 'confidence_score', 0),
                        'analysis_timestamp': getattr(result, 'analysis_timestamp', datetime.now()).isoformat()
                    }
                    
                    # Handle alerts
                    if hasattr(result, 'alerts'):
                        result_data['alerts'] = []
                        for alert in result.alerts:
                            alert_data = {
                                'level': self._get_alert_level_string(alert),
                                'message': getattr(alert, 'message', str(alert)),
                                'timestamp': getattr(alert, 'timestamp', datetime.now()).isoformat()
                            }
                            if hasattr(alert, 'details'):
                                alert_data['details'] = alert.details
                            result_data['alerts'].append(alert_data)
                    
                    # Handle recommendations
                    if hasattr(result, 'recommendations'):
                        result_data['recommendations'] = result.recommendations
                    
                    # Handle metrics
                    if hasattr(result, 'metrics'):
                        result_data['metrics'] = result.metrics
                    
                    export_data[domain_name] = result_data
                
                if file_path.endswith('.json'):
                    with open(file_path, 'w') as f:
                        json.dump(export_data, f, indent=2, default=str)
                else:
                    # Export as text
                    with open(file_path, 'w') as f:
                        f.write(self._generate_summary())
                        f.write("\n\nDETAILED RESULTS:\n")
                        f.write("=" * 50 + "\n")
                        
                        for domain, result in self.current_results.items():
                            domain_name = self._get_domain_name(domain)
                            f.write(f"\n{domain_name.upper()} DOMAIN:\n")
                            f.write("-" * 30 + "\n")
                            
                            if hasattr(result, 'confidence_score'):
                                f.write(f"Confidence: {result.confidence_score:.2f}\n")
                            if hasattr(result, 'analysis_timestamp'):
                                f.write(f"Timestamp: {result.analysis_timestamp}\n\n")
                            
                            if hasattr(result, 'alerts') and result.alerts:
                                f.write("ALERTS:\n")
                                for alert in result.alerts:
                                    level_str = self._get_alert_level_string(alert)
                                    message = getattr(alert, 'message', str(alert))
                                    f.write(f"  • [{level_str}] {message}\n")
                                f.write("\n")
                            
                            if hasattr(result, 'recommendations') and result.recommendations:
                                f.write("RECOMMENDATIONS:\n")
                                for i, rec in enumerate(result.recommendations, 1):
                                    f.write(f"{i}. {rec}\n")
                            f.write("\n")
                
                messagebox.showinfo("Export Complete", f"Results exported to {file_path}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")

    def clear_results(self):
        """Clear all results"""
        
        if messagebox.askyesno("Clear Results", "Clear all analysis results?"):
            self.current_results.clear()
            
            # Clear all displays
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(1.0, "No results available.")
            
            for item in self.status_tree.get_children():
                self.status_tree.delete(item)
            
            for item in self.alert_tree.get_children():
                self.alert_tree.delete(item)
            
            self.all_rec_text.delete(1.0, tk.END)
            self.all_rec_text.insert(1.0, "No recommendations available.")
            
            self.alert_summary_label.config(text="No alerts available")