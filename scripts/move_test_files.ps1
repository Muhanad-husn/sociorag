# Script to move test files from root directory to organized test directory structure
# Created: May 26, 2025

# Test files to move
$testFiles = @(
    "test_embedding_cache.py",
    "test_embedding_singleton_integration.py",
    "test_embedding.py",
    "test_enhanced_reranking.py", 
    "test_enhanced_vector_utils.py",
    "test_similarity_functions.py",
    "test_sqlite_vec_utils.py"
)

# Target directory
$targetDir = ".\tests\retriever"

# Ensure target directory exists
if (-not (Test-Path $targetDir)) {
    New-Item -Path $targetDir -ItemType Directory -Force | Out-Null
    Write-Host "Created directory: $targetDir"
}

# Process each test file
foreach ($file in $testFiles) {
    $sourceFile = ".\$file"
    $targetFile = "$targetDir\$file"
    
    if (Test-Path $sourceFile) {
        # Read file content
        $content = Get-Content -Path $sourceFile -Raw
        
        # Update path in comments if needed
        $content = $content -replace "# filepath: d:\\sociorag\\$file", "# filepath: d:\\sociorag\\tests\\retriever\\$file"
        
        # Update imports if needed (this pattern keeps the imports working from the new location)
        # The sys.path.append already has parent.parent which will still work from the new location
        
        # Write to new location
        Set-Content -Path $targetFile -Value $content
        Write-Host "Moved and updated: $file to $targetDir"
        
        # Remove original file (only after successful write)
        if (Test-Path $targetFile) {
            Remove-Item -Path $sourceFile
            Write-Host "Removed original: $sourceFile"
        }
    } else {
        Write-Host "Warning: Source file not found - $sourceFile"
    }
}

Write-Host "Test file reorganization complete!"
