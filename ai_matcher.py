"""AI-powered job matching and recommendation system."""
import re
import json
from typing import List, Dict, Tuple
from collections import Counter
from datetime import datetime
from database import JobDatabase
from rich.console import Console
import os

console = Console()


class JobMatcher:
    """AI-powered job matching using skill extraction and scoring."""
    
    def __init__(self):
        """Initialize job matcher."""
        self.db = JobDatabase()
        self.preferences = self.load_preferences()
    
    def load_preferences(self) -> Dict:
        """Load user preferences from file.
        
        Returns:
            Dictionary of user preferences
        """
        prefs_file = 'preferences.json'
        
        if os.path.exists(prefs_file):
            with open(prefs_file, 'r') as f:
                return json.load(f)
        
        # Default preferences
        return {
            'required_skills': [],
            'preferred_skills': [],
            'excluded_keywords': [],
            'min_salary': None,
            'remote_only': False,
            'experience_years': None,
            'job_types': ['fulltime'],
            'preferred_companies': [],
            'excluded_companies': []
        }
    
    def save_preferences(self, preferences: Dict):
        """Save user preferences to file.
        
        Args:
            preferences: Dictionary of preferences
        """
        with open('preferences.json', 'w') as f:
            json.dump(preferences, f, indent=2)
        
        self.preferences = preferences
        console.print("[green]✓[/green] Preferences saved")
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from job text.
        
        Args:
            text: Job title, description, or other text
            
        Returns:
            List of extracted skills
        """
        if not text:
            return []
        
        text = text.lower()
        
        # Common tech skills
        skills = [
            # Programming languages
            'python', 'java', 'javascript', 'typescript', 'c\\+\\+', 'c#', 'go', 'rust',
            'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab',
            
            # Web technologies
            'react', 'angular', 'vue', 'node\\.js', 'express', 'django', 'flask',
            'spring', 'laravel', 'rails', 'asp\\.net', 'html', 'css', 'sass',
            
            # Databases
            'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            'cassandra', 'dynamodb', 'oracle', 'sqlite',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform',
            'ansible', 'ci/cd', 'git', 'linux', 'unix', 'bash',
            
            # Data Science & ML
            'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras',
            'scikit-learn', 'pandas', 'numpy', 'spark', 'hadoop', 'tableau',
            
            # Mobile
            'ios', 'android', 'react native', 'flutter', 'xamarin',
            
            # Other
            'rest', 'api', 'graphql', 'microservices', 'agile', 'scrum',
            'testing', 'tdd', 'security', 'blockchain', 'devops'
        ]
        
        found_skills = []
        for skill in skills:
            pattern = r'\b' + skill + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                found_skills.append(skill.replace('\\', ''))
        
        return list(set(found_skills))
    
    def calculate_match_score(self, job: Dict) -> Tuple[float, Dict]:
        """Calculate match score for a job based on preferences.
        
        Args:
            job: Job dictionary
            
        Returns:
            Tuple of (score, breakdown) where score is 0-100
        """
        score = 0
        max_score = 0
        breakdown = {}
        
        # Extract skills from job
        job_text = f"{job.get('title', '')} {job.get('description', '')}"
        job_skills = self.extract_skills(job_text)
        
        # 1. Required skills (40 points) - MUST HAVE
        if self.preferences['required_skills']:
            max_score += 40
            required_found = [s for s in self.preferences['required_skills'] 
                            if s.lower() in [js.lower() for js in job_skills]]
            
            if len(self.preferences['required_skills']) > 0:
                required_pct = len(required_found) / len(self.preferences['required_skills'])
                required_score = required_pct * 40
                score += required_score
                breakdown['required_skills'] = {
                    'score': round(required_score, 1),
                    'found': required_found,
                    'missing': [s for s in self.preferences['required_skills'] 
                              if s not in required_found]
                }
        
        # 2. Preferred skills (30 points) - NICE TO HAVE
        if self.preferences['preferred_skills']:
            max_score += 30
            preferred_found = [s for s in self.preferences['preferred_skills'] 
                             if s.lower() in [js.lower() for js in job_skills]]
            
            if len(self.preferences['preferred_skills']) > 0:
                preferred_pct = len(preferred_found) / len(self.preferences['preferred_skills'])
                preferred_score = preferred_pct * 30
                score += preferred_score
                breakdown['preferred_skills'] = {
                    'score': round(preferred_score, 1),
                    'found': preferred_found
                }
        
        # 3. Remote preference (15 points)
        max_score += 15
        if self.preferences['remote_only']:
            if job.get('remote'):
                score += 15
                breakdown['remote'] = {'score': 15, 'match': True}
            else:
                breakdown['remote'] = {'score': 0, 'match': False}
        else:
            score += 15  # No preference, give full points
            breakdown['remote'] = {'score': 15, 'match': 'no_preference'}
        
        # 4. Salary (10 points)
        max_score += 10
        if self.preferences['min_salary']:
            job_salary = self._extract_salary(job.get('salary', ''))
            if job_salary:
                if job_salary >= self.preferences['min_salary']:
                    score += 10
                    breakdown['salary'] = {'score': 10, 'meets_minimum': True}
                else:
                    breakdown['salary'] = {'score': 0, 'meets_minimum': False}
            else:
                score += 5  # No salary info, give partial points
                breakdown['salary'] = {'score': 5, 'no_info': True}
        else:
            score += 10  # No preference, give full points
            breakdown['salary'] = {'score': 10, 'no_preference': True}
        
        # 5. Company preference (5 points)
        max_score += 5
        company = job.get('company', '').lower()
        if self.preferences['preferred_companies']:
            if any(pc.lower() in company for pc in self.preferences['preferred_companies']):
                score += 5
                breakdown['company'] = {'score': 5, 'preferred': True}
            else:
                breakdown['company'] = {'score': 0, 'preferred': False}
        else:
            score += 5  # No preference, give full points
            breakdown['company'] = {'score': 5, 'no_preference': True}
        
        # 6. Excluded keywords penalty
        if self.preferences['excluded_keywords']:
            job_text_lower = job_text.lower()
            excluded_found = [k for k in self.preferences['excluded_keywords'] 
                            if k.lower() in job_text_lower]
            
            if excluded_found:
                penalty = len(excluded_found) * 10
                score = max(0, score - penalty)
                breakdown['excluded_keywords'] = {
                    'penalty': penalty,
                    'found': excluded_found
                }
        
        # 7. Excluded companies penalty
        if self.preferences['excluded_companies']:
            if any(ec.lower() in company for ec in self.preferences['excluded_companies']):
                score = 0  # Automatic disqualification
                breakdown['excluded_company'] = True
        
        # Normalize score to 0-100
        if max_score > 0:
            normalized_score = (score / max_score) * 100
        else:
            normalized_score = 50  # Default if no preferences
        
        return round(normalized_score, 1), breakdown
    
    def score_jobs(self, jobs: List[Dict] = None, min_score: float = 0) -> List[Dict]:
        """Score all jobs and return sorted by match score.
        
        Args:
            jobs: List of jobs to score (if None, gets from database)
            min_score: Minimum score threshold (0-100)
            
        Returns:
            List of jobs with scores, sorted by score descending
        """
        if jobs is None:
            jobs = self.db.search_jobs(limit=1000)
        
        scored_jobs = []
        
        for job in jobs:
            score, breakdown = self.calculate_match_score(job)
            
            if score >= min_score:
                job_copy = job.copy()
                job_copy['match_score'] = score
                job_copy['match_breakdown'] = breakdown
                scored_jobs.append(job_copy)
        
        # Sort by score descending
        scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        return scored_jobs
    
    def get_recommendations(self, limit: int = 10, min_score: float = 50) -> List[Dict]:
        """Get top job recommendations.
        
        Args:
            limit: Maximum number of recommendations
            min_score: Minimum score threshold
            
        Returns:
            List of top recommended jobs
        """
        # Get only new jobs
        new_jobs = self.db.get_new_jobs(since_hours=168)  # Last week
        
        if not new_jobs:
            console.print("[yellow]No new jobs to recommend[/yellow]")
            return []
        
        # Score and filter
        scored = self.score_jobs(new_jobs, min_score=min_score)
        
        return scored[:limit]
    
    def learn_from_feedback(self, job_url: str, liked: bool):
        """Learn from user feedback on jobs.
        
        Args:
            job_url: Job URL
            liked: Whether user liked the job (True) or not (False)
        """
        with self.db:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT title, description, company FROM jobs WHERE url = ?
            """, (job_url,))
            job = cursor.fetchone()
            
            if not job:
                console.print("[red]Job not found[/red]")
                return
            
            # Extract skills from liked/disliked job
            job_text = f"{job['title']} {job['description']}"
            skills = self.extract_skills(job_text)
            
            if liked:
                # Add skills to preferred if not already there
                for skill in skills:
                    if skill not in self.preferences['preferred_skills']:
                        if skill not in self.preferences['required_skills']:
                            self.preferences['preferred_skills'].append(skill)
                
                # Add company to preferred
                company = job['company']
                if company and company not in self.preferences['preferred_companies']:
                    self.preferences['preferred_companies'].append(company)
                
                console.print(f"[green]✓[/green] Learned from liked job: {skills}")
            else:
                # Add keywords to excluded
                # (Be conservative - don't auto-exclude skills)
                console.print(f"[yellow]✓[/yellow] Noted disliked job")
            
            # Save updated preferences
            self.save_preferences(self.preferences)
    
    def analyze_skills_demand(self) -> Dict:
        """Analyze which skills are most in-demand.
        
        Returns:
            Dictionary with skill statistics
        """
        jobs = self.db.search_jobs(limit=1000)
        
        all_skills = []
        for job in jobs:
            job_text = f"{job.get('title', '')} {job.get('description', '')}"
            skills = self.extract_skills(job_text)
            all_skills.extend(skills)
        
        skill_counts = Counter(all_skills)
        
        return {
            'total_jobs': len(jobs),
            'unique_skills': len(skill_counts),
            'top_skills': skill_counts.most_common(20),
            'all_skills': dict(skill_counts)
        }
    
    def suggest_skills_to_learn(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Suggest skills to learn based on job market demand.
        
        Args:
            top_n: Number of skills to suggest
            
        Returns:
            List of (skill, count) tuples
        """
        analysis = self.analyze_skills_demand()
        
        # Get skills you don't have
        your_skills = set(self.preferences['required_skills'] + 
                         self.preferences['preferred_skills'])
        
        suggestions = []
        for skill, count in analysis['top_skills']:
            if skill.lower() not in [s.lower() for s in your_skills]:
                suggestions.append((skill, count))
                if len(suggestions) >= top_n:
                    break
        
        return suggestions
    
    def _extract_salary(self, salary_text: str) -> int:
        """Extract numeric salary from text.
        
        Args:
            salary_text: Salary text (e.g., "$120K", "100000")
            
        Returns:
            Annual salary as integer, or None
        """
        if not salary_text:
            return None
        
        # Remove common formatting
        text = salary_text.lower().replace(',', '').replace('$', '')
        
        # Try to extract number
        numbers = re.findall(r'\d+', text)
        if not numbers:
            return None
        
        amount = int(numbers[0])
        
        # Handle K notation (e.g., "120K")
        if 'k' in text and amount < 1000:
            amount *= 1000
        
        # Handle hourly -> annual conversion
        if 'hour' in text or '/hr' in text:
            amount *= 2080  # Assume 40 hours/week
        
        return amount
    
    def display_recommendations(self, recommendations: List[Dict]):
        """Display recommendations with scores.
        
        Args:
            recommendations: List of scored jobs
        """
        if not recommendations:
            console.print("[yellow]No recommendations found[/yellow]")
            return
        
        console.print(f"\n[bold cyan]🎯 Top {len(recommendations)} Job Recommendations[/bold cyan]\n")
        
        for i, job in enumerate(recommendations, 1):
            score = job['match_score']
            
            # Color-code score
            if score >= 80:
                score_color = 'green'
                emoji = '🌟'
            elif score >= 60:
                score_color = 'yellow'
                emoji = '⭐'
            else:
                score_color = 'white'
                emoji = '✓'
            
            console.print(f"{emoji} [{score_color}]{score}%[/{score_color}] - {job.get('title', 'N/A')}")
            console.print(f"   Company: {job.get('company', 'N/A')}")
            console.print(f"   Location: {job.get('location', 'N/A')}")
            
            if job.get('salary'):
                console.print(f"   Salary: {job.get('salary')}")
            
            console.print(f"   Remote: {'Yes' if job.get('remote') else 'No'}")
            console.print(f"   Platform: {job.get('platform', 'N/A')}")
            console.print(f"   URL: {job.get('url', 'N/A')}")
            
            # Show breakdown
            breakdown = job.get('match_breakdown', {})
            if breakdown.get('required_skills'):
                req = breakdown['required_skills']
                if req.get('found'):
                    console.print(f"   ✓ Skills: {', '.join(req['found'])}")
                if req.get('missing'):
                    console.print(f"   ✗ Missing: {', '.join(req['missing'])}")
            
            console.print()


class PreferencesManager:
    """Manage user preferences for job matching."""
    
    def __init__(self):
        """Initialize preferences manager."""
        self.matcher = JobMatcher()
    
    def interactive_setup(self):
        """Interactive setup for preferences."""
        console.print("\n[bold cyan]🎯 AI Job Matching Setup[/bold cyan]\n")
        console.print("Let's set up your job preferences for AI matching.\n")
        
        prefs = {}
        
        # Required skills
        console.print("[bold]Required Skills[/bold] (must-have, comma-separated):")
        console.print("Examples: Python, JavaScript, React, AWS")
        required = input("Enter required skills: ").strip()
        prefs['required_skills'] = [s.strip() for s in required.split(',') if s.strip()]
        
        # Preferred skills
        console.print("\n[bold]Preferred Skills[/bold] (nice-to-have, comma-separated):")
        preferred = input("Enter preferred skills: ").strip()
        prefs['preferred_skills'] = [s.strip() for s in preferred.split(',') if s.strip()]
        
        # Remote preference
        console.print("\n[bold]Remote Work[/bold]")
        remote = input("Remote only? (y/n): ").strip().lower()
        prefs['remote_only'] = remote == 'y'
        
        # Minimum salary
        console.print("\n[bold]Minimum Salary[/bold] (annual, leave empty to skip)")
        salary = input("Enter minimum salary (e.g., 120000): ").strip()
        prefs['min_salary'] = int(salary) if salary.isdigit() else None
        
        # Excluded keywords
        console.print("\n[bold]Excluded Keywords[/bold] (comma-separated, leave empty to skip)")
        console.print("Examples: junior, intern, contract")
        excluded = input("Enter keywords to exclude: ").strip()
        prefs['excluded_keywords'] = [k.strip() for k in excluded.split(',') if k.strip()]
        
        # Job types
        prefs['job_types'] = ['fulltime']
        prefs['preferred_companies'] = []
        prefs['excluded_companies'] = []
        
        # Save
        self.matcher.save_preferences(prefs)
        
        console.print("\n[green]✓[/green] Preferences saved!")
        console.print("\nYou can now use: [cyan]python main.py --ai-recommend[/cyan]")


def main():
    """CLI for AI job matching."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Job Matching')
    parser.add_argument('--setup', action='store_true', help='Interactive preferences setup')
    parser.add_argument('--recommend', action='store_true', help='Get job recommendations')
    parser.add_argument('--analyze', action='store_true', help='Analyze skills demand')
    parser.add_argument('--suggest', action='store_true', help='Suggest skills to learn')
    parser.add_argument('--limit', type=int, default=10, help='Number of recommendations')
    parser.add_argument('--min-score', type=float, default=50, help='Minimum match score')
    
    args = parser.parse_args()
    
    if args.setup:
        pm = PreferencesManager()
        pm.interactive_setup()
    
    elif args.recommend:
        matcher = JobMatcher()
        recommendations = matcher.get_recommendations(limit=args.limit, min_score=args.min_score)
        matcher.display_recommendations(recommendations)
    
    elif args.analyze:
        matcher = JobMatcher()
        analysis = matcher.analyze_skills_demand()
        
        console.print("\n[bold cyan]📊 Skills Demand Analysis[/bold cyan]\n")
        console.print(f"Total jobs analyzed: {analysis['total_jobs']}")
        console.print(f"Unique skills found: {analysis['unique_skills']}\n")
        console.print("[bold]Top 20 Most In-Demand Skills:[/bold]\n")
        
        for i, (skill, count) in enumerate(analysis['top_skills'], 1):
            pct = (count / analysis['total_jobs']) * 100
            console.print(f"{i:2}. {skill:20} - {count:4} jobs ({pct:.1f}%)")
    
    elif args.suggest:
        matcher = JobMatcher()
        suggestions = matcher.suggest_skills_to_learn()
        
        console.print("\n[bold cyan]💡 Skills You Should Learn[/bold cyan]\n")
        
        if not suggestions:
            console.print("[yellow]No suggestions - you already have all top skills![/yellow]")
        else:
            console.print("Based on current job market demand:\n")
            for i, (skill, count) in enumerate(suggestions, 1):
                console.print(f"{i:2}. {skill:20} - Found in {count} jobs")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
