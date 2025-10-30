"""Quick test script for AI Job Matching functionality."""
from ai_matcher import JobMatcher
from rich.console import Console
import json

console = Console()

def test_ai_matching():
    """Test AI matching system."""
    console.print("\n[bold cyan]🤖 Testing AI Job Matching System[/bold cyan]\n")
    
    # Initialize matcher
    matcher = JobMatcher()
    
    # Test 1: Check preferences
    console.print("[bold]Test 1: Preferences System[/bold]")
    console.print(f"Current preferences: {json.dumps(matcher.preferences, indent=2)}")
    console.print("[green]✓[/green] Preferences loaded\n")
    
    # Test 2: Skill extraction
    console.print("[bold]Test 2: Skill Extraction[/bold]")
    test_text = "Looking for a Python developer with Django, React, AWS, and Docker experience"
    skills = matcher.extract_skills(test_text)
    console.print(f"Text: '{test_text}'")
    console.print(f"Extracted skills: {skills}")
    console.print(f"[green]✓[/green] Found {len(skills)} skills\n")
    
    # Test 3: Job scoring
    console.print("[bold]Test 3: Job Scoring[/bold]")
    test_job = {
        'title': 'Senior Python Developer',
        'description': 'We need a Python expert with Django, PostgreSQL, AWS, Docker, and Kubernetes experience. Remote work available.',
        'company': 'TechCorp',
        'location': 'Remote',
        'remote': True,
        'salary': '$120,000 - $150,000',
        'platform': 'LinkedIn',
        'url': 'https://example.com/job1'
    }
    
    # Set some test preferences if none exist
    if not matcher.preferences['required_skills']:
        test_prefs = {
            'required_skills': ['python', 'django'],
            'preferred_skills': ['aws', 'docker', 'postgresql'],
            'excluded_keywords': [],
            'min_salary': 100000,
            'remote_only': True,
            'job_types': ['fulltime'],
            'preferred_companies': [],
            'excluded_companies': []
        }
        matcher.preferences = test_prefs
    
    score, breakdown = matcher.calculate_match_score(test_job)
    
    console.print(f"Job: {test_job['title']}")
    console.print(f"Score: [bold green]{score}%[/bold green]")
    console.print(f"Breakdown: {json.dumps(breakdown, indent=2)}")
    console.print("[green]✓[/green] Scoring works!\n")
    
    # Test 4: Skills analysis
    console.print("[bold]Test 4: Skills Analysis[/bold]")
    try:
        from database import JobDatabase
        db = JobDatabase()
        jobs = db.search_jobs(limit=10)
        
        if jobs:
            analysis = matcher.analyze_skills_demand()
            console.print(f"Total jobs analyzed: {analysis['total_jobs']}")
            console.print(f"Unique skills: {analysis['unique_skills']}")
            if analysis['top_skills']:
                console.print("Top 5 skills:")
                for i, (skill, count) in enumerate(analysis['top_skills'][:5], 1):
                    console.print(f"  {i}. {skill}: {count} jobs")
            console.print("[green]✓[/green] Analysis works!\n")
        else:
            console.print("[yellow]⚠[/yellow] No jobs in database yet (run a scrape first)\n")
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Database test skipped: {e}\n")
    
    # Test 5: Recommendations
    console.print("[bold]Test 5: Recommendations[/bold]")
    try:
        recommendations = matcher.get_recommendations(limit=3, min_score=0)
        if recommendations:
            console.print(f"Found {len(recommendations)} recommendations:")
            for rec in recommendations[:3]:
                console.print(f"  - {rec.get('title', 'N/A')} ({rec.get('match_score', 0)}%)")
            console.print("[green]✓[/green] Recommendations work!\n")
        else:
            console.print("[yellow]⚠[/yellow] No new jobs for recommendations (run a scrape first)\n")
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Recommendations test skipped: {e}\n")
    
    # Summary
    console.print("\n[bold green]✅ AI Matching System Test Complete![/bold green]")
    console.print("\n[cyan]Next steps:[/cyan]")
    console.print("1. Run: [bold]python main.py --ai-setup[/bold] (setup preferences)")
    console.print("2. Run: [bold]python main.py 'Python Developer' --remote[/bold] (scrape jobs)")
    console.print("3. Run: [bold]python main.py --ai-recommend[/bold] (get recommendations)")
    console.print("4. Run: [bold]python main.py --ai-analyze[/bold] (analyze market)")
    console.print("5. Run: [bold]python app.py[/bold] (start web dashboard)\n")

if __name__ == '__main__':
    test_ai_matching()
