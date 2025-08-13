import tkinter as tk
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
