# AI Job Matching Examples

## Quick Start Examples

### Example 1: Full-Stack Developer

**Setup preferences:**
```bash
python main.py --ai-setup
```

**When prompted, enter:**
```
Required skills: Python, JavaScript, React
Preferred skills: Docker, AWS, PostgreSQL, TypeScript
Remote only: y
Minimum salary: 100000
Excluded keywords: junior, intern
```

**Get recommendations:**
```bash
python main.py --ai-recommend
```

**Expected output:**
```
🤖 AI Job Recommendations (min score: 60)

🌟 87.5% - Senior Full Stack Engineer
   Company: TechStartup Inc
   Location: Remote
   Salary: $120,000 - $160,000
   Remote: Yes
   Platform: LinkedIn
   ✓ Skills: python, javascript, react, docker, aws
   ✗ Missing: None

⭐ 73.2% - Full Stack Developer
   Company: Digital Solutions
   Location: San Francisco, CA
   Salary: $110,000 - $140,000
   Remote: Yes
   Platform: Indeed
   ✓ Skills: python, react, postgresql
   ✗ Missing: docker, aws
```

### Example 2: Data Scientist

**Preferences file (preferences.json):**
```json
{
  "required_skills": ["python", "machine learning", "pandas"],
  "preferred_skills": ["tensorflow", "pytorch", "spark", "aws", "sql"],
  "excluded_keywords": ["junior", "analyst", "intern"],
  "min_salary": 120000,
  "remote_only": true,
  "job_types": ["fulltime"],
  "preferred_companies": ["Google", "Microsoft", "Amazon"],
  "excluded_companies": []
}
```

**Commands:**
```bash
# Scrape jobs
python main.py "data scientist" --remote --platforms indeed linkedin

# Get AI recommendations
python main.py --ai-recommend --min-score 70

# Analyze what skills are hot
python main.py --ai-analyze

# See what you should learn next
python main.py --ai-suggest
```

### Example 3: DevOps Engineer

**Quick setup:**
```bash
# Use example file
copy preferences.example.json preferences.json

# Edit with your skills (or use text editor)
```

**Edit preferences.json:**
```json
{
  "required_skills": ["docker", "kubernetes", "aws"],
  "preferred_skills": ["terraform", "ansible", "jenkins", "python", "linux"],
  "excluded_keywords": ["junior", "entry-level"],
  "min_salary": 110000,
  "remote_only": false,
  "job_types": ["fulltime"],
  "preferred_companies": [],
  "excluded_companies": []
}
```

**Usage:**
```bash
# Scrape DevOps jobs
python main.py "devops engineer" --platforms indeed linkedin glassdoor

# Get top 20 matches
python main.py --ai-recommend --display 20 --min-score 60

# Only show excellent matches (80%+)
python main.py --ai-recommend --min-score 80
```

### Example 4: Frontend Developer

**Interactive setup:**
```bash
python main.py --ai-setup
```

**Enter:**
- Required: `react, javascript, html, css`
- Preferred: `typescript, next.js, tailwind, figma`
- Remote: `y`
- Salary: `90000`
- Excluded: `backend, full-stack, senior`

**Daily workflow:**
```bash
# Morning: Check new jobs
python main.py "frontend developer" --remote --show-new-only

# Get AI recommendations for new jobs
python main.py --ai-recommend --new-since-hours 24

# Apply to top 3 matches (80%+ score)
python main.py --ai-recommend --min-score 80 --display 3
```

## Advanced Examples

### Example 5: Multiple Roles

**Create multiple preference files:**

**preferences_senior.json:**
```json
{
  "required_skills": ["python", "django", "postgresql", "aws"],
  "preferred_skills": ["docker", "kubernetes", "react"],
  "min_salary": 140000,
  "remote_only": true,
  "excluded_keywords": ["junior", "mid-level"]
}
```

**preferences_consultant.json:**
```json
{
  "required_skills": ["python", "architecture", "leadership"],
  "preferred_skills": ["microservices", "system design", "mentoring"],
  "min_salary": 160000,
  "remote_only": false,
  "job_types": ["contract", "fulltime"]
}
```

