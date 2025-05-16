import os
import re
from dotenv import load_dotenv
from typing import Optional
from fastapi import HTTPException, status
from pathlib import Path
import certifi
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent.parent / 'Email.env'
logger.info(f"Loading environment variables from: {env_path}")
load_dotenv(dotenv_path=env_path, override=True)

# Removed additional .env loading to prioritize Email.env

# Configure SSL certificates
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Email configuration
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')

# Parse EMAIL_FROM (e.g. "Introgy Support <support@introgy.ai>")
EMAIL_FROM_RAW = os.getenv('EMAIL_FROM')
EMAIL_FROM_NAME = None
FROM_EMAIL = None
if EMAIL_FROM_RAW:
    match = re.match(r'"?([^"<]*)<([^>]+)>"?', EMAIL_FROM_RAW)
    if match:
        EMAIL_FROM_NAME = match.group(1).strip()
        FROM_EMAIL = match.group(2).strip()
    else:
        FROM_EMAIL = EMAIL_FROM_RAW.strip()
        EMAIL_FROM_NAME = "Introgy Support"
else:
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'support@introgy.ai')
    EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'Introgy Support')

FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://introgy.ai')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
EMAIL_MOCK_MODE = os.getenv('EMAIL_MOCK_MODE', 'false').lower() == 'true'

# Validate critical email configuration
if not SENDGRID_API_KEY:
    logger.error('SENDGRID_API_KEY is not set in Email.env')
    raise ValueError('SENDGRID_API_KEY must be set in Email.env')
if not FROM_EMAIL:
    logger.error('FROM_EMAIL is not set in Email.env')
    raise ValueError('FROM_EMAIL must be set in Email.env')

logger.info(f"Parsed Email Configuration:")
logger.info(f"EMAIL_FROM_NAME: {EMAIL_FROM_NAME}")
logger.info(f"FROM_EMAIL: {FROM_EMAIL}")

logger.info(f"Email Configuration:")
logger.info(f"FROM_EMAIL: {FROM_EMAIL}")
logger.info(f"FRONTEND_URL: {FRONTEND_URL}")
logger.info(f"ENVIRONMENT: {ENVIRONMENT}")
logger.info(f"MOCK MODE: {EMAIL_MOCK_MODE}")
logger.info(f"SendGrid API Key exists: {'Yes' if SENDGRID_API_KEY else 'No'}")
logger.info(f"Using SSL certificates from: {certifi.where()}")

# Debug: Print ALL environment variables
for key, value in os.environ.items():
    if 'EMAIL' in key or 'FROM' in key or 'SENDGRID' in key:
        logger.info(f"ENV: {key} = {value}")

# Log warning if no SendGrid key but continue for mock mode
if not SENDGRID_API_KEY and not EMAIL_MOCK_MODE:
    message = "SENDGRID_API_KEY not found in environment variables"
    if ENVIRONMENT == "production":
        logger.warning(f"{message}. Email functionality will be disabled.")
    else:
        logger.warning(f"{message}. Consider enabling EMAIL_MOCK_MODE=true for testing.")

async def send_email(to_email: str, subject: str, html_content: str):
    """Send an email using SendGrid or mock if mock mode is enabled."""
    # If mock mode is enabled, just log the email instead of sending
    if EMAIL_MOCK_MODE:
        logger.info(f"MOCK EMAIL: To: {to_email}, Subject: {subject}")
        logger.info(f"MOCK EMAIL CONTENT: {html_content}")
        return {"success": True, "message": "Email logged (mock mode enabled)"}
        
    if not SENDGRID_API_KEY:
        logger.warning(f"Email not sent to {to_email}: SendGrid API key not configured")
        return {"success": False, "message": "Email service not configured"}
        
    try:
        # Import SendGrid here to avoid import errors when API key is not set
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
        
        logger.info(f"Attempting to send email to: {to_email}")
        logger.info(f"Using FROM_EMAIL: {FROM_EMAIL}")
        logger.info(f"Using EMAIL_FROM_NAME: {EMAIL_FROM_NAME}")
        
        # Initialize SendGrid client
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        
        # Create email message
        from_email = Email(FROM_EMAIL, EMAIL_FROM_NAME)
        to_email = To(to_email)
        content = HtmlContent(html_content)
        
        mail = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=content
        )
        
        try:
            # Send email - Note: SendGrid's send() is not async, but it's fast enough to not block
            response = sg.send(mail)
            logger.info(f"SendGrid Response Status Code: {response.status_code}")
            logger.info(f"SendGrid Response Headers: {response.headers}")
            logger.info(f"SendGrid Response Body: {response.body}")
        except Exception as send_error:
            logger.error(f"SendGrid send error: {str(send_error)}")
            if hasattr(send_error, 'body'):
                logger.error(f"Error body: {send_error.body}")
            if hasattr(send_error, 'headers'):
                logger.error(f"Error headers: {send_error.headers}")
            raise send_error
        
        if response.status_code not in [200, 201, 202]:
            logger.error(f"SendGrid API error: Status code {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send email. SendGrid Status: {response.status_code}"
            )
            
        logger.info(f"Email sent successfully to {to_email}")
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        
        if "unauthorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Email service configuration error: {str(e)}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )

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

async def send_otp_email(email: str, otp: str):
    """Send an OTP code via email."""
    logger.info(f"Attempting to send OTP email to: {email}")
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
                <p style="margin-top: 20px; font-size: 12px; color: #666;">
                    This is an automated message from Introgy. Please do not reply to this email.
                    Add support@introgy.ai to your contacts to ensure delivery.
                </p>
            </div>
        </body>
    </html>
    """
    try:
        result = await send_email(email, subject, html_content)
        logger.info(f"OTP email sent successfully to {email}")
        return result
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {str(e)}")
        if hasattr(e, 'body'):
            logger.error(f"SendGrid error body: {e.body}")
        raise

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