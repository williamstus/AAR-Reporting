# ui/components/configuration_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from core.models import AnalysisDomain, SystemConfiguration, DEFAULT_THRESHOLDS


class ConfigurationDialog(tk.Toplevel):
    """
    Configuration Dialog - system-wide configuration management
    """
    
    def __init__(self, parent, current_config: SystemConfiguration = None):
        super().__init__(parent)
        self.parent = parent
        self.current_config = current_config or SystemConfiguration()
        self.result = None
        
        # Configuration state
        self.config_vars = {}
        self.threshold_vars = {}
        self.unsaved_changes = False
        
        # Setup window
        self._setup_window()
        
        # Create UI
        self._create_ui()
        
        # Load current configuration
        self._load_configuration()
    
    def _setup_window(self):
        """Setup window properties"""
        self.title("System Configuration")
        self.geometry("800x600")
        self.transient(self.parent)
        self.grab_set()
        
        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 400
        y = (self.winfo_screenheight() // 2) - 300
        self.geometry(f"800x600+{x}+{y}")
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Make resizable
        self.resizable(True, True)
    
    def _create_ui(self):
        """Create configuration UI"""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Create tabs
        self._create_general_tab()
        self._create_analysis_tab()
        self._create_thresholds_tab()
        self._create_ui_tab()
        self._create_advanced_tab()
        
        # Button frame
        button_frame = ttk.Frame(self)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        
        # Buttons
        ttk.Button(button_frame, text="Load Config", 
                  command=self._load_config_file).pack(side="left")
        ttk.Button(button_frame, text="Save Config", 
                  command=self._save_config_file).pack(side="left", padx=(5, 0))
        ttk.Button(button_frame, text="Reset to Defaults", 
                  command=self._reset_to_defaults).pack(side="left", padx=(5, 0))
        
        # Right side buttons
        ttk.Button(button_frame, text="Cancel", 
                  command=self._cancel).pack(side="right")
        ttk.Button(button_frame, text="Apply", 
                  command=self._apply).pack(side="right", padx=(0, 5))
        ttk.Button(button_frame, text="OK", 
                  command=self._ok).pack(side="right", padx=(0, 5))
        
        # Status label
        self.status_label = ttk.Label(button_frame, text="Ready")
        self.status_label.pack(side="left", padx=(20, 0))
    
    def _create_general_tab(self):
        """Create general configuration tab"""
        general_frame = ttk.Frame(self.notebook)
        self.notebook.add(general_frame, text="General")
        
        # System settings
        system_frame = ttk.LabelFrame(general_frame, text="System Settings", padding="10")
        system_frame.pack(fill="x", padx=10, pady=5)
        system_frame.grid_columnconfigure(1, weight=1)
        
        # Max concurrent tasks
        ttk.Label(system_frame, text="Max Concurrent Tasks:").grid(row=0, column=0, sticky="w", pady=2)
        self.max_tasks_var = tk.StringVar(value=str(self.current_config.max_concurrent_tasks))
        max_tasks_entry = ttk.Entry(system_frame, textvariable=self.max_tasks_var, width=10)
        max_tasks_entry.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=2)
        
        # Default timeout
        ttk.Label(system_frame, text="Default Timeout (seconds):").grid(row=1, column=0, sticky="w", pady=2)
        self.timeout_var = tk.StringVar(value=str(self.current_config.default_timeout))
        timeout_entry = ttk.Entry(system_frame, textvariable=self.timeout_var, width=10)
        timeout_entry.grid(row=1, column=1, sticky="w", padx=(5, 0), pady=2)
        
        # Output directory
        ttk.Label(system_frame, text="Output Directory:").grid(row=2, column=0, sticky="w", pady=2)
        self.output_dir_var = tk.StringVar(value=self.current_config.output_directory)
        output_dir_frame = ttk.Frame(system_frame)
        output_dir_frame.grid(row=2, column=1, sticky="ew", padx=(5, 0), pady=2)
        output_dir_frame.grid_columnconfigure(0, weight=1)
        
        output_dir_entry = ttk.Entry(output_dir_frame, textvariable=self.output_dir_var)
        output_dir_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(output_dir_frame, text="Browse", 
                  command=self._browse_output_dir).grid(row=0, column=1, padx=(5, 0))
        
        # Log level
        ttk.Label(system_frame, text="Log Level:").grid(row=3, column=0, sticky="w", pady=2)
        self.log_level_var = tk.StringVar(value=self.current_config.log_level)
        log_level_combo = ttk.Combobox(system_frame, textvariable=self.log_level_var,
                                     values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                     state="readonly", width=15)
        log_level_combo.grid(row=3, column=1, sticky="w", padx=(5, 0), pady=2)
        
        # Feature settings
        features_frame = ttk.LabelFrame(general_frame, text="Features", padding="10")
        features_frame.pack(fill="x", padx=10, pady=5)
        
        self.real_time_alerts_var = tk.BooleanVar(value=self.current_config.enable_real_time_alerts)
        ttk.Checkbutton(features_frame, text="Enable Real-time Alerts", 
                       variable=self.real_time_alerts_var).pack(anchor="w", pady=2)
        
        self.auto_generate_reports_var = tk.BooleanVar(value=self.current_config.auto_generate_reports)
        ttk.Checkbutton(features_frame, text="Auto-generate Reports", 
                       variable=self.auto_generate_reports_var).pack(anchor="w", pady=2)
        
        # Data retention
        retention_frame = ttk.Frame(features_frame)
        retention_frame.pack(fill="x", pady=5)
        
        ttk.Label(retention_frame, text="Data Retention (days):").pack(side="left")
        self.retention_var = tk.StringVar(value=str(self.current_config.data_retention_days))
        retention_entry = ttk.Entry(retention_frame, textvariable=self.retention_var, width=10)
        retention_entry.pack(side="left", padx=(5, 0))
        
        # Store config vars
        self.config_vars.update({
            'max_concurrent_tasks': self.max_tasks_var,
            'default_timeout': self.timeout_var,
            'output_directory': self.output_dir_var,
            'log_level': self.log_level_var,
            'enable_real_time_alerts': self.real_time_alerts_var,
            'auto_generate_reports': self.auto_generate_reports_var,
            'data_retention_days': self.retention_var
        })
        
        # Bind change events
        for var in self.config_vars.values():
            if isinstance(var, tk.StringVar):
                var.trace('w', self._on_config_changed)
            elif isinstance(var, tk.BooleanVar):
                var.trace('w', self._on_config_changed)
    
    def _create_analysis_tab(self):
        """Create analysis configuration tab"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Analysis")
        
        # Analysis engines
        engines_frame = ttk.LabelFrame(analysis_frame, text="Analysis Engines", padding="10")
        engines_frame.pack(fill="x", padx=10, pady=5)
        
        # Engine status
        ttk.Label(engines_frame, text="Available Engines:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        engines_info = [
            ("Soldier Safety", "✅ Implemented", "REQ-SAFETY-001 to REQ-SAFETY-008"),
            ("Network Performance", "✅ Implemented", "REQ-NETWORK-001 to REQ-NETWORK-008"),
            ("Soldier Activity", "🔲 Planned", "REQ-ACTIVITY-001 to REQ-ACTIVITY-008"),
            ("Equipment Management", "🔲 Planned", "REQ-EQUIPMENT-001 to REQ-EQUIPMENT-008"),
            ("Environmental Monitoring", "🔲 Planned", "REQ-ENV-001 to REQ-ENV-004")
        ]
        
        for name, status, requirements in engines_info:
            engine_frame = ttk.Frame(engines_frame)
            engine_frame.pack(fill="x", pady=2)
            
            ttk.Label(engine_frame, text=f"{name}:").pack(side="left", anchor="w")
            ttk.Label(engine_frame, text=status).pack(side="left", padx=(10, 0))
            ttk.Label(engine_frame, text=f"({requirements})", 
                     foreground="gray").pack(side="left", padx=(10, 0))
        
        # Analysis options
        options_frame = ttk.LabelFrame(analysis_frame, text="Analysis Options", padding="10")
        options_frame.pack(fill="x", padx=10, pady=5)
        
        # Default analysis level
        level_frame = ttk.Frame(options_frame)
        level_frame.pack(fill="x", pady=2)
        
        ttk.Label(level_frame, text="Default Analysis Level:").pack(side="left")
        self.default_level_var = tk.StringVar(value="INDIVIDUAL")
        level_combo = ttk.Combobox(level_frame, textvariable=self.default_level_var,
                                 values=["INDIVIDUAL", "SQUAD", "PLATOON", "COMPANY"],
                                 state="readonly", width=15)
        level_combo.pack(side="left", padx=(5, 0))
        
        # Parallel processing
        self.parallel_processing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Enable Parallel Processing", 
                       variable=self.parallel_processing_var).pack(anchor="w", pady=2)
        
        # Data validation
        self.strict_validation_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Strict Data Validation", 
                       variable=self.strict_validation_var).pack(anchor="w", pady=2)
        
        # Performance settings
        performance_frame = ttk.LabelFrame(analysis_frame, text="Performance", padding="10")
        performance_frame.pack(fill="x", padx=10, pady=5)
        
        # Memory limit
        memory_frame = ttk.Frame(performance_frame)
        memory_frame.pack(fill="x", pady=2)
        
        ttk.Label(memory_frame, text="Memory Limit (MB):").pack(side="left")
        self.memory_limit_var = tk.StringVar(value="1024")
        memory_entry = ttk.Entry(memory_frame, textvariable=self.memory_limit_var, width=10)
        memory_entry.pack(side="left", padx=(5, 0))
        
        # Cache settings
        self.enable_cache_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(performance_frame, text="Enable Result Caching", 
                       variable=self.enable_cache_var).pack(anchor="w", pady=2)
        
        # Add to config vars
        self.config_vars.update({
            'default_level': self.default_level_var,
            'parallel_processing': self.parallel_processing_var,
            'strict_validation': self.strict_validation_var,
            'memory_limit': self.memory_limit_var,
            'enable_cache': self.enable_cache_var
        })
    
    def _create_thresholds_tab(self):
        """Create thresholds configuration tab"""
        thresholds_frame = ttk.Frame(self.notebook)
        self.notebook.add(thresholds_frame, text="Thresholds")
        
        # Domain selection
        domain_frame = ttk.Frame(thresholds_frame)
        domain_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(domain_frame, text="Domain:").pack(side="left")
        self.threshold_domain_var = tk.StringVar(value="SOLDIER_SAFETY")
        domain_combo = ttk.Combobox(domain_frame, textvariable=self.threshold_domain_var,
                                  values=["SOLDIER_SAFETY", "NETWORK_PERFORMANCE"],
                                  state="readonly", width=20)
        domain_combo.pack(side="left", padx=(5, 0))
        domain_combo.bind('<<ComboboxSelected>>', self._on_domain_changed)
        
        ttk.Button(domain_frame, text="Reset Domain", 
                  command=self._reset_domain_thresholds).pack(side="left", padx=(10, 0))
        
        # Thresholds display
        self.thresholds_notebook = ttk.Notebook(thresholds_frame)
        self.thresholds_notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create threshold tabs
        self._create_safety_thresholds_tab()
        self._create_network_thresholds_tab()
    
    def _create_safety_thresholds_tab(self):
        """Create safety thresholds tab"""
        safety_frame = ttk.Frame(self.thresholds_notebook)
        self.thresholds_notebook.add(safety_frame, text="Safety Thresholds")
        
        # Create scrollable frame
        canvas = tk.Canvas(safety_frame)
        scrollbar = ttk.Scrollbar(safety_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Safety thresholds
        safety_thresholds = DEFAULT_THRESHOLDS.get(AnalysisDomain.SOLDIER_SAFETY, {})
        current_safety = self.current_config.get_domain_thresholds(AnalysisDomain.SOLDIER_SAFETY)
        
        self.safety_threshold_vars = {}
        
        # Create threshold controls
        threshold_configs = [
            ('high_fall_risk_threshold', 'High Fall Risk Threshold', 'falls per unit'),
            ('critical_fall_risk_threshold', 'Critical Fall Risk Threshold', 'falls per unit'),
            ('heat_stress_threshold', 'Heat Stress Threshold', '°C'),
            ('safety_score_critical', 'Safety Score Critical', 'score (0-100)'),
            ('safety_score_warning', 'Safety Score Warning', 'score (0-100)'),
            ('casualty_rate_warning', 'Casualty Rate Warning', 'ratio (0-1)'),
            ('casualty_rate_critical', 'Casualty Rate Critical', 'ratio (0-1)'),
            ('survival_time_minimum', 'Survival Time Minimum', 'seconds')
        ]
        
        for i, (key, label, unit) in enumerate(threshold_configs):
            threshold_frame = ttk.Frame(scrollable_frame)
            threshold_frame.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            threshold_frame.grid_columnconfigure(1, weight=1)
            
            ttk.Label(threshold_frame, text=f"{label}:").grid(row=0, column=0, sticky="w")
            
            current_value = current_safety.get(key, safety_thresholds.get(key, 0))
            var = tk.StringVar(value=str(current_value))
            entry = ttk.Entry(threshold_frame, textvariable=var, width=15)
            entry.grid(row=0, column=1, sticky="w", padx=(5, 0))
            
            ttk.Label(threshold_frame, text=unit).grid(row=0, column=2, sticky="w", padx=(5, 0))
            
            self.safety_threshold_vars[key] = var
            var.trace('w', self._on_config_changed)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add to threshold vars
        self.threshold_vars['SOLDIER_SAFETY'] = self.safety_threshold_vars
    
    def _create_network_thresholds_tab(self):
        """Create network thresholds tab"""
        network_frame = ttk.Frame(self.thresholds_notebook)
        self.thresholds_notebook.add(network_frame, text="Network Thresholds")
        
        # Create scrollable frame
        canvas = tk.Canvas(network_frame)
        scrollbar = ttk.Scrollbar(network_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Network thresholds
        network_thresholds = DEFAULT_THRESHOLDS.get(AnalysisDomain.NETWORK_PERFORMANCE, {})
        current_network = self.current_config.get_domain_thresholds(AnalysisDomain.NETWORK_PERFORMANCE)
        
        self.network_threshold_vars = {}
        
        # Create threshold controls
        threshold_configs = [
            ('rssi_excellent', 'RSSI Excellent', 'dBm'),
            ('rssi_good', 'RSSI Good', 'dBm'),
            ('rssi_poor', 'RSSI Poor', 'dBm'),
            ('rssi_critical', 'RSSI Critical', 'dBm'),
            ('mcs_optimal_min', 'MCS Optimal Min', 'index'),
            ('mcs_optimal_max', 'MCS Optimal Max', 'index'),
            ('mcs_minimum', 'MCS Minimum', 'index'),
            ('blackout_duration_warning', 'Blackout Duration Warning', 'seconds'),
            ('blackout_duration_critical', 'Blackout Duration Critical', 'seconds'),
            ('packet_loss_warning', 'Packet Loss Warning', 'ratio (0-1)'),
            ('packet_loss_critical', 'Packet Loss Critical', 'ratio (0-1)')
        ]
        
        for i, (key, label, unit) in enumerate(threshold_configs):
            threshold_frame = ttk.Frame(scrollable_frame)
            threshold_frame.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            threshold_frame.grid_columnconfigure(1, weight=1)
            
            ttk.Label(threshold_frame, text=f"{label}:").grid(row=0, column=0, sticky="w")
            
            current_value = current_network.get(key, network_thresholds.get(key, 0))
            var = tk.StringVar(value=str(current_value))
            entry = ttk.Entry(threshold_frame, textvariable=var, width=15)
            entry.grid(row=0, column=1, sticky="w", padx=(5, 0))
            
            ttk.Label(threshold_frame, text=unit).grid(row=0, column=2, sticky="w", padx=(5, 0))
            
            self.network_threshold_vars[key] = var
            var.trace('w', self._on_config_changed)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add to threshold vars
        self.threshold_vars['NETWORK_PERFORMANCE'] = self.network_threshold_vars
    
    def _create_ui_tab(self):
        """Create UI configuration tab"""
        ui_frame = ttk.Frame(self.notebook)
        self.notebook.add(ui_frame, text="User Interface")
        
        # Appearance settings
        appearance_frame = ttk.LabelFrame(ui_frame, text="Appearance", padding="10")
        appearance_frame.pack(fill="x", padx=10, pady=5)
        
        # Theme
        theme_frame = ttk.Frame(appearance_frame)
        theme_frame.pack(fill="x", pady=2)
        
        ttk.Label(theme_frame, text="Theme:").pack(side="left")
        self.theme_var = tk.StringVar(value="default")
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var,
                                 values=["default", "dark", "light"],
                                 state="readonly", width=15)
        theme_combo.pack(side="left", padx=(5, 0))
        
        # Font size
        font_frame = ttk.Frame(appearance_frame)
        font_frame.pack(fill="x", pady=2)
        
        ttk.Label(font_frame, text="Font Size:").pack(side="left")
        self.font_size_var = tk.StringVar(value="10")
        font_size_combo = ttk.Combobox(font_frame, textvariable=self.font_size_var,
                                     values=["8", "9", "10", "11", "12", "14", "16"],
                                     state="readonly", width=10)
        font_size_combo.pack(side="left", padx=(5, 0))
        
        # Behavior settings
        behavior_frame = ttk.LabelFrame(ui_frame, text="Behavior", padding="10")
        behavior_frame.pack(fill="x", padx=10, pady=5)
        
        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(behavior_frame, text="Auto-refresh displays", 
                       variable=self.auto_refresh_var).pack(anchor="w", pady=2)
        
        self.show_tooltips_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(behavior_frame, text="Show tooltips", 
                       variable=self.show_tooltips_var).pack(anchor="w", pady=2)
        
        self.confirm_actions_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(behavior_frame, text="Confirm destructive actions", 
                       variable=self.confirm_actions_var).pack(anchor="w", pady=2)
        
        # Default tab
        default_frame = ttk.Frame(behavior_frame)
        default_frame.pack(fill="x", pady=2)
        
        ttk.Label(default_frame, text="Default Tab:").pack(side="left")
        self.default_tab_var = tk.StringVar(value="Data Management")
        default_tab_combo = ttk.Combobox(default_frame, textvariable=self.default_tab_var,
                                       values=["Data Management", "Domain Selection", "Analysis Control", 
                                              "Results", "Reports"],
                                       state="readonly", width=20)
        default_tab_combo.pack(side="left", padx=(5, 0))
        
        # Alert settings
        alert_frame = ttk.LabelFrame(ui_frame, text="Alert Display", padding="10")
        alert_frame.pack(fill="x", padx=10, pady=5)
        
        self.alert_popup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(alert_frame, text="Show alert popup", 
                       variable=self.alert_popup_var).pack(anchor="w", pady=2)
        
        self.alert_sound_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(alert_frame, text="Play alert sounds", 
                       variable=self.alert_sound_var).pack(anchor="w", pady=2)
        
        self.alert_blink_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(alert_frame, text="Blink on critical alerts", 
                       variable=self.alert_blink_var).pack(anchor="w", pady=2)
        
        # Add to config vars
        self.config_vars.update({
            'theme': self.theme_var,
            'font_size': self.font_size_var,
            'auto_refresh': self.auto_refresh_var,
            'show_tooltips': self.show_tooltips_var,
            'confirm_actions': self.confirm_actions_var,
            'default_tab': self.default_tab_var,
            'alert_popup': self.alert_popup_var,
            'alert_sound': self.alert_sound_var,
            'alert_blink': self.alert_blink_var
        })
    
    def _create_advanced_tab(self):
        """Create advanced configuration tab"""
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="Advanced")
        
        # Debug settings
        debug_frame = ttk.LabelFrame(advanced_frame, text="Debug", padding="10")
        debug_frame.pack(fill="x", padx=10, pady=5)
        
        self.debug_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(debug_frame, text="Enable debug mode", 
                       variable=self.debug_mode_var).pack(anchor="w", pady=2)
        
        self.verbose_logging_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(debug_frame, text="Verbose logging", 
                       variable=self.verbose_logging_var).pack(anchor="w", pady=2)
        
        self.save_intermediate_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(debug_frame, text="Save intermediate results", 
                       variable=self.save_intermediate_var).pack(anchor="w", pady=2)
        
        # Performance monitoring
        monitor_frame = ttk.LabelFrame(advanced_frame, text="Performance Monitoring", padding="10")
        monitor_frame.pack(fill="x", padx=10, pady=5)
        
        self.profile_analysis_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(monitor_frame, text="Profile analysis performance", 
                       variable=self.profile_analysis_var).pack(anchor="w", pady=2)
        
        self.track_memory_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(monitor_frame, text="Track memory usage", 
                       variable=self.track_memory_var).pack(anchor="w", pady=2)
        
        # Export/Import
        export_frame = ttk.LabelFrame(advanced_frame, text="Configuration Management", padding="10")
        export_frame.pack(fill="x", padx=10, pady=5)
        
        export_controls = ttk.Frame(export_frame)
        export_controls.pack(fill="x", pady=5)
        
        ttk.Button(export_controls, text="Export Configuration", 
                  command=self._export_configuration).pack(side="left")
        ttk.Button(export_controls, text="Import Configuration", 
                  command=self._import_configuration).pack(side="left", padx=(5, 0))
        ttk.Button(export_controls, text="Validate Configuration", 
                  command=self._validate_configuration).pack(side="left", padx=(5, 0))
        
        # Configuration info
        info_frame = ttk.LabelFrame(advanced_frame, text="Configuration Information", padding="10")
        info_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.config_info_text = tk.Text(info_frame, height=8, wrap="word")
        info_scroll = ttk.Scrollbar(info_frame, orient="vertical", command=self.config_info_text.yview)
        self.config_info_text.configure(yscrollcommand=info_scroll.set)
        
        self.config_info_text.pack(side="left", fill="both", expand=True)
        info_scroll.pack(side="right", fill="y")
        
        # Add to config vars
        self.config_vars.update({
            'debug_mode': self.debug_mode_var,
            'verbose_logging': self.verbose_logging_var,
            'save_intermediate': self.save_intermediate_var,
            'profile_analysis': self.profile_analysis_var,
            'track_memory': self.track_memory_var
        })
        
        # Update config info
        self._update_config_info()
    
    def _load_configuration(self):
        """Load current configuration into UI"""
        # Configuration already loaded in _create_* methods
        self.unsaved_changes = False
        self._update_status("Configuration loaded")
    
    def _browse_output_dir(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_dir_var.get()
        )
        
        if directory:
            self.output_dir_var.set(directory)
    
    def _on_domain_changed(self, event=None):
        """Handle domain selection change"""
        domain = self.threshold_domain_var.get()
        
        if domain == "SOLDIER_SAFETY":
            self.thresholds_notebook.select(0)
        elif domain == "NETWORK_PERFORMANCE":
            self.thresholds_notebook.select(1)
    
    def _reset_domain_thresholds(self):
        """Reset domain thresholds to defaults"""
        domain = self.threshold_domain_var.get()
        
        if messagebox.askyesno("Reset Thresholds", f"Reset {domain} thresholds to defaults?"):
            try:
                domain_enum = AnalysisDomain(domain)
                default_thresholds = DEFAULT_THRESHOLDS.get(domain_enum, {})
                
                threshold_vars = self.threshold_vars.get(domain, {})
                
                for key, default_value in default_thresholds.items():
                    if key in threshold_vars:
                        threshold_vars[key].set(str(default_value))
                
                self._update_status(f"{domain} thresholds reset to defaults")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error resetting thresholds: {str(e)}")
    
    def _load_config_file(self):
        """Load configuration from file"""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    config_data = json.load(f)
                
                # Apply configuration
                self._apply_config_data(config_data)
                
                self._update_status(f"Configuration loaded from {filename}")
                messagebox.showinfo("Success", "Configuration loaded successfully")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading configuration: {str(e)}")
    
    def _save_config_file(self):
        """Save configuration to file"""
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                config_data = self._get_config_data()
                
                with open(filename, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                self._update_status(f"Configuration saved to {filename}")
                messagebox.showinfo("Success", "Configuration saved successfully")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error saving configuration: {str(e)}")
    
    def _reset_to_defaults(self):
        """Reset all configuration to defaults"""
        if messagebox.askyesno("Reset to Defaults", "Reset all configuration to defaults?"):
            try:
                # Reset to default configuration
                default_config = SystemConfiguration()
                self.current_config = default_config
                
                # Update UI
                self._update_ui_from_config()
                
                self._update_status("Configuration reset to defaults")
                messagebox.showinfo("Success", "Configuration reset to defaults")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error resetting configuration: {str(e)}")
    
    def _export_configuration(self):
        """Export configuration"""
        try:
            config_data = self._get_config_data()
            
            filename = filedialog.asksaveasfilename(
                title="Export Configuration",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                messagebox.showinfo("Success", f"Configuration exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error exporting configuration: {str(e)}")
    
    def _import_configuration(self):
        """Import configuration"""
        self._load_config_file()
    
    def _validate_configuration(self):
        """Validate current configuration"""
        try:
            config_data = self._get_config_data()
            errors = []
            
            # Validate basic settings
            if config_data.get('max_concurrent_tasks', 0) <= 0:
                errors.append("Max concurrent tasks must be positive")
            
            if config_data.get('default_timeout', 0) <= 0:
                errors.append("Default timeout must be positive")
            
            if not config_data.get('output_directory'):
                errors.append("Output directory is required")
            
            # Validate thresholds
            for domain, thresholds in config_data.get('thresholds', {}).items():
                for key, value in thresholds.items():
                    try:
                        float(value)
                    except ValueError:
                        errors.append(f"Invalid threshold value for {domain}.{key}: {value}")
            
            if errors:
                error_msg = "Configuration validation errors:\n\n" + "\n".join(errors)
                messagebox.showerror("Validation Errors", error_msg)
            else:
                messagebox.showinfo("Validation Success", "Configuration is valid")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error validating configuration: {str(e)}")
    
    def _update_config_info(self):
        """Update configuration information display"""
        try:
            config_data = self._get_config_data()
            
            info_text = f"Configuration Summary\n"
            info_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # System info
            info_text += f"System Settings:\n"
            info_text += f"  Max Tasks: {config_data.get('max_concurrent_tasks', 'N/A')}\n"
            info_text += f"  Timeout: {config_data.get('default_timeout', 'N/A')}s\n"
            info_text += f"  Output Dir: {config_data.get('output_directory', 'N/A')}\n"
            info_text += f"  Log Level: {config_data.get('log_level', 'N/A')}\n\n"
            
            # Features
            info_text += f"Features:\n"
            info_text += f"  Real-time Alerts: {config_data.get('enable_real_time_alerts', 'N/A')}\n"
            info_text += f"  Auto Reports: {config_data.get('auto_generate_reports', 'N/A')}\n"
            info_text += f"  Data Retention: {config_data.get('data_retention_days', 'N/A')} days\n\n"
            
            # Thresholds
            info_text += f"Thresholds:\n"
            for domain, thresholds in config_data.get('thresholds', {}).items():
                info_text += f"  {domain}: {len(thresholds)} thresholds configured\n"
            
            self.config_info_text.delete(1.0, tk.END)
            self.config_info_text.insert(tk.END, info_text)
            
        except Exception as e:
            self.config_info_text.delete(1.0, tk.END)
            self.config_info_text.insert(tk.END, f"Error updating config info: {str(e)}")
    
    def _get_config_data(self) -> Dict[str, Any]:
        """Get current configuration data"""
        config_data = {}
        
        # Basic configuration
        try:
            config_data['max_concurrent_tasks'] = int(self.max_tasks_var.get())
        except ValueError:
            config_data['max_concurrent_tasks'] = 5
        
        try:
            config_data['default_timeout'] = int(self.timeout_var.get())
        except ValueError:
            config_data['default_timeout'] = 300
        
        config_data['output_directory'] = self.output_dir_var.get()
        config_data['log_level'] = self.log_level_var.get()
        config_data['enable_real_time_alerts'] = self.real_time_alerts_var.get()
        config_data['auto_generate_reports'] = self.auto_generate_reports_var.get()
        
        try:
            config_data['data_retention_days'] = int(self.retention_var.get())
        except ValueError:
            config_data['data_retention_days'] = 30
        
        # Analysis settings
        config_data['default_level'] = self.default_level_var.get()
        config_data['parallel_processing'] = self.parallel_processing_var.get()
        config_data['strict_validation'] = self.strict_validation_var.get()
        
        try:
            config_data['memory_limit'] = int(self.memory_limit_var.get())
        except ValueError:
            config_data['memory_limit'] = 1024
        
        config_data['enable_cache'] = self.enable_cache_var.get()
        
        # UI settings
        config_data['theme'] = self.theme_var.get()
        config_data['font_size'] = self.font_size_var.get()
        config_data['auto_refresh'] = self.auto_refresh_var.get()
        config_data['show_tooltips'] = self.show_tooltips_var.get()
        config_data['confirm_actions'] = self.confirm_actions_var.get()
        config_data['default_tab'] = self.default_tab_var.get()
        config_data['alert_popup'] = self.alert_popup_var.get()
        config_data['alert_sound'] = self.alert_sound_var.get()
        config_data['alert_blink'] = self.alert_blink_var.get()
        
        # Advanced settings
        config_data['debug_mode'] = self.debug_mode_var.get()
        config_data['verbose_logging'] = self.verbose_logging_var.get()
        config_data['save_intermediate'] = self.save_intermediate_var.get()
        config_data['profile_analysis'] = self.profile_analysis_var.get()
        config_data['track_memory'] = self.track_memory_var.get()
        
        # Thresholds
        config_data['thresholds'] = {}
        
        for domain, threshold_vars in self.threshold_vars.items():
            config_data['thresholds'][domain] = {}
            for key, var in threshold_vars.items():
                try:
                    config_data['thresholds'][domain][key] = float(var.get())
                except ValueError:
                    config_data['thresholds'][domain][key] = 0.0
        
        return config_data
    
    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Apply configuration data to UI"""
        try:
            # Basic settings
            if 'max_concurrent_tasks' in config_data:
                self.max_tasks_var.set(str(config_data['max_concurrent_tasks']))
            
            if 'default_timeout' in config_data:
                self.timeout_var.set(str(config_data['default_timeout']))
            
            if 'output_directory' in config_data:
                self.output_dir_var.set(config_data['output_directory'])
            
            if 'log_level' in config_data:
                self.log_level_var.set(config_data['log_level'])
            
            if 'enable_real_time_alerts' in config_data:
                self.real_time_alerts_var.set(config_data['enable_real_time_alerts'])
            
            if 'auto_generate_reports' in config_data:
                self.auto_generate_reports_var.set(config_data['auto_generate_reports'])
            
            if 'data_retention_days' in config_data:
                self.retention_var.set(str(config_data['data_retention_days']))
            
            # Analysis settings
            if 'default_level' in config_data:
                self.default_level_var.set(config_data['default_level'])
            
            if 'parallel_processing' in config_data:
                self.parallel_processing_var.set(config_data['parallel_processing'])
            
            if 'strict_validation' in config_data:
                self.strict_validation_var.set(config_data['strict_validation'])
            
            if 'memory_limit' in config_data:
                self.memory_limit_var.set(str(config_data['memory_limit']))
            
            if 'enable_cache' in config_data:
                self.enable_cache_var.set(config_data['enable_cache'])
            
            # UI settings
            if 'theme' in config_data:
                self.theme_var.set(config_data['theme'])
            
            if 'font_size' in config_data:
                self.font_size_var.set(config_data['font_size'])
            
            if 'auto_refresh' in config_data:
                self.auto_refresh_var.set(config_data['auto_refresh'])
            
            if 'show_tooltips' in config_data:
                self.show_tooltips_var.set(config_data['show_tooltips'])
            
            if 'confirm_actions' in config_data:
                self.confirm_actions_var.set(config_data['confirm_actions'])
            
            if 'default_tab' in config_data:
                self.default_tab_var.set(config_data['default_tab'])
            
            if 'alert_popup' in config_data:
                self.alert_popup_var.set(config_data['alert_popup'])
            
            if 'alert_sound' in config_data:
                self.alert_sound_var.set(config_data['alert_sound'])
            
            if 'alert_blink' in config_data:
                self.alert_blink_var.set(config_data['alert_blink'])
            
            # Advanced settings
            if 'debug_mode' in config_data:
                self.debug_mode_var.set(config_data['debug_mode'])
            
            if 'verbose_logging' in config_data:
                self.verbose_logging_var.set(config_data['verbose_logging'])
            
            if 'save_intermediate' in config_data:
                self.save_intermediate_var.set(config_data['save_intermediate'])
            
            if 'profile_analysis' in config_data:
                self.profile_analysis_var.set(config_data['profile_analysis'])
            
            if 'track_memory' in config_data:
                self.track_memory_var.set(config_data['track_memory'])
            
            # Thresholds
            thresholds = config_data.get('thresholds', {})
            for domain, domain_thresholds in thresholds.items():
                if domain in self.threshold_vars:
                    threshold_vars = self.threshold_vars[domain]
                    for key, value in domain_thresholds.items():
                        if key in threshold_vars:
                            threshold_vars[key].set(str(value))
            
            # Update displays
            self._update_config_info()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error applying configuration: {str(e)}")
    
    def _update_ui_from_config(self):
        """Update UI from current configuration"""
        config_data = {
            'max_concurrent_tasks': self.current_config.max_concurrent_tasks,
            'default_timeout': self.current_config.default_timeout,
            'output_directory': self.current_config.output_directory,
            'log_level': self.current_config.log_level,
            'enable_real_time_alerts': self.current_config.enable_real_time_alerts,
            'auto_generate_reports': self.current_config.auto_generate_reports,
            'data_retention_days': self.current_config.data_retention_days,
            'thresholds': {
                'SOLDIER_SAFETY': self.current_config.safety_thresholds,
                'NETWORK_PERFORMANCE': self.current_config.network_thresholds
            }
        }
        
        self._apply_config_data(config_data)
    
    def _create_system_configuration(self) -> SystemConfiguration:
        """Create SystemConfiguration object from current settings"""
        config_data = self._get_config_data()
        
        config = SystemConfiguration()
        config.max_concurrent_tasks = config_data['max_concurrent_tasks']
        config.default_timeout = config_data['default_timeout']
        config.output_directory = config_data['output_directory']
        config.log_level = config_data['log_level']
        config.enable_real_time_alerts = config_data['enable_real_time_alerts']
        config.auto_generate_reports = config_data['auto_generate_reports']
        config.data_retention_days = config_data['data_retention_days']
        
        # Set thresholds
        config.safety_thresholds = config_data['thresholds'].get('SOLDIER_SAFETY', {})
        config.network_thresholds = config_data['thresholds'].get('NETWORK_PERFORMANCE', {})
        
        return config
    
    def _on_config_changed(self, *args):
        """Handle configuration change"""
        self.unsaved_changes = True
        self._update_status("Configuration modified")
        self._update_config_info()
    
    def _update_status(self, message: str):
        """Update status label"""
        self.status_label.config(text=message)
    
    def _validate_inputs(self) -> List[str]:
        """Validate all inputs"""
        errors = []
        
        # Validate numeric inputs
        try:
            max_tasks = int(self.max_tasks_var.get())
            if max_tasks <= 0:
                errors.append("Max concurrent tasks must be positive")
        except ValueError:
            errors.append("Max concurrent tasks must be a number")
        
        try:
            timeout = int(self.timeout_var.get())
            if timeout <= 0:
                errors.append("Default timeout must be positive")
        except ValueError:
            errors.append("Default timeout must be a number")
        
        try:
            retention = int(self.retention_var.get())
            if retention <= 0:
                errors.append("Data retention days must be positive")
        except ValueError:
            errors.append("Data retention days must be a number")
        
        # Validate output directory
        output_dir = self.output_dir_var.get()
        if not output_dir:
            errors.append("Output directory is required")
        else:
            try:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
            except Exception:
                errors.append("Output directory path is invalid")
        
        # Validate thresholds
        for domain, threshold_vars in self.threshold_vars.items():
            for key, var in threshold_vars.items():
                try:
                    value = float(var.get())
                    if value < 0:
                        errors.append(f"{domain} {key} must be non-negative")
                except ValueError:
                    errors.append(f"{domain} {key} must be a number")
        
        return errors
    
    def _apply(self):
        """Apply configuration changes"""
        try:
            # Validate inputs
            errors = self._validate_inputs()
            if errors:
                error_msg = "Configuration errors:\n\n" + "\n".join(errors)
                messagebox.showerror("Configuration Errors", error_msg)
                return
            
            # Create new configuration
            new_config = self._create_system_configuration()
            
            # Apply configuration
            self.current_config = new_config
            self.result = new_config
            self.unsaved_changes = False
            
            self._update_status("Configuration applied")
            messagebox.showinfo("Success", "Configuration applied successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error applying configuration: {str(e)}")
    
    def _ok(self):
        """OK button handler"""
        self._apply()
        if self.result:
            self.destroy()
    
    def _cancel(self):
        """Cancel button handler"""
        if self.unsaved_changes:
            if messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Are you sure you want to cancel?"):
                self.result = None
                self.destroy()
        else:
            self.result = None
            self.destroy()
    
    def _on_closing(self):
        """Handle window closing"""
        self._cancel()
    
    def get_configuration(self) -> Optional[SystemConfiguration]:
        """Get the configured system configuration"""
        return self.result


