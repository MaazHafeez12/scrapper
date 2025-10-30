"""Main job scraper application."""
import argparse
from typing import List, Dict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import config
from scrapers import (
    IndeedScraper,
    LinkedInScraper,
    RemoteOKScraper,
    WeWorkRemotelyScraper,
    GlassdoorScraper,
    MonsterScraper,
    DiceScraper,
    SimplyHiredScraper,
    ZipRecruiterScraper,
    AngelListScraper,
)
from scrapers import GlassdoorPlaywrightScraper
from filters import JobFilter
from export import DataExporter
from database import JobDatabase
from notifications import NotificationManager
from ai_matcher import JobMatcher, PreferencesManager
from resume_parser import ResumeParser
from auto_apply import AutoApplier, ApplicationTemplate, setup_template_interactive
import os


console = Console()


class JobScraperApp:
    """Main application for scraping jobs from multiple platforms."""
    
    def __init__(self):
        """Initialize the job scraper application."""
        # Choose Glassdoor engine dynamically
        use_playwright_glassdoor = (
            (getattr(config, 'USE_STEALTH', True) and getattr(config, 'STEALTH_BACKEND', 'undetected') == 'playwright')
            or getattr(config, 'USE_PLAYWRIGHT', False)
        ) and (GlassdoorPlaywrightScraper is not None)

        glassdoor_engine = GlassdoorPlaywrightScraper() if use_playwright_glassdoor else GlassdoorScraper()

        self.scrapers = {
            'indeed': IndeedScraper(),
            'linkedin': LinkedInScraper(),
            'remoteok': RemoteOKScraper(),
            'weworkremotely': WeWorkRemotelyScraper(),
            'glassdoor': glassdoor_engine,
            'monster': MonsterScraper(),
            'dice': DiceScraper(),
            'simplyhired': SimplyHiredScraper(),
            'ziprecruiter': ZipRecruiterScraper(),
            'angellist': AngelListScraper()
        }
        self.exporter = DataExporter()
        self.filter = JobFilter()
        self.database = JobDatabase()
        self.notifier = NotificationManager()
        
    def scrape_all_platforms(self, filters: Dict, platforms: List[str] = None) -> List[Dict]:
        """Scrape jobs from all or specified platforms.
        
        Args:
            filters: Dictionary of search filters
            platforms: List of platform names to scrape (None = all)
            
        Returns:
            List of all scraped jobs
        """
        all_jobs = []
        
        if platforms is None:
            platforms = list(self.scrapers.keys())
            
        console.print(f"\n[bold cyan]Starting job scraper...[/bold cyan]")
        console.print(f"Platforms: {', '.join(platforms)}")
        console.print(f"Filters: {filters}\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for platform_name in platforms:
                if platform_name not in self.scrapers:
                    console.print(f"[yellow]Warning: Unknown platform '{platform_name}'[/yellow]")
                    continue
                    
                task = progress.add_task(f"Scraping {platform_name}...", total=None)
                
                try:
                    scraper = self.scrapers[platform_name]
                    jobs = scraper.scrape_jobs(filters)
                    all_jobs.extend(jobs)
                    progress.update(task, completed=True)
                    console.print(f"[green]✓[/green] {platform_name}: Found {len(jobs)} jobs")
                    
                except Exception as e:
                    progress.update(task, completed=True)
                    console.print(f"[red]✗[/red] {platform_name}: Error - {str(e)}")
                    
        return all_jobs
        
    def run(self, args):
        """Run the job scraper with provided arguments.
        
        Args:
            args: Parsed command line arguments
        """
        # Build filters dictionary
        filters = {
            'keywords': args.keywords,
            'location': args.location,
            'remote': args.remote,
            'job_type': args.job_type,
            'max_pages': args.max_pages,
        }
        
        # Scrape jobs
        jobs = self.scrape_all_platforms(filters, args.platforms)
        
        # Save to database and get new/updated counts
        new_jobs_list = []
        if args.use_database:
            console.print("\n[cyan]Saving jobs to database...[/cyan]")
            db_results = self.database.save_jobs(jobs)
            console.print(f"[green]✓[/green] New jobs: {db_results['new']}")
            console.print(f"[yellow]↻[/yellow] Updated jobs: {db_results['updated']}")
            
            # Save search history
            self.database.save_search_history(filters, db_results)
            
            # If show_new_only, filter to only new jobs
            if args.show_new_only:
                new_jobs = self.database.get_new_jobs(since_hours=args.new_since_hours)
                console.print(f"[cyan]Showing only {len(new_jobs)} new jobs from last {args.new_since_hours} hours[/cyan]")
                jobs = new_jobs
                new_jobs_list = new_jobs
            elif db_results['new'] > 0:
                # Get the newly added jobs for notifications
                new_jobs_list = self.database.get_new_jobs(since_hours=1)
        
        # Apply additional filters
        if args.min_salary:
            filters['min_salary'] = args.min_salary
            
        if args.exclude:
            filters['exclude_keywords'] = args.exclude
            
        filtered_jobs = self.filter.filter_jobs(jobs, filters)
        
        # Remove duplicates
        if args.deduplicate:
            filtered_jobs = self.filter.deduplicate_jobs(filtered_jobs)
            
        # Sort results
        if args.sort_by:
            filtered_jobs = self.filter.sort_jobs(filtered_jobs, args.sort_by)
            
        # Display results
        console.print(f"\n[bold green]Scraping complete![/bold green]")
        console.print(f"Total jobs found: {len(jobs)}")
        console.print(f"After filtering: {len(filtered_jobs)}\n")
        
        if filtered_jobs:
            # Show summary
            self.exporter.export_summary(filtered_jobs)
            
            # Display first few jobs
            if args.display:
                self.display_jobs_table(filtered_jobs, limit=args.display)
                
            # Export to file
            if args.output_format:
                if 'csv' in args.output_format:
                    self.exporter.export_to_csv(filtered_jobs)
                if 'json' in args.output_format:
                    self.exporter.export_to_json(filtered_jobs)
                if 'excel' in args.output_format:
                    self.exporter.export_to_excel(filtered_jobs)
        else:
            console.print("[yellow]No jobs found matching your criteria.[/yellow]")
            
    def display_jobs_table(self, jobs: List[Dict], limit: int = 10):
        """Display jobs in a rich table.
        
        Args:
            jobs: List of job dictionaries
            limit: Maximum number of jobs to display
        """
        table = Table(title=f"Top {min(limit, len(jobs))} Jobs")
        
        table.add_column("Title", style="cyan", no_wrap=False, max_width=30)
        table.add_column("Company", style="magenta")
        table.add_column("Location", style="green")
        table.add_column("Remote", style="yellow")
        table.add_column("Platform", style="blue")
        
        for job in jobs[:limit]:
            table.add_row(
                job.get('title', 'N/A')[:30],
                job.get('company', 'N/A'),
                job.get('location', 'N/A'),
                "✓" if job.get('remote') else "✗",
                job.get('platform', 'N/A')
            )
            
        console.print(table)


def handle_notification_commands(args):
    """Handle notification-only commands.
    
    Args:
        args: Parsed arguments
        
    Returns:
        True if command was handled, False otherwise
    """
    # Send daily digest
    if args.send_digest:
        notifier = NotificationManager()
        email_to = args.email_to or os.getenv('RECIPIENT_EMAIL')
        
        if not email_to:
            console.print("[red]Error: No recipient email specified[/red]")
            console.print("Use --email-to or set RECIPIENT_EMAIL in .env")
            return True
        
        console.print(f"\n[cyan]Sending daily digest to {email_to}...[/cyan]")
        success = notifier.email.send_daily_digest(email_to, hours=args.digest_hours)
        
        if success:
            console.print("[green]✓[/green] Digest sent successfully")
        else:
            console.print("[red]✗[/red] Failed to send digest")
        
        return True
    
    return False


def handle_database_commands(args):
    """Handle database-only commands.
    
    Args:
        args: Parsed arguments
        
    Returns:
        True if command was handled, False otherwise
    """
    db = JobDatabase()
    
    # Show statistics
    if args.db_stats:
        console.print("\n[bold cyan]Database Statistics[/bold cyan]")
        console.print("=" * 60)
        
        stats = db.get_statistics()
        
        console.print(f"\n[bold]Total Jobs:[/bold] {stats['total_jobs']}")
        console.print(f"[bold]Remote Jobs:[/bold] {stats['remote_jobs']}")
        console.print(f"[bold]Non-Remote Jobs:[/bold] {stats['non_remote_jobs']}")
        
        console.print(f"\n[bold green]New in Last 24h:[/bold green] {stats['new_last_24h']}")
        console.print(f"[bold yellow]New in Last 7 Days:[/bold yellow] {stats['new_last_7d']}")
        
        console.print("\n[bold]Jobs by Status:[/bold]")
        for status, count in stats['by_status'].items():
            console.print(f"  {status}: {count}")
            
        console.print("\n[bold]Jobs by Platform:[/bold]")
        for platform, count in sorted(stats['by_platform'].items(), key=lambda x: x[1], reverse=True):
            console.print(f"  {platform}: {count}")
            
        console.print("\n" + "=" * 60)
        return True
        
    # Search database
    if args.search_db:
        console.print(f"\n[cyan]Searching database for: {args.search_db}[/cyan]")
        
        jobs = db.search_jobs(
            keywords=args.search_db,
            remote_only=args.remote,
            platform=args.platforms[0] if args.platforms else None
        )
        
        console.print(f"[green]Found {len(jobs)} matching jobs[/green]\n")
        
        if jobs:
            exporter = DataExporter()
            exporter.display_jobs(jobs, limit=args.display)
            
            # Export if requested
            if args.output_format:
                if 'csv' in args.output_format:
                    exporter.export_to_csv(jobs, 'database_search_results.csv')
                if 'json' in args.output_format:
                    exporter.export_to_json(jobs, 'database_search_results.json')
                    
        return True
        
    # Cleanup old jobs
    if args.cleanup_old:
        console.print(f"\n[yellow]Cleaning up jobs older than {args.cleanup_old} days...[/yellow]")
        deleted = db.cleanup_old_jobs(args.cleanup_old)
        console.print(f"[green]✓[/green] Deleted {deleted} old jobs")
        return True
        
    return False


def handle_analytics_commands(args) -> bool:
    """Handle analytics commands."""
    from analytics import JobAnalytics, print_analytics_report
    
    # Comprehensive analytics
    if args.analytics:
        analytics = JobAnalytics()
        print_analytics_report(analytics)
        return True
    
    # Individual reports
    if args.trends or args.salary_report or args.skills_report or args.platform_report:
        analytics = JobAnalytics()
        
        if args.trends:
            console.print("\n[bold cyan]📈 Job Posting Trends (Last 30 Days)[/bold cyan]\n")
            trends = analytics.get_job_trends(30)
            console.print(f"Total Jobs: [green]{trends['total_jobs']}[/green]")
            console.print(f"Daily Average: [yellow]{trends['avg_per_day']}[/yellow]")
            console.print(f"Peak Day: [cyan]{trends['peak_day']}[/cyan] ({trends['peak_count']} jobs)")
            console.print(f"Trend: [bold]{trends['trend'].upper()}[/bold]\n")
        
        if args.salary_report:
            console.print("\n[bold cyan]💰 Salary Insights[/bold cyan]\n")
            salary = analytics.get_salary_insights()
            if not salary.get('insufficient_data'):
                console.print(f"Jobs with Salary: [green]{salary['jobs_with_salary']}[/green]")
                console.print(f"Median: [yellow]${salary['median']:,}[/yellow]")
                console.print(f"Mean: [yellow]${salary['mean']:,}[/yellow]")
                console.print(f"Range: ${salary['min']:,} - ${salary['max']:,}")
                console.print(f"25th Percentile: ${salary['percentile_25']:,}")
                console.print(f"75th Percentile: ${salary['percentile_75']:,}\n")
            else:
                console.print("[yellow]Insufficient salary data[/yellow]\n")
        
        if args.skills_report:
            console.print("\n[bold cyan]🔥 Top Skills in Demand[/bold cyan]\n")
            skills = analytics.get_skills_frequency(15)
            for i, (skill, count) in enumerate(skills, 1):
                console.print(f"{i:2}. [green]{skill:20}[/green] - {count} jobs")
            console.print()
        
        if args.platform_report:
            console.print("\n[bold cyan]🌐 Platform Performance[/bold cyan]\n")
            platforms = analytics.get_platform_stats()
            for platform in platforms[:10]:
                console.print(f"\n[bold]{platform['platform']}[/bold]")
                console.print(f"  Jobs: {platform['total_jobs']}")
                console.print(f"  Remote: {platform['remote_percentage']}%")
                if platform['avg_salary']:
                    console.print(f"  Avg Salary: ${platform['avg_salary']:,}")
                console.print(f"  Applied: {platform['applied_count']}")
            console.print()
        
        return True
    
    return False


def handle_auto_apply_commands(args) -> bool:
    """Handle auto-apply commands."""
    # Setup template
    if args.auto_apply_setup:
        setup_template_interactive()
        return True
    
    # Auto-apply to jobs
    if args.auto_apply:
        # Check template
        template = ApplicationTemplate()
        is_complete, missing = template.is_complete()
        
        if not is_complete:
            console.print("[red]❌ Application template incomplete![/red]")
            console.print("\n[yellow]Missing required fields:[/yellow]")
            for field in missing:
                console.print(f"  • {field}")
            console.print(f"\n[cyan]Run: python main.py --auto-apply-setup[/cyan]")
            return True
        
        # Get jobs to apply to
        db = JobDatabase()
        
        # If AI recommendations requested
        if args.ai_recommend:
            console.print("[cyan]🤖 Getting AI-recommended jobs for auto-apply...[/cyan]\n")
            matcher = JobMatcher(db)
            jobs = matcher.get_recommendations(min_score=args.min_score, limit=args.max_applications * 2)
            
            if not jobs:
                console.print("[yellow]No jobs match your AI criteria[/yellow]")
                return True
            
            console.print(f"[green]Found {len(jobs)} AI-recommended jobs[/green]\n")
        else:
            # Get jobs from database (new jobs preferred)
            if args.show_new_only:
                hours = args.new_since_hours
                jobs = db.get_new_jobs_since_hours(hours)
                console.print(f"[cyan]Found {len(jobs)} new jobs from last {hours} hours[/cyan]\n")
            else:
                # Get jobs with 'new' status
                jobs = db.search_jobs(status='new', limit=args.max_applications * 2)
                console.print(f"[cyan]Found {len(jobs)} jobs in 'new' status[/cyan]\n")
        
        if not jobs:
            console.print("[yellow]No jobs available for auto-apply[/yellow]")
            console.print("[dim]Try scraping first or remove filters[/dim]")
            return True
        
        # Filter by platforms if specified
        if args.platforms:
            jobs = [j for j in jobs if j.get('platform') in args.platforms]
            console.print(f"[cyan]Filtered to {len(jobs)} jobs from selected platforms[/cyan]\n")
        
        if not jobs:
            console.print("[yellow]No jobs match the platform filter[/yellow]")
            return True
        
        # Show what we're about to do
        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[bold]🤖 AUTO-APPLY SESSION[/bold]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"📊 Jobs available: {len(jobs)}")
        console.print(f"📊 Max applications: {args.max_applications}")
        console.print(f"⏱️  Delay between apps: {args.apply_delay}s")
        console.print(f"🌐 Browser: {'Playwright' if args.use_playwright else 'Selenium'}")
        console.print(f"👁️  Browser visible: {'Yes' if args.show_browser else 'No'}")
        if args.dry_run:
            console.print(f"[yellow]🔍 DRY RUN MODE: No actual submissions[/yellow]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")
        
        if not args.dry_run:
            confirm = input("⚠️  Start auto-applying? (yes/no): ").strip().lower()
            if confirm != 'yes':
                console.print("[yellow]Auto-apply cancelled[/yellow]")
                return True
        
        # Start auto-applying
        try:
            with AutoApplier(
                template,
                use_playwright=args.use_playwright,
                headless=not args.show_browser,
                dry_run=args.dry_run
            ) as applier:
                stats = applier.apply_to_jobs(
                    jobs[:args.max_applications],
                    max_applications=args.max_applications,
                    delay_between=args.apply_delay
                )
                
                # Send notification if enabled
                if args.email_notify and stats['successful'] > 0:
                    notifier = NotificationManager()
                    subject = f"🤖 Auto-Apply Session Complete - {stats['successful']} Applications Submitted"
                    message = f"""
Auto-Apply Session Summary:

✅ Successful: {stats['successful']}
❌ Failed: {stats['failed']}
⚠️  CAPTCHAs: {stats['captcha_detected']}
📋 Total attempted: {stats['attempted']}

Check your email confirmations from employers.
                    """
                    notifier.send_email(subject, message, args.email_to)
                
        except KeyboardInterrupt:
            console.print("\n\n[yellow]⚠️  Auto-apply interrupted by user[/yellow]")
        except Exception as e:
            console.print(f"\n[red]❌ Auto-apply error: {e}[/red]")
        
        return True
    
    return False


