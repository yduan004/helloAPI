# Django User Management API

A comprehensive REST API for user management with full CRUD operations, built with Django and Django REST Framework.

## 📋 Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [API Endpoints](#api-endpoints)
- [API Usage Examples](#api-usage-examples)
- [Understanding the Code](#understanding-the-code)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## ✨ Features

- **Complete CRUD Operations**: Create, Read, Update, and Delete users
- **RESTful API**: Following REST best practices
- **PostgreSQL Integration**: Connected to existing `my_database` database
- **Data Validation**: Automatic validation of user data
- **Search & Filtering**: Search users by name and email
- **Pagination**: Efficient handling of large datasets
- **CORS Support**: Ready for frontend integration
- **Admin Interface**: Built-in Django admin for easy management
- **Comprehensive Documentation**: Well-commented code for learning

## 🛠 Technology Stack

- **Python 3.x**
- **Django 4.2.7**: Web framework
- **Django REST Framework 3.14.0**: API toolkit
- **PostgreSQL**: Database (using existing `my_database`)
- **psycopg2-binary 2.9.9**: PostgreSQL adapter
- **django-cors-headers 4.3.1**: CORS handling

## 📁 Project Structure

```
helloApi/
├── backend/                 # Main project directory
│   ├── __init__.py
│   ├── settings.py         # Project settings (database, apps, middleware)
│   ├── urls.py             # Main URL routing
│   ├── wsgi.py             # WSGI configuration
│   └── asgi.py             # ASGI configuration
├── users/                   # Users app
│   ├── __init__.py
│   ├── models.py           # User model (database schema)
│   ├── serializers.py      # Data serialization/validation
│   ├── views.py            # Business logic and API endpoints
│   ├── urls.py             # App-level URL routing
│   ├── admin.py            # Django admin configuration
│   ├── apps.py             # App configuration
│   └── migrations/         # Database migrations
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🚀 Setup Instructions

### 1. Prerequisites

Make sure you have:
- Python 3.8 or higher installed
- PostgreSQL installed and running
- Database `my_database` created with `users` table

### 2. Install Dependencies

```bash
# Navigate to project directory
cd /Users/yduan/git/helloApi

# Install required packages
pip install -r requirements.txt
```

### 3. Configure Database

The project is already configured to use your PostgreSQL database. If you need to change the database credentials, edit `backend/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'my_database',      # Your database name
        'USER': 'postgres',          # Your PostgreSQL username
        'PASSWORD': 'postgres',      # Your PostgreSQL password
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 4. Verify Database Connection

```bash
# Test database connection
python manage.py dbshell
# If successful, you'll enter PostgreSQL shell. Type \q to exit.
```

### 5. Create Django Admin User (Optional)

```bash
# Create a superuser for Django admin interface
python manage.py createsuperuser
# Follow the prompts to create username, email, and password
```

### 6. Run the Development Server

```bash
# Start the server
python manage.py runserver

# Server will start at: http://localhost:8000
```

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000/api/
```

### Standard CRUD Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/` | List all users (paginated) |
| POST | `/api/users/` | Create a new user |
| GET | `/api/users/{id}/` | Get a specific user |
| PUT | `/api/users/{id}/` | Update a user (full update) |
| PATCH | `/api/users/{id}/` | Update a user (partial update) |
| DELETE | `/api/users/{id}/` | Delete a user |

### Query Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `search` | Search in name and email | `/api/users/?search=john` |
| `page` | Page number for pagination | `/api/users/?page=2` |

## 📝 API Usage Examples

### 1. List All Users

**Request:**
```bash
curl -X GET http://localhost:8000/api/users/
```

**Response:**
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/users/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com"
        }
    ]
}
```

### 2. Create a New User

**Request:**
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane@example.com"
  }'
```

**Response:**
```json
{
    "id": 2,
    "name": "Jane Smith",
    "email": "jane@example.com"
}
```

### 3. Get a Specific User

**Request:**
```bash
curl -X GET http://localhost:8000/api/users/1/
```

**Response:**
```json
{
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
}
```

### 4. Update a User (Full Update)

**Request:**
```bash
curl -X PUT http://localhost:8000/api/users/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe Updated",
    "email": "john.updated@example.com"
  }'
```

### 5. Update a User (Partial Update)

**Request:**
```bash
curl -X PATCH http://localhost:8000/api/users/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Johnny Doe"
  }'
```

