# test_csv_loading.py - Test the CSV loading functionality
import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from core.event_bus import EventBus
from core.models import AnalysisDomain
from ui.components.data_management_tab import DataManagementTab

class MockMainApp:
    """Mock main application for testing"""
    def __init__(self):
        self.current_data = None
        self.selected_domains = []
        self.selected_columns = []
        self.orchestrator = None
        self.config = None

def test_csv_loading():
    """Test the CSV loading functionality"""
    
    # Create main window
    root = tk.Tk()
    root.title("Test CSV Loading")
    root.geometry("1000x700")
    
    # Create event bus
    event_bus = EventBus()
    
    # Create mock main app
    mock_app = MockMainApp()
    
    # Create notebook
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Create data management tab
    try:
        data_tab = DataManagementTab(notebook, event_bus, mock_app)
        notebook.add(data_tab.frame, text="Data Management")
        
        # Add status label
        status_label = ttk.Label(root, text="✅ CSV Loading functionality ready to test!", 
                               font=("Arial", 10, "bold"), foreground="green")
        status_label.pack(pady=10)
        
        # Add instructions
        instructions = """
        📋 How to test CSV loading:
        
        1. Click 'Browse for CSV File' to select a CSV file
        2. Or click 'Load Sample Data' to create demonstration data
        3. Click 'Load Data' to load the selected file
        4. Preview the data in the table
        5. Select analysis domain and columns
        6. Click 'Start Analysis' to begin processing
        
        🔍 Features to test:
        - File browsing and selection
        - Data preview and information
        - Column selection and domain configuration
        - Data validation
        - Sample data generation
        - Export functionality
        """
        
        instructions_label = ttk.Label(root, text=instructions, 
                                     font=("Arial", 9), justify='left')
        instructions_label.pack(pady=10)
        
        print("✅ CSV Loading test interface created successfully!")
        print("🚀 You can now test the CSV loading functionality")
        
    except Exception as e:
        print(f"❌ Error creating data management tab: {e}")
        import traceback
        traceback.print_exc()
        
        # Show error in UI
        error_label = ttk.Label(root, text=f"❌ Error: {str(e)}", 
                               font=("Arial", 12, "bold"), foreground="red")
        error_label.pack(pady=20)
    
    # Run the application
    root.mainloop()

if __name__ == "__main__":
    print("🧪 Testing CSV Loading Functionality")
    print("=" * 50)
    test_csv_loading()
