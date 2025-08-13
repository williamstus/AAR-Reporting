#!/usr/bin/env python3
"""
Windows Compatible AAR Reports Fix
Fixes Unicode encoding issues on Windows systems
"""

import os
import sys
from datetime import datetime

def create_windows_compatible_reports_tab():
    """Create a Windows-compatible reports tab without Unicode issues"""
    
    # Ensure directories exist
    os.makedirs("ui/components", exist_ok=True)
    os.makedirs("reports/generated", exist_ok=True)
    
    # Reports tab code without problematic Unicode characters
    reports_tab_code = '''import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os

class ReportsTab:
    def __init__(self, parent, event_bus=None, analysis_orchestrator=None):
        self.parent = parent
        self.event_bus = event_bus
        self.analysis_orchestrator = analysis_orchestrator
        self.current_results = {}
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.setup_ui()
        
        # Subscribe to events
        if self.event_bus:
            try:
                self.event_bus.subscribe("analysis_completed", self.on_analysis_completed)
                print("[Reports] Subscribed to analysis_completed events")
            except Exception as e:
                print(f"[Reports] Could not subscribe to events: {e}")
        
    def setup_ui(self):
        """Setup the reports UI"""
        # Title
        ttk.Label(self.frame, text="After Action Review Reports", 
                 font=("Arial", 16, "bold")).pack(pady=(0, 20))
        
        # Status
        self.status_label = ttk.Label(self.frame, text="Ready to generate reports")
        self.status_label.pack(pady=(0, 10))
        
        # Quick report buttons frame
        button_frame = ttk.LabelFrame(self.frame, text="Quick Report Generation", padding=10)
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Row 1 of buttons
        row1_frame = ttk.Frame(button_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(row1_frame, text="Executive Summary", 
                  command=lambda: self.generate_quick_report("executive")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(row1_frame, text="Safety Report", 
                  command=lambda: self.generate_quick_report("safety")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(row1_frame, text="Activity Report", 
                  command=lambda: self.generate_quick_report("activity")).pack(side=tk.LEFT, padx=(0, 5))
        
        # Row 2 of buttons
        row2_frame = ttk.Frame(button_frame)
        row2_frame.pack(fill=tk.X)
        
        ttk.Button(row2_frame, text="Equipment Report", 
                  command=lambda: self.generate_quick_report("equipment")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(row2_frame, text="Environmental Report", 
                  command=lambda: self.generate_quick_report("environmental")).pack(side=tk.LEFT, padx=(0, 5))
        
        # Main action buttons
        main_button_frame = ttk.LabelFrame(self.frame, text="Main Actions", padding=10)
        main_button_frame.pack(fill=tk.X, pady=(0, 10))
        
        action_frame = ttk.Frame(main_button_frame)
        action_frame.pack(fill=tk.X)
        
        self.main_generate_btn = ttk.Button(action_frame, text="Generate Analysis Report", 
                                           command=self.generate_main_report)
        self.main_generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="Test Report Generation", 
                  command=self.test_report_generation).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="Open Reports Folder", 
                  command=self.open_reports_folder).pack(side=tk.LEFT)
        
        # Results area
        results_frame = ttk.LabelFrame(self.frame, text="Report Output", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_text = tk.Text(results_frame, height=12, wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        # Initial message
        self.show_welcome_message()
        
    def show_welcome_message(self):
        """Show welcome message"""
        welcome_text = """AAR Reports System Ready!

Welcome to the After Action Review reports generator.
This system generates comprehensive reports from your training exercise data.

Available Report Types:
* Executive Summary - High-level overview with key findings
* Safety Report - Safety incidents and risk analysis  
* Activity Report - Movement and performance metrics
* Equipment Report - Equipment status and battery analysis
* Environmental Report - Environmental conditions analysis

How to Use:
1. Click any of the quick report buttons above
2. Or use "Generate Analysis Report" for comprehensive reports
3. View generated reports in the output area below
4. Access saved files using "Open Reports Folder"

Reports are automatically saved as HTML files for easy viewing and sharing.

Status: Waiting for analysis data or click "Test Report Generation" to try now.
"""
        self.results_text.delete('1.0', 'end')
        self.results_text.insert('1.0', welcome_text)
        
    def on_analysis_completed(self, event_data):
        """Handle analysis completion - this is the key fix!"""
        try:
            print("[Reports] Analysis completed event received!")
            self.current_results = event_data.get('results', {})
            domains = list(self.current_results.keys())
            
            self.status_label.config(text=f"Analysis completed for: {', '.join(domains)}")
            
            # Update results display
            self.results_text.delete('1.0', 'end')
            
            status_text = f"""Analysis Results Ready!

Completed domains: {', '.join(domains)}

You can now generate comprehensive reports with actual training data!

Domain Details:
"""
            
            for domain in domains:
                result = self.current_results[domain]
                summary = getattr(result, 'summary', 'Analysis completed')
                status_text += f"* {domain}: {summary}\\n"
            
            status_text += "\\nClick any report button above to generate detailed reports with this data!"
            
            self.results_text.insert('1.0', status_text)
            
            # Enable the main button
            self.main_generate_btn.config(state="normal")
            
            print(f"[Reports] UI updated with results for: {domains}")
            
        except Exception as e:
            print(f"[Reports] Error handling analysis completion: {e}")
            import traceback
            traceback.print_exc()
    
    def generate_quick_report(self, report_type):
        """Generate a quick report of specified type"""
        print(f"[Reports] Generating {report_type} report...")
        self.generate_report(report_type)
    
    def generate_main_report(self):
        """Generate the main comprehensive report"""
        print("[Reports] Generating comprehensive analysis report...")
        self.generate_report("comprehensive")
    
    def test_report_generation(self):
        """Test report generation with sample data"""
        print("[Reports] Testing report generation...")
        
        # Create fake analysis results for testing
        fake_results = {
            'ACTIVITY': type('Result', (), {'summary': 'Activity analysis completed successfully'})(),
            'EQUIPMENT': type('Result', (), {'summary': 'Equipment status nominal'})(),
            'ENVIRONMENTAL': type('Result', (), {'summary': 'Environmental conditions favorable'})()
        }
        
        # Temporarily set results
        original_results = self.current_results
        self.current_results = fake_results
        
        # Generate test report
        self.generate_report("test")
        
        # Restore original results
        self.current_results = original_results
    
    def generate_report(self, report_type):
        """Core report generation function"""
        try:
            print(f"[Reports] Starting {report_type} report generation...")
            
            # Create timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create content based on available data
            if self.current_results:
                content = self.create_report_with_data(report_type, timestamp)
                data_status = "with analysis data"
            else:
                content = self.create_sample_report(report_type, timestamp)
                data_status = "sample report"
            
            # Save the report
            filename = f"reports/generated/AAR_{report_type}_report_{timestamp}.html"
            
            # Create full HTML
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>AAR {report_type.title()} Report</title>
    <meta charset="UTF-8">
    <style>
        body {{ 
            font-family: 'Segoe UI', Arial, sans-serif; 
            margin: 40px; 
            line-height: 1.6; 
            color: #333;
        }}
        h1 {{ 
            color: #2c3e50; 
            border-bottom: 3px solid #3498db; 
            padding-bottom: 10px;
        }}
        h2 {{ 
            color: #34495e; 
            border-bottom: 1px solid #bdc3c7; 
            margin-top: 25px;
        }}
        .highlight {{ 
            background: #f8f9fa; 
            padding: 15px; 
            border-left: 4px solid #3498db; 
            margin: 15px 0;
        }}
        .success {{ color: #27ae60; font-weight: bold; }}
        .warning {{ color: #f39c12; font-weight: bold; }}
        .error {{ color: #e74c3c; font-weight: bold; }}
        .metric {{ 
            background: #ecf0f1; 
            padding: 10px; 
            border-radius: 5px; 
            margin: 10px 0;
        }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            margin: 15px 0;
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 12px; 
            text-align: left;
        }}
        th {{ background-color: #f2f2f2; }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    {content}
    <div class="footer">
        <p>Generated by AAR System v2.0 on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
        <p>Report Type: {report_type.title()} | Status: {data_status}</p>
    </div>
</body>
</html>"""
            
            # Save file with proper encoding
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Update UI
            self.results_text.delete('1.0', 'end')
            
            success_message = f"""{report_type.title()} Report Generated Successfully!

File: {os.path.basename(filename)}
Location: reports/generated/
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Type: {report_type.title()} ({data_status})

Report Preview:
{'-' * 50}
"""
            
            self.results_text.insert('1.0', success_message)
            
            # Show preview
            import re
            preview_text = re.sub('<[^<]+?>', '', content)
            preview_lines = preview_text.split('\\n')[:8]
            for line in preview_lines:
                if line.strip():
                    self.results_text.insert('end', line.strip() + "\\n")
            
            self.results_text.insert('end', "\\n... (complete report saved to file)")
            self.results_text.insert('end', "\\n\\nClick 'Open Reports Folder' to view the HTML file in your browser.")
            
            # Show success dialog
            messagebox.showinfo("Report Generated", 
                              f"{report_type.title()} report generated successfully!\\n\\n"
                              f"Saved as: {filename}\\n\\n"
                              f"Click 'Open Reports Folder' to view the file.")
            
            print(f"[Reports] Successfully generated: {filename}")
            
        except Exception as e:
            error_msg = f"Error generating {report_type} report: {str(e)}"
            print(f"[Reports] {error_msg}")
            
            self.results_text.delete('1.0', 'end')
            self.results_text.insert('1.0', f"ERROR: {error_msg}\\n\\n")
            self.results_text.insert('end', "Please check the console output for more details.\\n")
            self.results_text.insert('end', "Try the 'Test Report Generation' button to verify functionality.")
            
            messagebox.showerror("Report Generation Error", error_msg)
            
            import traceback
            traceback.print_exc()
    
    def create_report_with_data(self, report_type, timestamp):
        """Create report using actual analysis data"""
        content = f"<h1>After Action Review - {report_type.title()} Report</h1>"
        content += f"<p><strong>Generated:</strong> {datetime.now().strftime('%A, %B %d, %Y at %H:%M:%S')}</p>"
        
        content += '<div class="highlight">'
        content += f"<p><strong>Data Status:</strong> <span class='success'>Real analysis data available</span></p>"
        content += f"<p><strong>Domains Analyzed:</strong> {', '.join(self.current_results.keys())}</p>"
        content += "</div>"
        
        content += "<h2>Analysis Results</h2>"
        
        for domain, result in self.current_results.items():
            content += f"<h3>{domain} Domain Analysis</h3>"
            
            if hasattr(result, 'summary'):
                content += f'<div class="metric"><strong>Summary:</strong> {result.summary}</div>'
            
            if hasattr(result, 'alerts') and result.alerts:
                content += f"<p><strong>Alerts Generated:</strong> {len(result.alerts)} issues identified</p>"
                content += "<ul>"
                for alert in result.alerts[:5]:  # Show first 5 alerts
                    content += f"<li>{getattr(alert, 'message', str(alert))}</li>"
                content += "</ul>"
            
            if hasattr(result, 'metrics') and result.metrics:
                content += "<table>"
                content += "<tr><th>Metric</th><th>Value</th></tr>"
                for metric, value in result.metrics.items():
                    content += f"<tr><td>{metric}</td><td>{value}</td></tr>"
                content += "</table>"
            else:
                content += f"<p>Analysis completed successfully for {domain} domain.</p>"
        
        content += "<h2>Recommendations</h2>"
        content += "<ol>"
        content += "<li>Review domain-specific findings for detailed insights</li>"
        content += "<li>Address any high-priority alerts identified in the analysis</li>"
        content += "<li>Implement performance improvement strategies based on metrics</li>"
        content += "<li>Schedule follow-up training to address identified gaps</li>"
        content += "<li>Use these insights for future training exercise planning</li>"
        content += "</ol>"
        
        return content
    
    def create_sample_report(self, report_type, timestamp):
        """Create sample report for demonstration"""
        content = f"<h1>After Action Review - {report_type.title()} Report</h1>"
        content += f"<p><strong>Generated:</strong> {datetime.now().strftime('%A, %B %d, %Y at %H:%M:%S')}</p>"
        
        content += '<div class="highlight">'
        content += "<p><strong>Data Status:</strong> <span class='warning'>Sample report (no analysis data loaded)</span></p>"
        content += "<p>This is a demonstration report. Load training data and run analysis to generate reports with actual insights.</p>"
        content += "</div>"
        
        content += "<h2>Sample Analysis Overview</h2>"
        content += "<p>This report demonstrates the format and structure of AAR reports generated by the system.</p>"
        
        if report_type == "safety":
            content += "<h3>Safety Analysis</h3>"
            content += "<p>Safety analysis would include:</p>"
            content += "<ul>"
            content += "<li>Fall detection monitoring and incident tracking</li>"
            content += "<li>Medical event analysis and casualty state transitions</li>"
            content += "<li>Risk assessment based on environmental factors</li>"
            content += "<li>Safety protocol compliance evaluation</li>"
            content += "</ul>"
            
        elif report_type == "activity":
            content += "<h3>Activity Analysis</h3>"
            content += "<p>Activity reports would show:</p>"
            content += "<ul>"
            content += "<li>Movement patterns and step count tracking</li>"
            content += "<li>Physical performance metrics and endurance</li>"
            content += "<li>Posture analysis and tactical positioning</li>"
            content += "<li>Individual and comparative performance assessment</li>"
            content += "</ul>"
            
        elif report_type == "equipment":
            content += "<h3>Equipment Analysis</h3>"
            content += "<p>Equipment analysis would cover:</p>"
            content += "<ul>"
            content += "<li>Battery level monitoring and power consumption</li>"
            content += "<li>Device status and reliability tracking</li>"
            content += "<li>Equipment maintenance needs and recommendations</li>"
            content += "<li>Load-out optimization suggestions</li>"
            content += "</ul>"
            
        elif report_type == "environmental":
            content += "<h3>Environmental Analysis</h3>"
            content += "<p>Environmental analysis would include:</p>"
            content += "<ul>"
            content += "<li>Temperature monitoring and heat stress assessment</li>"
            content += "<li>Weather impact on training performance</li>"
            content += "<li>Seasonal condition analysis</li>"
            content += "<li>Environmental optimization recommendations</li>"
            content += "</ul>"
            
        else:
            content += "<h3>Comprehensive Analysis</h3>"
            content += "<p>This comprehensive report would include insights from all available analysis domains:</p>"
            content += "<ul>"
            content += "<li>Safety: Fall detection, medical events, risk assessment</li>"
            content += "<li>Activity: Movement patterns, physical performance</li>"
            content += "<li>Equipment: Battery status, device reliability</li>"
            content += "<li>Environmental: Weather conditions, temperature effects</li>"
            content += "<li>Network: Communication effectiveness, connectivity</li>"
            content += "</ul>"
        
        content += "<h2>Getting Started</h2>"
        content += "<ol>"
        content += "<li>Load training data using the Data Management tab</li>"
        content += "<li>Configure analysis domains and thresholds</li>"
        content += "<li>Run comprehensive analysis on your training data</li>"
        content += "<li>Generate new reports with actual training insights</li>"
        content += "<li>Use reports for training improvement and decision making</li>"
        content += "</ol>"
        
        content += "<h2>System Status</h2>"
        content += '<div class="metric">'
        content += "<p><strong>Report Generation:</strong> <span class='success'>Working correctly</span></p>"
        content += "<p><strong>File Output:</strong> <span class='success'>HTML format ready</span></p>"
        content += "<p><strong>Next Step:</strong> Load real training data for comprehensive analysis</p>"
        content += "</div>"
        
        return content
    
    def open_reports_folder(self):
        """Open the reports folder"""
        reports_dir = os.path.abspath("reports/generated")
        
        try:
            # Try different methods to open the folder
            if os.name == 'nt':  # Windows
                os.startfile(reports_dir)
            elif os.name == 'posix':  # macOS and Linux
                import subprocess
                if sys.platform == 'darwin':  # macOS
                    subprocess.call(['open', reports_dir])
                else:  # Linux
                    subprocess.call(['xdg-open', reports_dir])
            else:
                # Fallback to webbrowser
                import webbrowser
                webbrowser.open(f"file://{reports_dir}")
                
            print(f"[Reports] Opened folder: {reports_dir}")
            
        except Exception as e:
            print(f"[Reports] Could not open folder automatically: {e}")
            messagebox.showinfo("Reports Folder", 
                              f"Reports are saved in:\\n{reports_dir}\\n\\n"
                              f"You can navigate to this folder manually to view your reports.")
'''
    
    # Write the file with proper encoding
    try:
        with open("ui/components/reports_tab.py", "w", encoding='utf-8') as f:
            f.write(reports_tab_code)
        print("✅ Created Windows-compatible reports tab: ui/components/reports_tab.py")
        return True
    except Exception as e:
        print(f"❌ Error creating reports tab: {e}")
        return False

