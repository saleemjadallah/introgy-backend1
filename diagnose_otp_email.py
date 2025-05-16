import asyncio
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / 'Email.env'
load_dotenv(dotenv_path=env_path)

async def diagnose_otp_email(email):
    from app.core.email import send_otp_email
    import logging
    import os
    import sendgrid

    # Configure detailed logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # Log environment variables for debugging
    api_key = os.getenv('SENDGRID_API_KEY')
    logger.info(f"SendGrid API Key Present: {bool(api_key)}")
    logger.info(f"SendGrid API Key Prefix: {api_key[:10] if api_key else 'N/A'}")
    logger.info(f"FROM_EMAIL: {os.getenv('FROM_EMAIL')}")
    logger.info(f"EMAIL_SERVICE: {os.getenv('EMAIL_SERVICE')}")

    # Validate API key format
    if api_key and not api_key.startswith('SG.'):
        logger.error(f"Invalid SendGrid API Key format: {api_key}")
        raise ValueError("Invalid SendGrid API Key")

    # Optional: Test API key validity
    try:
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        response = sg.client.mail.send.get()
        logger.info(f"SendGrid API Key Validation Response: {response.status_code}")
    except Exception as e:
        logger.error(f"SendGrid API Key Validation Failed: {e}")

    try:
        # Generate a test OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        logger.info(f"Attempting to send OTP {otp} to {email}")
        
        # Send OTP email
        result = await send_otp_email(email, otp)
        
        logger.info("OTP Email sending process completed successfully")
        logger.info(f"Result: {result}")
        
    except Exception as e:
        logger.error(f"Error in OTP email sending: {e}")
        logger.error(f"Error Type: {type(e)}")
        
        # If it's a SendGrid error, print more details
        if hasattr(e, 'body'):
            logger.error(f"SendGrid Error Body: {e.body}")
        if hasattr(e, 'headers'):
            logger.error(f"SendGrid Error Headers: {e.headers}")
        
        # Print full traceback
        import traceback
        traceback.print_exc()

# Allow email to be passed as command line argument
if __name__ == "__main__":
    import random
    
    # Use command line argument or default email
    email = sys.argv[1] if len(sys.argv) > 1 else "saleemjadallah@gmail.com"
    
    asyncio.run(diagnose_otp_email(email))
