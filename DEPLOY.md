# Job Scraper - Vercel Deployment Guide 🚀

Deploy your job scraper web dashboard to Vercel for free!

## 🚀 Quick Deploy to Vercel

### Option 1: Deploy with Vercel CLI (Recommended)

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy from project directory:**
   ```bash
   cd D:\Scrapper\scrapper
   vercel
   ```

4. **Follow the prompts:**
   - Project name: `job-scraper-dashboard`
   - Deploy: `Yes`
   - Framework: `Other`

### Option 2: Deploy via GitHub

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/job-scraper.git
   git push -u origin main
   ```

2. **Import to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Vercel will auto-detect the configuration

## 📁 Deployment Files

The following files are configured for Vercel deployment:

- `vercel.json` - Vercel configuration
- `api/index.py` - Main Flask application (serverless function)
- `requirements.txt` - Python dependencies
- Sample data included for demo

## 🌐 Features Available After Deployment

- **📊 Job Statistics Dashboard** - View job counts and metrics
- **💼 Job Listings** - Browse and filter jobs
- **📥 Export Functionality** - Download jobs as CSV
- **📱 Mobile Responsive** - Works on all devices
- **⚡ Fast Performance** - Serverless deployment

## 🔧 Configuration

### Environment Variables (Optional)

Set these in Vercel dashboard for production:

```bash
SECRET_KEY=your-secret-key-here
```

### Custom Domain (Optional)

1. Go to your Vercel project dashboard
2. Click "Domains"
3. Add your custom domain
4. Follow DNS configuration instructions

## 🎯 Demo

Your deployed app will include:
- Sample job data for demonstration
- All API endpoints working
- Interactive dashboard
- Export functionality

## 🔄 Updates

To update your deployment:

```bash
# Make changes to your code
git add .
git commit -m "Update description"
git push

# Or with Vercel CLI
vercel --prod
```

## 🐛 Troubleshooting

### Common Issues:

1. **Build Failed:**
   - Check `requirements.txt` has correct dependencies
   - Ensure no browser automation packages (selenium, playwright)

2. **Function Timeout:**
   - Vercel free tier has 10s function timeout
   - Heavy scraping should be done separately

3. **Memory Limits:**
   - Keep data processing lightweight
   - Use external database for large datasets

## 📚 Next Steps

After deployment:

1. **Add Real Database:**
   - Use Vercel Postgres, MongoDB Atlas, or Supabase
   - Replace sample data with real job storage

2. **Add Authentication:**
   - Implement user login/signup
   - Protect sensitive endpoints

3. **Add Real Scraping:**
   - Set up scheduled jobs with GitHub Actions
   - Use external APIs for job data

4. **Custom Features:**
   - Add job alerts
   - Implement favorites
   - Add notes and tracking

## 🎉 Success!

Once deployed, you'll have a live job dashboard at:
`https://your-project-name.vercel.app`

Share your dashboard URL and start managing jobs online! 🚀