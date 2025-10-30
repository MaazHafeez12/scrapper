# Resume Parser Guide

## 🎯 Overview

The **Resume Parser** automatically extracts skills, experience, and preferences from your resume to configure AI job matching. No more manual setup!

## ⚡ Quick Start

### Method 1: Via Main Application (Recommended)

```bash
# Parse resume and auto-configure AI
python main.py --parse-resume "my_resume.pdf"
```

This will:
1. Parse your resume (PDF, DOCX, or TXT)
2. Extract all technical skills
3. Determine required vs preferred skills
4. Detect experience level
5. Find salary expectations
6. Identify remote preference
7. Generate preferences.json automatically

### Method 2: Standalone Parser

```bash
# Preview without saving
python resume_parser.py my_resume.pdf --preview

# Parse and save
python resume_parser.py my_resume.pdf

# Custom output file
python resume_parser.py my_resume.pdf --output custom_prefs.json
```

## 📋 Supported File Formats

### PDF Files (.pdf)
```bash
python main.py --parse-resume resume.pdf
```
**Requirements:** `pip install PyPDF2`

### Word Documents (.docx)
```bash
python main.py --parse-resume resume.docx
```
**Requirements:** `pip install python-docx`

### Text Files (.txt)
```bash
python main.py --parse-resume resume.txt
```
**Requirements:** None (built-in)

## 🔍 What Gets Extracted

### 1. **Technical Skills** (150+ skills detected)

**Categories:**
- **Programming Languages:** Python, Java, JavaScript, TypeScript, Go, Rust, C++, C#, etc.
- **Web Frontend:** React, Angular, Vue, HTML, CSS, Tailwind, Bootstrap, etc.
- **Web Backend:** Node.js, Django, Flask, Spring, Laravel, Express, etc.
- **Databases:** PostgreSQL, MongoDB, MySQL, Redis, Elasticsearch, etc.
- **Cloud & DevOps:** AWS, Azure, Docker, Kubernetes, Terraform, Jenkins, etc.
- **Data Science:** TensorFlow, PyTorch, Pandas, Spark, scikit-learn, etc.
- **Mobile:** iOS, Android, React Native, Flutter, Swift, Kotlin
- **Tools:** Git, Linux, Jira, Slack, etc.

**Skill Prioritization:**
- Skills mentioned **multiple times** → **Required skills**
- Skills mentioned **once** → **Preferred skills**

### 2. **Experience Level**

Detects based on:
- Keywords: "senior", "lead", "junior", "entry-level"
- Years mentioned: "5 years of experience", "3+ years"

**Mapping:**
- 7+ years → **Senior**
- 3-6 years → **Mid-level**
- 0-2 years → **Junior**

**Auto-excludes inappropriate jobs:**
- Senior → Excludes "junior", "entry-level", "intern"
- Junior → Excludes "senior", "lead", "principal"

### 3. **Salary Expectations**

Detects patterns like:
- "$120,000"
- "$120K"
- "120k salary"
- "Salary expectation: $100,000"

Uses the **minimum** found as your threshold.

### 4. **Work Preferences**

**Remote:**
- Detects: "remote", "work from home", "WFH", "distributed"
- Sets `remote_only: true` if found

**Job Type:**
- Full-time (default)
- Contract (if "contract", "freelance", "consultant")
- Part-time (if "part-time")

## 📊 Example Output

### Sample Resume Content:
```
Senior Python Developer
5 years of experience

Skills:
- Python, Django, FastAPI
- React, TypeScript
- PostgreSQL, Redis
- AWS, Docker, Kubernetes
- Git, CI/CD

Seeking remote full-time opportunities.
Salary expectation: $120,000+
```

### Generated Preferences:
```json
{
  "required_skills": [
    "python",
    "django",
    "fastapi",
    "react",
    "typescript"
  ],
  "preferred_skills": [
    "postgresql",
    "redis",
    "aws",
    "docker",
    "kubernetes",
    "git",
    "ci/cd"
  ],
  "excluded_keywords": [
    "junior",
    "entry-level",
    "intern",
    "graduate"
  ],
  "min_salary": 120000,
  "remote_only": true,
  "job_types": ["fulltime"],
  "preferred_companies": [],
  "excluded_companies": []
}
```

