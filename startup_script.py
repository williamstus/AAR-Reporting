# start_aar_system.py - Startup script for AAR System
"""
AAR System Startup Script
This script will start the AAR system with proper CSV loading functionality.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from pathlib import Path
import logging

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('aar_system.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []
    
    try:
        import pandas as pd
    except ImportError:
        missing_deps.append("pandas")
    
    try:
        import numpy as np
    except ImportError:
        missing_deps.append("numpy")
    
    return missing_deps

def create_startup_window():
    """Create the startup window for the AAR system"""
    root = tk.Tk()
    root.title("AAR System - Startup")
    root.geometry("800x600")
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (800 // 2)
    y = (root.winfo_screenheight() // 2) - (600 // 2)
    root.geometry(f"800x600+{x}+{y}")
    
    return root

def main():
    """Main startup function"""
    logger = setup_logging()
    logger.info("Starting AAR System...")
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"Missing dependencies: {', '.join(missing_deps)}")
        print("Please install them using: pip install pandas numpy")
        return
    
    # Create startup window
    root = create_startup_window()
    
    # Main frame
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill='both', expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, 
                           text="🎯 AAR Analysis System", 
                           font=("Arial", 24, "bold"))
    title_label.pack(pady=(0, 10))
    
    subtitle_label = ttk.Label(main_frame, 
                              text="After Action Review System for Military Training Data",
                              font=("Arial", 14))
    subtitle_label.pack(pady=(0, 30))
    
    # Options frame
    options_frame = ttk.LabelFrame(main_frame, text="🚀 Launch Options", padding="20")
    options_frame.pack(fill='x', pady=(0, 20))
    
    # Launch buttons
    def launch_full_system():
        """Launch the full AAR system"""
        try:
            root.destroy()
            
            # Import and run the full system
            logger.info("Launching full AAR system...")
            
            # Try to import your main application
            try:
                from ui.main_application import AARSystemApplication
                
                # Create new root for main app
                main_root = tk.Tk()
                main_root.title("AAR Analysis System")
                main_root.geometry("1400x900")
                
                # Create the application
                app = AARSystemApplication(main_root)
                
                # Handle window close
                def on_closing():
                    if hasattr(app, 'cleanup'):
                        app.cleanup()
                    main_root.destroy()
                
                main_root.protocol("WM_DELETE_WINDOW", on_closing)
                
                # Start the main application
                main_root.mainloop()
                
            except ImportError as e:
                logger.error(f"Could not import main application: {e}")
                messagebox.showerror("Import Error", 
                                   f"Could not load full system: {e}\n\nTry the CSV Loader instead.")
                
        except Exception as e:
            logger.error(f"Error launching full system: {e}")
            messagebox.showerror("Error", f"Error launching system: {e}")
    
    def launch_csv_loader():
        """Launch the CSV loader"""
        try:
            root.destroy()
            
            # Import pandas and create CSV loader
            import pandas as pd
            
            # Create CSV loader window
            csv_root = tk.Tk()
            csv_root.title("AAR System - CSV Data Loader")
            csv_root.geometry("1200x800")
            
            # Use the SimplifiedCSVLoader class defined in this file
            app = SimplifiedCSVLoader(csv_root)
            
            # Handle window close
            def on_closing():
                if hasattr(app, 'cleanup'):
                    app.cleanup()
                csv_root.destroy()
            
            csv_root.protocol("WM_DELETE_WINDOW", on_closing)
            
            # Start the CSV loader
            csv_root.mainloop()
            
        except ImportError as e:
            logger.error(f"Missing pandas: {e}")
            messagebox.showerror("Missing Dependency", 
                               f"Pandas is required for CSV loading.\n\nInstall with: pip install pandas\n\nError: {e}")
        except Exception as e:
            logger.error(f"Error launching CSV loader: {e}")
            messagebox.showerror("Error", f"Error launching CSV loader: {e}")
    
    def launch_emergency_mode():
        """Launch emergency mode"""
        try:
            root.destroy()
            
            # Create emergency interface
            emergency_root = tk.Tk()
            emergency_root.title("AAR System - Emergency Mode")
            emergency_root.geometry("800x600")
            
            create_emergency_interface(emergency_root)
            
            emergency_root.mainloop()
            
        except Exception as e:
            logger.error(f"Error launching emergency mode: {e}")
            messagebox.showerror("Error", f"Error launching emergency mode: {e}")
    
    # Launch buttons
    ttk.Button(options_frame, 
               text="🎯 Launch Full AAR System", 
               command=launch_full_system,
               width=30).pack(pady=5)
    
    ttk.Button(options_frame, 
               text="📊 Launch CSV Data Loader", 
               command=launch_csv_loader,
               width=30).pack(pady=5)
    
    ttk.Button(options_frame, 
               text="🚨 Emergency Mode", 
               command=launch_emergency_mode,
               width=30).pack(pady=5)
    
    # Information frame
    info_frame = ttk.LabelFrame(main_frame, text="ℹ️ System Information", padding="15")
    info_frame.pack(fill='both', expand=True, pady=(0, 20))
    
    info_text = tk.Text(info_frame, height=8, wrap='word')
    info_scroll = ttk.Scrollbar(info_frame, orient='vertical', command=info_text.yview)
    info_text.configure(yscrollcommand=info_scroll.set)
    
    info_text.pack(side='left', fill='both', expand=True)
    info_scroll.pack(side='right', fill='y')
    
    # Add system info
    info_content = """🎯 AAR System Information:

