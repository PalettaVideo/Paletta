#!/usr/bin/env python3
import os
import sys
import django
from django.db import connections
from django.db.utils import OperationalError

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

def check_env_file():
    """Check if the .env file exists and is accessible."""
    env_path = '/home/ssm-user/Paletta/.env'
    if os.path.exists(env_path):
        print(f".env file found at: {env_path}")
        try:
            with open(env_path, 'r') as f:
                lines = f.readlines()
                print(f"   Contains {len(lines)} lines")
                # Show first few lines for debugging
                for i, line in enumerate(lines[:3]):
                    if line.strip() and not line.strip().startswith('#'):
                        key = line.split('=')[0] if '=' in line else 'unknown'
                        print(f"   Line {i+1}: {key}=...")
            return True
        except Exception as e:
            print(f"Error reading .env file: {e}")
            return False
    else:
        print(f".env file not found at: {env_path}")
        return False

# Load environment variables from .env file BEFORE Django setup
print("Loading environment variables...")
check_env_file()

try:
    from dotenv import load_dotenv
    env_path = '/home/ssm-user/Paletta/.env'
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded environment variables from: {env_path}")
except ImportError:
    print("python-dotenv not installed, trying to load .env manually")
    # Fallback: manually load .env file
    env_path = '/home/ssm-user/Paletta/.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print(f"Loaded environment variables from: {env_path}")
    else:
        print(f"Warning: .env file not found at {env_path}")

def test_database_connection():
    """Test the database connection and print the result."""
    try:
        # Set up Django environment for production
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_project.settings_production')
        print(f"Django settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
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
    found_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            found_vars.append(var)
            # Show first few characters of the value for debugging
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"  {var}: {display_value}")
        else:
            missing_vars.append(var)
            print(f" {var}: Not set")
    
    if missing_vars:
        print(f"\nMissing environment variables: {', '.join(missing_vars)}")
        print(f"Found {len(found_vars)}/{len(required_vars)} required variables")
        return False
    else:
        print(f"\n All {len(required_vars)} required environment variables are set")
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