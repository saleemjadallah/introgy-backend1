# Testing Authentication in Production

This document explains how to verify that the authentication system (auth.py) is properly deployed and functioning in your production environment.

## 1. Remote Server Check

Use the provided `check_remote_auth.sh` script to check if auth.py exists on your production server:

```bash
./check_remote_auth.sh your-server-ip-or-domain ubuntu
```

This script will:
- Check if the auth.py file exists in the expected location
- Verify if the auth router is properly registered in main.py
- Check if the service is running
- Test the API health endpoint
- Check service logs for auth-related errors

## 2. Testing Authentication Endpoints

Use the provided `test_auth.py` script to test authentication endpoints:

### Running the test locally

```bash
# Test against local server
./test_auth.py
```

### Running the test against production

```bash
# Test against production server
./test_auth.py https://api.introgy.ai
```

## 3. Manual API Testing

You can also test the authentication API manually using curl:

```bash
# Test health endpoint
curl https://api.introgy.ai/health

# Test login endpoint (will fail with invalid credentials, but confirms endpoint exists)
curl -X POST https://api.introgy.ai/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@example.com","password":"password"}'
```

## 4. Checking Server Logs

SSH into your server and check logs for authentication-related issues:

```bash
# Check service logs
sudo journalctl -u introgy-backend.service -n 100

# Check for errors specifically
sudo journalctl -u introgy-backend.service -n 200 | grep -i "error"

# Check for auth-related logs
sudo journalctl -u introgy-backend.service -n 200 | grep -i "auth"
```

## 5. Verifying Python Imports

To verify Python module imports are working correctly:

```bash
# SSH into your server
ssh ubuntu@your-server-ip

# Navigate to the project directory
cd /home/ubuntu/introgy-backend

# Activate the virtual environment
source venv/bin/activate

# Run a Python script to test imports
python -c "import sys; sys.path.insert(0, '.'); from app.routers import auth; print('Auth module successfully imported')"
```

## 6. Testing with a Real Account

Create a test user account to verify the end-to-end authentication flow:

1. Register a new user:
```bash
curl -X POST https://api.introgy.ai/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePassword123","display_name":"Test User"}'
```

2. Request an OTP:
```bash
curl -X POST https://api.introgy.ai/api/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

3. Check your email for the OTP and verify:
```bash
curl -X POST https://api.introgy.ai/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","code":"123456"}'
```

4. Login and get a token:
```bash
curl -X POST https://api.introgy.ai/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@example.com","password":"SecurePassword123"}'
```

5. Verify the token:
```bash
curl -X GET https://api.introgy.ai/api/auth/verify-token \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 7. Common Issues and Solutions

### Module Not Found Errors
- Check if PYTHONPATH is correctly set in the systemd service file
- Ensure all __init__.py files exist in the package directories

### Authentication Failures
- Verify JWT_SECRET_KEY is correctly set in the environment
- Check database connectivity for user lookup

### Server Connection Issues
- Verify the service is running with `systemctl status introgy-backend.service`
- Check if the correct ports are open in your firewall/security group

### Email Verification Problems
- Verify SENDGRID_API_KEY is correctly set
- Check logs for email sending errors 