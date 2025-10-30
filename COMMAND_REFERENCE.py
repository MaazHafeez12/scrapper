"""
Visual Command Reference - Job Scraper Tool
============================================

BASIC SYNTAX
------------
python main.py [OPTIONS]

COMMON OPTIONS
--------------
--keywords, -k     "search terms"        What job to search for
--location, -l     "city/state"          Where to search
--remote, -r                             Remote jobs only
--platforms, -p    platform1 platform2   Which sites to search
--output-format    csv json excel        Export formats

VISUAL EXAMPLES
===============

Example 1: Remote Developer Jobs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─ Command ──────────────────────────────────────┐
│ python main.py \                               │
│   --keywords "python developer" \              │
│   --remote                                     │
└────────────────────────────────────────────────┘
┌─ What it does ─────────────────────────────────┐
│ ✓ Searches ALL platforms                       │
│ ✓ Filters for remote jobs only                 │
│ ✓ Keywords: "python developer"                 │
│ ✓ Exports to CSV (default)                     │
└────────────────────────────────────────────────┘

Example 2: Specific Platforms + Location
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─ Command ──────────────────────────────────────┐
│ python main.py \                               │
│   --keywords "data scientist" \                │
│   --location "San Francisco" \                 │
│   --platforms indeed linkedin                  │
└────────────────────────────────────────────────┘
┌─ What it does ─────────────────────────────────┐
│ ✓ Searches Indeed & LinkedIn only              │
│ ✓ Jobs in San Francisco area                   │
│ ✓ Keywords: "data scientist"                   │
└────────────────────────────────────────────────┘

Example 3: High-Paying Remote Jobs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─ Command ──────────────────────────────────────┐
│ python main.py \                               │
│   --keywords "senior engineer" \               │
│   --remote \                                   │
│   --min-salary 120000 \                        │
│   --job-type fulltime                          │
└────────────────────────────────────────────────┘
┌─ What it does ─────────────────────────────────┐
│ ✓ Remote jobs only                             │
│ ✓ Full-time positions                          │
│ ✓ Minimum $120,000 salary                      │
│ ✓ Senior engineer positions                    │
└────────────────────────────────────────────────┘

Example 4: Multi-Format Export
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─ Command ──────────────────────────────────────┐
│ python main.py \                               │
│   --keywords "devops" \                        │
│   --remote \                                   │
│   --output-format csv json excel               │
└────────────────────────────────────────────────┘
┌─ What it does ─────────────────────────────────┐
│ ✓ Exports to 3 formats simultaneously          │
│ ✓ CSV for Excel                                │
│ ✓ JSON for databases                           │
│ ✓ XLSX for sharing                             │
└────────────────────────────────────────────────┘

Example 5: Advanced Filtering
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─ Command ──────────────────────────────────────┐
│ python main.py \                               │
│   --keywords "developer" \                     │
│   --remote \                                   │
│   --exclude "junior intern" \                  │
│   --deduplicate \                              │
│   --sort-by company \                          │
│   --max-pages 3                                │
└────────────────────────────────────────────────┘
┌─ What it does ─────────────────────────────────┐
│ ✓ Excludes junior/intern positions             │
│ ✓ Removes duplicate listings                   │
│ ✓ Sorts by company name                        │
│ ✓ Scrapes 3 pages per platform                 │
└────────────────────────────────────────────────┘

ALL AVAILABLE PLATFORMS
=======================
┌──────────────────┬─────────────────────────────┐
│ Platform         │ Best For                    │
├──────────────────┼─────────────────────────────┤
│ indeed           │ Large volume, all types     │
│ linkedin         │ Professional networking     │
│ glassdoor        │ Company reviews + salaries  │
│ remoteok         │ 100% remote tech jobs       │
│ weworkremotely   │ Remote work focused         │
└──────────────────┴─────────────────────────────┘

JOB TYPES
=========
┌──────────────┬──────────────────────────────┐
│ Type         │ Usage                        │
├──────────────┼──────────────────────────────┤
│ fulltime     │ --job-type fulltime          │
│ parttime     │ --job-type parttime          │
│ contract     │ --job-type contract          │
│ internship   │ --job-type internship        │
└──────────────┴──────────────────────────────┘

OUTPUT FORMATS
==============
┌────────┬─────────────────────────────────┐
│ Format │ File Extension                  │
├────────┼─────────────────────────────────┤
│ csv    │ .csv (Excel compatible)         │
│ json   │ .json (for APIs)                │
│ excel  │ .xlsx (Excel native)            │
└────────┴─────────────────────────────────┘

WORKFLOW DIAGRAM
================

   ┌─────────────┐
   │  Run Search │
   └──────┬──────┘
          │
   ┌──────▼────────────────────────┐
   │ Scrape Selected Platforms     │
   │ • Indeed                      │
   │ • LinkedIn                    │
   │ • RemoteOK                    │
   │ • etc.                        │
   └──────┬────────────────────────┘
          │
   ┌──────▼────────────────────────┐
   │ Apply Filters                 │
   │ • Remote                      │
   │ • Salary                      │
   │ • Keywords                    │
   │ • Location                    │
   └──────┬────────────────────────┘
          │
   ┌──────▼────────────────────────┐
   │ Process Results               │
   │ • Deduplicate                 │
   │ • Sort                        │
   │ • Generate summary            │
   └──────┬────────────────────────┘
          │
   ┌──────▼────────────────────────┐
   │ Export to Files               │
   │ • output/jobs_DATE.csv        │
   │ • output/jobs_DATE.json       │
   │ • output/jobs_DATE.xlsx       │
   └───────────────────────────────┘

QUICK REFERENCE CHEAT SHEET
============================

Search Term           Command
─────────────────────────────────────────────
Remote Python         python main.py -k "python" -r
Data Science NYC      python main.py -k "data science" -l "New York"
High Salary           python main.py -k "engineer" --min-salary 100000
Indeed Only           python main.py -k "developer" -p indeed
Multiple Platforms    python main.py -k "web dev" -p indeed linkedin
No Juniors           python main.py -k "dev" -e "junior entry"
Full Time Only       python main.py -k "engineer" -t fulltime
Export All Formats   python main.py -k "devops" -o csv json excel
Fast Test            python main.py -k "remote" -r -p remoteok --max-pages 1

INTERACTIVE MODE (Windows)
===========================

Double-click run.bat for interactive mode:

1. Script asks for keywords
2. Script asks if remote only
3. Script asks for location (optional)
4. Automatically runs search
5. Opens results folder

GET HELP
========

In terminal, run:
   python main.py --help

View all options and examples!

"""

if __name__ == "__main__":
    print(__doc__)