## 🚀 Complete Workflow

### Step 1: Parse Resume
```bash
python main.py --parse-resume my_resume.pdf
```

**Output:**
```
📄 Parsing resume: my_resume.pdf
✓ Resume parsed (3,456 characters)

🔍 Extracting skills...
✓ Found 25 skills
  - Required: 8 skills
  - Preferred: 17 skills
✓ Experience level: senior
✓ Salary expectation: $120,000
✓ Remote preference: Yes
✓ Job types: fulltime

🎯 Generated AI Preferences:

Required Skills:
  • python
  • django
  • postgresql
  • aws
  • docker
  • react
  • typescript
  • kubernetes

Preferred Skills:
  • redis
  • graphql
  • terraform
  • jenkins
  ... and 13 more

Excluded Keywords:
  junior, entry-level, intern, graduate

Other Preferences:
  Minimum Salary: $120,000
  Remote Only: True
  Job Types: fulltime

Save these preferences? (y/n):
```

### Step 2: Review & Adjust (Optional)
```bash
# Open preferences.json in your editor
code preferences.json

# Or
notepad preferences.json
```

### Step 3: Scrape Jobs
```bash
python main.py "Python Developer" --remote --platforms indeed linkedin
```

### Step 4: Get AI Recommendations
```bash
python main.py --ai-recommend --min-score 75
```

## 🎯 Advanced Usage

### Multiple Resume Profiles

Create different preferences for different job searches:

```bash
# Senior backend role
python resume_parser.py resume_backend.pdf -o prefs_backend.json

# Full-stack role
python resume_parser.py resume_fullstack.pdf -o prefs_fullstack.json

# Use backend preferences
copy prefs_backend.json preferences.json
python main.py --ai-recommend

# Switch to fullstack
copy prefs_fullstack.json preferences.json
python main.py --ai-recommend
```

### Resume Optimization

Use the parser to **optimize your resume**:

```bash
# Parse current resume
python resume_parser.py resume_v1.pdf --preview

# Check what skills were detected
# Add missing important skills to resume
# Re-parse and compare

python resume_parser.py resume_v2.pdf --preview
```

### Compare With Job Market

```bash
# 1. Parse your resume
python main.py --parse-resume resume.pdf

# 2. Scrape jobs
python main.py "Software Engineer" --platforms indeed linkedin

# 3. Analyze market demand
python main.py --ai-analyze

# 4. See what skills you should learn
python main.py --ai-suggest
```

## 💡 Tips for Best Results

### 1. **Use Standard Formatting**

✅ **Good:**
```
Skills:
- Python
- Django
- React
- AWS
```

❌ **Avoid:**
```
I know various technologies
```

### 2. **Be Explicit About Experience**

✅ **Good:**
```
Senior Software Engineer
5+ years of experience
```

❌ **Avoid:**
```
Experienced developer
```

### 3. **Include Salary If Known**

✅ **Good:**
```
Salary expectation: $120,000
```

❌ **Avoid:**
```
Competitive salary desired
```

### 4. **Mention Remote Preference Clearly**

✅ **Good:**
```
Seeking remote opportunities
Open to remote work
```

❌ **Avoid:**
```
Flexible about location
```

### 5. **Use Industry-Standard Terms**

✅ **Use:** PostgreSQL, React, AWS, Docker
❌ **Avoid:** Postgres, React.js, Amazon Cloud, Containers

The parser recognizes variations, but standard terms work best.

## 🐛 Troubleshooting

### Problem: "PyPDF2 not installed"

**Solution:**
```bash
pip install PyPDF2
```

### Problem: "python-docx not installed"

**Solution:**
```bash
pip install python-docx
```

### Problem: No skills detected

**Causes:**
1. Resume has unusual formatting
2. Skills in images (not text)
3. Non-standard skill names

**Solutions:**
1. Convert resume to plain text format
2. Use standard skill names
3. Check if PDF text is extractable:
   ```bash
   python resume_parser.py resume.pdf --preview
   ```

### Problem: Wrong experience level

**Cause:** No clear indicators in resume

**Solution:** Manually edit preferences.json:
```json
{
  "excluded_keywords": ["junior", "entry-level"]  // For senior roles
}
```

### Problem: Too many/few required skills

**Cause:** Skill frequency in resume