def show_configuration_dialog(parent, current_config: SystemConfiguration = None) -> Optional[SystemConfiguration]:
    """
    Show configuration dialog and return the configured SystemConfiguration
    
    Args:
        parent: Parent window
        current_config: Current system configuration
        
    Returns:
        New SystemConfiguration if OK was clicked, None if cancelled
    """
    dialog = ConfigurationDialog(parent, current_config)
    parent.wait_window(dialog)
    return dialog.get_configuration()


class ThresholdEditDialog(tk.Toplevel):
    """
    Threshold Edit Dialog - for editing individual threshold values
    """
    
    def __init__(self, parent, domain: str, threshold_name: str, current_value: float, 
                 description: str = "", unit: str = "", min_value: float = None, max_value: float = None):
        super().__init__(parent)
        self.parent = parent
        self.domain = domain
        self.threshold_name = threshold_name
        self.current_value = current_value
        self.description = description
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.result = None
        
        # Setup window
        self._setup_window()
        
        # Create UI
        self._create_ui()
    
    def _setup_window(self):
        """Setup window properties"""
        self.title(f"Edit Threshold - {self.threshold_name}")
        self.geometry("400x300")
        self.transient(self.parent)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 200
        y = (self.winfo_screenheight() // 2) - 150
        self.geometry(f"400x300+{x}+{y}")
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._cancel)
    
    def _create_ui(self):
        """Create threshold edit UI"""
        # Main frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(header_frame, text=f"Domain: {self.domain}", 
                 font=("Arial", 10, "bold")).pack(anchor="w")
        ttk.Label(header_frame, text=f"Threshold: {self.threshold_name}").pack(anchor="w")
        
        if self.description:
            ttk.Label(header_frame, text=f"Description: {self.description}", 
                     wraplength=350).pack(anchor="w", pady=(5, 0))
        
        # Value input
        value_frame = ttk.LabelFrame(main_frame, text="Threshold Value", padding="10")
        value_frame.pack(fill="x", pady=(0, 20))
        
        input_frame = ttk.Frame(value_frame)
        input_frame.pack(fill="x")
        
        ttk.Label(input_frame, text="Value:").pack(side="left")
        
        self.value_var = tk.StringVar(value=str(self.current_value))
        self.value_entry = ttk.Entry(input_frame, textvariable=self.value_var, width=15)
        self.value_entry.pack(side="left", padx=(5, 0))
        
        if self.unit:
            ttk.Label(input_frame, text=self.unit).pack(side="left", padx=(5, 0))
        
        # Validation info
        if self.min_value is not None or self.max_value is not None:
            validation_frame = ttk.Frame(value_frame)
            validation_frame.pack(fill="x", pady=(10, 0))
            
            validation_text = "Valid range: "
            if self.min_value is not None:
                validation_text += f"≥ {self.min_value}"
            if self.max_value is not None:
                if self.min_value is not None:
                    validation_text += f" and ≤ {self.max_value}"
                else:
                    validation_text += f"≤ {self.max_value}"
            
            ttk.Label(validation_frame, text=validation_text, 
                     foreground="gray").pack(anchor="w")
        
        # Current value info
        current_frame = ttk.LabelFrame(main_frame, text="Current Information", padding="10")
        current_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(current_frame, text=f"Current Value: {self.current_value} {self.unit}").pack(anchor="w")
        
        # Get default value if available
        try:
            domain_enum = AnalysisDomain(self.domain)
            default_thresholds = DEFAULT_THRESHOLDS.get(domain_enum, {})
            default_value = default_thresholds.get(self.threshold_name.lower())
            
            if default_value is not None:
                ttk.Label(current_frame, text=f"Default Value: {default_value} {self.unit}").pack(anchor="w")
        except:
            pass
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        ttk.Button(button_frame, text="Reset to Default", 
                  command=self._reset_to_default).pack(side="left")
        
        ttk.Button(button_frame, text="Cancel", 
                  command=self._cancel).pack(side="right")
        ttk.Button(button_frame, text="OK", 
                  command=self._ok).pack(side="right", padx=(0, 5))
        
        # Focus on entry
        self.value_entry.focus_set()
        self.value_entry.select_range(0, tk.END)
    
    def _reset_to_default(self):
        """Reset to default value"""
        try:
            domain_enum = AnalysisDomain(self.domain)
            default_thresholds = DEFAULT_THRESHOLDS.get(domain_enum, {})
            default_value = default_thresholds.get(self.threshold_name.lower())
            
            if default_value is not None:
                self.value_var.set(str(default_value))
            else:
                messagebox.showwarning("No Default", "No default value available for this threshold")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error getting default value: {str(e)}")
    
    def _validate_value(self) -> bool:
        """Validate entered value"""
        try:
            value = float(self.value_var.get())
            
            if self.min_value is not None and value < self.min_value:
                messagebox.showerror("Invalid Value", f"Value must be ≥ {self.min_value}")
                return False
            
            if self.max_value is not None and value > self.max_value:
                messagebox.showerror("Invalid Value", f"Value must be ≤ {self.max_value}")
                return False
            
            return True
            
        except ValueError:
            messagebox.showerror("Invalid Value", "Value must be a number")
            return False
    
    def _ok(self):
        """OK button handler"""
        if self._validate_value():
            self.result = float(self.value_var.get())
            self.destroy()
    
    def _cancel(self):
        """Cancel button handler"""
        self.result = None
        self.destroy()
    
    def get_value(self) -> Optional[float]:
        """Get the entered value"""
        return self.result


def show_threshold_edit_dialog(parent, domain: str, threshold_name: str, current_value: float, 
                             description: str = "", unit: str = "", 
                             min_value: float = None, max_value: float = None) -> Optional[float]:
    """
    Show threshold edit dialog and return the new value
    
    Args:
        parent: Parent window
        domain: Domain name
        threshold_name: Threshold name
        current_value: Current threshold value
        description: Description of the threshold
        unit: Unit of measurement
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        New threshold value if OK was clicked, None if cancelled
    """
    dialog = ThresholdEditDialog(parent, domain, threshold_name, current_value, 
                               description, unit, min_value, max_value)
    parent.wait_window(dialog)
    return dialog.get_value()