**Usage:**
```bash
# Use senior developer preferences
copy preferences_senior.json preferences.json
python main.py --ai-recommend

# Switch to consultant preferences
copy preferences_consultant.json preferences.json
python main.py --ai-recommend
```

### Example 6: Market Research

**Analyze current market:**
```bash
# Scrape broad search
python main.py "software engineer" --platforms indeed linkedin glassdoor

# See what skills are in demand
python main.py --ai-analyze
```

**Output:**
```
📊 Skills Demand Analysis

Total jobs analyzed: 1,234
Unique skills found: 87

Top 20 Most In-Demand Skills:

 1. python              -  456 jobs (37.0%)
 2. javascript          -  398 jobs (32.3%)
 3. react               -  345 jobs (28.0%)
 4. aws                 -  298 jobs (24.1%)
 5. docker              -  267 jobs (21.6%)
 6. kubernetes          -  234 jobs (19.0%)
 7. postgresql          -  221 jobs (17.9%)
 8. typescript          -  198 jobs (16.0%)
 9. node.js             -  187 jobs (15.2%)
10. git                 -  176 jobs (14.3%)
```

**See what to learn:**
```bash
python main.py --ai-suggest
```

**Output:**
```
💡 Skills You Should Learn

Based on current job market demand:

 1. kubernetes          - Found in 234 jobs
 2. typescript          - Found in 198 jobs
 3. graphql             - Found in 156 jobs
 4. terraform           - Found in 143 jobs
 5. mongodb             - Found in 128 jobs
```

### Example 7: Automated Job Hunt

**Windows Task Scheduler setup:**

**Task 1: Morning scrape (8 AM daily)**
```
Program: python
Arguments: main.py "Python Developer" --remote --show-new-only --email-notify
Start in: D:\Scrapper
```

**Task 2: AI recommendations (8:30 AM daily)**
```
Program: python
Arguments: main.py --ai-recommend --min-score 75 --email-notify
Start in: D:\Scrapper
```

**Task 3: Daily digest (9 AM daily)**
```
Program: python
Arguments: main.py --send-digest
Start in: D:\Scrapper
```

**Result:** Wake up to an email with new jobs and AI recommendations!

### Example 8: Team/Multiple Users

**Different preference files for different team members:**

```bash
# Alice (Senior Python Dev)
copy preferences_alice.json preferences.json
python main.py --ai-recommend --export csv
# Sends recommendations to alice@company.com

# Bob (Junior React Dev)
copy preferences_bob.json preferences.json
python main.py --ai-recommend --export csv
# Sends recommendations to bob@company.com
```

### Example 9: Web Dashboard Usage

**Start dashboard:**
```bash
python app.py
```

**Visit:** http://localhost:5000

**Workflow:**
1. Click "AI Recommendations" button
2. Adjust minimum score slider (60%, 70%, 80%)
3. View scored jobs with color-coded badges
4. Click job card to see detailed breakdown
5. Quick action: Mark as "Interested" or "Applied"
6. Export top matches to CSV

**API usage (for custom integrations):**
```bash
# Get recommendations via API
curl http://localhost:5000/api/ai/recommendations?limit=10&min_score=70

# Update preferences via API
curl -X POST http://localhost:5000/api/ai/preferences \
  -H "Content-Type: application/json" \
  -d '{"required_skills": ["python", "django"]}'

# Get skills analysis
curl http://localhost:5000/api/ai/analyze-skills

# Score specific job
curl http://localhost:5000/api/ai/score-job/123
```

### Example 10: Career Planning

**Step 1: Current state analysis**
```bash
# See what you match now
python main.py --ai-recommend --min-score 60
```

**Step 2: Future state planning**
```bash
# See what skills are valuable
python main.py --ai-analyze

# Get learning suggestions
python main.py --ai-suggest
```

**Step 3: Track progress**
```bash
# After 3 months of learning Kubernetes
# Add to your preferred_skills
# Re-run recommendations
python main.py --ai-recommend

# Compare: Are you matching more jobs now?
# Is average score higher?
```

