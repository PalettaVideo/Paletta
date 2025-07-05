# Paletta Clean Deployment Guide

This guide provides step-by-step instructions for deploying the Paletta video library system after database changes or clean installations.

## Prerequisites

- Django environment properly configured
- Database connection established
- Virtual environment activated
- Proper permissions on the server

## Quick Deployment (Recommended)

### Option 1: Using the Deployment Script

1. **Make the script executable** (if not already):

   ```bash
   chmod +x /home/ssm-user/Paletta/paletta_code/deploy.sh
   ```

2. **Run the deployment**:
   ```bash
   cd /home/ssm-user/Paletta/paletta_code
   ./deploy.sh
   ```

### Option 2: Using Django Management Commands

1. **Navigate to project directory**:

   ```bash
   cd /home/ssm-user/Paletta/paletta_code/paletta_project
   ```

2. **Run the deployment setup**:
   ```bash
   python manage.py deploy_setup
   ```

## Manual Deployment (Step by Step)

If you prefer to run commands manually or if the script fails:

### Step 1: Database Setup

```bash
cd /home/ssm-user/Paletta/paletta_code/paletta_project
export DJANGO_SETTINGS_MODULE=paletta_project.settings_production

# Generate and apply migrations
python manage.py makemigrations
python manage.py migrate
```

### Step 2: Create Superuser

```bash
python manage.py createsuperuser
```

### Step 3: Load Initial Data

```bash
python manage.py deploy_setup
```

### Step 4: Static Files & Services

```bash
# Bump static version
python manage.py bump_static_version

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart paletta nginx
```

## What Gets Created

The deployment process creates:

### Content Types (10 items)

- Campus Life
- Teaching & Learning
- Research & Innovation
- City & Environment
- Aerial & Establishing Shots
- People & Portraits
- Culture & Events
- Workspaces & Facilities
- Cutaways & Abstracts
- Historical & Archive

### Paletta Categories (10 items)

- People and Community
- Buildings & Architecture
- Classrooms & Learning Spaces
- Field Trips & Outdoor Learning
- Events & Conferences
- Research & Innovation Spaces
- Technology & Equipment
- Everyday Campus Life
- Urban & Natural Environments
- Backgrounds & Abstracts

### Default Paletta Library

- Name: "Paletta"
- Type: Paletta Style Categories
- Owner: First superuser
- Status: Active

### Verification Steps

After deployment, verify everything works:

1. **Check services**:

   ```bash
   sudo systemctl status paletta nginx
   ```

2. **Access the application**:

   - Main site: `https://paletta.io`
   - Admin panel: `https://paletta.io/admin/`