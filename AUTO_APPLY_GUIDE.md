# 🤖 Job Application Automation Guide

Automatically apply to jobs using browser automation. Fill forms, attach resumes, and track applications—all automatically!

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Setup](#setup)
- [Usage](#usage)
- [Features](#features)
- [Safety & Best Practices](#safety--best-practices)
- [Platform Compatibility](#platform-compatibility)
- [Troubleshooting](#troubleshooting)
- [Legal Considerations](#legal-considerations)

---

## Overview

The Auto-Apply system automatically fills job application forms using browser automation (Selenium or Playwright). It can:

✅ **Auto-fill personal information** (name, email, phone, address)
✅ **Upload documents** (resume, cover letter)
✅ **Handle multi-page forms** with smart navigation
✅ **Detect CAPTCHAs** and pause for manual solving
✅ **Track success/failure** in database
✅ **Work with AI recommendations** for targeted applications
✅ **Dry-run mode** for testing without actual submission
✅ **Smart retry logic** and error recovery

---

## Quick Start

### 1. Install Dependencies

```bash
# Selenium (default - stable)
pip install selenium webdriver-manager

# OR Playwright (faster, modern)
pip install playwright
python -m playwright install chromium
```

### 2. Setup Application Template

```bash
python main.py --auto-apply-setup
```

Follow the prompts to enter:
- Personal info (name, email, phone, address)
- Resume file path
- Professional links (LinkedIn, GitHub, portfolio)
- Work authorization details

### 3. Test with Dry Run

```bash
# Test without actually submitting
python main.py --auto-apply --dry-run --max-applications 2 --show-browser
```

### 4. Start Auto-Applying

```bash
# Apply to new jobs
python main.py --auto-apply --max-applications 10

# Apply to AI-recommended jobs (score > 80%)
python main.py --auto-apply --ai-recommend --min-score 80 --max-applications 5
```

---

## Setup

### Application Template

The template stores your information in `application_templates.json`. Required fields:

**Personal Information:**
- First name, Last name
- Email, Phone
- Address (optional but recommended)
- City, State, ZIP code

**Professional Information:**
- Resume path (absolute or relative)
- Cover letter path (optional)
- LinkedIn URL
- GitHub URL
- Portfolio/website URL

**Work Authorization:**
- Authorized to work (Yes/No)
- Require sponsorship (Yes/No)
- Visa status

### Example Template

```json
{
  "personal_info": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@email.com",
    "phone": "(555) 123-4567",
    "address": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "zip_code": "94102"
  },
  "professional_info": {
    "resume_path": "resume.pdf",
    "cover_letter_path": "cover_letter.pdf",
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "github_url": "https://github.com/johndoe",
    "portfolio_url": "https://johndoe.com"
  },
  "work_authorization": {
    "authorized_to_work": "Yes",
    "require_sponsorship": "No"
  }
}
```

### Edit Template Manually

```bash
# Edit the JSON file directly
notepad application_templates.json

# OR run setup again
python main.py --auto-apply-setup
```

---

## Usage

### Basic Commands

**Setup template:**
```bash
python main.py --auto-apply-setup
```

**Auto-apply to new jobs:**
```bash
python main.py --auto-apply --max-applications 10
```

**Dry run (test mode):**
```bash
python main.py --auto-apply --dry-run --show-browser
```

**Apply to AI-recommended jobs:**
```bash
python main.py --auto-apply --ai-recommend --min-score 75 --max-applications 5
```

**Apply to specific platforms:**
```bash
python main.py --auto-apply --platforms indeed remoteok --max-applications 10
```

**Use Playwright (faster):**
```bash
python main.py --auto-apply --use-playwright --max-applications 10
```

**Show browser window:**
```bash
python main.py --auto-apply --show-browser
```

**Custom delay between applications:**
```bash
python main.py --auto-apply --apply-delay 15 --max-applications 10
```

### Advanced Usage

**Combine with scraping:**
```bash
# Scrape jobs, then auto-apply to best matches
python main.py "Python Developer" --remote --platforms indeed remoteok
python main.py --auto-apply --ai-recommend --min-score 80 --max-applications 5
```

**Scheduled auto-apply:**
```bash
# Windows Task Scheduler - Every 6 hours
python main.py --show-new-only --new-since-hours 6
python main.py --auto-apply --ai-recommend --min-score 75 --max-applications 3 --email-notify
```

**High-quality applications only:**
```bash
python main.py --auto-apply --ai-recommend --min-score 90 --max-applications 2 --show-browser
```

---

## Features

### 🎯 Smart Form Filling

The system automatically detects and fills common form fields:

**Personal Fields:**
- First name, Last name, Full name
- Email address
- Phone number
- Address, City, State, ZIP code

**Professional Fields:**
- LinkedIn profile URL
- GitHub profile URL
- Portfolio/website URL
- Resume upload
- Cover letter upload

**Field Detection:**
- Matches multiple name patterns (firstname, first_name, fname, etc.)
- Case-insensitive matching
- Handles various form layouts

### 🔒 Safety Features

**CAPTCHA Detection:**
- Automatically detects CAPTCHAs
- Pauses and waits for manual solving (120s timeout)
- Continues once solved

**Dry Run Mode:**
- Test without submitting
- See what would be filled
- Verify form detection

**Application Limits:**
- Max applications per session (default: 10)
- Prevents accidental mass-applying
- Customizable limits

**Delays:**
- Delay between applications (default: 10s)
- Prevents rate limiting
- Respects website resources

**Confirmation:**
- Asks for confirmation before starting (non-dry-run)
- Clear session summary
- Shows what will happen

### 📊 Tracking & Reporting

**Database Integration:**
- Automatically updates job status to 'applied'
- Adds timestamp and notes
- Tracks application attempts

**Session Statistics:**
- Successful applications count
- Failed applications count
- CAPTCHAs encountered
- Errors with details

**Email Notifications:**
- Session summary via email
- Include with `--email-notify`
- Shows success/failure counts

---

## Safety & Best Practices

### ⚠️ Important Safety Guidelines

1. **Start with Dry Run**
   ```bash
   python main.py --auto-apply --dry-run --show-browser --max-applications 2
   ```
   - Test before actual submissions
   - Verify form filling works correctly
   - Check for any issues

2. **Use Low Application Limits**
   ```bash
   # Start with 3-5 applications max
   python main.py --auto-apply --max-applications 5
   ```
   - Don't mass-apply to hundreds of jobs
   - Quality over quantity
   - Avoid triggering anti-bot measures

3. **Increase Delays**
   ```bash
   python main.py --auto-apply --apply-delay 15
   ```
   - Use 15-30 second delays
   - Appears more human-like
   - Reduces detection risk

4. **Use AI Filtering**
   ```bash
   python main.py --auto-apply --ai-recommend --min-score 80
   ```
   - Only apply to well-matched jobs
   - Higher quality applications
   - Better response rates

5. **Monitor Applications**
   - Watch browser window (use `--show-browser`)
   - Check email confirmations
   - Review database status
   - Follow up manually

6. **Customize Applications**
   - Tailor resume for each role
   - Review applications manually when possible
   - Auto-apply is for speed, not replacement

### 🎯 Best Practices

**DO:**
- ✅ Use for high-volume, simple applications (Indeed, RemoteOK)
- ✅ Apply to jobs that match your skills (AI recommendations)
- ✅ Keep resume and info up-to-date
- ✅ Follow up on applications manually
- ✅ Track which jobs you applied to
- ✅ Use realistic personal information

**DON'T:**
- ❌ Apply to 100+ jobs per session
- ❌ Apply to unrelated positions
- ❌ Use on platforms with complex applications
- ❌ Ignore CAPTCHAs (solve them!)
- ❌ Use fake information
- ❌ Rely 100% on automation (manual review is better)

---

## Platform Compatibility

### ✅ Works Well With

**Indeed** ⭐⭐⭐⭐⭐
- Simple "Quick Apply" forms
- Standard fields
- High success rate

**RemoteOK** ⭐⭐⭐⭐⭐
- Straightforward applications
- Email-based apply
- Reliable

**SimplyHired** ⭐⭐⭐⭐
- Standard form fields
- Good compatibility

**ZipRecruiter** ⭐⭐⭐
- Varies by job posting
- Some have simple forms

### ⚠️ Limited Support

**LinkedIn** ⭐⭐
- Requires login
- "Easy Apply" might work
- Often has multi-step processes
- May require manual intervention

**Glassdoor** ⭐⭐
- Redirects to company sites
- Inconsistent form layouts
- Lower success rate

**Monster** ⭐⭐
- Account required
- Complex forms
- Use cautiously

### ❌ Not Recommended

**Company Career Pages**
- Highly customized forms
- Multi-page applications
- Behavioral questions
- Assessment tests
- Video introductions

**Platforms with:**
- Complex screening questions
- Long essay answers
- Skills assessments
- Video interviews
- Multi-stage applications

---

## Troubleshooting

### Common Issues

**Issue: "Template incomplete" error**
```
Solution:
1. Run: python main.py --auto-apply-setup
2. Fill all required fields
3. Verify resume file exists at specified path
```

**Issue: "Could not find apply button"**
```
Solution:
1. Use --show-browser to see what's happening
2. Platform may have non-standard buttons
3. Manual application may be required
4. Try --dry-run to test form filling
```

**Issue: "Failed to fill [field]"**
```
Solution:
1. Form field may have unusual naming
2. Check browser window for actual field names
3. Platform may not be compatible
4. Consider manual application
```

**Issue: CAPTCHA timeout**
```
Solution:
1. Solve CAPTCHA when prompted (120s timeout)
2. Use --show-browser to see CAPTCHA
3. Reduce application speed to avoid CAPTCHAs
4. Increase --apply-delay
```

**Issue: High failure rate**
```
Solution:
1. Use --dry-run first to test
2. Check platform compatibility
3. Verify template information is correct
4. Try different platforms
5. Consider manual applications
```

**Issue: Browser doesn't start**
```
Solution:
# For Selenium:
pip install --upgrade selenium webdriver-manager

# For Playwright:
pip install playwright
python -m playwright install chromium
```

**Issue: "Selenium not installed"**
```
Solution:
pip install selenium webdriver-manager
```

**Issue: "Playwright not installed"**
```
Solution:
pip install playwright
python -m playwright install chromium
```

### Debug Mode

**Show browser window:**
```bash
python main.py --auto-apply --show-browser --max-applications 1
```

**Use dry run:**
```bash
python main.py --auto-apply --dry-run --show-browser
```

**Check single job:**
```bash
python auto_apply.py --test --url "https://job-url" --dry-run --visible
```

**Check template:**
```bash
python -c "from auto_apply import ApplicationTemplate; t=ApplicationTemplate(); print(t.is_complete())"
```

---

## Legal Considerations

### ⚖️ Terms of Service

**Important:** Many job platforms have Terms of Service that prohibit automated tools. Auto-apply is provided for:

- **Educational purposes** - Learning automation
- **Personal use** - Speed up your own job search
- **Convenience** - Simple form filling assistance

**You are responsible for:**
- ✅ Reading and following platform Terms of Service
- ✅ Using the tool ethically and responsibly
- ✅ Not violating platform policies
- ✅ Providing accurate information
- ✅ Following up on applications

### 📜 Disclaimer

This tool is provided "as is" without warranties. Use at your own risk. The authors are not responsible for:
- Account suspensions or bans
- Policy violations
- Application quality
- Job outcomes
- Any damages or losses

**Recommendation:** Use auto-apply sparingly for simple, high-volume applications. For important applications, apply manually with customized materials.

### 🎯 Ethical Use

**Be Respectful:**
- Don't overload platforms with requests
- Use reasonable delays (10-30 seconds)
- Limit applications per session (5-10 max)
- Solve CAPTCHAs when requested
- Provide genuine interest in positions

**Be Honest:**
- Use accurate personal information
- Don't apply to completely unrelated jobs
- Tailor resume for each role type
- Follow up on applications
- Withdraw if not interested

---

## Examples

### Example 1: Conservative Approach

```bash
# Setup template
python main.py --auto-apply-setup

# Test with dry run
python main.py --auto-apply --dry-run --max-applications 2 --show-browser

# Apply to 3 best matches only
python main.py --auto-apply --ai-recommend --min-score 85 --max-applications 3 --apply-delay 20
```

### Example 2: Targeted Campaign

```bash
# Scrape Python jobs
python main.py "Python Developer" --remote --platforms indeed remoteok

# Get AI recommendations
python main.py --ai-recommend --min-score 75

# Auto-apply to top matches with email notification
python main.py --auto-apply --ai-recommend --min-score 80 --max-applications 5 --email-notify
```

### Example 3: Daily Routine

```bash
# Morning: Check new jobs
python main.py --show-new-only --new-since-hours 24

# Review AI recommendations
python main.py --ai-recommend --min-score 70

# Auto-apply to best new matches (dry run first!)
python main.py --auto-apply --show-new-only --ai-recommend --min-score 85 --max-applications 3 --dry-run

# If looks good, run for real
python main.py --auto-apply --show-new-only --ai-recommend --min-score 85 --max-applications 3
```

### Example 4: Platform-Specific

```bash
# Indeed only (good compatibility)
python main.py "Software Engineer" --platforms indeed --remote
python main.py --auto-apply --platforms indeed --max-applications 10

# RemoteOK only (excellent compatibility)
python main.py "Remote Developer" --platforms remoteok
python main.py --auto-apply --platforms remoteok --max-applications 8
```

---

## API Reference

### Command Line Options

```
--auto-apply-setup          Setup application template (interactive)
--auto-apply                Start auto-applying to jobs
--max-applications N        Max applications per session (default: 10)
--apply-delay N             Delay between applications in seconds (default: 10)
--dry-run                   Test mode without actual submission
--use-playwright            Use Playwright instead of Selenium
--show-browser              Show browser window (non-headless)

# Combine with:
--ai-recommend              Apply to AI-recommended jobs only
--min-score N               Minimum AI match score (default: 60)
--show-new-only             Apply to new jobs only
--platforms P [P ...]       Apply to specific platforms
--email-notify              Send email notification when done
```

### Python API

```python
from auto_apply import AutoApplier, ApplicationTemplate

# Load template
template = ApplicationTemplate()

# Check if complete
is_complete, missing = template.is_complete()

# Apply to jobs
with AutoApplier(template, headless=True, dry_run=False) as applier:
    jobs = [
        {'url': 'https://...', 'title': 'Job 1', 'company': 'Company A'},
        {'url': 'https://...', 'title': 'Job 2', 'company': 'Company B'}
    ]
    
    stats = applier.apply_to_jobs(
        jobs,
        max_applications=10,
        delay_between=10
    )
    
    print(f"Applied: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
```

---

## FAQ

**Q: Is this safe to use?**
A: Use responsibly. Start with dry-run mode, apply to few jobs, and follow platform Terms of Service.

**Q: Will I get banned?**
A: Possible if you overuse it. Keep sessions small (5-10 apps), use delays, and don't abuse.

**Q: Which platforms work best?**
A: Indeed and RemoteOK have simple forms and work well. LinkedIn and Glassdoor are less reliable.

**Q: Can it handle complex applications?**
A: No. It works for simple forms. For complex applications with essays, assessments, or multiple pages, apply manually.

**Q: What about CAPTCHAs?**
A: The tool detects CAPTCHAs and pauses. You solve it manually (120s timeout), then it continues.

**Q: How do I track applications?**
A: Check database: `python db_manager.py search --status applied`

**Q: Should I use this for important jobs?**
A: No. Use for high-volume, quick applications. Apply manually to important/dream jobs with customized materials.

**Q: Can I customize per job?**
A: Not automatically. The tool uses one template. For customization, apply manually or edit template between applications.

**Q: Selenium vs Playwright?**
A: Selenium is more stable (default). Playwright is faster and more modern. Try both.

**Q: Does it work offline?**
A: No, needs internet connection to access job sites.

---

## Support

**Issues?** Check:
1. Template is complete: `python main.py --auto-apply-setup`
2. Dependencies installed: Selenium or Playwright
3. Resume file exists and path is correct
4. Platform compatibility (see above)
5. Try with `--dry-run --show-browser` to debug

**Still stuck?** See troubleshooting section above or review error messages carefully.

---

## Summary

🤖 **Auto-apply makes job hunting faster, but not a replacement for thoughtful applications.**

**Use it for:**
- High-volume, simple applications
- Jobs with quick apply buttons
- Platforms like Indeed, RemoteOK
- Saving time on repetitive form-filling

**Don't use it for:**
- Dream jobs or important positions
- Complex applications
- Positions requiring customization
- Platforms with strict anti-automation policies

**Always:**
- Start with dry-run mode
- Keep limits low (5-10 max)
- Use AI filtering for quality matches
- Follow up on applications manually
- Review and customize when possible
- Use ethically and responsibly

**Happy (responsible) job hunting! 🚀**
