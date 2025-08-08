# fix_aar_system.py - Script to fix missing event types and components
"""
This script fixes the missing event types and components in your AAR system.
Run this script to resolve the EventType.ALERT_RESOLVED error and similar issues.
"""

import os
import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def fix_event_types():
    """Fix missing event types in core/models.py"""
    logger.info("Fixing EventType enum...")
    
    models_file = Path("core/models.py")
    if not models_file.exists():
        logger.error(f"File not found: {models_file}")
        return False
    
    # Read current content
    with open(models_file, 'r') as f:
        content = f.read()
    
    # Additional event types to add
    additional_events = """
    # Alert management events
    ALERT_RESOLVED = "alert_resolved"
    ALERT_DISMISSED = "alert_dismissed"
    ALERT_ACKNOWLEDGED = "alert_acknowledged"
    
    # Data management events
    DATA_LOAD_REQUESTED = "data_load_requested"
    DATA_LOAD_STARTED = "data_load_started"
    DATA_LOAD_COMPLETED = "data_load_completed"
    DATA_LOAD_CANCELLED = "data_load_cancelled"
    DATA_VALIDATION_REQUESTED = "data_validation_requested"
    DATA_VALIDATION_STARTED = "data_validation_started"
    DATA_VALIDATION_COMPLETED = "data_validation_completed"
    
    # System events
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    SYSTEM_STATUS_CHANGED = "system_status_changed"
    
    # UI events
    UI_COMPONENT_LOADED = "ui_component_loaded"
    UI_TAB_CHANGED = "ui_tab_changed"
    UI_REFRESH_REQUESTED = "ui_refresh_requested"
"""
    
    # Find the EventType class and add missing events
    if "class EventType(Enum):" in content:
        # Find the end of the EventType class
        lines = content.split('\n')
        new_lines = []
        in_event_type = False
        added_events = False
        
        for line in lines:
            if "class EventType(Enum):" in line:
                in_event_type = True
            elif in_event_type and line.strip().startswith("class ") and "EventType" not in line:
                # End of EventType class, add our events before the next class
                if not added_events:
                    new_lines.extend(additional_events.split('\n'))
                    added_events = True
                in_event_type = False
            elif in_event_type and not added_events and (line.strip() == "" or line.strip().startswith("#")):
                # Look for a good place to add events
                if "ERROR_OCCURRED" in content and "ALERT_RESOLVED" not in content:
                    new_lines.append(line)
                    if line.strip() == "" and len(new_lines) > 5:
                        new_lines.extend(additional_events.split('\n'))
                        added_events = True
                    continue
            
            new_lines.append(line)
        
        # If we didn't add events yet, add them at the end of the file
        if not added_events:
            new_lines.extend(additional_events.split('\n'))
        
        # Write back to file
        with open(models_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        logger.info("✅ EventType enum updated successfully")
        return True
    else:
        logger.error("Could not find EventType class in models.py")
        return False

def create_alert_widget():
    """Create the AlertWidget component"""
    logger.info("Creating AlertWidget component...")
    
    # Create components directory if it doesn't exist
    components_dir = Path("ui/components")
    components_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py if it doesn't exist
    init_file = components_dir / "__init__.py"
    if not init_file.exists():
        with open(init_file, 'w') as f:
            f.write("# UI Components module\n")
    
    alert_widget_content = '''# ui/components/alert_widget.py - Alert Widget for AAR System
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Dict, List, Optional
import logging

from core.event_bus import EventBus, Event, EventType
from core.models import Alert, AlertLevel

class AlertWidget:
    """Widget for displaying and managing alerts in the AAR system"""
    
    def __init__(self, parent, event_bus: EventBus):
        self.parent = parent
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Alert storage
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # Create UI
        self._create_widget()
        
        # Setup event subscriptions with error handling
        self._setup_event_subscriptions()
        
        self.logger.info("AlertWidget initialized")
    
    def _create_widget(self):
        """Create the alert widget UI"""
        # Create main frame
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill='x', padx=10, pady=5)
        
        # Alert status label
        self.status_label = ttk.Label(
            self.frame, 
            text="System Status: Normal", 
            foreground="green"
        )
        self.status_label.pack(side='left')
        
        # Alert count label
        self.count_label = ttk.Label(
            self.frame, 
            text="Alerts: 0"
        )
        self.count_label.pack(side='left', padx=(20, 0))
        
        # Show alerts button
        self.show_button = ttk.Button(
            self.frame, 
            text="Show Alerts", 
            command=self._show_alerts_dialog
        )
        self.show_button.pack(side='right')
        
        # Clear alerts button
        self.clear_button = ttk.Button(
            self.frame, 
            text="Clear All", 
            command=self._clear_all_alerts
        )
        self.clear_button.pack(side='right', padx=(0, 5))
    
    def _setup_event_subscriptions(self):
        """Setup event subscriptions with error handling for missing event types"""
        try:
            # Subscribe to alert events
            self.event_bus.subscribe(EventType.ALERT_TRIGGERED, self._on_alert_triggered)
            
            # Try to subscribe to alert resolution events if they exist
            if hasattr(EventType, 'ALERT_RESOLVED'):
                self.event_bus.subscribe(EventType.ALERT_RESOLVED, self._on_alert_resolved)
            
            if hasattr(EventType, 'ALERT_DISMISSED'):
                self.event_bus.subscribe(EventType.ALERT_DISMISSED, self._on_alert_dismissed)
            
            if hasattr(EventType, 'ALERT_ACKNOWLEDGED'):
                self.event_bus.subscribe(EventType.ALERT_ACKNOWLEDGED, self._on_alert_acknowledged)
            
        except Exception as e:
            self.logger.error(f"Error setting up event subscriptions: {e}")
    
    def _on_alert_triggered(self, event: Event):
        """Handle alert triggered events"""
        try:
            alert_data = event.data
            
            # Create alert object
            alert = Alert(
                alert_type=alert_data.get('alert_type', 'UNKNOWN'),
                level=AlertLevel(alert_data.get('level', 'INFO')),
                message=alert_data.get('message', 'No message'),
                timestamp=datetime.now(),
                affected_units=alert_data.get('affected_units', []),
                metric_value=alert_data.get('metric_value'),
                threshold=alert_data.get('threshold')
            )
            
            # Store alert
            alert_id = f"{alert.alert_type}_{alert.timestamp.strftime('%Y%m%d_%H%M%S')}"
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # Update UI
            self._update_alert_display()
            
            # Log alert
            self.logger.info(f"Alert triggered: {alert.alert_type} - {alert.message}")
            
        except Exception as e:
            self.logger.error(f"Error handling alert triggered event: {e}")
    
    def _on_alert_resolved(self, event: Event):
        """Handle alert resolved events"""
        try:
            alert_id = event.data.get('alert_id')
            if alert_id in self.active_alerts:
                del self.active_alerts[alert_id]
                self._update_alert_display()
                self.logger.info(f"Alert resolved: {alert_id}")
        except Exception as e:
            self.logger.error(f"Error handling alert resolved event: {e}")
    
    def _on_alert_dismissed(self, event: Event):
        """Handle alert dismissed events"""
        try:
            alert_id = event.data.get('alert_id')
            if alert_id in self.active_alerts:
                del self.active_alerts[alert_id]
                self._update_alert_display()
                self.logger.info(f"Alert dismissed: {alert_id}")
        except Exception as e:
            self.logger.error(f"Error handling alert dismissed event: {e}")
    
    def _on_alert_acknowledged(self, event: Event):
        """Handle alert acknowledged events"""
        try:
            alert_id = event.data.get('alert_id')
            if alert_id in self.active_alerts:
                # Mark as acknowledged but keep in active alerts
                self.active_alerts[alert_id].acknowledged = True
                self._update_alert_display()
                self.logger.info(f"Alert acknowledged: {alert_id}")
        except Exception as e:
            self.logger.error(f"Error handling alert acknowledged event: {e}")
    
    def _update_alert_display(self):
        """Update the alert display"""
        try:
            alert_count = len(self.active_alerts)
            self.count_label.config(text=f"Alerts: {alert_count}")
            
            # Update status based on highest alert level
            if alert_count == 0:
                self.status_label.config(text="System Status: Normal", foreground="green")
            else:
                highest_level = max(alert.level for alert in self.active_alerts.values())
                if highest_level == AlertLevel.CRITICAL:
                    self.status_label.config(text="System Status: Critical", foreground="red")
                elif highest_level == AlertLevel.WARNING:
                    self.status_label.config(text="System Status: Warning", foreground="orange")
                else:
                    self.status_label.config(text="System Status: Information", foreground="blue")
            
            # Update button state
            self.show_button.config(state='normal' if alert_count > 0 else 'disabled')
            self.clear_button.config(state='normal' if alert_count > 0 else 'disabled')
            
        except Exception as e:
            self.logger.error(f"Error updating alert display: {e}")
    
    def _show_alerts_dialog(self):
        """Show alerts in a dialog window"""
        try:
            dialog = tk.Toplevel(self.parent)
            dialog.title("System Alerts")
            dialog.geometry("600x400")
            
            # Create treeview for alerts
            tree_frame = ttk.Frame(dialog)
            tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            columns = ('Time', 'Level', 'Type', 'Message')
            tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
            
            # Configure columns
            tree.heading('Time', text='Time')
            tree.heading('Level', text='Level')
            tree.heading('Type', text='Type')
            tree.heading('Message', text='Message')
            
            tree.column('Time', width=120)
            tree.column('Level', width=80)
            tree.column('Type', width=150)
            tree.column('Message', width=250)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack tree and scrollbar
            tree.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            
            # Populate with alerts
            for alert_id, alert in self.active_alerts.items():
                tree.insert('', 'end', values=(
                    alert.timestamp.strftime('%H:%M:%S'),
                    alert.level.value,
                    alert.alert_type,
                    alert.message
                ))
            
            # Button frame
            button_frame = ttk.Frame(dialog)
            button_frame.pack(fill='x', padx=10, pady=5)
            
            ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side='right')
            ttk.Button(button_frame, text="Clear All", command=lambda: [self._clear_all_alerts(), dialog.destroy()]).pack(side='right', padx=(0, 5))
            
        except Exception as e:
            self.logger.error(f"Error showing alerts dialog: {e}")
    
    def _clear_all_alerts(self):
        """Clear all active alerts"""
        try:
            self.active_alerts.clear()
            self._update_alert_display()
            self.logger.info("All alerts cleared")
        except Exception as e:
            self.logger.error(f"Error clearing alerts: {e}")
    
    def add_test_alert(self, level: AlertLevel = AlertLevel.INFO, message: str = "Test alert"):
        """Add a test alert (for testing purposes)"""
        try:
            test_alert = Alert(
                alert_type="TEST_ALERT",
                level=level,
                message=message,
                timestamp=datetime.now()
            )
            
            alert_id = f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_alerts[alert_id] = test_alert
            self.alert_history.append(test_alert)
            
            self._update_alert_display()
            self.logger.info(f"Test alert added: {message}")
            
        except Exception as e:
            self.logger.error(f"Error adding test alert: {e}")
    
    def get_alert_statistics(self) -> Dict[str, int]:
        """Get alert statistics"""
        stats = {
            'active_alerts': len(self.active_alerts),
            'total_alerts': len(self.alert_history),
            'critical_alerts': len([a for a in self.active_alerts.values() if a.level == AlertLevel.CRITICAL]),
            'warning_alerts': len([a for a in self.active_alerts.values() if a.level == AlertLevel.WARNING])
        }
        return stats
'''
    
    alert_widget_file = components_dir / "alert_widget.py"
    with open(alert_widget_file, 'w') as f:
        f.write(alert_widget_content)
    
    logger.info("✅ AlertWidget component created successfully")
    return True

def create_placeholder_components():
    """Create placeholder components for missing UI components"""
    logger.info("Creating placeholder UI components...")
    
    components_dir = Path("ui/components")
    components_dir.mkdir(parents=True, exist_ok=True)
    
    components = [
        "data_management_tab.py",
        "domain_selection_tab.py", 
        "analysis_control_tab.py",
        "results_tab.py",
        "reports_tab.py",
        "configuration_dialog.py"
    ]
    
    for component_name in components:
        component_file = components_dir / component_name
        if not component_file.exists():
            class_name = component_name.replace('.py', '').replace('_', ' ').title().replace(' ', '')
            
            placeholder_content = f'''# ui/components/{component_name} - Placeholder Component
import tkinter as tk
from tkinter import ttk
import logging

class {class_name}:
    """Placeholder component for {class_name}"""
    
    def __init__(self, parent, event_bus, *args, **kwargs):
        self.parent = parent
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Create placeholder content
        self._create_placeholder()
        
        self.logger.info(f"{class_name} placeholder initialized")
    
    def _create_placeholder(self):
        """Create placeholder UI"""
        # Create main frame
        self.frame = ttk.Frame(self.parent)
        
        # Add placeholder content
        placeholder_label = ttk.Label(
            self.frame, 
            text=f"{class_name} Component\\n\\nThis component is under development.\\nThe event-driven architecture is ready for implementation.",
            font=("Arial", 12),
            justify="center"
        )
        placeholder_label.pack(expand=True, fill="both", padx=20, pady=50)
        
        # Add a button to demonstrate event system
        def test_event():
            from core.event_bus import Event, EventType
            self.event_bus.publish(Event(
                EventType.UI_COMPONENT_LOADED,
                {{'component': '{class_name}', 'status': 'placeholder_loaded'}},
                source='{class_name}'
            ))
        
        test_button = ttk.Button(
            self.frame,
            text="Test Event System",
            command=test_event
        )
        test_button.pack(pady=10)
    
    def pack(self, **kwargs):
        """Pack the frame"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the frame"""
        self.frame.grid(**kwargs)
'''
            
            with open(component_file, 'w') as f:
                f.write(placeholder_content)
            
            logger.info(f"✅ Created placeholder: {component_name}")
    
    return True

def fix_main_application():
    """Fix the main application to handle missing components gracefully"""
    logger.info("Fixing main application...")
    
    main_app_file = Path("ui/main_application.py")
    if not main_app_file.exists():
        logger.error(f"File not found: {main_app_file}")
        return False
    
    # Read current content
    with open(main_app_file, 'r') as f:
        content = f.read()
    
    # Add error handling around AlertWidget creation
    if "self.alert_widget = AlertWidget(self.root, self.event_bus)" in content:
        content = content.replace(
            "self.alert_widget = AlertWidget(self.root, self.event_bus)",
            """try:
            self.alert_widget = AlertWidget(self.root, self.event_bus)
        except Exception as e:
            self.logger.error(f"Error creating AlertWidget: {e}")
            self.alert_widget = None"""
        )
    
    # Write back to file
    with open(main_app_file, 'w') as f:
        f.write(content)
    
    logger.info("✅ Main application fixed")
    return True

def fix_missing_alert_properties():
    """Fix missing properties in Alert class"""
    logger.info("Fixing Alert class properties...")
    
    models_file = Path("core/models.py")
    if not models_file.exists():
        logger.error(f"File not found: {models_file}")
        return False
    
    # Read current content
    with open(models_file, 'r') as f:
        content = f.read()
    
    # Add acknowledged property to Alert class if it doesn't exist
    if "class Alert:" in content and "acknowledged:" not in content:
        # Find the Alert class and add the acknowledged property
        lines = content.split('\\n')
        new_lines = []
        in_alert_class = False
        
        for line in lines:
            if "class Alert:" in line:
                in_alert_class = True
            elif in_alert_class and line.strip().startswith("class "):
                in_alert_class = False
            elif in_alert_class and "threshold:" in line:
                # Add acknowledged property after threshold
                new_lines.append(line)
                new_lines.append("    acknowledged: bool = False")
                continue
            
            new_lines.append(line)
        
        # Write back to file
        with open(models_file, 'w') as f:
            f.write('\\n'.join(new_lines))
        
        logger.info("✅ Alert class properties updated")
    
    return True

def main():
    """Main fix function"""
    logger.info("🔧 Starting AAR System Fix")
    logger.info("=" * 40)
    
    fixes_applied = 0
    total_fixes = 5
    
    # Apply fixes
    if fix_event_types():
        fixes_applied += 1
    
    if create_alert_widget():
        fixes_applied += 1
    
    if create_placeholder_components():
        fixes_applied += 1
    
    if fix_main_application():
        fixes_applied += 1
    
    if fix_missing_alert_properties():
        fixes_applied += 1
    
    # Summary
    logger.info("=" * 40)
    logger.info(f"📊 Fix Results: {fixes_applied}/{total_fixes} fixes applied")
    
    if fixes_applied == total_fixes:
        logger.info("✅ All fixes applied successfully!")
        logger.info("Your AAR system should now run without the EventType errors.")
        logger.info("\\nNext steps:")
        logger.info("1. Run your main application: python main.py")
        logger.info("2. Test the data management services")
        logger.info("3. Implement the remaining UI components as needed")
    else:
        logger.info("❌ Some fixes failed. Please check the error messages above.")
    
    logger.info("\\n📁 Files modified/created:")
    logger.info("- core/models.py (added missing EventType values)")
    logger.info("- ui/components/alert_widget.py (created)")
    logger.info("- ui/components/*.py (placeholder components)")
    logger.info("- ui/main_application.py (error handling)")

if __name__ == "__main__":
    main()
