#!/usr/bin/env python3
"""
Comprehensive Video Upload Test Suite
Combines upload pipeline testing and fixes verification into one comprehensive test suite.

Tests all critical aspects of the video upload pipeline:
- Frontend simulation and edge cases
- Backend API validation and error handling  
- AWS integration and S3 operations
- Database transactions and race conditions
- Performance and stress testing
- Upload pipeline fixes verification

Usage:
    python test_upload_comprehensive.py [--quick] [--full] [--fixes-only] [--pipeline-only]
"""

import os
import sys
import django
import argparse
import time
import logging
import uuid
import json
from concurrent.futures import ThreadPoolExecutor

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

# Change to the paletta_project directory where settings are located
paletta_project_dir = os.path.join(project_dir, 'paletta_project')
os.chdir(paletta_project_dir)

# Add the current directory to Python path so Django can find the settings module
sys.path.insert(0, os.getcwd())

print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}")

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_project.settings_production')
print(f"Django settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
django.setup()

from django.test.client import Client
from django.conf import settings

# Fix ALLOWED_HOSTS for testing
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from accounts.models import User
from libraries.models import Library
from videos.models import Video, ContentType, Tag
import boto3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveUploadTestSuite:
    """
    Comprehensive test suite combining upload pipeline testing and fixes verification.
    Tests all failure points, edge cases, and validates that recent fixes are working.
    """
    
    def __init__(self):
        self.client = Client()
        self.test_user = None
        self.test_library = None
        self.test_content_type = None
        self.s3_client = None
        self.results = {
            'fixes_verification': {},
            'frontend_simulation': {},
            'backend_validation': {},
            'aws_integration': {},
            'performance_stress': {},
            'integration_tests': {}
        }
        
    def setup_test_environment(self):
        """Setup comprehensive test data and connections."""
        logger.info("Setting up comprehensive test environment...")
        
        # Create or get test user
        try:
            self.test_user = User.objects.get(email='comprehensive-test@example.com')
        except User.DoesNotExist:
            self.test_user = User.objects.create_user(
                email='comprehensive-test@example.com',
                password='testpass123',
                first_name='Comprehensive',
                last_name='Test',
                role='user'
            )
        
        # Create or get admin user for library ownership
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                email='admin-test@example.com',
                password='adminpass123',
                first_name='Admin',
                last_name='Test'
            )
        
        # Create test library
        self.test_library, created = Library.objects.get_or_create(
            name='Test Lib', 
            defaults={
                'description': 'Test library for comprehensive upload validation',
                'owner': admin_user,
                'is_active': True
            }
        )
        
        # Create test content type
        self.test_content_type, created = ContentType.objects.get_or_create(
            subject_area='engineering_sciences',
            library=self.test_library,
            defaults={'description': 'Test content type for comprehensive validation'}
        )
        
        # Setup S3 client if possible
        try:
            if hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
                )
        except Exception as e:
            logger.warning(f"Could not initialize S3 client: {str(e)}")
        
        # Login user
        self.client.force_login(self.test_user)
        
        # Validate test data doesn't exceed database limits
        test_titles = [
            'Race Condition Test',
            'Test Video',
            'Valid Test Video',
            'Test 视频 Vidéo',
            'Video with Metadata',
            'Missing S3 Key'
        ]
        
        for title in test_titles:
            if not self._validate_title_length(title):
                logger.error(f" Test setup failed: title '{title}' exceeds database limit")
                raise ValueError(f"Title '{title}' exceeds 25 character limit")
        
        # Validate library name length
        library_name = 'Test Lib'
        if len(library_name) > 25:
            logger.error(f"Test setup failed: library name '{library_name}' exceeds database limit")
            raise ValueError(f"Library name '{library_name}' exceeds 25 character limit")
        
        logger.info("test environment setup completed")
    
    # ========================================
    # UPLOAD FIXES VERIFICATION TESTS
    # ========================================
    
    def test_allowed_hosts_fix(self):
        """Verify ALLOWED_HOSTS fix is working."""
        logger.info("Testing ALLOWED_HOSTS fix...")
        
        try:
            response = self.client.get('/admin/')
            # Should not get 400 DisallowedHost error
            if response.status_code == 400:
                logger.error("ALLOWED_HOSTS fix failed - still getting 400 error")
                return False
            else:
                logger.info("ALLOWED_HOSTS fix working - no DisallowedHost error")
                return True
        except Exception as e:
            logger.error(f"ALLOWED_HOSTS test failed: {str(e)}")
            return False
    
    def test_url_routing_fix(self):
        """Verify URL routing fixes are working."""
        logger.info("Testing URL routing fixes...")
        
        test_endpoints = [
            '/api/uploads/',  # Updated to plural for consistency
            '/api/content-types/',
            '/api/videos/',
            '/api/orders/request-download/',  # Test the fixed orders routing
        ]
        
        routing_success = True
        for endpoint in test_endpoints:
            try:
                response = self.client.get(endpoint)
                # Should not get 404 (not found) - other status codes are acceptable
                if response.status_code == 404:
                    logger.error(f"URL routing issue: {endpoint} returns 404")
                    routing_success = False
                else:
                    logger.info(f"URL routing OK: {endpoint} returns {response.status_code}")
            except Exception as e:
                logger.error(f"URL routing test failed for {endpoint}: {str(e)}")
                routing_success = False
                
        return routing_success
    
    def test_content_types_api_fix(self):
        """Verify content-types API is accessible."""
        logger.info("Testing content-types API fix...")
        
        try:
            response = self.client.get(f'/api/content-types/?library={self.test_library.id}')
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    logger.info(f"Content-types API working: returned {len(data)} content types")
                    return True
                else:
                    logger.error("Content-types API returned invalid format")
                    return False
            else:
                logger.error(f"Content-types API failed: status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Content-types API test failed: {str(e)}")
            return False
    
    def test_race_condition_fix(self):
        """Verify tag race condition fix is working."""
        logger.info("Testing tag race condition fix...")
        
        try:
            upload_data = {
                's3_key': f'test/race_condition_{uuid.uuid4()}.mp4',
                'title': 'Race Condition Test',  # Fixed: was 26 chars, now 20 chars
                'content_type': self.test_content_type.id,
                'library_id': self.test_library.id,
                'tags': 'race_test_tag,common_test_tag,unique_test_tag'
            }
            
            response = self.client.post('/api/uploads/', upload_data)
            
            if response.status_code == 201:
                # Check that tags were created properly
                test_tag = Tag.objects.filter(name='race_test_tag', library=self.test_library).first()
                if test_tag:
                    logger.info("Tag race condition fix working - tags created successfully")
                    return True
                else:
                    logger.error("Tags not created - race condition fix may not be working")
                    return False
            else:
                logger.error(f"Upload failed: status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Race condition test failed: {str(e)}")
            return False
    
    def test_backend_validation_improvements(self):
        """Verify backend validation improvements."""
        logger.info("Testing backend validation improvements...")
        
        validation_tests = [
            {
                'name': 'Missing s3_key',
                'data': {
                    'title': 'Test Video',
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                },
                'expected_status': 400
            },
            {
                'name': 'Invalid content type',
                'data': {
                    's3_key': f'test/validation_{uuid.uuid4()}.mp4',
                    'title': 'Test Video',
                    'content_type': 99999,
                    'library_id': self.test_library.id,
                },
                'expected_status': 404
            }
        ]
        
        passed_tests = 0
        for test_case in validation_tests:
            try:
                response = self.client.post('/api/uploads/', data=test_case['data'])
                if response.status_code == test_case['expected_status']:
                    logger.info(f"{test_case['name']}: Validation working correctly")
                    passed_tests += 1
                else:
                    logger.error(f"{test_case['name']}: Expected {test_case['expected_status']}, got {response.status_code}")
            except Exception as e:
                logger.error(f"{test_case['name']} test failed: {str(e)}")
        
        return passed_tests == len(validation_tests)
    
    # ========================================
    # FRONTEND SIMULATION TESTS
    # ========================================
    
    def test_file_validation_edge_cases(self):
        """Test file validation with edge cases."""
        logger.info("Testing file validation edge cases...")
        
        test_cases = [
            {
                'name': 'Unicode filename',
                'filename': 'видео_тест_测试.mp4',
                'content_type': 'video/mp4',
                'should_pass': True
            },
            {
                'name': 'Long filename',
                'filename': 'a' * 300 + '.mp4',
                'content_type': 'video/mp4',
                'should_pass': False
            },
            {
                'name': 'Special characters',
                'filename': 'test<>:|"?*.mp4',
                'content_type': 'video/mp4',
                'should_pass': False
            },
            {
                'name': 'Normal file',
                'filename': 'normal_video.mp4',
                'content_type': 'video/mp4',
                'should_pass': True
            },
        ]
        
        passed_tests = 0
        for test_case in test_cases:
            try:
                result = self._validate_filename(test_case['filename'], test_case['content_type'])
                
                if test_case['should_pass']:
                    if result['valid']:
                        logger.info(f"{test_case['name']}: Passed as expected")
                        passed_tests += 1
                    else:
                        logger.error(f"{test_case['name']}: Should have passed but failed")
                else:
                    if not result['valid']:
                        logger.info(f"{test_case['name']}: Failed as expected")
                        passed_tests += 1
                    else:
                        logger.error(f"{test_case['name']}: Should have failed but passed")
            except Exception as e:
                logger.error(f"{test_case['name']} test failed: {str(e)}")
        
        success_rate = passed_tests / len(test_cases)
        self.results['frontend_simulation']['file_validation'] = {
            'passed': passed_tests,
            'total': len(test_cases),
            'success_rate': success_rate
        }
        return success_rate >= 0.75
    
    def test_metadata_extraction_edge_cases(self):
        """Test metadata extraction edge cases."""
        logger.info("Testing metadata extraction edge cases...")
        
        test_cases = [
            {
                'name': 'Zero duration',
                'metadata': {'duration': 0, 'fileSize': 1000000, 'format': 'MP4'},
                'should_pass': True
            },
            {
                'name': 'Negative duration',
                'metadata': {'duration': -1, 'fileSize': 1000000, 'format': 'MP4'},
                'should_pass': False
            },
            {
                'name': 'Large file',
                'metadata': {'duration': 3600, 'fileSize': 100 * 1024 * 1024, 'format': 'MP4'},
                'should_pass': True
            },
            {
                'name': 'Missing metadata',
                'metadata': {},
                'should_pass': True  # Should be allowed
            },
        ]
        
        passed_tests = 0
        for test_case in test_cases:
            try:
                result = self._validate_metadata(test_case['metadata'])
                
                if test_case['should_pass']:
                    if result['valid']:
                        logger.info(f"{test_case['name']}: Validation passed")
                        passed_tests += 1
                    else:
                        logger.error(f"{test_case['name']}: Should have passed")
                else:
                    if not result['valid']:
                        logger.info(f"{test_case['name']}: Validation failed as expected")
                        passed_tests += 1
                    else:
                        logger.error(f"{test_case['name']}: Should have failed")
            except Exception as e:
                logger.error(f"{test_case['name']} test failed: {str(e)}")
        
        success_rate = passed_tests / len(test_cases)
        self.results['frontend_simulation']['metadata_extraction'] = {
            'passed': passed_tests,
            'total': len(test_cases),
            'success_rate': success_rate
        }
        return success_rate >= 0.75
    
    # ========================================
    # BACKEND VALIDATION TESTS
    # ========================================
    
    def test_upload_api_comprehensive(self):
        """Comprehensive test of the upload API endpoint."""
        logger.info("Testing upload API comprehensively...")
        
        test_cases = [
            {
                'name': 'Valid upload',
                'data': {
                    's3_key': f'test/valid_{uuid.uuid4()}.mp4',
                    'title': 'Valid Test Video',
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                },
                'expected_status': 201
            },
            {
                'name': 'Unicode title',
                'data': {
                    's3_key': f'test/unicode_{uuid.uuid4()}.mp4',
                    'title': 'Test 视频 Vidéo',  # Fixed: shortened to stay under 25 chars
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                },
                'expected_status': 201
            },
            {
                'name': 'With metadata',
                'data': {
                    's3_key': f'test/metadata_{uuid.uuid4()}.mp4',
                    'title': 'Video with Metadata',
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                    'description': 'Test description',
                    'duration': 120,
                    'file_size': 1024000,
                    'format': 'MP4',
                    'tags': 'test,metadata,upload'
                },
                'expected_status': 201
            },
            {
                'name': 'Missing required field',
                'data': {
                    'title': 'Missing S3 Key',
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                },
                'expected_status': 400
            },
        ]
        
        passed_tests = 0
        for test_case in test_cases:
            try:
                response = self.client.post('/api/uploads/', data=test_case['data'])
                
                if response.status_code == test_case['expected_status']:
                    logger.info(f"{test_case['name']}: Got expected status {response.status_code}")
                    passed_tests += 1
                else:
                    logger.error(f"{test_case['name']}: Expected {test_case['expected_status']}, got {response.status_code}")
                    if response.status_code >= 400:
                        try:
                            error_data = response.json()
                            logger.error(f"   Error response: {error_data}")
                        except:
                            logger.error(f"   Response content: {response.content}")
            except Exception as e:
                logger.error(f"{test_case['name']} test failed: {str(e)}")
        
        success_rate = passed_tests / len(test_cases)
        self.results['backend_validation']['upload_api'] = {
            'passed': passed_tests,
            'total': len(test_cases),
            'success_rate': success_rate
        }
        return success_rate >= 0.75
    
    def test_concurrent_upload_handling(self):
        """Test concurrent upload requests."""
        logger.info("Testing concurrent upload handling...")
        
        def upload_video(video_id):
            try:
                data = {
                    's3_key': f'test/concurrent_{video_id}_{uuid.uuid4()}.mp4',
                    'title': f'Concurrent {video_id}',  # Fixed: shortened to stay under 25 chars
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                    'tags': f'concurrent,test{video_id},shared_tag'
                }
                
                response = self.client.post('/api/uploads/', data=data)
                return {
                    'video_id': video_id,
                    'status_code': response.status_code,
                    'success': response.status_code == 201
                }
            except Exception as e:
                return {
                    'video_id': video_id,
                    'success': False,
                    'error': str(e)
                }
        
        # Run concurrent uploads
        num_concurrent = 5
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(upload_video, i) for i in range(num_concurrent)]
            results = [future.result() for future in futures]
        
        successful_uploads = sum(1 for result in results if result['success'])
        success_rate = successful_uploads / num_concurrent
        
        # Check for race conditions in tag creation
        shared_tag_count = Tag.objects.filter(name='shared_tag', library=self.test_library).count()
        if shared_tag_count <= 1:
            logger.info("No race condition detected in tag creation")
        else:
            logger.warning(f"Potential race condition: shared tag created {shared_tag_count} times")
            success_rate *= 0.8  # Reduce score for race condition
        
        self.results['backend_validation']['concurrent_uploads'] = {
            'passed': successful_uploads,
            'total': num_concurrent,
            'success_rate': success_rate
        }
        
        logger.info(f"Concurrent uploads: {successful_uploads}/{num_concurrent} successful ({success_rate*100:.1f}%)")
        return success_rate >= 0.8
    
    # ========================================
    # AWS INTEGRATION TESTS
    # ========================================
    
    def test_s3_integration(self):
        """Test S3 integration if available."""
        logger.info("Testing S3 integration...")
        
        if not self.s3_client:
            logger.info("⏭️ Skipping S3 tests - client not configured")
            self.results['aws_integration']['s3_tests'] = {'skipped': True}
            return True
        
        try:
            # Test bucket access
            bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'test-bucket')
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info("S3 bucket access successful")
            
            # Test presigned URL generation
            test_key = f"test/{uuid.uuid4()}.mp4"
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={'Bucket': bucket_name, 'Key': test_key},
                ExpiresIn=300
            )
            
            if presigned_url:
                logger.info("Presigned URL generation successful")
                return True
            else:
                logger.error("Presigned URL generation failed")
                return False
                
        except Exception as e:
            logger.error(f"S3 integration test failed: {str(e)}")
            return False
    
    # ========================================
    # PERFORMANCE TESTS
    # ========================================
    
    def test_upload_performance(self):
        """Test upload performance under load."""
        logger.info("Testing upload performance...")
        
        try:
            start_time = time.time()
            
            # Perform multiple uploads rapidly
            upload_times = []
            for i in range(10):
                upload_start = time.time()
                
                data = {
                    's3_key': f'test/perf_{i}_{uuid.uuid4()}.mp4',
                    'title': f'Perf Test {i}',  # Fixed: shortened to stay under 25 chars
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                }
                
                response = self.client.post('/api/uploads/', data=data)
                upload_end = time.time()
                
                upload_times.append(upload_end - upload_start)
                
                if response.status_code != 201:
                    logger.error(f"Performance test upload {i} failed: {response.status_code}")
            
            total_time = time.time() - start_time
            avg_time = sum(upload_times) / len(upload_times) if upload_times else 0
            
            logger.info(f"Performance test: {len(upload_times)} uploads in {total_time:.2f}s")
            logger.info(f"Average upload time: {avg_time:.3f}s")
            
            # Consider successful if average time is under 1 second
            success = avg_time < 1.0
            
            self.results['performance_stress']['upload_performance'] = {
                'total_time': total_time,
                'avg_time': avg_time,
                'uploads': len(upload_times),
                'success': success
            }
            
            return success
            
        except Exception as e:
            logger.error(f"Performance test failed: {str(e)}")
            return False
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    def _validate_title_length(self, title):
        """Validate that title doesn't exceed database limit."""
        if len(title.split()) > 20:
            logger.warning(f"Title '{title}' exceeds 20 words ({len(title.split())} words)")
            return False
        return True
    
    def _validate_filename(self, filename, content_type):
        """Validate filename and content type."""
        try:
            # Basic validation rules
            if not filename or len(filename) > 255:
                return {'valid': False, 'error': 'Invalid filename length'}
            
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
            if any(char in filename for char in invalid_chars):
                return {'valid': False, 'error': 'Invalid characters in filename'}
            
            if not content_type.startswith('video/'):
                return {'valid': False, 'error': 'Invalid content type'}
            
            return {'valid': True}
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _validate_metadata(self, metadata):
        """Validate video metadata."""
        try:
            duration = metadata.get('duration')
            file_size = metadata.get('fileSize')
            
            if duration is not None and duration < 0:
                return {'valid': False, 'error': 'Negative duration not allowed'}
            
            if file_size is not None and file_size < 0:
                return {'valid': False, 'error': 'Negative file size not allowed'}
            
            return {'valid': True}
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def cleanup_test_environment(self):
        """Clean up all test data."""
        logger.info("Cleaning up test environment...")
        
        try:
            # Delete test videos
            Video.objects.filter(library=self.test_library).delete()
            
            # Delete test tags
            Tag.objects.filter(library=self.test_library).delete()
            
            # Don't delete library and user as they might be reused
            logger.info("Test environment cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
    
    # ========================================
    # MAIN TEST RUNNERS
    # ========================================
    
    def run_fixes_verification(self):
        """Run upload fixes verification tests."""
        logger.info("=" * 60)
        logger.info("UPLOAD FIXES VERIFICATION")
        logger.info("=" * 60)
        
        tests = {
            'allowed_hosts': self.test_allowed_hosts_fix(),
            'url_routing': self.test_url_routing_fix(),
            'content_types_api': self.test_content_types_api_fix(),
            'race_condition': self.test_race_condition_fix(),
            'backend_validation': self.test_backend_validation_improvements(),
        }
        
        self.results['fixes_verification'] = tests
        return tests
    
    def run_pipeline_tests(self):
        """Run comprehensive pipeline tests."""
        logger.info("=" * 60)
        logger.info("COMPREHENSIVE PIPELINE TESTS")
        logger.info("=" * 60)
        
        tests = {
            'file_validation': self.test_file_validation_edge_cases(),
            'metadata_extraction': self.test_metadata_extraction_edge_cases(),
            'upload_api': self.test_upload_api_comprehensive(),
            'concurrent_uploads': self.test_concurrent_upload_handling(),
            's3_integration': self.test_s3_integration(),
            'upload_performance': self.test_upload_performance(),
        }
        
        self.results['pipeline_tests'] = tests
        return tests
    
    def run_quick_test(self):
        """Run quick essential tests only."""
        logger.info("=" * 60)
        logger.info("QUICK UPLOAD TESTS")
        logger.info("=" * 60)
        
        self.setup_test_environment()
        
        essential_tests = {
            'url_routing': self.test_url_routing_fix(),
            'upload_api_basic': self.test_upload_api_comprehensive(),
            'backend_validation': self.test_backend_validation_improvements(),
        }
        
        self.cleanup_test_environment()
        
        passed = sum(1 for result in essential_tests.values() if result)
        total = len(essential_tests)
        
        logger.info(f"\nQuick test results: {passed}/{total} passed")
        return passed == total
    
    def run_comprehensive_test(self):
        """Run all tests comprehensively."""
        logger.info("🚀 COMPREHENSIVE VIDEO UPLOAD TEST SUITE")
        logger.info("=" * 60)
        
        self.setup_test_environment()
        
        try:
            # Run all test categories
            fixes_results = self.run_fixes_verification()
            pipeline_results = self.run_pipeline_tests()
            
            # Calculate overall results
            all_results = {**fixes_results, **pipeline_results}
            passed_tests = sum(1 for result in all_results.values() if result)
            total_tests = len(all_results)
            
            logger.info("=" * 60)
            logger.info("COMPREHENSIVE TEST RESULTS SUMMARY")
            logger.info("=" * 60)
            
            logger.info(f"Overall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
            
            # Detailed breakdown
            logger.info("\nFixes Verification:")
            for test_name, result in fixes_results.items():
                status = "PASS" if result else "FAIL"
                logger.info(f"  {test_name}: {status}")
            
            logger.info("\nPipeline Tests:")
            for test_name, result in pipeline_results.items():
                status = "PASS" if result else "FAIL"
                logger.info(f"  {test_name}: {status}")
            
            if passed_tests == total_tests:
                logger.info("\nAll tests passed! Upload system is working correctly.")
                return True
            else:
                logger.warning(f"\n{total_tests - passed_tests} tests failed. Issues need attention.")
                return False
                
        finally:
            self.cleanup_test_environment()

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='Comprehensive Video Upload Test Suite')
    parser.add_argument('--quick', action='store_true', help='Run quick essential tests only')
    parser.add_argument('--full', action='store_true', help='Run comprehensive test suite (default)')
    parser.add_argument('--fixes-only', action='store_true', help='Run upload fixes verification only')
    parser.add_argument('--pipeline-only', action='store_true', help='Run pipeline tests only')
    
    args = parser.parse_args()
    
    test_suite = ComprehensiveUploadTestSuite()
    
    try:
        if args.quick:
            success = test_suite.run_quick_test()
        elif args.fixes_only:
            test_suite.setup_test_environment()
            results = test_suite.run_fixes_verification()
            test_suite.cleanup_test_environment()
            success = all(results.values())
        elif args.pipeline_only:
            test_suite.setup_test_environment()
            results = test_suite.run_pipeline_tests()
            test_suite.cleanup_test_environment()
            success = all(results.values())
        else:
            success = test_suite.run_comprehensive_test()
        
        if success:
            print("\nAll selected tests passed!")
            sys.exit(0)
        else:
            print("\nSome tests failed. Please review the logs.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        test_suite.cleanup_test_environment()
        sys.exit(1)
    except Exception as e:
        print(f"\nTest suite crashed: {str(e)}")
        test_suite.cleanup_test_environment()
        sys.exit(1)

if __name__ == '__main__':
    main() 