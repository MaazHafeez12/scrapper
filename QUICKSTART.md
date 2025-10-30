# Quick Start Guide

## Installation

1. Install dependencies:
```powershell
pip install -r requirements.txt
```

## Quick Examples

### 1. Search for Remote Jobs
```powershell
python main.py --keywords "python developer" --remote
```

### 2. Search on Specific Platforms
```powershell
python main.py --keywords "data scientist" --platforms indeed remoteok
```

### 3. Search with Salary Filter
```powershell
python main.py --keywords "software engineer" --min-salary 100000 --remote
```

### 4. Search with Location
```powershell
python main.py --keywords "web developer" --location "New York"
```

### 5. Export to Multiple Formats
```powershell
python main.py --keywords "devops engineer" --output-format csv json excel --remote
```

### 6. Advanced Search with Multiple Filters
```powershell
python main.py --keywords "senior developer" --remote --job-type fulltime --min-salary 120000 --exclude "junior intern" --deduplicate --sort-by company
```

## Using Programmatically

Check `examples.py` for code examples:
```powershell
python examples.py
```

## Common Use Cases

### Find Remote Developer Jobs
```powershell
python main.py -k "developer" -r -p indeed linkedin remoteok -o csv
```

### Find High-Paying Jobs in Specific City
```powershell
python main.py -k "engineer" -l "San Francisco" --min-salary 150000 -o excel
```

### Find Contract Work
```powershell
python main.py -k "consultant" -t contract -p indeed linkedin -o json
```

### Find Entry-Level Positions
```powershell
python main.py -k "junior developer entry level" --max-pages 3 -o csv
```

## Tips

- Use `--remote` flag for work-from-home opportunities
- Combine multiple platforms for better coverage
- Use `--deduplicate` to remove duplicate listings
- Adjust `--max-pages` to control scraping depth (more pages = more results but slower)
- Results are saved in the `output/` folder with timestamps

## Troubleshooting

If you encounter issues:
1. Make sure Chrome browser is installed (needed for Selenium)
2. Check your internet connection
3. Try reducing `--max-pages` if it's timing out
4. Some platforms may block automated access - try different platforms
