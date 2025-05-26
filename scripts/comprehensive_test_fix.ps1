# Script to comprehensively fix test files in the new location
# Created: May 26, 2025

# Target directory
$targetDir = ".\tests\retriever"

# Get all test files
$testFiles = Get-ChildItem -Path $targetDir -Filter "test_*.py"

# Process each test file
foreach ($file in $testFiles) {
    $filePath = $file.FullName
    Write-Host "Processing: $filePath"
    
    # Read file content
    $content = Get-Content -Path $filePath -Raw
    
    # Replace import style with absolute imports using the project root
    if ($content -match "import sys\s+import time\s+from pathlib import Path") {
        # This is the standard pattern with sys.path.append
        $newImportBlock = @"
import sys
import time
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

"@
        $content = $content -replace "import sys\s+import time\s+from pathlib import Path\s+# Add the parent directory to the path so we can import the app modules\s+sys\.path\.append\(str\(Path\(__file__\)\.parent\.parent\.parent\)\)", $newImportBlock
    }
    elseif ($content -match "import sys\s+import traceback") {
        # This is the pattern in test_embedding.py
        $newImportBlock = @"
import sys
import traceback
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

try:
"@
        $content = $content -replace "import sys\s+import traceback\s+try:", $newImportBlock
    }
    elseif ($content -match "import sys\s+from pathlib import Path") {
        # Another possible pattern
        $newImportBlock = @"
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

"@
        $content = $content -replace "import sys\s+from pathlib import Path\s+# Add the parent directory to the path so we can import the app modules\s+sys\.path\.append\(str\(Path\(__file__\)\.parent\.parent\.parent\)\)", $newImportBlock
    }
    
    # Write updated content
    Set-Content -Path $filePath -Value $content
    Write-Host "Updated: $filePath"
}

# Create a conftest.py file to help with pytest discovery
$conftestPath = Join-Path $targetDir "conftest.py"
$conftestContent = @"
# filepath: d:\sociorag\tests\retriever\conftest.py
"""
Configuration for pytest in the retriever tests directory.
Helps with module import paths and test discovery.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
"@

Set-Content -Path $conftestPath -Value $conftestContent
Write-Host "Created conftest.py for test discovery"

# Create a __main__.py file to allow running tests as a module
$mainPath = Join-Path $targetDir "__main__.py"
$mainContent = @"
# filepath: d:\sociorag\tests\retriever\__main__.py
"""
Main entry point for running retriever tests as a module.
Example: python -m tests.retriever
"""

import sys
import os
import unittest
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

if __name__ == "__main__":
    import pytest
    # Run all tests in this directory
    pytest.main(["-v", str(Path(__file__).parent)])
"@

Set-Content -Path $mainPath -Value $mainContent
Write-Host "Created __main__.py for running tests as a module"

Write-Host "Tests fixed comprehensively!"
