"""Example usage of the job scraper."""
from scrapers import IndeedScraper, RemoteOKScraper
from filters import JobFilter
from export import DataExporter


def example_basic_search():
    """Example: Basic job search."""
    print("Example 1: Basic search for Python jobs on Indeed")
    print("=" * 60)
    
    scraper = IndeedScraper()
    filters = {
        'keywords': 'python developer',
        'location': 'New York',
        'max_pages': 2
    }
    
    jobs = scraper.scrape_jobs(filters)
    print(f"Found {len(jobs)} jobs")
    
    # Export to CSV
    exporter = DataExporter()
    exporter.export_to_csv(jobs, 'python_jobs_example.csv')
    exporter.display_jobs(jobs, limit=5)
    

def example_remote_jobs():
    """Example: Search for remote jobs."""
    print("\nExample 2: Remote JavaScript jobs")
    print("=" * 60)
    
    scraper = RemoteOKScraper()
    filters = {
        'keywords': 'javascript',
        'remote': True,
        'max_pages': 1
    }
    
    jobs = scraper.scrape_jobs(filters)
    print(f"Found {len(jobs)} remote jobs")
    
    exporter = DataExporter()
    exporter.display_jobs(jobs, limit=5)


def example_with_filtering():
    """Example: Search with advanced filtering."""
    print("\nExample 3: Advanced filtering")
    print("=" * 60)
    
    # Get jobs from multiple sources
    indeed = IndeedScraper()
    remote_ok = RemoteOKScraper()
    
    filters = {
        'keywords': 'software engineer',
        'max_pages': 1
    }
    
    jobs = []
    jobs.extend(indeed.scrape_jobs(filters))
    jobs.extend(remote_ok.scrape_jobs(filters))
    
    print(f"Total jobs before filtering: {len(jobs)}")
    
    # Apply filters
    job_filter = JobFilter()
    
    # Filter for remote jobs only
    remote_jobs = job_filter.filter_remote(jobs)
    print(f"Remote jobs: {len(remote_jobs)}")
    
    # Filter by keywords
    filtered = job_filter.filter_keywords(remote_jobs, 'senior')
    print(f"Senior positions: {len(filtered)}")
    
    # Remove duplicates
    unique_jobs = job_filter.deduplicate_jobs(filtered)
    print(f"After deduplication: {len(unique_jobs)}")
    
    # Export
    exporter = DataExporter()
    exporter.export_summary(unique_jobs)
    exporter.export_to_json(unique_jobs, 'filtered_jobs_example.json')


def example_multi_format_export():
    """Example: Export to multiple formats."""
    print("\nExample 4: Multi-format export")
    print("=" * 60)
    
    scraper = RemoteOKScraper()
    filters = {'keywords': 'data science', 'max_pages': 1}
    
    jobs = scraper.scrape_jobs(filters)
    
    if jobs:
        exporter = DataExporter()
        exporter.export_to_csv(jobs, 'data_science_jobs.csv')
        exporter.export_to_json(jobs, 'data_science_jobs.json')
        exporter.export_summary(jobs)


if __name__ == '__main__':
    # Run examples
    # Uncomment the ones you want to try
    
    # example_basic_search()
    # example_remote_jobs()
    # example_with_filtering()
    example_multi_format_export()
    
    print("\nExamples completed!")
    print("Check the 'output' folder for exported files.")
