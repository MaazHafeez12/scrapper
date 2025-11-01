"""Email notification setup helper."""
import os
import getpass
from pathlib import Path

def setup_email_notifications():
    """Interactive setup for email notifications."""
    print("📧 Email Notifications Setup")
    print("=" * 50)
    
    # Get email provider choice
    print("\nChoose your email provider:")
    print("1. Gmail (recommended)")
    print("2. Outlook/Hotmail")
    print("3. Yahoo Mail")
    print("4. Custom SMTP server")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    # Configure SMTP settings based on choice
    if choice == "1":
        smtp_server = "smtp.gmail.com"
        smtp_port = "587"
        print("\n📝 Gmail Setup Instructions:")
        print("1. Enable 2-Factor Authentication on your Google account")
        print("2. Go to Google Account settings > Security > App passwords")
        print("3. Generate an 'App Password' for this application")
        print("4. Use the app password below (not your regular password)")
    elif choice == "2":
        smtp_server = "smtp-mail.outlook.com"
        smtp_port = "587"
        print("\n📝 Outlook Setup Instructions:")
        print("1. Use your regular Outlook email and password")
        print("2. Make sure 'Less secure app access' is enabled if needed")
    elif choice == "3":
        smtp_server = "smtp.mail.yahoo.com"
        smtp_port = "587"
        print("\n📝 Yahoo Setup Instructions:")
        print("1. Enable 2-Factor Authentication")
        print("2. Generate an 'App Password'")
        print("3. Use the app password below")
    else:
        smtp_server = input("Enter SMTP server: ").strip()
        smtp_port = input("Enter SMTP port (usually 587): ").strip()
    
    # Get email credentials
    print("\n📧 Email Configuration:")
    sender_email = input("Your email address: ").strip()
    sender_password = getpass.getpass("Your password/app-password: ")
    recipient_email = input("Recipient email (press Enter for same): ").strip()
    
    if not recipient_email:
        recipient_email = sender_email
    
    # Update .env file
    env_path = Path(".env")
    env_content = env_path.read_text() if env_path.exists() else ""
    
    # Update or add email settings
    lines = env_content.split('\n')
    updated_lines = []
    email_settings = {
        'SMTP_SERVER': smtp_server,
        'SMTP_PORT': smtp_port,
        'SENDER_EMAIL': sender_email,
        'SENDER_PASSWORD': sender_password,
        'RECIPIENT_EMAIL': recipient_email,
        'EMAIL_ENABLED': 'true'
    }
    
    # Update existing lines or add new ones
    for line in lines:
        found = False
        for key, value in email_settings.items():
            if line.startswith(f"{key}="):
                updated_lines.append(f"{key}={value}")
                email_settings.pop(key)
                found = True
                break
        if not found:
            updated_lines.append(line)
    
    # Add any remaining settings
    for key, value in email_settings.items():
        updated_lines.append(f"{key}={value}")
    
    # Write back to .env
    env_path.write_text('\n'.join(updated_lines))
    
    print("\n✅ Email configuration saved to .env file!")
    print("\n🧪 Test your email setup:")
    print("python main.py --send-digest --email-notify")
    
    return True

def setup_webhook_notifications():
    """Setup webhook notifications for Slack/Discord."""
    print("\n🔗 Webhook Notifications Setup")
    print("=" * 50)
    
    print("\nChoose webhook type:")
    print("1. Slack")
    print("2. Discord")
    print("3. Generic webhook")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        webhook_type = "slack"
        print("\n📝 Slack Setup Instructions:")
        print("1. Go to your Slack workspace")
        print("2. Apps > Incoming Webhooks > Add to Slack")
        print("3. Choose channel and copy webhook URL")
    elif choice == "2":
        webhook_type = "discord"
        print("\n📝 Discord Setup Instructions:")
        print("1. Go to Discord server settings")
        print("2. Integrations > Webhooks > New Webhook")
        print("3. Choose channel and copy webhook URL")
    else:
        webhook_type = "generic"
    
    webhook_url = input("\nEnter webhook URL: ").strip()
    
    if webhook_url:
        # Update .env file
        env_path = Path(".env")
        env_content = env_path.read_text() if env_path.exists() else ""
        
        lines = env_content.split('\n')
        updated_lines = []
        webhook_settings = {
            'WEBHOOK_URL': webhook_url,
            'WEBHOOK_TYPE': webhook_type,
            'WEBHOOK_ENABLED': 'true'
        }
        
        for line in lines:
            found = False
            for key, value in webhook_settings.items():
                if line.startswith(f"{key}="):
                    updated_lines.append(f"{key}={value}")
                    webhook_settings.pop(key)
                    found = True
                    break
            if not found:
                updated_lines.append(line)
        
        for key, value in webhook_settings.items():
            updated_lines.append(f"{key}={value}")
        
        env_path.write_text('\n'.join(updated_lines))
        
        print("\n✅ Webhook configuration saved!")
        print("\n🧪 Test your webhook:")
        print("python main.py --webhook-notify")

if __name__ == "__main__":
    print("🔧 Notification Setup")
    print("=" * 30)
    
    setup_type = input("\nSetup: (1) Email, (2) Webhook, (3) Both: ").strip()
    
    if setup_type in ["1", "3"]:
        setup_email_notifications()
    
    if setup_type in ["2", "3"]:
        setup_webhook_notifications()
    
    print("\n🎉 Notification setup complete!")
    print("\nNext steps:")
    print("• Test notifications with: python main.py --send-digest")
    print("• Use --email-notify flag when scraping")
    print("• Set up scheduled scraping for automatic alerts")