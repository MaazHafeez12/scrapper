# Kanban Board Guide

## 🎯 Overview

The **Kanban Board** provides a visual pipeline for managing your job search. Drag and drop jobs through different stages from discovery to offer!

## 📋 Pipeline Stages

### 1. 📝 New
**Jobs you haven't acted on yet**
- Freshly scraped jobs
- Saved from searches
- Not yet reviewed

**Actions:** Review, Apply, or Reject

### 2. 📤 Applied
**Jobs you've applied to**
- Application submitted
- Waiting for response
- Tracking application status

**Actions:** Move to Interview or Rejected

### 3. 🎤 Interview
**Jobs with scheduled interviews**
- Phone screening
- Technical interviews
- In-person interviews
- Final rounds

**Actions:** Move to Offer or Rejected

### 4. 🎉 Offer
**Jobs that made you an offer**
- Offer received
- Negotiation in progress
- Decision pending

**Actions:** Accept (remove from board) or Reject

### 5. ❌ Rejected
**Jobs you declined or were rejected from**
- Not a good fit
- Rejected by company
- Offer declined
- Archive

**Actions:** Review for learning

## 🚀 Quick Start

### Access Kanban Board

```bash
# Start the dashboard
python app.py

# Open in browser
http://localhost:5000/kanban
```

### Or from List View

Click **"📋 Kanban View"** button in the header

## ✨ Features

### 1. **Drag & Drop**

**Move jobs between stages:**
1. Click and hold a job card
2. Drag to target column
3. Drop to update status
4. Auto-saves to database

**Keyboard:**
- Click card → View details → Use action buttons

### 2. **Visual Pipeline**

**Color-coded columns:**
- 🟦 New (Gray)
- 🔵 Applied (Blue)
- 🟡 Interview (Yellow)
- 🟢 Offer (Green)
- 🔴 Rejected (Red)

**Card badges:**
- 🌍 Remote jobs
- 📍 Location
- 💰 Salary
- 🤖 AI match score

### 3. **Quick Stats**

Top bar shows counts for each stage:
- 📝 New: 15
- 📤 Applied: 8
- 🎤 Interview: 3
- 🎉 Offer: 1
- ❌ Rejected: 5

### 4. **Filtering**

**Search bar:**
- Filter by keywords
- Real-time search
- Searches title, company, description

**Platform filter:**
- Filter by job platform
- Indeed, LinkedIn, etc.

**Remote filter:**
- Remote only
- On-site only
- Both

### 5. **Job Details Modal**

**Click any card to see:**
- Full description
- Company details
- AI match score breakdown
- Quick action buttons
- External job link

### 6. **Mobile Responsive**

Works on all devices:
- Desktop: 5-column layout
- Tablet: 2-3 columns
- Mobile: 1 column (scroll through stages)

## 📊 Workflow Examples

### Example 1: Daily Job Hunt

**Morning:**
1. Open Kanban board
2. Check "New" column (fresh jobs from scraping)
3. Review AI scores (focus on 75%+)
4. Drag high-matches to "Applied"

**Afternoon:**
5. Update "Applied" jobs with responses
6. Move jobs to "Interview" when scheduled

**Evening:**
7. Prepare for interviews (check "Interview" column)
8. Track offers in "Offer" column

### Example 2: Application Tracking

```
New Job Discovered
    ↓ (Drag to Applied)
Application Submitted
    ↓ (Drag to Interview after email)
Interview Scheduled
    ↓ (Drag to Interview)
Interview Completed
    ↓ (Drag to Offer if successful)
Offer Received
    ↓ (Accept or Reject)
Done!
```

### Example 3: Bulk Processing

**Weekend review:**
1. Check "New" column
2. Sort by AI score (high to low)
3. Bulk apply to 80%+ matches:
   - Drag all to "Applied"
4. Reject low matches:
   - Drag to "Rejected"

## 💡 Pro Tips

### 1. **Use AI Scores**

Cards show match scores:
- 🟢 **75%+** (Green): Apply immediately
- 🟡 **50-74%** (Yellow): Review carefully
- 🔴 **<50%** (Red): Consider rejecting

### 2. **Color Coding**

Add your own mental associations:
- Blue cards (Applied): Waiting for response
- Yellow cards (Interview): Need preparation
- Green cards (Offer): Decision needed

### 3. **Daily Routine**

**Morning (10 min):**
- Check new jobs (AI recommended)
- Quick apply to top matches

**Lunch (5 min):**
- Update interview statuses
- Check for responses

**Evening (15 min):**
- Prepare for tomorrow's interviews
- Review offers

### 4. **Column Limits**

Keep columns manageable:
- **New:** <20 jobs (archive or reject old ones)
- **Applied:** Track until response (1-2 weeks)
- **Interview:** Active interviews only
- **Offer:** Current offers only
- **Rejected:** Archive monthly

### 5. **Batch Actions**

Group similar tasks:
- **Monday:** Review all new jobs
- **Tuesday:** Follow up on applications (1 week old)
- **Wednesday:** Prepare for Thursday interviews
- **Thursday:** Interview day
- **Friday:** Review week, plan next week

## 🎨 Customization Ideas

