# AI Job Matching Guide

## 🤖 Overview

The AI Job Matching system uses machine learning techniques to score and recommend jobs based on your preferences. It learns from your feedback and analyzes market demand to help you find the best opportunities.

## 🚀 Quick Start

### 1. Setup Your Preferences

```bash
python main.py --ai-setup
```

This interactive setup will ask you about:
- **Required Skills**: Must-have skills (e.g., Python, React, AWS)
- **Preferred Skills**: Nice-to-have skills
- **Remote Preference**: Remote only or flexible
- **Minimum Salary**: Annual salary threshold
- **Excluded Keywords**: Terms to avoid (e.g., junior, intern)

Your preferences are saved in `preferences.json`.

### 2. Get Recommendations

```bash
# Get top 10 recommendations
python main.py --ai-recommend

# Get 20 recommendations with minimum 70% match
python main.py --ai-recommend --display 20 --min-score 70
```

## 📊 Features

### 1. **Intelligent Scoring System**

Jobs are scored 0-100 based on multiple factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| Required Skills | 40% | Must-have skills - critical match |
| Preferred Skills | 30% | Nice-to-have skills - bonus points |
| Remote Match | 15% | Matches your remote preference |
| Salary Match | 10% | Meets your minimum salary |
| Company Preference | 5% | Preferred companies |
| Penalties | Variable | Excluded keywords/companies |

### 2. **Skills Analysis**

Analyze which skills are most in-demand:

```bash
python main.py --ai-analyze
```

Output example:
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
...
```

### 3. **Skill Learning Suggestions**

Get personalized suggestions on what to learn next:

```bash
python main.py --ai-suggest
```

Output:
```
💡 Skills You Should Learn

Based on current job market demand:

 1. kubernetes          - Found in 234 jobs
 2. typescript          - Found in 198 jobs
 3. graphql             - Found in 156 jobs
...
```

### 4. **Automatic Learning**

The system learns from your feedback:

```python
# When you mark jobs as "applied" or "interested"
# The AI learns your preferences automatically
```

## 🎯 Scoring Breakdown

When you get recommendations, each job shows:

```
🌟 85.5% - Senior Python Developer
   Company: TechCorp
   Location: Remote
   Salary: $120,000 - $150,000
   ✓ Skills: python, django, aws, docker
   ✗ Missing: kubernetes
```

Score interpretation:
- 🌟 **80-100%**: Excellent match - highly recommended
- ⭐ **60-79%**: Good match - worth considering  
- ✓ **40-59%**: Fair match - review carefully
- Below 40%: Poor match (filtered out by default)

## 🔧 Configuration

### Preferences File (`preferences.json`)

```json
{
  "required_skills": ["python", "django", "postgresql"],
  "preferred_skills": ["docker", "aws", "react"],
  "excluded_keywords": ["junior", "intern"],
  "min_salary": 120000,
  "remote_only": true,
  "experience_years": 5,
  "job_types": ["fulltime"],
  "preferred_companies": ["Google", "Microsoft"],
  "excluded_companies": ["BadCorp"]
}
```

### Manual Editing

You can manually edit `preferences.json` or update via the web dashboard.

## 🌐 Web Dashboard Integration

### View Recommendations

1. Open dashboard: `http://localhost:5000`
2. Click **"AI Recommendations"** tab
3. Adjust minimum score slider
4. View scored jobs with breakdown

### Manage Preferences

1. Click **"Preferences"** button
2. Edit skills, salary, remote preference
3. Save changes
4. Get updated recommendations instantly

### API Endpoints

```bash
# Get recommendations
GET /api/ai/recommendations?limit=10&min_score=60

# Get/Update preferences
GET /api/ai/preferences
POST /api/ai/preferences

# Analyze skills
GET /api/ai/analyze-skills

# Suggest skills
GET /api/ai/suggest-skills?limit=10

# Score specific job
GET /api/ai/score-job/123
```

## 🎓 Advanced Usage

### Custom Scoring Weights

Edit `ai_matcher.py` to adjust scoring weights:

```python
# In calculate_match_score method
max_score += 40  # Required skills weight
max_score += 30  # Preferred skills weight
max_score += 15  # Remote preference weight
# ... etc
```

### Add Custom Skills

Add industry-specific skills to the skill extraction:

```python
# In extract_skills method
skills = [
    # Add your custom skills
    'your_skill', 'another_skill',
    # ... existing skills
]
```

### Learning Rate

Control how quickly the AI learns from feedback:

```python
# In learn_from_feedback method
# Adjust how skills are added to preferences
```

## 📈 Best Practices

### 1. **Start Broad, Refine Later**

- Begin with 3-5 required skills
- Add 5-10 preferred skills
- Refine based on recommendations

### 2. **Review Low-Scoring Matches**

Sometimes good opportunities score lower:
- Hidden gems in new industries
- Growth opportunities
- Companies with strong culture

### 3. **Update Preferences Regularly**

