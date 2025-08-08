# File: src/gui/components/soldier_list.py
"""Soldier selection component"""

import tkinter as tk
from tkinter import messagebox

from src.core.event_bus import EventBus
from src.core.events import EventType, ReportGenerationRequestedEvent


class SoldierList:
    """Component for soldier selection and report generation"""
    
    def __init__(self, parent, event_bus: EventBus):
        self.parent = parent
        self.event_bus = event_bus
        self.soldiers = []
        self.current_dataset = None  # Store the current dataset
        
        self._create_widgets()
        self._setup_layout()
        self._setup_event_handlers()
    
    def _create_widgets(self):
        """Create soldier list widgets"""
        # Main frame
        self.frame = tk.LabelFrame(
            self.parent,
            text="👥 Soldier Selection & Report Generation",
            font=('Arial', 12, 'bold'),
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        
        # Available soldiers label
        self.soldiers_label = tk.Label(
            self.frame,
            text="Available Soldiers:",
            font=('Arial', 10, 'bold'),
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        
        # Listbox frame with scrollbar
        self.listbox_frame = tk.Frame(self.frame, bg='#ecf0f1')
        
        self.soldier_listbox = tk.Listbox(
            self.listbox_frame,
            font=('Courier', 9),
            selectmode='extended',
            height=8
        )
        
        self.scrollbar = tk.Scrollbar(
            self.listbox_frame,
            orient='vertical',
            command=self.soldier_listbox.yview
        )
        self.soldier_listbox.configure(yscrollcommand=self.scrollbar.set)
        
        # Instructions
        self.instructions = tk.Label(
            self.frame,
            text="↑ Select soldiers above, then generate reports ↓",
            font=('Arial', 10, 'bold'),
            bg='#ecf0f1',
            fg='#e67e22'
        )
        
        # Button frame
        self.button_frame = tk.Frame(self.frame, bg='#34495e', relief='raised', bd=2)
        
        self.button_label = tk.Label(
            self.button_frame,
            text="REPORT GENERATION:",
            font=('Arial', 9, 'bold'),
            bg='#34495e',
            fg='white'
        )
        
        # Report generation buttons
        self.buttons_container = tk.Frame(self.button_frame, bg='#34495e')
        
        self.generate_selected_button = tk.Button(
            self.buttons_container,
            text="📋 Generate Selected Reports",
            command=self._generate_selected_reports,
            font=('Arial', 10, 'bold'),
            bg='#27ae60',
            fg='white',
            relief='raised',
            bd=3,
            padx=15,
            pady=8,
            state='disabled'
        )
        
        self.generate_all_button = tk.Button(
            self.buttons_container,
            text="📤 Generate ALL Soldier Reports",
            command=self._generate_all_reports,
            font=('Arial', 10, 'bold'),
            bg='#f39c12',
            fg='white',
            relief='raised',
            bd=3,
            padx=15,
            pady=8,
            state='disabled'
        )
        
        # Analysis controls
        self.analysis_frame = tk.LabelFrame(
            self.parent,
            text="🎯 Analysis Controls",
            font=('Arial', 12, 'bold'),
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        
        self.analyze_button = tk.Button(
            self.analysis_frame,
            text="🔬 Run Battle Analysis",
            command=self._run_analysis,
            font=('Arial', 11, 'bold'),
            bg='#e74c3c',
            fg='white',
            relief='flat',
            padx=20,
            pady=10,
            state='disabled'
        )
        
        self.debug_button = tk.Button(
            self.analysis_frame,
            text="🔍 Debug Failed Reports",
            command=self._debug_failed_reports,
            font=('Arial', 10),
            bg='#9b59b6',
            fg='white',
            relief='flat',
            padx=15,
            pady=5
        )
    
    def _setup_layout(self):
        """Setup widget layout"""
        # Soldiers label
        self.soldiers_label.pack(anchor='w', padx=5, pady=(5, 0))
        
        # Listbox with scrollbar
        self.listbox_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.soldier_listbox.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')
        
        # Instructions
        self.instructions.pack(pady=(5, 10))
        
        # Button frame
        self.button_frame.pack(fill='x', padx=5, pady=5)
        self.button_label.pack(pady=(5, 2))
        self.buttons_container.pack(fill='x', padx=10, pady=(0, 10))
        
        # Report generation buttons
        self.generate_selected_button.pack(fill='x', pady=(0, 5))
        self.generate_all_button.pack(fill='x')
        
        # Analysis controls
        self.analyze_button.pack(pady=5)
        self.debug_button.pack(pady=5)
    
    def _setup_event_handlers(self):
        """Setup event handlers"""
        self.event_bus.subscribe(
            EventType.DATA_LOADED.value,
            self._handle_data_loaded
        )
        
        self.event_bus.subscribe(
            EventType.ANALYSIS_COMPLETED.value,
            self._handle_analysis_completed
        )
    
    def _handle_data_loaded(self, event):
        """Handle data loaded event"""
        dataset = event.data['dataset']
        
        # Store the dataset for analysis
        self.current_dataset = dataset
        
        # Enable analysis button
        self.analyze_button.config(state='normal')
        
        # Clear existing soldiers
        self.soldier_listbox.delete(0, 'end')
        self.soldiers = []
        
        # Get soldiers from dataset
        if 'Callsign' in dataset.raw_dataframe.columns:
            self.soldiers = sorted(dataset.raw_dataframe['Callsign'].unique())
            
            # Populate listbox
            for soldier in self.soldiers:
                self.soldier_listbox.insert('end', soldier)
    
    def _handle_analysis_completed(self, event):
        """Handle analysis completed event"""
        # Enable report generation buttons
        self.generate_selected_button.config(state='normal')
        self.generate_all_button.config(state='normal')
    
    def _run_analysis(self):
        """Run analysis"""
        from ...core.events import Event
        
        # Check if we have a dataset to analyze
        if self.current_dataset is None:
            messagebox.showwarning(
                "No Data",
                "Please load a CSV file before running analysis."
            )
            return
        
        # Publish analysis event with dataset
        self.event_bus.publish(Event(
            type=EventType.ANALYSIS_STARTED.value,
            data={'dataset': self.current_dataset},
            source="SoldierList"
        ))
    
    def _generate_selected_reports(self):
        """Generate reports for selected soldiers"""
        selected_indices = self.soldier_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning(
                "No Selection",
                "Please select at least one soldier from the list."
            )
            return
        
        selected_callsigns = [self.soldiers[i] for i in selected_indices]
        
        self.event_bus.publish(ReportGenerationRequestedEvent(
            soldier_callsigns=selected_callsigns,
            output_directory="reports/enhanced",  # TODO: Get from settings
            source="SoldierList"
        ))
    
    def _generate_all_reports(self):
        """Generate reports for all soldiers"""
        if not self.soldiers:
            return
        
        result = messagebox.askyesno(
            "Generate All Reports",
            f"Generate reports for all {len(self.soldiers)} soldiers?\n\n"
            "This may take several minutes."
        )
        
        if result:
            self.event_bus.publish(ReportGenerationRequestedEvent(
                soldier_callsigns=self.soldiers,
                output_directory="reports/enhanced",  # TODO: Get from settings
                source="SoldierList"
            ))
    
    def _debug_failed_reports(self):
        """Debug failed reports - placeholder for now"""
        messagebox.showinfo(
            "Debug Reports",
            "Debug functionality will be implemented in the reporting service."
        )
    
    def pack(self, **kwargs):
        """Pack the soldier list frame"""
        self.analysis_frame.pack(fill='x', pady=(0, 10))
        self.frame.pack(**kwargs)