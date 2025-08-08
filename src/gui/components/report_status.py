# File: src/gui/components/report_status.py
"""Report generation status display component"""

import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

from src.core.event_bus import EventBus
from src.core.events import EventType


class ReportStatus:
    """Component for displaying report generation status"""
    
    def __init__(self, parent, event_bus: EventBus):
        self.parent = parent
        self.event_bus = event_bus
        
        self._create_widgets()
        self._setup_layout()
        self._setup_event_handlers()
    
    def _create_widgets(self):
        """Create report status widgets"""
        # Main frame
        self.frame = tk.LabelFrame(
            self.parent,
            text="📝 Generated Reports",
            font=('Arial', 12, 'bold'),
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        
        # Reports text widget with scrollbar
        self.reports_text = scrolledtext.ScrolledText(
            self.frame,
            height=15,
            font=('Courier', 9),
            bg='white',
            fg='#2c3e50',
            wrap='word',
            state='disabled'
        )
    
    def _setup_layout(self):
        """Setup widget layout"""
        self.reports_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def _setup_event_handlers(self):
        """Setup event handlers"""
        self.event_bus.subscribe(
            EventType.REPORT_GENERATION_REQUESTED.value,
            self._handle_report_requested
        )
        
        self.event_bus.subscribe(
            EventType.REPORT_STARTED.value,
            self._handle_report_started
        )
        
        self.event_bus.subscribe(
            EventType.REPORT_COMPLETED.value,
            self._handle_report_completed
        )
        
        self.event_bus.subscribe(
            EventType.REPORT_FAILED.value,
            self._handle_report_failed
        )
        
        self.event_bus.subscribe(
            EventType.BATCH_REPORT_COMPLETED.value,
            self._handle_batch_completed
        )
    
    def _handle_report_requested(self, event):
        """Handle report generation requested event"""
        count = event.data['count']
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"[{timestamp}] 🚀 Report generation requested for {count} soldiers\n"
        self._add_message(message)
    
    def _handle_report_started(self, event):
        """Handle individual report started event"""
        callsign = event.data.get('callsign', 'Unknown')
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"[{timestamp}] 🔄 Generating report for {callsign}...\n"
        self._add_message(message)
    
    def _handle_report_completed(self, event):
        """Handle individual report completed event"""
        callsign = event.data.get('callsign', 'Unknown')
        report_path = event.data.get('report_path', '')
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"[{timestamp}] ✅ {callsign} -> {report_path}\n"
        self._add_message(message)
    
    def _handle_report_failed(self, event):
        """Handle individual report failed event"""
        callsign = event.data.get('callsign', 'Unknown')
        error = event.data.get('error', 'Unknown error')
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"[{timestamp}] ❌ {callsign} - Error: {error}\n"
        self._add_message(message)
    
    def _handle_batch_completed(self, event):
        """Handle batch report completion event"""
        successful = event.data.get('successful', 0)
        failed = event.data.get('failed', 0)
        output_dir = event.data.get('output_directory', '')
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""[{timestamp}] 🎉 Batch generation complete!
    ✅ Successful: {successful}
    ❌ Failed: {failed}
    📁 Output: {output_dir}

"""
        self._add_message(message)
    
    def _add_message(self, message):
        """Add message to the reports display"""
        self.reports_text.config(state='normal')
        self.reports_text.insert('end', message)
        self.reports_text.see('end')
        self.reports_text.config(state='disabled')
    
    def pack(self, **kwargs):
        """Pack the report status frame"""
        self.frame.pack(**kwargs)