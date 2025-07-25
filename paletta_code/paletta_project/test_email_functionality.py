#!/usr/bin/env python
"""
Test script for the new FilmBright email functionality.
This script tests that emails are sent to the manager instead of customers.
"""

import os
import sys
import django

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_core.settings_development')
django.setup()

from django.conf import settings
from django.utils import timezone
from orders.services import DownloadRequestService
from orders.models import DownloadRequest
from videos.models import Video
from accounts.models import User

def test_email_configuration():
    """Test the basic email configuration."""
    print("=== EMAIL CONFIGURATION TEST ===")
    
    print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')}")
    print(f"AWS_SES_SENDER_EMAIL: {getattr(settings, 'AWS_SES_SENDER_EMAIL', 'NOT SET')}")
    print(f"MANAGER_EMAIL: {getattr(settings, 'MANAGER_EMAIL', 'NOT SET')}")
    print(f"AWS_SES_ENABLED: {getattr(settings, 'AWS_SES_ENABLED', 'NOT SET')}")
    print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'NOT SET')}")
    
    # Check if we're using the correct sender email
    expected_sender = 'info@filmbright.com'
    actual_sender = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
    
    if actual_sender == expected_sender:
        print(f"Sender email correctly set to {expected_sender}")
    else:
        print(f"Sender email is {actual_sender}, expected {expected_sender}")
    
    # Check manager email
    expected_manager = 'vvomifares@gmail.com'
    actual_manager = getattr(settings, 'MANAGER_EMAIL', '')
    
    if actual_manager == expected_manager:
        print(f"Manager email correctly set to {expected_manager}")
    else:
        print(f"Manager email is {actual_manager}, expected {expected_manager}")
    
    print()

def test_service_initialization():
    """Test that the DownloadRequestService initializes correctly."""
    print("=== SERVICE INITIALIZATION TEST ===")
    
    try:
        service = DownloadRequestService()
        print(f"DownloadRequestService initialized successfully")
        print(f"   Sender email: {service.sender_email}")
        print(f"   Manager email: {service.manager_email}")
        print(f"   SES enabled: {service.ses_enabled}")
        print(f"   Storage enabled: {service.storage_enabled}")
        print()
        return service
    except Exception as e:
        print(f"Failed to initialize DownloadRequestService: {str(e)}")
        print()
        return None

def test_manager_notification_method():
    """Test the manager notification method with mock data."""
    print("=== MANAGER NOTIFICATION METHOD TEST ===")
    
    service = DownloadRequestService()
    
    # Create mock objects for testing
    class MockUser:
        def __init__(self):
            self.id = 1
            self.email = "testuser@example.com"
        
        def get_full_name(self):
            return "Test User"
    
    class MockVideo:
        def __init__(self):
            self.id = 1
            self.title = "Test Video"
            self.description = "A test video for email functionality"
            self.duration_formatted = "5:30"
            self.file_size = 1024 * 1024 * 100  # 100MB
            self.format = "mp4"
            self.content_type = MockContentType()
            self.library = MockLibrary()
    
    class MockContentType:
        def __init__(self):
            self.display_name = "Test Category"
    
    class MockLibrary:
        def __init__(self):
            self.name = "Test Library"
    
    class MockDownloadRequest:
        def __init__(self, user, video):
            self.id = 1
            self.user = user
            self.video = video
            self.email = user.email
            self.email_sent = False
            self.email_sent_at = None
            self.status = 'pending'
            self.email_error = ''
        
        def save(self, update_fields=None):
            print(f"   Mock save called with fields: {update_fields}")
    
    # Test with a single request
    print("Testing single video request notification...")
    mock_user = MockUser()
    mock_video = MockVideo()
    mock_request = MockDownloadRequest(mock_user, mock_video)
    
    try:
        # Note: This would actually send an email if SES is configured
        # For testing purposes, you may want to temporarily set EMAIL_BACKEND to console
        result = service.send_manager_notification(mock_request)
        
        if result:
            print("Single video manager notification sent successfully")
        else:
            print("Failed to send single video manager notification")
    except Exception as e:
        print(f"Error sending single video notification: {str(e)}")
    
    # Test with multiple requests
    print("\nTesting multiple video request notification...")
    mock_request2 = MockDownloadRequest(mock_user, MockVideo())
    mock_request2.video.title = "Second Test Video"
    
    try:
        result = service.send_manager_notification([mock_request, mock_request2])
        
        if result:
            print("Multiple video manager notification sent successfully")
        else:
            print("Failed to send multiple video manager notification")
    except Exception as e:
        print(f"Error sending multiple video notification: {str(e)}")
    
    print()

def test_database_connectivity():
    """Test that we can connect to the database and check for existing data."""
    print("=== DATABASE CONNECTIVITY TEST ===")
    
    try:
        # Test database connection
        user_count = User.objects.count()
        video_count = Video.objects.count()
        request_count = DownloadRequest.objects.count()
        
        print(f"Database connection successful")
        print(f"   Users: {user_count}")
        print(f"   Videos: {video_count}")
        print(f"   Download Requests: {request_count}")
        
        # Check if there are any recent download requests
        recent_requests = DownloadRequest.objects.order_by('-request_date')[:5]
        if recent_requests:
            print(f"   Recent requests:")
            for req in recent_requests:
                print(f"     - {req.user.email} requested '{req.video.title}' ({req.status})")
        
        print()
        return True
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        print()
        return False

def main():
    """Run all tests."""
    print("FILMBRGHT EMAIL FUNCTIONALITY TEST")
    print("=" * 50)
    print()
    
    # Test email configuration
    test_email_configuration()
    
    # Test service initialization
    service = test_service_initialization()
    if not service:
        print("Service initialization failed. Cannot continue with other tests.")
        return
    
    # Test database connectivity
    if not test_database_connectivity():
        print("Database connectivity failed. Cannot continue with database-dependent tests.")
        return
    
    # Test manager notification method
    test_manager_notification_method()
    
    print("=" * 50)
    print("TEST SUMMARY:")
    print("- Email configuration: Check the output above")
    print("- Service initialization: Check the output above")
    print("- Manager notification: Check the output above")
    print()
    print("To test with real email sending:")
    print("1. Ensure AWS SES is configured with info@filmbright.com")
    print("2. Set EMAIL_BACKEND to django_ses.SESBackend in your environment")
    print("3. Run this script again")
    print()

if __name__ == "__main__":
    main() 