#!/usr/bin/env python
"""
Test script for contact form functionality.
This script validates that the contact form email functionality works correctly.
"""

import os
import sys
import django
from datetime import datetime

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_project.settings_production')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def test_contact_form_email():
    """Test contact form email functionality."""
    print("Testing Contact Form Email Functionality...")
    
    # Check email configuration
    manager_email = getattr(settings, 'MANAGER_EMAIL', 'niklaas@filmbright.com')
    sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@filmbright.com')
    email_backend = getattr(settings, 'EMAIL_BACKEND', 'Not set')
    
    print(f"Manager Email: {manager_email}")
    print(f"Sender Email: {sender_email}")
    print(f"Email Backend: {email_backend}")
    
    # Create test context
    context = {
        'sender_email': 'test@example.com',
        'message': 'This is a test message from the contact form.',
        'ip_address': '192.168.1.1',
        'user_agent': 'Mozilla/5.0 (Test Browser)',
        'request_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    try:
        # Render template
        html_message = render_to_string('accounts/emails/contact_form_notification.html', context)
        plain_message = strip_tags(html_message)
        
        # Send test email
        subject = 'TEST: New Contact Form Message - From: test@example.com'
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=sender_email,
            recipient_list=[manager_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print("Contact form test email sent successfully!")
        print(f"   Sent to: {manager_email}")
        print(f"   Subject: {subject}")
        return True
        
    except Exception as e:
        print(f"Contact form test email failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_contact_form_email() 