#!/usr/bin/env python
"""
Quick Upload Pipeline Diagnostic Tool
Identifies immediate issues that could cause upload failures.

Usage:
    python test_upload_quick_check.py
"""

import os
import sys
import django
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_project.settings_production')
django.setup()

from django.test.client import Client
from django.conf import settings
from accounts.models import User
from libraries.models import Library
from videos.models import ContentType
import boto3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuickUploadDiagnostic:
    """Quick diagnostic tool for upload pipeline issues."""
    
    def __init__(self):
        self.client = Client()
        self.issues_found = []
        
    def log_issue(self, category, issue, severity='ERROR'):
        """Log an issue found during diagnostics."""
        self.issues_found.append({
            'category': category,
            'issue': issue,
            'severity': severity
        })
        logger.error(f"[{severity}] {category}: {issue}")
    
    def check_url_routing(self):
        """Check for URL routing issues."""
        logger.info("🔍 Checking URL routing...")
        
        try:
            # Test the upload API endpoint
            response = self.client.get('/api/api/upload/')
            if response.status_code == 405:  # Method not allowed (expected for GET)
                logger.info("✅ Upload API endpoint accessible")
            elif response.status_code == 404:
                self.log_issue("URL_ROUTING", "Upload API endpoint not found - URL routing issue")
            else:
                logger.warning(f"⚠️ Upload API returned unexpected status: {response.status_code}")
                
            # Test content types API
            response = self.client.get('/api/api/content-types/')
            if response.status_code in [200, 401, 403]:  # Success or auth required
                logger.info("✅ Content types API endpoint accessible")
            elif response.status_code == 404:
                self.log_issue("URL_ROUTING", "Content types API endpoint not found")
                
        except Exception as e:
            self.log_issue("URL_ROUTING", f"Exception testing URLs: {str(e)}")
    
    def check_database_setup(self):
        """Check database setup and required data."""
        logger.info("🔍 Checking database setup...")
        
        try:
            # Check if we have any libraries
            library_count = Library.objects.count()
            if library_count == 0:
                self.log_issue("DATABASE", "No libraries found - users cannot upload without libraries")
            else:
                logger.info(f"✅ Found {library_count} libraries")
                
            # Check if we have content types
            content_type_count = ContentType.objects.count()
            if content_type_count == 0:
                self.log_issue("DATABASE", "No content types found - uploads will fail validation")
            else:
                logger.info(f"✅ Found {content_type_count} content types")
                
            # Check if we have any users
            user_count = User.objects.count()
            if user_count == 0:
                self.log_issue("DATABASE", "No users found - cannot test authenticated uploads")
            else:
                logger.info(f"✅ Found {user_count} users")
                
        except Exception as e:
            self.log_issue("DATABASE", f"Exception checking database: {str(e)}")
    
    def check_aws_configuration(self):
        """Check AWS configuration."""
        logger.info("🔍 Checking AWS configuration...")
        
        # Check settings
        aws_enabled = getattr(settings, 'AWS_STORAGE_ENABLED', False)
        if not aws_enabled:
            self.log_issue("AWS_CONFIG", "AWS_STORAGE_ENABLED is False - uploads will fail", "WARNING")
            return
            
        required_settings = [
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
            self.log_issue("AWS_CONFIG", f"Missing AWS settings: {', '.join(missing_settings)}")
        else:
            logger.info("✅ AWS settings present")
            
            # Test S3 connection
            try:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
                s3_client.list_buckets()
                logger.info("✅ S3 connection successful")
                
                # Test bucket access
                bucket_name = settings.AWS_STORAGE_BUCKET_NAME
                try:
                    s3_client.head_bucket(Bucket=bucket_name)
                    logger.info(f"✅ S3 bucket '{bucket_name}' accessible")
                except Exception as e:
                    self.log_issue("AWS_CONFIG", f"Cannot access S3 bucket '{bucket_name}': {str(e)}")
                    
            except Exception as e:
                self.log_issue("AWS_CONFIG", f"S3 connection failed: {str(e)}")
    
    def check_upload_endpoint_basic(self):
        """Test basic upload endpoint functionality."""
        logger.info("🔍 Testing upload endpoint...")
        
        try:
            # Create a test user if none exists
            test_user = None
            try:
                test_user = User.objects.get(email='diagnostic@test.com')
            except User.DoesNotExist:
                if User.objects.filter(is_superuser=True).exists():
                    admin_user = User.objects.filter(is_superuser=True).first()
                    test_user = User.objects.create_user(
                        email='diagnostic@test.com',
                        password='testpass123',
                        first_name='Test',
                        last_name='User'
                    )
                else:
                    self.log_issue("UPLOAD_TEST", "No users available for testing upload endpoint")
                    return
            
            # Login the test user
            self.client.force_login(test_user)
            
            # Test with missing data
            response = self.client.post('/api/api/upload/', data={})
            if response.status_code == 400:
                logger.info("✅ Upload endpoint correctly rejects empty requests")
            else:
                self.log_issue("UPLOAD_TEST", f"Upload endpoint should return 400 for empty request, got {response.status_code}")
                
            # Test with minimal valid data (if we have library and content type)
            library = Library.objects.first()
            content_type = ContentType.objects.first()
            
            if library and content_type:
                data = {
                    's3_key': 'test/diagnostic.mp4',
                    'title': 'Diagnostic Test',
                    'content_type': content_type.id,
                    'library_id': library.id,
                }
                
                response = self.client.post('/api/api/upload/', data=data)
                if response.status_code == 201:
                    logger.info("✅ Upload endpoint accepts valid requests")
                    # Clean up test video
                    try:
                        from videos.models import Video
                        Video.objects.filter(title='Diagnostic Test').delete()
                    except:
                        pass
                elif response.status_code == 400:
                    logger.info("⚠️ Upload endpoint rejected valid request - check validation logic")
                    try:
                        error_data = response.json()
                        logger.info(f"   Error response: {error_data}")
                    except:
                        logger.info(f"   Response content: {response.content}")
                else:
                    self.log_issue("UPLOAD_TEST", f"Unexpected response from upload endpoint: {response.status_code}")
            else:
                self.log_issue("UPLOAD_TEST", "Cannot test upload endpoint - no library or content type available")
                
        except Exception as e:
            self.log_issue("UPLOAD_TEST", f"Exception testing upload endpoint: {str(e)}")
    
    def check_frontend_upload_page(self):
        """Check if upload page loads correctly."""
        logger.info("🔍 Checking upload page...")
        
        try:
            # Create a test user if none exists
            test_user = None
            try:
                test_user = User.objects.get(email='diagnostic@test.com')
            except User.DoesNotExist:
                if User.objects.filter(is_superuser=True).exists():
                    admin_user = User.objects.filter(is_superuser=True).first()
                    test_user = User.objects.create_user(
                        email='diagnostic@test.com',
                        password='testpass123',
                        first_name='Test',
                        last_name='User'
                    )
                else:
                    self.log_issue("FRONTEND", "No users available for testing upload page")
                    return
            
            # Login the test user
            self.client.force_login(test_user)
            
            # Test upload page
            response = self.client.get('/videos/upload/')
            if response.status_code == 200:
                logger.info("✅ Upload page loads successfully")
                
                # Check if page contains expected elements
                content = response.content.decode('utf-8')
                if 'upload-form' in content:
                    logger.info("✅ Upload form found on page")
                else:
                    self.log_issue("FRONTEND", "Upload form not found on upload page")
                    
                if 'content-types-grid' in content:
                    logger.info("✅ Content types grid found on page")
                else:
                    self.log_issue("FRONTEND", "Content types grid not found on upload page")
                    
            else:
                self.log_issue("FRONTEND", f"Upload page failed to load: {response.status_code}")
                
        except Exception as e:
            self.log_issue("FRONTEND", f"Exception checking upload page: {str(e)}")
    
    def check_critical_file_paths(self):
        """Check if critical files exist."""
        logger.info("🔍 Checking critical file paths...")
        
        critical_files = [
            ('static/js/upload.js', 'Frontend upload JavaScript'),
            ('videos/views/api_views.py', 'Backend upload API'),
            ('videos/models.py', 'Video models'),
            ('videos/urls.py', 'Video URL configuration'),
        ]
        
        project_root = os.path.dirname(os.path.abspath(__file__))
        
        for file_path, description in critical_files:
            full_path = os.path.join(project_root, file_path)
            if os.path.exists(full_path):
                logger.info(f"✅ {description} found")
            else:
                # Try alternative paths
                alt_path = os.path.join(project_root, '..', file_path)
                if os.path.exists(alt_path):
                    logger.info(f"✅ {description} found (alternative path)")
                else:
                    self.log_issue("FILE_PATHS", f"Missing critical file: {file_path} ({description})")
    
    def check_javascript_errors(self):
        """Check for potential JavaScript errors in upload.js."""
        logger.info("🔍 Checking for JavaScript issues...")
        
        try:
            # Find upload.js file
            project_root = os.path.dirname(os.path.abspath(__file__))
            js_paths = [
                os.path.join(project_root, 'static/js/upload.js'),
                os.path.join(project_root, '..', 'static', 'js', 'upload.js'),
            ]
            
            js_file = None
            for path in js_paths:
                if os.path.exists(path):
                    js_file = path
                    break
                    
            if not js_file:
                self.log_issue("JAVASCRIPT", "upload.js file not found")
                return
                
            with open(js_file, 'r', encoding='utf-8') as f:
                js_content = f.read()
                
            # Check for common issues
            issues = []
            
            # Check for correct API endpoint
            if '/api/api/upload/' not in js_content:
                issues.append("API endpoint path may be incorrect")
                
            # Check for proper error handling
            if 'catch' not in js_content:
                issues.append("No error handling found in JavaScript")
                
            # Check for timeout configuration
            if 'timeout' not in js_content.lower():
                issues.append("No timeout configuration found")
                
            # Check for CSRF token handling
            if 'csrftoken' not in js_content.lower():
                issues.append("CSRF token handling may be missing")
                
            if issues:
                for issue in issues:
                    self.log_issue("JAVASCRIPT", issue, "WARNING")
            else:
                logger.info("✅ No obvious JavaScript issues found")
                
        except Exception as e:
            self.log_issue("JAVASCRIPT", f"Exception checking JavaScript: {str(e)}")
    
    def run_diagnostics(self):
        """Run all diagnostic checks."""
        logger.info("🚀 Running quick upload pipeline diagnostics...")
        logger.info("="*60)
        
        # Run all checks
        self.check_critical_file_paths()
        self.check_url_routing()
        self.check_database_setup() 
        self.check_aws_configuration()
        self.check_frontend_upload_page()
        self.check_upload_endpoint_basic()
        self.check_javascript_errors()
        
        # Summary
        logger.info("="*60)
        logger.info("🏁 DIAGNOSTIC SUMMARY")
        logger.info("="*60)
        
        if not self.issues_found:
            logger.info("🎉 No issues found! Upload pipeline appears to be configured correctly.")
            return True
        else:
            logger.error(f"❌ Found {len(self.issues_found)} issues:")
            
            categories = {}
            for issue in self.issues_found:
                category = issue['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(issue)
                
            for category, category_issues in categories.items():
                logger.error(f"\n{category}:")
                for issue in category_issues:
                    logger.error(f"  [{issue['severity']}] {issue['issue']}")
                    
            logger.error(f"\n⚠️ Please fix these issues before testing uploads with users.")
            return False

def main():
    """Run quick diagnostics."""
    diagnostic = QuickUploadDiagnostic()
    success = diagnostic.run_diagnostics()
    
    if success:
        print("\n✅ Quick diagnostics passed! Consider running the full test suite for comprehensive testing.")
        sys.exit(0)
    else:
        print("\n❌ Issues found. Fix them before running the full test suite.")
        sys.exit(1)

if __name__ == '__main__':
    main() 