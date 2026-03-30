@echo off
REM Load environment variables from .env file
for /f "tokens=*" %%i in (.env) do (
    for /f "tokens=1,2 delims==" %%a in ("%%i") do (
        if not "%%a"=="" if not "%%b"=="" (
            set "%%a=%%b"
        )
    )
)

REM Check if GITHUB_TOKEN is set
if "%GITHUB_TOKEN%"=="" (
    echo ERROR: GITHUB_TOKEN not found in .env file
    exit /b 1
)

REM Run the Python script
.\.venv\Scripts\python.exe scripts/pr_and_merge.py