import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paletta_core.settings')

def run_django():
    """Run the Django development server."""
    try:
        # Initialize Django
        django.setup()
        
        # Import Django management commands after setup
        from django.core.management import call_command
        
        # Check if migrations are needed
        print("Checking for migrations...")
        call_command('makemigrations')
        
        # Apply migrations
        print("Applying migrations...")
        call_command('migrate')
        
        # Run the development server
        print("Starting development server...")
        call_command('runserver')
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_django() 