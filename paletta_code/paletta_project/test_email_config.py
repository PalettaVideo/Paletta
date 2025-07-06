"""
Email Configuration Test Script
This script tests the current email configuration to diagnose sending issues.
"""

import os
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_project.settings_production')
django.setup()

from django.core.mail import send_mail
from django.test import override_settings
import logging

logger = logging.getLogger(__name__)

def test_email_configuration():
    """Test and diagnose email configuration."""
    
    print("=== EMAIL CONFIGURATION DIAGNOSIS ===")
    
    # 1. Check current configuration
    print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'NOT SET')}")
    print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'NOT SET')}")
    print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'NOT SET')}")
    print(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'NOT SET')}")
    print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'NOT SET')}")
    print(f"EMAIL_HOST_PASSWORD: {'SET' if getattr(settings, 'EMAIL_HOST_PASSWORD', '') else 'NOT SET'}")
    print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')}")
    print(f"AWS_SES_ENABLED: {getattr(settings, 'AWS_SES_ENABLED', 'NOT SET')}")
    print(f"AWS_SES_SENDER_EMAIL: {getattr(settings, 'AWS_SES_SENDER_EMAIL', 'NOT SET')}")
    
    # 2. Check environment variables
    print("\n=== ENVIRONMENT VARIABLES ===")
    env_vars = [
        'EMAIL_BACKEND',
        'EMAIL_HOST',
        'EMAIL_PORT',
        'EMAIL_USE_TLS',
        'EMAIL_HOST_USER',
        'EMAIL_HOST_PASSWORD',
        'DEFAULT_FROM_EMAIL',
        'AWS_SES_ENABLED',
        'AWS_SES_SENDER_EMAIL'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if var == 'EMAIL_HOST_PASSWORD' and value:
            print(f"{var}: SET")
        else:
            print(f"{var}: {value if value else 'NOT SET'}")
    
    # 3. Test current configuration
    print("\n=== TESTING CURRENT EMAIL CONFIGURATION ===")
    
    if getattr(settings, 'EMAIL_BACKEND', '') == 'django.core.mail.backends.console.EmailBackend':
        print("⚠️  WARNING: You're using the console email backend!")
        print("   This means emails are being printed to console, not actually sent.")
        print("   This is likely why you're not receiving emails.")
        
    # 4. Test sending an email
    print("\n=== TESTING EMAIL SENDING ===")
    try:
        send_mail(
            subject='Test Email - Paletta Configuration',
            message='This is a test email to verify email configuration.',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'test@paletta.io'),
            recipient_list=['test@example.com'],
            fail_silently=False
        )
        print("✅ Email send command executed successfully")
        
        if getattr(settings, 'EMAIL_BACKEND', '') == 'django.core.mail.backends.console.EmailBackend':
            print("📝 Email was printed to console (check your terminal/logs)")
        else:
            print("📧 Email was sent using configured backend")
            
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
    
    # 5. Recommendations
    print("\n=== RECOMMENDATIONS ===")
    
    current_backend = getattr(settings, 'EMAIL_BACKEND', '')
    
    if current_backend == 'django.core.mail.backends.console.EmailBackend':
        print("🔧 TO FIX: Set EMAIL_BACKEND environment variable to one of:")
        print("   - django.core.mail.backends.smtp.EmailBackend (for SMTP)")
        print("   - django_ses.SESBackend (for AWS SES)")
        print()
        print("📧 FOR AWS SES:")
        print("   1. Set AWS_SES_ENABLED=True")
        print("   2. Set EMAIL_BACKEND=django_ses.SESBackend")
        print("   3. Ensure AWS credentials are configured")
        print()
        print("📧 FOR SMTP:")
        print("   1. Set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend")
        print("   2. Configure EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD")
        
    print("\n=== NEXT STEPS ===")
    print("1. Choose your email service (AWS SES or SMTP)")
    print("2. Set the appropriate environment variables")
    print("3. Test again using this script")
    print("4. Test the actual download request system")

if __name__ == "__main__":
    test_email_configuration() 