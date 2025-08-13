#!/usr/bin/env python3
"""
Fix specific import issues in core modules
"""

import os
import re
from pathlib import Path

def fix_core_event_bus():
    """Fix imports in core/event_bus.py"""
    event_bus_path = Path("src/core/event_bus.py")
    
    if not event_bus_path.exists():
        print(f"File not found: {event_bus_path}")
        return
    
    try:
        with open(event_bus_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix the specific import issue
        # Change "from events import" to "from core.events import"
        content = re.sub(r'from\s+events\s+import', 'from core.events import', content)
        
        # Also fix any other similar patterns
        content = re.sub(r'import\s+events', 'import core.events as events', content)
        
        if content != original_content:
            with open(event_bus_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed imports in: {event_bus_path}")
            return True
        else:
            print(f"No changes needed in: {event_bus_path}")
            return False
        
    except Exception as e:
        print(f"Error processing {event_bus_path}: {e}")
        return False

def fix_other_core_imports():
    """Fix other potential import issues in core modules"""
    core_dir = Path("src/core")
    
    for py_file in core_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix imports within core modules
            # Pattern: from events import -> from core.events import
            content = re.sub(r'from\s+events\s+import', 'from core.events import', content)
            content = re.sub(r'from\s+event_bus\s+import', 'from core.event_bus import', content)
            
            # Fix any remaining simple imports
            content = re.sub(r'^import\s+events$', 'import core.events as events', content, flags=re.MULTILINE)
            content = re.sub(r'^import\s+event_bus$', 'import core.event_bus as event_bus', content, flags=re.MULTILINE)
            
            if content != original_content:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed imports in: {py_file}")
        
        except Exception as e:
            print(f"Error processing {py_file}: {e}")

def main():
    print("Fixing core module import issues...")
    
    # Change to project directory
    if not Path("src").exists():
        print("Error: 'src' directory not found. Make sure you're running this from the project root.")
        return 1
    
    # Fix specific issues
    fix_core_event_bus()
    fix_other_core_imports()
    
    print("\nCore imports fixed! Try running again:")
    print("python -m src.main")
    
    return 0

if __name__ == "__main__":
    exit(main())
