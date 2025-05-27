"""Script to fix import statements in the SocioGraph codebase.

This script finds all Python files in the backend directory and changes
import statements from 'app.' to 'backend.app.' to fix the import path issues.
"""

import os
import re
from pathlib import Path

def fix_imports(directory):
    """Fix import statements in all Python files in the given directory."""
    # Pattern to match imports from app.*
    app_import_pattern = re.compile(r'from\s+app\.')
    # Pattern to match imports from backend.app.*
    backend_app_import_pattern = re.compile(r'from\s+backend\.app\.')
    
    # List of all Python files modified
    modified_files = []
    
    # Walk through the directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # Read the file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if the file contains imports from app but not already from backend.app
                if app_import_pattern.search(content) and not backend_app_import_pattern.search(content):
                    # Replace 'from app.' with 'from backend.app.'
                    new_content = app_import_pattern.sub('from backend.app.', content)
                    
                    # Write the modified content back to the file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    modified_files.append(file_path)
                    print(f"Fixed imports in {file_path}")
    
    return modified_files

if __name__ == "__main__":
    # Path to the backend directory
    backend_dir = Path("d:/sociorag/backend")
    
    # Fix imports in all Python files
    modified_files = fix_imports(backend_dir)
    
    # Print summary
    print(f"\nFixed imports in {len(modified_files)} files.")
    print("The following files were modified:")
    for file in modified_files:
        print(f"  - {file}")
