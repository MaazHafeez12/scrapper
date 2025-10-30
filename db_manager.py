#!/usr/bin/env python
"""Database management CLI tool."""
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from database import JobDatabase
from export import DataExporter

console = Console()


def show_stats(db: JobDatabase):
    """Show database statistics."""
    stats = db.get_statistics()
    
    console.print("\n[bold cyan]═══ Database Statistics ═══[/bold cyan]\n")
    
    # Overview panel
    overview = f"""[bold]Total Jobs:[/bold] {stats['total_jobs']}
[bold]Remote Jobs:[/bold] {stats['remote_jobs']} ({stats['remote_jobs']/max(stats['total_jobs'], 1)*100:.1f}%)
[bold]Non-Remote:[/bold] {stats['non_remote_jobs']} ({stats['non_remote_jobs']/max(stats['total_jobs'], 1)*100:.1f}%)

[bold green]New in Last 24h:[/bold green] {stats['new_last_24h']}
[bold yellow]New in Last 7 Days:[/bold yellow] {stats['new_last_7d']}
[bold blue]New in Last 30 Days:[/bold blue] {stats['new_last_30d']}"""
    
    console.print(Panel(overview, title="Overview", border_style="cyan"))
    
    # Status table
    if stats['by_status']:
        status_table = Table(title="Jobs by Status", show_header=True, header_style="bold magenta")
        status_table.add_column("Status", style="cyan")
        status_table.add_column("Count", justify="right", style="green")
        status_table.add_column("Percentage", justify="right", style="yellow")
        
        for status, count in sorted(stats['by_status'].items()):
            percentage = count / max(stats['total_jobs'], 1) * 100
            status_table.add_row(status, str(count), f"{percentage:.1f}%")
        
        console.print("\n", status_table)
    
    # Platform table
    if stats['by_platform']:
        platform_table = Table(title="Jobs by Platform", show_header=True, header_style="bold magenta")
        platform_table.add_column("Platform", style="cyan")
        platform_table.add_column("Count", justify="right", style="green")
        platform_table.add_column("Percentage", justify="right", style="yellow")
        
        for platform, count in sorted(stats['by_platform'].items(), key=lambda x: x[1], reverse=True):
            percentage = count / max(stats['total_jobs'], 1) * 100
            platform_table.add_row(platform, str(count), f"{percentage:.1f}%")
        
        console.print("\n", platform_table)
    
    console.print()


def search_jobs(db: JobDatabase, args):
    """Search jobs in database."""
    console.print(f"\n[cyan]Searching for: {args.keywords}[/cyan]")
    
    jobs = db.search_jobs(
        keywords=args.keywords,
        remote_only=args.remote,
        platform=args.platform,
        status=args.status,
        limit=args.limit
    )
    
    if not jobs:
        console.print("[yellow]No jobs found[/yellow]")
        return
    
    console.print(f"[green]Found {len(jobs)} jobs[/green]\n")
    
    # Display jobs
    exporter = DataExporter()
    exporter.display_jobs(jobs, limit=args.display)
    
    # Export if requested
    if args.export:
        format_map = {'csv': 'csv', 'json': 'json', 'excel': 'xlsx'}
        filename = f"search_results.{format_map[args.export]}"
        
        if args.export == 'csv':
            exporter.export_to_csv(jobs, filename)
        elif args.export == 'json':
            exporter.export_to_json(jobs, filename)
        elif args.export == 'excel':
            exporter.export_to_excel(jobs, filename)


def list_new_jobs(db: JobDatabase, args):
    """List new jobs from last N hours."""
    console.print(f"\n[cyan]Jobs from last {args.hours} hours:[/cyan]")
    
    jobs = db.get_new_jobs(since_hours=args.hours)
    
    if not jobs:
        console.print("[yellow]No new jobs found[/yellow]")
        return
    
    console.print(f"[green]Found {len(jobs)} new jobs[/green]\n")
    
    exporter = DataExporter()
    exporter.display_jobs(jobs, limit=args.display)


def update_job_status(db: JobDatabase, args):
    """Update job status."""
    with db:
        cursor = db.conn.cursor()
        cursor.execute("SELECT id, title, company FROM jobs WHERE url = ?", (args.url,))
        job = cursor.fetchone()
        
        if not job:
            console.print(f"[red]Job not found: {args.url}[/red]")
            return
        
        db.update_job_status(args.url, args.status, args.notes)
        console.print(f"[green]✓[/green] Updated status to '{args.status}' for:")
        console.print(f"  {job['title']} at {job['company']}")


