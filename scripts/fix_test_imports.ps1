# Script to fix import paths in moved test files
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
    
    # Update sys.path.append to handle the new location (two directory levels deeper)
    $content = $content -replace "sys.path.append\(str\(Path\(__file__\)\.parent\.parent\)\)", "sys.path.append(str(Path(__file__).parent.parent.parent))"
    
    # Write updated content
    Set-Content -Path $filePath -Value $content
    Write-Host "Updated: $filePath"
}

Write-Host "Import paths fixed in all test files!"
