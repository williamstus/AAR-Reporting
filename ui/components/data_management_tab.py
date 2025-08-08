# ui/components/data_management_tab.py - Enhanced Data Management with CSV Loading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import threading
import time
import logging
from typing import Dict, List, Any, Optional

from core.event_bus import EventBus, Event, EventType
from core.models import (
    AnalysisDomain, DataQualityMetrics, SystemConfiguration,
    create_analysis_task, AnalysisLevel, TaskPriority
)

class DataManagementTab:
    """Enhanced data management tab with robust CSV loading functionality"""
    
    def __init__(self, parent, event_bus: EventBus, main_app):
        self.parent = parent
        self.event_bus = event_bus
        self.main_app = main_app
        self.logger = logging.getLogger(__name__)
        
        # Data management state
        self.current_data: Optional[pd.DataFrame] = None
        self.data_file_path: Optional[str] = None
        self.validation_result: Optional[Dict] = None
        self.selected_columns: List[str] = []
        self.selected_domain: Optional[AnalysisDomain] = None
        
        # Create the UI
        self._create_ui()
        
        # Setup event subscriptions
        self._setup_event_subscriptions()
        
        self.logger.info("Enhanced DataManagementTab initialized")
    
    def _create_ui(self):
        """Create the enhanced data management UI"""
        # Main frame
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title and instructions
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=(0, 15))
        
        title_label = ttk.Label(title_frame, text="📊 Data Management & Analysis", 
                               font=("Arial", 16, "bold"))
        title_label.pack(side='left')
        
        help_label = ttk.Label(title_frame, 
                              text="Load CSV files and configure analysis settings",
                              font=("Arial", 10), foreground="gray")
        help_label.pack(side='left', padx=(20, 0))
        
        # Create sections in logical order
        self._create_file_selection_section(main_frame)
        self._create_data_preview_section(main_frame)
        self._create_column_selection_section(main_frame)
        self._create_analysis_configuration_section(main_frame)
        self._create_action_buttons_section(main_frame)
        
        # Store main frame reference
        self.frame = main_frame
        
        # Initialize UI state
        self._update_ui_state()
    
    def _create_file_selection_section(self, parent):
        """Create enhanced file selection section"""
        file_frame = ttk.LabelFrame(parent, text="🗂️ Step 1: Select CSV Data File", padding="15")
        file_frame.pack(fill='x', pady=(0, 10))
        
        # Instructions
        instructions = ttk.Label(file_frame, 
                                text="Choose a CSV file containing your training data for analysis:",
                                font=("Arial", 10, "bold"))
        instructions.pack(anchor='w', pady=(0, 10))
        
        # File selection row
        file_select_frame = ttk.Frame(file_frame)
        file_select_frame.pack(fill='x', pady=(0, 10))
        
        # File path display
        self.file_path_var = tk.StringVar(value="No file selected")
        file_display_frame = ttk.Frame(file_select_frame)
        file_display_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(file_display_frame, text="Selected File:", font=("Arial", 9, "bold")).pack(side='left')
        self.file_path_label = ttk.Label(file_display_frame, textvariable=self.file_path_var, 
                                        foreground="gray", font=("Arial", 9))
        self.file_path_label.pack(side='left', padx=(10, 0))
        
        # Main action buttons
        button_frame = ttk.Frame(file_select_frame)
        button_frame.pack(fill='x', pady=(5, 0))
        
        # Browse button with icon
        self.browse_button = ttk.Button(button_frame, text="📁 Browse for CSV File", 
                                       command=self._browse_file, width=20)
        self.browse_button.pack(side='left', padx=(0, 10))
        
        # Load button
        self.load_button = ttk.Button(button_frame, text="📊 Load Data", 
                                     command=self._load_data, state='disabled', width=15)
        self.load_button.pack(side='left', padx=(0, 10))
        
        # Quick actions
        self.sample_button = ttk.Button(button_frame, text="🔄 Load Sample Data", 
                                       command=self._load_sample_data, width=18)
        self.sample_button.pack(side='right')
        
        # Progress and status
        progress_frame = ttk.Frame(file_frame)
        progress_frame.pack(fill='x', pady=(5, 0))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           mode='determinate')
        self.progress_bar.pack(fill='x', pady=(0, 5))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to load data")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var,
                                     font=("Arial", 9), foreground="blue")
        self.status_label.pack(anchor='w')
        
        # File info help
        help_frame = ttk.Frame(file_frame)
        help_frame.pack(fill='x', pady=(10, 0))
        
        help_text = ("💡 Supported: CSV files with headers like 'callsign', 'processedtimegmt', "
                    "'falldetected', 'casualtystate', 'latitude', 'longitude', 'temp', 'battery', etc.")
        ttk.Label(help_frame, text=help_text, font=("Arial", 8), foreground="gray",
                 wraplength=700).pack(anchor='w')
    
    def _create_data_preview_section(self, parent):
        """Create enhanced data preview section"""
        preview_frame = ttk.LabelFrame(parent, text="👁️ Data Preview", padding="10")
        preview_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Create notebook for different views
        self.preview_notebook = ttk.Notebook(preview_frame)
        self.preview_notebook.pack(fill='both', expand=True)
        
        # Data preview tab
        self.data_tab = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(self.data_tab, text="📋 Data Table")
        
        # Create treeview for data with improved layout
        tree_frame = ttk.Frame(self.data_tab)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Data treeview with styling
        self.data_tree = ttk.Treeview(tree_frame, show='headings', height=8)
        
        # Scrollbars with improved positioning
        v_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.data_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.data_tree.xview)
        self.data_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout for better control
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.data_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        # Data info tab
        self.info_tab = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(self.info_tab, text="📊 Data Information")
        
        # Data info text with improved styling
        info_frame = ttk.Frame(self.info_tab)
        info_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.data_info_text = tk.Text(info_frame, height=10, wrap='word', font=("Consolas", 10))
        info_scroll = ttk.Scrollbar(info_frame, orient='vertical', command=self.data_info_text.yview)
        self.data_info_text.configure(yscrollcommand=info_scroll.set)
        
        self.data_info_text.pack(side='left', fill='both', expand=True)
        info_scroll.pack(side='right', fill='y')
        
        # Add initial message
        self._show_initial_message()
    
    def _create_column_selection_section(self, parent):
        """Create enhanced column selection section"""
        column_frame = ttk.LabelFrame(parent, text="🎯 Step 2: Configure Analysis", padding="10")
        column_frame.pack(fill='x', pady=(0, 10))
        
        # Instructions
        instructions = ttk.Label(column_frame, 
                                text="Select analysis domain and choose data columns:",
                                font=("Arial", 10, "bold"))
        instructions.pack(anchor='w', pady=(0, 10))
        
        # Domain selection with improved layout
        config_frame = ttk.Frame(column_frame)
        config_frame.pack(fill='x', pady=(0, 10))
        
        # Domain selection
        domain_config_frame = ttk.Frame(config_frame)
        domain_config_frame.pack(side='left', fill='x', expand=True)
        
        ttk.Label(domain_config_frame, text="Analysis Domain:", font=("Arial", 9, "bold")).pack(side='left')
        self.domain_var = tk.StringVar()
        self.domain_combo = ttk.Combobox(domain_config_frame, textvariable=self.domain_var,
                                        values=[domain.value for domain in AnalysisDomain],
                                        state='readonly', width=25)
        self.domain_combo.pack(side='left', padx=(10, 0))
        self.domain_combo.bind('<<ComboboxSelected>>', self._on_domain_changed)
        
        # Set default domain
        self.domain_combo.set(AnalysisDomain.SOLDIER_SAFETY.value)
        self.domain_var.set(AnalysisDomain.SOLDIER_SAFETY.value)
        self.selected_domain = AnalysisDomain.SOLDIER_SAFETY
        
        # Analysis level selection
        level_config_frame = ttk.Frame(config_frame)
        level_config_frame.pack(side='right')
        
        ttk.Label(level_config_frame, text="Analysis Level:", font=("Arial", 9, "bold")).pack(side='left')
        self.level_var = tk.StringVar(value=AnalysisLevel.INDIVIDUAL.value)
        level_combo = ttk.Combobox(level_config_frame, textvariable=self.level_var,
                                 values=[level.value for level in AnalysisLevel],
                                 state='readonly', width=15)
        level_combo.pack(side='left', padx=(10, 0))
        
        # Column selection with improved layout
        columns_frame = ttk.Frame(column_frame)
        columns_frame.pack(fill='x', pady=(10, 0))
        
        # Available columns
        available_frame = ttk.Frame(columns_frame)
        available_frame.pack(side='left', fill='both', expand=True)
        
        ttk.Label(available_frame, text="Available Columns:", font=("Arial", 9, "bold")).pack(anchor='w')
        self.available_listbox = tk.Listbox(available_frame, height=6, selectmode='extended')
        self.available_listbox.pack(fill='both', expand=True, pady=(5, 0))
        
        # Control buttons with improved styling
        control_frame = ttk.Frame(columns_frame)
        control_frame.pack(side='left', fill='y', padx=(15, 15))
        
        # Add vertical centering
        ttk.Label(control_frame, text="").pack(pady=10)
        
        ttk.Button(control_frame, text="Add →", command=self._add_columns, width=12).pack(pady=2)
        ttk.Button(control_frame, text="← Remove", command=self._remove_columns, width=12).pack(pady=2)
        ttk.Button(control_frame, text="Add All →", command=self._add_all_columns, width=12).pack(pady=2)
        ttk.Button(control_frame, text="← Remove All", command=self._remove_all_columns, width=12).pack(pady=2)
        
        # Selected columns
        selected_frame = ttk.Frame(columns_frame)
        selected_frame.pack(side='left', fill='both', expand=True)
        
        ttk.Label(selected_frame, text="Selected Columns:", font=("Arial", 9, "bold")).pack(anchor='w')
        self.selected_listbox = tk.Listbox(selected_frame, height=6, selectmode='extended')
        self.selected_listbox.pack(fill='both', expand=True, pady=(5, 0))
        
        # Selection help
        help_frame = ttk.Frame(column_frame)
        help_frame.pack(fill='x', pady=(10, 0))
        
        help_text = ("💡 Tip: Required columns are automatically selected based on your chosen domain. "
                    "You can add additional columns for enhanced analysis.")
        ttk.Label(help_frame, text=help_text, font=("Arial", 8), foreground="gray",
                 wraplength=700).pack(anchor='w')
    
    def _create_analysis_configuration_section(self, parent):
        """Create analysis configuration section"""
        config_frame = ttk.LabelFrame(parent, text="⚙️ Step 3: Analysis Options", padding="10")
        config_frame.pack(fill='x', pady=(0, 10))
        
        # Configuration options
        options_frame = ttk.Frame(config_frame)
        options_frame.pack(fill='x')
        
        # Validation option
        self.validate_data_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Validate data quality", 
                       variable=self.validate_data_var).pack(side='left')
        
        # Real-time processing option
        self.real_time_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Enable real-time processing", 
                       variable=self.real_time_var).pack(side='left', padx=(20, 0))
        
        # Priority selection
        ttk.Label(options_frame, text="Priority:", font=("Arial", 9)).pack(side='left', padx=(20, 5))
        self.priority_var = tk.StringVar(value=TaskPriority.NORMAL.value)
        priority_combo = ttk.Combobox(options_frame, textvariable=self.priority_var,
                                     values=[priority.value for priority in TaskPriority],
                                     state='readonly', width=12)
        priority_combo.pack(side='left')
    
    def _create_action_buttons_section(self, parent):
        """Create enhanced action buttons section"""
        action_frame = ttk.LabelFrame(parent, text="🚀 Step 4: Execute Analysis", padding="10")
        action_frame.pack(fill='x')
        
        # Instructions
        instructions = ttk.Label(action_frame, 
                                text="Ready to analyze? Start your analysis or manage your data:",
                                font=("Arial", 10, "bold"))
        instructions.pack(anchor='w', pady=(0, 10))
        
        # Main action buttons
        main_buttons = ttk.Frame(action_frame)
        main_buttons.pack(fill='x', pady=(0, 10))
        
        # Primary action - Start Analysis
        self.analyze_button = ttk.Button(main_buttons, text="🚀 Start Analysis", 
                                        command=self._start_analysis, state='disabled', width=20)
        self.analyze_button.pack(side='left', padx=(0, 10))
        
        # Quick validation
        self.validate_button = ttk.Button(main_buttons, text="🔍 Validate Data", 
                                         command=self._validate_data, state='disabled', width=15)
        self.validate_button.pack(side='left', padx=(0, 10))
        
        # Analysis info
        self.analysis_info_var = tk.StringVar(value="Load data and select columns to enable analysis")
        analysis_info_label = ttk.Label(main_buttons, textvariable=self.analysis_info_var,
                                       font=("Arial", 9), foreground="gray")
        analysis_info_label.pack(side='left', padx=(20, 0))
        
        # Secondary buttons
        secondary_buttons = ttk.Frame(action_frame)
        secondary_buttons.pack(fill='x')
        
        # Data management buttons
        self.save_button = ttk.Button(secondary_buttons, text="💾 Save Data", 
                                     command=self._save_data, state='disabled', width=15)
        self.save_button.pack(side='left', padx=(0, 10))
        
        self.export_button = ttk.Button(secondary_buttons, text="📤 Export Selected", 
                                       command=self._export_selected_data, state='disabled', width=18)
        self.export_button.pack(side='left', padx=(0, 10))
        
        self.clear_button = ttk.Button(secondary_buttons, text="🗑️ Clear All", 
                                      command=self._clear_data, width=15)
        self.clear_button.pack(side='left', padx=(0, 10))
        
        # Progress indicator for analysis
        self.analysis_progress_var = tk.StringVar(value="")
        analysis_progress_label = ttk.Label(secondary_buttons, textvariable=self.analysis_progress_var,
                                           font=("Arial", 9), foreground="blue")
        analysis_progress_label.pack(side='right')
    
    def _setup_event_subscriptions(self):
        """Setup event subscriptions"""
        try:
            self.event_bus.subscribe(EventType.ANALYSIS_COMPLETED, self._on_analysis_completed)
            self.event_bus.subscribe(EventType.DATA_VALIDATION_COMPLETED, self._on_data_validated)
        except Exception as e:
            self.logger.error(f"Error setting up event subscriptions: {e}")
    
    def _browse_file(self):
        """Enhanced file browsing with better user experience"""
        try:
            # Show file dialog with improved options
            initial_dir = Path.cwd()
            if Path("data").exists():
                initial_dir = Path("data")
            
            file_path = filedialog.askopenfilename(
                title="Select Training Data CSV File",
                initialdir=initial_dir,
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                self.data_file_path = file_path
                filename = Path(file_path).name
                self.file_path_var.set(filename)
                self.file_path_label.config(foreground="blue")
                self.load_button.config(state='normal')
                
                # Show file info
                try:
                    file_size = Path(file_path).stat().st_size
                    size_mb = file_size / (1024 * 1024)
                    self.status_var.set(f"✅ File selected: {filename} ({size_mb:.1f} MB) - Click 'Load Data' to continue")
                    self.status_label.config(foreground="green")
                except:
                    self.status_var.set(f"✅ File selected: {filename} - Click 'Load Data' to continue")
                    self.status_label.config(foreground="green")
                
                self.logger.info(f"File selected: {file_path}")
        
        except Exception as e:
            self.logger.error(f"Error in file browsing: {e}")
            messagebox.showerror("Error", f"Error selecting file: {str(e)}")
    
    def _load_data(self):
        """Enhanced data loading with better error handling and progress indication"""
        if not self.data_file_path:
            messagebox.showerror("Error", "Please select a file first")
            return
        
        # Update UI for loading state
        self.status_var.set("Loading data...")
        self.status_label.config(foreground="blue")
        self.progress_var.set(0)
        self.load_button.config(state='disabled')
        
        def load_worker():
            try:
                # Simulate progress updates
                for i in range(1, 6):
                    time.sleep(0.1)
                    self.progress_var.set(i * 20)
                
                # Load data based on file type
                if self.data_file_path.endswith('.csv'):
                    self.current_data = pd.read_csv(self.data_file_path)
                elif self.data_file_path.endswith('.xlsx'):
                    self.current_data = pd.read_excel(self.data_file_path)
                else:
                    raise ValueError("Unsupported file format")
                
                # Complete progress
                self.progress_var.set(100)
                
                # Update UI on main thread
                self.parent.after(0, self._on_data_loaded_success)
                
            except Exception as e:
                self.logger.error(f"Error loading data: {e}")
                self.parent.after(0, lambda: self._on_data_loaded_error(str(e)))
        
        # Start loading in background thread
        loading_thread = threading.Thread(target=load_worker)
        loading_thread.daemon = True
        loading_thread.start()
    
    def _on_data_loaded_success(self):
        """Handle successful data loading"""
        try:
            # Update status
            self.status_var.set(f"✅ Successfully loaded {len(self.current_data)} records with {len(self.current_data.columns)} columns")
            self.status_label.config(foreground="green")
            
            # Update all UI components
            self._update_data_preview()
            self._update_column_lists()
            self._update_data_info()
            
            # Enable buttons
            self.validate_button.config(state='normal')
            self.save_button.config(state='normal')
            self.export_button.config(state='normal')
            self.load_button.config(state='normal')
            
            # Auto-select required columns
            self._auto_select_required_columns()
            
            # Update analysis button state
            self._update_analysis_button()
            
            # Show success message
            messagebox.showinfo("Success", f"Data loaded successfully!\n\n"
                                f"Records: {len(self.current_data)}\n"
                                f"Columns: {len(self.current_data.columns)}")
            
            self.logger.info("Data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error in data loaded success handler: {e}")
            self._on_data_loaded_error(str(e))
    
    def _on_data_loaded_error(self, error_message: str):
        """Handle data loading errors"""
        self.status_var.set(f"❌ Error: {error_message}")
        self.status_label.config(foreground="red")
        self.progress_var.set(0)
        self.load_button.config(state='normal')
        
        messagebox.showerror("Loading Error", f"Failed to load data:\n{error_message}")
    
    def _load_sample_data(self):
        """Load sample data for demonstration"""
        try:
            # Create sample training data
            sample_data = self._create_sample_data()
            
            # Save to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                sample_data.to_csv(f.name, index=False)
                self.data_file_path = f.name
            
            # Update UI
            self.file_path_var.set("sample_training_data.csv")
            self.file_path_label.config(foreground="blue")
            self.load_button.config(state='normal')
            self.status_var.set("📊 Sample data created - Click 'Load Data' to continue")
            self.status_label.config(foreground="blue")
            
            messagebox.showinfo("Sample Data", 
                              f"Sample training data created with {len(sample_data)} records\n"
                              f"Columns: {', '.join(sample_data.columns[:5])}...")
            
        except Exception as e:
            self.logger.error(f"Error creating sample data: {e}")
            messagebox.showerror("Error", f"Failed to create sample data: {str(e)}")
    
    def _create_sample_data(self):
        """Create realistic sample training data"""
        import numpy as np
        from datetime import datetime, timedelta
        
        # Create realistic sample data based on your requirements
        num_records = 100
        units = ['Unit_108', 'Unit_134', 'Unit_156', 'Unit_178']
        
        # Base time
        base_time = datetime.now() - timedelta(minutes=30)
        
        data = []
        for i in range(num_records):
            # Unit selection with Unit_108 having more activity
            if i < 40:
                unit = 'Unit_108'  # High activity unit
            else:
                unit = np.random.choice(units)
            
            # Time progression
            time_offset = (i / num_records) * 30 * 60  # 30 minutes in seconds
            timestamp = base_time + timedelta(seconds=time_offset)
            
            # Realistic data generation
            record = {
                'callsign': unit,
                'processedtimegmt': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'latitude': 40.7128 + np.random.uniform(-0.01, 0.01),
                'longitude': -74.0060 + np.random.uniform(-0.01, 0.01),
                'temp': np.random.normal(25, 3),
                'battery': max(0, 100 - (i * 0.2) + np.random.uniform(-5, 5)),
                'falldetected': 'Yes' if (unit == 'Unit_108' and np.random.random() < 0.2) else 'No',
                'casualtystate': self._generate_casualty_state(unit, i),
                'rssi': max(-50, min(50, np.random.normal(20, 10))),
                'mcs': np.random.randint(3, 8),
                'nexthop': f'Router_{np.random.randint(1, 4)}',
                'steps': np.random.randint(100, 400),
                'posture': np.random.choice(['Standing', 'Prone', 'Unknown'], p=[0.4, 0.4, 0.2]),
                'squad': 'Alpha' if unit in ['Unit_108', 'Unit_134'] else 'Bravo'
            }
            data.append(record)
        
        return pd.DataFrame(data)
    
    def _generate_casualty_state(self, unit: str, index: int) -> str:
        """Generate realistic casualty states"""
        if unit == 'Unit_108':
            # High-risk unit with casualties
            if index % 25 == 0:
                return 'KILLED'
            elif index % 15 == 0:
                return 'FALL ALERT'
            elif index % 35 == 0:
                return 'RESURRECTED'
            else:
                return 'GOOD'
        else:
            # Low-risk units
            if index % 50 == 0:
                return 'FALL ALERT'
            else:
                return 'GOOD'
    
    def _update_data_preview(self):
        """Update data preview display"""
        if self.current_data is None:
            return
        
        # Clear existing data
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        # Set columns
        columns = list(self.current_data.columns)
        self.data_tree['columns'] = columns
        
        # Configure column headings and widths
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=100, minwidth=50)
        
        # Add data (first 100 rows for performance)
        for idx, row in self.current_data.head(100).iterrows():
            values = [str(val) if pd.notna(val) else "" for val in row]
            self.data_tree.insert('', 'end', values=values)
    
    def _update_column_lists(self):
        """Update available and selected column lists"""
        if self.current_data is None:
            return
        
        # Update available columns
        self.available_listbox.delete(0, tk.END)
        for col in self.current_data.columns:
            self.available_listbox.insert(tk.END, col)
        
        # Clear selected columns
        self.selected_listbox.delete(0, tk.END)
        self.selected_columns = []
    
    def _update_data_info(self):
        """Update data information display"""
        if self.current_data is None:
            self._show_initial_message()
            return
        
        info_text = f"📊 Dataset Information\n"
        info_text += "=" * 50 + "\n\n"
        
        info_text += f"Shape: {self.current_data.shape[0]} rows × {self.current_data.shape[1]} columns\n"
        info_text += f"Memory Usage: {self.current_data.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB\n\n"
        
        info_text += "📋 Column Information:\n"
        info_text += "-" * 30 + "\n"
        for col in self.current_data.columns:
            dtype = self.current_data[col].dtype
            null_count = self.current_data[col].isnull().sum()
            null_pct = (null_count / len(self.current_data)) * 100
            unique_count = self.current_data[col].nunique()
            
            info_text += f"{col}:\n"
            info_text += f"  Type: {dtype}\n"
            info_text += f"  Missing: {null_count} ({null_pct:.1f}%)\n"
            info_text += f"  Unique: {unique_count}\n\n"
        
        info_text += "🔍 Data Quality Summary:\n"
        info_text += "-" * 30 + "\n"
        info_text += f"Total missing values: {self.current_data.isnull().sum().sum()}\n"
        info_text += f"Complete rows: {len(self.current_data.dropna())}\n"
        info_text += f"Completeness: {(len(self.current_data.dropna()) / len(self.current_data)) * 100:.1f}%\n"
        
        self.data_info_text.delete(1.0, tk.END)
        self.data_info_text.insert(tk.END, info_text)
    
    def _show_initial_message(self):
        """Show initial message in data info"""
        initial_message = """
📊 Data Management System
========================

Welcome to the AAR Data Management System!

🔄 Getting Started:
1. Click 'Browse for CSV File' to select your training data
2. Or click 'Load Sample Data' to try with demonstration data
3. Preview your data in the table view
4. Select analysis domain and configure columns
5. Start your analysis!

📋 Supported Data Format:
- CSV files with headers
- Required columns vary by analysis domain
- Common columns: callsign, processedtimegmt, latitude, longitude
- Safety domain: falldetected, casualtystate, temp
- Network domain: rssi, mcs, nexthop
- Activity domain: steps, posture

💡 Tips:
- Use descriptive column names
- Ensure consistent data formats
- Remove unnecessary columns before analysis
- Check data quality before processing
"""
        
        self.data_info_text.delete(1.0, tk.END)
        self.data_info_text.insert(tk.END, initial_message)
    
    def _auto_select_required_columns(self):
        """Auto-select required columns for the selected domain"""
        if self.selected_domain and self.current_data is not None:
            required_columns = self._get_required_columns_for_domain(self.selected_domain)
            available_columns = list(self.current_data.columns)
            
            # Add required columns that are available
            for col in required_columns:
                if col in available_columns and col not in self.selected_columns:
                    self.selected_columns.append(col)
                    self.selected_listbox.insert(tk.END, col)
        
        self._update_analysis_button()
    
    def _get_required_columns_for_domain(self, domain: AnalysisDomain) -> List[str]:
        """Get required columns for a specific domain"""
        domain_columns = {
            AnalysisDomain.SOLDIER_SAFETY: ['callsign', 'falldetected', 'casualtystate', 'processedtimegmt'],
            AnalysisDomain.NETWORK_PERFORMANCE: ['callsign', 'processedtimegmt', 'rssi', 'mcs', 'nexthop'],
            AnalysisDomain.SOLDIER_ACTIVITY: ['callsign', 'processedtimegmt', 'steps', 'posture'],
            AnalysisDomain.EQUIPMENT_MANAGEMENT: ['callsign', 'processedtimegmt', 'battery']
        }
        return domain_columns.get(domain, ['callsign', 'processedtimegmt'])
    
    def _add_columns(self):
        """Add selected columns to selected list"""
        selected_indices = self.available_listbox.curselection()
        for idx in selected_indices:
            col = self.available_listbox.get(idx)
            if col not in self.selected_columns:
                self.selected_columns.append(col)
                self.selected_listbox.insert(tk.END, col)
        
        self._update_analysis_button()
    
    def _remove_columns(self):
        """Remove selected columns from selected list"""
        selected_indices = self.selected_listbox.curselection()
        for idx in reversed(selected_indices):
            col = self.selected_listbox.get(idx)
            if col in self.selected_columns:
                self.selected_columns.remove(col)
                self.selected_listbox.delete(idx)
        
        self._update_analysis_button()
    
    def _add_all_columns(self):
        """Add all columns to selected list"""
        if self.current_data is None:
            return
        
        self.selected_columns = list(self.current_data.columns)
        self.selected_listbox.delete(0, tk.END)
        for col in self.selected_columns:
            self.selected_listbox.insert(tk.END, col)
        
        self._update_analysis_button()
    
    def _remove_all_columns(self):
        """Remove all columns from selected list"""
        self.selected_columns = []
        self.selected_listbox.delete(0, tk.END)
        self._update_analysis_button()
    
    def _on_domain_changed(self, event=None):
        """Handle domain selection change"""
        domain_str = self.domain_var.get()
        if domain_str:
            self.selected_domain = AnalysisDomain(domain_str)
            self._auto_select_required_columns()
    
    def _update_analysis_button(self):
        """Update analysis button state"""
        if (self.current_data is not None and 
            self.selected_columns and 
            self.selected_domain):
            self.analyze_button.config(state='normal')
            self.analysis_info_var.set(f"✅ Ready: {self.selected_domain.value} analysis with {len(self.selected_columns)} columns")
        else:
            self.analyze_button.config(state='disabled')
            if self.current_data is None:
                self.analysis_info_var.set("❌ Load data first")
            elif not self.selected_columns:
                self.analysis_info_var.set("❌ Select columns for analysis")
            elif not self.selected_domain:
                self.analysis_info_var.set("❌ Select an analysis domain")
            else:
                self.analysis_info_var.set("❌ Complete all steps to enable analysis")
    
    def _update_ui_state(self):
        """Update UI state based on current data and selections"""
        self._update_analysis_button()
        
        # Update button states
        has_data = self.current_data is not None
        self.validate_button.config(state='normal' if has_data else 'disabled')
        self.save_button.config(state='normal' if has_data else 'disabled')
        self.export_button.config(state='normal' if has_data else 'disabled')
    
    def _validate_data(self):
        """Validate the current data"""
        if self.current_data is None:
            messagebox.showerror("Error", "Please load data first")
            return
        
        try:
            # Simple validation
            issues = []
            
            # Check for missing data
            missing_data = self.current_data.isnull().sum()
            for col, count in missing_data.items():
                if count > 0:
                    pct = (count / len(self.current_data)) * 100
                    issues.append(f"Column '{col}' has {count} missing values ({pct:.1f}%)")
            
            # Check data types
            for col in self.current_data.columns:
                if col in ['processedtimegmt', 'timestamp']:
                    try:
                        pd.to_datetime(self.current_data[col])
                    except:
                        issues.append(f"Column '{col}' contains invalid datetime values")
            
            # Show results
            if issues:
                result_msg = f"Data validation found {len(issues)} issues:\n\n" + "\n".join(issues[:10])
                if len(issues) > 10:
                    result_msg += f"\n... and {len(issues) - 10} more issues"
                messagebox.showwarning("Validation Results", result_msg)
            else:
                messagebox.showinfo("Validation Results", "✅ Data validation passed successfully!")
            
        except Exception as e:
            self.logger.error(f"Error validating data: {e}")
            messagebox.showerror("Error", f"Error validating data: {str(e)}")
    
    def _start_analysis(self):
        """Start analysis with selected data and columns"""
        if self.current_data is None:
            messagebox.showerror("Error", "Please load data first")
            return
        
        if not self.selected_columns:
            messagebox.showerror("Error", "Please select columns for analysis")
            return
        
        if not self.selected_domain:
            messagebox.showerror("Error", "Please select an analysis domain")
            return
        
        try:
            # Filter data to selected columns
            analysis_data = self.current_data[self.selected_columns].copy()
            
            # Store data in main application for analysis
            self.main_app.current_data = analysis_data
            self.main_app.selected_domains = [self.selected_domain]
            self.main_app.selected_columns = self.selected_columns
            
            # Create analysis task
            task = create_analysis_task(
                domain=self.selected_domain,
                level=AnalysisLevel(self.level_var.get()),
                priority=TaskPriority(self.priority_var.get()),
                config={
                    'selected_columns': self.selected_columns,
                    'data_source': self.data_file_path,
                    'validate_data': self.validate_data_var.get(),
                    'real_time': self.real_time_var.get()
                }
            )
            
            # Submit task through orchestrator
            if hasattr(self.main_app, 'orchestrator'):
                task_id = self.main_app.orchestrator.submit_task(task)
                self.analysis_progress_var.set(f"✅ Analysis started: {task_id[:8]}...")
                
                # Show success message
                messagebox.showinfo("Analysis Started", 
                                  f"Analysis task submitted successfully!\n\n"
                                  f"Task ID: {task_id[:8]}...\n"
                                  f"Domain: {self.selected_domain.value}\n"
                                  f"Level: {self.level_var.get()}\n"
                                  f"Priority: {self.priority_var.get()}\n"
                                  f"Columns: {len(self.selected_columns)}\n"
                                  f"Records: {len(analysis_data)}")
            else:
                messagebox.showinfo("Analysis Started", 
                                  f"Analysis data prepared for {self.selected_domain.value}")
            
        except Exception as e:
            self.logger.error(f"Error starting analysis: {e}")
            messagebox.showerror("Error", f"Failed to start analysis: {str(e)}")
    
    def _save_data(self):
        """Save processed data"""
        if self.current_data is None:
            messagebox.showerror("Error", "No data to save")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                title="Save Processed Data",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
            )
            
            if file_path:
                data_to_save = self.current_data
                
                if file_path.endswith('.xlsx'):
                    data_to_save.to_excel(file_path, index=False)
                else:
                    data_to_save.to_csv(file_path, index=False)
                
                messagebox.showinfo("Success", f"Data saved to {file_path}")
                
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
            messagebox.showerror("Error", f"Error saving data: {str(e)}")
    
    def _export_selected_data(self):
        """Export selected columns data"""
        if self.current_data is None:
            messagebox.showerror("Error", "No data to export")
            return
        
        if not self.selected_columns:
            messagebox.showerror("Error", "Please select columns to export")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Selected Data",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
            )
            
            if file_path:
                data_to_export = self.current_data[self.selected_columns]
                
                if file_path.endswith('.xlsx'):
                    data_to_export.to_excel(file_path, index=False)
                else:
                    data_to_export.to_csv(file_path, index=False)
                
                messagebox.showinfo("Success", f"Selected data exported to {file_path}")
                
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            messagebox.showerror("Error", f"Error exporting data: {str(e)}")
    
    def _clear_data(self):
        """Clear all data and reset UI"""
        if messagebox.askyesno("Clear Data", "Are you sure you want to clear all data?"):
            try:
                # Clear data
                self.current_data = None
                self.data_file_path = None
                self.validation_result = None
                self.selected_columns = []
                self.selected_domain = AnalysisDomain.SOLDIER_SAFETY
                
                # Reset UI
                self.file_path_var.set("No file selected")
                self.file_path_label.config(foreground="gray")
                self.status_var.set("Ready to load data")
                self.status_label.config(foreground="blue")
                self.analysis_info_var.set("Load data and select columns to enable analysis")
                self.analysis_progress_var.set("")
                self.progress_var.set(0)
                self.domain_var.set(AnalysisDomain.SOLDIER_SAFETY.value)
                self.level_var.set(AnalysisLevel.INDIVIDUAL.value)
                self.priority_var.set(TaskPriority.NORMAL.value)
                
                # Clear displays
                for item in self.data_tree.get_children():
                    self.data_tree.delete(item)
                
                self.available_listbox.delete(0, tk.END)
                self.selected_listbox.delete(0, tk.END)
                
                # Reset data info
                self._show_initial_message()
                
                # Update button states
                self._update_ui_state()
                
                self.logger.info("Data cleared successfully")
                
            except Exception as e:
                self.logger.error(f"Error clearing data: {e}")
                messagebox.showerror("Error", f"Error clearing data: {str(e)}")
    
    def _on_analysis_completed(self, event):
        """Handle analysis completion events"""
        self.analysis_progress_var.set("✅ Analysis completed")
    
    def _on_data_validated(self, event):
        """Handle data validation completion events"""
        # Update UI based on validation results
        pass
    
    # Methods for external access
    def get_current_data(self) -> Optional[pd.DataFrame]:
        """Get current loaded data"""
        return self.current_data
    
    def get_selected_columns(self) -> List[str]:
        """Get selected columns"""
        return self.selected_columns
    
    def get_selected_domain(self) -> Optional[AnalysisDomain]:
        """Get selected domain"""
        return self.selected_domain
    
    def set_data(self, data: pd.DataFrame):
        """Set data programmatically"""
        self.current_data = data
        self._on_data_loaded_success()
