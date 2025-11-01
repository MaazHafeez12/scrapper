"""
Deployment preparation script for Vercel.
"""
import os
import json

def check_deployment_readiness():
    """Check if the project is ready for Vercel deployment."""
    print("🔍 Checking Vercel deployment readiness...")
    
    # Check required files
    required_files = [
        'vercel.json',
        'api/index.py',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    # Check vercel.json format
    try:
        with open('vercel.json', 'r') as f:
            vercel_config = json.load(f)
        print("✅ vercel.json is valid")
    except json.JSONDecodeError:
        print("❌ vercel.json is not valid JSON")
        return False
    
    # Check requirements.txt
    with open('requirements.txt', 'r') as f:
        requirements = f.read()
    
    # Check for problematic packages
    problematic = ['selenium', 'playwright', 'webdriver-manager', 'undetected-chromedriver']
    issues = [pkg for pkg in problematic if pkg in requirements.lower()]
    
    if issues:
        print(f"⚠️  Warning: Found browser automation packages that won't work on Vercel: {issues}")
        print("   Consider removing these for serverless deployment")
    
    print("✅ Project appears ready for Vercel deployment!")
    return True

def create_deployment_commands():
    """Generate deployment commands."""
    print("\n🚀 Deployment Commands:")
    print("=" * 50)
    
    print("1. Install Vercel CLI (if not installed):")
    print("   npm install -g vercel")
    
    print("\n2. Login to Vercel:")
    print("   vercel login")
    
    print("\n3. Deploy (from this directory):")
    print("   vercel")
    
    print("\n4. For production deployment:")
    print("   vercel --prod")
    
    print("\n🌐 Alternative: GitHub Deploy")
    print("1. Push to GitHub:")
    print("   git init")
    print("   git add .")
    print("   git commit -m 'Initial deployment'")
    print("   git push origin main")
    
    print("\n2. Import to Vercel:")
    print("   - Go to vercel.com")
    print("   - Click 'New Project'")
    print("   - Import from GitHub")

def main():
    """Main deployment check function."""
    print("🚀 Vercel Deployment Preparation")
    print("=" * 40)
    
    if check_deployment_readiness():
        create_deployment_commands()
        print("\n✅ Ready to deploy!")
        print("\nYour deployed app will be available at:")
        print("https://your-project-name.vercel.app/demo")
    else:
        print("\n❌ Please fix the issues above before deploying.")

if __name__ == "__main__":
    main()