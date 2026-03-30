# PowerShell helper for users on Windows without make installed
# Usage: .\run_dbt.ps1 build  OR  .\run_dbt.ps1 run --select bronze

$venvPython = Join-Path -Path $PSScriptRoot -ChildPath ".venv\Scripts\python.exe"
$remainingArgs = $args

if (-Not (Test-Path $venvPython)) {
    Write-Error "Virtual environment python not found at $venvPython. Run .\venv\Scripts\python.exe -m venv .venv then pip install -r requirements.txt"
    exit 1
}

& $venvPython -m dbt.cli.main @remainingArgs