## Scoring Interpretation

### 🌟 90-100% - Perfect Match
- Has ALL required skills
- Has MOST preferred skills
- Meets all criteria
- **Action:** Apply immediately!

### 🌟 80-89% - Excellent Match
- Has all/most required skills
- Has several preferred skills
- Matches main criteria
- **Action:** Definitely apply

### ⭐ 70-79% - Very Good Match
- Has most required skills
- Has some preferred skills
- Meets key criteria
- **Action:** Strong consideration

### ⭐ 60-69% - Good Match
- Has some required skills
- Limited preferred skills
- Meets basic criteria
- **Action:** Review carefully

### ✓ 50-59% - Fair Match
- Missing several requirements
- Few preferred skills
- **Action:** Only if very interested

### ❌ <50% - Poor Match
- Missing most requirements
- Doesn't meet criteria
- **Action:** Skip (filtered out by default)

## Tips for Best Results

### 1. Start Conservative
```json
{
  "required_skills": ["python", "sql"],  // Only 2-3 essentials
  "preferred_skills": ["django", "react", "aws", "docker"],  // 5-10 nice-to-haves
  "min_salary": 80000  // Realistic minimum
}
```

### 2. Iterate Based on Results
```bash
# If getting no matches (too strict)
# - Reduce required skills
# - Lower min_salary
# - Set remote_only to false

# If getting too many matches (too loose)
# - Add more required skills
# - Increase min_score threshold
# - Add excluded keywords
```

### 3. Use Excluded Keywords Wisely
```json
{
  "excluded_keywords": [
    "junior",      // If you're senior
    "senior",      // If you're junior
    "lead",        // If not ready for leadership
    "manager",     // If prefer IC roles
    "on-site",     // If remote only
    "contract",    // If want fulltime
    "clearance"    // If don't have security clearance
  ]
}
```

### 4. Monitor Market Trends
```bash
# Monthly: Check what's hot
python main.py --ai-analyze

# Quarterly: Update your skills
# Add newly learned skills to required/preferred

# Yearly: Reassess career goals
# Update preferences to match new direction
```

### 5. Combine with Notifications
```bash
# Get alerted for excellent matches only
python main.py "Python Developer" --remote --ai-recommend --min-score 85 --email-notify

# Daily digest with AI scores
python main.py --send-digest
# (Edit notifications.py to include AI scores in digest)
```

## Troubleshooting

### Issue: No recommendations found

**Solution 1:** Lower threshold
```bash
python main.py --ai-recommend --min-score 30
```

**Solution 2:** Check preferences
```bash
# View current preferences
cat preferences.json

# Make sure they're not too strict
```

**Solution 3:** Scrape more jobs first
```bash
python main.py "your role" --platforms indeed linkedin glassdoor remoteok
```

### Issue: All scores are low

**Cause:** Required skills too specific or numerous

**Solution:**
```json
{
  "required_skills": ["python"],  // Keep only 1-2 essentials
  "preferred_skills": ["django", "flask", "fastapi", "sqlalchemy"]  // Move others here
}
```

### Issue: Skills not being detected

**Check:** Is the skill in the detection list?
- Open `ai_matcher.py`
- Search for the skill in `extract_skills()` method
- Add your skill if missing

**Alternative:** Use variations
```json
{
  "required_skills": [
    "node.js",   // Try this
    "nodejs",    // Or this
    "node"       // Or this
  ]
}
```

## Integration Examples

### With Slack Notifications
```bash
# Get high-scoring matches and notify Slack
python main.py "Software Engineer" --remote --ai-recommend --min-score 80 --webhook-notify
```

### With Excel Export
```bash
# Export top recommendations to Excel
python main.py --ai-recommend --min-score 70 --export excel
```

### With Database Search
```bash
# Score existing database jobs
python main.py --search-db "Python" --ai-recommend
```

---

**Happy job hunting with AI! 🤖🚀**

For more details, see:
- `AI_MATCHING_GUIDE.md` - Complete guide
- `README.md` - Overview
- `PROGRESS_UPDATE.md` - Feature status
