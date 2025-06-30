import os
import re
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    """
    BACKEND-READY: Django management command for static file cache invalidation.
    MAPPED TO: python manage.py bump_static_version
    USED BY: Deployment scripts and version management
    
    Updates STATIC_VERSION in settings files to force browser cache refresh.
    """
    help = 'Bump the static version to force cache invalidation'

    def add_arguments(self, parser):
        """
        BACKEND-READY: Command argument configuration.
        MAPPED TO: Django management command system
        USED BY: Command line interface
        
        Adds optional --set-version argument for manual version specification.
        """
        parser.add_argument(
            '--set-version',
            type=str,
            help='Specific version to set (e.g., 2.1.0)',
        )

    def handle(self, *args, **options):
        """
        BACKEND-READY: Main command execution logic.
        MAPPED TO: Django management command system
        USED BY: python manage.py bump_static_version
        
        Increments or sets static version across all settings files.
        """
        # Find the settings files relative to the Django project directory
        settings_files = [
            'paletta_core/settings_development.py',
            'paletta_project/settings_production.py'
        ]
        
        if options['set_version']:
            new_version = options['set_version']
        else:
            # Auto-increment version
            current_version = getattr(settings, 'STATIC_VERSION', '1.0.0')
            version_parts = current_version.split('.')
            if len(version_parts) >= 3:
                # Increment patch version
                version_parts[2] = str(int(version_parts[2]) + 1)
            else:
                version_parts = ['1', '0', '1']
            new_version = '.'.join(version_parts)

        self.stdout.write(f'Current version: {getattr(settings, "STATIC_VERSION", "Not set")}')
        self.stdout.write(f'New version: {new_version}')

        # Update version in settings files
        updated_files = []
        for settings_file in settings_files:
            self.stdout.write(f'Checking file: {settings_file}')
            if os.path.exists(settings_file):
                self.stdout.write(f'File exists: {settings_file}')
                try:
                    with open(settings_file, 'r') as f:
                        content = f.read()
                    
                    # Replace the STATIC_VERSION line
                    pattern = r"STATIC_VERSION = '[^']*'"
                    replacement = f"STATIC_VERSION = '{new_version}'"
                    
                    if re.search(pattern, content):
                        new_content = re.sub(pattern, replacement, content)
                        
                        with open(settings_file, 'w') as f:
                            f.write(new_content)
                        
                        updated_files.append(settings_file)
                        self.stdout.write(
                            self.style.SUCCESS(f'Updated {settings_file}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'STATIC_VERSION not found in {settings_file}')
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error updating {settings_file}: {e}')
                    )
            else:
                self.stdout.write(f'File does not exist: {os.path.abspath(settings_file)}')

        if updated_files:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nStatic version bumped to {new_version}'
                )
            )
            self.stdout.write(
                'All browsers will now download fresh static files on next visit.'
            )
        else:
            self.stdout.write(
                self.style.ERROR('No settings files were updated.')
            ) 