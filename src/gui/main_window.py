# File: src/gui/main_window.py
"""Professional Main GUI window for the Enhanced Soldier Report System"""

import tkinter as tk
from tkinter import ttk
import logging

from src.core.event_bus import EventBus, Event
from src.core.events import EventType, StatusUpdateEvent
from src.gui.components.file_selector import FileSelector
from src.gui.components.soldier_list import SoldierList
from src.gui.components.analysis_display import AnalysisDisplay
from src.gui.components.report_status import ReportStatus


class MainWindow:
    """Professional main application window with enhanced styling"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._logger = logging.getLogger(__name__)
        
        # Color scheme for professional appearance
        self.colors = {
            'primary_bg': '#1a1a1a',          # Dark background
            'secondary_bg': '#2d2d2d',        # Card backgrounds
            'accent': '#0078d4',              # Microsoft blue accent
            'accent_hover': '#106ebe',        # Darker blue for hover
            'text_primary': '#000000',        # Black text
            'text_secondary': '#000000',      # Black text
            'text_muted': '#000000',          # Black text
            'border': '#404040',              # Border color
            'success': '#107c10',             # Success green
            'warning': '#ff8c00',             # Warning orange
            'error': '#d13438',               # Error red
            'card_shadow': '#0d1117'          # Card shadow
        }
        
        # Initialize main window
        self.root = tk.Tk()
        self._setup_window()
        
        # Initialize components
        self._create_components()
        self._setup_layout()
        self._setup_event_handlers()
        
        self._logger.info("Professional main window initialized")
    
    def _setup_window(self):
        """Setup main window properties with professional styling"""
        self.root.title("Enhanced Individual Soldier Report System")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        self.root.configure(bg=self.colors['primary_bg'])
        
        # Configure ttk styles for professional appearance
        self._setup_styles()
        
        # Configure grid weights for responsive layout
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Set window icon if available
        try:
            # You can add an icon file here
            # self.root.iconbitmap('assets/icon.ico')
            pass
        except:
            pass
    
    def _setup_styles(self):
        """Configure ttk styles for professional appearance"""
        style = ttk.Style()
        
        # Configure notebook style
        style.theme_use('clam')
        
        style.configure('Professional.TNotebook', 
                       background=self.colors['primary_bg'],
                       borderwidth=0)
        
        style.configure('Professional.TNotebook.Tab',
                       background=self.colors['secondary_bg'],
                       foreground=self.colors['text_primary'],
                       padding=[20, 10],
                       borderwidth=1,
                       focuscolor='none')
        
        style.map('Professional.TNotebook.Tab',
                 background=[('selected', self.colors['accent']),
                           ('active', self.colors['accent_hover'])],
                 foreground=[('selected', self.colors['text_primary']),
                           ('active', self.colors['text_primary'])])
        
        # Configure frame styles
        style.configure('Card.TFrame',
                       background=self.colors['secondary_bg'],
                       relief='flat',
                       borderwidth=1)
        
        style.configure('Header.TFrame',
                       background=self.colors['accent'],
                       relief='flat')
    
    def _create_components(self):
        """Create all GUI components with professional styling"""
        # Header frame
        self.header_frame = self._create_header()
        
        # Main content with professional notebook
        self.notebook = ttk.Notebook(self.root, style='Professional.TNotebook')
        
        # Main analysis tab
        self.main_tab = tk.Frame(self.notebook, bg=self.colors['primary_bg'])
        self.notebook.add(self.main_tab, text='  System Analysis  ')
        
        # Help and documentation tab
        self.help_tab = tk.Frame(self.notebook, bg=self.colors['primary_bg'])
        self.notebook.add(self.help_tab, text='  Help & Criteria  ')
        
        # Create help content
        self._create_help_content()
        
        # Main tab components
        self._create_main_tab_components()
        
        # Professional status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Select a CSV file to begin analysis")
        self.status_bar = self._create_status_bar()
    
    def _create_header(self):
        """Create professional header section"""
        header_frame = tk.Frame(self.root, bg=self.colors['accent'], height=100)
        header_frame.grid(row=0, column=0, sticky='ew', padx=0, pady=0)
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Main title
        title_label = tk.Label(
            header_frame,
            text="Enhanced Individual Soldier Report System",
            font=('Segoe UI', 24, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['accent']
        )
        title_label.grid(row=0, column=0, pady=(20, 5))
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Advanced Battle Analysis • Tactical Assessment • Safety Monitoring",
            font=('Segoe UI', 12),
            fg=self.colors['text_primary'],
            bg=self.colors['accent']
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 20))
        
        return header_frame
    
    def _create_main_tab_components(self):
        """Create components for main analysis tab"""
        # Configure main tab grid
        self.main_tab.grid_rowconfigure(0, weight=1)
        self.main_tab.grid_columnconfigure(0, weight=0, minsize=400)  # Left panel
        self.main_tab.grid_columnconfigure(1, weight=1)               # Right panel
        
        # Left control panel with professional styling
        self.left_panel = tk.Frame(
            self.main_tab, 
            bg=self.colors['secondary_bg'],
            relief='flat',
            bd=1
        )
        self.left_panel.grid(row=0, column=0, sticky='nsew', padx=(10, 5), pady=10)
        
        # Right analysis panel
        self.right_panel = tk.Frame(
            self.main_tab,
            bg=self.colors['secondary_bg'], 
            relief='flat',
            bd=1
        )
        self.right_panel.grid(row=0, column=1, sticky='nsew', padx=(5, 10), pady=10)
        
        # Left panel components with enhanced styling
        self.file_selector = FileSelector(self.left_panel, self.event_bus, self.colors)
        self.soldier_list = SoldierList(self.left_panel, self.event_bus)
        
        # Right panel components
        self.analysis_display = AnalysisDisplay(self.right_panel, self.event_bus)
        self.report_status = ReportStatus(self.right_panel, self.event_bus)
    
    def _create_help_content(self):
        """Create professional help and documentation content"""
        # Configure help tab
        self.help_tab.grid_rowconfigure(0, weight=1)
        self.help_tab.grid_columnconfigure(0, weight=1)
        
        # Scrollable text widget for help content
        help_frame = tk.Frame(self.help_tab, bg=self.colors['primary_bg'])
        help_frame.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        help_frame.grid_rowconfigure(0, weight=1)
        help_frame.grid_columnconfigure(0, weight=1)
        
        # Help text widget with professional styling
        help_text = tk.Text(
            help_frame,
            bg=self.colors['secondary_bg'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 11),
            wrap=tk.WORD,
            padx=20,
            pady=20,
            relief='flat',
            selectbackground=self.colors['accent'],
            selectforeground=self.colors['text_primary']
        )
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(help_frame, orient="vertical", command=help_text.yview)
        help_text.configure(yscrollcommand=scrollbar.set)
        
        help_text.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Insert help content
        help_content = self._get_help_content()
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)  # Make read-only
    
    def _get_help_content(self):
        """Return comprehensive help content"""
        return """ENHANCED INDIVIDUAL SOLDIER REPORT SYSTEM
