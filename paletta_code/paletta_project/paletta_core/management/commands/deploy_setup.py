from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from videos.models import ContentType, PalettaCategory
from libraries.models import Library
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup initial data for Paletta deployment'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Paletta deployment setup...'))
        
        # Create content types
        content_types = [
            'campus_life', 'teaching_learning', 'research_innovation', 
            'city_environment', 'aerial_establishing', 'people_portraits', 
            'culture_events', 'workspaces_facilities', 'cutaways_abstracts', 
            'historical_archive'
        ]
        
        self.stdout.write('Creating content types...')
        for ct in content_types:
            obj, created = ContentType.objects.get_or_create(code=ct)
            if created:
                self.stdout.write(f'Created content type: {obj.display_name}')
            else:
                self.stdout.write(f'Content type already exists: {obj.display_name}')

        # Create Paletta categories  
        paletta_categories = [
            'people_community', 'buildings_architecture', 'classrooms_learning',
            'field_trips_outdoor', 'events_conferences', 'research_innovation_spaces',
            'technology_equipment', 'everyday_campus', 'urban_natural_environments',
            'backgrounds_abstracts'
        ]
        
        self.stdout.write('Creating Paletta categories...')
        for pc in paletta_categories:
            obj, created = PalettaCategory.objects.get_or_create(code=pc)
            if created:
                self.stdout.write(f'Created Paletta category: {obj.display_name}')
            else:
                self.stdout.write(f'Paletta category already exists: {obj.display_name}')

        # Create default Paletta library
        self.stdout.write('Creating default Paletta library...')
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
                self.stdout.write(self.style.SUCCESS('Created default Paletta library'))
            else:
                self.stdout.write('Default Paletta library already exists')
        else:
            self.stdout.write(self.style.ERROR('No superuser found, cannot create Paletta library'))
            self.stdout.write('Please create a superuser first: python manage.py createsuperuser')

        self.stdout.write(self.style.SUCCESS('Deployment setup complete!')) 