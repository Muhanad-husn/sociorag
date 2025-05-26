"""
Script to update the graph.py module with the fixed version.
This will make the fix permanent in the main codebase.
"""

import shutil
import os
from pathlib import Path

def update_graph_module():
    # Get paths
    current_dir = Path(__file__).resolve().parent
    original_path = current_dir / "backend" / "app" / "retriever" / "graph.py"
    fixed_path = current_dir / "backend" / "app" / "retriever" / "graph_fixed.py"
    backup_path = current_dir / "backend" / "app" / "retriever" / "graph.py.bak"
    
    # Check if paths exist
    if not fixed_path.exists():
        print(f"Error: Fixed file {fixed_path} does not exist.")
        return False
    
    if not original_path.exists():
        print(f"Error: Original file {original_path} does not exist.")
        return False
    
    try:
        # Create backup of original file
        print(f"Creating backup of original file at {backup_path}")
        shutil.copy2(original_path, backup_path)
        
        # Replace original with fixed version
        print(f"Replacing {original_path} with {fixed_path}")
        shutil.copy2(fixed_path, original_path)
        
        print("Successfully updated graph.py with the fixed version.")
        return True
    except Exception as e:
        print(f"Error updating files: {e}")
        return False

if __name__ == "__main__":
    success = update_graph_module()
    print(f"Update {'completed successfully' if success else 'failed'}.")
