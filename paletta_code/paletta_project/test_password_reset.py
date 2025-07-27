#!/usr/bin/env python
"""
Test script for password reset email functionality.
This script validates that the password reset notification emails work correctly.
"""

import os
import sys
import django
from datetime import datetime

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_project.settings_production')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from accounts.models import User

def test_email_configuration():
    """Test email configuration and settings."""
    print("Testing Email Configuration...")
    
    # Check manager email
    manager_email = getattr(settings, 'MANAGER_EMAIL', 'vvomifares@gmail.com')
    print(f"Manager Email: {manager_email}")
    
    # Check sender email
    sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@filmbright.com')
    print(f"Sender Email: {sender_email}")
    
    # Check email backend
    email_backend = getattr(settings, 'EMAIL_BACKEND', 'Not set')
    print(f"Email Backend: {email_backend}")
    
    return True

def test_template_rendering():
    """Test that the email template renders correctly."""
    print("\nTesting Email Template Rendering...")
    
    # Create mock context data
    context = {
        'user_email': 'test@example.com',
        'user_name': 'Test User',
        'user_institution': 'Test University',
        'user_company': 'Test Company',
        'user_role': 'Contributor',
        'ip_address': '192.168.1.1',
        'user_agent': 'Mozilla/5.0 (Test Browser)',
        'request_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    try:
        # Render the template
        html_message = render_to_string('accounts/emails/password_reset_notification.html', context)
        plain_message = strip_tags(html_message)
        
        print("Template rendered successfully")
        print(f"HTML length: {len(html_message)} characters")
        print(f"Plain text length: {len(plain_message)} characters")
        
        # Check for key content
        if 'Password Reset Request' in html_message:
            print("Template contains expected content")
        else:
            print("Template missing expected content")
            return False
            
        return True
        
    except Exception as e:
        print(f"Template rendering failed: {str(e)}")
        return False

def test_user_lookup():
    """Test user lookup functionality."""
    print("\nTesting User Lookup...")
    
    # Try to find a test user
    try:
        # Look for any user in the database
        users = User.objects.all()
        if users.exists():
            test_user = users.first()
            print(f"Found test user: {test_user.email}")
            print(f"User name: {test_user.get_full_name()}")
            print(f"User role: {test_user.get_role_display()}")
            return test_user
        else:
            print("No users found in database")
            return None
            
    except Exception as e:
        print(f"User lookup failed: {str(e)}")
        return None

def test_email_sending():
    """Test actual email sending."""
    print("\nTesting Email Sending...")
    
    # Get manager email
    manager_email = getattr(settings, 'MANAGER_EMAIL', 'vvomifares@gmail.com')
    sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@filmbright.com')
    
    # Create test context
    context = {
        'user_email': 'test@example.com',
        'user_name': 'Test User',
        'user_institution': 'Test University',
        'user_company': 'Test Company',
        'user_role': 'Contributor',
        'ip_address': '192.168.1.1',
        'user_agent': 'Mozilla/5.0 (Test Browser)',
        'request_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    try:
        # Render template
        html_message = render_to_string('accounts/emails/password_reset_notification.html', context)
        plain_message = strip_tags(html_message)
        
        # Send test email
        subject = 'TEST: Password Reset Request - User: test@example.com'
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=sender_email,
            recipient_list=[manager_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print("Test email sent successfully")
        print(f"Sent to: {manager_email}")
        print(f"Subject: {subject}")
        return True
        
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False

def test_forgot_password_view():
    """Test the forgot password view functionality."""
    print("\nTesting Forgot Password View...")
    
    from django.test import RequestFactory, TestCase
    from django.contrib.messages.middleware import MessageMiddleware
    from django.contrib.sessions.middleware import SessionMiddleware
    from accounts.views.forgot_password import ForgotPasswordView
    
    # Create a mock request with proper middleware
    factory = RequestFactory()
    
    # Test GET request
    request = factory.get('/forgot-password/')
    
    # Add middleware manually for testing
    session_middleware = SessionMiddleware(lambda req: None)
    message_middleware = MessageMiddleware(lambda req: None)
    
    # Apply middleware to request
    session_middleware.process_request(request)
    message_middleware.process_request(request)
    
    view = ForgotPasswordView()
    
    try:
        response = view.get(request)
        print("GET request works")
    except Exception as e:
        print(f"GET request failed: {str(e)}")
        return False
    
    # Test POST request with valid email
    test_user = test_user_lookup()
    if test_user:
        request = factory.post('/forgot-password/', {'email': test_user.email})
        
        # Apply middleware to request
        session_middleware.process_request(request)
        message_middleware.process_request(request)
        
        try:
            response = view.post(request)
            print("POST request with valid email works")
        except Exception as e:
            print(f"POST request failed: {str(e)}")
            return False
    
    # Test POST request with invalid email
    request = factory.post('/forgot-password/', {'email': 'nonexistent@example.com'})
    
    # Apply middleware to request
    session_middleware.process_request(request)
    message_middleware.process_request(request)
    
    try:
        response = view.post(request)
        print("POST request with invalid email works")
    except Exception as e:
        print(f"POST request with invalid email failed: {str(e)}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("Starting Password Reset Email Tests...\n")
    
    tests = [
        ("Email Configuration", test_email_configuration),
        ("Template Rendering", test_template_rendering),
        ("User Lookup", test_user_lookup),
        ("Email Sending", test_email_sending),
        ("Forgot Password View", test_forgot_password_view),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Password reset functionality is working correctly.")
    else:
        print("Some tests failed. Please check the configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 