# File: src/gui/components/analysis_display.py
"""Analysis results display component"""

import tkinter as tk
from tkinter import scrolledtext

from src.core.event_bus import EventBus
from src.core.events import EventType


class AnalysisDisplay:
    """Component for displaying analysis results"""
    
    def __init__(self, parent, event_bus: EventBus):
        self.parent = parent
        self.event_bus = event_bus
        
        self._create_widgets()
        self._setup_layout()
        self._setup_event_handlers()
    
    def _create_widgets(self):
        """Create analysis display widgets"""
        # Main frame
        self.frame = tk.LabelFrame(
            self.parent,
            text="⚔️ Battle Analysis Results",
            font=('Arial', 12, 'bold'),
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        
        # Results text widget with scrollbar
        self.results_text = tk.Text(
            self.frame,
            height=10,
            font=('Courier', 9),
            bg='white',
            fg='#2c3e50',
            wrap='word',
            state='disabled'
        )
        
        self.results_scrollbar = tk.Scrollbar(
            self.frame,
            orient='vertical',
            command=self.results_text.yview
        )
        self.results_text.configure(yscrollcommand=self.results_scrollbar.set)
    
    def _setup_layout(self):
        """Setup widget layout"""
        self.results_scrollbar.pack(side='right', fill='y')
        self.results_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def _setup_event_handlers(self):
        """Setup event handlers"""
        self.event_bus.subscribe(
            EventType.ANALYSIS_COMPLETED.value,
            self._handle_analysis_completed
        )
        
        self.event_bus.subscribe(
            EventType.ANALYSIS_STARTED.value,
            self._handle_analysis_started
        )
    
    def _handle_analysis_started(self, event):
        """Handle analysis started event"""
        self._update_display("🔬 Running comprehensive battle analysis...\n\nPlease wait...")
    
    def _handle_analysis_completed(self, event):
        """Handle analysis completed event"""
        # Use 'batch_result' key instead of 'results' to match AnalysisEngine
        batch_result = event.data['batch_result']
        self._display_analysis_results(batch_result)
    
    def _display_analysis_results(self, batch_result):
        """Display analysis results"""
        # Display basic batch analysis information
        display_text = f"""⚔️  BATTLE ANALYSIS RESULTS
════════════════════════════════════

👥 Total Soldiers Analyzed: {len(batch_result.soldier_results)}
📊 Analysis Status: {batch_result.analysis_status.value}
🆔 Analysis ID: {batch_result.analysis_id}

🎖️  READY FOR REPORT GENERATION
════════════════════════════════════

Select soldiers from the list and click
"Generate Selected Reports" or "Generate ALL Reports"

Analysis completed successfully!
"""
        
        # Add error information if there are any errors
        if batch_result.errors:
            display_text += f"\n⚠️  Errors encountered:\n"
            for error in batch_result.errors:
                display_text += f"  • {error}\n"
        
        # Add individual soldier analysis summary
        if batch_result.soldier_results:
            display_text += f"\n📋 Individual Soldier Analysis:\n"
            for callsign, soldier_result in list(batch_result.soldier_results.items())[:10]:  # Show first 10
                status = soldier_result.analysis_status.value
                display_text += f"  • {callsign}: {status}\n"
            
            if len(batch_result.soldier_results) > 10:
                remaining = len(batch_result.soldier_results) - 10
                display_text += f"  ... and {remaining} more soldiers\n"
        
        self._update_display(display_text)
    
    def _update_display(self, text):
        """Update the display with new text"""
        self.results_text.config(state='normal')
        self.results_text.delete('1.0', 'end')
        self.results_text.insert('1.0', text)
        self.results_text.config(state='disabled')
    
    def pack(self, **kwargs):
        """Pack the analysis display frame"""
        self.frame.pack(**kwargs)