#!/usr/bin/env python3
"""
Fix missing import issues in the Enhanced Soldier Report System
This script will identify and fix missing class imports
"""

import os
import re
from pathlib import Path

def find_missing_imports():
    """Find all missing imports in the project"""
    src_dir = Path("src")
    missing_imports = []
    
    # Common missing classes that need to be created
    missing_classes = {
        'AnalysisResults': 'models.analysis_results',
        'BatchAnalysisResult': 'models.analysis_results', 
        'SoldierAnalysisResult': 'models.analysis_results',
        'ReportConfig': 'models.report_config',
        'Settings': 'config.settings',
        'HtmlRenderer': 'reporting.html_renderer',
        'PerformanceScorer': 'services.performance_scorer',
        'SafetyAnalyzer': 'services.safety_analyzer',
    }
    
    for py_file in src_dir.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find import statements
            import_lines = re.findall(r'from\s+[\w.]+\s+import\s+[\w\s,]+', content)
            
            for line in import_lines:
                # Extract imported names
                parts = line.split(' import ')
                if len(parts) == 2:
                    module_part = parts[0].replace('from ', '').strip()
                    imports_part = parts[1].strip()
                    imported_names = [name.strip() for name in imports_part.split(',')]
                    
                    for name in imported_names:
                        if name in missing_classes:
                            missing_imports.append((py_file, line, name, missing_classes[name]))
                            
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return missing_imports

def create_missing_modules():
    """Create missing modules with placeholder classes"""
    
    modules_to_create = {
        'src/models/analysis_results.py': '''"""Analysis results data models"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class PerformanceRating(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    NEEDS_IMPROVEMENT = "needs_improvement"
    CRITICAL = "critical"

@dataclass
class AnalysisResults:
    """Base analysis results class"""
    soldier_id: str
    timestamp: datetime
    overall_risk: RiskLevel = RiskLevel.LOW
    performance_rating: PerformanceRating = PerformanceRating.SATISFACTORY
    notes: str = ""
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

@dataclass
class SoldierAnalysisResult(AnalysisResults):
    """Individual soldier analysis results"""
    callsign: str = ""
    physical_metrics: Dict[str, Any] = None
    physiological_metrics: Dict[str, Any] = None
    safety_metrics: Dict[str, Any] = None
    performance_score: float = 0.0
    
    def __post_init__(self):
        super().__post_init__()
        if self.physical_metrics is None:
            self.physical_metrics = {}
        if self.physiological_metrics is None:
            self.physiological_metrics = {}
        if self.safety_metrics is None:
            self.safety_metrics = {}

@dataclass
class BatchAnalysisResult:
    """Batch analysis results for multiple soldiers"""
    results: List[SoldierAnalysisResult]
    summary: Dict[str, Any]
    timestamp: datetime
    total_soldiers: int = 0
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
        self.total_soldiers = len(self.results)
''',
        
        'src/models/report_config.py': '''"""Report configuration models"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum
from pathlib import Path

class ReportType(Enum):
    INDIVIDUAL_SOLDIER = "individual_soldier"
    SQUAD_SUMMARY = "squad_summary"
    BATTLE_ANALYSIS = "battle_analysis"
    SAFETY_REPORT = "safety_report"
    PERFORMANCE_COMPARISON = "performance_comparison"

class ReportFormat(Enum):
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"

@dataclass
class ReportConfig:
    """Configuration for report generation"""
    report_type: ReportType = ReportType.INDIVIDUAL_SOLDIER
    report_format: ReportFormat = ReportFormat.HTML
    template_name: str = "default"
    output_directory: Path = None
    include_charts: bool = True
    include_raw_data: bool = False
    classification_level: str = "UNCLASSIFIED"
    custom_sections: List[str] = None
    
    def __post_init__(self):
        if self.output_directory is None:
            self.output_directory = Path("reports")
        if self.custom_sections is None:
            self.custom_sections = []
        if isinstance(self.output_directory, str):
            self.output_directory = Path(self.output_directory)
''',
        
        'src/config/settings.py': '''"""Application settings and configuration"""
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Settings:
    """Application settings"""
    max_workers: int = 4
    event_queue_size: int = 1000
    debug_mode: bool = False
    log_level: str = "INFO"
    data_directory: str = "data"
    reports_directory: str = "reports"
    templates_directory: str = "templates"
    
    @classmethod
    def load_from_file(cls, config_path: Path) -> 'Settings':
        """Load settings from configuration file"""
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                return cls(**config_data)
            except Exception as e:
                print(f"Error loading config: {e}")
        return cls()  # Return default settings
    
    def save_to_file(self, config_path: Path):
        """Save settings to configuration file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_data = {
            'max_workers': self.max_workers,
            'event_queue_size': self.event_queue_size,
            'debug_mode': self.debug_mode,
            'log_level': self.log_level,
            'data_directory': self.data_directory,
            'reports_directory': self.reports_directory,
            'templates_directory': self.templates_directory
        }
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
''',
        
        'src/reporting/html_renderer.py': '''"""HTML rendering service for reports"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template

class HtmlRenderer:
    """Service for rendering HTML reports"""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"
        
        self.templates_dir = templates_dir
        self.templates_dir.mkdir(exist_ok=True)
        
        try:
            self.env = Environment(loader=FileSystemLoader(str(templates_dir)))
        except Exception as e:
            self.logger.warning(f"Could not initialize Jinja2 environment: {e}")
            self.env = None
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template with the given context"""
        try:
            if self.env:
                template = self.env.get_template(template_name)
                return template.render(**context)
            else:
                # Fallback to simple string replacement
                return self._simple_render(template_name, context)
        except Exception as e:
            self.logger.error(f"Error rendering template {template_name}: {e}")
            return self._create_error_html(str(e))
    
    def _simple_render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Simple fallback rendering"""
        return f"""
        <html>
        <head><title>Report</title></head>
        <body>
            <h1>Enhanced Soldier Report System</h1>
            <p>Template: {template_name}</p>
            <p>Context: {context}</p>
        </body>
        </html>
        """
    
    def _create_error_html(self, error_msg: str) -> str:
        """Create error HTML"""
        return f"""
        <html>
        <head><title>Render Error</title></head>
        <body>
            <h1>Template Rendering Error</h1>
            <p>{error_msg}</p>
        </body>
        </html>
        """
''',
    }
    
    # Create the modules
    for file_path, content in modules_to_create.items():
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if not path.exists():
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created: {path}")
        else:
            print(f"Already exists: {path}")

