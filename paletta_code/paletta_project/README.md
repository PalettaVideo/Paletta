## Setup Instructions

To run the Django application, follow these steps:

1. Set up a new virtual environment:

   > python -m venv .venv

2. Activate the virtual environment:

   - Windows:

     > .\.venv\Scripts\activate

   - macOS/Linux:

     > source .venv/bin/activate

3. Install all dependencies required by the application:

   > pip install -r requirements.txt

4. Navigate to the project directory:

   > cd paletta_project

5. Run database migrations:

   > python manage.py migrate

6. Create a superuser to access the admin interface:

   > python manage.py createsuperuser

7. Start the development server:

   > python manage.py runserver

8. Access the application:
   - Main site: http://127.0.0.1:8000/
   - Admin interface: http://127.0.0.1:8000/admin/

## Project Structure

- `paletta_project/` - Main Django project directory
  - `accounts/` - User authentication and management app
  - `videos/` - Video management app
  - `templates/` - HTML templates
  - `paletta_core/` - Core settings and configuration
  - `libraries/` - Additional libraries and utilities

## API Endpoints

### Authentication and User Management

- **Login**: `/api/accounts/token/` (POST)
- **Register**: `/api/accounts/register/` (POST)
- **User Profile**: `/api/accounts/users/me/` (GET)
- **Update Profile**: `/api/accounts/users/me/update/` (PUT)
- **Change Password**: `/api/accounts/users/me/change-password/` (POST)

### Videos

- **List/Create Videos**: `/api/videos/videos/` (GET, POST)
- **Retrieve/Update/Delete Video**: `/api/videos/videos/{id}/` (GET, PUT, DELETE)
- **List/Create Categories**: `/api/videos/categories/` (GET, POST)
- **Retrieve/Update/Delete Category**: `/api/videos/categories/{id}/` (GET, PUT, DELETE)
- **Filter Videos by Category**: `/api/videos/videos/?category={id}` (GET)
- **Search Videos**: `/api/videos/videos/?search={query}` (GET)

### Libraries

- **List/Create Libraries**: `/api/libraries/libraries/` (GET, POST)
- **Retrieve/Update/Delete Library**: `/api/libraries/libraries/{id}/` (GET, PUT, DELETE)
- **List/Create Library Members**: `/api/libraries/members/` (GET, POST)
- **Retrieve/Update/Delete Library Member**: `/api/libraries/members/{id}/` (GET, PUT, DELETE)

## User Roles

The application supports the following user roles:

- Owner
- Administrator
- User

## Django Admin Interface

The Django admin interface allows superusers/staff to:

- Manage users and their roles
- Control video uploads and content type
- Monitor system activity
- Manage libraries and their members
- Track orders and downloads