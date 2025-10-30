"""Data storage and export utilities."""
import os
import json
import csv
from typing import List, Dict
from datetime import datetime
import pandas as pd
import config
from database import JobDatabase


class DataExporter:
    """Export job data to various formats."""
    
    def __init__(self, output_dir: str = config.OUTPUT_DIR):
        """Initialize exporter.
        
        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def export_to_csv(self, jobs: List[Dict], filename: str = None) -> str:
        """Export jobs to CSV file.
        
        Args:
            jobs: List of job dictionaries
            filename: Custom filename (optional)
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"jobs_{timestamp}.csv"
            
        filepath = os.path.join(self.output_dir, filename)
        
        if not jobs:
            print("No jobs to export")
            return filepath
            
        # Convert to DataFrame for easier CSV export
        df = pd.DataFrame(jobs)
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        print(f"Exported {len(jobs)} jobs to {filepath}")
        return filepath
        
    def export_to_json(self, jobs: List[Dict], filename: str = None) -> str:
        """Export jobs to JSON file.
        
        Args:
            jobs: List of job dictionaries
            filename: Custom filename (optional)
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"jobs_{timestamp}.json"
            
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
            
        print(f"Exported {len(jobs)} jobs to {filepath}")
        return filepath
        
    def export_to_excel(self, jobs: List[Dict], filename: str = None) -> str:
        """Export jobs to Excel file.
        
        Args:
            jobs: List of job dictionaries
            filename: Custom filename (optional)
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"jobs_{timestamp}.xlsx"
            
        filepath = os.path.join(self.output_dir, filename)
        
        if not jobs:
            print("No jobs to export")
            return filepath
            
        df = pd.DataFrame(jobs)
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        print(f"Exported {len(jobs)} jobs to {filepath}")
        return filepath
        
    def export_summary(self, jobs: List[Dict]) -> None:
        """Print summary statistics of scraped jobs.
        
        Args:
            jobs: List of job dictionaries
        """
        if not jobs:
            print("No jobs found")
            return
            
        print(f"\n{'='*60}")
        print(f"JOB SCRAPING SUMMARY")
        print(f"{'='*60}")
        print(f"Total jobs found: {len(jobs)}")
        
        # Count by platform
        platforms = {}
        for job in jobs:
            platform = job.get('platform', 'Unknown')
            platforms[platform] = platforms.get(platform, 0) + 1
            
        print(f"\nJobs by platform:")
        for platform, count in sorted(platforms.items()):
            print(f"  {platform}: {count}")
            
        # Count remote jobs
        remote_count = sum(1 for job in jobs if job.get('remote', False))
        print(f"\nRemote jobs: {remote_count} ({remote_count/len(jobs)*100:.1f}%)")
        
        # Top companies
        companies = {}
        for job in jobs:
            company = job.get('company', 'Unknown')
            if company:
                companies[company] = companies.get(company, 0) + 1
                
        if companies:
            print(f"\nTop 5 companies:")
            top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5]
            for company, count in top_companies:
                print(f"  {company}: {count}")
                
        print(f"{'='*60}\n")
        
    def display_jobs(self, jobs: List[Dict], limit: int = 10) -> None:
        """Display jobs in a formatted table.
        
        Args:
            jobs: List of job dictionaries
            limit: Maximum number of jobs to display
        """
        if not jobs:
            print("No jobs to display")
            return
            
        print(f"\nShowing first {min(limit, len(jobs))} of {len(jobs)} jobs:\n")
        
        for i, job in enumerate(jobs[:limit], 1):
            print(f"{i}. {job.get('title', 'N/A')}")
            print(f"   Company: {job.get('company', 'N/A')}")
            print(f"   Location: {job.get('location', 'N/A')}")
            if job.get('salary'):
                print(f"   Salary: {job.get('salary')}")
            print(f"   Remote: {'Yes' if job.get('remote') else 'No'}")
            print(f"   Platform: {job.get('platform', 'N/A')}")
            print(f"   URL: {job.get('url', 'N/A')}")
            print()
    
    def export_database_to_file(self, format: str = 'csv', filename: str = None, filters: Dict = None) -> str:
        """Export all jobs from database to file.
        
        Args:
            format: Export format ('csv', 'json', 'excel')
            filename: Optional custom filename
            filters: Optional dictionary of filters to apply
            
        Returns:
            Path to saved file
        """
        db = JobDatabase()
        
        # Get jobs from database
        if filters:
            jobs = db.search_jobs(
                keywords=filters.get('keywords'),
                remote_only=filters.get('remote', False),
                platform=filters.get('platform'),
                status=filters.get('status')
            )
        else:
            # Get all jobs from database
            with db:
                cursor = db.conn.cursor()
                cursor.execute("""
                    SELECT title, company, location, description, salary, 
                           url, platform, remote, posted_date, scraped_at, status
                    FROM jobs
                    ORDER BY scraped_at DESC
                """)
                rows = cursor.fetchall()
                jobs = [dict(row) for row in rows]
        
        if not jobs:
            print("No jobs found in database")
            return None
        
        # Export based on format
        if format == 'csv':
            return self.export_to_csv(jobs, filename)
        elif format == 'json':
            return self.export_to_json(jobs, filename)
        elif format == 'excel':
            return self.export_to_excel(jobs, filename)
        else:
            print(f"Unknown format: {format}")
            return None
