"""
Django management command to test email configuration
Usage: python manage.py test_email_config
"""

import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


class Command(BaseCommand):
    help = 'Test email configuration and diagnose issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--send-test',
            action='store_true',
            help='Send a test email to a specified address',
        )
        parser.add_argument(
            '--to',
            type=str,
            help='Email address to send test email to',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== EMAIL CONFIGURATION DIAGNOSIS ==='))
        
        # 1. Check current configuration
        self.stdout.write('\nCurrent Django Settings:')
        self.stdout.write(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'NOT SET')}")
        self.stdout.write(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'NOT SET')}")
        self.stdout.write(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'NOT SET')}")
        self.stdout.write(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'NOT SET')}")
        self.stdout.write(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'NOT SET')}")
        self.stdout.write(f"EMAIL_HOST_PASSWORD: {'SET' if getattr(settings, 'EMAIL_HOST_PASSWORD', '') else 'NOT SET'}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')}")
        self.stdout.write(f"AWS_SES_ENABLED: {getattr(settings, 'AWS_SES_ENABLED', 'NOT SET')}")
        self.stdout.write(f"AWS_SES_SENDER_EMAIL: {getattr(settings, 'AWS_SES_SENDER_EMAIL', 'NOT SET')}")
        
        # 2. Check environment variables
        self.stdout.write('\nEnvironment Variables:')
        env_vars = [
            'EMAIL_BACKEND',
            'EMAIL_HOST',
            'EMAIL_PORT',
            'EMAIL_USE_TLS',
            'EMAIL_HOST_USER',
            'EMAIL_HOST_PASSWORD',
            'DEFAULT_FROM_EMAIL',
            'AWS_SES_ENABLED',
            'AWS_SES_SENDER_EMAIL'
        ]
        
        for var in env_vars:
            value = os.environ.get(var)
            if var == 'EMAIL_HOST_PASSWORD' and value:
                self.stdout.write(f"{var}: SET")
            else:
                self.stdout.write(f"{var}: {value if value else 'NOT SET'}")
        
        # 3. Analyze configuration
        self.stdout.write('\nConfiguration Analysis:')
        
        current_backend = getattr(settings, 'EMAIL_BACKEND', '')
        
        if current_backend == 'django.core.mail.backends.console.EmailBackend':
            self.stdout.write(self.style.WARNING('WARNING: You are using the console email backend!'))
            self.stdout.write(self.style.WARNING('   This means emails are being printed to console, not actually sent.'))
            self.stdout.write(self.style.WARNING('   This is likely why you are not receiving emails.'))
            
        elif current_backend == 'django_ses.SESBackend':
            self.stdout.write(self.style.SUCCESS('Using AWS SES backend'))
            
            # Check AWS SES configuration
            if not getattr(settings, 'AWS_SES_ENABLED', False):
                self.stdout.write(self.style.WARNING('AWS_SES_ENABLED is False'))
                
            if not getattr(settings, 'AWS_ACCESS_KEY_ID', ''):
                self.stdout.write(self.style.WARNING('AWS_ACCESS_KEY_ID not set'))
                
            if not getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''):
                self.stdout.write(self.style.WARNING('AWS_SECRET_ACCESS_KEY not set'))
                
        elif current_backend == 'django.core.mail.backends.smtp.EmailBackend':
            self.stdout.write(self.style.SUCCESS('Using SMTP backend'))
            
            # Check SMTP configuration
            if not getattr(settings, 'EMAIL_HOST', ''):
                self.stdout.write(self.style.WARNING('EMAIL_HOST not set'))
                
            if not getattr(settings, 'EMAIL_HOST_USER', ''):
                self.stdout.write(self.style.WARNING('EMAIL_HOST_USER not set'))
                
            if not getattr(settings, 'EMAIL_HOST_PASSWORD', ''):
                self.stdout.write(self.style.WARNING('EMAIL_HOST_PASSWORD not set'))
                
        else:
            self.stdout.write(self.style.ERROR(f'Unknown email backend: {current_backend}'))
        
        # 4. Test sending email if requested
        if options['send_test']:
            if not options['to']:
                self.stdout.write(self.style.ERROR('Please specify --to email address for test email'))
                return
                
            self.stdout.write(f'\nSending test email to {options["to"]}...')
            
            try:
                send_mail(
                    subject='Test Email - Paletta Configuration',
                    message=f'This is a test email sent at {timezone.now()} to verify email configuration.',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'test@paletta.io'),
                    recipient_list=[options['to']],
                    fail_silently=False
                )
                
                if current_backend == 'django.core.mail.backends.console.EmailBackend':
                    self.stdout.write(self.style.SUCCESS('Email sent to console (check above output)'))
                else:
                    self.stdout.write(self.style.SUCCESS('Email sent successfully'))
                    self.stdout.write('   Check the recipient inbox and AWS SES console for delivery status')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Email sending failed: {str(e)}'))
        
        # 5. Provide recommendations
        self.stdout.write('\nRecommendations:')
        
        if current_backend == 'django.core.mail.backends.console.EmailBackend':
            self.stdout.write(self.style.WARNING('TO FIX: Set EMAIL_BACKEND environment variable to:'))
            self.stdout.write('   - django_ses.SESBackend (for AWS SES - recommended)')
            self.stdout.write('   - django.core.mail.backends.smtp.EmailBackend (for SMTP)')
            self.stdout.write('\nFor AWS SES:')
            self.stdout.write('   1. Set EMAIL_BACKEND=django_ses.SESBackend in .env')
            self.stdout.write('   2. Verify automatic-video-request@paletta.io in AWS SES Console')
            self.stdout.write('   3. Ensure AWS credentials have SES permissions')
            self.stdout.write('   4. Restart Django application')
            
        self.stdout.write('\nNext Steps:')
        self.stdout.write('1. Update configuration as needed')
        self.stdout.write('2. Run: python manage.py test_email_config --send-test --to your-email@example.com')
        self.stdout.write('3. Test the actual download request system')
        self.stdout.write('4. Check AWS SES sending statistics if using SES')
        
        self.stdout.write(self.style.SUCCESS('\n=== EMAIL DIAGNOSIS COMPLETE ===')) 