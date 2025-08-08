#!/usr/bin/env python3
"""
Script to fix relative imports in the Enhanced Soldier Report System
Run this from the project root directory
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path: Path):
    """Fix relative imports in a single Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace relative imports with absolute imports
        # Pattern: from ..module import something -> from module import something
        content = re.sub(r'from\s+\.\.([a-zA-Z_][a-zA-Z0-9_.]*)\s+import', r'from \1 import', content)
        
        # Pattern: from .module import something -> from module import something  
        content = re.sub(r'from\s+\.([a-zA-Z_][a-zA-Z0-9_.]*)\s+import', r'from \1 import', content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed imports in: {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def fix_all_imports(src_dir: Path):
    """Fix imports in all Python files in the src directory"""
    python_files = list(src_dir.rglob("*.py"))
    fixed_count = 0
    
    for py_file in python_files:
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print(f"\nFixed imports in {fixed_count} files out of {len(python_files)} Python files.")

def create_init_files(src_dir: Path):
    """Create __init__.py files in all subdirectories"""
    subdirs = [d for d in src_dir.rglob("*") if d.is_dir()]
    
    for subdir in subdirs:
        init_file = subdir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created: {init_file}")

if __name__ == "__main__":
    # Get the project root directory
    project_root = Path.cwd()
    src_dir = project_root / "src"
    
    if not src_dir.exists():
        print("Error: 'src' directory not found. Make sure you're running this from the project root.")
        exit(1)
    
    print("Fixing import statements in Enhanced Soldier Report System...")
    print(f"Project root: {project_root}")
    print(f"Source directory: {src_dir}")
    
    # Create __init__.py files
    print("\nCreating __init__.py files...")
    create_init_files(src_dir)
    
    # Fix imports
    print("\nFixing import statements...")
    fix_all_imports(src_dir)
    
    print("\nDone! You should now be able to run:")
    print("python -m src.main")
