#!/usr/bin/env python3
import os
import sys
import django
from django.db import connections
from django.db.utils import OperationalError

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

def test_database_connection():
    """Test the database connection and print the result."""
    try:
        # Set up Django environment for production
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_project.settings_production')
        django.setup()
        
        # Get the default database connection
        connection = connections['default']
        
        # Test the connection by creating a cursor
        cursor = connection.cursor()
        
        # If we get here, the connection is working
        print("Database connection successful!")
        print(f"Connected to: {connection.settings_dict['NAME']} on {connection.settings_dict['HOST']}:{connection.settings_dict['PORT']}")
        print(f"User: {connection.settings_dict['USER']}")
        
        # Test if we can execute a simple query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"PostgreSQL version: {version}")
        
        # Close the cursor
        cursor.close()
        
        return True
    except ImportError as e:
        print(f"Import error: {e}")
        print("This might be due to missing dependencies or incorrect settings path.")
        return False
    except OperationalError as e:
        print("Database connection failed!")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def test_database_tables():
    """Test if we can access the main database tables."""
    try:
        from django.db import connection
        
        # Test a simple query on a main table
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM videos_video;")
            video_count = cursor.fetchone()[0]
            print(f"Videos table accessible: {video_count} videos found")
            
            cursor.execute("SELECT COUNT(*) FROM libraries_library;")
            library_count = cursor.fetchone()[0]
            print(f"Libraries table accessible: {library_count} libraries found")
            
            cursor.execute("SELECT COUNT(*) FROM accounts_user;")
            user_count = cursor.fetchone()[0]
            print(f"Users table accessible: {user_count} users found")
            
        return True
    except Exception as e:
        print(f"Database tables test failed: {e}")
        return False

def check_environment():
    """Check if required environment variables are set."""
    print("Checking environment variables...")
    
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_REGION',
        'AWS_STORAGE_BUCKET_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("All required environment variables are set")
        return True

if __name__ == "__main__":
    print("Testing Database Connection for Paletta Production")
    print("=" * 50)
    
    # Check environment first
    env_ok = check_environment()
    
    if not env_ok:
        print("\nEnvironment check failed. Please set required environment variables.")
        sys.exit(1)
    
    # Test basic connection
    connection_ok = test_database_connection()
    
    if connection_ok:
        # Test table access
        tables_ok = test_database_tables()
        
        if tables_ok:
            print("\nAll database tests passed! Production database is working correctly.")
            sys.exit(0)
        else:
            print("\nDatabase connection works but table access failed.")
            sys.exit(1)
    else:
        print("\nDatabase connection failed. Check your production settings.")
        sys.exit(1) 