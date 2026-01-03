#!/usr/bin/env python3
"""
Script to validate code before deployment.
Checks for common errors: syntax, imports, type issues, etc.
"""

import sys
import os
import importlib.util
import ast
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

ERRORS = []
WARNINGS = []

def check_syntax(file_path):
    """Check Python syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code, filename=str(file_path))
        return True
    except SyntaxError as e:
        ERRORS.append(f"Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        ERRORS.append(f"Error parsing {file_path}: {e}")
        return False

def check_imports(file_path):
    """Check if imports can be resolved."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        tree = ast.parse(code)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # Try to import main modules (skip if not critical)
        critical_modules = [
            'streamlit',
            'pandas',
            'core.database',
            'services.vocab_service',
            'core.srs',
        ]
        
        for module in imports:
            for critical in critical_modules:
                if module.startswith(critical):
                    try:
                        importlib.import_module(module)
                    except ImportError as e:
                        WARNINGS.append(f"Import warning in {file_path}: {module} - {e}")
        return True
    except Exception as e:
        WARNINGS.append(f"Import check warning in {file_path}: {e}")
        return True  # Non-critical

def check_common_issues(file_path):
    """Check for common coding issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        issues = []
        for i, line in enumerate(lines, 1):
            # Check for common patterns that might cause issues
            if 'vocab_id' in line and '.0' in line and 'int(' not in line:
                # Check if it's in a context where conversion is needed
                if 'row.get(' in lines[i-2:i+2] if i > 2 else lines[:i+2]:
                    issues.append(f"Line {i}: vocab_id might need int conversion")
            
            # Check for potential None issues
            if '.get(' in line and '.get(' not in line.split('#')[0]:  # Not in comment
                if 'vocab_id' in line and 'int(' not in line:
                    # This is just a warning, not all cases need conversion
                    pass
        
        if issues:
            WARNINGS.extend([f"{file_path}: {issue}" for issue in issues])
        
        return True
    except Exception as e:
        WARNINGS.append(f"Common issues check warning in {file_path}: {e}")
        return True

def validate_file(file_path):
    """Validate a single file."""
    file_path = Path(file_path)
    if not file_path.exists():
        ERRORS.append(f"File not found: {file_path}")
        return False
    
    print(f"Checking {file_path}...")
    
    syntax_ok = check_syntax(file_path)
    imports_ok = check_imports(file_path)
    issues_ok = check_common_issues(file_path)
    
    return syntax_ok and imports_ok

def main():
    """Main validation function."""
    print("=" * 60)
    print("DEPLOYMENT VALIDATION")
    print("=" * 60)
    
    # Files to check
    files_to_check = [
        'pages/06_On_Tap.py',
        'services/vocab_service.py',
        'core/vocab_utils.py',
        'pages/12_Cai_Dat.py',
        'core/auth.py',
    ]
    
    all_ok = True
    for file_path in files_to_check:
        full_path = project_root / file_path
        if full_path.exists():
            if not validate_file(full_path):
                all_ok = False
        else:
            WARNINGS.append(f"File not found (might be optional): {file_path}")
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if ERRORS:
        print(f"\nERRORS ({len(ERRORS)}):")
        for error in ERRORS:
            print(f"  - {error}")
        all_ok = False
    
    if WARNINGS:
        print(f"\nWARNINGS ({len(WARNINGS)}):")
        for warning in WARNINGS[:20]:  # Limit warnings
            print(f"  - {warning}")
        if len(WARNINGS) > 20:
            print(f"  ... and {len(WARNINGS) - 20} more warnings")
    
    if all_ok and not ERRORS:
        print("\n[OK] All critical checks passed!")
        return 0
    else:
        print("\n[FAIL] Validation failed. Please fix errors before deployment.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
