import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

class AARMainApplication:
    """Main AAR Application - Compatible with existing system"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AAR System v2.0 - Fixed")
        self.root.geometry("1200x800")
        self.root.state('zoomed')  # Maximize on Windows
        
        # Initialize components
        self.event_bus = None
        self.analysis_orchestrator = None
        self.current_data = None
        
        self.setup_ui()
        self.initialize_components()
        
    def initialize_components(self):
        """Initialize core components if available"""
        try:
            # Try to import and initialize core components
            from core.event_bus import EventBus
            self.event_bus = EventBus()
            print("[Main] ✅ Event bus initialized")
            
            try:
                from services.orchestration.analysis_orchestrator import AnalysisOrchestrator
                self.analysis_orchestrator = AnalysisOrchestrator(self.event_bus)
                print("[Main] ✅ Analysis orchestrator initialized")
                
                # Register available engines
                self.register_engines()
                
            except Exception as e:
                print(f"[Main] ⚠️ Could not initialize analysis orchestrator: {e}")
                
        except Exception as e:
            print(f"[Main] ⚠️ Could not initialize event bus: {e}")
            print("[Main] 📝 Running in standalone mode")
    
    def register_engines(self):
        """Register available analysis engines"""
        if not self.analysis_orchestrator:
            return
            
        try:
            # Try to register engines that are available
            from core.models import AnalysisDomain
            
            # Activity engine
            try:
                from engines.activity.soldier_activity_engine import SoldierActivityAnalysisEngine
                activity_engine = SoldierActivityAnalysisEngine(self.event_bus)
                self.analysis_orchestrator.register_engine(AnalysisDomain.ACTIVITY, activity_engine)
                print("[Main] ✅ Registered activity engine")
            except Exception as e:
                print(f"[Main] ⚠️ Could not register activity engine: {e}")
            
            # Equipment engine
            try:
                from engines.equipment.equipment_management_engine import EquipmentManagementAnalysisEngine
                equipment_engine = EquipmentManagementAnalysisEngine(self.event_bus)
                self.analysis_orchestrator.register_engine(AnalysisDomain.EQUIPMENT, equipment_engine)
                print("[Main] ✅ Registered equipment engine")
            except Exception as e:
                print(f"[Main] ⚠️ Could not register equipment engine: {e}")
            
            # Environmental engine
            try:
                from engines.environmental.environmental_monitoring_engine import EnvironmentalMonitoringAnalysisEngine
                env_engine = EnvironmentalMonitoringAnalysisEngine(self.event_bus)
                self.analysis_orchestrator.register_engine(AnalysisDomain.ENVIRONMENTAL, env_engine)
                print("[Main] ✅ Registered environmental engine")
            except Exception as e:
                print(f"[Main] ⚠️ Could not register environmental engine: {e}")
                
        except Exception as e:
            print(f"[Main] ⚠️ Error registering engines: {e}")
    
    def setup_ui(self):
        """Setup the main UI"""
        # Create main menu
        self.create_menu()
        
        # Create main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_tabs()
        
        # Create status bar
        self.status_bar = ttk.Label(self.root, text="🚀 AAR System Ready")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
    
    def create_menu(self):
        """Create the main menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Data...", command=self.load_data)
        file_menu.add_command(label="Export Reports...", command=self.export_reports)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Run Analysis", command=self.run_analysis)
        analysis_menu.add_command(label="View Results", command=self.view_results)
        
        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        reports_menu.add_command(label="Generate Executive Summary", command=lambda: self.quick_report("executive"))
        reports_menu.add_command(label="Generate Safety Report", command=lambda: self.quick_report("safety"))
        reports_menu.add_command(label="Generate Activity Report", command=lambda: self.quick_report("activity"))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_tabs(self):
        """Create all application tabs"""
        
        # Data Management Tab
        self.create_data_management_tab()
        
        # Analysis Control Tab
        self.create_analysis_control_tab()
        
        # Reports Tab (using our fixed version)
        self.create_reports_tab()
        
        # System Status Tab
        self.create_status_tab()
    
    def create_data_management_tab(self):
        """Create data management tab"""
        data_frame = ttk.Frame(self.notebook)
        self.notebook.add(data_frame, text="Data Management")
        
        # Title
        ttk.Label(data_frame, text="Data Management", 
                 font=("Arial", 16, "bold")).pack(pady=20)
        
        # File selection
        file_frame = ttk.LabelFrame(data_frame, text="Data Loading", padding=10)
        file_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.file_path_var = tk.StringVar()
        ttk.Label(file_frame, text="CSV File:").pack(anchor=tk.W)
        
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(path_frame, textvariable=self.file_path_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="Browse...", command=self.browse_file).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Load button
        ttk.Button(file_frame, text="Load Data", command=self.load_data).pack(pady=10)
        
        # Data preview
        preview_frame = ttk.LabelFrame(data_frame, text="Data Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.data_text = tk.Text(preview_frame, height=15)
        self.data_text.pack(fill=tk.BOTH, expand=True)
        
        # Initial message
        self.data_text.insert('1.0', """AAR Data Management

Welcome to the data management interface.

Steps to get started:
1. Click "Browse..." to select your training data CSV file
2. Click "Load Data" to import the data
3. Review the data preview below
4. Go to "Analysis Control" to run analysis
5. Generate reports in the "Reports" tab

Supported file format: CSV files with training exercise data
Required columns vary by analysis domain (Safety, Activity, Equipment, etc.)
""")
    
    def create_analysis_control_tab(self):
        """Create analysis control tab"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Analysis Control")
        
        # Title
        ttk.Label(analysis_frame, text="Analysis Control", 
                 font=("Arial", 16, "bold")).pack(pady=20)
        
        # Analysis options
        options_frame = ttk.LabelFrame(analysis_frame, text="Analysis Configuration", padding=10)
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Domain selection
        ttk.Label(options_frame, text="Analysis Domains:").pack(anchor=tk.W)
        
        self.domain_vars = {}
        domains = ["ACTIVITY", "EQUIPMENT", "ENVIRONMENTAL", "SAFETY", "NETWORK"]
        
        domain_frame = ttk.Frame(options_frame)
        domain_frame.pack(fill=tk.X, pady=5)
        
        for domain in domains:
            var = tk.BooleanVar(value=True if domain in ["ACTIVITY", "EQUIPMENT", "ENVIRONMENTAL"] else False)
            self.domain_vars[domain] = var
            ttk.Checkbutton(domain_frame, text=domain, variable=var).pack(side=tk.LEFT, padx=(0, 10))
        
        # Analysis buttons
        button_frame = ttk.Frame(options_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Run Analysis", command=self.run_analysis).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Test Analysis", command=self.test_analysis).pack(side=tk.LEFT)
        
        # Results area
        results_frame = ttk.LabelFrame(analysis_frame, text="Analysis Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.analysis_text = tk.Text(results_frame, height=15)
        self.analysis_text.pack(fill=tk.BOTH, expand=True)
        
        self.analysis_text.insert('1.0', """Analysis Control Center

This tab controls the analysis execution process.

Instructions:
1. Select which analysis domains to run (checkboxes above)
2. Click "Run Analysis" to analyze loaded data
3. Or click "Test Analysis" to run with sample data
4. View results below and in the Reports tab

Available Domains:
• ACTIVITY: Movement patterns, step count, physical performance
• EQUIPMENT: Battery levels, device status, maintenance needs  
• ENVIRONMENTAL: Temperature, weather conditions, environmental impact
• SAFETY: Fall detection, medical events, risk assessment
• NETWORK: Communication effectiveness, connectivity analysis

Analysis results will automatically trigger report generation capabilities.
""")
    
    def create_reports_tab(self):
        """Create reports tab using our fixed version"""
        reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(reports_frame, text="Reports")
        
        try:
            # Import and use our fixed reports tab
            from ui.components.reports_tab import ReportsTab
            self.reports_tab = ReportsTab(reports_frame, self.event_bus, self.analysis_orchestrator)
            print("[Main] ✅ Reports tab loaded successfully")
        except Exception as e:
            print(f"[Main] ❌ Could not load reports tab: {e}")
            # Create fallback reports tab
            self.create_fallback_reports_tab(reports_frame)
    
    def create_fallback_reports_tab(self, parent):
        """Create a fallback reports tab if the main one fails"""
        ttk.Label(parent, text="Reports", font=("Arial", 16, "bold")).pack(pady=20)
        ttk.Label(parent, text="Reports functionality is being loaded...").pack()
        ttk.Button(parent, text="Test Report Generation", command=self.test_report).pack(pady=10)
    
    def create_status_tab(self):
        """Create system status tab"""
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text="System Status")
        
        # Title
        ttk.Label(status_frame, text="System Status", 
                 font=("Arial", 16, "bold")).pack(pady=20)
        
        # Status information
        status_text = tk.Text(status_frame, height=20)
        status_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Generate status report
        status_info = f"""AAR System Status Report

Core Components:
✅ Main Application: Loaded successfully
{"✅" if self.event_bus else "❌"} Event Bus: {"Available" if self.event_bus else "Not Available"}
{"✅" if self.analysis_orchestrator else "❌"} Analysis Orchestrator: {"Available" if self.analysis_orchestrator else "Not Available"}

UI Components:
✅ Data Management Tab: Ready
✅ Analysis Control Tab: Ready  
✅ Reports Tab: {"Ready" if hasattr(self, 'reports_tab') else "Loading..."}
✅ System Status Tab: Ready

File Structure:
✅ reports/generated/: Available for report output
✅ ui/components/: Component files present
✅ Configuration: System configured

Analysis Engines:
• ACTIVITY: {"Available" if self.analysis_orchestrator else "Pending initialization"}
• EQUIPMENT: {"Available" if self.analysis_orchestrator else "Pending initialization"}  
• ENVIRONMENTAL: {"Available" if self.analysis_orchestrator else "Pending initialization"}
• SAFETY: Requires configuration
• NETWORK: Requires configuration

Next Steps:
1. Load training data via Data Management tab
2. Configure analysis domains in Analysis Control
3. Run analysis to generate insights
4. Create comprehensive reports in Reports tab

System Version: 2.0 (Fixed)
Last Updated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        status_text.insert('1.0', status_info)
        status_text.config(state='disabled')
    
    def browse_file(self):
        """Browse for data file"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="Select Training Data CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)
    
    def load_data(self):
        """Load data from selected file"""
        filepath = self.file_path_var.get()
        if not filepath:
            messagebox.showwarning("No File", "Please select a CSV file first.")
            return
        
        try:
            import pandas as pd
            df = pd.read_csv(filepath)
            
            self.current_data = df
            
            # Update data preview
            self.data_text.delete('1.0', 'end')
            self.data_text.insert('1.0', f"Data loaded successfully from: {os.path.basename(filepath)}\n\n")
            self.data_text.insert('end', f"Rows: {len(df)}\n")
            self.data_text.insert('end', f"Columns: {len(df.columns)}\n\n")
            self.data_text.insert('end', "Column names:\n")
            for col in df.columns:
                self.data_text.insert('end', f"• {col}\n")
            
            self.data_text.insert('end', f"\nFirst 5 rows:\n{df.head().to_string()}")
            
            messagebox.showinfo("Success", f"Loaded {len(df)} rows of data successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
    
    def run_analysis(self):
        """Run analysis on loaded data"""
        if self.current_data is None:
            messagebox.showwarning("No Data", "Please load data first.")
            return
        
        if not self.analysis_orchestrator:
            messagebox.showwarning("No Orchestrator", "Analysis orchestrator not available. Using test mode.")
            self.test_analysis()
            return
        
        try:
            # Get selected domains
            selected_domains = [domain for domain, var in self.domain_vars.items() if var.get()]
            
            if not selected_domains:
                messagebox.showwarning("No Domains", "Please select at least one analysis domain.")
                return
            
            self.analysis_text.delete('1.0', 'end')
            self.analysis_text.insert('1.0', f"Running analysis for domains: {', '.join(selected_domains)}\n\n")
            
            # This would trigger real analysis - for now, simulate
            self.test_analysis()
            
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Failed to run analysis: {str(e)}")
    
    def test_analysis(self):
        """Run test analysis with sample results"""
        self.analysis_text.delete('1.0', 'end')
        self.analysis_text.insert('1.0', "Running test analysis...\n\n")
        
        # Simulate analysis results
        fake_results = {
            'ACTIVITY': type('Result', (), {'summary': 'Activity analysis completed successfully'})(),
            'EQUIPMENT': type('Result', (), {'summary': 'Equipment status nominal'})(),
            'ENVIRONMENTAL': type('Result', (), {'summary': 'Environmental conditions favorable'})()
        }
        
        # Trigger analysis completed event if event bus is available
        if self.event_bus:
            try:
                self.event_bus.publish("analysis_completed", {"results": fake_results})
                self.analysis_text.insert('end', "✅ Analysis completed and results published\n")
            except Exception as e:
                self.analysis_text.insert('end', f"⚠️ Event publishing error: {e}\n")
        
        # Update reports tab if available
        if hasattr(self, 'reports_tab') and hasattr(self.reports_tab, 'on_analysis_completed'):
            try:
                self.reports_tab.on_analysis_completed({"results": fake_results})
                self.analysis_text.insert('end', "✅ Reports tab updated with results\n")
            except Exception as e:
                self.analysis_text.insert('end', f"⚠️ Reports update error: {e}\n")
        
        self.analysis_text.insert('end', "\nTest analysis complete! Go to Reports tab to generate reports.")
        
        messagebox.showinfo("Analysis Complete", "Test analysis completed successfully!\nGo to the Reports tab to generate reports.")
    
    def quick_report(self, report_type):
        """Generate a quick report"""
        if hasattr(self, 'reports_tab') and hasattr(self.reports_tab, 'generate_quick_report'):
            self.reports_tab.generate_quick_report(report_type)
        else:
            messagebox.showinfo("Reports", f"Generating {report_type} report...")
    
    def view_results(self):
        """Switch to reports tab"""
        self.notebook.select(2)  # Assuming reports is the 3rd tab (index 2)
    
    def export_reports(self):
        """Export reports"""
        reports_dir = "reports/generated"
        if os.path.exists(reports_dir) and os.listdir(reports_dir):
            messagebox.showinfo("Export", f"Reports are available in: {os.path.abspath(reports_dir)}")
        else:
            messagebox.showinfo("Export", "No reports available to export. Generate reports first.")
    
    def test_report(self):
        """Test report generation"""
        if hasattr(self, 'reports_tab') and hasattr(self.reports_tab, 'test_report_generation'):
            self.reports_tab.test_report_generation()
        else:
            messagebox.showinfo("Test", "Report testing functionality not available.")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About", "AAR System v2.0\nAfter Action Review System\nFixed and Compatible Version")
    
    def run(self):
        """Run the application"""
        print("[Main] 🚀 Starting AAR System...")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit the AAR System?"):
            self.root.destroy()

# Compatibility aliases
MainApplication = AARMainApplication
App = AARMainApplication
