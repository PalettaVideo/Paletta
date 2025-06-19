#!/bin/bash

# Paletta Clean Deployment Script
# Run this after dropping the database to set everything up correctly

set -e  # Exit on any error

echo "Starting Paletta clean deployment..."

# Navigate to project directory
cd /home/ssm-user/Paletta/paletta_code/paletta_project

# Set Django settings
export DJANGO_SETTINGS_MODULE=paletta_project.settings_production

echo "Bumping static version..."
python manage.py bump_static_version

echo "Creating migrations..."
python manage.py makemigrations

echo "Applying migrations..."
python manage.py migrate

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

for ct in content_types:
    ContentType.objects.get_or_create(code=ct)

# Create Paletta categories  
paletta_categories = ['people_community', 'buildings_architecture', 'classrooms_learning', 'field_trips_outdoor', 'events_conferences', 'research_innovation_spaces', 'technology_equipment', 'everyday_campus', 'urban_natural_environments', 'backgrounds_abstracts']

for pc in paletta_categories:
    PalettaCategory.objects.get_or_create(code=pc)

# Create default Paletta library
admin_user = User.objects.filter(is_superuser=True).first()
if admin_user:
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
    if created:
        print("Created default Paletta library")
    else:
        print("Default Paletta library already exists")
else:
    print("No superuser found, cannot create Paletta library")

print("Initial data loaded successfully")
EOF

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Restarting services..."
sudo systemctl restart paletta nginx

echo "Deployment complete!"
echo "Checking service status..."
sudo systemctl status paletta nginx --no-pager

echo ""
echo "Paletta is ready!"
echo "Access the application at paletta.io"
echo "Admin panel: /admin/"
echo ""
EOF 