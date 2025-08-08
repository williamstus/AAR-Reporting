# ui/components/alert_widget.py - Alert Widget for AAR System
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