### Add Notes (Future Enhancement)

Click "Edit" on cards to add:
- Application date
- Contact person
- Next steps
- Deadline

### Add Dates (Future Enhancement)

Track timelines:
- Applied date
- Interview date
- Offer deadline
- Response deadline

### Add Priority (Future Enhancement)

Star high-priority jobs:
- Dream companies
- High salary
- Perfect match

## 📈 Analytics

### Track Your Pipeline

**Conversion rates:**
- New → Applied: X%
- Applied → Interview: Y%
- Interview → Offer: Z%

**Time in each stage:**
- Applied → Interview: Average N days
- Interview → Offer: Average M days

**Success metrics:**
- Total offers received
- Best performing platforms
- Highest AI scores accepted

## 🔧 Technical Details

### Database Integration

Status is saved automatically:
- Changes sync to SQLite database
- Persistent across sessions
- Tracked in job_history table

### API Endpoints Used

```bash
GET  /api/jobs          # Load all jobs
POST /api/jobs/{id}/status  # Update job status
GET  /api/platforms      # Load platform list
```

### Status Values

```python
statuses = [
    'new',        # Fresh job, not reviewed
    'applied',    # Application submitted
    'interview',  # Interview scheduled
    'offer',      # Offer received
    'rejected'    # Not proceeding
]
```

## 🐛 Troubleshooting

### Cards not dragging

**Cause:** JavaScript not loaded

**Solution:**
1. Refresh page (Ctrl+R)
2. Check browser console for errors
3. Try different browser

### Status not saving

**Cause:** API error

**Solution:**
1. Check Flask app is running
2. Look for errors in terminal
3. Verify database file exists

### Cards in wrong column

**Cause:** Status mismatch

**Solution:**
1. Click card → View details
2. Use action buttons to correct status
3. Reload page

### Filters not working

**Cause:** Browser caching

**Solution:**
1. Hard refresh (Ctrl+Shift+R)
2. Clear browser cache
3. Restart Flask app

## 🎯 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Esc` | Close modal |
| `Ctrl+R` | Refresh jobs |
| `Ctrl+F` | Focus search |
| Click card | View details |

## 📱 Mobile Usage

**Touch gestures:**
- **Tap card:** View details
- **Long press:** Select for drag
- **Drag:** Move between columns
- **Swipe:** Scroll columns

**Tips for mobile:**
- Use landscape mode for better view
- Focus on one column at a time
- Use action buttons instead of drag-drop

## 🔗 Integration with Other Features

### 1. **With AI Matching**

Cards show AI match scores:
```bash
# Scrape with AI scoring
python main.py "Python Developer" --ai-recommend

# View in Kanban
# Cards automatically show match %
```

### 2. **With Notifications**

Get notified when:
- New high-score jobs arrive (email)
- Interview reminders (webhook)
- Offer deadlines (email)

### 3. **With Resume Parser**

```bash
# Parse resume for preferences
python main.py --parse-resume resume.pdf

# Scrape matching jobs
python main.py "Developer" --remote

# Manage in Kanban
# High-scoring jobs automatically prioritized
```

### 4. **With Database**

Full history tracking:
- Status change history
- Time in each stage
- Application timeline
- Success analytics

## 📊 Best Practices

### 1. **Keep It Clean**

- Archive old "New" jobs (> 2 weeks)
- Move old "Applied" to "Rejected" after 2 weeks no response
- Clear "Rejected" monthly

### 2. **Be Realistic**

- Don't apply to everything
- Focus on 70%+ AI matches
- Quality over quantity

### 3. **Track Everything**

- Move cards as soon as status changes
- Keep pipeline current
- Review weekly

### 4. **Use as Dashboard**

- Check daily (like checking email)
- Update after each interaction
- Visual reminder of progress

### 5. **Celebrate Wins**

- Watch "Offer" column grow
- Track your success rate
- Learn from rejections

## 🎊 Success Stories

### "The Visual Advantage"

> "Seeing all my jobs in one place changed everything. I could see I was stuck with too many applications and no interviews. I adjusted my strategy, focused on better matches, and got 3 interviews in 2 weeks!"

### "The Pipeline Power"

> "The Kanban board helped me realize I was applying but not following up. Now I track everything and follow up at the right time. My interview rate doubled!"

### "The Quick Win"

> "I can process 20 new jobs in 10 minutes now. Drag high-scoring ones to Applied, reject low scores, and move on. So much faster than my old spreadsheet!"

## 🚀 Next Steps

1. **Start using Kanban board** instead of list view
2. **Develop your routine** (morning review, evening updates)
3. **Track your metrics** (conversion rates, time in stages)
4. **Optimize your pipeline** (find bottlenecks, improve process)
5. **Celebrate successes** (track offers, analyze what works)

## 📚 Related Documentation

- **[DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md)** - Main dashboard features
- **[AI_MATCHING_GUIDE.md](AI_MATCHING_GUIDE.md)** - AI scoring system
- **[DATABASE_GUIDE.md](DATABASE_GUIDE.md)** - Data tracking
- **[CHEATSHEET.md](CHEATSHEET.md)** - Quick commands

---

**Happy job hunting with visual pipeline management! 📋🚀**
