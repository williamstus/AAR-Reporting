# simplified_csv_loader.py - Standalone CSV loader module
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging

class SimplifiedCSVLoader:
    """Simplified CSV loader for AAR system"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AAR System - CSV Data Loader")
        self.logger = logging.getLogger(__name__)
        
        # Data management state
        self.current_data = None
        self.data_file_path = None
        self.selected_columns = []
        
        # Create UI
        self.create_ui()
        
        self.logger.info("SimplifiedCSVLoader initialized")
    
    def create_ui(self):
        """Create the user interface"""
        # Configure root
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure main frame
        main_frame.grid_rowconfigure(2, weight=1)  # Data preview area
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, 
                               text="📊 AAR System - CSV Data Loader", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # File selection section
        self.create_file_section(main_frame)
        
        # Data preview section
        self.create_preview_section(main_frame)
        
        # Action buttons section
        self.create_action_section(main_frame)
    
    def create_file_section(self, parent):
        """Create file selection section"""
        file_frame = ttk.LabelFrame(parent, text="🗂️ Select CSV File", padding="15")
        file_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # Configure file frame
        file_frame.grid_columnconfigure(0, weight=1)
        
        # File path display
        self.file_path_var = tk.StringVar(value="No file selected")
        file_path_label = ttk.Label(file_frame, textvariable=self.file_path_var, 
                                   font=("Arial", 10))
        file_path_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # Buttons frame
        button_frame = ttk.Frame(file_frame)
        button_frame.grid(row=1, column=0, sticky="ew")
        
        # Browse button
        self.browse_button = ttk.Button(button_frame, text="📁 Browse CSV File", 
                                       command=self.browse_file, width=20)
        self.browse_button.grid(row=0, column=0, padx=(0, 10))
        
        # Load button
        self.load_button = ttk.Button(button_frame, text="📊 Load Data", 
                                     command=self.load_data, state='disabled', width=15)
        self.load_button.grid(row=0, column=1, padx=(0, 10))
        
        # Sample data button
        self.sample_button = ttk.Button(button_frame, text="🔄 Create Sample Data", 
                                       command=self.create_sample_data, width=20)
        self.sample_button.grid(row=0, column=2)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to load data")
        status_label = ttk.Label(file_frame, textvariable=self.status_var,
                                font=("Arial", 9), foreground="blue")
        status_label.grid(row=2, column=0, sticky="w", pady=(10, 0))
    
    def create_preview_section(self, parent):
        """Create data preview section"""
        preview_frame = ttk.LabelFrame(parent, text="👁️ Data Preview", padding="10")
        preview_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        
        # Configure preview frame
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        # Create notebook for different views
        self.notebook = ttk.Notebook(preview_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        
        # Data table tab
        self.create_data_table_tab()
        
        # Data info tab
        self.create_data_info_tab()
        
        # Show initial message
        self.show_initial_message()
    
    def create_data_table_tab(self):
        """Create data table tab"""
        table_frame = ttk.Frame(self.notebook)
        self.notebook.add(table_frame, text="📋 Data Table")
        
        # Configure table frame
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview
        self.data_tree = ttk.Treeview(table_frame, show='headings', height=15)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.data_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient='horizontal', command=self.data_tree.xview)
        self.data_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.data_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
    
    def create_data_info_tab(self):
        """Create data info tab"""
        info_frame = ttk.Frame(self.notebook)
        self.notebook.add(info_frame, text="📊 Data Info")
        
        # Configure info frame
        info_frame.grid_rowconfigure(0, weight=1)
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Create text widget
        self.info_text = tk.Text(info_frame, wrap='word', font=("Consolas", 10))
        info_scroll = ttk.Scrollbar(info_frame, orient='vertical', command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scroll.set)
        
        # Grid layout
        self.info_text.grid(row=0, column=0, sticky='nsew')
        info_scroll.grid(row=0, column=1, sticky='ns')
    
    def create_action_section(self, parent):
        """Create action buttons section"""
        action_frame = ttk.LabelFrame(parent, text="🚀 Actions", padding="10")
        action_frame.grid(row=3, column=0, sticky="ew")
        
        # Configure action frame
        action_frame.grid_columnconfigure(0, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(action_frame)
        button_frame.grid(row=0, column=0, sticky="ew")
        
        # Analysis info
        self.analysis_info_var = tk.StringVar(value="Load data to enable analysis")
        analysis_info_label = ttk.Label(button_frame, textvariable=self.analysis_info_var,
                                       font=("Arial", 9), foreground="gray")
        analysis_info_label.grid(row=0, column=0, sticky="w")
        
        # Action buttons
        self.validate_button = ttk.Button(button_frame, text="🔍 Validate Data", 
                                         command=self.validate_data, state='disabled', width=15)
        self.validate_button.grid(row=0, column=1, padx=(10, 0))
        
        self.analyze_button = ttk.Button(button_frame, text="📊 Analyze Data", 
                                        command=self.analyze_data, state='disabled', width=15)
        self.analyze_button.grid(row=0, column=2, padx=(10, 0))
        
        self.export_button = ttk.Button(button_frame, text="📤 Export Data", 
                                       command=self.export_data, state='disabled', width=15)
        self.export_button.grid(row=0, column=3, padx=(10, 0))
        
        # Status info
        self.progress_var = tk.StringVar(value="")
        progress_label = ttk.Label(action_frame, textvariable=self.progress_var,
                                  font=("Arial", 9), foreground="blue")
        progress_label.grid(row=1, column=0, sticky="w", pady=(10, 0))
    
    def show_initial_message(self):
        """Show initial message in info tab"""
        initial_message = """
