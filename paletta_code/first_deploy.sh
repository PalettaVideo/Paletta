#!/bin/bash

# Paletta FRESH Deployment Script
# Use this when you've dropped the database completely

set -e  # Exit on any error

echo "Starting Paletta FRESH deployment..."

# Navigate to project directory
cd /home/ssm-user/Paletta/paletta_code/paletta_project

# Set Django settings
export DJANGO_SETTINGS_MODULE=paletta_project.settings_production

echo "Testing database connection..."
if python manage.py check --database default; then
    echo "Database connection successful!"
else
    echo "ERROR: Cannot connect to database!"
    exit 1
fi

echo "Removing old migration files..."
# Remove old migration files but keep __init__.py
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

echo "Bumping static version..."
python manage.py bump_static_version

echo "Creating migrations..."
python manage.py makemigrations

echo "Applying migrations..."
if python manage.py migrate; then
    echo "Migrations applied successfully!"
else
    echo "ERROR: Migration failed!"
    exit 1
fi

echo "Creating superuser..."
if ! python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); exit(0 if User.objects.filter(is_superuser=True).exists() else 1)"; then
    echo "Creating superuser (you'll be prompted for credentials)..."
    python manage.py createsuperuser
else
    echo "Superuser already exists, skipping..."
fi

echo "Loading initial data..."
python manage.py shell << 'EOF'
from videos.models import ContentType, PalettaCategory
from libraries.models import Library
from django.contrib.auth import get_user_model

User = get_user_model()

# Create content types
content_types = ['campus_life', 'teaching_learning', 'research_innovation', 'city_environment', 'aerial_establishing', 'people_portraits', 'culture_events', 'workspaces_facilities', 'cutaways_abstracts', 'historical_archive']

print("Creating content types...")
for ct in content_types:
    obj, created = ContentType.objects.get_or_create(code=ct)
    if created:
        print(f"Created ContentType: {ct}")
    else:
        print(f"ContentType already exists: {ct}")

# Create Paletta categories  
paletta_categories = ['people_community', 'buildings_architecture', 'classrooms_learning', 'field_trips_outdoor', 'events_conferences', 'research_innovation_spaces', 'technology_equipment', 'everyday_campus', 'urban_natural_environments', 'backgrounds_abstracts', 'private']

print("Creating Paletta categories...")
for pc in paletta_categories:
    obj, created = PalettaCategory.objects.get_or_create(code=pc)
    if created:
        print(f"Created PalettaCategory: {pc}")
    else:
        print(f"PalettaCategory already exists: {pc}")

# Create default Paletta library
admin_user = User.objects.filter(is_superuser=True).first()
if admin_user:
    print("Creating default Paletta library...")
    paletta_lib, created = Library.objects.get_or_create(
        name='Paletta',
        defaults={
            'description': 'Default Paletta video library for educational content',
            'owner': admin_user,
            'category_source': 'paletta_style',
            'storage_tier': 'enterprise',
            'is_active': True
        }
    )
    # Always ensure the Paletta library owner is the superuser
    if not created and paletta_lib.owner != admin_user:
        paletta_lib.owner = admin_user
        paletta_lib.save()
        print("Updated Paletta library owner to superuser")
    
    # ALWAYS ensure categories are set up for the Paletta library
    paletta_lib.setup_default_categories()
    print("Set up default categories for Paletta library")
    
    if created:
        print("Created default Paletta library")
    else:
        print("Default Paletta library already exists")
else:
    print("No superuser found, cannot create Paletta library")

print("Initial data loaded successfully")
EOF

echo "Setting up categories for Paletta library..."
python manage.py shell << 'EOF'
from videos.models import Category
from libraries.models import Library

try:
    paletta_lib = Library.objects.get(name='Paletta')
    print("Setting up default categories...")
    paletta_lib.setup_default_categories()
    
    category_count = Category.objects.filter(library=paletta_lib).count()
    print(f"Paletta library now has {category_count} categories")
    
    if category_count >= 11:
        print("✓ All categories created successfully!")
    else:
        print(f"⚠ Warning: Expected 11 categories, found {category_count}")
        
except Library.DoesNotExist:
    print("✗ Error: Paletta library not found")
EOF

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Restarting services..."
if sudo systemctl restart paletta nginx; then
    echo "Services restarted successfully!"
else
    echo "WARNING: Service restart failed. Check logs with 'sudo journalctl -u paletta -f'"
    exit 1
fi

echo "Deployment complete!"
echo "Checking service status..."
sudo systemctl status paletta nginx --no-pager

echo ""
echo "Performing final health check..."
sleep 3  # Give services time to fully start

if curl -f -s http://localhost/healthcheck/ > /dev/null; then
    echo "Health check passed!"
    echo ""
    echo "Paletta is ready!"
    echo "Access the application at paletta.io"
    echo "Admin panel: /admin/"
    echo ""
else
    echo "WARNING: Health check failed. Application may not be responding correctly."
    echo "   Check logs with: sudo journalctl -u paletta -f"
    echo ""
fi 