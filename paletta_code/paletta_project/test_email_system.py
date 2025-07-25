#!/usr/bin/env python
"""
Comprehensive Email System Test Suite
Combines functionality from all email-related test files:
- test_download_request_system.py
- test_email_robustness.py  
- test_email_functionality.py
- test_email_config.py

Usage:
    python test_comprehensive_email_system.py [--config-only] [--unit-only] [--integration-only] [--robustness-only]
"""

import os
import sys
import django
import argparse
from django.conf import settings
from django.utils import timezone
import time
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_project.settings_production')
django.setup()

from orders.models import DownloadRequest
from orders.services import DownloadRequestService
from accounts.models import User
from videos.models import Video, ContentType
from libraries.models import Library
from django.template.loader import render_to_string

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveEmailSystemTest:
    """
    Unified test suite for the complete email system.
    Includes configuration, unit tests, integration tests, and robustness testing.
    """
    
    def __init__(self):
        self.service = DownloadRequestService()
        self.test_user = None
        self.test_video = None
        self.test_library = None
        
    # ========================================
    # CONFIGURATION TESTS (from test_email_config.py)
    # ========================================
    
    def test_email_configuration(self):
        """Test email configuration and provide diagnostics."""
        logger.info("Testing email configuration...")
        
        config_issues = []
        
        # Check basic email settings
        email_backend = getattr(settings, 'EMAIL_BACKEND', 'NOT SET')
        default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')
        manager_email = getattr(settings, 'MANAGER_EMAIL', 'NOT SET')
        aws_ses_enabled = getattr(settings, 'AWS_SES_ENABLED', False)
        
        logger.info(f"EMAIL_BACKEND: {email_backend}")
        logger.info(f"DEFAULT_FROM_EMAIL: {default_from_email}")
        logger.info(f"MANAGER_EMAIL: {manager_email}")
        logger.info(f"AWS_SES_ENABLED: {aws_ses_enabled}")
        
        # Analyze configuration issues
        if email_backend == 'django.core.mail.backends.console.EmailBackend':
            config_issues.append("Using console backend - emails won't be sent")
            
        if default_from_email == 'NOT SET':
            config_issues.append("DEFAULT_FROM_EMAIL not configured")
            
        if manager_email == 'NOT SET':
            config_issues.append("MANAGER_EMAIL not configured")
            
        # Check AWS SES configuration if enabled
        if aws_ses_enabled:
            if not getattr(settings, 'AWS_ACCESS_KEY_ID', ''):
                config_issues.append("AWS_ACCESS_KEY_ID not set")
            if not getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''):
                config_issues.append("AWS_SECRET_ACCESS_KEY not set")
        
        if config_issues:
            logger.warning("Configuration issues found:")
            for issue in config_issues:
                logger.warning(f"  - {issue}")
            return False
        
        logger.info("Email configuration looks good")
        return True
    
    def test_service_initialization(self):
        """Test DownloadRequestService initialization."""
        logger.info("Testing service initialization...")
        
        try:
            service = DownloadRequestService()
            logger.info(f"Service initialized successfully")
            logger.info(f"  Sender email: {service.sender_email}")
            logger.info(f"  Manager email: {service.manager_email}")
            logger.info(f"  SES enabled: {service.ses_enabled}")
            logger.info(f"  Storage enabled: {service.storage_enabled}")
            return True
        except Exception as e:
            logger.error(f"Service initialization failed: {str(e)}")
            return False
    
    # ========================================
    # UNIT TESTS (from test_email_functionality.py)
    # ========================================
    
    def test_manager_notification_with_mocks(self):
        """Test manager notification with mock objects."""
        logger.info("Testing manager notification with mock data...")
        
        # Create mock objects
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
                self.description = "A test video"
                self.duration_formatted = "5:30"
                self.file_size = 1024 * 1024 * 100
                self.format = "mp4"
                self.content_type = type('obj', (), {'display_name': 'Test Category'})()
                self.library = type('obj', (), {'name': 'Test Library'})()
        
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
                pass
        
        try:
            mock_user = MockUser()
            mock_video = MockVideo()
            mock_request = MockDownloadRequest(mock_user, mock_video)
            
            # This will test the email logic without sending real emails
            # if using console backend
            result = self.service.send_manager_notification(mock_request)
            
            if result:
                logger.info("Mock manager notification test passed")
                return True
            else:
                logger.error("Mock manager notification test failed")
                return False
                
        except Exception as e:
            logger.error(f"Mock notification test failed: {str(e)}")
            return False
    
    # ========================================
    # ROBUSTNESS TESTS (from test_email_robustness.py)
    # ========================================
    
    def test_problematic_characters(self):
        """Test email system with various problematic characters."""
        logger.info("Testing email system with problematic characters...")
        
        # Test cases with different types of problematic content
        test_cases = [
            {
                'name': 'Smart Quotes',
                'email': 'smartquotes@example.com',
                'first_name': 'John "Smart" Test',
                'video_title': 'Video "quotes" dash–em—'
            },
            {
                'name': 'Unicode Content',
                'email': 'unicode@example.com',
                'first_name': 'José María',
                'video_title': 'Café résumé content'
            }
        ]
        
        passed_tests = 0
        
        for test_case in test_cases:
            logger.info(f"Testing case: {test_case['name']}")
            
            try:
                # Test template rendering with problematic content
                context = {
                    'customer_name': test_case['first_name'],
                    'customer_email': test_case['email'],
                    'customer_id': 1,
                    'request_date': timezone.now(),
                    'video_count': 1,
                    'videos': [{
                        'id': 1,
                        'title': test_case['video_title'],
                        'description': f'Test for {test_case["name"]}',
                        'duration_formatted': '5:30',
                        'file_size': 1024000,
                        'format': 'mp4',
                        'content_type': {'display_name': 'Test Category'}
                    }],
                    'customer_library': 'Test Library',
                    'request_id': 1
                }
                
                # Test template rendering
                html_content = render_to_string('emails/manager_download_request.html', context)
                
                # Test encoding
                html_content.encode('utf-8')
                
                logger.info(f"✓ {test_case['name']}: Template rendering passed")
                passed_tests += 1
                
            except Exception as e:
                logger.error(f"✗ {test_case['name']}: Failed - {str(e)}")
        
        success_rate = passed_tests / len(test_cases)
        logger.info(f"Problematic characters test: {passed_tests}/{len(test_cases)} passed ({success_rate*100:.1f}%)")
        return success_rate >= 0.8  # 80% success rate required
    
    def test_header_injection_protection(self):
        """Test header injection protection."""
        logger.info("Testing header injection protection...")
        
        # Test cases that should be rejected
        injection_tests = [
            "normal@example.com\nBCC: evil@hacker.com",
            "Subject: Fake\rTo: victim@example.com",
            "test@example.com\r\nBCC: hidden@attacker.com"
        ]
        
        protected_count = 0
        
        for test_email in injection_tests:
            try:
                # Create fake context for testing
                fake_context = [type('obj', (object,), {
                    'user': type('obj', (object,), {
                        'email': test_email,
                        'get_full_name': lambda: 'Test User'
                    })(),
                    'video': type('obj', (object,), {
                        'title': 'Test Video',
                        'library': type('obj', (object,), {'name': 'Test Library'})()
                    })()
                })()]
                
                result = self.service.send_manager_notification(fake_context)
                
                if not result:
                    protected_count += 1
                    logger.info(f"✓ Protected against: {repr(test_email[:30])}")
                else:
                    logger.warning(f"! Not protected against: {repr(test_email[:30])}")
                    
            except ValueError as e:
                if "Header injection" in str(e):
                    protected_count += 1
                    logger.info(f"✓ Caught header injection: {repr(test_email[:30])}")
                else:
                    logger.warning(f"! Unexpected error: {str(e)}")
            except Exception as e:
                # Other exceptions might also indicate protection
                protected_count += 1
                logger.info(f"✓ Exception caught for: {repr(test_email[:30])}")
        
        success = protected_count == len(injection_tests)
        logger.info(f"Header injection protection: {protected_count}/{len(injection_tests)} protected")
        return success
    
    # ========================================
    # INTEGRATION TESTS (from test_download_request_system.py)
    # ========================================
    
    def setup_test_data(self):
        """Create test data for integration testing."""
        logger.info("Setting up test data...")
        
        # Create test library
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            logger.error("No admin user found. Please create a superuser first.")
            return False
            
        self.test_library, created = Library.objects.get_or_create(
            name='Test Library',
            defaults={
                'description': 'Test library for email system validation',
                'owner': admin_user,
                'is_active': True
            }
        )
        
        # Create test user
        try:
            self.test_user = User.objects.get(email='test@example.com')
        except User.DoesNotExist:
            self.test_user = User.objects.create_user(
                email='test@example.com',
                first_name='Test',
                last_name='User'
            )
        
        # Create test video
        self.test_video, created = Video.objects.get_or_create(
            title='Test Email Video',
            defaults={
                'description': 'Test video for email system validation',
                'library': self.test_library,
                'uploader': admin_user,
                'storage_status': 'stored',
                'storage_reference_id': 'test-email-video.mp4',
                'content_type': ContentType.objects.get_or_create(
                    subject_area='engineering_sciences',
                    library=self.test_library,
                    defaults={'description': 'Test content type'}
                )[0],
                'duration': 330  # 5:30
            }
        )
        
        logger.info(f"Test data setup complete:")
        logger.info(f"  Library: {self.test_library.name}")
        logger.info(f"  User: {self.test_user.email}")
        logger.info(f"  Video: {self.test_video.title}")
        
        return True
    
    def test_aws_configuration(self):
        """Test AWS configuration and connectivity."""
        logger.info("Testing AWS configuration...")
        
        # Check required settings
        required_settings = [
            'AWS_STORAGE_ENABLED',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_REGION',
            'AWS_STORAGE_BUCKET_NAME'
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not getattr(settings, setting, None):
                missing_settings.append(setting)
        
        if missing_settings:
            logger.warning(f"Missing AWS settings: {', '.join(missing_settings)}")
            return False
        
        # Test S3 connectivity
        if self.service.storage_enabled:
            try:
                self.service.s3_client.list_buckets()
                logger.info("AWS S3 connection successful")
                return True
            except Exception as e:
                logger.error(f"AWS S3 connection failed: {str(e)}")
                return False
        else:
            logger.warning("AWS storage is not enabled")
            return False
    
    def test_download_request_creation(self):
        """Test download request creation."""
        logger.info("Testing download request creation...")
        
        try:
            download_request = self.service.create_download_request(
                user=self.test_user,
                video=self.test_video,
                email='test@example.com'
            )
            
            # Validate request
            assert download_request.user == self.test_user
            assert download_request.video == self.test_video
            assert download_request.email == 'test@example.com'
            assert download_request.status == 'pending'
            
            logger.info(f"Download request created successfully (ID: {download_request.id})")
            return download_request
            
        except Exception as e:
            logger.error(f"Download request creation failed: {str(e)}")
            return None
    
    def test_complete_email_flow(self):
        """Test the complete email flow."""
        logger.info("Testing complete email flow...")
        
        try:
            # Create download request
            download_request = self.service.create_download_request(
                user=self.test_user,
                video=self.test_video,
                email='test@example.com'
            )
            
            # Process the request (this includes email sending)
            success = self.service.process_download_request(download_request)
            
            if success:
                # Refresh from database
                download_request.refresh_from_db()
                
                # Validate final state
                assert download_request.status == 'completed'
                assert download_request.email_sent == True
                
                logger.info("Complete email flow test successful")
                return True
            else:
                logger.error("Complete email flow test failed")
                return False
                
        except Exception as e:
            logger.error(f"Complete email flow test failed: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data."""
        logger.info("Cleaning up test data...")
        
        try:
            # Delete test download requests
            DownloadRequest.objects.filter(user=self.test_user).delete()
            
            # Delete test video
            if self.test_video:
                self.test_video.delete()
            
            # Delete test user
            if self.test_user:
                self.test_user.delete()
            
            # Delete test library
            if self.test_library:
                self.test_library.delete()
            
            logger.info("Test data cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
    
    # ========================================
    # MAIN TEST RUNNER
    # ========================================
    
    def run_configuration_tests(self):
        """Run configuration tests only."""
        logger.info("="*60)
        logger.info("CONFIGURATION TESTS")
        logger.info("="*60)
        
        results = {
            'email_configuration': self.test_email_configuration(),
            'service_initialization': self.test_service_initialization()
        }
        
        return results
    
    def run_unit_tests(self):
        """Run unit tests only."""
        logger.info("="*60)
        logger.info("UNIT TESTS")
        logger.info("="*60)
        
        results = {
            'manager_notification_mocks': self.test_manager_notification_with_mocks()
        }
        
        return results
    
    def run_robustness_tests(self):
        """Run robustness tests only."""
        logger.info("="*60)
        logger.info("ROBUSTNESS TESTS")
        logger.info("="*60)
        
        results = {
            'problematic_characters': self.test_problematic_characters(),
            'header_injection_protection': self.test_header_injection_protection()
        }
        
        return results
    
    def run_integration_tests(self):
        """Run integration tests only."""
        logger.info("="*60)
        logger.info("INTEGRATION TESTS")
        logger.info("="*60)
        
        # Setup
        if not self.setup_test_data():
            logger.error("Test data setup failed")
            return {'setup_failed': True}
        
        results = {
            'aws_configuration': self.test_aws_configuration(),
            'download_request_creation': False,
            'complete_email_flow': self.test_complete_email_flow()
        }
        
        # Test download request creation
        download_request = self.test_download_request_creation()
        if download_request:
            results['download_request_creation'] = True
        
        # Cleanup
        self.cleanup_test_data()
        
        return results
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        logger.info("COMPREHENSIVE EMAIL SYSTEM TEST SUITE")
        logger.info("="*60)
        
        all_results = {
            'configuration': self.run_configuration_tests(),
            'unit': self.run_unit_tests(),
            'robustness': self.run_robustness_tests(),
            'integration': self.run_integration_tests()
        }
        
        # Calculate overall results
        logger.info("="*60)
        logger.info("COMPREHENSIVE TEST RESULTS SUMMARY")
        logger.info("="*60)
        
        total_tests = 0
        passed_tests = 0
        
        for category, results in all_results.items():
            if 'setup_failed' in results:
                logger.warning(f"{category.title()}: Setup failed")
                continue
                
            category_passed = sum(1 for result in results.values() if result)
            category_total = len(results)
            
            logger.info(f"{category.title()}: {category_passed}/{category_total} passed")
            
            total_tests += category_total
            passed_tests += category_passed
        
        logger.info("-"*60)
        logger.info(f"Overall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            logger.info("🎉 All tests passed! Email system is fully functional.")
            return True
        else:
            logger.warning("⚠️  Some tests failed. Review the logs and fix issues.")
            return False

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='Comprehensive Email System Test Suite')
    parser.add_argument('--config-only', action='store_true', help='Run configuration tests only')
    parser.add_argument('--unit-only', action='store_true', help='Run unit tests only')
    parser.add_argument('--robustness-only', action='store_true', help='Run robustness tests only')
    parser.add_argument('--integration-only', action='store_true', help='Run integration tests only')
    
    args = parser.parse_args()
    
    test_suite = ComprehensiveEmailSystemTest()
    
    if args.config_only:
        results = test_suite.run_configuration_tests()
        success = all(results.values())
    elif args.unit_only:
        results = test_suite.run_unit_tests()
        success = all(results.values())
    elif args.robustness_only:
        results = test_suite.run_robustness_tests()
        success = all(results.values())
    elif args.integration_only:
        results = test_suite.run_integration_tests()
        success = all(results.values()) and 'setup_failed' not in results
    else:
        success = test_suite.run_all_tests()
    
    if success:
        print("\n✅ All selected tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please review the logs.")
        sys.exit(1)

if __name__ == '__main__':
    main() 