HELP & ASSESSMENT CRITERIA

OVERVIEW
========
This system analyzes soldier performance data from military training exercises and operations, 
providing comprehensive safety monitoring and tactical assessment capabilities.

GETTING STARTED
===============
1. Select Data File: Click "Select CSV File" to load your soldier data
2. Run Analysis: Click "Run Battle Analysis" to process the data
3. Select Soldiers: Choose specific soldiers from the list for detailed reports
4. Generate Reports: Create individual or batch reports for selected soldiers

DATA REQUIREMENTS
=================
Required CSV Columns:
• Callsign - Soldier identifier
• Player_ID - System-generated ID (optional)
• Step_Count - Movement activity data
• Posture - Current position (Standing, Kneeling, Prone, Moving)
• Heart_Rate - Physiological monitoring
• GPS coordinates - Location tracking
• Casualty_State - Health status
• Equipment status - Battery, communication levels

PERFORMANCE SCORING
===================
Movement Metrics:
• Step Count Analysis (Engagement vs Non-Engagement periods)
• Position Change Frequency
• Tactical Movement Patterns

Tactical Positioning:
• Posture Distribution During Battle
• GPS Movement Pattern Analysis
• Cover Utilization Assessment

Safety Monitoring:
• Heart Rate Zone Analysis (60-190 BPM safe range)
• Temperature Stress Monitoring
• Injury Risk Assessment
• Medical Alert Generation

SAFETY ZONES
============
Heart Rate Monitoring:
🟢 Green Zone (60-140 BPM): Normal operation
🟡 Yellow Zone (140-170 BPM): Monitor closely, no penalties
🟠 Orange Zone (170-190 BPM): Medical alert, performance scoring suspended
🔴 Red Zone (>190 or <60 BPM): Immediate medical intervention required

