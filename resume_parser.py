"""Resume parser for extracting skills and auto-configuring AI preferences."""
import re
import os
from typing import Dict, List, Set
from pathlib import Path
from rich.console import Console

console = Console()

# Try to import PDF/DOCX libraries
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    import docx
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False


class ResumeParser:
    """Parse resumes and extract skills, experience, and preferences."""
    
    def __init__(self):
        """Initialize resume parser."""
        # Comprehensive skill database
        self.skills = {
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'golang',
            'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl',
            'shell', 'bash', 'powershell',
            
            # Web Frontend
            'react', 'angular', 'vue', 'vue.js', 'svelte', 'next.js', 'nextjs', 'nuxt',
            'html', 'html5', 'css', 'css3', 'sass', 'scss', 'less', 'tailwind',
            'bootstrap', 'material-ui', 'webpack', 'vite', 'jquery',
            
            # Web Backend
            'node.js', 'nodejs', 'express', 'django', 'flask', 'fastapi', 'spring',
            'spring boot', 'laravel', 'rails', 'ruby on rails', 'asp.net', '.net',
            
            # Databases
            'sql', 'nosql', 'postgresql', 'postgres', 'mysql', 'mongodb', 'redis',
            'elasticsearch', 'cassandra', 'dynamodb', 'oracle', 'sqlite', 'mariadb',
            'neo4j', 'couchdb', 'influxdb',
            
            # Cloud & DevOps
            'aws', 'amazon web services', 'azure', 'microsoft azure', 'gcp',
            'google cloud', 'docker', 'kubernetes', 'k8s', 'jenkins', 'gitlab ci',
            'github actions', 'terraform', 'ansible', 'chef', 'puppet', 'vagrant',
            'circleci', 'travis ci', 'ci/cd', 'continuous integration',
            
            # Data Science & ML
            'machine learning', 'deep learning', 'artificial intelligence', 'ai',
            'ml', 'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn',
            'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'plotly',
            'jupyter', 'spark', 'pyspark', 'hadoop', 'kafka', 'airflow',
            'data science', 'data analysis', 'data engineering', 'etl',
            
            # Mobile
            'ios', 'android', 'react native', 'flutter', 'xamarin', 'swift',
            'objective-c', 'kotlin',
            
            # Tools & Platforms
            'git', 'github', 'gitlab', 'bitbucket', 'svn', 'jira', 'confluence',
            'slack', 'linux', 'unix', 'macos', 'windows', 'vim', 'vscode',
            
            # Architecture & Concepts
            'rest', 'restful', 'api', 'graphql', 'grpc', 'microservices', 'monolith',
            'serverless', 'lambda', 'agile', 'scrum', 'kanban', 'tdd', 'bdd',
            'test-driven development', 'unit testing', 'integration testing',
            'design patterns', 'solid', 'mvc', 'mvvm',
            
            # Security
            'security', 'cybersecurity', 'oauth', 'jwt', 'ssl', 'tls', 'encryption',
            'penetration testing', 'vulnerability assessment',
            
            # Other
            'blockchain', 'ethereum', 'solidity', 'web3', 'defi', 'nft',
            'iot', 'embedded systems', 'robotics', 'game development', 'unity',
            'unreal engine', 'ui/ux', 'figma', 'sketch', 'adobe xd'
        }
        
        # Experience level keywords
        self.experience_levels = {
            'senior': ['senior', 'lead', 'principal', 'staff', 'architect', 'expert'],
            'mid': ['mid-level', 'intermediate', '3-5 years', '2-4 years'],
            'junior': ['junior', 'entry-level', 'graduate', 'intern', '0-2 years']
        }
        
        # Job type keywords
        self.job_types = {
            'fulltime': ['full-time', 'fulltime', 'full time', 'permanent'],
            'contract': ['contract', 'contractor', 'freelance', 'consultant'],
            'parttime': ['part-time', 'parttime', 'part time'],
            'internship': ['intern', 'internship', 'co-op', 'coop']
        }
    
    def parse_file(self, file_path: str) -> str:
        """Parse resume file and extract text.
        
        Args:
            file_path: Path to resume file (PDF, DOCX, or TXT)
            
        Returns:
            Extracted text from resume
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return self._parse_pdf(file_path)
        elif extension in ['.docx', '.doc']:
            return self._parse_docx(file_path)
        elif extension == '.txt':
            return self._parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}. Supported: .pdf, .docx, .txt")
    
    def _parse_pdf(self, file_path: Path) -> str:
        """Parse PDF file."""
        if not PDF_SUPPORT:
            raise ImportError("PyPDF2 not installed. Run: pip install PyPDF2")
        
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Error parsing PDF: {e}")
        
        return text
    
    def _parse_docx(self, file_path: Path) -> str:
        """Parse DOCX file."""
        if not DOCX_SUPPORT:
            raise ImportError("python-docx not installed. Run: pip install python-docx")
        
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            raise Exception(f"Error parsing DOCX: {e}")
    
    def _parse_txt(self, file_path: Path) -> str:
        """Parse TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Error parsing TXT: {e}")
    
    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract skills from resume text.
        
        Args:
            text: Resume text
            
        Returns:
            Dictionary with categorized skills
        """
        text_lower = text.lower()
        found_skills = set()
        
        # Find all skills mentioned in resume
        for skill in self.skills:
            # Use word boundaries for accurate matching
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)
        
        # Categorize skills by frequency/importance
        # Skills mentioned multiple times are more important
        skill_counts = {}
        for skill in found_skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            count = len(re.findall(pattern, text_lower))
            skill_counts[skill] = count
        
        # Sort by frequency
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Top skills (mentioned most) become required
        # Others become preferred
        all_skills = [skill for skill, _ in sorted_skills]
        
        # Split into required (top third) and preferred (rest)
        split_point = max(3, len(all_skills) // 3)  # At least 3 required skills
        required = all_skills[:split_point]
        preferred = all_skills[split_point:]
        
        return {
            'required_skills': required,
            'preferred_skills': preferred,
            'all_skills': all_skills,
            'skill_counts': skill_counts
        }
    
    def extract_experience_level(self, text: str) -> str:
        """Extract experience level from resume.
        
        Args:
            text: Resume text
            
        Returns:
            Experience level (senior, mid, junior, or None)
        """
        text_lower = text.lower()
        
        # Check for experience level keywords
        for level, keywords in self.experience_levels.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return level
        
        # Try to extract years of experience
        years_pattern = r'(\d+)[\+\s]*years?'
        matches = re.findall(years_pattern, text_lower)
        
        if matches:
            max_years = max([int(y) for y in matches])
            if max_years >= 7:
                return 'senior'
            elif max_years >= 3:
                return 'mid'
            else:
                return 'junior'
        
        return None
    
    def extract_salary_expectations(self, text: str) -> int:
        """Extract salary expectations from resume.
        
        Args:
            text: Resume text
            
        Returns:
            Minimum salary or None
        """
        # Look for salary mentions
        salary_patterns = [
            r'\$\s*(\d{2,3}),?(\d{3})',  # $100,000 or $100000
            r'(\d{2,3})k',  # 100k
            r'salary.*?(\d{2,3}),?(\d{3})',  # salary: $100,000
        ]
        
        text_lower = text.lower()
        salaries = []
        
        for pattern in salary_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle comma-separated numbers
                    if len(match) == 2:
                        salary = int(match[0]) * 1000 + int(match[1])
                    else:
                        salary = int(match[0]) * 1000
                else:
                    salary = int(match) * 1000
                
                # Sanity check (between $30k and $500k)
                if 30000 <= salary <= 500000:
                    salaries.append(salary)
        
        return min(salaries) if salaries else None
    
    def extract_preferences(self, text: str) -> Dict:
        """Extract job preferences from resume.
        
        Args:
            text: Resume text
            
        Returns:
            Dictionary of preferences
        """
        text_lower = text.lower()
        
        # Check for remote preference
        remote_keywords = ['remote', 'work from home', 'wfh', 'distributed', 'location independent']
        remote_only = any(keyword in text_lower for keyword in remote_keywords)
        
        # Check for job type preferences
        preferred_job_types = []
        for job_type, keywords in self.job_types.items():
            if any(keyword in text_lower for keyword in keywords):
                if job_type == 'internship':
                    # Skip internship unless explicitly seeking it
                    if 'seeking internship' in text_lower or 'looking for internship' in text_lower:
                        preferred_job_types.append(job_type)
                else:
                    preferred_job_types.append(job_type)
        
        # Default to full-time if nothing specified
        if not preferred_job_types:
            preferred_job_types = ['fulltime']
        
        return {
            'remote_only': remote_only,
            'job_types': preferred_job_types
        }
    
    def parse_and_generate_preferences(self, file_path: str) -> Dict:
        """Parse resume and generate AI preferences.
        
        Args:
            file_path: Path to resume file
            
        Returns:
            Complete preferences dictionary for AI matching
        """
        console.print(f"\n[cyan]📄 Parsing resume: {file_path}[/cyan]")
        
        # Parse resume
        text = self.parse_file(file_path)
        
        console.print(f"[green]✓[/green] Resume parsed ({len(text)} characters)")
        
        # Extract skills
        console.print("\n[cyan]🔍 Extracting skills...[/cyan]")
        skills = self.extract_skills(text)
        
        console.print(f"[green]✓[/green] Found {len(skills['all_skills'])} skills")
        console.print(f"  - Required: {len(skills['required_skills'])} skills")
        console.print(f"  - Preferred: {len(skills['preferred_skills'])} skills")
        
        # Extract experience level
        experience = self.extract_experience_level(text)
        if experience:
            console.print(f"[green]✓[/green] Experience level: {experience}")
        
        # Extract salary
        salary = self.extract_salary_expectations(text)
        if salary:
            console.print(f"[green]✓[/green] Salary expectation: ${salary:,}")
        
        # Extract preferences
        prefs = self.extract_preferences(text)
        console.print(f"[green]✓[/green] Remote preference: {'Yes' if prefs['remote_only'] else 'No'}")
        console.print(f"[green]✓[/green] Job types: {', '.join(prefs['job_types'])}")
        
        # Generate excluded keywords based on experience
        excluded = []
        if experience == 'senior':
            excluded = ['junior', 'entry-level', 'intern', 'graduate']
        elif experience == 'junior':
            excluded = ['senior', 'lead', 'principal', 'architect', 'manager']
        
        # Build preferences dictionary
        preferences = {
            'required_skills': skills['required_skills'][:10],  # Top 10
            'preferred_skills': skills['preferred_skills'][:15],  # Next 15
            'excluded_keywords': excluded,
            'min_salary': salary,
            'remote_only': prefs['remote_only'],
            'experience_years': None,
            'job_types': prefs['job_types'],
            'preferred_companies': [],
            'excluded_companies': []
        }
        
        return preferences
    
    def display_preferences(self, preferences: Dict):
        """Display generated preferences in a nice format.
        
        Args:
            preferences: Preferences dictionary
        """
        console.print("\n[bold cyan]🎯 Generated AI Preferences:[/bold cyan]\n")
        
        console.print("[bold]Required Skills:[/bold]")
        if preferences['required_skills']:
            for skill in preferences['required_skills']:
                console.print(f"  • {skill}")
        else:
            console.print("  (none)")
        
        console.print("\n[bold]Preferred Skills:[/bold]")
        if preferences['preferred_skills']:
            for skill in preferences['preferred_skills'][:10]:  # Show first 10
                console.print(f"  • {skill}")
            if len(preferences['preferred_skills']) > 10:
                console.print(f"  ... and {len(preferences['preferred_skills']) - 10} more")
        else:
            console.print("  (none)")
        
        console.print("\n[bold]Excluded Keywords:[/bold]")
        if preferences['excluded_keywords']:
            console.print(f"  {', '.join(preferences['excluded_keywords'])}")
        else:
            console.print("  (none)")
        
        console.print("\n[bold]Other Preferences:[/bold]")
        if preferences['min_salary']:
            console.print(f"  Minimum Salary: ${preferences['min_salary']:,}")
        console.print(f"  Remote Only: {preferences['remote_only']}")
        console.print(f"  Job Types: {', '.join(preferences['job_types'])}")


def main():
    """CLI for resume parser."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Resume Parser - Extract skills and generate AI preferences')
    parser.add_argument('resume', help='Path to resume file (PDF, DOCX, or TXT)')
    parser.add_argument('--output', '-o', default='preferences.json', help='Output preferences file')
    parser.add_argument('--preview', '-p', action='store_true', help='Preview without saving')
    
    args = parser.parse_args()
    
    # Parse resume
    rp = ResumeParser()
    
    try:
        preferences = rp.parse_and_generate_preferences(args.resume)
        
        # Display preferences
        rp.display_preferences(preferences)
        
        if args.preview:
            console.print("\n[yellow]Preview mode - preferences not saved[/yellow]")
        else:
            # Save preferences
            with open(args.output, 'w') as f:
                json.dump(preferences, f, indent=2)
            
            console.print(f"\n[green]✓[/green] Preferences saved to: {args.output}")
            console.print("\nNext steps:")
            console.print("  1. Review and edit preferences.json if needed")
            console.print("  2. Run: [cyan]python main.py 'your role' --remote[/cyan]")
            console.print("  3. Run: [cyan]python main.py --ai-recommend[/cyan]")
    
    except Exception as e:
        console.print(f"\n[red]✗ Error:[/red] {e}")
        
        if "not installed" in str(e):
            console.print("\n[yellow]Install missing library:[/yellow]")
            if "PyPDF2" in str(e):
                console.print("  pip install PyPDF2")
            elif "python-docx" in str(e):
                console.print("  pip install python-docx")


if __name__ == '__main__':
    main()
