# API Reference - User Management

Quick reference for your simplified User API with 3 fields: `id`, `name`, `email`

## Database Schema

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);
```

## Base URL
```
http://localhost:8000/api/
```

## Endpoints

### 1. List All Users
```http
GET /api/users/
```

**Query Parameters:**
- `search` - Search in name and email fields
- `is_active` - Filter by active status (true/false)
- `page` - Page number (default: 1, 10 items per page)

**Example Request:**
```bash
curl http://localhost:8000/api/users/
```

**Example Response:**
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "is_active": true
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "email": "jane@example.com",
            "is_active": true
        }
    ]
}
```

### 2. Create a User
```http
POST /api/users/
```

**Request Body:**
```json
{
    "name": "John Doe",
    "email": "john@example.com",
    "is_active": true
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com"
  }'
```

**Success Response (201 Created):**
```json
{
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "is_active": true
}
```

**Error Response (400 Bad Request):**
```json
{
    "name": ["This field is required."],
    "email": ["A user with this email already exists."]
}
```

### 3. Get a Specific User
```http
GET /api/users/{id}/
```

**Example Request:**
```bash
curl http://localhost:8000/api/users/1/
```

**Success Response (200 OK):**
```json
{
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "is_active": true
}
```

**Error Response (404 Not Found):**
```json
{
    "detail": "Not found."
}
```

### 4. Update a User (Full Update)
```http
PUT /api/users/{id}/
```

**Request Body (all fields required):**
```json
{
    "name": "John Doe Updated",
    "email": "john.updated@example.com",
    "is_active": false
}
```

**Example Request:**
```bash
curl -X PUT http://localhost:8000/api/users/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe Updated",
    "email": "john.updated@example.com"
  }'
```

**Success Response (200 OK):**
```json
{
    "id": 1,
    "name": "John Doe Updated",
    "email": "john.updated@example.com",
    "is_active": false
}
```

### 5. Update a User (Partial Update)
```http
PATCH /api/users/{id}/
```

**Request Body (only include fields to update):**
```json
{
    "name": "Johnny Doe"
}
```

**Example Request:**
```bash
curl -X PATCH http://localhost:8000/api/users/1/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Johnny Doe"}'
```

**Success Response (200 OK):**
```json
{
    "id": 1,
    "name": "Johnny Doe",
    "email": "john@example.com",
    "is_active": true
}
```

### 6. Delete a User
```http
DELETE /api/users/{id}/
```

**Example Request:**
```bash
curl -X DELETE http://localhost:8000/api/users/1/
```

**Success Response (204 No Content):**
```
(empty response body)
```

### 7. Search Users
```http
GET /api/users/?search={query}
```

**Example Request:**
```bash
curl "http://localhost:8000/api/users/?search=john"
```

### 8. Filter Active Users
```http
GET /api/users/?is_active={true|false}
```

**Example Request:**
```bash
curl "http://localhost:8000/api/users/?is_active=true"
```

**Response:**
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "is_active": true
        }
    ]
}
```

### 9. Get All Active Users
```http
GET /api/users/active_users/
```

**Example Request:**
```bash
curl http://localhost:8000/api/users/active_users/
```

**Response:**
```json
[
    {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "is_active": true
    },
    {
        "id": 2,
        "name": "Jane Smith",
        "email": "jane@example.com",
        "is_active": true
    }
]
```

### 10. Activate a User
```http
POST /api/users/{id}/activate/
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/users/1/activate/
```

**Success Response (200 OK):**
```json
{
    "status": "User activated successfully",
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "is_active": true
    }
}
```

### 11. Deactivate a User
```http
POST /api/users/{id}/deactivate/
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/users/1/deactivate/
```

**Success Response (200 OK):**
```json
{
    "status": "User deactivated successfully",
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "is_active": false
    }
}
```

**Response:**
```json
{
    "count": 1,
    "next": null,
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

## Field Validation

### Name Field
- **Type:** String
- **Required:** Yes
- **Max Length:** 255 characters
- **Validation:**
  - Cannot be empty
  - Whitespace is trimmed automatically
  - Cannot be only whitespace

### Email Field
- **Type:** Email
- **Required:** Yes
- **Max Length:** 254 characters
- **Validation:**
  - Must be valid email format
  - Must be unique (no duplicates)
  - Converted to lowercase automatically

### Is Active Field
- **Type:** Boolean
- **Required:** No
- **Default:** `true`
- **Description:** Indicates whether the user account is active

## HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Validation error |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Something went wrong |

## Python Examples

```python
import requests

BASE_URL = "http://localhost:8000/api"

# List all users
response = requests.get(f"{BASE_URL}/users/")
users = response.json()
print(users)

# Create a user
data = {
    "name": "John Doe",
    "email": "john@example.com",
    "is_active": True
}
response = requests.post(f"{BASE_URL}/users/", json=data)
new_user = response.json()
print(f"Created user with ID: {new_user['id']}")

# Get a user
user_id = 1
response = requests.get(f"{BASE_URL}/users/{user_id}/")
user = response.json()
print(user)

# Update a user (partial)
data = {"name": "Johnny Doe"}
response = requests.patch(f"{BASE_URL}/users/{user_id}/", json=data)
updated_user = response.json()
print(updated_user)

# Delete a user
response = requests.delete(f"{BASE_URL}/users/{user_id}/")
print(f"Status: {response.status_code}")  # 204

# Search users
params = {"search": "john"}
response = requests.get(f"{BASE_URL}/users/", params=params)
results = response.json()
print(results)

# Filter active users
params = {"is_active": "true"}
response = requests.get(f"{BASE_URL}/users/", params=params)
active_users = response.json()
print(active_users)

# Activate a user
response = requests.post(f"{BASE_URL}/users/{user_id}/activate/")
result = response.json()
print(result['status'])

# Deactivate a user
response = requests.post(f"{BASE_URL}/users/{user_id}/deactivate/")
result = response.json()
print(result['status'])
```

## Testing

### Start the Server
```bash
python manage.py runserver
```

### Test in Browser
Open: http://localhost:8000/api/users/

You'll see Django REST Framework's browsable API interface where you can:
- View all users
- Create new users using the form
- Click on users to view/edit/delete

### Test with curl
```bash
# Create a test user
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com"}'

# List all users
curl http://localhost:8000/api/users/

# Get specific user (replace 1 with actual ID)
curl http://localhost:8000/api/users/1/

# Update user
curl -X PATCH http://localhost:8000/api/users/1/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'

# Delete user
curl -X DELETE http://localhost:8000/api/users/1/
```

## Common Errors

### "A user with this email already exists"
**Cause:** Trying to create/update a user with an email that's already in the database.
**Solution:** Use a different email address.

### "This field is required"
**Cause:** Missing required field (name or email) in POST/PUT request.
**Solution:** Include all required fields in your request.

### "Not found"
**Cause:** Trying to access a user ID that doesn't exist.
**Solution:** Check that the user ID is correct and exists in the database.

---

**Quick Start:**
```bash
# 1. Start server
python manage.py runserver

# 2. Test in browser
open http://localhost:8000/api/users/

# 3. Or test with curl
curl http://localhost:8000/api/users/
```

