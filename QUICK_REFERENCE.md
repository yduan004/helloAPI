# Quick Reference Guide

A cheat sheet for common tasks and commands.

## 🚀 Starting the Server

```bash
# Start development server
python manage.py runserver

# Start on different port
python manage.py runserver 8080

# Start on all interfaces (accessible from network)
python manage.py runserver 0.0.0.0:8000
```

## 📡 API Endpoints Quick Reference

### Base URL
```
http://localhost:8000/api/
```

### User Endpoints

| Action | Method | Endpoint | Body |
|--------|--------|----------|------|
| List users | `GET` | `/api/users/` | - |
| Create user | `POST` | `/api/users/` | `{"username": "...", "email": "..."}` |
| Get user | `GET` | `/api/users/{id}/` | - |
| Update user (full) | `PUT` | `/api/users/{id}/` | `{"username": "...", "email": "...", ...}` |
| Update user (partial) | `PATCH` | `/api/users/{id}/` | `{"first_name": "..."}` |
| Delete user | `DELETE` | `/api/users/{id}/` | - |
| Activate user | `POST` | `/api/users/{id}/activate/` | - |
| Deactivate user | `POST` | `/api/users/{id}/deactivate/` | - |
| Get active users | `GET` | `/api/users/active_users/` | - |

## 🔍 Query Parameters

```bash
# Search users
/api/users/?search=john

# Filter by active status
/api/users/?is_active=true
/api/users/?is_active=false

# Pagination
/api/users/?page=2

# Combine parameters
/api/users/?search=john&is_active=true&page=1
```

## 💻 curl Commands

### List All Users
```bash
curl http://localhost:8000/api/users/
```

### Create User
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Get User by ID
```bash
curl http://localhost:8000/api/users/1/
```

### Update User (Full)
```bash
curl -X PUT http://localhost:8000/api/users/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "Johnny",
    "last_name": "Doe",
    "is_active": true
  }'
```

### Update User (Partial)
```bash
curl -X PATCH http://localhost:8000/api/users/1/ \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Johnny"}'
```

### Delete User
```bash
curl -X DELETE http://localhost:8000/api/users/1/
```

### Search Users
```bash
curl "http://localhost:8000/api/users/?search=john"
```

### Filter Active Users
```bash
curl "http://localhost:8000/api/users/?is_active=true"
```

### Activate User
```bash
curl -X POST http://localhost:8000/api/users/1/activate/
```

### Deactivate User
```bash
curl -X POST http://localhost:8000/api/users/1/deactivate/
```

## 🐍 Python requests Examples

```python
import requests

BASE_URL = "http://localhost:8000/api"

# List all users
response = requests.get(f"{BASE_URL}/users/")
users = response.json()

# Create a user
data = {
    "username": "jane_doe",
    "email": "jane@example.com",
    "first_name": "Jane",
    "last_name": "Doe"
}
response = requests.post(f"{BASE_URL}/users/", json=data)
new_user = response.json()

# Get a user
user_id = 1
response = requests.get(f"{BASE_URL}/users/{user_id}/")
user = response.json()

# Update a user (partial)
data = {"first_name": "Janet"}
response = requests.patch(f"{BASE_URL}/users/{user_id}/", json=data)
updated_user = response.json()

# Delete a user
response = requests.delete(f"{BASE_URL}/users/{user_id}/")
# response.status_code == 204

# Search users
params = {"search": "john"}
response = requests.get(f"{BASE_URL}/users/", params=params)
results = response.json()

# Filter active users
params = {"is_active": "true"}
response = requests.get(f"{BASE_URL}/users/", params=params)
active_users = response.json()
```

## 🗄 Database Commands

### Connect to Database
```bash
# Using Django
python manage.py dbshell

# Using psql directly
psql -U postgres -d my_database
```

### Useful SQL Queries
```sql
-- View all users
SELECT * FROM users;

-- Count users
SELECT COUNT(*) FROM users;

-- Find user by username
SELECT * FROM users WHERE username = 'john_doe';

-- Find active users
SELECT * FROM users WHERE is_active = true;

-- Search users
SELECT * FROM users WHERE username ILIKE '%john%' OR email ILIKE '%john%';

-- Delete a user
DELETE FROM users WHERE id = 1;

-- Update a user
UPDATE users SET first_name = 'Johnny' WHERE id = 1;
```

