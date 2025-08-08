# ui/components/analysis_control_tab.py - Analysis Control Tab Implementation
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from core.event_bus import EventBus, Event, EventType
from core.models import (
    AnalysisDomain, AnalysisLevel, TaskPriority, TaskStatus,
    create_analysis_task, AnalysisTask
)

class AnalysisControlTab:
    """Analysis control and monitoring tab"""
    
    def __init__(self, parent, event_bus: EventBus, main_app):
        self.parent = parent
        self.event_bus = event_bus
        self.main_app = main_app
        self.logger = logging.getLogger(__name__)
        
        # Analysis state
        self.active_tasks: Dict[str, AnalysisTask] = {}
        self.completed_tasks: Dict[str, AnalysisTask] = {}
        
        # Create UI
        self._create_ui()
        
        # Setup event subscriptions
        self._setup_event_subscriptions()
        
        self.logger.info("AnalysisControlTab initialized")
    
    def _create_ui(self):
        """Create the analysis control UI"""
        # Main frame
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create sections
        self._create_analysis_status_section(main_frame)
        self._create_task_queue_section(main_frame)
        self._create_analysis_controls_section(main_frame)
        
        # Store main frame reference
        self.frame = main_frame
        
        # Initial update
        self._update_displays()
    
    def _create_analysis_status_section(self, parent):
        """Create analysis status section"""
        status_frame = ttk.LabelFrame(parent, text="Analysis Status", padding="10")
        status_frame.pack(fill='x', pady=(0, 10))
        
        # Status grid
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill='x')
        
        # System status
        ttk.Label(status_grid, text="System Status:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.system_status_var = tk.StringVar(value="Ready")
        self.system_status_label = ttk.Label(status_grid, textvariable=self.system_status_var, 
                                            foreground="green")
        self.system_status_label.grid(row=0, column=1, sticky='w', padx=(0, 20))
        
        # Active tasks
        ttk.Label(status_grid, text="Active Tasks:").grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.active_tasks_var = tk.StringVar(value="0")
        ttk.Label(status_grid, textvariable=self.active_tasks_var).grid(row=0, column=3, sticky='w', padx=(0, 20))
        
        # Completed tasks
        ttk.Label(status_grid, text="Completed:").grid(row=0, column=4, sticky='w', padx=(0, 10))
        self.completed_tasks_var = tk.StringVar(value="0")
        ttk.Label(status_grid, textvariable=self.completed_tasks_var).grid(row=0, column=5, sticky='w', padx=(0, 20))
        
        # Progress bar for current analysis
        progress_frame = ttk.Frame(status_frame)
        progress_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(progress_frame, text="Current Analysis Progress:").pack(anchor='w')
        self.analysis_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.analysis_progress.pack(fill='x', pady=(5, 0))
        
        # Current task info
        self.current_task_var = tk.StringVar(value="No active analysis")
        ttk.Label(progress_frame, textvariable=self.current_task_var).pack(anchor='w', pady=(5, 0))
    
    def _create_task_queue_section(self, parent):
        """Create task queue section"""
        queue_frame = ttk.LabelFrame(parent, text="Task Queue", padding="10")
        queue_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Task queue treeview
        tree_frame = ttk.Frame(queue_frame)
        tree_frame.pack(fill='both', expand=True)
        
        # Create treeview
        columns = ('Task ID', 'Domain', 'Level', 'Priority', 'Status', 'Created', 'Progress')
        self.task_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        self.task_tree.heading('Task ID', text='Task ID')
        self.task_tree.heading('Domain', text='Domain')
        self.task_tree.heading('Level', text='Level')
        self.task_tree.heading('Priority', text='Priority')
        self.task_tree.heading('Status', text='Status')
        self.task_tree.heading('Created', text='Created')
        self.task_tree.heading('Progress', text='Progress')
        
        # Configure column widths
        self.task_tree.column('Task ID', width=100)
        self.task_tree.column('Domain', width=150)
        self.task_tree.column('Level', width=100)
        self.task_tree.column('Priority', width=80)
        self.task_tree.column('Status', width=100)
        self.task_tree.column('Created', width=120)
        self.task_tree.column('Progress', width=80)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.task_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Task controls
        task_controls = ttk.Frame(queue_frame)
        task_controls.pack(fill='x', pady=(10, 0))
        
        ttk.Button(task_controls, text="Cancel Selected", command=self._cancel_selected_task).pack(side='left')
        ttk.Button(task_controls, text="Retry Failed", command=self._retry_failed_tasks).pack(side='left', padx=(5, 0))
        ttk.Button(task_controls, text="Clear Completed", command=self._clear_completed_tasks).pack(side='left', padx=(5, 0))
        ttk.Button(task_controls, text="Refresh", command=self._refresh_task_queue).pack(side='right')
    
    def _create_analysis_controls_section(self, parent):
        """Create analysis controls section"""
        controls_frame = ttk.LabelFrame(parent, text="Analysis Controls", padding="10")
        controls_frame.pack(fill='x')
        
        # Quick analysis section
        quick_frame = ttk.Frame(controls_frame)
        quick_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(quick_frame, text="Quick Analysis:").pack(side='left')
        
        # Quick analysis buttons
        self.quick_safety_btn = ttk.Button(quick_frame, text="Safety Analysis", 
                                          command=lambda: self._quick_analysis(AnalysisDomain.SOLDIER_SAFETY))
        self.quick_safety_btn.pack(side='left', padx=(10, 5))
        
        self.quick_network_btn = ttk.Button(quick_frame, text="Network Analysis", 
                                           command=lambda: self._quick_analysis(AnalysisDomain.NETWORK_PERFORMANCE))
        self.quick_network_btn.pack(side='left', padx=(0, 5))
        
        self.quick_activity_btn = ttk.Button(quick_frame, text="Activity Analysis", 
                                            command=lambda: self._quick_analysis(AnalysisDomain.SOLDIER_ACTIVITY))
        self.quick_activity_btn.pack(side='left', padx=(0, 5))
        
        # Batch analysis section
        batch_frame = ttk.Frame(controls_frame)
        batch_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(batch_frame, text="Batch Analysis:").pack(side='left')
        
        self.batch_all_btn = ttk.Button(batch_frame, text="Analyze All Domains", 
                                       command=self._batch_analysis_all)
        self.batch_all_btn.pack(side='left', padx=(10, 5))
        
        self.batch_selected_btn = ttk.Button(batch_frame, text="Analyze Selected Domains", 
                                            command=self._batch_analysis_selected)
        self.batch_selected_btn.pack(side='left', padx=(0, 5))
        
        # System controls
        system_frame = ttk.Frame(controls_frame)
        system_frame.pack(fill='x')
        
        ttk.Label(system_frame, text="System Controls:").pack(side='left')
        
        self.pause_btn = ttk.Button(system_frame, text="Pause Analysis", 
                                   command=self._pause_analysis)
        self.pause_btn.pack(side='left', padx=(10, 5))
        
        self.resume_btn = ttk.Button(system_frame, text="Resume Analysis", 
                                    command=self._resume_analysis, state='disabled')
        self.resume_btn.pack(side='left', padx=(0, 5))
        
        self.stop_all_btn = ttk.Button(system_frame, text="Stop All", 
                                      command=self._stop_all_analysis)
        self.stop_all_btn.pack(side='left', padx=(0, 5))
    
    def _setup_event_subscriptions(self):
        """Setup event subscriptions"""
        self.event_bus.subscribe(EventType.ANALYSIS_STARTED, self._on_analysis_started)
        self.event_bus.subscribe(EventType.ANALYSIS_COMPLETED, self._on_analysis_completed)
        self.event_bus.subscribe(EventType.ANALYSIS_FAILED, self._on_analysis_failed)
        self.event_bus.subscribe(EventType.ANALYSIS_PROGRESS, self._on_analysis_progress)
    
    def _update_displays(self):
        """Update all displays"""
        # Update status
        active_count = len(self.active_tasks)
        completed_count = len(self.completed_tasks)
        
        self.active_tasks_var.set(str(active_count))
        self.completed_tasks_var.set(str(completed_count))
        
        # Update system status
        if active_count > 0:
            self.system_status_var.set("Running")
            self.system_status_label.config(foreground="blue")
            self.analysis_progress.start()
        else:
            self.system_status_var.set("Ready")
            self.system_status_label.config(foreground="green")
            self.analysis_progress.stop()
        
        # Update task queue
        self._update_task_queue()
        
        # Update button states
        self._update_button_states()
    
    def _update_task_queue(self):
        """Update task queue display"""
        # Clear existing items
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Add active tasks
        for task in self.active_tasks.values():
            self.task_tree.insert('', 'end', values=(
                task.task_id[:8] + "...",
                task.domain.value,
                task.analysis_level.value,
                task.priority.value,
                task.status.value,
                task.created_at.strftime('%H:%M:%S'),
                "Running..." if task.status == TaskStatus.RUNNING else "Queued"
            ))
        
        # Add completed tasks (last 20)
        for task in list(self.completed_tasks.values())[-20:]:
            self.task_tree.insert('', 'end', values=(
                task.task_id[:8] + "...",
                task.domain.value,
                task.analysis_level.value,
                task.priority.value,
                task.status.value,
                task.created_at.strftime('%H:%M:%S'),
                "Complete" if task.status == TaskStatus.COMPLETED else "Failed"
            ))
    
    def _update_button_states(self):
        """Update button states based on system status"""
        has_data = self.main_app.current_data is not None
        
        # Enable/disable analysis buttons based on data availability
        self.quick_safety_btn.config(state='normal' if has_data else 'disabled')
        self.quick_network_btn.config(state='normal' if has_data else 'disabled')
        self.quick_activity_btn.config(state='normal' if has_data else 'disabled')
        self.batch_all_btn.config(state='normal' if has_data else 'disabled')
        self.batch_selected_btn.config(state='normal' if has_data else 'disabled')
    
    def _quick_analysis(self, domain: AnalysisDomain):
        """Start quick analysis for a domain"""
        if not self.main_app.current_data is not None:
            messagebox.showerror("Error", "Please load data first")
            return
        
        # Create analysis task
        task = create_analysis_task(
            domain=domain,
            level=AnalysisLevel.INDIVIDUAL,
            priority=TaskPriority.HIGH,
            config={
                'quick_analysis': True,
                'data_source': 'ui_selection'
            }
        )
        
        # Submit task
        self._submit_task(task)
        
        messagebox.showinfo("Analysis Started", f"Quick {domain.value} analysis started")
    
    def _batch_analysis_all(self):
        """Start batch analysis for all domains"""
        if not self.main_app.current_data is not None:
            messagebox.showerror("Error", "Please load data first")
            return
        
        domains = [
            AnalysisDomain.SOLDIER_SAFETY,
            AnalysisDomain.NETWORK_PERFORMANCE,
            AnalysisDomain.SOLDIER_ACTIVITY,
            AnalysisDomain.EQUIPMENT_MANAGEMENT
        ]
        
        for domain in domains:
            task = create_analysis_task(
                domain=domain,
                level=AnalysisLevel.INDIVIDUAL,
                priority=TaskPriority.NORMAL,
                config={'batch_analysis': True}
            )
            self._submit_task(task)
        
        messagebox.showinfo("Batch Analysis Started", f"Started analysis for {len(domains)} domains")
    
    def _batch_analysis_selected(self):
        """Start batch analysis for selected domains"""
        if not self.main_app.current_data is not None:
            messagebox.showerror("Error", "Please load data first")
            return
        
        # Get selected domains from domain tab
        selected_domains = getattr(self.main_app, 'selected_domains', [])
        
        if not selected_domains:
            messagebox.showwarning("Warning", "Please select domains in the Analysis Domains tab")
            return
        
        for domain in selected_domains:
            task = create_analysis_task(
                domain=domain,
                level=AnalysisLevel.INDIVIDUAL,
                priority=TaskPriority.NORMAL,
                config={'batch_analysis': True}
            )
            self._submit_task(task)
        
        messagebox.showinfo("Batch Analysis Started", f"Started analysis for {len(selected_domains)} domains")
    
    def _submit_task(self, task: AnalysisTask):
        """Submit a task for analysis"""
        try:
            # Add to active tasks
            self.active_tasks[task.task_id] = task
            
            # Submit to orchestrator if available
            if hasattr(self.main_app, 'orchestrator'):
                self.main_app.orchestrator.submit_task(task)
            
            # Update displays
            self._update_displays()
            
        except Exception as e:
            self.logger.error(f"Error submitting task: {e}")
            messagebox.showerror("Error", f"Failed to submit task: {str(e)}")
    
    def _cancel_selected_task(self):
        """Cancel selected task"""
        selected_items = self.task_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select a task to cancel")
            return
        
        # Get task ID from selection
        item = selected_items[0]
        task_id_short = self.task_tree.item(item)['values'][0]
        
        # Find full task ID
        task_id = None
        for tid in self.active_tasks.keys():
            if tid.startswith(task_id_short.replace("...", "")):
                task_id = tid
                break
        
        if task_id and task_id in self.active_tasks:
            # Cancel task
            task = self.active_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            
            # Move to completed
            self.completed_tasks[task_id] = task
            del self.active_tasks[task_id]
            
            # Update displays
            self._update_displays()
            
            messagebox.showinfo("Task Cancelled", f"Task {task_id_short} cancelled")
    
    def _retry_failed_tasks(self):
        """Retry failed tasks"""
        failed_tasks = [task for task in self.completed_tasks.values() if task.status == TaskStatus.FAILED]
        
        if not failed_tasks:
            messagebox.showinfo("No Failed Tasks", "No failed tasks to retry")
            return
        
        for task in failed_tasks:
            # Reset task
            task.status = TaskStatus.QUEUED
            task.error = None
            
            # Move back to active
            self.active_tasks[task.task_id] = task
            del self.completed_tasks[task.task_id]
        
        self._update_displays()
        messagebox.showinfo("Tasks Retried", f"Retried {len(failed_tasks)} failed tasks")
    
    def _clear_completed_tasks(self):
        """Clear completed tasks"""
        if not self.completed_tasks:
            messagebox.showinfo("No Completed Tasks", "No completed tasks to clear")
            return
        
        count = len(self.completed_tasks)
        self.completed_tasks.clear()
        self._update_displays()
        messagebox.showinfo("Tasks Cleared", f"Cleared {count} completed tasks")
    
    def _refresh_task_queue(self):
        """Refresh task queue display"""
        self._update_displays()
    
    def _pause_analysis(self):
        """Pause analysis"""
        # Pause orchestrator if available
        if hasattr(self.main_app, 'orchestrator'):
            self.main_app.orchestrator.pause()
        
        self.pause_btn.config(state='disabled')
        self.resume_btn.config(state='normal')
        
        messagebox.showinfo("Analysis Paused", "Analysis has been paused")
    
    def _resume_analysis(self):
        """Resume analysis"""
        # Resume orchestrator if available
        if hasattr(self.main_app, 'orchestrator'):
            self.main_app.orchestrator.resume()
        
        self.pause_btn.config(state='normal')
        self.resume_btn.config(state='disabled')
        
        messagebox.showinfo("Analysis Resumed", "Analysis has been resumed")
    
    def _stop_all_analysis(self):
        """Stop all analysis"""
        if not messagebox.askyesno("Stop All Analysis", "Are you sure you want to stop all analysis?"):
            return
        
        # Stop orchestrator if available
        if hasattr(self.main_app, 'orchestrator'):
            self.main_app.orchestrator.stop()
        
        # Cancel all active tasks
        for task in self.active_tasks.values():
            task.status = TaskStatus.CANCELLED
        
        # Move all active tasks to completed
        self.completed_tasks.update(self.active_tasks)
        self.active_tasks.clear()
        
        self._update_displays()
        
        messagebox.showinfo("Analysis Stopped", "All analysis has been stopped")
    
    def _on_analysis_started(self, event):
        """Handle analysis started event"""
        task_id = event.data.get('task_id')
        if task_id in self.active_tasks:
            self.active_tasks[task_id].status = TaskStatus.RUNNING
            self.active_tasks[task_id].started_at = datetime.now()
            self._update_displays()
    
    def _on_analysis_completed(self, event):
        """Handle analysis completed event"""
        task_id = event.data.get('task_id')
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            # Move to completed
            self.completed_tasks[task_id] = task
            del self.active_tasks[task_id]
            
            self._update_displays()
    
    def _on_analysis_failed(self, event):
        """Handle analysis failed event"""
        task_id = event.data.get('task_id')
        error = event.data.get('error', 'Unknown error')
        
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = datetime.now()
            
            # Move to completed
            self.completed_tasks[task_id] = task
            del self.active_tasks[task_id]
            
            self._update_displays()
    
    def _on_analysis_progress(self, event):
        """Handle analysis progress event"""
        task_id = event.data.get('task_id')
        progress = event.data.get('progress', 0)
        
        if task_id in self.active_tasks:
            # Update current task display
            task = self.active_tasks[task_id]
            self.current_task_var.set(f"Running: {task.domain.value} - {progress}%")
    
    # Methods for external access
    def get_active_tasks(self) -> Dict[str, AnalysisTask]:
        """Get active tasks"""
        return self.active_tasks.copy()
    
    def get_completed_tasks(self) -> Dict[str, AnalysisTask]:
        """Get completed tasks"""
        return self.completed_tasks.copy()
    
    def submit_external_task(self, task: AnalysisTask):
        """Submit task from external source"""
        self._submit_task(task)