def handle_ai_commands(args):
    """Handle AI matching commands.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        True if command was handled, False otherwise
    """
    # Resume parsing
    if args.parse_resume:
        import json
        
        try:
            rp = ResumeParser()
            preferences = rp.parse_and_generate_preferences(args.parse_resume)
            
            # Display preferences
            rp.display_preferences(preferences)
            
            # Ask for confirmation
            console.print("\n[bold]Save these preferences?[/bold] (y/n): ", end='')
            response = input().strip().lower()
            
            if response == 'y':
                with open('preferences.json', 'w') as f:
                    json.dump(preferences, f, indent=2)
                
                console.print("\n[green]✓[/green] Preferences saved to preferences.json")
                console.print("\n[cyan]Next steps:[/cyan]")
                console.print("  1. Review preferences.json and adjust if needed")
                console.print("  2. Run: [bold]python main.py 'your role' --remote[/bold] (scrape jobs)")
                console.print("  3. Run: [bold]python main.py --ai-recommend[/bold] (get recommendations)")
            else:
                console.print("\n[yellow]Preferences not saved[/yellow]")
                console.print("To save manually, run: [bold]python resume_parser.py your_resume.pdf[/bold]")
            
            return True
        
        except Exception as e:
            console.print(f"\n[red]✗ Error parsing resume:[/red] {e}")
            
            if "not installed" in str(e).lower():
                console.print("\n[yellow]Missing library. Install with:[/yellow]")
                if "pypdf2" in str(e).lower():
                    console.print("  pip install PyPDF2")
                elif "docx" in str(e).lower():
                    console.print("  pip install python-docx")
            elif "not found" in str(e).lower():
                console.print(f"\n[yellow]File not found:[/yellow] {args.parse_resume}")
                console.print("Make sure the file path is correct")
            
            return True
    
    # AI setup
    if args.ai_setup:
        pm = PreferencesManager()
        pm.interactive_setup()
        return True
    
    # AI recommendations
    if args.ai_recommend:
        matcher = JobMatcher()
        console.print(f"\n[bold cyan]🤖 AI Job Recommendations (min score: {args.min_score})[/bold cyan]")
        recommendations = matcher.get_recommendations(limit=args.display, min_score=args.min_score)
        matcher.display_recommendations(recommendations)
        return True
    
    # Skills analysis
    if args.ai_analyze:
        matcher = JobMatcher()
        analysis = matcher.analyze_skills_demand()
        
        console.print("\n[bold cyan]📊 Skills Demand Analysis[/bold cyan]\n")
        console.print(f"Total jobs analyzed: {analysis['total_jobs']}")
        console.print(f"Unique skills found: {analysis['unique_skills']}\n")
        console.print("[bold]Top 20 Most In-Demand Skills:[/bold]\n")
        
        for i, (skill, count) in enumerate(analysis['top_skills'], 1):
            pct = (count / analysis['total_jobs']) * 100
            console.print(f"{i:2}. {skill:20} - {count:4} jobs ({pct:.1f}%)")
        return True
    
    # Skill suggestions
    if args.ai_suggest:
        matcher = JobMatcher()
        suggestions = matcher.suggest_skills_to_learn()
        
        console.print("\n[bold cyan]💡 Skills You Should Learn[/bold cyan]\n")
        
        if not suggestions:
            console.print("[yellow]No suggestions - you already have all top skills![/yellow]")
        else:
            console.print("Based on current job market demand:\n")
            for i, (skill, count) in enumerate(suggestions, 1):
                console.print(f"{i:2}. {skill:20} - Found in {count} jobs")
        return True
    
    return False


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description='Job Scraper - Find jobs across multiple platforms with advanced filtering',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for remote Python jobs
  python main.py --keywords "python developer" --remote
  
  # Search on specific platforms
  python main.py --keywords "data scientist" --platforms indeed linkedin
  
  # Search with salary filter
  python main.py --keywords "software engineer" --min-salary 100000
  
  # Search with location
  python main.py --keywords "web developer" --location "New York"
  
  # Export to multiple formats
  python main.py --keywords "devops" --output-format csv json
        """
    )
    
    # Search parameters
    parser.add_argument('--keywords', '-k', type=str, default='',
                        help='Job keywords to search for')
    parser.add_argument('--location', '-l', type=str, default='',
                        help='Job location')
    parser.add_argument('--remote', '-r', action='store_true',
                        help='Search for remote jobs only')
    parser.add_argument('--job-type', '-t', type=str, 
                        choices=['fulltime', 'parttime', 'contract', 'internship'],
                        help='Type of job')
    parser.add_argument('--min-salary', type=int,
                        help='Minimum salary (yearly)')
    parser.add_argument('--exclude', '-e', type=str,
                        help='Keywords to exclude from results')
    
    # Platform selection
    parser.add_argument('--platforms', '-p', nargs='+',
                        choices=['indeed', 'linkedin', 'glassdoor', 'remoteok', 'weworkremotely',
                                'monster', 'dice', 'simplyhired', 'ziprecruiter', 'angellist'],
                        help='Platforms to scrape (default: all)')
    
    # Scraping options
    parser.add_argument('--max-pages', type=int, default=config.MAX_PAGES,
                        help=f'Maximum pages to scrape per platform (default: {config.MAX_PAGES})')
    
    # Output options
    parser.add_argument('--output-format', '-o', nargs='+',
                        choices=['csv', 'json', 'excel'],
                        default=['csv'],
                        help='Output format(s) (default: csv)')
    parser.add_argument('--display', '-d', type=int, default=10,
                        help='Number of jobs to display (default: 10)')
    parser.add_argument('--deduplicate', action='store_true',
                        help='Remove duplicate jobs')
    parser.add_argument('--sort-by', choices=['platform', 'company', 'title', 'location'],
                        help='Sort results by field')
    
    # Database options
    parser.add_argument('--use-database', action='store_true', default=True,
                        help='Save jobs to database (default: True)')
    parser.add_argument('--show-new-only', action='store_true',
                        help='Show only new jobs not seen before')
    parser.add_argument('--new-since-hours', type=int, default=24,
                        help='When using --show-new-only, show jobs from last N hours (default: 24)')
    parser.add_argument('--db-stats', action='store_true',
                        help='Show database statistics and exit')
    parser.add_argument('--search-db', type=str, metavar='KEYWORDS',
                        help='Search jobs in database instead of scraping')
    parser.add_argument('--cleanup-old', type=int, metavar='DAYS',
                        help='Remove jobs older than N days from database')
    
    # Notification options
    parser.add_argument('--email-notify', action='store_true',
                        help='Send email notification for new jobs')
    parser.add_argument('--email-to', type=str,
                        help='Email recipient (default: from .env RECIPIENT_EMAIL)')
    parser.add_argument('--webhook-notify', action='store_true',
                        help='Send webhook notification (Slack/Discord)')
    parser.add_argument('--send-digest', action='store_true',
                        help='Send daily digest email and exit')
    parser.add_argument('--digest-hours', type=int, default=24,
                        help='Hours to include in digest (default: 24)')
    
    # AI matching options
    parser.add_argument('--ai-setup', action='store_true',
                        help='Setup AI job matching preferences (interactive)')
    parser.add_argument('--ai-recommend', action='store_true',
                        help='Get AI-powered job recommendations')
    parser.add_argument('--ai-analyze', action='store_true',
                        help='Analyze skills demand in job market')
    parser.add_argument('--ai-suggest', action='store_true',
                        help='Get skill learning suggestions based on market demand')
    parser.add_argument('--min-score', type=float, default=60,
                        help='Minimum match score for AI recommendations (0-100, default: 60)')
    parser.add_argument('--parse-resume', type=str, metavar='FILE',
                        help='Parse resume and auto-generate AI preferences (PDF, DOCX, or TXT)')
    
    # Analytics options
    parser.add_argument('--analytics', action='store_true',
                        help='Show comprehensive analytics report')
    parser.add_argument('--trends', action='store_true',
                        help='Show job posting trends')
    parser.add_argument('--salary-report', action='store_true',
                        help='Show salary insights')
    parser.add_argument('--skills-report', action='store_true',
                        help='Show skills demand report')
    parser.add_argument('--platform-report', action='store_true',
                        help='Show platform comparison')
    
    # Auto-apply options
    parser.add_argument('--auto-apply-setup', action='store_true',
                        help='Setup auto-apply template (interactive)')
    parser.add_argument('--auto-apply', action='store_true',
                        help='Automatically apply to jobs')
    parser.add_argument('--max-applications', type=int, default=10,
                        help='Maximum applications per session (default: 10)')
    parser.add_argument('--apply-delay', type=int, default=10,
                        help='Delay in seconds between applications (default: 10)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Test auto-apply without actually submitting')
    parser.add_argument('--use-playwright', action='store_true',
                        help='Use Playwright instead of Selenium for auto-apply')
    parser.add_argument('--show-browser', action='store_true',
                        help='Show browser window during auto-apply')
    
    args = parser.parse_args()
    
    # Handle analytics commands
    if handle_analytics_commands(args):
        return
    
    # Handle auto-apply commands
    if handle_auto_apply_commands(args):
        return
    
    # Handle AI matching commands
    if handle_ai_commands(args):
        return
    
    # Handle notification-only commands
    if handle_notification_commands(args):
        return
    
    # Handle database-only commands
    if handle_database_commands(args):
        return
    
    # Create and run the application
    app = JobScraperApp()
    app.run(args)


if __name__ == '__main__':
    main()