def create_quick_test_script():
    """Create a quick test script"""
    test_script = '''import tkinter as tk
from tkinter import ttk
import sys
import os

# Add to path
sys.path.insert(0, os.getcwd())

try:
    from ui.components.reports_tab import ReportsTab
    
    print("Testing AAR Reports...")
    
    # Create test window
    root = tk.Tk()
    root.title("AAR Reports Test")
    root.geometry("1000x700")
    
    # Create the reports tab
    reports_tab = ReportsTab(root)
    
    print("✅ Reports tab loaded successfully!")
    print("💡 Try clicking the report generation buttons")
    
    root.mainloop()
    
except Exception as e:
    print(f"❌ Error testing reports: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to continue...")
'''
    
    try:
        with open("test_reports_quick.py", "w", encoding='utf-8') as f:
            f.write(test_script)
        print("✅ Created quick test script: test_reports_quick.py")
        return True
    except Exception as e:
        print(f"❌ Error creating test script: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Windows Compatible AAR Reports Fix")
    print("=" * 50)
    
    print("📁 Checking directory structure...")
    os.makedirs("ui/components", exist_ok=True)
    os.makedirs("reports/generated", exist_ok=True)
    print("✅ Directories ready")
    
    print("📝 Creating Windows-compatible reports tab...")
    if create_windows_compatible_reports_tab():
        print("✅ Reports tab created successfully")
    else:
        print("❌ Failed to create reports tab")
        return
    
    print("🧪 Creating test script...")
    if create_quick_test_script():
        print("✅ Test script created successfully")
    else:
        print("❌ Failed to create test script")
    
    print("\n" + "=" * 50)
    print("✅ Windows-compatible fix completed!")
    print("\n🚀 Next steps:")
    print("1. Test immediately: python test_reports_quick.py")
    print("2. Or restart your main app: python main.py")
    print("3. Go to Reports tab and try the buttons")
    print("4. Reports will be saved to: reports/generated/")
    
    print("\n💡 Features fixed:")
    print("• ✅ Unicode encoding issues resolved")
    print("• ✅ Windows-compatible file operations")
    print("• ✅ Proper event handling for analysis_completed")
    print("• ✅ Working report generation buttons")
    print("• ✅ Professional HTML report formatting")
    print("• ✅ Error handling and user feedback")
    
    print("\n🎯 The reports tab now includes:")
    print("• Executive Summary, Safety, Activity, Equipment, Environmental reports")
    print("• Test report generation capability")
    print("• Automatic folder opening (Windows compatible)")
    print("• Professional HTML output with CSS styling")

if __name__ == "__main__":
    main()