def cleanup_database(db: JobDatabase, args):
    """Clean up old jobs."""
    console.print(f"\n[yellow]Cleaning up jobs older than {args.days} days...[/yellow]")
    
    deleted = db.cleanup_old_jobs(args.days)
    console.print(f"[green]✓[/green] Deleted {deleted} old jobs")


def export_database(db: JobDatabase, args):
    """Export entire database."""
    console.print(f"\n[cyan]Exporting database to {args.format}...[/cyan]")
    
    filters = {}
    if args.remote:
        filters['remote'] = True
    if args.platform:
        filters['platform'] = args.platform
    if args.status:
        filters['status'] = args.status
    
    exporter = DataExporter()
    filepath = exporter.export_database_to_file(
        format=args.format,
        filename=args.output,
        filters=filters if filters else None
    )
    
    if filepath:
        console.print(f"[green]✓[/green] Exported to {filepath}")


def view_history(db: JobDatabase, args):
    """View job change history."""
    console.print(f"\n[cyan]Change history for: {args.url}[/cyan]\n")
    
    with db:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT jh.change_date, jh.field_name, jh.old_value, jh.new_value
            FROM job_history jh
            JOIN jobs j ON jh.job_id = j.id
            WHERE j.url = ?
            ORDER BY jh.change_date DESC
            LIMIT ?
        """, (args.url, args.limit))
        
        history = cursor.fetchall()
        
        if not history:
            console.print("[yellow]No history found[/yellow]")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Date", style="cyan")
        table.add_column("Field", style="yellow")
        table.add_column("Old Value", style="red")
        table.add_column("New Value", style="green")
        
        for entry in history:
            table.add_row(
                entry['change_date'],
                entry['field_name'],
                str(entry['old_value']) if entry['old_value'] else '-',
                str(entry['new_value']) if entry['new_value'] else '-'
            )
        
        console.print(table)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Job Scraper Database Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show statistics
  python db_manager.py stats
  
  # Search for Python jobs
  python db_manager.py search "python developer" --remote
  
  # List new jobs from last 24 hours
  python db_manager.py new --hours 24
  
  # Update job status
  python db_manager.py update-status <job_url> applied --notes "Applied via email"
  
  # Export database to CSV
  python db_manager.py export --format csv --remote
  
  # Clean up old jobs
  python db_manager.py cleanup --days 90
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search jobs')
    search_parser.add_argument('keywords', help='Keywords to search for')
    search_parser.add_argument('--remote', action='store_true', help='Remote jobs only')
    search_parser.add_argument('--platform', help='Filter by platform')
    search_parser.add_argument('--status', help='Filter by status')
    search_parser.add_argument('--limit', type=int, default=100, help='Max results')
    search_parser.add_argument('--display', type=int, default=10, help='Number to display')
    search_parser.add_argument('--export', choices=['csv', 'json', 'excel'], help='Export results')
    
    # New jobs command
    new_parser = subparsers.add_parser('new', help='List new jobs')
    new_parser.add_argument('--hours', type=int, default=24, help='Hours to look back')
    new_parser.add_argument('--display', type=int, default=20, help='Number to display')
    
    # Update status command
    update_parser = subparsers.add_parser('update-status', help='Update job status')
    update_parser.add_argument('url', help='Job URL')
    update_parser.add_argument('status', choices=['new', 'applied', 'interested', 'rejected', 'archived'],
                               help='New status')
    update_parser.add_argument('--notes', help='Optional notes')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old jobs')
    cleanup_parser.add_argument('--days', type=int, default=90, help='Delete jobs older than N days')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export database')
    export_parser.add_argument('--format', choices=['csv', 'json', 'excel'], default='csv',
                               help='Export format')
    export_parser.add_argument('--output', help='Output filename')
    export_parser.add_argument('--remote', action='store_true', help='Remote jobs only')
    export_parser.add_argument('--platform', help='Filter by platform')
    export_parser.add_argument('--status', help='Filter by status')
    
    # History command
    history_parser = subparsers.add_parser('history', help='View job change history')
    history_parser.add_argument('url', help='Job URL')
    history_parser.add_argument('--limit', type=int, default=50, help='Max entries')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    db = JobDatabase()
    
    try:
        if args.command == 'stats':
            show_stats(db)
        elif args.command == 'search':
            search_jobs(db, args)
        elif args.command == 'new':
            list_new_jobs(db, args)
        elif args.command == 'update-status':
            update_job_status(db, args)
        elif args.command == 'cleanup':
            cleanup_database(db, args)
        elif args.command == 'export':
            export_database(db, args)
        elif args.command == 'history':
            view_history(db, args)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


if __name__ == '__main__':
    main()
