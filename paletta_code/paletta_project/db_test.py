#!/usr/bin/env python3
import os
import sys
import django
from django.db import connections
from django.db.utils import OperationalError

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_core.settings')
django.setup()

def test_database_connection():
    """Test the database connection and print the result."""
    try:
        # Try to get a cursor from the default database connection
        connection = connections['default']
        connection.cursor()
        
        # If we get here, the connection is working
        print("Database connection successful!")
        print(f"Connected to: {connection.settings_dict['NAME']} on {connection.settings_dict['HOST']}:{connection.settings_dict['PORT']}")
        print(f"User: {connection.settings_dict['USER']}")
        
        # Test if we can execute a simple query
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"PostgreSQL version: {version}")
            
        return True
    except OperationalError as e:
        print("Database connection failed!")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_database_connection() 