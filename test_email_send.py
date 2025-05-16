import os
import ssl
import certifi
from dotenv import load_dotenv
from pathlib import Path

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

# Load environment variables
env_path = Path(__file__).parent / 'Email.env'
load_dotenv(dotenv_path=env_path)

def test_email_send():
    import traceback
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent

    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    FROM_EMAIL = "support@introgy.ai"  # Hardcode the verified email
    
    print("Detailed SendGrid Test")
    print(f"SendGrid API Key: {SENDGRID_API_KEY}")
    print(f"From Email: {FROM_EMAIL}")

    try:
        # Validate API key
        if not SENDGRID_API_KEY or not SENDGRID_API_KEY.startswith('SG.'):
            raise ValueError("Invalid SendGrid API Key")

        # Initialize SendGrid client
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        
        # Create email message
        from_email = Email(FROM_EMAIL, "Introgy App")
        to_email = To("saleemjadallah@gmail.com")  # Replace with your email
        subject = "Introgy Email Test"
        html_content = HtmlContent("<p>This is a test email from Introgy backend.</p>")
        
        mail = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        # Send email
        response = sg.send(mail)
        
        print("Email sent successfully!")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Body: {response.body}")
        
    except Exception as e:
        print("Detailed Error Information:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("Full Traceback:")
        traceback.print_exc()
        
        # Additional SendGrid specific error handling
        if hasattr(e, 'body'):
            print(f"\nSendGrid Error Body: {e.body}")
        if hasattr(e, 'headers'):
            print(f"SendGrid Error Headers: {e.headers}")

# Run the function
test_email_send()