### 6. Delete a User

**Request:**
```bash
curl -X DELETE http://localhost:8000/api/users/1/
```

**Response:** `204 No Content`

### 7. Search Users

**Request:**
```bash
curl -X GET "http://localhost:8000/api/users/?search=john"
```

## 🧠 Understanding the Code

### How Django REST Framework Works

```
Client Request → URL Router → View → Serializer → Model → Database
                                ↓
Client Response ← JSON ← Serializer ← View ← Model ← Database
```

### Key Components

#### 1. Models (`users/models.py`)
- Defines the database schema
- Maps to the `users` table in PostgreSQL
- Provides methods for data manipulation

```python
class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    # ... more fields
```

#### 2. Serializers (`users/serializers.py`)
- Converts between Python objects and JSON
- Validates incoming data
- Handles data transformation

```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email']
```

#### 3. Views (`users/views.py`)
- Contains business logic
- Handles HTTP requests
- Returns HTTP responses

```python
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
```

#### 4. URLs (`users/urls.py` & `backend/urls.py`)
- Maps URLs to views
- Defines API endpoints

```python
router.register(r'users', UserViewSet, basename='user')
```

### Request Flow Example

When you make a request to `GET /api/users/1/`:

1. **URL Routing**: Django matches the URL pattern in `backend/urls.py`
2. **View Selection**: Routes to `UserViewSet.retrieve()`
3. **Database Query**: View fetches user with ID 1 from database
4. **Serialization**: `UserSerializer` converts the User object to JSON
5. **Response**: JSON is returned to the client

## 🗄 Database Schema

The `users` table structure:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL
);
```

**Note:** The model is set to `managed = False`, which means Django won't try to create or modify this table. It will only read from and write to the existing table.

## 🧪 Testing

### Using Django's Browsable API

1. Open your browser and go to: `http://localhost:8000/api/users/`
2. You'll see a web interface where you can:
   - View all users
   - Create new users using the form
   - Click on individual users to view/edit/delete

### Using curl

See the [API Usage Examples](#api-usage-examples) section above.

### Using Postman

1. Import the following base URL: `http://localhost:8000/api/`
2. Create requests for each endpoint
3. Set `Content-Type: application/json` header for POST/PUT/PATCH requests

### Using Python requests

```python
import requests

# List all users
response = requests.get('http://localhost:8000/api/users/')
print(response.json())

# Create a user
data = {
    'username': 'test_user',
    'email': 'test@example.com',
    'first_name': 'Test',
    'last_name': 'User'
}
response = requests.post('http://localhost:8000/api/users/', json=data)
print(response.json())
```

## 🔧 Troubleshooting

### Issue: "django.db.utils.OperationalError: FATAL: password authentication failed"

**Solution:** Check your database credentials in `backend/settings.py`. Make sure the username, password, and database name are correct.

### Issue: "Table 'users' doesn't exist"

**Solution:** Make sure your PostgreSQL database has a `users` table. You can create it using the SQL schema provided in the [Database Schema](#database-schema) section.

### Issue: "Port 8000 is already in use"

**Solution:** Either stop the process using port 8000 or run the server on a different port:
```bash
python manage.py runserver 8080
```

### Issue: "ModuleNotFoundError: No module named 'rest_framework'"

**Solution:** Install the dependencies:
```bash
pip install -r requirements.txt
```

### Issue: CORS errors when calling from frontend

**Solution:** The project is configured to allow all origins during development (`CORS_ALLOW_ALL_ORIGINS = True`). For production, update the CORS settings in `backend/settings.py` to specify allowed origins.

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework Documentation](https://www.django-rest-framework.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🎓 Learning Path

If you're new to Django, here's a recommended learning path:

1. **Understand Models**: Start with `users/models.py` to see how data is structured
2. **Learn Serializers**: Check `users/serializers.py` to understand data validation
3. **Study Views**: Review `users/views.py` to see how requests are handled
4. **Explore URLs**: Look at `users/urls.py` and `backend/urls.py` for routing
5. **Test the API**: Use the browsable API or curl to test endpoints
6. **Modify and Experiment**: Try adding new fields or endpoints

## 📞 Support

If you encounter any issues or have questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review the code comments - they explain what each part does
3. Consult the Django and DRF documentation

---

**Happy Coding! 🚀**

