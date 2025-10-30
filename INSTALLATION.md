# Installation & Setup Guide

## Prerequisites

### 1. Install Python
- Download Python 3.8 or higher from [python.org](https://www.python.org/downloads/)
- During installation, **check the box** "Add Python to PATH"
- Verify installation:
  ```powershell
  python --version
  ```

### 2. Install Google Chrome
- Download from [google.com/chrome](https://www.google.com/chrome/)
- Required for Selenium web scraping

## Installation Steps

### Option 1: Automatic Setup (Windows)

1. Double-click `run.bat`
2. The script will:
   - Create a virtual environment
   - Install all dependencies
   - Launch interactive mode

### Option 2: Manual Setup

1. **Open PowerShell or Command Prompt** in the project directory

2. **Create virtual environment** (recommended):
   ```powershell
   python -m venv venv
   ```

3. **Activate virtual environment**:
   
   Windows (PowerShell):
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   
   Windows (CMD):
   ```cmd
   venv\Scripts\activate.bat
   ```
   
   Linux/Mac:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

5. **(Optional) Configure settings**:
   ```powershell
   copy .env.example .env
   notepad .env
   ```

## First Run

### Quick Test
```powershell
python main.py --keywords "remote developer" --remote --max-pages 1 --platforms remoteok
```

This will:
- Search RemoteOK for "remote developer" jobs
- Scrape 1 page only (fast test)
- Save results to `output/` folder

### View Results
```powershell
# List output files
dir output

# Open CSV in Excel or default program
start output\jobs_*.csv
```

## Common Issues & Solutions

### Issue 1: Python not found
**Solution**: 
- Reinstall Python and check "Add to PATH"
- Or use full path: `C:\Python311\python.exe`

### Issue 2: pip not found
**Solution**:
```powershell
python -m pip install --upgrade pip
```

### Issue 3: ChromeDriver errors
**Solution**:
- Ensure Chrome browser is installed
- Update Chrome to latest version
- The script will auto-download compatible ChromeDriver

### Issue 4: "Permission Denied" on PowerShell
**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue 5: Module not found errors
**Solution**:
```powershell
# Ensure virtual environment is activated
pip install -r requirements.txt --force-reinstall
```

### Issue 6: No results found
**Solutions**:
- Try broader keywords
- Use RemoteOK platform for testing (most reliable)
- Check internet connection
- Some platforms block automated access

## Usage Examples

### Example 1: Find Remote Python Jobs
```powershell
python main.py --keywords "python developer" --remote
```

### Example 2: Find Jobs in Specific City
```powershell
python main.py --keywords "software engineer" --location "New York"
```

### Example 3: Find High-Paying Jobs
```powershell
python main.py --keywords "senior developer" --min-salary 120000 --remote
```

### Example 4: Search Specific Platforms
```powershell
python main.py --keywords "data scientist" --platforms indeed remoteok
```

### Example 5: Export to Multiple Formats
```powershell
python main.py --keywords "web developer" --output-format csv json excel
```

## Testing the Scrapers

Run the examples file to test individual scrapers:
```powershell
python examples.py
```

## Directory Structure After Setup

```
Scrapper/
├── venv/                    # Virtual environment (created after setup)
├── output/                  # Results saved here
│   ├── jobs_YYYYMMDD_HHMMSS.csv
│   ├── jobs_YYYYMMDD_HHMMSS.json
│   └── jobs_YYYYMMDD_HHMMSS.xlsx
├── scrapers/               # Platform scrapers
├── main.py                 # Run this!
├── requirements.txt        # Dependencies
└── README.md              # Documentation
```

## Next Steps

1. ✅ Complete installation
2. ✅ Run test search
3. ✅ Check output folder for results
4. ✅ Read QUICKSTART.md for more examples
5. ✅ Customize searches for your needs

## Getting Help

- Check README.md for full documentation
- See QUICKSTART.md for command examples
- Run `python main.py --help` for all options
- Review examples.py for programmatic usage

## Performance Tips

- Start with `--max-pages 1` for testing
- Use `--platforms remoteok` (fastest platform)
- Enable `--deduplicate` to remove duplicates
- Use specific keywords for better results

Enjoy your job hunting! 🚀