- After learning new skills
- When changing career focus
- Based on market trends

### 4. **Use Skill Analysis**

Run `--ai-analyze` monthly to:
- Track market trends
- Identify emerging technologies
- Spot declining skills

### 5. **Combine with Filters**

```bash
# AI recommendations for specific platforms
python main.py --ai-recommend --platforms linkedin indeed

# Recent AI recommendations only
python main.py --ai-recommend --new-since-hours 48
```

## 🔍 Understanding Match Scores

### High Score (80-100%)

**What it means:**
- Matches most/all required skills
- Includes several preferred skills
- Meets salary/remote preferences
- No excluded keywords

**Action:** Apply immediately!

### Medium Score (60-79%)

**What it means:**
- Matches some required skills
- May miss a few preferences
- Still within your criteria

**Action:** Review carefully, consider growth potential

### Low Score (40-59%)

**What it means:**
- Missing key required skills
- Limited preference matches
- May have some concerns

**Action:** Only if strongly interested despite gaps

## 🐛 Troubleshooting

### No Recommendations

**Problem:** `--ai-recommend` returns no jobs

**Solutions:**
1. Lower minimum score: `--min-score 40`
2. Reduce required skills
3. Make salary more flexible
4. Scrape more jobs first

### Poor Matches

**Problem:** Recommendations don't match expectations

**Solutions:**
1. Review preferences: `cat preferences.json`
2. Re-run setup: `--ai-setup`
3. Be more specific with required skills
4. Add excluded keywords

### Missing Skills

**Problem:** Important skills not detected

**Solutions:**
1. Check skill list in `ai_matcher.py`
2. Add custom skills to extraction
3. Use skill variations (e.g., "node.js" vs "nodejs")

## 📊 Examples

### Example 1: Entry-Level Developer

```json
{
  "required_skills": ["python", "sql"],
  "preferred_skills": ["django", "react", "git"],
  "min_salary": 60000,
  "remote_only": false,
  "excluded_keywords": ["senior", "lead"]
}
```

### Example 2: Senior Full-Stack

```json
{
  "required_skills": ["javascript", "react", "node.js", "postgresql"],
  "preferred_skills": ["typescript", "docker", "aws", "graphql"],
  "min_salary": 120000,
  "remote_only": true,
  "excluded_keywords": ["junior", "intern", "contract"]
}
```

### Example 3: Data Scientist

```json
{
  "required_skills": ["python", "machine learning", "pandas"],
  "preferred_skills": ["tensorflow", "pytorch", "spark", "aws"],
  "min_salary": 100000,
  "remote_only": true,
  "excluded_keywords": ["junior", "analyst"]
}
```

## 🚀 Integration with Workflow

### Daily Workflow

1. **Morning**: Check new recommendations
   ```bash
   python main.py --ai-recommend --new-since-hours 24
   ```

2. **Apply to top matches**: Score 80%+

3. **Research medium matches**: Score 60-79%

4. **Update status** in dashboard

### Weekly Workflow

1. **Scrape new jobs**:
   ```bash
   python main.py --keywords "python developer" --remote
   ```

2. **Analyze market**:
   ```bash
   python main.py --ai-analyze
   ```

3. **Update preferences** based on trends

### Monthly Workflow

1. **Review skill suggestions**:
   ```bash
   python main.py --ai-suggest
   ```

2. **Plan learning path**

3. **Update required/preferred skills** after learning

## 🔗 Related Features

- **Database Integration**: AI uses job history for better matching
- **Email Notifications**: Get alerts for high-scoring matches
- **Web Dashboard**: Visual interface for all AI features
- **Export**: Export recommendations to CSV/JSON

## 📚 Technical Details

### Scoring Algorithm

1. **Skill Extraction**: Regex-based with 100+ tech skills
2. **Text Analysis**: Searches title + description
3. **Weighted Scoring**: Configurable weights per factor
4. **Normalization**: Final score 0-100
5. **Penalties**: Deductions for excluded terms

### Data Sources

- Job title
- Job description
- Company name
- Salary information
- Remote status
- Historical user feedback

### Machine Learning

Current implementation uses:
- **Supervised Learning**: From user feedback
- **Collaborative Filtering**: Skill co-occurrence
- **Statistical Analysis**: Market trend detection

Future enhancements:
- NLP embeddings (BERT/GPT)
- Deep learning models
- Collaborative filtering with other users

## 🎯 Tips for Best Results

1. **Be Specific**: "React" beats "frontend framework"
2. **Use Industry Terms**: Match job posting language
3. **Balance Skills**: Don't require everything
4. **Update Regularly**: Market changes fast
5. **Trust the Numbers**: High scores = good matches
6. **Give Feedback**: Mark jobs as applied/interested
7. **Check Breakdowns**: Understand why jobs scored well/poorly

## 📞 Support

For issues or questions:
1. Check this guide
2. Review `preferences.json`
3. Run with `--help` for options
4. Check logs for errors

---

**Happy job hunting! 🎯🚀**
