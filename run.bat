@echo off
REM Job Scraper - Quick Launch Script for Windows

echo ====================================
echo    Job Scraper Tool
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Check if dependencies are installed
if not exist "venv\" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    echo.
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies if needed
echo Checking dependencies...
pip install -q -r requirements.txt

echo.
echo ====================================
echo Ready to scrape jobs!
echo ====================================
echo.
echo Examples:
echo   1. Remote Python jobs:
echo      python main.py --keywords "python developer" --remote
echo.
echo   2. Data Scientist jobs in New York:
echo      python main.py --keywords "data scientist" --location "New York"
echo.
echo   3. High-paying remote engineering jobs:
echo      python main.py --keywords "software engineer" --remote --min-salary 100000
echo.
echo ====================================
echo.

REM Interactive mode
set /p keywords="Enter job keywords (e.g., python developer): "
set /p remote="Remote only? (y/n): "

if /i "%remote%"=="y" (
    python main.py --keywords "%keywords%" --remote --output-format csv json
) else (
    set /p location="Enter location (or press Enter to skip): "
    if "%location%"=="" (
        python main.py --keywords "%keywords%" --output-format csv json
    ) else (
        python main.py --keywords "%keywords%" --location "%location%" --output-format csv json
    )
)

echo.
echo ====================================
echo Scraping complete! Check the output folder for results.
echo ====================================
pause
