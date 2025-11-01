"""Test notification configuration."""
from notifications import NotificationManager

def test_notifications():
    """Test notification setup."""
    try:
        nm = NotificationManager()
        print("✅ NotificationManager loaded successfully")
        
        # Check configuration
        print(f"SMTP Server configured: {hasattr(nm, 'smtp_server')}")
        print(f"Email enabled: {getattr(nm, 'email_enabled', False)}")
        print(f"Webhook enabled: {getattr(nm, 'webhook_enabled', False)}")
        
        return True
    except Exception as e:
        print(f"❌ Notification test failed: {e}")
        return False

if __name__ == "__main__":
    test_notifications()