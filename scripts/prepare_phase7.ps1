# Script to prepare for Phase 7 by addressing Phase 6 housekeeping items
# Created on May 26, 2025

# Create sample PDF for testing
$sampleDir = "../input"
$samplePath = "../input/climate_article.pdf"

# Check if sample PDF exists, if not create it
if (-Not (Test-Path $samplePath)) {
    Write-Host "Creating sample PDF for API testing..."
    
    # Make sure the input directory exists
    if (-Not (Test-Path $sampleDir)) {
        New-Item -Path $sampleDir -ItemType Directory -Force | Out-Null
    }
    
    # Run the sample PDF creation script
    python create_sample_pdf.py
    
    if (Test-Path $samplePath) {
        Write-Host "Sample PDF created successfully at $samplePath"
    } else {
        Write-Host "Error: Failed to create sample PDF"
    }
} else {
    Write-Host "Sample PDF already exists at $samplePath"
}

# Run all API tests with the sample PDF
Write-Host "Running all API endpoint tests..."
python test_phase6_api.py all

Write-Host "Phase 6 housekeeping complete - Ready for Phase 7!"
