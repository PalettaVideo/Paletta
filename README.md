# Paletta - Platform Structure

## Owner – Full control over:

- Overall system rules & pricing structure
- High-level admin access
- Publish their libraries to potential buyers of their stock
- Set categories within their library

## Administrator - Assigned by Library Owners:

Create & manage a library (e.g., UCL Main Library, Faculty of Life Sciences Library, UCL East Campus library etc)

- Upload & store B-roll content for future productions
- Edit their uploads
- Customise aspects like logos and content type thumbnails

Library Owners maintain control over their own content, ensuring their IP is secure and categorised under their chosen branding.

## User:

- Only view and request downloads

---

# EC2 Instance Management & Deployment

## Connecting to EC2 Instance

### Via AWS Systems Manager (Recommended)

1. **Access AWS Console** → EC2 → Instances
2. **Select the `paletta-app` instance**
3. **Click "Connect"** → "Session Manager" tab
4. **Click "Connect"** to open a terminal session

### Via SSH (Alternative)

```bash
ssh -i your-key.pem ec2-user@your-instance-ip
```

## Initial Setup on EC2 Instance

### 1. Navigate to Project Directory

```bash
cd /home/ssm-user/Paletta
```

### to access the .env file containing secrets:

```bash
nano .env
```

### 2. Activate Virtual Environment

```bash
. ./.venv/bin/activate
(.venv) $
```

### 3. Navigate to Django Project

```bash
(.venv) $ cd paletta_code/paletta_project
```

## Deployment Procedures

### Fresh Deployment (New EC2 Instance)

For a completely new EC2 instance or when you need to reset everything:

```bash
# Navigate to project directory
cd /home/ssm-user/Paletta/paletta_code

# Run the complete deployment script
chmod +x first_deploy.sh
./first_deploy.sh
```

This script will:

- Set up the database connection
- Create and apply migrations
- Create superuser (niklaas@filmbright.com)
- Set up default content types and images
- Collect static files
- Restart services

### Incremental Updates

For regular updates after the initial deployment:

```bash
# Navigate to Django project
cd /home/ssm-user/Paletta/paletta_code/paletta_project

# Set Django settings
export DJANGO_SETTINGS_MODULE=paletta_project.settings_production

# Bump static version (for cache busting)
python manage.py bump_static_version

# Create new migrations (if model changes)
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart paletta nginx

# Check service status
sudo systemctl status paletta nginx
```

### Service Management

```bash
# Start services
sudo systemctl start paletta nginx

# Stop services
sudo systemctl stop paletta nginx

# Restart services
sudo systemctl restart paletta nginx

# Check service status
sudo systemctl status paletta nginx

# View service logs
sudo journalctl -u paletta -f
sudo journalctl -u nginx -f
```

## Database Management

### PostgreSQL RDS Connection

```bash
# Connect to the database
psql -h paletta-db.cx0siguuk92i.eu-west-2.rds.amazonaws.com -U palettaadmin -d postgres
```

**Database Password**: [Contact system administrator]

### Database Reset (Dangerous - Use with caution)

```sql
-- Terminate all connections to the database
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'paletta_db';

-- Drop and recreate the database
DROP DATABASE paletta_db;
CREATE DATABASE paletta_db;

-- Connect to the new database
\c paletta_db
```

### Database Backup

```bash
# Create a backup
pg_dump -h paletta-db.cx0siguuk92i.eu-west-2.rds.amazonaws.com -U palettaadmin -d paletta_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql -h paletta-db.cx0siguuk92i.eu-west-2.rds.amazonaws.com -U palettaadmin -d paletta_db < backup_file.sql
```

## Content Type Management

### Set Up Default Images for Content Types

```bash
# Navigate to Django project
cd /home/ssm-user/Paletta/paletta_code/paletta_project

# Set Django settings
export DJANGO_SETTINGS_MODULE=paletta_project.settings_production

# Assign default images to content types
python manage.py setup_content_type_images --force

# For specific library only
python manage.py setup_content_type_images --library "LibraryName" --force
```

### Create New Content Types

```bash
# Access Django shell
python manage.py shell

# In the shell:
from videos.models import ContentType
from libraries.models import Library

# Create new content type
library = Library.objects.get(name='YourLibraryName')
ContentType.objects.create(
    subject_area='your_new_content_type',
    library=library,
    is_active=True,
    description='Description of your new content type'
)
```

### Common Issues and Solutions

#### Service Won't Start

```bash
# Check service status
sudo systemctl status paletta

# Check for errors
sudo journalctl -u paletta --no-pager

# Restart services
sudo systemctl restart paletta nginx
```

#### Database Connection Issues

```bash
# Test database connection
python manage.py check --database default

# Check if database is accessible
psql -h paletta-db.cx0siguuk92i.eu-west-2.rds.amazonaws.com -U palettaadmin -d postgres -c "SELECT 1;"
```

#### Static Files Not Loading

```bash
# Recollect static files
python manage.py collectstatic --noinput

# Check static files directory
ls -la /home/ssm-user/Paletta/paletta_code/static/

# Bump static version
python manage.py bump_static_version
```

## File Structure

```
/home/ssm-user/Paletta/
├── .env
├── .venv/                          # Virtual environment
├── paletta_code/                   # Main project directory
│   ├── first_deploy.sh            # Fresh deployment script
│   ├── paletta_project/           # Django project
│   │   ├── manage.py
│   │   ├── videos/               # Videos app
│   │   ├── libraries/            # Libraries app
│   │   ├── accounts/             # Accounts app
│   │   ├── static/               # Static files
│   │   └── html_templates/       # HTML templates
│   └── static/                   # Collected static files
└── logs/                         # Application logs
```
