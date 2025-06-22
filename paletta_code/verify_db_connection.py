#!/usr/bin/env python3
"""
Database Connection Verification Script
Run this script to verify your database settings are loading correctly.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

def main():
    print("=== Database Connection Verification ===\n")
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    # Load environment variables
    env_files = [
        '.env',
        '/home/ssm-user/Paletta/.env',
        Path.home() / 'Paletta' / '.env'
    ]
    
    env_loaded = False
    for env_file in env_files:
        if Path(env_file).exists():
            print(f"Loading .env from: {env_file}")
            load_dotenv(dotenv_path=env_file)
            env_loaded = True
            break
    
    if not env_loaded:
        print("No .env file found in expected locations")
        print("Expected locations:")
        for env_file in env_files:
            print(f"  - {env_file}")
    
    # Check DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    print(f"\nDATABASE_URL: {database_url}")
    
    if database_url:
        print("DATABASE_URL is set")
        
        # Parse the database URL
        try:
            db_config = dj_database_url.parse(database_url)
            print(f"Database configuration parsed successfully:")
            print(f"   Engine: {db_config.get('ENGINE')}")
            print(f"   Host: {db_config.get('HOST')}")
            print(f"   Port: {db_config.get('PORT')}")
            print(f"   Name: {db_config.get('NAME')}")
            print(f"   User: {db_config.get('USER')}")
            
            # Check if it's the expected RDS host
            expected_host = 'paletta-db.cx0siguuk92i.eu-west-2.rds.amazonaws.com'
            if db_config.get('HOST') == expected_host:
                print("Using correct RDS host")
            else:
                print(f"Expected host: {expected_host}")
                print(f"Actual host: {db_config.get('HOST')}")
                
        except Exception as e:
            print(f"Error parsing DATABASE_URL: {e}")
    else:
        print("DATABASE_URL is not set")
    
    print("\n=== Django Settings Test ===")
    
    # Test Django settings loading
    try:
        # Add the project path to Python path
        project_path = Path(__file__).parent / 'paletta_project'
        sys.path.insert(0, str(project_path))
        
        # Set Django settings module
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_core.settings_development')
        
        import django
        django.setup()
        
        from django.conf import settings
        
        print("Django settings loaded successfully")
        print(f"Database configuration:")
        db_settings = settings.DATABASES['default']
        for key, value in db_settings.items():
            if key == 'PASSWORD':
                print(f"{key}: {'*' * len(str(value)) if value else 'Not set'}")
            else:
                print(f"{key}: {value}")
                
        # Test database connection
        print("\n=== Database Connection Test ===")
        from django.db import connection
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                print("Database connection successful!")
                print(f"   Test query result: {result}")
        except Exception as e:
            print(f"Database connection failed: {e}")
            
    except Exception as e:
        print(f"Error loading Django settings: {e}")
    
    print("\n=== Environment Variables Check ===")
    important_vars = [
        'DJANGO_SETTINGS_MODULE',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'SECRET_KEY',
    ]
    
    for var in important_vars:
        value = os.environ.get(var)
        if value:
            if 'SECRET' in var or 'PASSWORD' in var:
                print(f"{var}: {'*' * min(len(value), 20)}")
            else:
                print(f"{var}: {value}")
        else:
            print(f"{var}: Not set")

if __name__ == '__main__':
    main() 