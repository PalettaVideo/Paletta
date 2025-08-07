from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
import os
from videos.models import ContentType
from libraries.models import Library


class Command(BaseCommand):
    help = 'Set up default images for content types based on their subject area'

    def add_arguments(self, parser):
        parser.add_argument(
            '--library',
            type=str,
            help='Specific library name to update (optional)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if image already exists',
        )

    def handle(self, *args, **options):
        # Mapping of content type subject areas to their default images
        content_type_image_mapping = {
            'campus_life': 'campus_life.png',
            'teaching_learning': 'Teaching&Learning.png',
            'research_innovation': 'Research&Innovation.png',
            'city_environment': 'City&Environment.jpg',
            'aerial_establishing': 'Aerial&Establishing_shots.png',
            'people_portraits': 'People&Portraits.png',
            'culture_events': 'Culture&Events.png',
            'workspaces_facilities': 'Workspaces&Facilities.jpg',
            'cutaways_abstracts': 'Cutaways&Abstracts.png',
            'historical_archive': 'Historical&Archive.jpg',
            'private': 'main_campus.png',  # Default for private content type
        }

        # Get libraries to process
        if options['library']:
            try:
                libraries = [Library.objects.get(name=options['library'])]
                self.stdout.write(f"Processing library: {options['library']}")
            except Library.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Library '{options['library']}' not found")
                )
                return
        else:
            libraries = Library.objects.filter(is_active=True)
            self.stdout.write(f"Processing {libraries.count()} libraries")

        # Static files directory path
        static_dir = os.path.join(settings.BASE_DIR, '..', 'static', 'picture')
        
        if not os.path.exists(static_dir):
            self.stdout.write(
                self.style.ERROR(f"Static directory not found: {static_dir}")
            )
            return

        total_updated = 0
        total_skipped = 0

        for library in libraries:
            self.stdout.write(f"\nProcessing library: {library.name}")
            
            # Get all content types for this library
            content_types = ContentType.objects.filter(library=library, is_active=True)
            
            for content_type in content_types:
                subject_area = content_type.subject_area
                
                # Skip if image already exists and not forcing update
                if content_type.image and not options['force']:
                    self.stdout.write(
                        f"  Skipping {content_type.display_name} (image already exists)"
                    )
                    total_skipped += 1
                    continue
                
                # Get the corresponding image file
                image_filename = content_type_image_mapping.get(subject_area)
                
                if not image_filename:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  No default image mapping for '{subject_area}' content type"
                        )
                    )
                    continue
                
                image_path = os.path.join(static_dir, image_filename)
                
                if not os.path.exists(image_path):
                    self.stdout.write(
                        self.style.ERROR(
                            f"  Image file not found: {image_path}"
                        )
                    )
                    continue
                
                try:
                    # Open and assign the image file
                    with open(image_path, 'rb') as image_file:
                        # Create a Django File object
                        django_file = File(image_file, name=image_filename)
                        
                        # Assign to content type
                        content_type.image.save(image_filename, django_file, save=True)
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  ✓ Updated {content_type.display_name} with {image_filename}"
                            )
                        )
                        total_updated += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  Error updating {content_type.display_name}: {str(e)}"
                        )
                    )

        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("SETUP SUMMARY")
        self.stdout.write("="*50)
        self.stdout.write(f"Total content types updated: {total_updated}")
        self.stdout.write(f"Total content types skipped: {total_skipped}")
        
        if total_updated > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ Successfully updated {total_updated} content types with default images!"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠ No content types were updated. Use --force to update existing images."
                )
            ) 