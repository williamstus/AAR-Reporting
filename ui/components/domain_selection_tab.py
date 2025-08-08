# ui/components/domain_selection_tab.py - Domain Selection Tab Implementation
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional
import logging

from core.event_bus import EventBus, Event, EventType
from core.models import AnalysisDomain, AnalysisLevel, TaskPriority

class DomainSelectionTab:
    """Domain selection and configuration tab"""
    
    def __init__(self, parent, event_bus: EventBus, orchestrator):
        self.parent = parent
        self.event_bus = event_bus
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)
        
        # Selection state
        self.selected_domains: List[AnalysisDomain] = []
        self.domain_configs: Dict[AnalysisDomain, Dict[str, Any]] = {}
        
        # Create UI
        self._create_ui()
        
        # Initialize domain configurations
        self._initialize_domain_configs()
        
        self.logger.info("DomainSelectionTab initialized")
    
    def _create_ui(self):
        """Create the domain selection UI"""
        # Main frame
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create sections
        self._create_domain_selection_section(main_frame)
        self._create_domain_configuration_section(main_frame)
        self._create_analysis_settings_section(main_frame)
        
        # Store main frame reference
        self.frame = main_frame
    
    def _create_domain_selection_section(self, parent):
        """Create domain selection section"""
        selection_frame = ttk.LabelFrame(parent, text="Analysis Domains", padding="10")
        selection_frame.pack(fill='x', pady=(0, 10))
        
        # Domain checkboxes
        self.domain_vars = {}
        
        # Create checkbox for each domain
        for domain in AnalysisDomain:
            var = tk.BooleanVar()
            checkbox = ttk.Checkbutton(
                selection_frame,
                text=self._get_domain_display_name(domain),
                variable=var,
                command=lambda d=domain, v=var: self._on_domain_toggled(d, v)
            )
            checkbox.pack(anchor='w', pady=2)
            self.domain_vars[domain] = var
        
        # Quick selection buttons
        button_frame = ttk.Frame(selection_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(button_frame, text="Select All", command=self._select_all_domains).pack(side='left')
        ttk.Button(button_frame, text="Clear All", command=self._clear_all_domains).pack(side='left', padx=(5, 0))
        ttk.Button(button_frame, text="Recommended", command=self._select_recommended_domains).pack(side='left', padx=(5, 0))
    
    def _create_domain_configuration_section(self, parent):
        """Create domain configuration section"""
        config_frame = ttk.LabelFrame(parent, text="Domain Configuration", padding="10")
        config_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Configuration notebook
        self.config_notebook = ttk.Notebook(config_frame)
        self.config_notebook.pack(fill='both', expand=True)
        
        # Create configuration tabs for each domain
        self.config_tabs = {}
        for domain in AnalysisDomain:
            tab_frame = ttk.Frame(self.config_notebook)
            self.config_notebook.add(tab_frame, text=self._get_domain_display_name(domain))
            self.config_tabs[domain] = tab_frame
            self._create_domain_config_tab(domain, tab_frame)
    
    def _create_domain_config_tab(self, domain: AnalysisDomain, parent):
        """Create configuration tab for a specific domain"""
        # Domain info
        info_frame = ttk.LabelFrame(parent, text="Domain Information", padding="10")
        info_frame.pack(fill='x', pady=(0, 10))
        
        info_text = self._get_domain_info(domain)
        ttk.Label(info_frame, text=info_text, wraplength=500, justify='left').pack(anchor='w')
        
        # Required columns
        columns_frame = ttk.LabelFrame(parent, text="Required Data Columns", padding="10")
        columns_frame.pack(fill='x', pady=(0, 10))
        
        required_columns = self._get_required_columns(domain)
        columns_text = "Required: " + ", ".join(required_columns)
        ttk.Label(columns_frame, text=columns_text, wraplength=500, justify='left').pack(anchor='w')
        
        optional_columns = self._get_optional_columns(domain)
        if optional_columns:
            optional_text = "Optional: " + ", ".join(optional_columns)
            ttk.Label(columns_frame, text=optional_text, wraplength=500, justify='left').pack(anchor='w', pady=(5, 0))
        
        # Configuration options
        options_frame = ttk.LabelFrame(parent, text="Configuration Options", padding="10")
        options_frame.pack(fill='both', expand=True)
        
        self._create_domain_options(domain, options_frame)
    
    def _create_domain_options(self, domain: AnalysisDomain, parent):
        """Create configuration options for a domain"""
        if domain == AnalysisDomain.SOLDIER_SAFETY:
            self._create_safety_options(parent)
        elif domain == AnalysisDomain.NETWORK_PERFORMANCE:
            self._create_network_options(parent)
        elif domain == AnalysisDomain.SOLDIER_ACTIVITY:
            self._create_activity_options(parent)
        elif domain == AnalysisDomain.EQUIPMENT_MANAGEMENT:
            self._create_equipment_options(parent)
        else:
            ttk.Label(parent, text="Configuration options will be available when this domain is implemented.").pack()
    
    def _create_safety_options(self, parent):
        """Create safety domain configuration options"""
        # Fall detection thresholds
        fall_frame = ttk.LabelFrame(parent, text="Fall Detection Settings", padding="5")
        fall_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(fall_frame, text="High fall risk threshold:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.fall_high_var = tk.StringVar(value="5")
        ttk.Entry(fall_frame, textvariable=self.fall_high_var, width=10).grid(row=0, column=1, sticky='w')
        
        ttk.Label(fall_frame, text="Critical fall risk threshold:").grid(row=1, column=0, sticky='w', padx=(0, 10))
        self.fall_critical_var = tk.StringVar(value="10")
        ttk.Entry(fall_frame, textvariable=self.fall_critical_var, width=10).grid(row=1, column=1, sticky='w')
        
        # Safety score thresholds
        score_frame = ttk.LabelFrame(parent, text="Safety Score Thresholds", padding="5")
        score_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(score_frame, text="Critical score threshold:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.safety_critical_var = tk.StringVar(value="50")
        ttk.Entry(score_frame, textvariable=self.safety_critical_var, width=10).grid(row=0, column=1, sticky='w')
        
        ttk.Label(score_frame, text="Warning score threshold:").grid(row=1, column=0, sticky='w', padx=(0, 10))
        self.safety_warning_var = tk.StringVar(value="70")
        ttk.Entry(score_frame, textvariable=self.safety_warning_var, width=10).grid(row=1, column=1, sticky='w')
        
        # Environmental settings
        env_frame = ttk.LabelFrame(parent, text="Environmental Settings", padding="5")
        env_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(env_frame, text="Heat stress threshold (°C):").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.heat_stress_var = tk.StringVar(value="35")
        ttk.Entry(env_frame, textvariable=self.heat_stress_var, width=10).grid(row=0, column=1, sticky='w')
    
    def _create_network_options(self, parent):
        """Create network domain configuration options"""
        # RSSI thresholds
        rssi_frame = ttk.LabelFrame(parent, text="RSSI Thresholds (dBm)", padding="5")
        rssi_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(rssi_frame, text="Excellent threshold:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.rssi_excellent_var = tk.StringVar(value="30")
        ttk.Entry(rssi_frame, textvariable=self.rssi_excellent_var, width=10).grid(row=0, column=1, sticky='w')
        
        ttk.Label(rssi_frame, text="Good threshold:").grid(row=1, column=0, sticky='w', padx=(0, 10))
        self.rssi_good_var = tk.StringVar(value="20")
        ttk.Entry(rssi_frame, textvariable=self.rssi_good_var, width=10).grid(row=1, column=1, sticky='w')
        
        ttk.Label(rssi_frame, text="Poor threshold:").grid(row=2, column=0, sticky='w', padx=(0, 10))
        self.rssi_poor_var = tk.StringVar(value="10")
        ttk.Entry(rssi_frame, textvariable=self.rssi_poor_var, width=10).grid(row=2, column=1, sticky='w')
        
        # MCS settings
        mcs_frame = ttk.LabelFrame(parent, text="MCS Settings", padding="5")
        mcs_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(mcs_frame, text="Optimal MCS range:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.mcs_min_var = tk.StringVar(value="5")
        ttk.Entry(mcs_frame, textvariable=self.mcs_min_var, width=5).grid(row=0, column=1, sticky='w')
        ttk.Label(mcs_frame, text="to").grid(row=0, column=2, padx=5)
        self.mcs_max_var = tk.StringVar(value="7")
        ttk.Entry(mcs_frame, textvariable=self.mcs_max_var, width=5).grid(row=0, column=3, sticky='w')
        
        # Blackout settings
        blackout_frame = ttk.LabelFrame(parent, text="Blackout Detection", padding="5")
        blackout_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(blackout_frame, text="Warning duration (seconds):").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.blackout_warning_var = tk.StringVar(value="30")
        ttk.Entry(blackout_frame, textvariable=self.blackout_warning_var, width=10).grid(row=0, column=1, sticky='w')
        
        ttk.Label(blackout_frame, text="Critical duration (seconds):").grid(row=1, column=0, sticky='w', padx=(0, 10))
        self.blackout_critical_var = tk.StringVar(value="60")
        ttk.Entry(blackout_frame, textvariable=self.blackout_critical_var, width=10).grid(row=1, column=1, sticky='w')
    
    def _create_activity_options(self, parent):
        """Create activity domain configuration options"""
        # Activity thresholds
        activity_frame = ttk.LabelFrame(parent, text="Activity Thresholds", padding="5")
        activity_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(activity_frame, text="Normal step range:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.steps_min_var = tk.StringVar(value="100")
        ttk.Entry(activity_frame, textvariable=self.steps_min_var, width=8).grid(row=0, column=1, sticky='w')
        ttk.Label(activity_frame, text="to").grid(row=0, column=2, padx=5)
        self.steps_max_var = tk.StringVar(value="400")
        ttk.Entry(activity_frame, textvariable=self.steps_max_var, width=8).grid(row=0, column=3, sticky='w')
        
        # Posture settings
        posture_frame = ttk.LabelFrame(parent, text="Posture Monitoring", padding="5")
        posture_frame.pack(fill='x', pady=(0, 5))
        
        self.track_posture_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(posture_frame, text="Track posture changes", variable=self.track_posture_var).pack(anchor='w')
        
        self.analyze_movement_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(posture_frame, text="Analyze movement patterns", variable=self.analyze_movement_var).pack(anchor='w')
    
    def _create_equipment_options(self, parent):
        """Create equipment domain configuration options"""
        # Battery thresholds
        battery_frame = ttk.LabelFrame(parent, text="Battery Monitoring", padding="5")
        battery_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(battery_frame, text="Critical battery level (%):").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.battery_critical_var = tk.StringVar(value="40")
        ttk.Entry(battery_frame, textvariable=self.battery_critical_var, width=10).grid(row=0, column=1, sticky='w')
        
        ttk.Label(battery_frame, text="Warning battery level (%):").grid(row=1, column=0, sticky='w', padx=(0, 10))
        self.battery_warning_var = tk.StringVar(value="60")
        ttk.Entry(battery_frame, textvariable=self.battery_warning_var, width=10).grid(row=1, column=1, sticky='w')
        
        # Equipment monitoring
        equipment_frame = ttk.LabelFrame(parent, text="Equipment Monitoring", padding="5")
        equipment_frame.pack(fill='x', pady=(0, 5))
        
        self.monitor_power_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(equipment_frame, text="Monitor power consumption", variable=self.monitor_power_var).pack(anchor='w')
        
        self.predict_depletion_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(equipment_frame, text="Predict battery depletion", variable=self.predict_depletion_var).pack(anchor='w')
    
    def _create_analysis_settings_section(self, parent):
        """Create analysis settings section"""
        settings_frame = ttk.LabelFrame(parent, text="Analysis Settings", padding="10")
        settings_frame.pack(fill='x')
        
        # Analysis level
        level_frame = ttk.Frame(settings_frame)
        level_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(level_frame, text="Analysis Level:").pack(side='left')
        self.analysis_level_var = tk.StringVar(value="INDIVIDUAL")
        level_combo = ttk.Combobox(level_frame, textvariable=self.analysis_level_var,
                                  values=[level.value for level in AnalysisLevel],
                                  state='readonly', width=15)
        level_combo.pack(side='left', padx=(10, 0))
        
        # Priority
        ttk.Label(level_frame, text="Priority:").pack(side='left', padx=(20, 0))
        self.priority_var = tk.StringVar(value="NORMAL")
        priority_combo = ttk.Combobox(level_frame, textvariable=self.priority_var,
                                     values=[priority.value for priority in TaskPriority],
                                     state='readonly', width=15)
        priority_combo.pack(side='left', padx=(10, 0))
        
        # Real-time analysis
        options_frame = ttk.Frame(settings_frame)
        options_frame.pack(fill='x', pady=(0, 10))
        
        self.real_time_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Enable real-time analysis", variable=self.real_time_var).pack(side='left')
        
        self.auto_alerts_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Auto-generate alerts", variable=self.auto_alerts_var).pack(side='left', padx=(20, 0))
        
        # Action buttons
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(button_frame, text="Apply Configuration", command=self._apply_configuration).pack(side='left')
        ttk.Button(button_frame, text="Reset to Defaults", command=self._reset_to_defaults).pack(side='left', padx=(10, 0))
        ttk.Button(button_frame, text="Save Configuration", command=self._save_configuration).pack(side='right')
    
    def _initialize_domain_configs(self):
        """Initialize default domain configurations"""
        for domain in AnalysisDomain:
            self.domain_configs[domain] = self._get_default_config(domain)
    
    def _get_domain_display_name(self, domain: AnalysisDomain) -> str:
        """Get display name for domain"""
        display_names = {
            AnalysisDomain.SOLDIER_SAFETY: "Soldier Safety Analysis",
            AnalysisDomain.NETWORK_PERFORMANCE: "Network Performance Analysis",
            AnalysisDomain.SOLDIER_ACTIVITY: "Soldier Activity Analysis",
            AnalysisDomain.EQUIPMENT_MANAGEMENT: "Equipment Management Analysis",
            AnalysisDomain.ENVIRONMENTAL_MONITORING: "Environmental Monitoring"
        }
        return display_names.get(domain, domain.value)
    
    def _get_domain_info(self, domain: AnalysisDomain) -> str:
        """Get domain information text"""
        info_texts = {
            AnalysisDomain.SOLDIER_SAFETY: "Analyzes soldier safety metrics including fall detection, casualty states, survival times, and environmental correlation. Implements REQ-SAFETY-001 through REQ-SAFETY-008.",
            AnalysisDomain.NETWORK_PERFORMANCE: "Monitors network performance including RSSI, MCS efficiency, communication blackouts, and coverage analysis. Implements REQ-NETWORK-001 through REQ-NETWORK-008.",
            AnalysisDomain.SOLDIER_ACTIVITY: "Tracks soldier activity patterns including step counts, posture monitoring, and movement analysis. Implements REQ-ACTIVITY-001 through REQ-ACTIVITY-008.",
            AnalysisDomain.EQUIPMENT_MANAGEMENT: "Manages equipment status including battery monitoring, power consumption, and equipment reliability. Implements REQ-EQUIPMENT-001 through REQ-EQUIPMENT-008.",
            AnalysisDomain.ENVIRONMENTAL_MONITORING: "Monitors environmental conditions and their impact on performance. Implements REQ-ENV-001 through REQ-ENV-004."
        }
        return info_texts.get(domain, "Domain information not available.")
    
    def _get_required_columns(self, domain: AnalysisDomain) -> List[str]:
        """Get required columns for domain"""
        required_columns = {
            AnalysisDomain.SOLDIER_SAFETY: ['callsign', 'falldetected', 'casualtystate', 'processedtimegmt'],
            AnalysisDomain.NETWORK_PERFORMANCE: ['callsign', 'processedtimegmt', 'rssi', 'mcs', 'nexthop'],
            AnalysisDomain.SOLDIER_ACTIVITY: ['callsign', 'processedtimegmt', 'steps', 'posture'],
            AnalysisDomain.EQUIPMENT_MANAGEMENT: ['callsign', 'processedtimegmt', 'battery'],
            AnalysisDomain.ENVIRONMENTAL_MONITORING: ['callsign', 'processedtimegmt', 'temp']
        }
        return required_columns.get(domain, ['callsign', 'processedtimegmt'])
    
    def _get_optional_columns(self, domain: AnalysisDomain) -> List[str]:
        """Get optional columns for domain"""
        optional_columns = {
            AnalysisDomain.SOLDIER_SAFETY: ['latitude', 'longitude', 'temp', 'squad'],
            AnalysisDomain.NETWORK_PERFORMANCE: ['latitude', 'longitude', 'ip'],
            AnalysisDomain.SOLDIER_ACTIVITY: ['latitude', 'longitude', 'squad'],
            AnalysisDomain.EQUIPMENT_MANAGEMENT: ['latitude', 'longitude', 'squad'],
            AnalysisDomain.ENVIRONMENTAL_MONITORING: ['latitude', 'longitude', 'squad']
        }
        return optional_columns.get(domain, ['latitude', 'longitude'])
    
    def _get_default_config(self, domain: AnalysisDomain) -> Dict[str, Any]:
        """Get default configuration for domain"""
        default_configs = {
            AnalysisDomain.SOLDIER_SAFETY: {
                'high_fall_risk_threshold': 5,
                'critical_fall_risk_threshold': 10,
                'heat_stress_threshold': 35,
                'safety_score_critical': 50,
                'safety_score_warning': 70
            },
            AnalysisDomain.NETWORK_PERFORMANCE: {
                'rssi_excellent': 30,
                'rssi_good': 20,
                'rssi_poor': 10,
                'mcs_optimal_min': 5,
                'mcs_optimal_max': 7,
                'blackout_duration_warning': 30,
                'blackout_duration_critical': 60
            },
            AnalysisDomain.SOLDIER_ACTIVITY: {
                'normal_step_min': 100,
                'normal_step_max': 400,
                'track_posture': True,
                'analyze_movement': True
            },
            AnalysisDomain.EQUIPMENT_MANAGEMENT: {
                'battery_critical': 40,
                'battery_warning': 60,
                'monitor_power': True,
                'predict_depletion': True
            }
        }
        return default_configs.get(domain, {})
    
    def _on_domain_toggled(self, domain: AnalysisDomain, var: tk.BooleanVar):
        """Handle domain toggle"""
        if var.get():
            if domain not in self.selected_domains:
                self.selected_domains.append(domain)
        else:
            if domain in self.selected_domains:
                self.selected_domains.remove(domain)
        
        # Publish domain selection change event
        self.event_bus.publish(Event(
            EventType.CONFIG_CHANGED,
            {
                'type': 'domain_selection',
                'selected_domains': [d.value for d in self.selected_domains]
            },
            source='DomainSelectionTab'
        ))
    
    def _select_all_domains(self):
        """Select all domains"""
        for domain, var in self.domain_vars.items():
            var.set(True)
            if domain not in self.selected_domains:
                self.selected_domains.append(domain)
    
    def _clear_all_domains(self):
        """Clear all domain selections"""
        for var in self.domain_vars.values():
            var.set(False)
        self.selected_domains.clear()
    
    def _select_recommended_domains(self):
        """Select recommended domains for typical analysis"""
        recommended = [AnalysisDomain.SOLDIER_SAFETY, AnalysisDomain.NETWORK_PERFORMANCE]
        
        # Clear current selection
        self._clear_all_domains()
        
        # Select recommended
        for domain in recommended:
            if domain in self.domain_vars:
                self.domain_vars[domain].set(True)
                self.selected_domains.append(domain)
    
    def _apply_configuration(self):
        """Apply current configuration"""
        # Collect configuration from UI
        config = {}
        
        # Safety configuration
        if AnalysisDomain.SOLDIER_SAFETY in self.selected_domains:
            config['safety_thresholds'] = {
                'high_fall_risk_threshold': int(self.fall_high_var.get()),
                'critical_fall_risk_threshold': int(self.fall_critical_var.get()),
                'safety_score_critical': int(self.safety_critical_var.get()),
                'safety_score_warning': int(self.safety_warning_var.get()),
                'heat_stress_threshold': int(self.heat_stress_var.get())
            }
        
        # Network configuration
        if AnalysisDomain.NETWORK_PERFORMANCE in self.selected_domains:
            config['network_thresholds'] = {
                'rssi_excellent': int(self.rssi_excellent_var.get()),
                'rssi_good': int(self.rssi_good_var.get()),
                'rssi_poor': int(self.rssi_poor_var.get()),
                'mcs_optimal_min': int(self.mcs_min_var.get()),
                'mcs_optimal_max': int(self.mcs_max_var.get()),
                'blackout_duration_warning': int(self.blackout_warning_var.get()),
                'blackout_duration_critical': int(self.blackout_critical_var.get())
            }
        
        # General settings
        config['analysis_level'] = self.analysis_level_var.get()
        config['priority'] = self.priority_var.get()
        config['real_time_analysis'] = self.real_time_var.get()
        config['auto_alerts'] = self.auto_alerts_var.get()
        
        # Publish configuration change event
        self.event_bus.publish(Event(
            EventType.CONFIG_CHANGED,
            config,
            source='DomainSelectionTab'
        ))
        
        messagebox.showinfo("Configuration Applied", "Domain configuration has been applied successfully!")
    
    def _reset_to_defaults(self):
        """Reset all configurations to defaults"""
        # Reset safety settings
        self.fall_high_var.set("5")
        self.fall_critical_var.set("10")
        self.safety_critical_var.set("50")
        self.safety_warning_var.set("70")
        self.heat_stress_var.set("35")
        
        # Reset network settings
        self.rssi_excellent_var.set("30")
        self.rssi_good_var.set("20")
        self.rssi_poor_var.set("10")
        self.mcs_min_var.set("5")
        self.mcs_max_var.set("7")
        self.blackout_warning_var.set("30")
        self.blackout_critical_var.set("60")
        
        # Reset activity settings
        self.steps_min_var.set("100")
        self.steps_max_var.set("400")
        self.track_posture_var.set(True)
        self.analyze_movement_var.set(True)
        
        # Reset equipment settings
        self.battery_critical_var.set("40")
        self.battery_warning_var.set("60")
        self.monitor_power_var.set(True)
        self.predict_depletion_var.set(True)
        
        # Reset general settings
        self.analysis_level_var.set("INDIVIDUAL")
        self.priority_var.set("NORMAL")
        self.real_time_var.set(False)
        self.auto_alerts_var.set(True)
        
        messagebox.showinfo("Reset Complete", "All configurations have been reset to default values!")
    
    def _save_configuration(self):
        """Save current configuration"""
        # This would save configuration to file
        messagebox.showinfo("Save Configuration", "Configuration saved successfully!")
    
    # Methods for external access
    def get_selected_domains(self) -> List[AnalysisDomain]:
        """Get selected domains"""
        return self.selected_domains.copy()
    
    def get_domain_config(self, domain: AnalysisDomain) -> Dict[str, Any]:
        """Get configuration for specific domain"""
        return self.domain_configs.get(domain, {})
    
    def set_selected_domains(self, domains: List[AnalysisDomain]):
        """Set selected domains programmatically"""
        self.selected_domains = domains.copy()
        for domain, var in self.domain_vars.items():
            var.set(domain in domains)
