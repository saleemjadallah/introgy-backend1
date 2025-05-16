import os
import re
from dotenv import load_dotenv
from typing import Optional
from fastapi import HTTPException, status
from pathlib import Path
import certifi
import logging
import json
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent.parent / 'Email.env'
logger.info(f"Loading environment variables from: {env_path}")
load_dotenv(dotenv_path=env_path)

# Configure SSL certificates
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Email configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_MOCK_MODE = os.getenv("EMAIL_MOCK_MODE", "false").lower() == "true"
FROM_EMAIL = os.getenv("FROM_EMAIL", "support@introgy.ai")
EMAIL_FROM_NAME = "Introgy App"
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://introgy.netlify.app")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"

logger.info(f"Email Configuration:")
logger.info(f"FROM_EMAIL: {FROM_EMAIL}")
logger.info(f"FRONTEND_URL: {FRONTEND_URL}")
logger.info(f"ENVIRONMENT: {ENVIRONMENT}")
logger.info(f"SendGrid API Key exists: {'Yes' if SENDGRID_API_KEY else 'No'}")
logger.info(f"Using SSL certificates from: {certifi.where()}")

async def send_email(to_email: str, subject: str, html_content: str):
    """Send an email using SendGrid API directly."""
    if EMAIL_MOCK_MODE:
        logger.warning(f"Email not sent to {to_email}: Running in mock mode")
        return {"success": True, "message": "Email sending skipped (mock mode)"}

    if not SENDGRID_API_KEY:
        logger.warning(f"Email not sent to {to_email}: SendGrid API key not configured")
        return {"success": False, "message": "Email service not configured"}
        
    try:
        logger.info(f"Attempting to send email to: {to_email}, Subject: {subject}")
        
        # Prepare the request
        headers = {
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}]
                }
            ],
            "from": {
                "email": FROM_EMAIL,
                "name": EMAIL_FROM_NAME
            },
            "subject": subject,
            "content": [{
                "type": "text/html",
                "value": html_content
            }]
        }
        
        # Send the request
        response = requests.post(
            SENDGRID_API_URL,
            headers=headers,
            json=data,
            verify=certifi.where(),
            timeout=30
        )
        
        # Log response details
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        logger.info(f"Response Body: {response.text}")
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"Email sent successfully to {to_email}")
            return {"success": True}
        else:
            error_msg = f"SendGrid API error: Status {response.status_code}, Body: {response.text}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
            
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )

async def send_otp_email(email: str, otp: str):
    """Send an OTP code via email."""
    subject = "Your Introgy Verification Code"
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; text-align: center;">Verification Code</h2>
                <p>Here is your verification code for Introgy:</p>
                <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
                    <p style="font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #2c3e50;">
                        {otp}
                    </p>
                </div>
                <p style="margin-top: 20px;">This code will expire in 10 minutes.</p>
                <p style="color: #7f8c8d; font-size: 12px;">
                    If you didn't request this code, please ignore this email.
                </p>
            </div>
        </body>
    </html>
    """
    return await send_email(email, subject, html_content)

async def send_verification_email(email: str):
    """Send a verification email to the user."""
    subject = "Welcome to Introgy - Verify Your Email"
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; text-align: center;">Welcome to Introgy!</h2>
                <p>Thank you for registering with Introgy. We're excited to have you join our community!</p>
                <p>Your email has been registered: <strong>{email}</strong></p>
                <p>You can now proceed with the verification process in your app.</p>
                <div style="text-align: center; margin-top: 30px;">
                    <p style="color: #7f8c8d; font-size: 12px;">
                        If you didn't create an account with Introgy, please ignore this email.
                    </p>
                </div>
            </div>
        </body>
    </html>
    """
    return await send_email(email, subject, html_content)

async def send_password_reset_email(email: str, reset_token: str):
    """Send a password reset email."""
    subject = "Reset Your Introgy Password"
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; text-align: center;">Password Reset Request</h2>
                <p>We received a request to reset your password. Please use this code at <a href="{FRONTEND_URL}/reset-password">{FRONTEND_URL}/reset-password</a>:</p>
                <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
                    <p style="font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #2c3e50;">
                        {reset_token}
                    </p>
                </div>
                <p>This code will expire in 10 minutes.</p>
                <p style="color: #7f8c8d; font-size: 12px;">
                    If you didn't request this password reset, please ignore this email.
                </p>
            </div>
        </body>
    </html>
    """
    return await send_email(email, subject, html_content) 