**Solution:** Manually adjust in preferences.json:
```json
{
  "required_skills": ["python", "django"],  // Reduce to essentials
  "preferred_skills": ["docker", "aws", "kubernetes"]  // Move others here
}
```

## 🔄 Integration with Workflow

### Daily Job Hunt Automation

**1. One-time Setup:**
```bash
# Parse resume once
python main.py --parse-resume resume.pdf
```

**2. Daily Scraping (Scheduled):**
```bash
# Windows Task Scheduler (8 AM daily)
python main.py "Python Developer" --remote --show-new-only --ai-recommend --min-score 75 --email-notify
```

**3. Update Resume Quarterly:**
```bash
# After learning new skills, update resume
# Re-parse to update preferences
python main.py --parse-resume resume_updated.pdf
```

### Resume-Driven Job Search

```bash
# 1. Parse resume
python main.py --parse-resume resume.pdf

# 2. See what you match now
python main.py --ai-analyze

# 3. Identify gaps
python main.py --ai-suggest

# 4. Learn missing skills
# ... 3 months of learning ...

# 5. Update resume with new skills
python main.py --parse-resume resume_new.pdf

# 6. Compare recommendations
python main.py --ai-recommend
# Should see higher scores and more matches!
```

## 📊 What Gets Prioritized

The parser uses a **frequency-based prioritization**:

### Required Skills (Top 33%)
- Mentioned **multiple times** in resume
- Listed in multiple sections
- Emphasized in job titles/summaries

### Preferred Skills (Remaining)
- Mentioned **once**
- In skill lists
- In project descriptions

### Example:

**Resume mentions:**
- Python (5 times) → **Required**
- Django (3 times) → **Required**
- React (1 time) → **Preferred**
- Docker (1 time) → **Preferred**

## 🎓 Resume Writing Tips

To get **better AI matching**, structure your resume to highlight:

### 1. Skills Section
```
Technical Skills:
Languages: Python, JavaScript, TypeScript, Go
Frameworks: Django, React, Node.js, Flask
Cloud: AWS, Azure, Docker, Kubernetes
Databases: PostgreSQL, MongoDB, Redis
```

### 2. Experience with Skills
```
Senior Python Developer | TechCorp | 2020-Present
• Built microservices using Python, Django, and PostgreSQL
• Deployed to AWS using Docker and Kubernetes
• Implemented frontend with React and TypeScript
```

### 3. Clear Experience Level
```
Senior Software Engineer
7+ years of professional experience
```

### 4. Work Preferences
```
Seeking full-time remote opportunities
Salary range: $120,000 - $150,000
```

## 🔗 API Integration

Use the resume parser in your own scripts:

```python
from resume_parser import ResumeParser
import json

# Initialize parser
rp = ResumeParser()

# Parse resume
preferences = rp.parse_and_generate_preferences('resume.pdf')

# Customize preferences
preferences['min_salary'] = 130000
preferences['preferred_companies'] = ['Google', 'Microsoft']

# Save
with open('preferences.json', 'w') as f:
    json.dump(preferences, f, indent=2)

print(f"Found {len(preferences['required_skills'])} required skills")
```

## 📈 Benefits

### ⏱️ **Time Savings**
- Manual setup: **15-20 minutes**
- Resume parsing: **30 seconds**
- **40x faster!**

### 🎯 **Accuracy**
- Catches all skills you might forget
- Consistent skill naming
- Frequency-based prioritization

### 🔄 **Easy Updates**
- Changed resume? Re-parse instantly
- Learned new skill? Update resume, re-parse
- No manual preference editing needed

### 📊 **Gap Analysis**
1. Parse resume → See your current skills
2. Run AI analyze → See market demand
3. Run AI suggest → See what to learn
4. Update resume → Re-parse → Better matches!

## 🎯 Next Steps

After parsing your resume:

1. **Review** generated preferences.json
2. **Scrape** jobs: `python main.py "your role" --remote`
3. **Get recommendations**: `python main.py --ai-recommend`
4. **Start web dashboard**: `python app.py`
5. **Set up automation** for daily scraping

---

**Questions?** Check the main [AI_MATCHING_GUIDE.md](AI_MATCHING_GUIDE.md) for more details!

**Happy job hunting! 🚀📄**
