"""File selection component (patched to match MainWindow styling and event flow)"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os
from pathlib import Path

from src.core.event_bus import EventBus
from src.core.events import FileSelectedEvent, EventType, StatusUpdateEvent


class FileSelector:
    """Component for selecting and displaying data files (styled + event driven)"""

    def __init__(self, parent, event_bus: EventBus, colors: dict = None):
        self.parent = parent
        self.event_bus = event_bus
        # Fallback colors if none provided (keeps it usable outside MainWindow)
        self.colors = colors or {
            'primary_bg': '#1a1a1a',
            'secondary_bg': '#2d2d2d',
            'accent': '#0078d4',
            'accent_hover': '#106ebe',
            'text_primary': '#ffffff',
            'border': '#404040',
            'success': '#107c10',
            'warning': '#ff8c00',
            'error': '#d13438',
        }

        self._create_widgets()
        self._setup_layout()
        self._setup_event_handlers()

    def _create_widgets(self):
        """Create file selector widgets"""
        # Container frame
        self.frame = tk.Frame(self.parent, bg=self.colors['secondary_bg'])

        # Title
        self.title_label = tk.Label(
            self.frame,
            text="📁 Data File Selection",
            font=('Segoe UI', 14, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['secondary_bg']
        )

        # File path display
        self.file_path_var = tk.StringVar(value="No file selected")
        self.file_label = tk.Label(
            self.frame,
            textvariable=self.file_path_var,
            font=('Segoe UI', 10),
            bg=self.colors['secondary_bg'],
            fg=self.colors['text_primary'],
            wraplength=350,
            anchor='w',
            justify='left'
        )

        # Select file button
        self.select_button = tk.Button(
            self.frame,
            text="Select CSV File",
            font=('Segoe UI', 11, 'bold'),
            bg=self.colors['accent'],
            fg=self.colors['text_primary'],
            relief='flat',
            padx=30,
            pady=12,
            cursor='hand2',
            activebackground=self.colors['accent_hover'],
            command=self._select_file
        )

        # Data info section
        self.info_frame = tk.Frame(self.parent, bg=self.colors['secondary_bg'])
        self.info_title = tk.Label(
            self.info_frame,
            text="Data Information",
            font=('Segoe UI', 12, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['secondary_bg']
        )
        self.info_text = tk.Text(
            self.info_frame,
            height=6,
            font=('Consolas', 10),
            bg=self.colors['primary_bg'],
            fg=self.colors['text_primary'],
            wrap='word',
            relief='flat',
            state='disabled'
        )

    def _setup_layout(self):
        """Setup widget layout"""
        self.title_label.pack(anchor='w', pady=(0, 8))
        self.select_button.pack(anchor='w')
        self.file_label.pack(fill='x', pady=(8, 0))

        self.info_title.pack(anchor='w', pady=(10, 6))
        self.info_text.pack(fill='x')

    def _setup_event_handlers(self):
        """Setup event handlers"""
        self.event_bus.subscribe(
            EventType.DATA_LOADED.value,
            self._handle_data_loaded
        )

    def _select_file(self):
        """Handle file selection"""
        filetypes = [('CSV files', '*.csv'), ('All files', '*.*')]

        filename = filedialog.askopenfilename(
            title='Select Training Data CSV File',
            filetypes=filetypes,
            initialdir='.'
        )

        if not filename:
            # user cancelled; optional status ping
            self.event_bus.publish(StatusUpdateEvent(
                "File selection cancelled",
                level="info",
                source="FileSelector"
            ))
            return

        # Basic validation
        path = Path(filename)
        if path.suffix.lower() != '.csv':
            messagebox.showwarning("Invalid File", "Please select a .csv file.")
            self.event_bus.publish(StatusUpdateEvent(
                "Invalid file selected (not .csv)",
                level="warning",
                source="FileSelector"
            ))
            return

        if not path.exists() or path.stat().st_size == 0:
            messagebox.showerror("File Error", "The selected file is missing or empty." )
            self.event_bus.publish(StatusUpdateEvent(
                "Selected file missing or empty",
                level="error",
                source="FileSelector"
            ))
            return

        self.file_path_var.set(f"File: {os.path.basename(filename)}")


        # Let the rest of the system know
        self.event_bus.publish(StatusUpdateEvent(
            f"Loading data from {path.name}...",
            level="info",
            source="FileSelector"
        ))
        self.event_bus.publish(FileSelectedEvent(
            file_path=str(path),
            source="FileSelector"
        ))

    def _handle_data_loaded(self, event):
        """Handle data loaded event to update info display"""
        dataset = event.data['dataset']
        self._update_data_info(dataset)

        # Nice success ping
        self.event_bus.publish(StatusUpdateEvent(
            "Data loaded successfully",
            level="success",
            source="FileSelector"
        ))

    def _update_data_info(self, dataset):
        """Update data information display"""
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', 'end')

        info = [
            "DATA SUMMARY",
            "────────────────────────",
            f"Records: {getattr(dataset, 'total_records', 'N/A'):,}" if hasattr(dataset, 'total_records') else "Records: N/A",
            f"Soldiers: {getattr(dataset, 'total_soldiers', 'N/A')}",
            f"Columns: {len(dataset.data.columns) if hasattr(dataset, 'data') and hasattr(dataset.data, 'columns') else 'N/A'}",
            ""
        ]

        # Data quality issues
        issues = getattr(dataset, 'data_quality_issues', None)
        if issues:
            info.append("Data Quality Issues:")
            for issue in issues:
                info.append(f"  • {issue}")
            info.append("")

        # Column mapping
        mapping = getattr(dataset, 'column_mapping_applied', None)
        if mapping:
            try:
                count = len(mapping)
            except Exception:
                count = "some"
            info.append(f"Column Mapping Applied: {count}")

        self.info_text.insert('1.0', "\n".join(info))
        self.info_text.config(state='disabled')

    def pack(self, **kwargs):
        """Pack frames with sensible padding"""
        self.frame.pack(**kwargs)
        self.info_frame.pack(fill='x', pady=(10, 0))