## 🔧 Django Management Commands

### Database
```bash
# Check database connection
python manage.py dbshell

# Show migrations
python manage.py showmigrations

# Create migrations (if needed)
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Admin
```bash
# Create superuser
python manage.py createsuperuser

# Change user password
python manage.py changepassword username
```

### Development
```bash
# Run development server
python manage.py runserver

# Open Python shell with Django context
python manage.py shell

# Check for issues
python manage.py check

# Show all available commands
python manage.py help
```

## 📝 Common Django Shell Commands

```bash
# Open Django shell
python manage.py shell
```

```python
# Import the User model
from users.models import User

# Get all users
users = User.objects.all()
print(users)

# Get user by ID
user = User.objects.get(id=1)
print(user.username)

# Filter users
active_users = User.objects.filter(is_active=True)
print(active_users)

# Search users
users = User.objects.filter(username__icontains='john')
print(users)

# Create a user
user = User.objects.create(
    username='test_user',
    email='test@example.com',
    first_name='Test',
    last_name='User'
)
print(f"Created user: {user.id}")

# Update a user
user = User.objects.get(id=1)
user.first_name = 'Johnny'
user.save()

# Delete a user
user = User.objects.get(id=1)
user.delete()

# Count users
count = User.objects.count()
print(f"Total users: {count}")

# Get or create
user, created = User.objects.get_or_create(
    username='john_doe',
    defaults={'email': 'john@example.com'}
)
print(f"Created: {created}")
```

## 🧪 Testing Workflow

```bash
# 1. Start the server
python manage.py runserver

# 2. In another terminal, test the API
# Create a user
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com"}'

# 3. Verify in database
python manage.py dbshell
# Then in psql:
SELECT * FROM users WHERE username = 'testuser';
\q

# 4. Test in browser
# Open: http://localhost:8000/api/users/
```

## 🔍 Debugging Tips

### Check Server Logs
The terminal where you ran `python manage.py runserver` shows all requests:
```
[30/Dec/2025 12:00:00] "GET /api/users/ HTTP/1.1" 200 1234
[30/Dec/2025 12:00:05] "POST /api/users/ HTTP/1.1" 201 567
```

### Print Debugging
Add print statements in views:
```python
def create(self, request, *args, **kwargs):
    print(f"Received data: {request.data}")
    # ... rest of code
```

### Django Shell for Testing
```bash
python manage.py shell
```
```python
from users.models import User
from users.serializers import UserSerializer

# Test serializer
data = {"username": "test", "email": "test@example.com"}
serializer = UserSerializer(data=data)
print(serializer.is_valid())
print(serializer.errors)
```

## 📊 HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Validation error |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Something went wrong |

## 🎯 Common Response Formats

### Success Response (List)
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/users/?page=2",
    "previous": null,
    "results": [...]
}
```

### Success Response (Single)
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    ...
}
```

### Error Response
```json
{
    "username": ["A user with this username already exists."],
    "email": ["This field is required."]
}
```

## 📁 File Structure Reference

```
Key Files:
- backend/settings.py    → Configuration
- backend/urls.py        → Main URL routing
- users/models.py        → Database schema
- users/serializers.py   → Data validation
- users/views.py         → Business logic
- users/urls.py          → App URL routing
- users/admin.py         → Admin interface
- requirements.txt       → Dependencies
```

## 🔗 Useful URLs

- **API Root**: http://localhost:8000/api/users/
- **Admin Interface**: http://localhost:8000/admin/
- **API Auth**: http://localhost:8000/api-auth/login/

## 💡 Tips

1. **Use the Browsable API**: Open endpoints in your browser for a nice UI
2. **Check Server Logs**: Always monitor the terminal where the server is running
3. **Use Django Shell**: Great for testing queries and debugging
4. **Read Error Messages**: Django provides detailed error messages
5. **Check Database**: Verify changes directly in PostgreSQL when debugging

---

**Keep this guide handy for quick reference! 📌**

