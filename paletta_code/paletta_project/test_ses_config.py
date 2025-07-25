#!/usr/bin/env python3
"""
Quick test script to verify SES email configuration and send a test email.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_core.settings_development')

# Initialize Django
django.setup()

from django.core.mail import send_mail
from django.conf import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ses_configuration():
    """Test AWS SES email configuration and send a test email."""
    
    print("=== AWS SES Configuration Test ===")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"MANAGER_EMAIL: {settings.MANAGER_EMAIL}")
    print(f"AWS_SES_ENABLED: {getattr(settings, 'AWS_SES_ENABLED', False)}")
    
    if hasattr(settings, 'AWS_ACCESS_KEY_ID'):
        print(f"AWS_ACCESS_KEY_ID: {'***' + settings.AWS_ACCESS_KEY_ID[-4:] if settings.AWS_ACCESS_KEY_ID else 'Not set'}")
    
    if hasattr(settings, 'AWS_SES_REGION_NAME'):
        print(f"AWS_SES_REGION_NAME: {settings.AWS_SES_REGION_NAME}")
    
    print("\n=== Sending Test Email ===")
    
    try:
        # Send a simple test email
        subject = "Paletta SES Test Email"
        message = """
        This is a test email from the Paletta system to verify SES configuration.
        
        If you receive this email, your SES configuration is working correctly.
        
        Test details:
        - From: {from_email}
        - To: {to_email}
        - Backend: {backend}
        
        Timestamp: {timestamp}
        """.format(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_email=settings.MANAGER_EMAIL,
            backend=settings.EMAIL_BACKEND,
            timestamp=django.utils.timezone.now()
        )
        
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.MANAGER_EMAIL],
            fail_silently=False
        )
        
        if result:
            print("✅ Test email sent successfully!")
            print(f"   Sent to: {settings.MANAGER_EMAIL}")
            print(f"   From: {settings.DEFAULT_FROM_EMAIL}")
            return True
        else:
            print("❌ Email sending failed - no result returned")
            return False
            
    except Exception as e:
        print(f"❌ Email sending failed with error: {str(e)}")
        
        # Additional debugging for SES errors
        if "InvalidParameterValue" in str(e):
            print("\n💡 Common SES Issues:")
            print("   - Make sure both sender and recipient emails are verified in SES")
            print("   - Check if SES is in sandbox mode (sandbox mode only allows verified emails)")
            print("   - Verify AWS credentials have SES permissions")
        
        return False

if __name__ == "__main__":
    import django.utils.timezone
    test_ses_configuration() 