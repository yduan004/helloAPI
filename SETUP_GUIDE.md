# Setup Guide

This guide will help you set up and run the Django User Management API.

## 📋 Prerequisites Checklist

Before you begin, make sure you have:

- [ ] Python 3.8 or higher installed
  ```bash
  python --version
  # or
  python3 --version
  ```

- [ ] PostgreSQL installed and running
  ```bash
  # Check if PostgreSQL is running
  psql --version
  ```

- [ ] Database `my_database` created with `users` table
  ```bash
  # Connect to PostgreSQL
  psql -U postgres
  
  # Check if database exists
  \l
  
  # Connect to your database
  \c my_database
  
  # Check if users table exists
  \dt
  ```

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
# Navigate to project directory
cd /Users/yduan/git/helloApi

# Install all required packages
pip install -r requirements.txt
```

Expected output:
```
Successfully installed Django-4.2.7 djangorestframework-3.14.0 ...
```

### Step 2: Configure Database

Open `backend/settings.py` and verify the database settings:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'my_database',      # ← Your database name
        'USER': 'postgres',          # ← Your PostgreSQL username
        'PASSWORD': 'postgres',      # ← Your PostgreSQL password
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

**If your credentials are different, update them accordingly.**

### Step 3: Test Database Connection

```bash
# This command will try to connect to the database
python manage.py dbshell
```

If successful, you'll see the PostgreSQL prompt:
```
psql (14.x)
Type "help" for help.

my_database=#
```

Type `\q` to exit.

**If you get an error:**
- Check that PostgreSQL is running
- Verify your database credentials
- Make sure the database `my_database` exists

### Step 4: Verify Users Table

Since you already have a `users` table, let's verify Django can see it:

```bash
# This will show you the SQL Django would use (but won't execute it)
python manage.py sqlmigrate users 0001_initial 2>/dev/null || echo "No migrations needed - using existing table"
```

**Note:** The model is set to `managed = False`, so Django won't try to create or modify your existing table.

### Step 5: Create Admin User (Optional)

If you want to use the Django admin interface:

```bash
python manage.py createsuperuser
```

Follow the prompts:
```
Username: admin
Email address: admin@example.com
Password: ********
Password (again): ********
```

### Step 6: Run the Server

```bash
python manage.py runserver
```

You should see:
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
December 30, 2025 - 12:00:00
Django version 4.2.7, using settings 'backend.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

### Step 7: Test the API

Open a new terminal and test the API:

```bash
# Test 1: List all users
curl http://localhost:8000/api/users/

# Test 2: Create a new user
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
  }'

# Test 3: Get the user you just created (replace 1 with the actual ID)
curl http://localhost:8000/api/users/1/
```

### Step 8: Explore the Browsable API

Open your browser and go to:
- **API Root**: http://localhost:8000/api/users/
- **Django Admin**: http://localhost:8000/admin/ (if you created a superuser)

The browsable API provides a web interface where you can:
- View all endpoints
- Test API calls directly in the browser
- See request/response details

## 🔧 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'rest_framework'"

**Solution:**
```bash
pip install -r requirements.txt
```

### Problem: "django.db.utils.OperationalError: could not connect to server"

**Possible causes:**
1. PostgreSQL is not running
2. Wrong host/port in settings

**Solution:**
```bash
# Check if PostgreSQL is running
# On macOS:
brew services list | grep postgresql

# On Linux:
sudo systemctl status postgresql

# Start PostgreSQL if needed:
# On macOS:
brew services start postgresql

# On Linux:
sudo systemctl start postgresql
```

### Problem: "django.db.utils.OperationalError: FATAL: password authentication failed"

**Solution:**
Update the database credentials in `backend/settings.py` to match your PostgreSQL setup.

### Problem: "relation 'users' does not exist"

**Solution:**
Your database doesn't have a `users` table. Create it:

```sql
-- Connect to PostgreSQL
psql -U postgres -d my_database

-- Create the users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Problem: "Port 8000 is already in use"

**Solution:**
Either stop the process using port 8000 or use a different port:
```bash
python manage.py runserver 8080
```

### Problem: CORS errors when calling from frontend

**Solution:**
The API is configured to allow all origins during development. If you're still getting CORS errors:

1. Check that `corsheaders` is installed:
   ```bash
   pip show django-cors-headers
   ```

2. Verify CORS settings in `backend/settings.py`:
   ```python
   CORS_ALLOW_ALL_ORIGINS = True
   ```

## 📊 Verify Everything is Working

Run this comprehensive test:

```bash
# 1. Create a user
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }'

# Expected: 201 Created with user data

# 2. List all users
curl http://localhost:8000/api/users/

# Expected: 200 OK with list of users

# 3. Get specific user (replace 1 with actual ID from step 1)
curl http://localhost:8000/api/users/1/

# Expected: 200 OK with user details

# 4. Update user
curl -X PATCH http://localhost:8000/api/users/1/ \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Johnny"}'

# Expected: 200 OK with updated user data

# 5. Delete user
curl -X DELETE http://localhost:8000/api/users/1/

# Expected: 204 No Content
```

If all tests pass, congratulations! Your API is working correctly. 🎉

## 🎓 Next Steps

1. **Read the Documentation**
   - `README.md` - Overview and API reference
   - `API_WORKFLOW.md` - Detailed explanation of how the code works

2. **Explore the Code**
   - `users/models.py` - Database schema
   - `users/serializers.py` - Data validation
   - `users/views.py` - Business logic
   - `users/urls.py` - URL routing

3. **Experiment**
   - Add new fields to the User model
   - Create custom validation rules
   - Add new endpoints

4. **Build Something**
   - Create a frontend application
   - Add authentication
   - Create additional models

## 📞 Getting Help

If you're stuck:
1. Check the error message carefully
2. Look in the [Troubleshooting](#troubleshooting) section
3. Review the code comments
4. Check Django/DRF documentation

## 🔐 Security Notes

**Important:** This setup is for development only. Before deploying to production:

1. Change `SECRET_KEY` in `settings.py`
2. Set `DEBUG = False`
3. Update `ALLOWED_HOSTS`
4. Configure proper CORS settings (don't use `CORS_ALLOW_ALL_ORIGINS = True`)
5. Use environment variables for sensitive data
6. Enable HTTPS
7. Add authentication and authorization
8. Set up proper logging
9. Use a production-grade web server (Gunicorn, uWSGI)
10. Set up a reverse proxy (Nginx, Apache)

---

**Happy Coding! 🚀**

