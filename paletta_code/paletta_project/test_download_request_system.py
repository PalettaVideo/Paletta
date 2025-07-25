#!/usr/bin/env python
"""
Test script for validating the video download request system.
Run this script after completing the AWS setup to validate the entire flow.

Usage:
    python test_download_request_system.py
"""

import os
import sys
import django
from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_project.settings_production')
django.setup()

from orders.models import DownloadRequest
from orders.services import DownloadRequestService
from accounts.models import User
from videos.models import Video, ContentType
from libraries.models import Library
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DownloadRequestSystemTest:
    """
    Comprehensive test suite for the download request system.
    Tests all components from API to email delivery.
    """
    
    def __init__(self):
        self.service = DownloadRequestService()
        self.test_user = None
        self.test_video = None
        self.test_library = None
        
    def setup_test_data(self):
        """Create test data for validation."""
        logger.info("Setting up test data...")
        
        # Create test library
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            logger.error("No admin user found. Please create a superuser first.")
            return False
            
        self.test_library, created = Library.objects.get_or_create(
            name='Test Library',
            defaults={
                'description': 'Test library for download request validation',
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
            title='Test Download',
            defaults={
                'description': 'Test video for validating download requests',
                'library': self.test_library,
                'uploader': admin_user,
                'storage_status': 'stored',
                'storage_reference_id': 'test-video-key.mp4',
                'content_type': ContentType.objects.get_or_create(
                    subject_area='engineering_sciences',
                    library=self.test_library,
                    defaults={'description': 'Test content type'}
                )[0]
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
            'AWS_STORAGE_BUCKET_NAME',
            'AWS_SES_ENABLED',
            'AWS_SES_SENDER_EMAIL'
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not getattr(settings, setting, None):
                missing_settings.append(setting)
        
        if missing_settings:
            logger.error(f"Missing required settings: {', '.join(missing_settings)}")
            return False
        
        # Test S3 connectivity
        if self.service.storage_enabled:
            try:
                # Test S3 connection
                self.service.s3_client.list_buckets()
                logger.info("S3 connection successful")
            except Exception as e:
                logger.error(f"S3 connection failed: {str(e)}")
                return False
        else:
            logger.warning("AWS storage is not enabled")
            return False
        
        # Test SES configuration
        if self.service.ses_enabled:
            logger.info("SES is enabled")
        else:
            logger.warning("SES is not enabled")
        
        return True
    
    def test_download_request_creation(self):
        """Test download request creation."""
        logger.info("Testing download request creation...")
        
        try:
            # Create download request
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
            assert download_request.expiry_date > timezone.now()
            assert download_request.s3_key == self.test_video.storage_reference_id
            
            logger.info(f"Download request created successfully (ID: {download_request.id})")
            return download_request
            
        except Exception as e:
            logger.error(f"Download request creation failed: {str(e)}")
            return None
    
    def test_presigned_url_generation(self, download_request):
        """Test S3 presigned URL generation."""
        logger.info("Testing presigned URL generation...")
        
        try:
            # Generate presigned URL
            presigned_url = self.service.generate_presigned_url(download_request)
            
            if presigned_url:
                # Validate URL
                assert presigned_url.startswith('https://')
                assert self.service.bucket_name in presigned_url
                assert 'X-Amz-Expires=172800' in presigned_url  # 48 hours
                
                # Refresh from database
                download_request.refresh_from_db()
                assert download_request.download_url == presigned_url
                assert download_request.aws_request_id is not None
                
                logger.info("Presigned URL generated successfully")
                logger.info(f"  URL length: {len(presigned_url)} characters")
                logger.info(f"  Expires in: 48 hours")
                return True
            else:
                logger.error("Failed to generate presigned URL")
                return False
                
        except Exception as e:
            logger.error(f"Presigned URL generation failed: {str(e)}")
            return False
    
    def test_email_sending(self, download_request):
        """Test email sending functionality."""
        logger.info("Testing email sending...")
        
        try:
            # Send email
            success = self.service.send_download_email(download_request)
            
            if success:
                # Refresh from database
                download_request.refresh_from_db()
                assert download_request.email_sent == True
                assert download_request.email_sent_at is not None
                assert download_request.status == 'completed'
                
                logger.info("Email sent successfully")
                logger.info(f"  Sent to: {download_request.email}")
                logger.info(f"  Status: {download_request.get_status_display()}")
                return True
            else:
                logger.error("Email sending failed")
                return False
                
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return False
    
    def test_complete_flow(self):
        """Test the complete download request flow."""
        logger.info("Testing complete download request flow...")
        
        try:
            # Create and process download request
            download_request = self.service.create_download_request(
                user=self.test_user,
                video=self.test_video,
                email='test@example.com'
            )
            
            # Process the request
            success = self.service.process_download_request(download_request)
            
            if success:
                # Refresh from database
                download_request.refresh_from_db()
                
                # Validate final state
                assert download_request.status == 'completed'
                assert download_request.download_url is not None
                assert download_request.email_sent == True
                assert download_request.aws_request_id is not None
                
                logger.info("Complete flow test successful")
                return True
            else:
                logger.error("Complete flow test failed")
                return False
                
        except Exception as e:
            logger.error(f"Complete flow test failed: {str(e)}")
            return False
    
    def test_expiry_logic(self):
        """Test expiry logic and cleanup."""
        logger.info("Testing expiry logic...")
        
        try:
            # Create expired request
            expired_request = DownloadRequest.objects.create(
                user=self.test_user,
                video=self.test_video,
                email='test@example.com',
                expiry_date=timezone.now() - timedelta(hours=1),  # 1 hour ago
                status='completed'
            )
            
            # Test expiry check
            assert expired_request.is_expired() == True
            logger.info("Expiry check working")
            
            # Test cleanup
            cleaned_count = self.service.cleanup_expired_requests()
            
            # Refresh from database
            expired_request.refresh_from_db()
            assert expired_request.status == 'expired'
            
            logger.info(f"Cleanup successful - {cleaned_count} requests marked as expired")
            return True
            
        except Exception as e:
            logger.error(f"Expiry logic test failed: {str(e)}")
            return False
    
    def test_duplicate_request_handling(self):
        """Test handling of duplicate requests."""
        logger.info("Testing duplicate request handling...")
        
        try:
            # Create first request
            request1 = self.service.create_download_request(
                user=self.test_user,
                video=self.test_video,
                email='test@example.com'
            )
            
            # Create second request (should return existing)
            request2 = self.service.create_download_request(
                user=self.test_user,
                video=self.test_video,
                email='test@example.com'
            )
            
            # Should be the same request
            assert request1.id == request2.id
            logger.info("Duplicate request handling working")
            return True
            
        except Exception as e:
            logger.error(f"Duplicate request handling test failed: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        logger.info("Testing error handling...")
        
        try:
            # Test with non-existent video
            non_existent_video = Video(
                id=99999,
                title='Non-existent Video',
                storage_status='not_stored',
                storage_reference_id=None
            )
            
            try:
                request = self.service.create_download_request(
                    user=self.test_user,
                    video=non_existent_video,
                    email='test@example.com'
                )
                logger.error("Should have failed for non-stored video")
                return False
            except ValueError as e:
                logger.info(f"Properly caught error for non-stored video: {str(e)}")
            
            # Test with invalid email
            try:
                request = self.service.create_download_request(
                    user=self.test_user,
                    video=self.test_video,
                    email='invalid-email'
                )
                # This should not fail at creation, but might fail at sending
                logger.info("Invalid email handling test passed")
            except Exception as e:
                logger.info(f"Caught error for invalid email: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling test failed: {str(e)}")
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
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        logger.info("Starting download request system validation...")
        
        # Setup
        if not self.setup_test_data():
            logger.error("Test data setup failed")
            return False
        
        # Test results
        results = {
            'aws_configuration': self.test_aws_configuration(),
            'download_request_creation': False,
            'presigned_url_generation': False,
            'email_sending': False,
            'complete_flow': self.test_complete_flow(),
            'expiry_logic': self.test_expiry_logic(),
            'duplicate_handling': self.test_duplicate_request_handling(),
            'error_handling': self.test_error_handling()
        }
        
        # Individual component tests
        download_request = self.test_download_request_creation()
        if download_request:
            results['download_request_creation'] = True
            results['presigned_url_generation'] = self.test_presigned_url_generation(download_request)
            results['email_sending'] = self.test_email_sending(download_request)
        
        # Cleanup
        self.cleanup_test_data()
        
        # Report results
        logger.info("\n" + "="*60)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("="*60)
        
        passed = 0
        total = len(results)
        
        for test_name, passed_test in results.items():
            status = "PASS" if passed_test else "FAIL"
            logger.info(f"{test_name:30} {status}")
            if passed_test:
                passed += 1
        
        logger.info("-"*60)
        logger.info(f"Overall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("All tests passed! Download request system is ready.")
            return True
        else:
            logger.error("Some tests failed. Please check the logs and fix issues.")
            return False

def main():
    """Main entry point for the test script."""
    test_suite = DownloadRequestSystemTest()
    success = test_suite.run_all_tests()
    
    if success:
        print("\nAll tests passed! Your download request system is ready for production.")
        sys.exit(0)
    else:
        print("\nSome tests failed. Please review the logs and fix the issues.")
        sys.exit(1)

if __name__ == '__main__':
    main() 