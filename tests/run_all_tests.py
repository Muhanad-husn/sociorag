#!/usr/bin/env python3
"""
Comprehensive test runner for SocioRAG test suite.
Runs all tests in the consolidated test structure.
"""

import asyncio
import sys
import subprocess
import time
from pathlib import Path


def run_command(command, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout.strip():
                print(f"Output:\n{result.stdout}")
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error output:\n{result.stderr}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏱️  {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False


def main():
    """Run the comprehensive test suite."""
    print("🚀 SocioRAG Comprehensive Test Runner")
    print("=" * 60)
    
    # Change to the project root directory
    project_root = Path(__file__).parent.parent
    original_cwd = Path.cwd()
    
    try:
        # Go to project root
        import os
        os.chdir(project_root)
        
        results = []
        
        # 1. Backend tests
        results.append(run_command(
            "python -m pytest tests/backend/ -v --tb=short",
            "Backend Tests"
        ))
        
        # 2. Retriever tests
        results.append(run_command(
            "python -m pytest tests/retriever/ -v --tb=short",
            "Retriever Tests"
        ))
        
        # 3. Ingest tests
        results.append(run_command(
            "python -m pytest tests/ingest/ -v --tb=short",
            "Ingest Tests"
        ))
        
        # 4. Core tests (root level)
        results.append(run_command(
            "python -m pytest tests/test_enhanced_entity_extraction.py -v --tb=short",
            "Enhanced Entity Extraction Tests"
        ))
        
        results.append(run_command(
            "python -m pytest tests/test_pdf_generation_workflow.py -v --tb=short",
            "PDF Generation Workflow Tests"
        ))
        
        # 5. Scripts tests
        results.append(run_command(
            "python -m pytest tests/scripts/ -v --tb=short",
            "Scripts Tests"
        ))
        
        # 6. Run enhanced entity extraction as standalone
        results.append(run_command(
            "python tests/test_enhanced_entity_extraction.py",
            "Enhanced Entity Extraction (Standalone)"
        ))
        
        # 7. Run scripts test as standalone
        results.append(run_command(
            "python tests/scripts/test_logging.py",
            "Enhanced Logging Test (Standalone)"
        ))
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print(f"{'='*60}")
        
        passed = sum(results)
        total = len(results)
        
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed. Check output above.")
            return 1
            
    finally:
        # Return to original directory
        os.chdir(original_cwd)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
