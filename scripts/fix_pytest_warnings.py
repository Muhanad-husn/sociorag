"""
Fix pytest warnings about returning values from test functions.

This script analyzes the test files in the retriever folder and fixes 
test functions that return values instead of using assertions.
"""

import os
import re
from pathlib import Path

def find_test_files(test_dir):
    """Find all test files in the directory."""
    return list(Path(test_dir).glob("test_*.py"))

def fix_test_function(content):
    """Fix test functions that return values instead of using assertions."""
    # Pattern to find test functions that return values
    pattern = re.compile(r'def\s+(test_\w+).*?:(.*?)return\s+(.*?)\n', re.DOTALL)
    
    # Replace returns with assertions where appropriate
    def replace_return(match):
        func_name = match.group(1)
        func_body = match.group(2)
        return_value = match.group(3)
        
        # Check if the function already has assertions
        has_assertions = "assert" in func_body
        
        # Add a comment about not returning values
        new_body = func_body
        if return_value.strip():
            new_body += f"    # Assert that we got valid results\n"
            if not has_assertions:
                new_body += f"    assert {return_value.strip()} is not None, \"Result should not be None\"\n"
            new_body += f"    # No need to return values in pytest functions\n"
        
        return f"def {func_name}():{new_body}"
    
    # Apply the fix
    fixed_content = pattern.sub(replace_return, content)
    return fixed_content

def process_test_file(file_path):
    """Process a test file to fix pytest warnings."""
    print(f"Processing {file_path}")
    
    # Read the content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the content
    fixed_content = fix_test_function(content)
    
    # Only write if changes were made
    if fixed_content != content:
        print(f"  - Fixed test functions in {file_path.name}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
    else:
        print(f"  - No changes needed for {file_path.name}")

def main():
    """Main function."""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    test_dir = project_root / "tests" / "retriever"
    
    print(f"Looking for test files in {test_dir}")
    test_files = find_test_files(test_dir)
    print(f"Found {len(test_files)} test files")
    
    for file_path in test_files:
        process_test_file(file_path)
    
    print("Done!")

if __name__ == "__main__":
    main()