REPORT TYPES
============
Individual Reports:
• Detailed personal performance analysis
• Safety assessment and medical monitoring
• Tactical behavior evaluation
• Specific improvement recommendations

Squad/Platoon Reports:
• Unit cohesion metrics
• Comparative performance analysis
• Strategic effectiveness assessment
• Resource allocation recommendations

OUTPUT FORMATS
==============
• HTML: Interactive reports with charts and visualizations
• PDF: Professional formatted documents
• Excel: Data analysis and tracking spreadsheets
• JSON: API integration and data exchange

TROUBLESHOOTING
===============
Common Issues:
• File Format: Ensure CSV files are properly formatted
• Missing Columns: Check all required data columns are present
• Data Quality: Verify GPS coordinates and sensor data accuracy
• Performance: Large datasets may require additional processing time

For technical support or additional information, contact your system administrator.

Version 2.0 - Enhanced Controller Architecture
Last Updated: August 2025"""
    
    def _create_status_bar(self):
        """Create professional status bar"""
        status_frame = tk.Frame(
            self.root,
            bg=self.colors['secondary_bg'],
            height=35,
            relief='flat'
        )
        status_frame.grid(row=2, column=0, sticky='ew')
        status_frame.grid_propagate(False)
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Status indicator
        self.status_indicator = tk.Label(
            status_frame,
            text="●",
            font=('Segoe UI', 12),
            fg=self.colors['success'],
            bg=self.colors['secondary_bg'],
            width=3
        )
        self.status_indicator.grid(row=0, column=0, padx=(10, 5), pady=8)
        
        # Status text
        status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=('Segoe UI', 10),
            fg=self.colors['text_primary'],
            bg=self.colors['secondary_bg'],
            anchor='w'
        )
        status_label.grid(row=0, column=1, sticky='ew', pady=8)
        
        return status_frame
    
    def _setup_layout(self):
        """Setup component layout with professional spacing"""
        # Main notebook
        self.notebook.grid(row=1, column=0, sticky='nsew', padx=0, pady=0)
        
        # Left panel layout with proper spacing
        self.file_selector.pack(fill='x', padx=20, pady=(20, 10))
        
        # Separator line
        separator = tk.Frame(self.left_panel, height=1, bg=self.colors['border'])
        separator.pack(fill='x', padx=20, pady=10)
        
        self.soldier_list.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Right panel layout
        self.analysis_display.pack(fill='x', padx=20, pady=(20, 10))
        
        # Another separator
        separator2 = tk.Frame(self.right_panel, height=1, bg=self.colors['border'])
        separator2.pack(fill='x', padx=20, pady=10)
        
        self.report_status.pack(fill='both', expand=True, padx=20, pady=(0, 20))
    
    def _setup_event_handlers(self):
        """Setup event handlers for UI updates"""
        self.event_bus.subscribe(
            EventType.STATUS_UPDATE.value,
            self._handle_status_update
        )
        
        self.event_bus.subscribe(
            EventType.ERROR_OCCURRED.value,
            self._handle_error
        )
    
    def _handle_status_update(self, event: Event):
        """Handle status update events with visual indicators"""
        message = event.data['message']
        level = event.data.get('level', 'info')
        
        self.status_var.set(message)
        
        # Update status indicator color based on level
        if level == 'error':
            self.status_indicator.config(fg=self.colors['error'])
        elif level == 'warning':
            self.status_indicator.config(fg=self.colors['warning'])
        elif level == 'success':
            self.status_indicator.config(fg=self.colors['success'])
        else:
            self.status_indicator.config(fg=self.colors['accent'])
        
        self._logger.debug(f"Status update: {message}")
    
    def _handle_error(self, event: Event):
        """Handle error events with enhanced error display"""
        error_message = event.data['error_message']
        context = event.data.get('context', '')
        
        full_message = f"Error: {error_message}"
        if context:
            full_message += f" (Context: {context})"
        
        self.status_var.set(full_message)
        self.status_indicator.config(fg=self.colors['error'])
        self._logger.error(full_message)
    
    def run(self):
        """Start the GUI application"""
        # Publish application started event
        self.event_bus.publish(StatusUpdateEvent(
            "System ready - Select a CSV file to begin analysis",
            level="success",
            source="MainWindow"
        ))
        
        self._logger.info("Starting professional GUI main loop")
        self.root.mainloop()
    
    def destroy(self):
        """Clean shutdown of the window"""
        self._logger.info("Shutting down professional main window")
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            # Window already destroyed
            pass