📊 AAR System - CSV Data Loader
===============================

Welcome to the AAR (After Action Review) CSV Data Loader!

🔄 Getting Started:
1. Click 'Browse CSV File' to select your training data
2. Or click 'Create Sample Data' to generate test data
3. Click 'Load Data' to load the selected file
4. Preview your data in the 'Data Table' tab
5. Use the actions below to validate, analyze, or export

📋 Supported Data Columns:
• callsign - Unit identifier
• processedtimegmt - Timestamp
• latitude, longitude - GPS coordinates
• temp - Temperature readings
• battery - Battery level
• falldetected - Fall detection events
• casualtystate - Casualty status
• rssi - Signal strength
• mcs - Modulation coding scheme
• steps - Step count
• posture - Soldier posture

💡 Data Requirements:
• CSV format with headers
• Required: callsign, processedtimegmt
• Optional: All other columns enhance analysis

🎯 Analysis Domains:
• Soldier Safety - Fall detection, casualty tracking
• Network Performance - Signal strength, connectivity
• Activity Monitoring - Movement, posture analysis
• Equipment Status - Battery, system health

Select your CSV file to begin!
"""
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, initial_message)
        self.info_text.config(state='disabled')
    
    def browse_file(self):
        """Browse for CSV file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Select CSV Training Data File",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                self.data_file_path = file_path
                filename = Path(file_path).name
                self.file_path_var.set(f"Selected: {filename}")
                self.load_button.config(state='normal')
                self.status_var.set(f"✅ File selected: {filename} - Click 'Load Data' to continue")
                
                self.logger.info(f"File selected: {file_path}")
        
        except Exception as e:
            self.logger.error(f"Error browsing file: {e}")
            messagebox.showerror("Error", f"Error selecting file: {str(e)}")
    
    def load_data(self):
        """Load CSV data"""
        if not self.data_file_path:
            messagebox.showerror("Error", "Please select a file first")
            return
        
        try:
            # Update status
            self.status_var.set("Loading data...")
            self.load_button.config(state='disabled')
            self.root.update_idletasks()
            
            # Load data
            if self.data_file_path.endswith('.csv'):
                self.current_data = pd.read_csv(self.data_file_path)
            elif self.data_file_path.endswith('.xlsx'):
                self.current_data = pd.read_excel(self.data_file_path)
            else:
                self.current_data = pd.read_csv(self.data_file_path)
            
            # Update UI
            self.update_data_display()
            self.update_data_info()
            
            # Enable buttons
            self.validate_button.config(state='normal')
            self.analyze_button.config(state='normal')
            self.export_button.config(state='normal')
            self.load_button.config(state='normal')
            
            # Update status
            self.status_var.set(f"✅ Loaded {len(self.current_data)} records with {len(self.current_data.columns)} columns")
            self.analysis_info_var.set(f"✅ Data ready: {len(self.current_data)} records, {len(self.current_data.columns)} columns")
            
            # Show success message
            messagebox.showinfo("Success", 
                              f"Data loaded successfully!\n\n"
                              f"Records: {len(self.current_data):,}\n"
                              f"Columns: {len(self.current_data.columns)}")
            
            self.logger.info("Data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            self.status_var.set(f"❌ Error loading data: {str(e)}")
            self.load_button.config(state='normal')
            messagebox.showerror("Error", f"Failed to load data:\n{str(e)}")
    
    def update_data_display(self):
        """Update data display in table"""
        if self.current_data is None:
            return
        
        # Clear existing data
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        # Set columns
        columns = list(self.current_data.columns)
        self.data_tree['columns'] = columns
        
        # Configure columns
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=120, minwidth=50)
        
        # Add data (first 100 rows for performance)
        for idx, row in self.current_data.head(100).iterrows():
            values = [str(val) if pd.notna(val) else "" for val in row]
            self.data_tree.insert('', 'end', values=values)
    
    def update_data_info(self):
        """Update data information display"""
        if self.current_data is None:
            return
        
        info_text = f"📊 Dataset Information\n"
        info_text += "=" * 50 + "\n\n"
        
        info_text += f"📋 Basic Info:\n"
        info_text += f"  • File: {Path(self.data_file_path).name if self.data_file_path else 'Sample Data'}\n"
        info_text += f"  • Shape: {self.current_data.shape[0]} rows × {self.current_data.shape[1]} columns\n"
        info_text += f"  • Memory: {self.current_data.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB\n\n"
        
        info_text += f"📝 Columns:\n"
        for i, col in enumerate(self.current_data.columns, 1):
            dtype = self.current_data[col].dtype
            null_count = self.current_data[col].isnull().sum()
            null_pct = (null_count / len(self.current_data)) * 100
            unique_count = self.current_data[col].nunique()
            
            info_text += f"  {i:2d}. {col}\n"
            info_text += f"      Type: {dtype}\n"
            info_text += f"      Missing: {null_count} ({null_pct:.1f}%)\n"
            info_text += f"      Unique: {unique_count}\n\n"
        
        info_text += f"🔍 Data Quality:\n"
        total_missing = self.current_data.isnull().sum().sum()
        total_cells = len(self.current_data) * len(self.current_data.columns)
        completeness = ((total_cells - total_missing) / total_cells) * 100
        
        info_text += f"  • Total missing values: {total_missing}\n"
        info_text += f"  • Complete rows: {len(self.current_data.dropna())}\n"
        info_text += f"  • Data completeness: {completeness:.1f}%\n\n"
        
        # Analysis domain compatibility
        info_text += f"🎯 Analysis Domain Compatibility:\n"
        
        # Check for safety domain columns
        safety_cols = ['callsign', 'falldetected', 'casualtystate', 'processedtimegmt']
        safety_available = sum(1 for col in safety_cols if col in self.current_data.columns)
        info_text += f"  • Safety Analysis: {safety_available}/{len(safety_cols)} columns available\n"
        
        # Check for network domain columns
        network_cols = ['callsign', 'rssi', 'mcs', 'processedtimegmt']
        network_available = sum(1 for col in network_cols if col in self.current_data.columns)
        info_text += f"  • Network Analysis: {network_available}/{len(network_cols)} columns available\n"
        
        # Check for activity domain columns
        activity_cols = ['callsign', 'steps', 'posture', 'processedtimegmt']
        activity_available = sum(1 for col in activity_cols if col in self.current_data.columns)
        info_text += f"  • Activity Analysis: {activity_available}/{len(activity_cols)} columns available\n"
        
        # Check for equipment domain columns
        equipment_cols = ['callsign', 'battery', 'processedtimegmt']
        equipment_available = sum(1 for col in equipment_cols if col in self.current_data.columns)
        info_text += f"  • Equipment Analysis: {equipment_available}/{len(equipment_cols)} columns available\n"
        
        # Update text widget
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, info_text)
        self.info_text.config(state='disabled')
    
    def create_sample_data(self):
        """Create sample training data"""
        try:
            # Create realistic sample data
            num_records = 100
            units = ['Unit_108', 'Unit_134', 'Unit_156', 'Unit_178']
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
                    'casualtystate': self.generate_casualty_state(unit, i),
                    'rssi': max(-50, min(50, np.random.normal(20, 10))),
                    'mcs': np.random.randint(3, 8),
                    'nexthop': f'Router_{np.random.randint(1, 4)}',
                    'steps': np.random.randint(100, 400),
                    'posture': np.random.choice(['Standing', 'Prone', 'Unknown'], p=[0.4, 0.4, 0.2]),
                    'squad': 'Alpha' if unit in ['Unit_108', 'Unit_134'] else 'Bravo'
                }
                data.append(record)
            
            self.current_data = pd.DataFrame(data)
            self.data_file_path = "sample_training_data.csv"
            
            # Update UI
            self.file_path_var.set("Sample Training Data Created")
            self.status_var.set("📊 Sample data created with realistic training scenarios")
            
            # Update displays
            self.update_data_display()
            self.update_data_info()
            
            # Enable buttons
            self.validate_button.config(state='normal')
            self.analyze_button.config(state='normal')
            self.export_button.config(state='normal')
            
            self.analysis_info_var.set(f"✅ Sample data ready: {len(self.current_data)} records")
            
            messagebox.showinfo("Sample Data Created", 
                              f"Sample training data created successfully!\n\n"
                              f"Records: {len(self.current_data):,}\n"
                              f"Columns: {len(self.current_data.columns)}\n"
                              f"Units: {len(units)} units with varied activity levels\n"
                              f"Scenarios: Safety events, network data, activity tracking")
            
        except Exception as e:
            self.logger.error(f"Error creating sample data: {e}")
            messagebox.showerror("Error", f"Failed to create sample data: {str(e)}")
    
    def generate_casualty_state(self, unit: str, index: int) -> str:
        """Generate realistic casualty states"""
        if unit == 'Unit_108':
            # High-risk unit with more casualties
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
    
    def validate_data(self):
        """Validate the loaded data"""
        if self.current_data is None:
            messagebox.showerror("Error", "No data to validate")
            return
        
        try:
            self.progress_var.set("Validating data...")
            self.root.update_idletasks()
            
            validation_results = []
            
            # Check for missing data
            missing_data = self.current_data.isnull().sum()
            for col, count in missing_data.items():
                if count > 0:
                    pct = (count / len(self.current_data)) * 100
                    validation_results.append(f"• Column '{col}' has {count} missing values ({pct:.1f}%)")
            
            # Check required columns
            required_cols = ['callsign', 'processedtimegmt']
            missing_required = [col for col in required_cols if col not in self.current_data.columns]
            if missing_required:
                validation_results.append(f"• Missing required columns: {', '.join(missing_required)}")
            
            # Check data types
            if 'processedtimegmt' in self.current_data.columns:
                try:
                    pd.to_datetime(self.current_data['processedtimegmt'])
                except:
                    validation_results.append("• Column 'processedtimegmt' contains invalid datetime values")
            
            # Check numeric columns
            numeric_cols = ['latitude', 'longitude', 'temp', 'battery', 'rssi', 'mcs', 'steps']
            for col in numeric_cols:
                if col in self.current_data.columns:
                    non_numeric = pd.to_numeric(self.current_data[col], errors='coerce').isnull().sum()
                    if non_numeric > 0:
                        validation_results.append(f"• Column '{col}' has {non_numeric} non-numeric values")
            
            self.progress_var.set("")
            
            # Show results
            if validation_results:
                result_msg = f"Data validation found {len(validation_results)} issues:\n\n"
                result_msg += "\n".join(validation_results[:15])
                if len(validation_results) > 15:
                    result_msg += f"\n\n... and {len(validation_results) - 15} more issues"
                messagebox.showwarning("Validation Results", result_msg)
            else:
                messagebox.showinfo("Validation Results", 
                                  f"✅ Data validation passed!\n\n"
                                  f"Dataset: {len(self.current_data)} rows × {len(self.current_data.columns)} columns\n"
                                  f"No issues found in the data")
            
        except Exception as e:
            self.logger.error(f"Error validating data: {e}")
            self.progress_var.set("")
            messagebox.showerror("Error", f"Error validating data: {str(e)}")
    
    def analyze_data(self):
        """Analyze the loaded data"""
        if self.current_data is None:
            messagebox.showerror("Error", "No data to analyze")
            return
        
        try:
            # Create analysis window
            analysis_window = tk.Toplevel(self.root)
            analysis_window.title("AAR Data Analysis Results")
            analysis_window.geometry("800x600")
            
            # Configure window
            analysis_window.grid_rowconfigure(0, weight=1)
            analysis_window.grid_columnconfigure(0, weight=1)
            
            # Main frame
            main_frame = ttk.Frame(analysis_window, padding="20")
            main_frame.grid(row=0, column=0, sticky="nsew")
            
            # Configure main frame
            main_frame.grid_rowconfigure(1, weight=1)
            main_frame.grid_columnconfigure(0, weight=1)
            
            # Title
            title_label = ttk.Label(main_frame, 
                                   text="📊 AAR Data Analysis Results", 
                                   font=("Arial", 16, "bold"))
            title_label.grid(row=0, column=0, pady=(0, 20))
            
            # Analysis text
            analysis_text = tk.Text(main_frame, wrap='word', font=("Consolas", 10))
            analysis_scroll = ttk.Scrollbar(main_frame, orient='vertical', command=analysis_text.yview)
            analysis_text.configure(yscrollcommand=analysis_scroll.set)
            
            # Grid layout
            analysis_text.grid(row=1, column=0, sticky="nsew")
            analysis_scroll.grid(row=1, column=1, sticky="ns")
            
            # Generate and display analysis
            analysis_content = self.generate_analysis()
            analysis_text.insert(tk.END, analysis_content)
            analysis_text.config(state='disabled')
            
            # Close button
            close_button = ttk.Button(main_frame, text="Close", 
                                     command=analysis_window.destroy)
            close_button.grid(row=2, column=0, pady=(20, 0))
            
        except Exception as e:
            self.logger.error(f"Error analyzing data: {e}")
            messagebox.showerror("Error", f"Error analyzing data: {str(e)}")
    
    def generate_analysis(self):
        """Generate detailed analysis of the data"""
        if self.current_data is None:
            return "No data to analyze"
        
        df = self.current_data
        
        analysis = f"📊 AAR Training Data Analysis Report\n"
        analysis += "=" * 60 + "\n\n"
        
        # Dataset overview
        analysis += f"📋 Dataset Overview:\n"
        analysis += f"  • Total Records: {len(df):,}\n"
        analysis += f"  • Columns: {len(df.columns)}\n"
        analysis += f"  • Memory Usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB\n"
        analysis += f"  • Data Source: {Path(self.data_file_path).name if self.data_file_path else 'Sample Data'}\n\n"
        
        # Unit analysis
        if 'callsign' in df.columns:
            units = df['callsign'].value_counts()
            analysis += f"👥 Unit Analysis:\n"
            for unit, count in units.items():
                pct = (count / len(df)) * 100
                analysis += f"  • {unit}: {count:,} records ({pct:.1f}%)\n"
            analysis += "\n"
        
        # Time analysis
        if 'processedtimegmt' in df.columns:
            try:
                df['datetime'] = pd.to_datetime(df['processedtimegmt'])
                time_range = df['datetime'].max() - df['datetime'].min()
                analysis += f"⏰ Time Analysis:\n"
                analysis += f"  • Start Time: {df['datetime'].min()}\n"
                analysis += f"  • End Time: {df['datetime'].max()}\n"
                analysis += f"  • Duration: {time_range}\n"
                analysis += f"  • Records per minute: {len(df) / (time_range.total_seconds() / 60):.1f}\n\n"
            except:
                analysis += f"⏰ Time Analysis: Unable to parse timestamp data\n\n"
        
        # Safety analysis
        if 'falldetected' in df.columns:
            falls = df['falldetected'].value_counts()
            analysis += f"⚠️ Safety Analysis:\n"
            for state, count in falls.items():
                pct = (count / len(df)) * 100
                analysis += f"  • Falls {state}: {count:,} events ({pct:.1f}%)\n"
            analysis += "\n"
        
        if 'casualtystate' in df.columns:
            casualties = df['casualtystate'].value_counts()
            analysis += f"🏥 Casualty Analysis:\n"
            for state, count in casualties.items():
                pct = (count / len(df)) * 100
                analysis += f"  • {state}: {count:,} events ({pct:.1f}%)\n"
            analysis += "\n"
        
        # Network analysis
        if 'rssi' in df.columns:
            rssi_stats = df['rssi'].describe()
            analysis += f"📡 Network Performance:\n"
            analysis += f"  • Average RSSI: {rssi_stats['mean']:.1f} dBm\n"
            analysis += f"  • Min RSSI: {rssi_stats['min']:.1f} dBm\n"
            analysis += f"  • Max RSSI: {rssi_stats['max']:.1f} dBm\n"
            analysis += f"  • Std Dev: {rssi_stats['std']:.1f} dBm\n"
            
            # Signal quality assessment
            if rssi_stats['mean'] > 20:
                analysis += f"  • Signal Quality: Good\n"
            elif rssi_stats['mean'] > 10:
                analysis += f"  • Signal Quality: Moderate\n"
            else:
                analysis += f"  • Signal Quality: Poor\n"
            analysis += "\n"
        
        if 'mcs' in df.columns:
            mcs_stats = df['mcs'].describe()
            analysis += f"📊 MCS (Modulation Coding Scheme):\n"
            analysis += f"  • Average MCS: {mcs_stats['mean']:.1f}\n"
            analysis += f"  • Range: {mcs_stats['min']:.0f} - {mcs_stats['max']:.0f}\n"
            analysis += "\n"
        
        # Activity analysis
        if 'steps' in df.columns:
            steps_stats = df['steps'].describe()
            analysis += f"🏃 Activity Analysis:\n"
            analysis += f"  • Average Steps: {steps_stats['mean']:.0f}\n"
            analysis += f"  • Max Steps: {steps_stats['max']:.0f}\n"
            analysis += f"  • Min Steps: {steps_stats['min']:.0f}\n"
            analysis += f"  • Total Steps: {df['steps'].sum():.0f}\n"
            analysis += "\n"
        
        if 'posture' in df.columns:
            postures = df['posture'].value_counts()
            analysis += f"🧍 Posture Analysis:\n"
            for posture, count in postures.items():
                pct = (count / len(df)) * 100
                analysis += f"  • {posture}: {count:,} records ({pct:.1f}%)\n"
            analysis += "\n"
        
        # Equipment analysis
        if 'battery' in df.columns:
            battery_stats = df['battery'].describe()
            analysis += f"🔋 Equipment Analysis:\n"
            analysis += f"  • Average Battery: {battery_stats['mean']:.1f}%\n"
            analysis += f"  • Min Battery: {battery_stats['min']:.1f}%\n"
            analysis += f"  • Max Battery: {battery_stats['max']:.1f}%\n"
            
            # Battery health assessment
            low_battery = (df['battery'] < 20).sum()
            if low_battery > 0:
                analysis += f"  • Low Battery Alerts: {low_battery} records\n"
            analysis += "\n"
        
        # Environmental analysis
        if 'temp' in df.columns:
            temp_stats = df['temp'].describe()
            analysis += f"🌡️ Environmental Analysis:\n"
            analysis += f"  • Average Temperature: {temp_stats['mean']:.1f}°C\n"
            analysis += f"  • Temperature Range: {temp_stats['min']:.1f}°C - {temp_stats['max']:.1f}°C\n"
            analysis += "\n"
        
        # Data quality assessment
        analysis += f"🔍 Data Quality Assessment:\n"
        missing_total = df.isnull().sum().sum()
        total_cells = len(df) * len(df.columns)
        completeness = ((total_cells - missing_total) / total_cells) * 100
        
        analysis += f"  • Data Completeness: {completeness:.1f}%\n"
        analysis += f"  • Missing Values: {missing_total:,}\n"
        analysis += f"  • Complete Records: {len(df.dropna()):,}\n"
        
        # Column-specific missing data
        missing_by_col = df.isnull().sum()
        for col, missing in missing_by_col.items():
            if missing > 0:
                pct = (missing / len(df)) * 100
                analysis += f"    - {col}: {missing:,} missing ({pct:.1f}%)\n"
        
        analysis += "\n"
        
        # Recommendations
        analysis += f"💡 Recommendations:\n"
        
        if 'falldetected' in df.columns and df['falldetected'].value_counts().get('Yes', 0) > 0:
            analysis += f"  • Review fall detection events for safety protocol improvements\n"
        
        if 'rssi' in df.columns and df['rssi'].mean() < 15:
            analysis += f"  • Consider network infrastructure improvements for better connectivity\n"
        
        if missing_total > 0:
            analysis += f"  • Address data quality issues in sensor collection systems\n"
        
        if 'battery' in df.columns and df['battery'].min() < 20:
            analysis += f"  • Implement battery monitoring alerts for extended operations\n"
        
        if 'casualtystate' in df.columns and df['casualtystate'].value_counts().get('KILLED', 0) > 0:
            analysis += f"  • Analyze casualty patterns to improve training safety measures\n"
        
        return analysis
    
    def export_data(self):
        """Export current data"""
        if self.current_data is None:
            messagebox.showerror("Error", "No data to export")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export AAR Data",
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("JSON files", "*.json")
                ]
            )
            
            if file_path:
                self.progress_var.set("Exporting data...")
                self.root.update_idletasks()
                
                if file_path.endswith('.xlsx'):
                    self.current_data.to_excel(file_path, index=False)
                elif file_path.endswith('.json'):
                    self.current_data.to_json(file_path, orient='records', indent=2)
                else:
                    self.current_data.to_csv(file_path, index=False)
                
                self.progress_var.set("")
                messagebox.showinfo("Success", 
                                  f"Data exported successfully!\n\n"
                                  f"File: {Path(file_path).name}\n"
                                  f"Records: {len(self.current_data):,}\n"
                                  f"Location: {file_path}")
                
                self.logger.info(f"Data exported to: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            self.progress_var.set("")
            messagebox.showerror("Error", f"Error exporting data: {str(e)}")
    
    def cleanup(self):
        """Cleanup method"""
        self.logger.info("SimplifiedCSVLoader cleanup completed")


def main():
    """Main function to run the simplified CSV loader"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create root window
    root = tk.Tk()
    root.geometry("1200x800")
    
    # Create the loader
    loader = SimplifiedCSVLoader(root)
    
    # Handle window close
    def on_closing():
        loader.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the application
    root.mainloop()


if __name__ == "__main__":
    main()
