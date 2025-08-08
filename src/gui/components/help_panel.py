# File: src/gui/components/help_panel.py
"""Help panel component for the Enhanced Soldier Report System"""

import tkinter as tk
from tkinter import ttk


class HelpPanel:
    """Help panel component with comprehensive documentation"""
    
    def __init__(self, parent):
        self.parent = parent
        self.setup_help_tab()
    
    def setup_help_tab(self):
        """Setup the enhanced help tab with comprehensive documentation based on interface design specifications"""
        
        # Create main container with scrollable content
        main_container = tk.Frame(self.parent, bg='#ecf0f1')
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create canvas and scrollbar for scrollable content
        canvas = tk.Canvas(main_container, bg='#ecf0f1', highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ecf0f1')
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Header Section
        self._create_help_header(scrollable_frame)
        
        # Main content sections
        self._create_assessment_overview(scrollable_frame)
        self._create_data_models_section(scrollable_frame)
        self._create_analysis_framework_section(scrollable_frame)
        self._create_performance_scoring_section(scrollable_frame)
        self._create_safety_monitoring_section(scrollable_frame)
        self._create_report_configuration_section(scrollable_frame)
        self._create_troubleshooting_section(scrollable_frame)
        self._create_interface_patterns_section(scrollable_frame)
        
        # Footer
        self._create_help_footer(scrollable_frame)

    def _create_help_header(self, parent):
        """Create the help section header"""
        header_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Main title
        title_label = tk.Label(header_frame, 
                              text="🎖️ Enhanced Soldier Report System - Complete User Guide",
                              font=('Arial', 16, 'bold'),
                              fg='white', bg='#34495e')
        title_label.pack(pady=(15, 5))
        
        # Subtitle
        subtitle_label = tk.Label(header_frame,
                                 text="Comprehensive Military Performance Analysis & Safety Monitoring",
                                 font=('Arial', 11),
                                 fg='#bdc3c7', bg='#34495e')
        subtitle_label.pack(pady=(0, 10))
        
        # Version info
        version_label = tk.Label(header_frame,
                                text="Version 2.0 | Interface Design v2.0 | August 2025",
                                font=('Arial', 9),
                                fg='#95a5a6', bg='#34495e')
        version_label.pack(pady=(0, 15))

    def _create_assessment_overview(self, parent):
        """Create assessment criteria overview section"""
        section_frame = self._create_section_frame(parent, "🎯 ASSESSMENT CRITERIA OVERVIEW")
        
        content = """
📊 PERFORMANCE SCORING SYSTEM (0-100 Points)

The Enhanced Soldier Report System uses a comprehensive multi-factor scoring algorithm:

🔹 PHYSICAL PERFORMANCE (30-40% of score)
   • Activity Level: Step count and movement patterns
   • Posture Analysis: Battle positioning and stability  
   • Fall Incidents: Safety and coordination assessment
   • Mission Duration: Endurance and persistence metrics

🔹 EQUIPMENT READINESS (20-25% of score)
   • Battery Management: Power conservation and planning
   • Communication Quality: Signal strength and connectivity
   • Equipment Failures: Reliability and maintenance

🔹 COMBAT EFFECTIVENESS (25-30% of score)
   • Engagement Statistics: Active participation in scenarios
   • Casualty Status: Mission outcome and survival
   • Tactical Positioning: Strategic movement and positioning

🔹 SAFETY COMPLIANCE (15-20% of score)
   • Medical Alert Response: Following safety protocols
   • Environmental Awareness: Temperature and stress management
   • Risk Mitigation: Proactive safety measures

⚔️ BATTLE CONTEXT ANALYSIS
The system distinguishes between different mission phases:
   • Pre-Battle Period: Setup and preparation assessment
   • Active Battle Period: Last 45 minutes of high-intensity activity
   • Post-Battle Period: Recovery and debrief analysis

Different scoring weightings apply to each phase based on operational priorities.
        """
        
        self._add_content_text(section_frame, content)

    def _create_data_models_section(self, parent):
        """Create data models documentation section"""
        section_frame = self._create_section_frame(parent, "📋 DATA MODELS & STRUCTURE")
        
        content = """
🗂️ CORE DATA STRUCTURES

📌 SoldierIdentity (Immutable)
   • Callsign: Primary identifier for soldier
   • Player ID: System-generated unique identifier  
   • Squad/Platoon: Unit assignment and hierarchy

📌 SoldierDataRecord (Complete Profile)
   • Physical Metrics: Movement, posture, activity levels
   • Physiological Metrics: Heart rate zones, temperature
   • Equipment Metrics: Battery, communication, failures
   • Combat Metrics: Engagements, weapons, casualties
   • Data Quality: Completeness and reliability scores

📊 METRICS CATEGORIES

🏃 PhysicalMetrics
   • Step counting and movement analysis
   • Posture distribution and stability assessment
   • Fall detection and incident tracking
   • Activity level categorization

❤️ PhysiologicalMetrics  
   • Heart rate zones and statistical analysis
   • Temperature monitoring and stress detection
   • Abnormal reading flags and medical alerts
   • Physiological stress indicators

🔋 EquipmentMetrics
   • Battery level monitoring and optimization
   • Communication quality (RSSI) assessment
   • Equipment failure tracking and prediction
   • Risk level assessment for mission readiness

⚔️ CombatMetrics
   • Casualty status tracking and analysis
   • Engagement statistics and effectiveness
   • Weapon and munition data analysis
   • Survival and tactical effectiveness metrics
        """
        
        self._add_content_text(section_frame, content)

    def _create_analysis_framework_section(self, parent):
        """Create analysis framework documentation"""
        section_frame = self._create_section_frame(parent, "🔬 ANALYSIS FRAMEWORK")
        
        content = """
🎯 ANALYSIS STATUS LEVELS
   • PENDING: Analysis queued for processing
   • IN_PROGRESS: Active analysis in progress
   • COMPLETED: Analysis finished successfully
   • FAILED: Analysis encountered errors
   • CANCELLED: Analysis terminated by user

⚠️ RISK LEVEL ASSESSMENT
   • LOW: Minimal risk, standard monitoring
   • MODERATE: Increased attention recommended
   • HIGH: Immediate supervisor notification
   • CRITICAL: Emergency response required

🏆 PERFORMANCE RATING SCALE
   • EXCELLENT (90-100): Exemplary performance, commendation worthy
   • GOOD (80-89): Above average, meets high standards
   • SATISFACTORY (70-79): Meets basic requirements
   • NEEDS_IMPROVEMENT (60-69): Below standard, training recommended
   • CRITICAL (<60): Immediate intervention required

📈 SPECIALIZED ANALYSIS MODULES

❤️ HeartRateAnalysis
   • Statistical summaries with percentiles (5th, 25th, 50th, 75th, 95th)
   • Heart rate zone distribution analysis
   • Abnormal reading detection and flagging
   • Risk assessment with automated medical flags
   • Trend analysis for performance optimization

🏃 PhysicalPerformanceAnalysis
   • Step statistics and activity level assessment
   • Movement pattern analysis and optimization
   • Fall incident tracking and prevention
   • Performance rating assignment with detailed breakdown

🛡️ SafetyAnalysis
   • Overall safety score calculation (0-100)
   • Multi-dimensional risk assessment matrix
   • Temperature stress monitoring and alerts
   • Medical recommendations and action items
   • Immediate intervention requirements
        """
        
        self._add_content_text(section_frame, content)

    def _create_performance_scoring_section(self, parent):
        """Create performance scoring documentation"""
        section_frame = self._create_section_frame(parent, "📊 PERFORMANCE SCORING METHODOLOGY")
        
        content = """
🎖️ COMPREHENSIVE SCORING ALGORITHM

The system uses a 100-point scale with the following breakdown:

📍 STARTING BASELINE: 100 Points
All soldiers begin with perfect score, points deducted for performance issues.

➖ PERFORMANCE DEDUCTIONS

🔹 Activity Level Penalties
   • Low Activity (<50 avg steps): -15 points
   • Moderate Activity (50-100 avg steps): -10 points  
   • Insufficient movement patterns: -5 points

🔹 Mission Outcome Penalties  
   • WOUNDED status: -10 points
   • KIA (Killed in Action): -20 points
   • Mission failure incidents: -5 to -15 points

🔹 Equipment Readiness Penalties
   • Critical battery (<20%): -15 points
   • Low battery (20-40%): -8 points
   • Poor communication quality: -5 points
   • Equipment failures: -3 to -10 points

🔹 Safety Compliance Penalties
   • Medical alert incidents: -3 points each
   • Safety protocol violations: -5 to -10 points
   • Risk mitigation failures: -5 points

➕ PERFORMANCE BONUSES

🔹 Excellence Bonuses
   • Excellent communication quality: +3 points
   • Active combat engagement: +1 to +5 points
   • Leadership demonstration: +2 to +5 points
   • Equipment optimization: +1 to +3 points

🔹 Mission Achievement Bonuses
   • Objective completion: +2 to +8 points
   • Team coordination: +1 to +5 points
   • Tactical innovation: +2 to +5 points

🎯 FINAL SCORE CALCULATION
Final Score = 100 + Bonuses - Deductions (Minimum: 0, Maximum: 110)

📋 PERFORMANCE BREAKDOWN TRACKING
Every report includes detailed breakdown showing:
   • Starting score: 100 points
   • Total deductions with specific reasons
   • Total bonuses with achievement details  
   • Final calculated score
   • Performance rating assignment
        """
        
        self._add_content_text(section_frame, content)

    def _create_safety_monitoring_section(self, parent):
        """Create safety monitoring documentation"""
        section_frame = self._create_section_frame(parent, "🛡️ SAFETY MONITORING SYSTEM")
        
        content = """
💡 MEDICAL MONITORING PHILOSOPHY

The system prioritizes soldier health and safety above performance metrics:

❤️ HEART RATE MONITORING (Medical Focus)
   • Normal Range: 60-190 BPM (NO performance penalty)
   • >190 BPM: MEDICAL ALERT (immediate evaluation, no penalty)
   • <60 BPM: Medical evaluation recommended (no penalty)
   • Heart rate used for SAFETY, not performance punishment

🌡️ TEMPERATURE STRESS MONITORING
   • Normal Range: 95-100°F
   • >104°F: HEAT EMERGENCY - immediate cooling protocols
   • >100°F: Heat stress detected - increased monitoring
   • <95°F: Cold stress - warming protocols initiated

🚨 AUTOMATED ALERT SYSTEM

⚠️ MEDICAL ALERTS (No Performance Impact)
   • Physiological stress indicators
   • Abnormal vital sign patterns
   • Environmental stress conditions
   • Equipment failure medical risks

🔴 CRITICAL ALERTS (Immediate Response)
   • Cardiac emergency indicators (HR >190 BPM)
   • Heat stroke risk (Temp >104°F)
   • Equipment failure in hazardous conditions
   • Fall detection with no response

📋 MEDICAL RECOMMENDATIONS ENGINE

The system generates specific medical recommendations:

🔹 IMMEDIATE ACTION REQUIRED
   • Emergency medical evaluation
   • Environmental hazard mitigation
   • Equipment replacement/repair
   • Mission modification recommendations

🔹 ROUTINE MONITORING
   • Increased check intervals
   • Preventive care scheduling
   • Training recommendations
   • Equipment optimization

🔹 PERFORMANCE OPTIMIZATION
   • Physical conditioning programs
   • Stress management techniques
   • Equipment training needs
   • Tactical skill development

🎖️ SAFETY-FIRST SCORING PRINCIPLE
Performance scores reflect controllable factors:
   ✅ Effort, preparation, decision-making
   ❌ NOT medical conditions or physiological limits
        """
        
        self._add_content_text(section_frame, content)

    def _create_report_configuration_section(self, parent):
        """Create report configuration documentation"""
        section_frame = self._create_section_frame(parent, "📄 REPORT CONFIGURATION")
        
        content = """
📋 REPORT TYPES AVAILABLE

🔹 INDIVIDUAL_SOLDIER
   • Comprehensive single-soldier analysis
   • Detailed performance breakdown
   • Medical monitoring summary
   • Tactical assessment and recommendations

🔹 SQUAD_SUMMARY  
   • Multi-soldier comparative analysis
   • Squad-level performance metrics
   • Team coordination assessment
   • Leadership identification

🔹 BATTLE_ANALYSIS
   • Mission-wide performance overview
   • Tactical effectiveness assessment
   • Lessons learned compilation
   • Strategic recommendations

🔹 SAFETY_REPORT
   • Medical incident analysis
   • Risk assessment summary
   • Safety protocol compliance
   • Prevention recommendations

🔹 PERFORMANCE_COMPARISON
   • Cross-mission analysis
   • Trend identification
   • Improvement tracking
   • Benchmark comparisons
        """
        
        self._add_content_text(section_frame, content)

    def _create_troubleshooting_section(self, parent):
        """Create troubleshooting documentation"""
        section_frame = self._create_section_frame(parent, "🔧 TROUBLESHOOTING GUIDE")
        
        content = """
❗ COMMON ISSUES & SOLUTIONS

🔹 DATA LOADING PROBLEMS
   • File Format: Ensure CSV with proper column headers
   • Column Mapping: Verify Fort Moore data format compatibility
   • File Size: Large files may require chunked processing
   • Encoding: Check UTF-8 encoding for special characters

🔹 ANALYSIS FAILURES
   • Data Quality: Minimum 70% data completeness required
   • Time Coverage: Ensure sufficient data duration
   • Missing Columns: Critical columns must be present
   • Data Types: Verify numeric data in appropriate columns

🔹 REPORT GENERATION ISSUES
   • Memory Limits: Large batches may need smaller chunks
   • Template Errors: Check template syntax and references
   • Output Directory: Ensure write permissions
   • File Conflicts: Resolve naming conflicts with existing files
        """
        
        self._add_content_text(section_frame, content)

    def _create_interface_patterns_section(self, parent):
        """Create interface patterns documentation"""
        section_frame = self._create_section_frame(parent, "🎛️ INTERFACE DESIGN PATTERNS")
        
        content = """
🏗️ SYSTEM ARCHITECTURE OVERVIEW

📋 Separation of Concerns
   • Data Models: Pure data structures with validation
   • Analysis Logic: Separate processing components  
   • Controller Layer: User interface coordination
   • Report Generation: Configurable presentation layer
   • Configuration: Externalized settings and templates

🔄 Event-Driven Architecture
   • Centralized event bus for component communication
   • Type-safe event classes with structured data
   • Priority-based event handling system
   • Asynchronous processing with thread pool execution
   • Comprehensive error isolation and recovery
        """
        
        self._add_content_text(section_frame, content)

    def _create_help_footer(self, parent):
        """Create help section footer"""
        footer_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=2)
        footer_frame.pack(fill='x', pady=(20, 0))
        
        # System info
        system_info = tk.Label(footer_frame,
                              text="🎖️ Enhanced Individual Soldier Report System",
                              font=('Arial', 12, 'bold'),
                              fg='white', bg='#34495e')
        system_info.pack(pady=(10, 5))
        
        # Technical details
        tech_info = tk.Label(footer_frame,
                            text="Advanced Analytics for Military Operations | Controller Architecture v2.0",
                            font=('Arial', 10),
                            fg='#bdc3c7', bg='#34495e')
        tech_info.pack(pady=(0, 5))
        
        # Classification
        classification = tk.Label(footer_frame,
                                 text="FOR OFFICIAL USE ONLY (FOUO) | Export Controlled",
                                 font=('Arial', 9, 'bold'),
                                 fg='#e74c3c', bg='#34495e')
        classification.pack(pady=(0, 10))

    def _create_section_frame(self, parent, title):
        """Create a standardized section frame with title"""
        # Section container
        section_frame = tk.Frame(parent, bg='#ecf0f1')
        section_frame.pack(fill='x', pady=(0, 15))
        
        # Section title
        title_frame = tk.Frame(section_frame, bg='#3498db', relief='raised', bd=1)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title_label = tk.Label(title_frame, text=title,
                              font=('Arial', 12, 'bold'),
                              fg='white', bg='#3498db')
        title_label.pack(pady=8)
        
        # Content container
        content_frame = tk.Frame(section_frame, bg='white', relief='solid', bd=1)
        content_frame.pack(fill='x', padx=5)
        
        return content_frame

    def _add_content_text(self, parent, content):
        """Add formatted content text to a section"""
        text_widget = tk.Text(parent, 
                             font=('Courier', 9),
                             bg='white', fg='#2c3e50',
                             wrap='word', 
                             state='normal',
                             relief='flat',
                             padx=15, pady=15,
                             height=content.count('\n') + 2)
        
        text_widget.pack(fill='x', padx=5, pady=5)
        
        # Insert content
        text_widget.insert('1.0', content.strip())
        
        # Apply formatting for headings and special text
        lines = content.strip().split('\n')
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('📊') or line.strip().startswith('🔹') or line.strip().startswith('🎯'):
                text_widget.tag_add('heading', f'{i}.0', f'{i}.end')
            elif line.strip().startswith('   •'):
                text_widget.tag_add('bullet', f'{i}.0', f'{i}.end')
            elif '❤️' in line or '🌡️' in line or '🚨' in line:
                text_widget.tag_add('important', f'{i}.0', f'{i}.end')
        
        # Configure tags
        text_widget.tag_config('heading', font=('Arial', 10, 'bold'), foreground='#2c3e50')
        text_widget.tag_config('bullet', font=('Courier', 9), foreground='#34495e', lmargin1=20)
        text_widget.tag_config('important', font=('Arial', 9, 'bold'), foreground='#e74c3c')
        
        # Make read-only
        text_widget.config(state='disabled')
        
        return text_widget