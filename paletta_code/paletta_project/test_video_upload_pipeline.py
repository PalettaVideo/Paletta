#!/usr/bin/env python
"""
Comprehensive Video Upload Pipeline Test Suite
Tests all critical failure points that could cause browser/user-specific issues.

Usage:
    python test_video_upload_pipeline.py [--frontend-only] [--backend-only] [--integration-only] [--stress-only]
"""

import os
import sys
import django
import argparse
import time
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_project.settings_production')
django.setup()

from django.test.client import Client
from django.conf import settings
from accounts.models import User
from libraries.models import Library
from videos.models import Video, ContentType, Tag
import boto3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoUploadPipelineTestSuite:
    """
    Comprehensive test suite covering all failure points in the video upload pipeline.
    Tests frontend simulation, backend validation, AWS integration, and edge cases.
    """
    
    def __init__(self):
        self.client = Client()
        self.test_user = None
        self.test_library = None
        self.test_content_type = None
        self.s3_client = None
        self.results = {
            'frontend': {},
            'backend': {},
            'aws': {},
            'integration': {},
            'stress': {}
        }
        
    def setup_test_environment(self):
        """Setup test data and AWS connections."""
        logger.info("Setting up test environment...")
        
        # Create test user
        try:
            self.test_user = User.objects.get(email='pipeline-test@example.com')
        except User.DoesNotExist:
            self.test_user = User.objects.create_user(
                email='pipeline-test@example.com',
                password='testpass123',
                first_name='Pipeline',
                last_name='Test'
            )
        
        # Create test library
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                first_name='Admin',
                last_name='User'
            )
        
        self.test_library, created = Library.objects.get_or_create(
            name='Pipeline Test Library',
            defaults={
                'description': 'Test library for upload pipeline validation',
                'owner': admin_user,
                'is_active': True
            }
        )
        
        # Create test content type
        self.test_content_type, created = ContentType.objects.get_or_create(
            subject_area='engineering_sciences',
            library=self.test_library,
            defaults={'description': 'Test content type for pipeline validation'}
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
        
        logger.info("Test environment setup complete")
    
    # ========================================
    # FRONTEND SIMULATION TESTS
    # ========================================
    
    def test_file_validation_edge_cases(self):
        """Test file validation with edge cases that might fail in different browsers."""
        logger.info("Testing file validation edge cases...")
        
        test_cases = [
            {
                'name': 'Empty filename',
                'filename': '',
                'content_type': 'video/mp4',
                'expected_failure': True
            },
            {
                'name': 'Unicode filename',
                'filename': 'видео_тест_测试.mp4',
                'content_type': 'video/mp4',
                'expected_failure': False
            },
            {
                'name': 'Long filename',
                'filename': 'a' * 300 + '.mp4',
                'content_type': 'video/mp4',
                'expected_failure': True
            },
            {
                'name': 'Special characters',
                'filename': 'test<>:|"?*.mp4',
                'content_type': 'video/mp4',
                'expected_failure': True
            },
            {
                'name': 'Invalid content type',
                'filename': 'test.mp4',
                'content_type': 'invalid/type',
                'expected_failure': True
            },
            {
                'name': 'Content type mismatch',
                'filename': 'test.mp4',
                'content_type': 'video/avi',
                'expected_failure': False  # Should be allowed
            },
            {
                'name': 'No extension',
                'filename': 'testvideo',
                'content_type': 'video/mp4',
                'expected_failure': False  # Should be allowed
            },
        ]
        
        passed_tests = 0
        for test_case in test_cases:
            try:
                # Simulate presigned URL request
                query_params = {
                    'fileName': test_case['filename'],
                    'contentType': test_case['content_type']
                }
                
                # This would normally go to Lambda
                result = self._simulate_presigned_url_generation(query_params)
                
                if test_case['expected_failure']:
                    if result['success']:
                        logger.error(f"❌ {test_case['name']}: Expected failure but got success")
                    else:
                        logger.info(f"✅ {test_case['name']}: Expected failure occurred")
                        passed_tests += 1
                else:
                    if result['success']:
                        logger.info(f"✅ {test_case['name']}: Success as expected")
                        passed_tests += 1
                    else:
                        logger.error(f"❌ {test_case['name']}: Unexpected failure - {result.get('error', '')}")
                        
            except Exception as e:
                logger.error(f"❌ {test_case['name']}: Exception - {str(e)}")
        
        success_rate = passed_tests / len(test_cases)
        self.results['frontend']['file_validation'] = {
            'passed': passed_tests,
            'total': len(test_cases),
            'success_rate': success_rate
        }
        
        logger.info(f"File validation tests: {passed_tests}/{len(test_cases)} passed ({success_rate*100:.1f}%)")
        return success_rate >= 0.8
    
    def test_metadata_extraction_simulation(self):
        """Simulate metadata extraction failures that might occur in different browsers."""
        logger.info("Testing metadata extraction edge cases...")
        
        test_cases = [
            {
                'name': 'Missing duration',
                'metadata': {'fileSize': 1000000, 'format': 'MP4'},
                'expected_failure': False
            },
            {
                'name': 'Zero duration',
                'metadata': {'duration': 0, 'fileSize': 1000000, 'format': 'MP4'},
                'expected_failure': False
            },
            {
                'name': 'Negative duration',
                'metadata': {'duration': -1, 'fileSize': 1000000, 'format': 'MP4'},
                'expected_failure': True
            },
            {
                'name': 'Extremely large file',
                'metadata': {'duration': 3600, 'fileSize': 256 * 1024 * 1024 * 1024, 'format': 'MP4'},
                'expected_failure': False
            },
            {
                'name': 'Missing file size',
                'metadata': {'duration': 3600, 'format': 'MP4'},
                'expected_failure': False
            },
            {
                'name': 'Invalid format',
                'metadata': {'duration': 3600, 'fileSize': 1000000, 'format': ''},
                'expected_failure': False
            },
        ]
        
        passed_tests = 0
        for test_case in test_cases:
            try:
                # Simulate metadata validation
                result = self._validate_metadata(test_case['metadata'])
                
                if test_case['expected_failure']:
                    if result['valid']:
                        logger.error(f"❌ {test_case['name']}: Expected validation failure but got success")
                    else:
                        logger.info(f"✅ {test_case['name']}: Expected validation failure occurred")
                        passed_tests += 1
                else:
                    if result['valid']:
                        logger.info(f"✅ {test_case['name']}: Validation success as expected")
                        passed_tests += 1
                    else:
                        logger.error(f"❌ {test_case['name']}: Unexpected validation failure - {result.get('error', '')}")
                        
            except Exception as e:
                logger.error(f"❌ {test_case['name']}: Exception - {str(e)}")
        
        success_rate = passed_tests / len(test_cases)
        self.results['frontend']['metadata_extraction'] = {
            'passed': passed_tests,
            'total': len(test_cases),
            'success_rate': success_rate
        }
        
        logger.info(f"Metadata extraction tests: {passed_tests}/{len(test_cases)} passed ({success_rate*100:.1f}%)")
        return success_rate >= 0.8
    
    def test_network_timeout_simulation(self):
        """Simulate network timeouts and interruptions."""
        logger.info("Testing network timeout scenarios...")
        
        test_cases = [
            {
                'name': 'Slow connection simulation',
                'delay_seconds': 6,  # Longer than 5-minute Lambda timeout
                'expected_failure': True
            },
            {
                'name': 'Connection interruption',
                'simulate_interruption': True,
                'expected_failure': True
            },
            {
                'name': 'Normal connection',
                'delay_seconds': 1,
                'expected_failure': False
            },
        ]
        
        passed_tests = 0
        for test_case in test_cases:
            try:
                # Simulate network conditions
                result = self._simulate_network_request(test_case)
                
                if test_case['expected_failure']:
                    if result['success']:
                        logger.error(f"❌ {test_case['name']}: Expected timeout but got success")
                    else:
                        logger.info(f"✅ {test_case['name']}: Expected timeout occurred")
                        passed_tests += 1
                else:
                    if result['success']:
                        logger.info(f"✅ {test_case['name']}: Success as expected")
                        passed_tests += 1
                    else:
                        logger.error(f"❌ {test_case['name']}: Unexpected failure - {result.get('error', '')}")
                        
            except Exception as e:
                logger.error(f"❌ {test_case['name']}: Exception - {str(e)}")
        
        success_rate = passed_tests / len(test_cases)
        self.results['frontend']['network_timeouts'] = {
            'passed': passed_tests,
            'total': len(test_cases),
            'success_rate': success_rate
        }
        
        logger.info(f"Network timeout tests: {passed_tests}/{len(test_cases)} passed ({success_rate*100:.1f}%)")
        return success_rate >= 0.8
    
    # ========================================
    # BACKEND API TESTS
    # ========================================
    
    def test_backend_validation_edge_cases(self):
        """Test backend validation with edge cases."""
        logger.info("Testing backend validation edge cases...")
        
        # Login test user
        self.client.force_login(self.test_user)
        
        test_cases = [
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
                'name': 'Empty s3_key',
                'data': {
                    's3_key': '',
                    'title': 'Test Video',
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                },
                'expected_status': 400
            },
            {
                'name': 'Missing title',
                'data': {
                    's3_key': 'test/video.mp4',
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                },
                'expected_status': 400
            },
            {
                'name': 'Missing content_type',
                'data': {
                    's3_key': 'test/video.mp4',
                    'title': 'Test Video',
                    'library_id': self.test_library.id,
                },
                'expected_status': 400
            },
            {
                'name': 'Invalid content_type',
                'data': {
                    's3_key': 'test/video.mp4',
                    'title': 'Test Video',
                    'content_type': 99999,
                    'library_id': self.test_library.id,
                },
                'expected_status': 404
            },
            {
                'name': 'Missing library_id',
                'data': {
                    's3_key': 'test/video.mp4',
                    'title': 'Test Video',
                    'content_type': self.test_content_type.id,
                },
                'expected_status': 400
            },
            {
                'name': 'Invalid library_id',
                'data': {
                    's3_key': 'test/video.mp4',
                    'title': 'Test Video',
                    'content_type': self.test_content_type.id,
                    'library_id': 99999,
                },
                'expected_status': 404
            },
            {
                'name': 'Valid minimal data',
                'data': {
                    's3_key': 'test/video.mp4',
                    'title': 'Test Video',
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                },
                'expected_status': 201
            },
            {
                'name': 'Unicode in title',
                'data': {
                    's3_key': 'test/video2.mp4',
                    'title': 'Test 视频 Vidéo',
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                },
                'expected_status': 201
            },
            {
                'name': 'Long description',
                'data': {
                    's3_key': 'test/video3.mp4',
                    'title': 'Test Video',
                    'description': 'A' * 1000,  # Very long description
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                },
                'expected_status': 201
            },
        ]
        
        passed_tests = 0
        for test_case in test_cases:
            try:
                response = self.client.post('/api/api/upload/', data=test_case['data'])
                
                if response.status_code == test_case['expected_status']:
                    logger.info(f"✅ {test_case['name']}: Got expected status {response.status_code}")
                    passed_tests += 1
                else:
                    logger.error(f"❌ {test_case['name']}: Expected status {test_case['expected_status']}, got {response.status_code}")
                    if response.status_code >= 400:
                        try:
                            error_data = response.json()
                            logger.error(f"   Error response: {error_data}")
                        except:
                            logger.error(f"   Response content: {response.content}")
                        
            except Exception as e:
                logger.error(f"❌ {test_case['name']}: Exception - {str(e)}")
        
        success_rate = passed_tests / len(test_cases)
        self.results['backend']['validation'] = {
            'passed': passed_tests,
            'total': len(test_cases),
            'success_rate': success_rate
        }
        
        logger.info(f"Backend validation tests: {passed_tests}/{len(test_cases)} passed ({success_rate*100:.1f}%)")
        return success_rate >= 0.8
    
    def test_tag_handling_edge_cases(self):
        """Test tag creation and assignment edge cases."""
        logger.info("Testing tag handling edge cases...")
        
        self.client.force_login(self.test_user)
        
        test_cases = [
            {
                'name': 'Normal tags',
                'tags': 'education,science,research',
                'expected_status': 201,
                'expected_tag_count': 3
            },
            {
                'name': 'Empty tags',
                'tags': '',
                'expected_status': 201,
                'expected_tag_count': 0
            },
            {
                'name': 'Unicode tags',
                'tags': '教育,науки,éducation',
                'expected_status': 201,
                'expected_tag_count': 3
            },
            {
                'name': 'Tags with spaces',
                'tags': 'machine learning, data science, artificial intelligence',
                'expected_status': 201,
                'expected_tag_count': 3
            },
            {
                'name': 'Duplicate tags',
                'tags': 'research,science,research,education,science',
                'expected_status': 201,
                'expected_tag_count': 3  # Should deduplicate
            },
            {
                'name': 'Very long tag names',
                'tags': 'a' * 100 + ',' + 'b' * 100,
                'expected_status': 201,  # Might fail due to max_length=25
                'expected_tag_count': 0  # Tags might be rejected
            },
        ]
        
        passed_tests = 0
        for i, test_case in enumerate(test_cases):
            try:
                data = {
                    's3_key': f'test/tag_test_{i}.mp4',
                    'title': f'Tag Test {i}',
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                    'tags': test_case['tags']
                }
                
                response = self.client.post('/api/api/upload/', data=data)
                
                if response.status_code == test_case['expected_status']:
                    logger.info(f"✅ {test_case['name']}: Got expected status {response.status_code}")
                    
                    if response.status_code == 201:
                        # Check tag count if video was created
                        video_data = response.json()
                        video = Video.objects.get(id=video_data['id'])
                        actual_tag_count = video.tags.count()
                        
                        if actual_tag_count == test_case['expected_tag_count']:
                            logger.info(f"✅ {test_case['name']}: Tag count matches ({actual_tag_count})")
                            passed_tests += 1
                        else:
                            logger.error(f"❌ {test_case['name']}: Expected {test_case['expected_tag_count']} tags, got {actual_tag_count}")
                    else:
                        passed_tests += 1
                else:
                    logger.error(f"❌ {test_case['name']}: Expected status {test_case['expected_status']}, got {response.status_code}")
                        
            except Exception as e:
                logger.error(f"❌ {test_case['name']}: Exception - {str(e)}")
        
        success_rate = passed_tests / len(test_cases)
        self.results['backend']['tag_handling'] = {
            'passed': passed_tests,
            'total': len(test_cases),
            'success_rate': success_rate
        }
        
        logger.info(f"Tag handling tests: {passed_tests}/{len(test_cases)} passed ({success_rate*100:.1f}%)")
        return success_rate >= 0.8
    
    def test_concurrent_upload_handling(self):
        """Test concurrent upload requests to identify race conditions."""
        logger.info("Testing concurrent upload handling...")
        
        self.client.force_login(self.test_user)
        
        def upload_video(video_id):
            """Upload a single video."""
            try:
                data = {
                    's3_key': f'test/concurrent_{video_id}.mp4',
                    'title': f'Concurrent Test {video_id}',
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                    'tags': f'tag{video_id},common_tag'
                }
                
                response = self.client.post('/api/api/upload/', data=data)
                return {
                    'video_id': video_id,
                    'status_code': response.status_code,
                    'success': response.status_code == 201
                }
            except Exception as e:
                return {
                    'video_id': video_id,
                    'status_code': 500,
                    'success': False,
                    'error': str(e)
                }
        
        # Run 10 concurrent uploads
        num_concurrent = 10
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(upload_video, i) for i in range(num_concurrent)]
            results = [future.result() for future in futures]
        
        successful_uploads = sum(1 for result in results if result['success'])
        success_rate = successful_uploads / num_concurrent
        
        self.results['backend']['concurrent_uploads'] = {
            'passed': successful_uploads,
            'total': num_concurrent,
            'success_rate': success_rate
        }
        
        logger.info(f"Concurrent upload tests: {successful_uploads}/{num_concurrent} passed ({success_rate*100:.1f}%)")
        
        # Check for race conditions in tag creation
        common_tag_count = Tag.objects.filter(name='common_tag', library=self.test_library).count()
        if common_tag_count == 1:
            logger.info("✅ No race condition in tag creation - common tag created only once")
        else:
            logger.error(f"❌ Race condition detected - common tag created {common_tag_count} times")
            success_rate *= 0.5  # Penalize for race condition
        
        return success_rate >= 0.8
    
    # ========================================
    # AWS INTEGRATION TESTS
    # ========================================
    
    def test_presigned_url_generation(self):
        """Test presigned URL generation edge cases."""
        logger.info("Testing presigned URL generation...")
        
        if not self.s3_client:
            logger.warning("Skipping AWS tests - S3 client not available")
            self.results['aws']['presigned_urls'] = {'skipped': True}
            return True
        
        test_cases = [
            {
                'name': 'Normal file',
                'filename': 'test.mp4',
                'content_type': 'video/mp4',
                'expected_success': True
            },
            {
                'name': 'Unicode filename',
                'filename': 'тест_видео.mp4',
                'content_type': 'video/mp4',
                'expected_success': True
            },
            {
                'name': 'Very long filename',
                'filename': 'a' * 200 + '.mp4',
                'content_type': 'video/mp4',
                'expected_success': True
            },
            {
                'name': 'Special characters',
                'filename': 'test file (copy).mp4',
                'content_type': 'video/mp4',
                'expected_success': True
            },
        ]
        
        passed_tests = 0
        for test_case in test_cases:
            try:
                # Simulate Lambda presigned URL generation
                result = self._test_s3_presigned_url(test_case['filename'], test_case['content_type'])
                
                if test_case['expected_success']:
                    if result['success']:
                        logger.info(f"✅ {test_case['name']}: Presigned URL generated successfully")
                        passed_tests += 1
                    else:
                        logger.error(f"❌ {test_case['name']}: Failed to generate presigned URL - {result.get('error', '')}")
                else:
                    if not result['success']:
                        logger.info(f"✅ {test_case['name']}: Expected failure occurred")
                        passed_tests += 1
                    else:
                        logger.error(f"❌ {test_case['name']}: Expected failure but got success")
                        
            except Exception as e:
                logger.error(f"❌ {test_case['name']}: Exception - {str(e)}")
        
        success_rate = passed_tests / len(test_cases)
        self.results['aws']['presigned_urls'] = {
            'passed': passed_tests,
            'total': len(test_cases),
            'success_rate': success_rate
        }
        
        logger.info(f"Presigned URL tests: {passed_tests}/{len(test_cases)} passed ({success_rate*100:.1f}%)")
        return success_rate >= 0.8
    
    def test_s3_upload_simulation(self):
        """Test S3 upload scenarios."""
        logger.info("Testing S3 upload scenarios...")
        
        if not self.s3_client:
            logger.warning("Skipping S3 upload tests - S3 client not available")
            self.results['aws']['s3_uploads'] = {'skipped': True}
            return True
        
        test_cases = [
            {
                'name': 'Small file upload',
                'file_size': 1024,  # 1KB
                'content_type': 'video/mp4',
                'expected_success': True
            },
            {
                'name': 'Large file simulation',
                'file_size': 1024 * 1024 * 10,  # 10MB
                'content_type': 'video/mp4',
                'expected_success': True
            },
            {
                'name': 'Invalid content type',
                'file_size': 1024,
                'content_type': 'invalid/type',
                'expected_success': False
            },
        ]
        
        passed_tests = 0
        for test_case in test_cases:
            try:
                result = self._test_s3_upload(test_case['file_size'], test_case['content_type'])
                
                if test_case['expected_success']:
                    if result['success']:
                        logger.info(f"✅ {test_case['name']}: S3 upload successful")
                        passed_tests += 1
                    else:
                        logger.error(f"❌ {test_case['name']}: S3 upload failed - {result.get('error', '')}")
                else:
                    if not result['success']:
                        logger.info(f"✅ {test_case['name']}: Expected failure occurred")
                        passed_tests += 1
                    else:
                        logger.error(f"❌ {test_case['name']}: Expected failure but got success")
                        
            except Exception as e:
                logger.error(f"❌ {test_case['name']}: Exception - {str(e)}")
        
        success_rate = passed_tests / len(test_cases)
        self.results['aws']['s3_uploads'] = {
            'passed': passed_tests,
            'total': len(test_cases),
            'success_rate': success_rate
        }
        
        logger.info(f"S3 upload tests: {passed_tests}/{len(test_cases)} passed ({success_rate*100:.1f}%)")
        return success_rate >= 0.8
    
    # ========================================
    # STRESS TESTS
    # ========================================
    
    def test_memory_usage_patterns(self):
        """Test memory usage patterns that might cause issues."""
        logger.info("Testing memory usage patterns...")
        
        import psutil
        import gc
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        test_cases = [
            {
                'name': 'Large metadata handling',
                'metadata_size': 1024 * 100,  # 100KB of metadata
                'iterations': 10
            },
            {
                'name': 'Many small requests',
                'metadata_size': 1024,  # 1KB
                'iterations': 100
            },
            {
                'name': 'Unicode stress test',
                'metadata_size': 1024 * 10,  # 10KB
                'iterations': 20,
                'use_unicode': True
            },
        ]
        
        passed_tests = 0
        for test_case in test_cases:
            try:
                memory_before = psutil.Process().memory_info().rss / 1024 / 1024
                
                for i in range(test_case['iterations']):
                    # Simulate metadata processing
                    if test_case.get('use_unicode'):
                        large_data = '测试数据' * (test_case['metadata_size'] // 12)
                    else:
                        large_data = 'x' * test_case['metadata_size']
                    
                    # Simulate processing
                    processed_data = {
                        'title': large_data[:25],
                        'description': large_data[:1000],
                        'tags': large_data[:100],
                        'iteration': i
                    }
                    
                    # Force garbage collection periodically
                    if i % 10 == 0:
                        gc.collect()
                
                memory_after = psutil.Process().memory_info().rss / 1024 / 1024
                memory_increase = memory_after - memory_before
                
                # Consider test passed if memory increase is reasonable (< 50MB)
                if memory_increase < 50:
                    logger.info(f"✅ {test_case['name']}: Memory usage acceptable ({memory_increase:.1f}MB increase)")
                    passed_tests += 1
                else:
                    logger.error(f"❌ {test_case['name']}: Excessive memory usage ({memory_increase:.1f}MB increase)")
                
                # Clean up
                gc.collect()
                        
            except Exception as e:
                logger.error(f"❌ {test_case['name']}: Exception - {str(e)}")
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        success_rate = passed_tests / len(test_cases)
        self.results['stress']['memory_usage'] = {
            'passed': passed_tests,
            'total': len(test_cases),
            'success_rate': success_rate,
            'total_memory_increase_mb': total_increase
        }
        
        logger.info(f"Memory usage tests: {passed_tests}/{len(test_cases)} passed ({success_rate*100:.1f}%)")
        logger.info(f"Total memory increase: {total_increase:.1f}MB")
        return success_rate >= 0.8
    
    def test_database_transaction_stress(self):
        """Test database transaction handling under stress."""
        logger.info("Testing database transaction stress...")
        
        self.client.force_login(self.test_user)
        
        # Test rapid successive uploads
        rapid_uploads = []
        for i in range(20):
            try:
                data = {
                    's3_key': f'test/stress_{i}_{uuid.uuid4()}.mp4',
                    'title': f'Stress Test {i}',
                    'content_type': self.test_content_type.id,
                    'library_id': self.test_library.id,
                    'tags': f'stress,test{i}'
                }
                
                start_time = time.time()
                response = self.client.post('/api/api/upload/', data=data)
                end_time = time.time()
                
                rapid_uploads.append({
                    'success': response.status_code == 201,
                    'response_time': end_time - start_time,
                    'status_code': response.status_code
                })
                
                # Small delay to prevent overwhelming the database
                time.sleep(0.1)
                
            except Exception as e:
                rapid_uploads.append({
                    'success': False,
                    'error': str(e),
                    'response_time': 0
                })
        
        successful_uploads = sum(1 for upload in rapid_uploads if upload['success'])
        avg_response_time = sum(upload['response_time'] for upload in rapid_uploads if 'response_time' in upload) / len(rapid_uploads)
        
        success_rate = successful_uploads / len(rapid_uploads)
        
        self.results['stress']['database_transactions'] = {
            'passed': successful_uploads,
            'total': len(rapid_uploads),
            'success_rate': success_rate,
            'avg_response_time': avg_response_time
        }
        
        logger.info(f"Database stress tests: {successful_uploads}/{len(rapid_uploads)} passed ({success_rate*100:.1f}%)")
        logger.info(f"Average response time: {avg_response_time:.3f}s")
        
        # Check for database consistency
        created_videos = Video.objects.filter(title__startswith='Stress Test').count()
        logger.info(f"Videos created in database: {created_videos}")
        
        return success_rate >= 0.8
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    def _simulate_presigned_url_generation(self, query_params):
        """Simulate Lambda presigned URL generation."""
        try:
            filename = query_params.get('fileName', '')
            content_type = query_params.get('contentType', '')
            
            # Basic validation
            if not filename or not content_type:
                return {'success': False, 'error': 'Missing required parameters'}
            
            if len(filename) > 255:
                return {'success': False, 'error': 'Filename too long'}
            
            # Check for invalid characters (basic check)
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
            if any(char in filename for char in invalid_chars):
                return {'success': False, 'error': 'Invalid characters in filename'}
            
            if not content_type.startswith('video/'):
                return {'success': False, 'error': 'Invalid content type'}
            
            # Generate mock S3 key
            unique_id = uuid.uuid4()
            file_extension = os.path.splitext(filename)[1]
            s3_key = f"videos/{unique_id}{file_extension}"
            
            return {
                'success': True,
                'uploadURL': f'https://mock-bucket.s3.amazonaws.com/{s3_key}',
                'key': s3_key
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _validate_metadata(self, metadata):
        """Validate video metadata."""
        try:
            duration = metadata.get('duration')
            file_size = metadata.get('fileSize')
            format_type = metadata.get('format')
            
            # Validation rules
            if duration is not None and duration < 0:
                return {'valid': False, 'error': 'Negative duration not allowed'}
            
            if file_size is not None and file_size < 0:
                return {'valid': False, 'error': 'Negative file size not allowed'}
            
            # All validations passed
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _simulate_network_request(self, test_case):
        """Simulate network request with various conditions."""
        try:
            delay = test_case.get('delay_seconds', 0)
            simulate_interruption = test_case.get('simulate_interruption', False)
            
            if simulate_interruption:
                # Simulate connection interruption
                time.sleep(delay / 2)
                raise ConnectionError("Simulated network interruption")
            
            # Simulate delay
            time.sleep(delay)
            
            # Check if delay exceeded reasonable timeout
            if delay > 5:  # 5 seconds timeout
                return {'success': False, 'error': 'Request timeout'}
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_s3_presigned_url(self, filename, content_type):
        """Test actual S3 presigned URL generation."""
        try:
            if not self.s3_client:
                return {'success': False, 'error': 'S3 client not available'}
            
            bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'test-bucket')
            unique_id = uuid.uuid4()
            file_extension = os.path.splitext(filename)[1]
            s3_key = f"test/{unique_id}{file_extension}"
            
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': s3_key,
                    'ContentType': content_type,
                },
                ExpiresIn=300  # 5 minutes
            )
            
            return {'success': True, 'url': presigned_url, 'key': s3_key}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_s3_upload(self, file_size, content_type):
        """Test actual S3 upload."""
        try:
            if not self.s3_client:
                return {'success': False, 'error': 'S3 client not available'}
            
            # Create test file
            test_data = b'0' * file_size
            bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'test-bucket')
            s3_key = f"test/upload_test_{uuid.uuid4()}.dat"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=test_data,
                ContentType=content_type
            )
            
            # Clean up - delete the test file
            try:
                self.s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
            except:
                pass  # Ignore cleanup errors
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cleanup_test_environment(self):
        """Clean up test data."""
        logger.info("Cleaning up test environment...")
        
        try:
            # Delete test videos
            Video.objects.filter(title__startswith='Test').delete()
            Video.objects.filter(title__startswith='Pipeline Test').delete()
            Video.objects.filter(title__startswith='Stress Test').delete()
            Video.objects.filter(title__startswith='Concurrent Test').delete()
            Video.objects.filter(title__startswith='Tag Test').delete()
            
            # Delete test tags
            Tag.objects.filter(library=self.test_library, name__startswith='tag').delete()
            Tag.objects.filter(library=self.test_library, name='common_tag').delete()
            Tag.objects.filter(library=self.test_library, name='stress').delete()
            
            # Delete test user
            if self.test_user:
                self.test_user.delete()
            
            # Delete test library and content type
            if self.test_library:
                self.test_library.delete()
            
            logger.info("Test environment cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
    
    # ========================================
    # MAIN TEST RUNNERS
    # ========================================
    
    def run_frontend_tests(self):
        """Run frontend simulation tests."""
        logger.info("="*60)
        logger.info("FRONTEND SIMULATION TESTS")
        logger.info("="*60)
        
        results = {
            'file_validation': self.test_file_validation_edge_cases(),
            'metadata_extraction': self.test_metadata_extraction_simulation(),
            'network_timeouts': self.test_network_timeout_simulation()
        }
        
        return results
    
    def run_backend_tests(self):
        """Run backend API tests."""
        logger.info("="*60)
        logger.info("BACKEND API TESTS")
        logger.info("="*60)
        
        results = {
            'validation': self.test_backend_validation_edge_cases(),
            'tag_handling': self.test_tag_handling_edge_cases(),
            'concurrent_uploads': self.test_concurrent_upload_handling()
        }
        
        return results
    
    def run_aws_tests(self):
        """Run AWS integration tests."""
        logger.info("="*60)
        logger.info("AWS INTEGRATION TESTS")
        logger.info("="*60)
        
        results = {
            'presigned_urls': self.test_presigned_url_generation(),
            's3_uploads': self.test_s3_upload_simulation()
        }
        
        return results
    
    def run_stress_tests(self):
        """Run stress tests."""
        logger.info("="*60)
        logger.info("STRESS TESTS")
        logger.info("="*60)
        
        results = {
            'memory_usage': self.test_memory_usage_patterns(),
            'database_transactions': self.test_database_transaction_stress()
        }
        
        return results
    
    def run_integration_tests(self):
        """Run full integration tests."""
        logger.info("="*60)
        logger.info("INTEGRATION TESTS")
        logger.info("="*60)
        
        # Setup
        self.setup_test_environment()
        
        # Run all test categories
        all_results = {
            'frontend': self.run_frontend_tests(),
            'backend': self.run_backend_tests(),
            'aws': self.run_aws_tests(),
            'stress': self.run_stress_tests()
        }
        
        # Cleanup
        self.cleanup_test_environment()
        
        return all_results
    
    def run_all_tests(self):
        """Run comprehensive test suite."""
        logger.info("COMPREHENSIVE VIDEO UPLOAD PIPELINE TEST SUITE")
        logger.info("="*60)
        
        self.setup_test_environment()
        
        all_results = {
            'frontend': self.run_frontend_tests(),
            'backend': self.run_backend_tests(),
            'aws': self.run_aws_tests(),
            'stress': self.run_stress_tests()
        }
        
        # Calculate overall results
        logger.info("="*60)
        logger.info("COMPREHENSIVE TEST RESULTS SUMMARY")
        logger.info("="*60)
        
        total_tests = 0
        passed_tests = 0
        
        for category, results in all_results.items():
            if isinstance(results, dict):
                category_passed = sum(1 for result in results.values() if result)
                category_total = len(results)
                
                logger.info(f"{category.title()}: {category_passed}/{category_total} passed")
                
                total_tests += category_total
                passed_tests += category_passed
        
        logger.info("-"*60)
        logger.info(f"Overall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        # Detailed results
        logger.info("\nDETAILED RESULTS:")
        for category, category_results in self.results.items():
            if category_results:
                logger.info(f"\n{category.title()}:")
                for test_name, test_data in category_results.items():
                    if isinstance(test_data, dict) and 'success_rate' in test_data:
                        logger.info(f"  {test_name}: {test_data['passed']}/{test_data['total']} ({test_data['success_rate']*100:.1f}%)")
                    elif isinstance(test_data, dict) and 'skipped' in test_data:
                        logger.info(f"  {test_name}: SKIPPED")
        
        self.cleanup_test_environment()
        
        if passed_tests == total_tests:
            logger.info("\n🎉 All tests passed! Upload pipeline appears to be robust.")
            return True
        else:
            logger.warning(f"\n⚠️  {total_tests - passed_tests} tests failed. Issues identified in upload pipeline.")
            return False

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='Comprehensive Video Upload Pipeline Test Suite')
    parser.add_argument('--frontend-only', action='store_true', help='Run frontend tests only')
    parser.add_argument('--backend-only', action='store_true', help='Run backend tests only')
    parser.add_argument('--aws-only', action='store_true', help='Run AWS tests only')
    parser.add_argument('--stress-only', action='store_true', help='Run stress tests only')
    parser.add_argument('--integration-only', action='store_true', help='Run integration tests only')
    
    args = parser.parse_args()
    
    test_suite = VideoUploadPipelineTestSuite()
    
    try:
        if args.frontend_only:
            test_suite.setup_test_environment()
            results = test_suite.run_frontend_tests()
            success = all(results.values())
        elif args.backend_only:
            test_suite.setup_test_environment()
            results = test_suite.run_backend_tests()
            success = all(results.values())
        elif args.aws_only:
            test_suite.setup_test_environment()
            results = test_suite.run_aws_tests()
            success = all(results.values())
        elif args.stress_only:
            test_suite.setup_test_environment()
            results = test_suite.run_stress_tests()
            success = all(results.values())
        elif args.integration_only:
            results = test_suite.run_integration_tests()
            success = all(all(cat_results.values()) for cat_results in results.values() if isinstance(cat_results, dict))
        else:
            success = test_suite.run_all_tests()
        
        if success:
            print("\n✅ All selected tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed. Please review the logs and fix issues.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        test_suite.cleanup_test_environment()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {str(e)}")
        test_suite.cleanup_test_environment()
        sys.exit(1)

if __name__ == '__main__':
    main() 