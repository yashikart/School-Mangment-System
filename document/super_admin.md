# Super Admin Setup Guide

## Overview

This document describes the Super Admin setup and management for the School Management System. The Super Admin is the highest authority in the system and can only be created **once** during initial setup.

## Super Admin Details

- **Email**: `blackholeinfiverse48@gmail.com`
- **Password**: `superadmin123`
- **Role**: `SUPER_ADMIN`
- **School ID**: `NULL` (not associated with any school)

## Important Security Rules

1. **One-Time Creation Only**: The Super Admin account can only be created once. After creation, no API or script can create another SUPER_ADMIN user.

2. **No Signup Form**: There is **NO** signup form or API endpoint for regular users to create a Super Admin account.

3. **Secure Password Storage**: All passwords are hashed using bcrypt before storage in the database.

4. **Role Protection**: No API endpoint allows creating a user with `SUPER_ADMIN` role. This is enforced at the application level.

## Setup Methods

There are two methods to create the Super Admin account:

### Method 1: Using the Setup Script (Recommended)

The setup script is the preferred method for creating the Super Admin account.

```bash
python scripts/setup_super_admin.py
```

**What the script does:**
1. Checks if a SUPER_ADMIN already exists in the database
2. If no SUPER_ADMIN exists, creates one with the predefined credentials
3. If SUPER_ADMIN already exists, displays a message and exits

**Output (First Run):**
```
Creating Super Admin account...
✓ Super Admin created successfully!
  ID: 1
  Email: blackholeinfiverse48@gmail.com
  Role: SUPER_ADMIN
  School ID: None

⚠️  IMPORTANT:
  - Keep these credentials secure
  - Change the password after first login if possible
  - Do not run this script again
```

**Output (Subsequent Runs):**
```
✓ Super Admin already exists. Setup is not needed.
  The system already has a SUPER_ADMIN account.
```

### Method 2: Using the Setup API Endpoint

**⚠️ WARNING**: This endpoint should be protected or removed in production after initial setup.

```bash
POST /super-admin/setup
```

**Request:**
- No body required
- No authentication required (for initial setup only)

**Response (First Run):**
```json
{
  "success": true,
  "message": "Super Admin created successfully.",
  "already_exists": false
}
```

**Response (Subsequent Runs):**
```json
{
  "success": false,
  "message": "Super Admin already exists. Setup is disabled.",
  "already_exists": true
}
```

**Important Notes:**
- This endpoint checks for existing SUPER_ADMIN before creation
- After first successful creation, this endpoint becomes a no-op
- Consider removing this endpoint in production or protecting it with additional security measures

## Authentication & Login

### Login Endpoint

```bash
POST /auth/login
```

**Request Body:**
```json
{
  "email": "blackholeinfiverse48@gmail.com",
  "password": "superadmin123"
}
```

**Response (Success):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Response (Failure):**
```json
{
  "detail": "Incorrect email or password"
}
```

### JWT Token Contents

The JWT token contains the following claims:
- `sub`: User ID (integer)
- `role`: User role (SUPER_ADMIN, ADMIN, TEACHER, PARENT, STUDENT)
- `school_id`: Associated school ID (null for SUPER_ADMIN)
- `exp`: Token expiration timestamp

### Using the Token

Include the token in the Authorization header for protected endpoints:

```
Authorization: Bearer <access_token>
```

## Super Admin Permissions

The Super Admin has exclusive permissions to:

1. **Create Schools**
   - Endpoint: `POST /schools/`
   - Only SUPER_ADMIN can create new schools

2. **Create School Admins**
   - Endpoint: `POST /schools/{school_id}/admins`
   - Only SUPER_ADMIN can create ADMIN users for schools
   - The created admin will have `ADMIN` role (never `SUPER_ADMIN`)

3. **View All Schools**
   - Endpoint: `GET /schools/`
   - Only SUPER_ADMIN can view all schools in the system

## Access Control Enforcement

### Protected Endpoints

Endpoints that require SUPER_ADMIN role use the dependency `get_current_super_admin`:

```python
from app.dependencies import get_current_super_admin

@router.post("/schools/")
def create_school(
    current_user: User = Depends(get_current_super_admin)
):
    # Only SUPER_ADMIN can access this
    ...
```

### Role Validation

The system prevents creating SUPER_ADMIN users through any API:

- School admin creation endpoint (`POST /schools/{school_id}/admins`) hardcodes the role to `ADMIN`
- No user creation endpoint accepts `SUPER_ADMIN` as a role parameter
- The setup endpoint checks for existing SUPER_ADMIN before creation

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,  -- Hashed with bcrypt
    role user_role NOT NULL,  -- ENUM: SUPER_ADMIN, ADMIN, TEACHER, PARENT, STUDENT
    school_id INTEGER REFERENCES schools(id) NULL,  -- NULL for SUPER_ADMIN
    ...
);
```

### Schools Table

```sql
CREATE TABLE schools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    phone VARCHAR(50),
    email VARCHAR(255),
    ...
);
```

## Security Best Practices

1. **Environment Variables**: Store sensitive configuration (SECRET_KEY, DATABASE_URL) in environment variables, not in code.

2. **Password Hashing**: All passwords are hashed using bcrypt with automatic salt generation.

3. **Token Expiration**: JWT tokens expire after 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).

4. **CORS Configuration**: Configure CORS properly for production to only allow requests from your frontend domain.

5. **Remove Setup Endpoint**: Consider removing or heavily securing the `/super-admin/setup` endpoint after initial setup.

6. **Change Default Password**: After first login, implement a password change feature and change the default Super Admin password.

## Troubleshooting

### Super Admin Already Exists Error

If you see "Super Admin already exists" but don't know the credentials:
1. Check the database directly: `SELECT * FROM users WHERE role = 'SUPER_ADMIN';`
2. Use database admin tools to reset the password hash if needed
3. Alternatively, delete the SUPER_ADMIN record and run the setup script again (use with caution)

### Database Connection Issues

If the setup script fails with database connection errors:
1. Ensure PostgreSQL is running
2. Check `DATABASE_URL` in `.env` file
3. Verify database credentials
4. Ensure the database exists: `CREATE DATABASE school_management_db;`

### Token Authentication Issues

If login succeeds but protected endpoints return 401:
1. Check that the token is included in the Authorization header
2. Verify the token format: `Bearer <token>`
3. Check token expiration (tokens expire after 30 minutes)
4. Verify `SECRET_KEY` matches between token creation and validation

## API Endpoints Summary

| Endpoint | Method | Auth Required | Role Required | Description |
|----------|--------|---------------|---------------|-------------|
| `/auth/login` | POST | No | - | Login and get JWT token |
| `/super-admin/setup` | POST | No | - | One-time Super Admin creation |
| `/schools/` | POST | Yes | SUPER_ADMIN | Create a new school |
| `/schools/` | GET | Yes | SUPER_ADMIN | List all schools |
| `/schools/{id}/admins` | POST | Yes | SUPER_ADMIN | Create school admin |

## Frontend Integration Notes

**Important**: The frontend should **NOT** include:
- Super Admin creation forms
- Role selection during signup (roles are assigned by the backend)
- Any UI elements that allow users to select SUPER_ADMIN role

**Frontend should only support:**
- Login screen (email + password)
- Dashboard based on role returned from the backend
- Role-specific features based on the JWT token claims

## Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/school_management_db

# JWT Configuration
SECRET_KEY=your-secret-key-here-change-in-production-use-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
```

**Security Note**: Never commit the `.env` file to version control. Use `.env.example` as a template.

## Running the Application

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual configuration
   ```

3. **Create Super Admin:**
   ```bash
   python scripts/setup_super_admin.py
   ```

4. **Run the Server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access API Documentation:**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## Support

For issues or questions regarding Super Admin setup:
1. Check this documentation
2. Review the application logs
3. Verify database connectivity and schema
4. Ensure all environment variables are set correctly
