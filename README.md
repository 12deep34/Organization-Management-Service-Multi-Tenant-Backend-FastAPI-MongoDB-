# Organization Management Service

Multi-tenant backend service with FastAPI and MongoDB for managing organizations.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy environment file
cp .env.example .env

# 3. Start MongoDB (required)
# Option A: Local MongoDB
mongod

# Option B: Docker
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# 4. Run the application
uvicorn main:app --reload --port 8000
```

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/org/create` | Create organization | No |
| GET | `/org/get?organization_name=<name>` | Get organization | No |
| PUT | `/org/update` | Update organization | Credentials |
| DELETE | `/org/delete` | Delete organization | JWT |
| POST | `/admin/login` | Admin login | No |

## cURL Commands to Test Each Endpoint

### 1. Create Organization (POST /org/create)

```bash
curl -X POST http://localhost:8000/org/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "TechCorp",
    "email": "admin@techcorp.com",
    "password": "SecurePass123"
  }'
```

**Expected Response:**
```json
{
  "message": "Organization created successfully",
  "organization_id": "...",
  "admin_id": "...",
  "collection_name": "org_techcorp"
}
```

### 2. Get Organization (GET /org/get)

```bash
curl -X GET "http://localhost:8000/org/get?organization_name=TechCorp"
```

**Expected Response:**
```json
{
  "organization_name": "TechCorp",
  "admin_email": "admin@techcorp.com",
  "created_at": "2025-12-12T...",
  "collection_name": "org_techcorp"
}
```

### 3. Admin Login (POST /admin/login)

```bash
curl -X POST http://localhost:8000/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@techcorp.com",
    "password": "SecurePass123"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save the token for delete operation:**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4. Update Organization (PUT /org/update)

```bash
curl -X PUT http://localhost:8000/org/update \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "TechCorp Global",
    "email": "admin@techcorp.com",
    "password": "SecurePass123"
  }'
```

**Expected Response:**
```json
{
  "message": "Organization updated successfully",
  "old_name": "TechCorp",
  "new_name": "TechCorp Global"
}
```

### 5. Delete Organization (DELETE /org/delete)

**First login to get a fresh token:**
```bash
curl -X POST http://localhost:8000/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@techcorp.com",
    "password": "SecurePass123"
  }'
```

**Then delete with the token:**
```bash
curl -X DELETE http://localhost:8000/org/delete \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "organization_name": "TechCorp Global"
  }'
```

**Expected Response:**
```json
{
  "message": "Organization deleted successfully",
  "organization_name": "TechCorp Global",
  "collection_deleted": "org_techcorp_global"
}
```

### 6. Health Check (GET /health)

```bash
curl -X GET http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "mongodb": "connected"
}
```

## Complete Test Flow (Copy & Paste)

```bash
# 1. Create organization
curl -X POST http://localhost:8000/org/create -H "Content-Type: application/json" -d '{"organization_name": "TestOrg", "email": "test@example.com", "password": "TestPass123"}'

# 2. Get organization
curl -X GET "http://localhost:8000/org/get?organization_name=TestOrg"

# 3. Login and save token
TOKEN=$(curl -s -X POST http://localhost:8000/admin/login -H "Content-Type: application/json" -d '{"email": "test@example.com", "password": "TestPass123"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Token: $TOKEN"

# 4. Update organization
curl -X PUT http://localhost:8000/org/update -H "Content-Type: application/json" -d '{"organization_name": "TestOrg Updated", "email": "test@example.com", "password": "TestPass123"}'

# 5. Login again (org name changed)
TOKEN=$(curl -s -X POST http://localhost:8000/admin/login -H "Content-Type: application/json" -d '{"email": "test@example.com", "password": "TestPass123"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# 6. Delete organization
curl -X DELETE http://localhost:8000/org/delete -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"organization_name": "TestOrg Updated"}'
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 FastAPI Server                  │
├─────────────────────────────────────────────────┤
│  Routes: /org/*, /admin/*                       │
│  Auth: JWT + Bcrypt                             │
├─────────────────────────────────────────────────┤
│              MongoDB Database                   │
│  ├── organizations (metadata)                   │
│  ├── admins (credentials)                       │
│  └── org_<name> (dynamic collections)           │
└─────────────────────────────────────────────────┘
```

## Project Structure

```
├── main.py           # FastAPI app
├── config.py         # Settings
├── database.py       # MongoDB manager
├── models.py         # Pydantic models
├── auth.py           # JWT & Bcrypt
├── dependencies.py   # Auth middleware
├── routes/
│   ├── organization.py
│   └── admin.py
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Docker

```bash
docker-compose up -d
```

## Tech Stack

- **Framework**: FastAPI
- **Database**: MongoDB
- **Auth**: JWT + Bcrypt
- **Validation**: Pydantic