def fix_import_statements():
    """Fix problematic import statements"""
    
    # Files and their import fixes
    fixes = {
        'src/services/analysis_engine.py': [
            ('from models.soldier_data import SoldierDataset, AnalysisResults', 
             'from models.soldier_data import SoldierDataset\nfrom models.analysis_results import SoldierAnalysisResult, BatchAnalysisResult'),
        ],
        'src/services/performance_scorer.py': [
            ('from models.analysis_results import AnalysisResults',
             'from models.analysis_results import SoldierAnalysisResult'),
        ],
        'src/services/safety_analyzer.py': [
            ('from models.analysis_results import AnalysisResults',
             'from models.analysis_results import SoldierAnalysisResult'),
        ],
        'src/reporting/report_generator.py': [
            ('from models.report_config import ReportConfig',
             'from models.report_config import ReportConfig'),
            ('from reporting.html_renderer import HtmlRenderer',
             'from reporting.html_renderer import HtmlRenderer'),
        ],
    }
    
    for file_path, file_fixes in fixes.items():
        path = Path(file_path)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                for old_import, new_import in file_fixes:
                    content = content.replace(old_import, new_import)
                
                if content != original_content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Fixed imports in: {path}")
                    
            except Exception as e:
                print(f"Error fixing {path}: {e}")

def main():
    """Main function to fix all import issues"""
    print("Fixing missing import issues...")
    
    if not Path("src").exists():
        print("Error: 'src' directory not found.")
        return 1
    
    print("\\n1. Creating missing modules...")
    create_missing_modules()
    
    print("\\n2. Fixing import statements...")
    fix_import_statements()
    
    print("\\n3. Finding remaining issues...")
    missing = find_missing_imports()
    
    if missing:
        print("\\nRemaining issues found:")
        for file_path, line, name, suggested_module in missing:
            print(f"  {file_path}: {name} (suggested: {suggested_module})")
    else:
        print("No remaining import issues found!")
    
    print("\\nTry running the application again:")
    print("python -m src.main")
    
    return 0

if __name__ == "__main__":
    exit(main())