• Full AAR System: Complete analysis system with all domains (Safety, Network, Activity, Equipment)
• CSV Data Loader: Simplified interface for loading and previewing CSV training data
• Emergency Mode: Basic CSV viewer for troubleshooting

📋 Supported Data Formats:
• CSV files with training data
• Required columns: callsign, processedtimegmt, latitude, longitude
• Optional columns: falldetected, casualtystate, temp, battery, rssi, mcs, steps, etc.

🔧 System Requirements:
• Python 3.7+
• pandas (for data processing)
• numpy (for numerical operations)
• tkinter (for GUI - usually included with Python)

💡 Quick Start:
1. Click 'Launch CSV Data Loader' to begin
2. Load your training data CSV file
3. Preview and analyze your data
4. Export results as needed
"""
    
    info_text.insert(tk.END, info_content)
    info_text.config(state='disabled')
    
    # Status bar
    status_frame = ttk.Frame(main_frame)
    status_frame.pack(fill='x')
    
    status_label = ttk.Label(status_frame, text="Ready to launch AAR system")
    status_label.pack(side='left')
    
    # Version info
    version_label = ttk.Label(status_frame, text="Version 1.0", foreground="gray")
    version_label.pack(side='right')
    
    # Start the startup window
    root.mainloop()

def create_emergency_interface(root):
    """Create emergency interface"""
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill='both', expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, 
                           text="🚨 AAR System - Emergency Mode", 
                           font=("Arial", 16, "bold"))
    title_label.pack(pady=(0, 20))
    
    # File selection
    file_frame = ttk.LabelFrame(main_frame, text="Select CSV File", padding="10")
    file_frame.pack(fill='x', pady=(0, 20))
    
    file_path_var = tk.StringVar(value="No file selected")
    file_label = ttk.Label(file_frame, textvariable=file_path_var)
    file_label.pack(side='left')
    
    def browse_file():
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            file_path_var.set(f"Selected: {Path(file_path).name}")
            load_file(file_path)
    
    ttk.Button(file_frame, text="Browse", command=browse_file).pack(side='right')
    
    # Data display
    data_frame = ttk.LabelFrame(main_frame, text="Data Preview", padding="10")
    data_frame.pack(fill='both', expand=True)
    
    data_text = tk.Text(data_frame, wrap='word')
    data_scroll = ttk.Scrollbar(data_frame, orient='vertical', command=data_text.yview)
    data_text.configure(yscrollcommand=data_scroll.set)
    
    data_text.pack(side='left', fill='both', expand=True)
    data_scroll.pack(side='right', fill='y')
    
    def load_file(file_path):
        try:
            # Try to load with pandas
            import pandas as pd
            df = pd.read_csv(file_path)
            
            content = f"📊 CSV File Loaded: {Path(file_path).name}\n"
            content += "=" * 50 + "\n\n"
            content += f"Records: {len(df)}\n"
            content += f"Columns: {len(df.columns)}\n\n"
            content += "Column List:\n"
            for i, col in enumerate(df.columns, 1):
                content += f"  {i}. {col}\n"
            
            content += f"\nFirst 5 rows:\n"
            content += df.head().to_string()
            
            data_text.delete(1.0, tk.END)
            data_text.insert(tk.END, content)
            
        except ImportError:
            # Fallback to basic file reading
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                data_text.delete(1.0, tk.END)
                data_text.insert(tk.END, content)
            except Exception as e:
                data_text.delete(1.0, tk.END)
                data_text.insert(tk.END, f"Error loading file: {str(e)}")
        except Exception as e:
            data_text.delete(1.0, tk.END)
            data_text.insert(tk.END, f"Error loading CSV: {str(e)}")

# Simplified CSV Loader class (standalone)
class SimplifiedCSVLoader:
    """Simplified CSV loader for when full system isn't available"""
    
    def __init__(self, root):
        self.root = root
        self.current_data = None
        self.create_ui()
    
    def create_ui(self):
        """Create the UI"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, 
                               text="📊 AAR System - CSV Data Loader", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="🗂️ Select CSV File", padding="10")
        file_frame.pack(fill='x', pady=(0, 20))
        
        self.file_path_var = tk.StringVar(value="No file selected")
        file_label = ttk.Label(file_frame, textvariable=self.file_path_var)
        file_label.pack(side='left')
        
        button_frame = ttk.Frame(file_frame)
        button_frame.pack(side='right')
        
        ttk.Button(button_frame, text="📁 Browse", command=self.browse_file).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="🔄 Sample Data", command=self.create_sample_data).pack(side='left')
        
        # Data preview
        preview_frame = ttk.LabelFrame(main_frame, text="👁️ Data Preview", padding="10")
        preview_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Create treeview
        tree_frame = ttk.Frame(preview_frame)
        tree_frame.pack(fill='both', expand=True)
        
        self.data_tree = ttk.Treeview(tree_frame, show='headings', height=15)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.data_tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.data_tree.xview)
        self.data_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Grid layout
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.data_tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        # Status and actions
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill='x')
        
        self.status_var = tk.StringVar(value="Select a CSV file to begin")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side='left')
        
        # Action buttons
        action_frame = ttk.Frame(status_frame)
        action_frame.pack(side='right')
        
        ttk.Button(action_frame, text="📤 Export", command=self.export_data).pack(side='left', padx=(0, 5))
        ttk.Button(action_frame, text="🔍 Analyze", command=self.analyze_data).pack(side='left')
    
    def browse_file(self):
        """Browse for CSV file"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.load_csv_data(file_path)
    
    def load_csv_data(self, file_path):
        """Load CSV data"""
        try:
            import pandas as pd
            self.current_data = pd.read_csv(file_path)
            
            # Update UI
            self.file_path_var.set(f"File: {Path(file_path).name}")
            self.status_var.set(f"✅ Loaded {len(self.current_data)} records, {len(self.current_data.columns)} columns")
            
            # Update display
            self.update_data_display()
            
            messagebox.showinfo("Success", f"CSV loaded successfully!\nRecords: {len(self.current_data)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading CSV: {str(e)}")
    
    def update_data_display(self):
        """Update the data display"""
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
            self.data_tree.column(col, width=100)
        
        # Add data (first 100 rows)
        for idx, row in self.current_data.head(100).iterrows():
            values = [str(val) if pd.notna(val) else "" for val in row]
            self.data_tree.insert('', 'end', values=values)
    
    def create_sample_data(self):
        """Create sample data"""
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        # Create sample data
        num_records = 100
        base_time = datetime.now() - timedelta(minutes=30)
        
        data = []
        for i in range(num_records):
            record = {
                'callsign': f'Unit_{108 + (i % 4) * 26}',
                'processedtimegmt': (base_time + timedelta(minutes=i*0.3)).strftime('%Y-%m-%d %H:%M:%S'),
                'latitude': 40.7128 + np.random.uniform(-0.01, 0.01),
                'longitude': -74.0060 + np.random.uniform(-0.01, 0.01),
                'temp': np.random.normal(25, 3),
                'battery': max(0, 100 - (i * 0.5) + np.random.uniform(-10, 10)),
                'falldetected': np.random.choice(['Yes', 'No'], p=[0.15, 0.85]),
                'casualtystate': np.random.choice(['GOOD', 'FALL ALERT', 'KILLED', 'RESURRECTED'], p=[0.7, 0.15, 0.1, 0.05]),
                'rssi': np.random.normal(20, 10),
                'mcs': np.random.randint(3, 8),
                'steps': np.random.randint(50, 400),
                'posture': np.random.choice(['Standing', 'Prone', 'Unknown'], p=[0.5, 0.3, 0.2])
            }
            data.append(record)
        
        self.current_data = pd.DataFrame(data)
        self.file_path_var.set("Sample AAR Training Data")
        self.status_var.set(f"✅ Sample data created: {len(self.current_data)} records")
        self.update_data_display()
        
        messagebox.showinfo("Success", "Sample training data created successfully!")
    
    def export_data(self):
        """Export current data"""
        if self.current_data is None:
            messagebox.showerror("Error", "No data to export")
            return
        
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            title="Export Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.current_data.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Data exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error exporting: {str(e)}")
    
    def analyze_data(self):
        """Analyze current data"""
        if self.current_data is None:
            messagebox.showerror("Error", "No data to analyze")
            return
        
        # Create analysis window
        analysis_window = tk.Toplevel(self.root)
        analysis_window.title("AAR Data Analysis")
        analysis_window.geometry("700x500")
        
        # Analysis content
        analysis_frame = ttk.Frame(analysis_window, padding="20")
        analysis_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(analysis_frame, 
                               text="📊 AAR Data Analysis Results", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Analysis text
        analysis_text = tk.Text(analysis_frame, wrap='word', height=20)
        analysis_scroll = ttk.Scrollbar(analysis_frame, orient='vertical', command=analysis_text.yview)
        analysis_text.configure(yscrollcommand=analysis_scroll.set)
        
        analysis_text.pack(side='left', fill='both', expand=True)
        analysis_scroll.pack(side='right', fill='y')
        
        # Generate analysis
        analysis = self.generate_analysis()
        analysis_text.insert(tk.END, analysis)
        analysis_text.config(state='disabled')
    
    def generate_analysis(self):
        """Generate analysis of the data"""
        if self.current_data is None:
            return "No data to analyze"
        
        df = self.current_data
        
        analysis = f"📊 AAR Training Data Analysis\n"
        analysis += "=" * 50 + "\n\n"
        
        analysis += f"📋 Dataset Overview:\n"
        analysis += f"  • Total Records: {len(df)}\n"
        analysis += f"  • Columns: {len(df.columns)}\n"
        analysis += f"  • Memory Usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB\n\n"
        
        # Unit analysis
        if 'callsign' in df.columns:
            units = df['callsign'].value_counts()
            analysis += f"👥 Unit Analysis:\n"
            for unit, count in units.items():
                analysis += f"  • {unit}: {count} records ({count/len(df)*100:.1f}%)\n"
            analysis += "\n"
        
        # Safety analysis
        if 'falldetected' in df.columns:
            falls = df['falldetected'].value_counts()
            analysis += f"⚠️ Safety Analysis:\n"
            for state, count in falls.items():
                analysis += f"  • {state}: {count} events\n"
            analysis += "\n"
        
        if 'casualtystate' in df.columns:
            casualties = df['casualtystate'].value_counts()
            analysis += f"🏥 Casualty Analysis:\n"
            for state, count in casualties.items():
                analysis += f"  • {state}: {count} events\n"
            analysis += "\n"
        
        # Network analysis
        if 'rssi' in df.columns:
            rssi_avg = df['rssi'].mean() if pd.notna(df['rssi'].mean()) else 0
            analysis += f"📡 Network Performance:\n"
            analysis += f"  • Average RSSI: {rssi_avg:.1f} dBm\n"
            if rssi_avg > 20:
                analysis += f"  • Status: Good signal strength\n"
            elif rssi_avg > 10:
                analysis += f"  • Status: Moderate signal strength\n"
            else:
                analysis += f"  • Status: Poor signal strength\n"
            analysis += "\n"
        
        # Activity analysis
        if 'steps' in df.columns:
            steps_avg = df['steps'].mean() if pd.notna(df['steps'].mean()) else 0
            analysis += f"🏃 Activity Analysis:\n"
            analysis += f"  • Average Steps: {steps_avg:.0f}\n"
            analysis += f"  • Max Steps: {df['steps'].max()}\n"
            analysis += f"  • Min Steps: {df['steps'].min()}\n"
            analysis += "\n"
        
        # Data quality
        analysis += f"🔍 Data Quality:\n"
        missing_total = df.isnull().sum().sum()
        total_cells = len(df) * len(df.columns)
        completeness = ((total_cells - missing_total) / total_cells) * 100
        
        analysis += f"  • Completeness: {completeness:.1f}%\n"
        analysis += f"  • Missing Values: {missing_total}\n"
        
        # Column-specific missing data
        missing_by_col = df.isnull().sum()
        for col, missing in missing_by_col.items():
            if missing > 0:
                pct = (missing / len(df)) * 100
                analysis += f"    - {col}: {missing} missing ({pct:.1f}%)\n"
        
        analysis += "\n"
        
        # Recommendations
        analysis += f"💡 Recommendations:\n"
        
        if 'falldetected' in df.columns and df['falldetected'].value_counts().get('Yes', 0) > 0:
            analysis += f"  • Review fall detection events for safety improvements\n"
        
        if 'rssi' in df.columns and rssi_avg < 15:
            analysis += f"  • Consider network infrastructure improvements\n"
        
        if missing_total > 0:
            analysis += f"  • Address data quality issues in sensor collection\n"
        
        if 'battery' in df.columns and df['battery'].min() < 20:
            analysis += f"  • Monitor battery levels for extended operations\n"
        
        return analysis
    
    def cleanup(self):
        """Cleanup method"""
        pass

if __name__ == "__main__":
    main()
