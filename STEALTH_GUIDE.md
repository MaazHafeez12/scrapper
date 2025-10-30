# Stealth Mode (Anti-Bot) Guide

This project supports multiple anti-bot strategies to improve scraping reliability on hostile sites like Glassdoor and LinkedIn.

## Quick start

1) Configure stealth in your `.env` (or override in `config.py`):

```
# Enable stealth features
USE_STEALTH=True

# Choose backend:
# - undetected: Selenium with undetected-chromedriver (best when supported)
# - playwright: Playwright + playwright-stealth (great modern alternative)
STEALTH_BACKEND=undetected

# Optional proxy (residential/mobile recommended for tough sites)
# Example: http://user:pass@host:port
PROXY_URL=

# Optional: explicit Chrome/Chromium path
BROWSER_BINARY=
```

2) For Playwright users, ensure browsers are installed once:

```
python -m playwright install chromium
```

## How it works

- Selenium path:
  - If `USE_STEALTH=True` and `STEALTH_BACKEND=undetected`, the framework tries to launch the browser using `undetected-chromedriver`.
  - If that fails (e.g., incompatibility on certain Python versions), it falls back to standard ChromeDriver with anti-detection tweaks (user-agent override, webdriver flag removal, headless=new, etc.).
  - Proxy settings are applied to both HTTP requests and the browser when set.

- Playwright path:
  - If `STEALTH_BACKEND=playwright`, the Playwright engine applies `playwright-stealth` to reduce detection signals, in addition to built-in evasions (navigator.webdriver removal, etc.).
  - Proxy is applied at browser launch when configured.

## Notes for Windows + Python 3.12/3.13/3.14

- Some versions of `undetected-chromedriver` import `distutils`, which was removed from Python 3.12+. If you see a message like:
  
  `undetected-chromedriver failed: No module named 'distutils'`
  
  the scraper will automatically fall back to the standard ChromeDriver with stealth tweaks. To maximize stealth in this environment, consider setting `STEALTH_BACKEND=playwright`.

## Tips for tough platforms (e.g., Glassdoor)

- Use a reputable residential proxy (set `PROXY_URL`).
- Run headful (set `HEADLESS_MODE=False`) temporarily for debugging.
- Slow down slightly (increase `REQUEST_DELAY`).
- Try Playwright stealth if Selenium is still blocked.

## Troubleshooting

- Browser fails to start:
  - Ensure Google Chrome/Chromium is installed, or set `BROWSER_BINARY` to a valid path.
  - On Playwright, run `python -m playwright install chromium` once.

- Still getting blocked:
  - Try a proxy and switch to `STEALTH_BACKEND=playwright`.
  - Reduce page concurrency and add small random delays.

If you want me to switch Glassdoor to a Playwright-based scraper next, say the word and I’ll add it as a fallback when Selenium returns 0 jobs.
