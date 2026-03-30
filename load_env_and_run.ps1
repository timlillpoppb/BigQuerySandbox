# Load environment variables from .env file
$envContent = Get-Content .env -Raw
$envLines = $envContent -split '\r?\n'

foreach ($line in $envLines) {
    if ($line -match '^([^#][^=]+)=(.*)$' -and $matches[1] -and $matches[2]) {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim())
    }
}

# Check if GITHUB_TOKEN is set
if (-not $env:GITHUB_TOKEN) {
    Write-Host 'ERROR: GITHUB_TOKEN not found in .env file'
    exit 1
}

# Run the Python script
& .\.venv\Scripts\python.exe scripts/pr_and_merge.py