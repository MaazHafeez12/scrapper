"""Job filtering and validation utilities."""
from typing import List, Dict, Callable
import re


class JobFilter:
    """Filter jobs based on various criteria."""
    
    @staticmethod
    def filter_jobs(jobs: List[Dict], filters: Dict) -> List[Dict]:
        """Apply all filters to job list.
        
        Args:
            jobs: List of job dictionaries
            filters: Dictionary of filter criteria
            
        Returns:
            Filtered list of jobs
        """
        filtered = jobs
        
        # Remote filter
        if filters.get('remote', False):
            filtered = JobFilter.filter_remote(filtered)
            
        # Keywords filter
        if filters.get('keywords'):
            filtered = JobFilter.filter_keywords(filtered, filters['keywords'])
            
        # Location filter
        if filters.get('location') and not filters.get('remote'):
            filtered = JobFilter.filter_location(filtered, filters['location'])
            
        # Salary filter
        if filters.get('min_salary'):
            filtered = JobFilter.filter_salary(filtered, filters['min_salary'])
            
        # Exclude keywords
        if filters.get('exclude_keywords'):
            filtered = JobFilter.filter_exclude_keywords(filtered, filters['exclude_keywords'])
            
        # Company filter
        if filters.get('companies'):
            filtered = JobFilter.filter_companies(filtered, filters['companies'])
            
        return filtered
        
    @staticmethod
    def filter_remote(jobs: List[Dict]) -> List[Dict]:
        """Filter for remote jobs only.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            Jobs that are marked as remote
        """
        return [job for job in jobs if job.get('remote', False)]
        
    @staticmethod
    def filter_keywords(jobs: List[Dict], keywords: str) -> List[Dict]:
        """Filter jobs by keywords in title or description.
        
        Args:
            jobs: List of job dictionaries
            keywords: Keywords to search for (space or comma separated)
            
        Returns:
            Jobs matching keywords
        """
        keyword_list = [k.strip().lower() for k in re.split(r'[,\s]+', keywords)]
        
        filtered = []
        for job in jobs:
            text = f"{job.get('title', '')} {job.get('description', '')}".lower()
            if any(keyword in text for keyword in keyword_list):
                filtered.append(job)
                
        return filtered
        
    @staticmethod
    def filter_exclude_keywords(jobs: List[Dict], exclude_keywords: str) -> List[Dict]:
        """Exclude jobs with certain keywords.
        
        Args:
            jobs: List of job dictionaries
            exclude_keywords: Keywords to exclude (space or comma separated)
            
        Returns:
            Jobs not matching exclude keywords
        """
        exclude_list = [k.strip().lower() for k in re.split(r'[,\s]+', exclude_keywords)]
        
        filtered = []
        for job in jobs:
            text = f"{job.get('title', '')} {job.get('description', '')}".lower()
            if not any(keyword in text for keyword in exclude_list):
                filtered.append(job)
                
        return filtered
        
    @staticmethod
    def filter_location(jobs: List[Dict], location: str) -> List[Dict]:
        """Filter jobs by location.
        
        Args:
            jobs: List of job dictionaries
            location: Location to filter by
            
        Returns:
            Jobs in specified location
        """
        location_lower = location.lower()
        return [job for job in jobs 
                if location_lower in job.get('location', '').lower()]
        
    @staticmethod
    def filter_salary(jobs: List[Dict], min_salary: int) -> List[Dict]:
        """Filter jobs by minimum salary.
        
        Args:
            jobs: List of job dictionaries
            min_salary: Minimum salary (yearly)
            
        Returns:
            Jobs meeting salary requirement
        """
        filtered = []
        
        for job in jobs:
            salary_str = job.get('salary', '')
            if not salary_str:
                continue
                
            # Extract numbers from salary string
            numbers = re.findall(r'\d+[,\d]*', salary_str)
            if numbers:
                # Remove commas and convert to int
                salary_value = int(numbers[0].replace(',', ''))
                
                # Handle hourly rates (convert to yearly)
                if 'hour' in salary_str.lower():
                    salary_value = salary_value * 2080  # 40 hours * 52 weeks
                    
                if salary_value >= min_salary:
                    filtered.append(job)
                    
        return filtered
        
    @staticmethod
    def filter_companies(jobs: List[Dict], companies: List[str]) -> List[Dict]:
        """Filter jobs by company names.
        
        Args:
            jobs: List of job dictionaries
            companies: List of company names
            
        Returns:
            Jobs from specified companies
        """
        company_list = [c.strip().lower() for c in companies]
        return [job for job in jobs 
                if job.get('company', '').lower() in company_list]
        
    @staticmethod
    def deduplicate_jobs(jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on title and company.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            Deduplicated list of jobs
        """
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            key = (job.get('title', '').lower(), job.get('company', '').lower())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
                
        return unique_jobs
        
    @staticmethod
    def sort_jobs(jobs: List[Dict], sort_by: str = 'platform') -> List[Dict]:
        """Sort jobs by specified field.
        
        Args:
            jobs: List of job dictionaries
            sort_by: Field to sort by (platform, company, title, location)
            
        Returns:
            Sorted list of jobs
        """
        if sort_by in ['platform', 'company', 'title', 'location']:
            return sorted(jobs, key=lambda x: x.get(sort_by, '').lower())
        return jobs
