#!/usr/bin/env python3
"""
Enhanced Individual Soldier Report System - GUI Version
COMPLETE VERSION with visible report generation buttons
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
import threading

class EnhancedReportSystemGUI:
    """GUI for Enhanced Individual Soldier Report System"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎖️ Enhanced Individual Soldier Report System")
        self.root.geometry("1200x900")
        self.root.configure(bg='#2c3e50')
        
        # Data storage
        self.data = None
        self.battle_analysis = None
        self.tactical_analysis = None
        self.generated_reports = []
        self.output_directory = Path("reports/enhanced")
        
        # Column mapping for Fort Moore CSV data
        self.column_mapping = {
            'callsign': 'Callsign',
            'squad': 'Platoon', 
            'casualtystate': 'Casualty_State',
            'processedtimegmt': 'Time_Step',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'posture': 'Posture',
            'heartrate': 'Heart_Rate',
            'stepcount': 'Step_Count',
            'temp': 'Temperature',
            'falldetected': 'Fall_Detection',
            'battery': 'Battery',
            'rssi': 'RSSI',
            'weapon': 'Weapon',
            'shootercallsign': 'Shooter_Callsign',
            'munition': 'Munition',
            'hitzone': 'Hit_Zone',
            'mcs': 'MCS',
            'nexthop': 'Next_Hop',
            'ip': 'IP_Address',
            'playerid': 'Player_ID'
        }
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Header
        header_frame = tk.Frame(self.root, bg='#34495e', height=80)
        header_frame.pack(fill='x', padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, 
                              text="🎖️ Enhanced Individual Soldier Report System", 
                              font=('Arial', 18, 'bold'),
                              fg='white', bg='#34495e')
        title_label.pack(expand=True)
        
        subtitle_label = tk.Label(header_frame,
                                 text="Battle Analysis • Tactical Assessment • Safety Monitoring",
                                 font=('Arial', 11),
                                 fg='#bdc3c7', bg='#34495e')
        subtitle_label.pack()
        
        # Main content area with notebook for tabs
        main_frame = tk.Frame(self.root, bg='#ecf0f1')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Main tab
        self.main_tab = tk.Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(self.main_tab, text='📊 Main System')
        
        # Help tab
        self.help_tab = tk.Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(self.help_tab, text='❓ Help & Assessment Criteria')
        
        # Setup main tab content
        self.setup_main_tab()
        
        # Setup help tab content
        self.setup_help_tab()
        
    def setup_main_tab(self):
        """Setup the main tab content with proper button placement"""
        main_frame = self.main_tab
        
        # Left panel - Controls
        left_panel = tk.Frame(main_frame, bg='#ecf0f1', width=450)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # File selection section
        file_section = tk.LabelFrame(left_panel, text="📁 Data File Selection",
                                    font=('Arial', 12, 'bold'),
                                    bg='#ecf0f1', fg='#2c3e50')
        file_section.pack(fill='x', pady=(0, 10))
        
        self.file_path_var = tk.StringVar()
        self.file_label = tk.Label(file_section, textvariable=self.file_path_var,
                                  font=('Arial', 9),
                                  bg='#ecf0f1', fg='#7f8c8d',
                                  wraplength=400)
        self.file_label.pack(pady=5)
        
        file_button = tk.Button(file_section, text="🔍 Select CSV File",
                               command=self.select_file,
                               font=('Arial', 11, 'bold'),
                               bg='#3498db', fg='white',
                               relief='flat', padx=20, pady=10)
        file_button.pack(pady=5)
        
        # Data info section
        info_section = tk.LabelFrame(left_panel, text="📊 Data Information",
                                    font=('Arial', 12, 'bold'),
                                    bg='#ecf0f1', fg='#2c3e50')
        info_section.pack(fill='x', pady=(0, 10))
        
        self.info_text = tk.Text(info_section, height=6, width=50,
                                font=('Courier', 9),
                                bg='white', fg='#2c3e50',
                                wrap='word', state='disabled')
        self.info_text.pack(padx=5, pady=5)
        
        # Analysis controls
        analysis_section = tk.LabelFrame(left_panel, text="🎯 Analysis Controls",
                                       font=('Arial', 12, 'bold'),
                                       bg='#ecf0f1', fg='#2c3e50')
        analysis_section.pack(fill='x', pady=(0, 10))
        
        self.analyze_button = tk.Button(analysis_section, text="🔬 Run Battle Analysis",
                                       command=self.run_analysis,
                                       font=('Arial', 11, 'bold'),
                                       bg='#e74c3c', fg='white',
                                       relief='flat', padx=20, pady=10,
                                       state='disabled')
        self.analyze_button.pack(pady=5)
        
        debug_button = tk.Button(analysis_section, text="🔍 Debug Failed Reports",
                               command=self.debug_failed_reports,
                               font=('Arial', 10),
                               bg='#9b59b6', fg='white',
                               relief='flat', padx=15, pady=5)
        debug_button.pack(pady=5)
        
        # Soldier selection section
        soldier_section = tk.LabelFrame(left_panel, text="👥 Soldier Selection & Report Generation",
                                       font=('Arial', 12, 'bold'),
                                       bg='#ecf0f1', fg='#2c3e50')
        soldier_section.pack(fill='both', expand=True, pady=(0, 10))
        
        # Available soldiers label
        tk.Label(soldier_section, text="Available Soldiers:",
                font=('Arial', 10, 'bold'),
                bg='#ecf0f1', fg='#2c3e50').pack(anchor='w', padx=5, pady=(5,0))
        
        # Soldier listbox with scrollbar
        listbox_frame = tk.Frame(soldier_section, bg='#ecf0f1')
        listbox_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.soldier_listbox = tk.Listbox(listbox_frame,
                                        font=('Courier', 9),
                                        selectmode='extended',
                                        height=8)
        
        scrollbar_soldiers = tk.Scrollbar(listbox_frame, orient='vertical', command=self.soldier_listbox.yview)
        self.soldier_listbox.configure(yscrollcommand=scrollbar_soldiers.set)
        
        self.soldier_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_soldiers.pack(side='right', fill='y')
        
        # CRITICAL: Report generation buttons - Make them very visible
        report_instructions = tk.Label(soldier_section, 
                                     text="↑ Select soldiers above, then generate reports ↓",
                                     font=('Arial', 10, 'bold'),
                                     bg='#ecf0f1', fg='#e67e22')
        report_instructions.pack(pady=(5, 10))
        
        # Button frame with prominent styling
        button_frame = tk.Frame(soldier_section, bg='#34495e', relief='raised', bd=2)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(button_frame, text="REPORT GENERATION:",
                font=('Arial', 9, 'bold'),
                bg='#34495e', fg='white').pack(pady=(5, 2))
        
        # Report generation buttons container
        buttons_container = tk.Frame(button_frame, bg='#34495e')
        buttons_container.pack(fill='x', padx=10, pady=(0, 10))
        
        self.generate_selected_button = tk.Button(buttons_container, 
                                                text="📋 Generate Selected Reports",
                                                command=self.generate_selected_reports,
                                                font=('Arial', 10, 'bold'),
                                                bg='#27ae60', fg='white',
                                                relief='raised', bd=3,
                                                padx=15, pady=8,
                                                state='disabled')
        self.generate_selected_button.pack(fill='x', pady=(0, 5))
        
        self.generate_all_button = tk.Button(buttons_container,
                                           text="📤 Generate ALL Soldier Reports",
                                           command=self.generate_all_reports,
                                           font=('Arial', 10, 'bold'),
                                           bg='#f39c12', fg='white',
                                           relief='raised', bd=3,
                                           padx=15, pady=8,
                                           state='disabled')
        self.generate_all_button.pack(fill='x')
        
        # Output directory section
        output_section = tk.LabelFrame(left_panel, text="📁 Output Directory",
                                      font=('Arial', 12, 'bold'),
                                      bg='#ecf0f1', fg='#2c3e50')
        output_section.pack(fill='x')
        
        self.output_path_var = tk.StringVar()
        self.output_path_var.set("📁 reports/enhanced (default)")
        
        self.output_label = tk.Label(output_section, textvariable=self.output_path_var,
                                    font=('Arial', 9),
                                    bg='#ecf0f1', fg='#7f8c8d',
                                    wraplength=400)
        self.output_label.pack(pady=5)
        
        output_button_frame = tk.Frame(output_section, bg='#ecf0f1')
        output_button_frame.pack(pady=5)
        
        self.select_output_button = tk.Button(output_button_frame, text="📂 Choose Directory",
                                            command=self.select_output_directory,
                                            font=('Arial', 10),
                                            bg='#9b59b6', fg='white',
                                            relief='flat', padx=15, pady=5)
        self.select_output_button.pack(side='left', padx=(0, 5))
        
        self.open_output_button = tk.Button(output_button_frame, text="🔍 Open Folder",
                                          command=self.open_output_directory,
                                          font=('Arial', 10),
                                          bg='#16a085', fg='white',
                                          relief='flat', padx=15, pady=5)
        self.open_output_button.pack(side='right')
        
        # Right panel - Results
        right_panel = tk.Frame(main_frame, bg='#ecf0f1')
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Analysis results
        results_section = tk.LabelFrame(right_panel, text="⚔️ Battle Analysis Results",
                                       font=('Arial', 12, 'bold'),
                                       bg='#ecf0f1', fg='#2c3e50')
        results_section.pack(fill='x', pady=(0, 10))
        
        self.results_text = tk.Text(results_section, height=10,
                                   font=('Courier', 9),
                                   bg='white', fg='#2c3e50',
                                   wrap='word', state='disabled')
        scrollbar_results = tk.Scrollbar(results_section, orient='vertical', command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar_results.set)
        scrollbar_results.pack(side='right', fill='y')
        self.results_text.pack(fill='x', padx=5, pady=5)
        
        # Report status
        reports_section = tk.LabelFrame(right_panel, text="📝 Generated Reports",
                                       font=('Arial', 12, 'bold'),
                                       bg='#ecf0f1', fg='#2c3e50')
        reports_section.pack(fill='both', expand=True)
        
        self.reports_text = scrolledtext.ScrolledText(reports_section, height=15,
                                                     font=('Courier', 9),
                                                     bg='white', fg='#2c3e50',
                                                     wrap='word', state='disabled')
        self.reports_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Select a CSV file to begin")
        status_bar = tk.Label(self.root, textvariable=self.status_var,
                             font=('Arial', 10),
                             bg='#34495e', fg='white',
                             anchor='w', padx=10)
        status_bar.pack(fill='x')
    
    def setup_help_tab(self):
        """Setup the help tab with assessment criteria"""
        # Help content frame with scrollbar
        canvas = tk.Canvas(self.help_tab, bg='#ecf0f1')
        scrollbar = ttk.Scrollbar(self.help_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ecf0f1')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Help content
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
        
        help_label = tk.Label(scrollable_frame, text=help_text,
                             font=('Courier', 10),
                             bg='#ecf0f1', fg='#2c3e50',
                             justify='left', wraplength=1000)
        help_label.pack(padx=20, pady=20, anchor='w')
        
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
    
    def select_output_directory(self):
        """Select output directory for reports"""
        directory = filedialog.askdirectory(
            title='Select Directory for Reports',
            initialdir=str(self.output_directory.parent)
        )
        
        if directory:
            self.output_directory = Path(directory)
            self.output_path_var.set(f"📁 {directory}")
            self.status_var.set(f"Output directory set to: {directory}")
    
    def open_output_directory(self):
        """Open the output directory in file explorer"""
        try:
            self.output_directory.mkdir(parents=True, exist_ok=True)
            
            import platform
            import subprocess
            
            system = platform.system()
            if system == "Windows":
                os.startfile(str(self.output_directory))
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(self.output_directory)])
            else:  # Linux
                subprocess.run(["xdg-open", str(self.output_directory)])
                
            self.status_var.set(f"Opened directory: {self.output_directory}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not open directory:\n{str(e)}")
    
    def select_file(self):
        """Select CSV data file"""
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
            self.load_data(filename)
    
    def load_data(self, filename):
        """Load and validate Fort Moore CSV data file"""
        try:
            self.status_var.set("Loading Fort Moore training data...")
            
            # Load the CSV file
            self.data = pd.read_csv(filename)
            print(f"Loaded CSV with columns: {list(self.data.columns)}")
            
            # Rename columns to match expected format
            rename_dict = {}
            for csv_col, expected_col in self.column_mapping.items():
                if csv_col in self.data.columns:
                    rename_dict[csv_col] = expected_col
            
            if rename_dict:
                self.data = self.data.rename(columns=rename_dict)
                print(f"✅ Mapped {len(rename_dict)} columns to standard format")
            
            # Convert Fall_Detection to numeric (No=0, Yes=1)
            if 'Fall_Detection' in self.data.columns:
                self.data['Fall_Detection'] = self.data['Fall_Detection'].map({'No': 0, 'Yes': 1}).fillna(0)
                print("✅ Converted fall detection to numeric")
            
            # Convert Time_Step to datetime if possible
            if 'Time_Step' in self.data.columns:
                try:
                    self.data['Time_Step'] = pd.to_datetime(self.data['Time_Step'])
                    start_time = self.data['Time_Step'].min()
                    self.data['Time_Step_Numeric'] = (self.data['Time_Step'] - start_time).dt.total_seconds() / 60
                    print("✅ Converted timestamps to datetime")
                except:
                    print("⚠️ Could not convert time format, using original values")
            
            # Update file path display
            self.file_path_var.set(f"📁 {os.path.basename(filename)}")
            
            # Display data information
            self.update_data_info()
            
            # Enable analysis button
            self.analyze_button.config(state='normal')
            
            self.status_var.set(f"Fort Moore data loaded successfully - {len(self.data)} records")
            
        except Exception as e:
            messagebox.showerror("Error Loading File", 
                               f"Could not load the CSV file:\n\n{str(e)}")
            self.status_var.set("Error loading file")
            import traceback
            traceback.print_exc()
    
    def update_data_info(self):
        """Update data information display"""
        if self.data is None:
            return
        
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', 'end')
        
        info = f"""📊 FORT MOORE DATA SUMMARY
════════════════════════════════
Records: {len(self.data):,}
Columns: {len(self.data.columns)}
"""
        
        # Show available callsigns and squads
        if 'Callsign' in self.data.columns:
            callsigns = self.data['Callsign'].nunique()
            info += f"\n👥 Soldiers: {callsigns}"
            
        if 'Platoon' in self.data.columns:
            squads = ', '.join(self.data['Platoon'].unique())
            info += f"\n🏗️  Squads: {squads}"
        
        # Show casualty summary
        if 'Casualty_State' in self.data.columns:
            casualties = len(self.data[self.data['Casualty_State'].isin(['WOUNDED', 'KILL'])])
            info += f"\n💀 Casualties: {casualties}"
        
        # Show data time range
        if 'Time_Step' in self.data.columns:
            try:
                if pd.api.types.is_datetime64_any_dtype(self.data['Time_Step']):
                    start_time = self.data['Time_Step'].min()
                    end_time = self.data['Time_Step'].max()
                    duration = (end_time - start_time).total_seconds() / 60
                    info += f"\n⏰ Duration: {duration:.0f} minutes"
            except:
                pass
        
        self.info_text.insert('1.0', info)
        self.info_text.config(state='disabled')
    
    def debug_failed_reports(self):
        """Debug which soldiers have problematic data"""
        if self.data is None:
            messagebox.showwarning("No Data", "Please load data first.")
            return
        
        debug_window = tk.Toplevel(self.root)
        debug_window.title("🔍 Debug Failed Reports")
        debug_window.geometry("800x600")
        
        debug_text = scrolledtext.ScrolledText(debug_window, font=('Courier', 10))
        debug_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Analyze each soldier
        debug_info = "SOLDIER DATA QUALITY ANALYSIS\n" + "=" * 50 + "\n\n"
        
        callsigns = sorted(self.data['Callsign'].unique())
        problematic_soldiers = []
        
        for callsign in callsigns:
            soldier_data = self.data[self.data['Callsign'] == callsign]
            issues = []
            
            if len(soldier_data) < 10:
                issues.append(f"Low data volume: {len(soldier_data)} records")
            
            if 'Heart_Rate' in soldier_data.columns:
                hr_nulls = soldier_data['Heart_Rate'].isnull().sum()
                if hr_nulls > len(soldier_data) * 0.5:
                    issues.append(f"High heart rate nulls: {hr_nulls}/{len(soldier_data)}")
            
            if issues:
                problematic_soldiers.append(callsign)
                debug_info += f"❌ {callsign} - PROBLEMATIC:\n"
                for issue in issues:
                    debug_info += f"   • {issue}\n"
            else:
                debug_info += f"✅ {callsign} - Data looks good ({len(soldier_data)} records)\n"
            
            debug_info += "\n"
        
        debug_info += f"\nSUMMARY: {len(callsigns)} total, {len(problematic_soldiers)} problematic\n"
        debug_text.insert('1.0', debug_info)
    
    def run_analysis(self):
        """Run battle analysis"""
        if self.data is None:
            return
        
        self.status_var.set("Running analysis...")
        
        def analysis_thread():
            try:
                # Simple battle analysis
                self.battle_analysis = {
                    'total_soldiers': self.data['Callsign'].nunique() if 'Callsign' in self.data.columns else 0,
                    'total_casualties': len(self.data[self.data['Casualty_State'].isin(['WOUNDED', 'KILL'])]) if 'Casualty_State' in self.data.columns else 0,
                    'avg_heart_rate': self.data['Heart_Rate'].mean() if 'Heart_Rate' in self.data.columns else 0
                }
                
                # Update results
                self.root.after(0, self.update_analysis_results)
                self.root.after(0, self.populate_soldier_list)
                self.root.after(0, lambda: self.status_var.set("Analysis complete - Select soldiers for reports"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Analysis Error", str(e)))
                self.root.after(0, lambda: self.status_var.set("Analysis failed"))
        
        threading.Thread(target=analysis_thread, daemon=True).start()
    
    def update_analysis_results(self):
        """Update analysis results display"""
        if not self.battle_analysis:
            return
        
        self.results_text.config(state='normal')
        self.results_text.delete('1.0', 'end')
        
        results = f"""⚔️  BATTLE ANALYSIS RESULTS
════════════════════════════════════

👥 Total Soldiers: {self.battle_analysis['total_soldiers']}
💀 Total Casualties: {self.battle_analysis['total_casualties']}
❤️  Avg Heart Rate: {self.battle_analysis['avg_heart_rate']:.0f} BPM

🎖️  READY FOR REPORT GENERATION
════════════════════════════════════

Select soldiers from the list below and click
"Generate Selected Reports" or "Generate ALL Reports"
"""
        
        self.results_text.insert('1.0', results)
        self.results_text.config(state='disabled')
    
    def populate_soldier_list(self):
        """Populate soldier selection list"""
        if self.data is None or 'Callsign' not in self.data.columns:
            return
        
        self.soldier_listbox.delete(0, 'end')
        callsigns = sorted(self.data['Callsign'].unique())
        
        for callsign in callsigns:
            self.soldier_listbox.insert('end', callsign)
        
        # Enable report generation buttons
        self.generate_selected_button.config(state='normal')
        self.generate_all_button.config(state='normal')
        
        # Update status
        self.status_var.set(f"Ready to generate reports for {len(callsigns)} soldiers")
    
    def generate_selected_reports(self):
        """Generate reports for selected soldiers"""
        selected_indices = self.soldier_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select at least one soldier from the list.")
            return
        
        selected_callsigns = [self.soldier_listbox.get(i) for i in selected_indices]
        self.generate_reports(selected_callsigns)
    
    def generate_all_reports(self):
        """Generate reports for all soldiers"""
        if self.data is None:
            return
        
        callsigns = sorted(self.data['Callsign'].unique())
        
        result = messagebox.askyesno("Generate All Reports", 
                                   f"Generate reports for all {len(callsigns)} soldiers?\n\nThis may take several minutes.")
        if result:
            self.generate_reports(callsigns)
    
    def generate_reports(self, callsigns):
        """Generate reports for specified callsigns"""
        def generation_thread():
            self.root.after(0, lambda: self.status_var.set("Generating reports..."))
            
            # Create reports directory
            reports_dir = self.output_directory / "enhanced_individual_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            successful = 0
            failed = 0
            
            for i, callsign in enumerate(callsigns):
                try:
                    self.root.after(0, lambda c=callsign, idx=i: self.status_var.set(f"Generating {idx+1}/{len(callsigns)}: {c}"))
                    
                    # Get soldier data
                    soldier_data = self.data[self.data['Callsign'] == callsign]
                    
                    # Generate simple report
                    report_path = self.create_simple_report(callsign, soldier_data, reports_dir)
                    
                    # Update report list
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    relative_path = os.path.relpath(report_path, self.output_directory)
                    report_info = f"[{timestamp}] ✅ {callsign} -> {relative_path}\n"
                    self.root.after(0, lambda info=report_info: self.add_report_info(info))
                    
                    successful += 1
                    
                except Exception as e:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    error_info = f"[{timestamp}] ❌ {callsign} - Error: {str(e)}\n"
                    self.root.after(0, lambda info=error_info: self.add_report_info(info))
                    failed += 1
            
            # Final status update
            status = f"Generation complete: {successful} successful, {failed} failed"
            self.root.after(0, lambda: self.status_var.set(status))
            
            # Show completion message
            completion_msg = f"Report generation complete!\n\nSuccessful: {successful}\nFailed: {failed}\n\nReports saved in:\n{reports_dir}\n\nWould you like to open the folder?"
            self.root.after(0, lambda: self.show_completion_dialog(completion_msg, reports_dir))
        
        threading.Thread(target=generation_thread, daemon=True).start()
    
    def create_simple_report(self, callsign, soldier_data, reports_dir):
        """Create a comprehensive HTML report for individual soldier with full statistics"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_soldier_report_{callsign}_{timestamp}.html"
        report_path = reports_dir / filename
        
        try:
            # Calculate comprehensive statistics
            stats = self.calculate_comprehensive_stats(callsign, soldier_data)
            
            # Safety analysis
            safety_analysis = self.analyze_soldier_safety(soldier_data)
            
            # Performance score
            performance_score = self.calculate_performance_score(stats, safety_analysis)
            
            # Create comprehensive HTML report
            html = self.generate_comprehensive_html_report(callsign, stats, safety_analysis, performance_score, timestamp)
            
            # Save the report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            return str(report_path)
            
        except Exception as e:
            print(f"Error creating report for {callsign}: {e}")
            # Create basic report if comprehensive fails
            return self.create_basic_fallback_report(callsign, soldier_data, reports_dir, timestamp)
    
    def calculate_comprehensive_stats(self, callsign, soldier_data):
        """Calculate comprehensive soldier statistics"""
        stats = {
            'callsign': callsign,
            'total_records': len(soldier_data),
        }
        
        # Physical activity metrics
        if 'Step_Count' in soldier_data.columns:
            step_data = soldier_data['Step_Count'].dropna()
            if len(step_data) > 0:
                stats['total_steps'] = step_data.sum()
                stats['avg_steps'] = step_data.mean()
                stats['max_steps'] = step_data.max()
                stats['min_steps'] = step_data.min()
        
        # Heart rate analysis
        if 'Heart_Rate' in soldier_data.columns:
            hr_data = soldier_data['Heart_Rate'].dropna()
            if len(hr_data) > 0:
                stats['min_heart_rate'] = hr_data.min()
                stats['avg_heart_rate'] = hr_data.mean()
                stats['max_heart_rate'] = hr_data.max()
                stats['abnormal_hr_low'] = len(hr_data[hr_data < 60])
                stats['abnormal_hr_high'] = len(hr_data[hr_data > 190])
                stats['abnormal_hr_total'] = stats['abnormal_hr_low'] + stats['abnormal_hr_high']
                stats['hr_alert_triggered'] = stats['abnormal_hr_total'] > 0
                
                # Heart rate zones
                stats['hr_zones'] = {
                    'rest': len(hr_data[hr_data < 60]),
                    'normal': len(hr_data[(hr_data >= 60) & (hr_data < 100)]),
                    'elevated': len(hr_data[(hr_data >= 100) & (hr_data < 150)]),
                    'high': len(hr_data[(hr_data >= 150) & (hr_data < 180)]),
                    'extreme': len(hr_data[(hr_data >= 180) & (hr_data < 190)]),
                    'critical': len(hr_data[hr_data >= 190])
                }
        
        # Temperature analysis
        if 'Temperature' in soldier_data.columns:
            temp_data = soldier_data['Temperature'].dropna()
            if len(temp_data) > 0:
                stats['min_temperature'] = temp_data.min()
                stats['avg_temperature'] = temp_data.mean()
                stats['max_temperature'] = temp_data.max()
                stats['heat_stress_incidents'] = len(temp_data[temp_data > 104])
                stats['cold_stress_incidents'] = len(temp_data[temp_data < 95])
        
        # Equipment status
        if 'Battery' in soldier_data.columns:
            battery_data = soldier_data['Battery'].dropna()
            if len(battery_data) > 0:
                stats['min_battery'] = battery_data.min()
                stats['avg_battery'] = battery_data.mean()
                stats['max_battery'] = battery_data.max()
                stats['low_battery_incidents'] = len(battery_data[battery_data < 20])
                stats['critical_battery_incidents'] = len(battery_data[battery_data < 10])
        
        # Communication quality
        if 'RSSI' in soldier_data.columns:
            rssi_data = soldier_data['RSSI'].dropna()
            if len(rssi_data) > 0:
                stats['avg_rssi'] = rssi_data.mean()
                stats['min_rssi'] = rssi_data.min()
                stats['max_rssi'] = rssi_data.max()
                
                # Communication quality rating
                avg_rssi = stats['avg_rssi']
                if avg_rssi > -60:
                    stats['comm_quality'] = 'Excellent'
                elif avg_rssi > -70:
                    stats['comm_quality'] = 'Good'
                elif avg_rssi > -80:
                    stats['comm_quality'] = 'Fair'
                else:
                    stats['comm_quality'] = 'Poor'
        
        # Posture and movement analysis
        if 'Posture' in soldier_data.columns:
            posture_data = soldier_data['Posture'].dropna()
            if len(posture_data) > 0:
                posture_counts = posture_data.value_counts()
                stats['posture_distribution'] = posture_counts.to_dict()
                stats['dominant_posture'] = posture_counts.index[0] if len(posture_counts) > 0 else 'Unknown'
                
                # Calculate posture changes
                posture_changes = 0
                for i in range(1, len(posture_data)):
                    if posture_data.iloc[i] != posture_data.iloc[i-1]:
                        posture_changes += 1
                stats['posture_changes'] = posture_changes
                stats['posture_stability'] = 'Excellent' if posture_changes < 10 else 'Good' if posture_changes < 20 else 'Fair'
        
        # Combat effectiveness
        if 'Casualty_State' in soldier_data.columns:
            casualty_data = soldier_data['Casualty_State'].dropna()
            if len(casualty_data) > 0:
                stats['final_status'] = casualty_data.iloc[-1]
                
                # Count status changes
                casualty_changes = 0
                for i in range(1, len(casualty_data)):
                    if casualty_data.iloc[i] != casualty_data.iloc[i-1]:
                        casualty_changes += 1
                stats['casualty_events'] = casualty_changes
        
        # Combat engagements
        if 'Shooter_Callsign' in soldier_data.columns:
            engagement_data = soldier_data['Shooter_Callsign'].dropna()
            stats['combat_engagements'] = len(engagement_data)
            if len(engagement_data) > 0:
                stats['unique_shooters'] = engagement_data.nunique()
        
        # Weapon information
        if 'Weapon' in soldier_data.columns:
            weapon_data = soldier_data['Weapon'].dropna()
            if len(weapon_data) > 0:
                stats['primary_weapon'] = weapon_data.mode().iloc[0] if not weapon_data.mode().empty else 'Unknown'
        
        # Fall incidents
        if 'Fall_Detection' in soldier_data.columns:
            stats['fall_incidents'] = soldier_data['Fall_Detection'].sum()
        
        # Mission duration
        if 'Time_Step' in soldier_data.columns:
            try:
                if pd.api.types.is_datetime64_any_dtype(soldier_data['Time_Step']):
                    start_time = soldier_data['Time_Step'].min()
                    end_time = soldier_data['Time_Step'].max()
                    stats['mission_duration'] = (end_time - start_time).total_seconds() / 60  # minutes
            except:
                pass
        
        return stats
    
    def analyze_soldier_safety(self, soldier_data):
        """Analyze soldier safety metrics"""
        safety = {
            'overall_safety_score': 100,
            'temperature_risk': 'LOW',
            'physiological_stress': 'LOW',
            'heart_rate_alerts': [],
            'medical_alerts': [],
            'injury_risk': 'LOW',
            'equipment_risk': 'LOW'
        }
        
        # Temperature safety analysis
        if 'Temperature' in soldier_data.columns:
            temp_data = soldier_data['Temperature'].dropna()
            if len(temp_data) > 0:
                max_temp = temp_data.max()
                min_temp = temp_data.min()
                
                if max_temp > 104:  # Heat stroke risk
                    safety['temperature_risk'] = 'CRITICAL'
                    safety['overall_safety_score'] -= 25
                    safety['medical_alerts'].append(f"HEAT EMERGENCY: {max_temp:.1f}°F - Immediate cooling required")
                elif max_temp > 100:
                    safety['temperature_risk'] = 'HIGH'
                    safety['overall_safety_score'] -= 15
                    safety['medical_alerts'].append(f"Heat stress detected: {max_temp:.1f}°F")
                
                if min_temp < 95:  # Hypothermia risk
                    safety['overall_safety_score'] -= 10
                    safety['medical_alerts'].append(f"Cold stress detected: {min_temp:.1f}°F")
        
        # Heart rate safety analysis
        if 'Heart_Rate' in soldier_data.columns:
            hr_data = soldier_data['Heart_Rate'].dropna()
            if len(hr_data) > 0:
                max_hr = hr_data.max()
                min_hr = hr_data.min()
                
                if max_hr > 190:
                    safety['physiological_stress'] = 'CRITICAL'
                    safety['overall_safety_score'] -= 20
                    safety['heart_rate_alerts'].append(f"CARDIAC EMERGENCY: {max_hr:.0f} BPM")
                    safety['medical_alerts'].append(f"Immediate medical evaluation required - HR: {max_hr:.0f} BPM")
                elif max_hr > 180:
                    safety['physiological_stress'] = 'HIGH'
                    safety['overall_safety_score'] -= 10
                    safety['heart_rate_alerts'].append(f"Elevated heart rate: {max_hr:.0f} BPM")
                
                if min_hr < 60 and min_hr > 0:
                    safety['heart_rate_alerts'].append(f"Low heart rate detected: {min_hr:.0f} BPM")
                    safety['medical_alerts'].append(f"Bradycardia evaluation recommended - HR: {min_hr:.0f} BPM")
        
        # Equipment safety analysis
        if 'Battery' in soldier_data.columns:
            battery_data = soldier_data['Battery'].dropna()
            if len(battery_data) > 0:
                min_battery = battery_data.min()
                if min_battery < 10:
                    safety['equipment_risk'] = 'CRITICAL'
                    safety['overall_safety_score'] -= 15
                    safety['medical_alerts'].append(f"Equipment failure risk - Battery: {min_battery}%")
                elif min_battery < 20:
                    safety['equipment_risk'] = 'HIGH'
                    safety['overall_safety_score'] -= 8
        
        return safety
    
    def calculate_performance_score(self, stats, safety_analysis):
        """Calculate comprehensive performance score"""
        score = 100
        deductions = []
        bonuses = []
        
        # Activity performance
        if 'avg_steps' in stats:
            if stats['avg_steps'] < 50:
                deduction = 15
                score -= deduction
                deductions.append(f"Low activity: -{deduction} points ({stats['avg_steps']:.0f} avg steps)")
            elif stats['avg_steps'] < 100:
                deduction = 10
                score -= deduction
                deductions.append(f"Moderate activity: -{deduction} points ({stats['avg_steps']:.0f} avg steps)")
        
        # Casualty status impact
        final_status = stats.get('final_status', 'GOOD')
        if final_status == 'WOUNDED':
            deduction = 10
            score -= deduction
            deductions.append(f"Wounded status: -{deduction} points")
        elif final_status in ['KILL', 'KIA']:
            deduction = 20
            score -= deduction
            deductions.append(f"KIA status: -{deduction} points")
        
        # Equipment readiness
        if 'avg_battery' in stats:
            if stats['avg_battery'] < 20:
                deduction = 15
                score -= deduction
                deductions.append(f"Critical battery: -{deduction} points ({stats['avg_battery']:.1f}%)")
            elif stats['avg_battery'] < 40:
                deduction = 8
                score -= deduction
                deductions.append(f"Low battery: -{deduction} points ({stats['avg_battery']:.1f}%)")
        
        # Communication quality
        if 'comm_quality' in stats:
            if stats['comm_quality'] == 'Poor':
                deduction = 5
                score -= deduction
                deductions.append(f"Poor communication: -{deduction} points")
            elif stats['comm_quality'] == 'Excellent':
                bonus = 3
                score += bonus
                bonuses.append(f"Excellent communication: +{bonus} points")
        
        # Combat engagement bonus
        if 'combat_engagements' in stats and stats['combat_engagements'] > 0:
            bonus = min(5, stats['combat_engagements'])
            score += bonus
            bonuses.append(f"Combat engagement: +{bonus} points ({stats['combat_engagements']} engagements)")
        
        # Medical alerts (reduced penalty - safety focused)
        medical_alerts = len(safety_analysis.get('medical_alerts', []))
        if medical_alerts > 0:
            deduction = medical_alerts * 3  # Reduced from 5 to 3
            score -= deduction
            deductions.append(f"Medical alerts: -{deduction} points ({medical_alerts} alerts)")
        
        # Safety score impact (20% of deficit)
        safety_score = safety_analysis.get('overall_safety_score', 100)
        if safety_score < 100:
            deduction = int((100 - safety_score) * 0.2)
            score -= deduction
            deductions.append(f"Safety concerns: -{deduction} points")
        
        final_score = max(0, min(100, score))
        
        # Store breakdown
        stats['performance_breakdown'] = {
            'starting_score': 100,
            'final_score': final_score,
            'total_deductions': sum([int(d.split('-')[1].split(' ')[0]) for d in deductions if '-' in d]),
            'total_bonuses': sum([int(b.split('+')[1].split(' ')[0]) for b in bonuses if '+' in b]),
            'deduction_details': deductions,
            'bonus_details': bonuses
        }
        
        return final_score
    
    def generate_comprehensive_html_report(self, callsign, stats, safety_analysis, performance_score, timestamp):
        """Generate comprehensive HTML report with all statistics"""
        
        # Get performance status
        if performance_score >= 90:
            status = "EXCELLENT - Exemplary performance"
            status_color = "#27ae60"
        elif performance_score >= 80:
            status = "GOOD - Above average performance"
            status_color = "#f39c12"
        elif performance_score >= 70:
            status = "SATISFACTORY - Meets requirements"
            status_color = "#e67e22"
        elif performance_score >= 60:
            status = "NEEDS IMPROVEMENT - Below standard"
            status_color = "#e74c3c"
        else:
            status = "CRITICAL - Immediate attention required"
            status_color = "#c0392b"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Enhanced Soldier Report - {callsign}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f2f5; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); max-width: 1200px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #2c3e50, #3498db); color: white; padding: 25px; text-align: center; border-radius: 8px; margin-bottom: 25px; }}
                .performance-score {{ font-size: 4em; font-weight: bold; color: {status_color}; margin: 20px 0; text-align: center; }}
                .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin: 25px 0; }}
                .metric-card {{ background: #f8f9fa; padding: 25px; border-radius: 10px; text-align: center; border-left: 5px solid #3498db; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .metric-value {{ font-size: 2.5em; font-weight: bold; color: #2c3e50; margin: 10px 0; }}
                .metric-label {{ color: #7f8c8d; font-size: 1em; font-weight: 500; }}
                .section {{ background: white; padding: 25px; margin: 20px 0; border-radius: 10px; border-left: 5px solid #3498db; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }}
                .section h2 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; }}
                .alert-info {{ background: #e3f2fd; border: 2px solid #2196f3; border-radius: 8px; padding: 15px; margin: 10px 0; }}
                .alert-warning {{ background: #fff3e0; border: 2px solid #ff9800; border-radius: 8px; padding: 15px; margin: 10px 0; }}
                .alert-critical {{ background: #ffebee; border: 2px solid #f44336; border-radius: 8px; padding: 15px; margin: 10px 0; }}
                .breakdown-item {{ background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 4px solid #3498db; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎖️ Enhanced Individual Soldier Report</h1>
                    <h2>Soldier: {callsign}</h2>
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Analysis Period: {stats.get('total_records', 0)} data points</p>
                </div>
                
                <!-- PERFORMANCE SUMMARY -->
                <div class="section">
                    <h2>📊 Performance Summary</h2>
                    <div class="performance-score">{performance_score:.0f}/100</div>
                    <p style="text-align: center; font-size: 1.2em; color: {status_color}; font-weight: bold;">
                        {status}
                    </p>
                    
                    {self.generate_performance_breakdown_html(stats)}
                </div>
                
                <!-- KEY METRICS -->
                <div class="section">
                    <h2>📈 Key Performance Metrics</h2>
                    <div class="metric-grid">
                        <div class="metric-card">
                            <div class="metric-value">{stats.get('total_records', 0):,}</div>
                            <div class="metric-label">Total Data Points</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{stats.get('total_steps', 0):,}</div>
                            <div class="metric-label">Total Steps</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{stats.get('avg_heart_rate', 0):.0f}</div>
                            <div class="metric-label">Avg Heart Rate (BPM)</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{stats.get('final_status', 'Unknown')}</div>
                            <div class="metric-label">Final Status</div>
                        </div>
                    </div>
                </div>
                
                <!-- HEART RATE ANALYSIS -->
                <div class="section">
                    <h2>❤️ Heart Rate Analysis</h2>
                    {self.generate_heart_rate_analysis_html(stats, safety_analysis)}
                </div>
                
                <!-- PHYSICAL PERFORMANCE -->
                <div class="section">
                    <h2>🏃 Physical Performance</h2>
                    {self.generate_physical_performance_html(stats)}
                </div>
                
                <!-- EQUIPMENT STATUS -->
                <div class="section">
                    <h2>🔋 Equipment & Communication</h2>
                    {self.generate_equipment_status_html(stats, safety_analysis)}
                </div>
                
                <!-- POSTURE & MOVEMENT -->
                <div class="section">
                    <h2>🤸 Posture & Movement Analysis</h2>
                    {self.generate_posture_analysis_html(stats)}
                </div>
                
                <!-- SAFETY ANALYSIS -->
                <div class="section">
                    <h2>🛡️ Safety Analysis</h2>
                    {self.generate_safety_analysis_html(safety_analysis)}
                </div>
                
                <!-- MEDICAL RECOMMENDATIONS -->
                <div class="section">
                    <h2>💊 Medical Recommendations</h2>
                    {self.generate_medical_recommendations_html(stats, safety_analysis)}
                </div>
                
                <footer style="text-align: center; margin-top: 30px; padding: 25px; background: #2c3e50; color: white; border-radius: 8px;">
                    <p><strong>🎖️ Enhanced Individual Soldier Report System</strong></p>
                    <p>Advanced Analytics for Military Operations</p>
                    <p>Report ID: {callsign}-{timestamp} | Classification: FOR OFFICIAL USE ONLY</p>
                </footer>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def generate_performance_breakdown_html(self, stats):
        """Generate performance breakdown section"""
        if 'performance_breakdown' not in stats:
            return '<p>Performance breakdown not available</p>'
        
        breakdown = stats['performance_breakdown']
        
        html = f'''
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>🔍 Performance Score Breakdown</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <h4>📊 Score Calculation</h4>
                    <div class="breakdown-item">Starting Score: <strong>100 points</strong></div>
                    <div class="breakdown-item">Total Deductions: <strong>-{breakdown.get('total_deductions', 0)} points</strong></div>
                    <div class="breakdown-item">Total Bonuses: <strong>+{breakdown.get('total_bonuses', 0)} points</strong></div>
                    <div class="breakdown-item">Final Score: <strong>{breakdown.get('final_score', 0):.0f}/100 points</strong></div>
                </div>
                <div>
                    <h4>📋 Detailed Changes</h4>
        '''
        
        # Add deductions
        for deduction in breakdown.get('deduction_details', []):
            html += f'<div style="background: #ffebee; padding: 8px; margin: 3px 0; border-radius: 4px; border-left: 3px solid #f44336;"><small>{deduction}</small></div>'
        
        # Add bonuses
        for bonus in breakdown.get('bonus_details', []):
            html += f'<div style="background: #e8f5e8; padding: 8px; margin: 3px 0; border-radius: 4px; border-left: 3px solid #4caf50;"><small>{bonus}</small></div>'
        
        html += '</div></div></div>'
        return html
    
    def generate_heart_rate_analysis_html(self, stats, safety_analysis):
        """Generate heart rate analysis section"""
        if 'min_heart_rate' not in stats:
            return '<p>Heart rate data not available</p>'
        
        html = f'''
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value" style="color: #2196f3;">{stats.get('min_heart_rate', 0):.0f}</div>
                <div class="metric-label">Minimum BPM</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #4caf50;">{stats.get('avg_heart_rate', 0):.0f}</div>
                <div class="metric-label">Average BPM</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #ff5722;">{stats.get('max_heart_rate', 0):.0f}</div>
                <div class="metric-label">Maximum BPM</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats.get('abnormal_hr_total', 0)}</div>
                <div class="metric-label">Abnormal Readings</div>
            </div>
        </div>
        '''
        
        # Heart rate zones
        if 'hr_zones' in stats:
            html += '<h4>📊 Heart Rate Zone Distribution</h4>'
            html += '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 15px 0;">'
            zones = stats['hr_zones']
            for zone, count in zones.items():
                html += f'<div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 5px;"><strong>{zone.title()}</strong><br>{count}</div>'
            html += '</div>'
        
        # Medical alerts
        hr_alerts = safety_analysis.get('heart_rate_alerts', [])
        if hr_alerts:
            html += '<div class="alert-warning"><h4>⚠️ Heart Rate Alerts (Medical Monitoring)</h4>'
            for alert in hr_alerts:
                html += f'<p>• {alert}</p>'
            html += '<p><em>Note: Heart rate alerts are for medical monitoring and do not affect performance scores.</em></p></div>'
        else:
            html += '<div class="alert-info"><p>✅ All heart rate readings within acceptable range (60-190 BPM)</p></div>'
        
        return html
    
    def generate_physical_performance_html(self, stats):
        """Generate physical performance section"""
        html = '<div class="metric-grid">'
        
        if 'total_steps' in stats:
            html += f'''
            <div class="metric-card">
                <div class="metric-value">{stats['total_steps']:,}</div>
                <div class="metric-label">Total Steps</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats.get('avg_steps', 0):.0f}</div>
                <div class="metric-label">Average Steps</div>
            </div>
            '''
        
        if 'mission_duration' in stats:
            html += f'''
            <div class="metric-card">
                <div class="metric-value">{stats['mission_duration']:.0f}</div>
                <div class="metric-label">Mission Duration (min)</div>
            </div>
            '''
        
        if 'fall_incidents' in stats:
            html += f'''
            <div class="metric-card">
                <div class="metric-value">{stats['fall_incidents']}</div>
                <div class="metric-label">Fall Incidents</div>
            </div>
            '''
        
        html += '</div>'
        
        # Activity assessment
        if 'avg_steps' in stats:
            avg_steps = stats['avg_steps']
            if avg_steps >= 100:
                html += '<div class="alert-info"><p>✅ Excellent activity level - Above 100 steps average</p></div>'
            elif avg_steps >= 50:
                html += '<div class="alert-warning"><p>⚠️ Moderate activity level - Consider increasing physical activity</p></div>'
            else:
                html += '<div class="alert-critical"><p>❌ Low activity level - Physical conditioning recommended</p></div>'
        
        return html
    
    def generate_equipment_status_html(self, stats, safety_analysis):
        """Generate equipment status section"""
        html = '<div class="metric-grid">'
        
        if 'avg_battery' in stats:
            battery_color = '#4caf50' if stats['avg_battery'] > 60 else '#ff9800' if stats['avg_battery'] > 20 else '#f44336'
            html += f'''
            <div class="metric-card">
                <div class="metric-value" style="color: {battery_color};">{stats['avg_battery']:.1f}%</div>
                <div class="metric-label">Average Battery</div>
            </div>
            '''
        
        if 'avg_rssi' in stats:
            html += f'''
            <div class="metric-card">
                <div class="metric-value">{stats['avg_rssi']:.0f}</div>
                <div class="metric-label">Avg RSSI (dBm)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats.get('comm_quality', 'Unknown')}</div>
                <div class="metric-label">Comm Quality</div>
            </div>
            '''
        
        if 'primary_weapon' in stats:
            html += f'''
            <div class="metric-card">
                <div class="metric-value" style="font-size: 1.5em;">{stats['primary_weapon']}</div>
                <div class="metric-label">Primary Weapon</div>
            </div>
            '''
        
        html += '</div>'
        
        # Equipment alerts
        equipment_alerts = []
        if 'low_battery_incidents' in stats and stats['low_battery_incidents'] > 0:
            equipment_alerts.append(f"🔋 {stats['low_battery_incidents']} low battery incidents detected")
        
        if equipment_alerts:
            html += '<div class="alert-warning"><h4>⚠️ Equipment Alerts</h4>'
            for alert in equipment_alerts:
                html += f'<p>• {alert}</p>'
            html += '</div>'
        
        return html
    
    def generate_posture_analysis_html(self, stats):
        """Generate posture analysis section"""
        html = '<div class="metric-grid">'
        
        if 'posture_changes' in stats:
            html += f'''
            <div class="metric-card">
                <div class="metric-value">{stats['posture_changes']}</div>
                <div class="metric-label">Posture Changes</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats.get('posture_stability', 'Unknown')}</div>
                <div class="metric-label">Stability Level</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats.get('dominant_posture', 'Unknown')}</div>
                <div class="metric-label">Dominant Posture</div>
            </div>
            '''
        
        html += '</div>'
        
        # Posture distribution
        if 'posture_distribution' in stats:
            html += '<h4>📊 Posture Distribution</h4>'
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px;">'
            for posture, count in stats['posture_distribution'].items():
                html += f'''
                <div style="text-align: center; background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <strong>{posture}</strong><br>
                    <span style="font-size: 1.5em; color: #2c3e50;">{count}</span>
                </div>
                '''
            html += '</div>'
        
        return html
    
    def generate_safety_analysis_html(self, safety_analysis):
        """Generate safety analysis section"""
        html = f'''
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{safety_analysis['overall_safety_score']:.0f}/100</div>
                <div class="metric-label">Safety Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{safety_analysis['temperature_risk']}</div>
                <div class="metric-label">Temperature Risk</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{safety_analysis['physiological_stress']}</div>
                <div class="metric-label">Physiological Stress</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{safety_analysis['equipment_risk']}</div>
                <div class="metric-label">Equipment Risk</div>
            </div>
        </div>
        '''
        
        # Medical alerts
        medical_alerts = safety_analysis.get('medical_alerts', [])
        if medical_alerts:
            html += '<div class="alert-warning"><h4>🏥 Medical Alerts</h4>'
            for alert in medical_alerts:
                html += f'<p>• {alert}</p>'
            html += '</div>'
        
        return html
    
    def generate_medical_recommendations_html(self, stats, safety_analysis):
        """Generate medical recommendations section"""
        recommendations = []
        
        # Heart rate recommendations
        if stats.get('hr_alert_triggered', False):
            if stats.get('abnormal_hr_high', 0) > 0:
                recommendations.append("🚨 IMMEDIATE: Medical evaluation for high heart rate readings")
            if stats.get('abnormal_hr_low', 0) > 0:
                recommendations.append("⚠️ MEDICAL: Evaluate for bradycardia or cardiac issues")
        
        # Temperature recommendations
        if 'heat_stress_incidents' in stats and stats['heat_stress_incidents'] > 0:
            recommendations.append("🌡️ HEAT: Monitor for heat exhaustion, increase hydration")
        if 'cold_stress_incidents' in stats and stats['cold_stress_incidents'] > 0:
            recommendations.append("🥶 COLD: Monitor for hypothermia, implement warming protocols")
        
        # Equipment recommendations
        if 'low_battery_incidents' in stats and stats['low_battery_incidents'] > 0:
            recommendations.append("🔋 EQUIPMENT: Replace/recharge batteries, check equipment")
        
        # General recommendations
        if not recommendations:
            recommendations.append("✅ Continue current monitoring protocols")
            recommendations.append("📊 Maintain regular health status checks")
        
        html = '<div style="background: #e8f5e8; padding: 20px; border-radius: 8px;">'
        for rec in recommendations:
            priority = '🚨 CRITICAL' if '🚨' in rec else '⚠️ IMPORTANT' if '⚠️' in rec else 'ℹ️ ROUTINE'
            html += f'<div class="breakdown-item"><strong>{priority}:</strong> {rec}</div>'
        html += '</div>'
        
        return html
    
    def create_basic_fallback_report(self, callsign, soldier_data, reports_dir, timestamp):
        """Create basic fallback report if comprehensive fails"""
        filename = f"basic_report_{callsign}_{timestamp}.html"
        report_path = reports_dir / filename
        
        total_records = len(soldier_data)
        avg_heart_rate = soldier_data['Heart_Rate'].mean() if 'Heart_Rate' in soldier_data.columns else 0
        final_status = soldier_data['Casualty_State'].iloc[-1] if 'Casualty_State' in soldier_data.columns and len(soldier_data) > 0 else 'Unknown'
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Basic Report - {callsign}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f0f2f5; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; max-width: 800px; margin: 0 auto; }}
                .header {{ background: #3498db; color: white; padding: 20px; text-align: center; border-radius: 8px; margin-bottom: 20px; }}
                .metric {{ background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #3498db; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎖️ Soldier Performance Report</h1>
                    <h2>{callsign}</h2>
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="metric">
                    <h3>📊 Basic Statistics</h3>
                    <p><strong>Total Data Points:</strong> {total_records}</p>
                    <p><strong>Average Heart Rate:</strong> {avg_heart_rate:.1f} BPM</p>
                    <p><strong>Final Status:</strong> {final_status}</p>
                </div>
                
                <div class="metric">
                    <h3>🎯 Assessment Summary</h3>
                    <p>This soldier's data has been processed and analyzed according to military assessment criteria.</p>
                    <p>For detailed scoring methodology, refer to the system's assessment criteria documentation.</p>
                </div>
                
                <footer style="text-align: center; margin-top: 30px; padding: 20px; background: #34495e; color: white; border-radius: 8px;">
                    <p><strong>🎖️ Enhanced Individual Soldier Report System</strong></p>
                    <p>Report ID: {callsign}-{timestamp}</p>
                </footer>
            </div>
        </body>
        </html>
        """
        
        # Save the report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return str(report_path)
    
    def show_completion_dialog(self, message, reports_dir):
        """Show completion dialog with option to open folder"""
        result = messagebox.askyesno("Generation Complete", message)
        if result:
            try:
                import platform
                import subprocess
                
                system = platform.system()
                if system == "Windows":
                    os.startfile(str(reports_dir))
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", str(reports_dir)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(reports_dir)])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder:\n{str(e)}")
    
    def add_report_info(self, info):
        """Add report information to the text widget"""
        self.reports_text.config(state='normal')
        self.reports_text.insert('end', info)
        self.reports_text.see('end')
        self.reports_text.config(state='disabled')
    
    def run(self):
        """Run the GUI application"""
        print("🎖️ Enhanced Individual Soldier Report System - Complete Version")
        print("=" * 70)
        print("Starting GUI with visible report generation buttons...")
        
        self.root.mainloop()


def main():
    """Main function"""
    try:
        app = EnhancedReportSystemGUI()
        app.run()
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()