# Introgy Backend

This is the backend for the Introgy project, built with Python, FastAPI, and MongoDB.

## Stack
- **Python 3.10+**
- **FastAPI** (web framework)
- **Motor** (async MongoDB driver)
- **Uvicorn** (ASGI server)
- **Pydantic** (data validation)
- **JWT** (authentication)
- **SMTP** (email notifications)

## Features
- Async API endpoints
- MongoDB integration
- JWT-based authentication
- Email verification system
- Environment-based configuration
- Ready for deployment on Amazon EC2

## Project Structure
```
introgy-backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── routes.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py
│   │   └── email.py
│   └── routers/
│       ├── __init__.py
│       └── auth.py
├── requirements.txt
└── README.md
```

## Domain Configuration

The Introgy platform uses different domains for different purposes:

### Domain Setup
- `introgy.ai` - Main website and email communications
  - Main website hosting
  - Email services (SendGrid)
  - User-facing URLs in email templates
  - Frontend application

- `introgy.app` - Backend API server (EC2)
  - FastAPI backend service
  - API endpoints
  - Server-side processing

This separation allows for better security and scalability while maintaining a consistent user experience through the main domain.

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:

   Create `Mongo.env` with MongoDB settings:
   ```env
   MONGO_URI=your_mongodb_connection_string
   ```

   Create `Email.env` with email settings:
   ```env
   SMTP_HOST=your_smtp_host
   SMTP_PORT=587
   SMTP_USER=your_smtp_username
   SMTP_PASSWORD=your_smtp_password
   FROM_EMAIL=noreply@introgy.ai
   JWT_SECRET_KEY=your_secure_jwt_secret
   ```

4. Run the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   The API will be available at:
   - Local: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Documentation

### Authentication Endpoints
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/send-verification-code` - Send email verification code
- `POST /auth/verify-otp` - Verify email with OTP
- `POST /auth/reset-password` - Reset user password
- `POST /auth/refresh-token` - Refresh access token
- `GET /auth/verify-token` - Verify token validity

### User Endpoints
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update user profile
- `GET /users/lookup` - Look up user by email

### Social Battery Endpoints
- `GET /social-battery/{user_id}` - Get user's social battery
- `POST /social-battery/{user_id}/record` - Record social interaction
- `GET /social-battery/{user_id}/activity` - Get social activity history

## Authentication Setup

The Introgy backend uses JWT-based authentication with the following features:

- JWT token authentication using the HS512 algorithm
- Password hashing with bcrypt (12 rounds)
- Email verification via OTP codes
- Password reset functionality
- Token refresh mechanism

### Setting Up Authentication

1. Make sure all required environment variables are set:
   - `JWT_SECRET_KEY`: Secret key for JWT signing (will be auto-generated if not provided)
   - `SENDGRID_API_KEY`: API key for SendGrid email service
   - `FROM_EMAIL`: Sender email address (defaults to support@introgy.ai)
   - `FRONTEND_URL`: URL of the frontend application

2. Run the application with proper Python path:
   ```
   PYTHONPATH=/path/to/introgy-backend python run.py
   ```

### Production Deployment

For production deployment, follow these steps:

1. Clone the repository to your server
2. Run the setup_production.sh script:
   ```
   ./setup_production.sh
   ```
   
   This script will:
   - Create a virtual environment and install dependencies
   - Generate a secure JWT secret key
   - Configure the systemd service
   - Start the application

3. The application will be running as a systemd service with proper environment configuration

### Troubleshooting

If you encounter ModuleNotFoundError:
- Make sure `PYTHONPATH` includes the root directory of the project
- Verify all imports are absolute rather than relative
- Check that `__init__.py` files exist in all package directories
- Ensure the systemd service has the correct environment variables

## Deployment

### Amazon EC2 Setup
1. Launch an EC2 instance (Ubuntu recommended)
2. Install Python 3.10+ and required packages
3. Set up Nginx as reverse proxy
4. Configure SSL with Let's Encrypt
5. Use systemd to manage the FastAPI service

### Environment Variables
Make sure to set up all environment variables in production:
- MongoDB connection string
- SMTP settings
- JWT secret key
- Production URLs and ports

### Security Notes
- Always use HTTPS in production
- Set proper CORS origins
- Keep environment files secure
- Regularly rotate JWT secrets
- Monitor API usage and rate limit if needed

## Verifying Authentication in Production

To verify that auth.py is properly deployed and functioning on your production Ubuntu server:

1. **Remote Server Check**:
   ```bash
   ./check_remote_auth.sh your-server-ip ubuntu
   ```

2. **Test Imports**:
   ```bash
   # On the production server:
   cd /home/ubuntu/introgy-backend
   python test_imports.py
   ```

3. **Test API Endpoints**:
   ```bash
   # Test from any machine:
   ./test_auth.py https://api.introgy.ai
   ```

4. **Check Logs**:
   ```bash
   sudo journalctl -u introgy-backend.service -n 100
   ```

For detailed testing instructions, see [docs/auth_testing.md](docs/auth_testing.md) 