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

#### API Docs (/docs, /redoc) Not Found (404 Error)

If you encounter a "404 Not Found" error when trying to access `https://yourdomain.com/docs` or `https://yourdomain.com/redoc`, even if the main API seems to be running (e.g., `https://yourdomain.com/` returns a 200 OK), it might be due to issues with how the FastAPI application is configured or being served in the production environment.

**Symptoms:**
- Main API endpoints (e.g., `/api/...`) might be working.
- Direct access to `/docs` or `/redoc` via the browser or `curl` returns a 404, sometimes with `{"detail":"Not Found"}`.
- Nginx logs might show 404s being returned from the backend Uvicorn process for these paths.

**Potential Causes & Solutions:**

1.  **Incorrect FastAPI Configuration in `app/main.py`:**
    *   **Problem:** The `docs_url` or `redoc_url` parameters in the `FastAPI()` constructor might be incorrect, conditionally disabled in production, or pointing to a namespaced path (e.g., `/api/docs`) that conflicts with router prefixes.
    *   **Solution:** Ensure these are set correctly and are not disabled for your production environment. In our case, the fix was to ensure they were set to root paths:
        ```python
        # In app/main.py
        app = FastAPI(
            # ... other parameters ...
            docs_url="/docs",
            redoc_url="/redoc"
        )
        ```

2.  **Code Changes Not Reflected on the Server:**
    *   **Problem:** Edits made to the Python files (e.g., `app/main.py`, `run.py`) in a local development environment or via automated tools might not have been correctly applied or deployed to the actual files being run by the `systemd` service on the production server. The service might be running an older version of the code or code from an unexpected location.
    *   **Solution:**
        *   **Verify Service Configuration:** Double-check your `systemd` service file (e.g., `introgy-backend.service`) to confirm the `WorkingDirectory` and `ExecStart` paths point to the correct location of your backend code on the server (e.g., `/home/ubuntu/introgy-backend`).
        *   **Manually Edit Files on Server:** Connect to your server (e.g., via SSH) and directly edit the Python files in the service's `WorkingDirectory` to apply the necessary changes (like the `docs_url` fix above).
        *   **Ensure `run.py` Uses Production Settings:** For production, `run.py` should typically run Uvicorn with `reload=False` and pass the `app` object directly, not as a string for auto-reloading.
            ```python
            # In run.py
            from app.main import app # Import the app object
            # ...
            uvicorn.run(
                app,             # Pass the app object
                host="0.0.0.0",
                port=8000,
                reload=False     # Essential for production
            )
            ```
        *   **Restart Service:** After making changes directly on the server, always restart the service: `sudo systemctl restart your-service-name.service` (e.g., `sudo systemctl restart introgy-backend.service`).
        *   **Clear Python Bytecode Cache (If Suspected):** In rare cases, old bytecode files (`.pyc`) might cause issues. You can try removing them from your project directory on the server: `sudo find /path/to/your/project -name '*.pyc' -delete` and then restart the service.

3.  **Nginx Configuration:**
    *   **Problem:** While less likely if other API routes work, ensure your Nginx configuration correctly proxies requests for `/docs`, `/redoc`, and `/openapi.json` to the backend service without stripping or altering the path in an unintended way.
    *   **Solution:** Review the `location` blocks in your Nginx site configuration. For FastAPI with docs at the root, a general proxy pass for `/` and `/api/` might be sufficient, but ensure the docs paths are not inadvertently caught or blocked by a more specific, incorrect rule.
        Example Nginx `location` blocks for docs and API:
        ```nginx
        location ~ ^/(docs|redoc|openapi\.json)$ {
            proxy_pass http://127.0.0.1:8000;
            # ... other proxy headers ...
        }

        location /api/ {
            proxy_pass http://127.0.0.1:8000/api/;
            # ... other proxy headers ...
        }

        location / {
            proxy_pass http://127.0.0.1:8000;
            # ... other proxy headers ...
        }
        ```
        *Ensure these are ordered correctly (more specific paths first) if you have multiple location blocks.*

**Diagnostic Steps Used in This Case:**
*   Checked Nginx access and error logs: `/var/log/nginx/introgy.access.log`, `/var/log/nginx/introgy.error.log`.
*   Checked backend service status and logs: `sudo systemctl status introgy-backend.service`, `sudo journalctl -u introgy-backend.service -n 50 --no-pager | cat`.
*   Bypassed Nginx to test backend directly: `curl -I http://127.0.0.1:8000/docs`.
*   Added temporary diagnostic `print()` statements in `app/main.py` (after `app = FastAPI(...)`) and in `run.py` to log the actual `docs_url` and the path of the loaded `app.main` module, then checked service logs for this output.
*   Verified the running process's CWD and command: `systemctl show -p MainPID --value introgy-backend.service`, then `pwdx <PID>` and `ps -p <PID> -o cmd --no-headers`.

By following these steps, we confirmed the FastAPI application instance running on the server did not have the correct `docs_url` until the `app/main.py` file was manually corrected on the server and the service restarted.

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