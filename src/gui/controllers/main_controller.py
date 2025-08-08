#!/usr/bin/env python3
"""
Main GUI Controller for Enhanced Individual Soldier Report System
Handles primary user interface coordination and event orchestration
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import os
import sys

# Import core system components (would be actual imports in real implementation)
from event_bus import EventBus, EventType
from events import (
    Event, FileSelectedEvent, DataLoadedEvent, AnalysisCompletedEvent,
    StatusUpdateEvent, ErrorEvent
)
from exceptions import SoldierReportSystemError, DataLoadError
from analysis_engine import AnalysisEngine
from data_loader import DataLoader
from report_generator import ReportGenerator


@dataclass
class UIState:
    """Current state of the user interface"""
    file_loaded: bool = False
    analysis_complete: bool = False
    selected_soldiers: List[str] = None
    current_dataset = None
    
    def __post_init__(self):
        if self.selected_soldiers is None:
            self.selected_soldiers = []


class MainController:
    """
    Main GUI Controller - Coordinates user interface and system components
    
    Responsibilities:
    - GUI lifecycle management
    - Event-driven component coordination
    - User interaction handling
    - Status and progress reporting
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.component_id = "MainController"
        
        # Core infrastructure
        self.event_bus = EventBus(max_workers=4, queue_size=1000)
        self.ui_state = UIState()
        
        # System components
        self.data_loader = DataLoader(self.event_bus)
        self.analysis_engine = AnalysisEngine(self.event_bus)
        self.report_generator = ReportGenerator(self.event_bus)
        
        # UI Components
        self.ui_components = {}
        self.status_var = tk.StringVar()
        self.file_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        
        # Output configuration
        self.output_directory = Path("reports/enhanced")
        
        # Setup
        self._setup_ui()
        self._setup_event_handlers()
        self._initialize_system()
    
    def _setup_event_handlers(self):
        """Subscribe to relevant system events"""
        
        # Data lifecycle events
        self.event_bus.subscribe(
            EventType.DATA_LOADED.value,
            self._handle_data_loaded,
            priority=10,
            handler_id=f"{self.component_id}_data_loaded"
        )
        
        self.event_bus.subscribe(
            EventType.DATA_LOAD_FAILED.value,
            self._handle_data_load_failed,
            priority=10,
            handler_id=f"{self.component_id}_data_load_failed"
        )
        
        # Analysis events
        self.event_bus.subscribe(
            EventType.ANALYSIS_COMPLETED.value,
            self._handle_analysis_completed,
            priority=10,
            handler_id=f"{self.component_id}_analysis_completed"
        )
        
        self.event_bus.subscribe(
            EventType.ANALYSIS_FAILED.value,
            self._handle_analysis_failed,
            priority=10,
            handler_id=f"{self.component_id}_analysis_failed"
        )
        
        # Status and error events
        self.event_bus.subscribe(
            EventType.STATUS_UPDATE.value,
            self._handle_status_update,
            priority=5,
            handler_id=f"{self.component_id}_status_update"
        )
        
        self.event_bus.subscribe(
            EventType.ERROR_OCCURRED.value,
            self._handle_error,
            priority=15,
            handler_id=f"{self.component_id}_error_handler"
        )
        
        # Report generation events
        self.event_bus.subscribe(
            EventType.REPORT_COMPLETED.value,
            self._handle_report_completed,
            priority=10,
            handler_id=f"{self.component_id}_report_completed"
        )
        
        self.event_bus.subscribe(
            EventType.BATCH_REPORT_COMPLETED.value,
            self._handle_batch_report_completed,
            priority=10,
            handler_id=f"{self.component_id}_batch_report_completed"
        )
    
    def _initialize_system(self):
        """Initialize system components"""
        try:
            self.event_bus.start()
            self._publish_status("System initialized successfully", "info")
            self.status_var.set("Ready - Select a CSV file to begin")
        except Exception as e:
            self._publish_error(e, "system_initialization")
            self.status_var.set("System initialization failed")
    
    def _setup_ui(self):
        """Setup the main user interface"""
        self.root.title("🎖️ Enhanced Individual Soldier Report System")
        self.root.geometry("1200x900")
        self.root.configure(bg='#2c3e50')
        
        # Setup main UI structure
        self._create_header()
        self._create_main_content()
        self._create_status_bar()
        
        # Configure window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_header(self):
        """Create application header"""
        header_frame = tk.Frame(self.root, bg='#34495e', height=80)
        header_frame.pack(fill='x', padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="🎖️ Enhanced Individual Soldier Report System", 
            font=('Arial', 18, 'bold'),
            fg='white', bg='#34495e'
        )
        title_label.pack(expand=True)
        
        subtitle_label = tk.Label(
            header_frame,
            text="Battle Analysis • Tactical Assessment • Safety Monitoring",
            font=('Arial', 11),
            fg='#bdc3c7', bg='#34495e'
        )
        subtitle_label.pack()
    
    def _create_main_content(self):
        """Create main content area with tabs"""
        main_frame = tk.Frame(self.root, bg='#ecf0f1')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Main analysis tab
        self.main_tab = tk.Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(self.main_tab, text='📊 Main System')
        
        # Help tab
        self.help_tab = tk.Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(self.help_tab, text='❓ Help & Assessment Criteria')
        
        # Setup tab content
        self._setup_main_tab()
        self._setup_help_tab()
    
    def _setup_main_tab(self):
        """Setup main analysis tab"""
        # Left panel - Controls
        left_panel = tk.Frame(self.main_tab, bg='#ecf0f1', width=450)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # File selection section
        self._create_file_selection_section(left_panel)
        
        # Data information section
        self._create_data_info_section(left_panel)
        
        # Analysis controls
        self._create_analysis_controls_section(left_panel)
        
        # Soldier selection and report generation
        self._create_soldier_selection_section(left_panel)
        
        # Output directory section
        self._create_output_directory_section(left_panel)
        
        # Right panel - Results
        right_panel = tk.Frame(self.main_tab, bg='#ecf0f1')
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Analysis results
        self._create_results_section(right_panel)
        
        # Report status
        self._create_reports_section(right_panel)
    
    def _create_file_selection_section(self, parent):
        """Create file selection section"""
        section = tk.LabelFrame(
            parent, text="📁 Data File Selection",
            font=('Arial', 12, 'bold'),
            bg='#ecf0f1', fg='#2c3e50'
        )
        section.pack(fill='x', pady=(0, 10))
        
        self.file_label = tk.Label(
            section, textvariable=self.file_path_var,
            font=('Arial', 9),
            bg='#ecf0f1', fg='#7f8c8d',
            wraplength=400
        )
        self.file_label.pack(pady=5)
        
        file_button = tk.Button(
            section, text="🔍 Select CSV File",
            command=self._select_file,
            font=('Arial', 11, 'bold'),
            bg='#3498db', fg='white',
            relief='flat', padx=20, pady=10
        )
        file_button.pack(pady=5)
        
        self.ui_components['file_button'] = file_button
    
    def _create_data_info_section(self, parent):
        """Create data information display section"""
        section = tk.LabelFrame(
            parent, text="📊 Data Information",
            font=('Arial', 12, 'bold'),
            bg='#ecf0f1', fg='#2c3e50'
        )
        section.pack(fill='x', pady=(0, 10))
        
        self.info_text = tk.Text(
            section, height=6, width=50,
            font=('Courier', 9),
            bg='white', fg='#2c3e50',
            wrap='word', state='disabled'
        )
        self.info_text.pack(padx=5, pady=5)
        
        self.ui_components['info_text'] = self.info_text
    
    def _create_analysis_controls_section(self, parent):
        """Create analysis controls section"""
        section = tk.LabelFrame(
            parent, text="🎯 Analysis Controls",
            font=('Arial', 12, 'bold'),
            bg='#ecf0f1', fg='#2c3e50'
        )
        section.pack(fill='x', pady=(0, 10))
        
        self.analyze_button = tk.Button(
            section, text="🔬 Run Battle Analysis",
            command=self._run_analysis,
            font=('Arial', 11, 'bold'),
            bg='#e74c3c', fg='white',
            relief='flat', padx=20, pady=10,
            state='disabled'
        )
        self.analyze_button.pack(pady=5)
        
        debug_button = tk.Button(
            section, text="🔍 Debug Failed Reports",
            command=self._debug_failed_reports,
            font=('Arial', 10),
            bg='#9b59b6', fg='white',
            relief='flat', padx=15, pady=5
        )
        debug_button.pack(pady=5)
        
        self.ui_components['analyze_button'] = self.analyze_button
        self.ui_components['debug_button'] = debug_button
    
    def _create_soldier_selection_section(self, parent):
        """Create soldier selection and report generation section"""
        section = tk.LabelFrame(
            parent, text="👥 Soldier Selection & Report Generation",
            font=('Arial', 12, 'bold'),
            bg='#ecf0f1', fg='#2c3e50'
        )
        section.pack(fill='both', expand=True, pady=(0, 10))
        
        # Soldier list
        tk.Label(
            section, text="Available Soldiers:",
            font=('Arial', 10, 'bold'),
            bg='#ecf0f1', fg='#2c3e50'
        ).pack(anchor='w', padx=5, pady=(5,0))
        
        listbox_frame = tk.Frame(section, bg='#ecf0f1')
        listbox_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.soldier_listbox = tk.Listbox(
            listbox_frame,
            font=('Courier', 9),
            selectmode='extended',
            height=8
        )
        
        scrollbar = tk.Scrollbar(
            listbox_frame, orient='vertical',
            command=self.soldier_listbox.yview
        )
        self.soldier_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.soldier_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Report generation buttons
        self._create_report_generation_buttons(section)
        
        self.ui_components['soldier_listbox'] = self.soldier_listbox
    
    def _create_report_generation_buttons(self, parent):
        """Create report generation button section"""
        instructions = tk.Label(
            parent, 
            text="↑ Select soldiers above, then generate reports ↓",
            font=('Arial', 10, 'bold'),
            bg='#ecf0f1', fg='#e67e22'
        )
        instructions.pack(pady=(5, 10))
        
        button_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(
            button_frame, text="REPORT GENERATION:",
            font=('Arial', 9, 'bold'),
            bg='#34495e', fg='white'
        ).pack(pady=(5, 2))
        
        buttons_container = tk.Frame(button_frame, bg='#34495e')
        buttons_container.pack(fill='x', padx=10, pady=(0, 10))
        
        self.generate_selected_button = tk.Button(
            buttons_container, 
            text="📋 Generate Selected Reports",
            command=self._generate_selected_reports,
            font=('Arial', 10, 'bold'),
            bg='#27ae60', fg='white',
            relief='raised', bd=3,
            padx=15, pady=8,
            state='disabled'
        )
        self.generate_selected_button.pack(fill='x', pady=(0, 5))
        
        self.generate_all_button = tk.Button(
            buttons_container,
            text="📤 Generate ALL Soldier Reports",
            command=self._generate_all_reports,
            font=('Arial', 10, 'bold'),
            bg='#f39c12', fg='white',
            relief='raised', bd=3,
            padx=15, pady=8,
            state='disabled'
        )
        self.generate_all_button.pack(fill='x')
        
        self.ui_components['generate_selected_button'] = self.generate_selected_button
        self.ui_components['generate_all_button'] = self.generate_all_button
    
    def _create_output_directory_section(self, parent):
        """Create output directory configuration section"""
        section = tk.LabelFrame(
            parent, text="📁 Output Directory",
            font=('Arial', 12, 'bold'),
            bg='#ecf0f1', fg='#2c3e50'
        )
        section.pack(fill='x')
        
        self.output_path_var.set("📁 reports/enhanced (default)")
        
        self.output_label = tk.Label(
            section, textvariable=self.output_path_var,
            font=('Arial', 9),
            bg='#ecf0f1', fg='#7f8c8d',
            wraplength=400
        )
        self.output_label.pack(pady=5)
        
        button_frame = tk.Frame(section, bg='#ecf0f1')
        button_frame.pack(pady=5)
        
        select_output_button = tk.Button(
            button_frame, text="📂 Choose Directory",
            command=self._select_output_directory,
            font=('Arial', 10),
            bg='#9b59b6', fg='white',
            relief='flat', padx=15, pady=5
        )
        select_output_button.pack(side='left', padx=(0, 5))
        
        open_output_button = tk.Button(
            button_frame, text="🔍 Open Folder",
            command=self._open_output_directory,
            font=('Arial', 10),
            bg='#16a085', fg='white',
            relief='flat', padx=15, pady=5
        )
        open_output_button.pack(side='right')
        
        self.ui_components['select_output_button'] = select_output_button
        self.ui_components['open_output_button'] = open_output_button
    
    def _create_results_section(self, parent):
        """Create analysis results section"""
        section = tk.LabelFrame(
            parent, text="⚔️ Battle Analysis Results",
            font=('Arial', 12, 'bold'),
            bg='#ecf0f1', fg='#2c3e50'
        )
        section.pack(fill='x', pady=(0, 10))
        
        self.results_text = tk.Text(
            section, height=10,
            font=('Courier', 9),
            bg='white', fg='#2c3e50',
            wrap='word', state='disabled'
        )
        
        results_scrollbar = tk.Scrollbar(
            section, orient='vertical',
            command=self.results_text.yview
        )
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        results_scrollbar.pack(side='right', fill='y')
        self.results_text.pack(fill='x', padx=5, pady=5)
        
        self.ui_components['results_text'] = self.results_text
    
    def _create_reports_section(self, parent):
        """Create generated reports section"""
        section = tk.LabelFrame(
            parent, text="📝 Generated Reports",
            font=('Arial', 12, 'bold'),
            bg='#ecf0f1', fg='#2c3e50'
        )
        section.pack(fill='both', expand=True)
        
        self.reports_text = scrolledtext.ScrolledText(
            section, height=15,
            font=('Courier', 9),
            bg='white', fg='#2c3e50',
            wrap='word', state='disabled'
        )
        self.reports_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.ui_components['reports_text'] = self.reports_text
    
    def _setup_help_tab(self):
        """Setup help and assessment criteria tab"""
        canvas = tk.Canvas(self.help_tab, bg='#ecf0f1')
        scrollbar = ttk.Scrollbar(
            self.help_tab, orient="vertical",
            command=canvas.yview
        )
        scrollable_frame = tk.Frame(canvas, bg='#ecf0f1')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        help_text = """
🎯 ASSESSMENT CRITERIA OVERVIEW

📊 PERFORMANCE SCORING (0-100 Points):
• Activity Level: Physical movement and step count
• Casualty Status: Mission outcome (WOUNDED -10, KIA -20)
• Heart Rate: Safety monitoring only (NO performance penalty)
• Tactical Posture: Battle positioning and movement
• Equipment Status: Battery and communication quality
• Combat Engagement: Active participation in combat

⚔️ BATTLE TIMELINE CONTEXT:
• Pre-Battle Period: Setup and preparation phase
• Battle Period: Last 45 minutes of exercise
• Different scoring rules apply to each phase

❤️ MEDICAL MONITORING:
• Heart rate 60-190 BPM = Normal (no penalty)
• >190 BPM = Medical alert (no performance penalty)
• <60 BPM = Medical evaluation needed (no penalty)
• Focus on soldier safety, not punishment

🔋 EQUIPMENT ASSESSMENT:
• Battery <20% = Critical (-15 points)
• Poor communication = Mission risk (-5 points)
• Excellent communication = Tactical advantage (+3 points)

🎖️ PHILOSOPHY:
• Performance = Controllable actions and decisions
• Medical = Health monitoring and safety support
• Fair assessment regardless of medical conditions
• Military realism in tactical evaluation

For complete details, see the comprehensive documentation
in the system's help sections and generated reports.
        """
        
        help_label = tk.Label(
            scrollable_frame, text=help_text,
            font=('Courier', 10),
            bg='#ecf0f1', fg='#2c3e50',
            justify='left', wraplength=1000
        )
        help_label.pack(padx=20, pady=20, anchor='w')
        
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
    
    def _create_status_bar(self):
        """Create application status bar"""
        status_bar = tk.Label(
            self.root, textvariable=self.status_var,
            font=('Arial', 10),
            bg='#34495e', fg='white',
            anchor='w', padx=10
        )
        status_bar.pack(fill='x')
    
    # Event Handlers
    def _handle_data_loaded(self, event: Event):
        """Handle data loaded event"""
        def update_ui():
            self.ui_state.file_loaded = True
            self.ui_state.current_dataset = event.data.get('dataset')
            
            # Update UI state
            self.analyze_button.config(state='normal')
            self._update_data_info()
            
            # Update file path display
            file_path = event.data.get('file_path', '')
            self.file_path_var.set(f"📁 {os.path.basename(file_path)}")
            
            self.status_var.set(
                f"Data loaded successfully - {event.data.get('record_count', 0)} records"
            )
        
        # Schedule UI update on main thread
        self.root.after(0, update_ui)
    
    def _handle_data_load_failed(self, event: Event):
        """Handle data load failure"""
        def update_ui():
            error_message = event.data.get('error_message', 'Unknown error')
            messagebox.showerror("Data Load Error", f"Failed to load data:\n{error_message}")
            self.status_var.set("Data load failed")
        
        self.root.after(0, update_ui)
    
    def _handle_analysis_completed(self, event: Event):
        """Handle analysis completion"""
        def update_ui():
            self.ui_state.analysis_complete = True
            
            # Update results display
            self._update_analysis_results(event.data.get('results'))
            
            # Populate soldier list
            self._populate_soldier_list()
            
            # Enable report generation
            self.generate_selected_button.config(state='normal')
            self.generate_all_button.config(state='normal')
            
            self.status_var.set("Analysis complete - Select soldiers for reports")
        
        self.root.after(0, update_ui)
    
    def _handle_analysis_failed(self, event: Event):
        """Handle analysis failure"""
        def update_ui():
            error_message = event.data.get('error_message', 'Analysis failed')
            messagebox.showerror("Analysis Error", error_message)
            self.status_var.set("Analysis failed")
        
        self.root.after(0, update_ui)
    
    def _handle_status_update(self, event: Event):
        """Handle status update events"""
        def update_ui():
            message = event.data.get('message', '')
            level = event.data.get('level', 'info')
            
            # Update status bar
            self.status_var.set(message)
        
        self.root.after(0, update_ui)
    
    def _handle_error(self, event: Event):
        """Handle error events"""
        def update_ui():
            error_message = event.data.get('error_message', 'An error occurred')
            context = event.data.get('context', '')
            
            # Show error to user if appropriate
            if context in ['critical', 'user_action']:
                messagebox.showerror("System Error", error_message)
            
            self.status_var.set(f"Error: {error_message}")
        
        self.root.after(0, update_ui)
    
    def _handle_report_completed(self, event: Event):
        """Handle individual report completion"""
        def update_ui():
            callsign = event.data.get('callsign', 'Unknown')
            report_path = event.data.get('report_path', '')
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            report_info = f"[{timestamp}] ✅ {callsign} -> {os.path.basename(report_path)}\n"
            self._add_report_info(report_info)
        
        self.root.after(0, update_ui)
    
    def _handle_batch_report_completed(self, event: Event):
        """Handle batch report completion"""
        def update_ui():
            successful = event.data.get('successful', 0)
            failed = event.data.get('failed', 0)
            reports_dir = event.data.get('reports_dir', '')
            
            completion_msg = (
                f"Report generation complete!\n\n"
                f"Successful: {successful}\nFailed: {failed}\n\n"
                f"Reports saved in:\n{reports_dir}\n\n"
                f"Would you like to open the folder?"
            )
            
            result = messagebox.askyesno("Generation Complete", completion_msg)
            if result and reports_dir:
                self._open_directory(reports_dir)
            
            self.status_var.set(f"Generation complete: {successful} successful, {failed} failed")
        
        self.root.after(0, update_ui)
    
    # UI Action Methods
    def _select_file(self):
        """Handle file selection"""
        filetypes = [
            ('CSV files', '*.csv'),
            ('All files', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title='Select Fort Moore Training Data CSV File',
            filetypes=filetypes,
            initialdir='.'
        )
        
        if filename:
            # Publish file selected event
            self.event_bus.publish(FileSelectedEvent(filename, self.component_id))
    
    def _run_analysis(self):
        """Run battle analysis"""
        if not self.ui_state.file_loaded:
            messagebox.showwarning("No Data", "Please load data first.")
            return
        
        # Publish analysis request event
        self.event_bus.publish(Event(
            type=EventType.ANALYSIS_STARTED.value,
            data={'dataset': self.ui_state.current_dataset},
            source=self.component_id
        ))
    
    def _generate_selected_reports(self):
        """Generate reports for selected soldiers"""
        selected_indices = self.soldier_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select at least one soldier from the list.")
            return
        
        selected_callsigns = [self.soldier_listbox.get(i) for i in selected_indices]
        self._request_report_generation(selected_callsigns)
    
    def _generate_all_reports(self):
        """Generate reports for all soldiers"""
        if not self.ui_state.analysis_complete:
            messagebox.showwarning("No Analysis", "Please run analysis first.")
            return
        
        # Get all callsigns from listbox
        all_callsigns = [self.soldier_listbox.get(i) for i in range(self.soldier_listbox.size())]
        
        result = messagebox.askyesno(
            "Generate All Reports", 
            f"Generate reports for all {len(all_callsigns)} soldiers?\n\nThis may take several minutes."
        )
        
        if result:
            self._request_report_generation(all_callsigns)
    
    def _request_report_generation(self, callsigns: List[str]):
        """Request report generation for specified callsigns"""
        self.event_bus.publish(Event(
            type=EventType.REPORT_GENERATION_REQUESTED.value,
            data={
                'callsigns': callsigns,
                'output_directory': str(self.output_directory),
                'dataset': self.ui_state.current_dataset
            },
            source=self.component_id
        ))
    
    def _select_output_directory(self):
        """Select output directory for reports"""
        directory = filedialog.askdirectory(
            title='Select Directory for Reports',
            initialdir=str(self.output_directory.parent)
        )
        
        if directory:
            self.output_directory = Path(directory)
            self.output_path_var.set(f"📁 {directory}")
            self.status_var.set(f"Output directory set to: {directory}")
    
    def _open_output_directory(self):
        """Open output directory in file explorer"""
        try:
            self.output_directory.mkdir(parents=True, exist_ok=True)
            self._open_directory(str(self.output_directory))
            self.status_var.set(f"Opened directory: {self.output_directory}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open directory:\n{str(e)}")
    
    def _debug_failed_reports(self):
        """Debug failed reports"""
        if not self.ui_state.current_dataset:
            messagebox.showwarning("No Data", "Please load data first.")
            return
        
        # This would integrate with the analysis engine's debug capabilities
        debug_window = tk.Toplevel(self.root)
        debug_window.title("🔍 Debug Failed Reports")
        debug_window.geometry("800x600")
        
        debug_text = scrolledtext.ScrolledText(debug_window, font=('Courier', 10))
        debug_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Request debug information via event
        self.event_bus.publish(Event(
            type="DEBUG_REQUEST",
            data={'debug_window': debug_window, 'debug_text': debug_text},
            source=self.component_id
        ))
    
    # Helper Methods
    def _update_data_info(self):
        """Update data information display"""
        if not self.ui_state.current_dataset:
            return
        
        # This would extract info from the dataset
        info = """📊 FORT MOORE DATA SUMMARY
════════════════════════════════
Records: 1,234
Columns: 15

👥 Soldiers: 25
🏗️  Squads: Alpha, Bravo, Charlie
💀 Casualties: 3
⏰ Duration: 120 minutes
        """
        
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', 'end')
        self.info_text.insert('1.0', info)
        self.info_text.config(state='disabled')
    
    def _update_analysis_results(self, results):
        """Update analysis results display"""
        if not results:
            return
        
        results_text = """⚔️  BATTLE ANALYSIS RESULTS
════════════════════════════════════

👥 Total Soldiers: 25
💀 Total Casualties: 3
❤️  Avg Heart Rate: 145 BPM

🎖️  READY FOR REPORT GENERATION
════════════════════════════════════

Select soldiers from the list below and click
"Generate Selected Reports" or "Generate ALL Reports"
        """
        
        self.results_text.config(state='normal')
        self.results_text.delete('1.0', 'end')
        self.results_text.insert('1.0', results_text)
        self.results_text.config(state='disabled')
    
    def _populate_soldier_list(self):
        """Populate soldier selection list"""
        if not self.ui_state.current_dataset:
            return
        
        self.soldier_listbox.delete(0, 'end')
        
        # This would get actual callsigns from the dataset
        callsigns = ['ALPHA-01', 'ALPHA-02', 'BRAVO-01', 'BRAVO-02', 'CHARLIE-01']
        
        for callsign in sorted(callsigns):
            self.soldier_listbox.insert('end', callsign)
        
        self.status_var.set(f"Ready to generate reports for {len(callsigns)} soldiers")
    
    def _add_report_info(self, info: str):
        """Add report information to reports display"""
        self.reports_text.config(state='normal')
        self.reports_text.insert('end', info)
        self.reports_text.see('end')
        self.reports_text.config(state='disabled')
    
    def _open_directory(self, directory_path: str):
        """Open directory in system file explorer"""
        import platform
        import subprocess
        
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(directory_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", directory_path])
            else:  # Linux
                subprocess.run(["xdg-open", directory_path])
        except Exception as e:
            raise Exception(f"Could not open directory: {e}")
    
    def _publish_status(self, message: str, level: str = "info"):
        """Publish status update event"""
        self.event_bus.publish(StatusUpdateEvent(message, level, self.component_id))
    
    def _publish_error(self, error: Exception, context: str = None):
        """Publish error event"""
        self.event_bus.publish(ErrorEvent(error, context, self.component_id))
    
    def _on_closing(self):
        """Handle application shutdown"""
        try:
            self._publish_status("Shutting down system...", "info")
            
            # Stop event bus
            self.event_bus.stop(timeout=2.0)
            
            # Destroy window
            self.root.destroy()
        except Exception as e:
            print(f"Error during shutdown: {e}")
            self.root.destroy()
    
    def run(self):
        """Run the main application"""
        print("🎖️ Enhanced Individual Soldier Report System - Main Controller")
        print("=" * 70)
        print("Starting GUI with event-driven architecture...")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
            self._on_closing()
        except Exception as e:
            print(f"❌ Error in main application: {e}")
            self._publish_error(e, "main_application")


def main():
    """Main function"""
    try:
        controller = MainController()
        controller.run()
    except Exception as e:
        print(f"❌ Error starting main controller: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
