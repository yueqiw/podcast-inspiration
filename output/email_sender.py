import logging
from typing import Optional

import resend

from models import Newsletter
from config.settings import Settings
from .markdown_generator import generate_email_html

logger = logging.getLogger(__name__)


def send_newsletter(
    newsletter: Newsletter,
    settings: Settings,
    recipient_email: Optional[str] = None,
) -> bool:
    """Send newsletter via Resend email service.

    Args:
        newsletter: The newsletter to send.
        settings: Application settings.
        recipient_email: Override recipient email (defaults to settings.newsletter_email).

    Returns:
        True if email was sent successfully, False otherwise.
    """
    if not settings.has_resend:
        logger.error("Resend API key not configured")
        return False

    to_email = recipient_email or settings.newsletter_email
    if not to_email:
        logger.error("No recipient email configured")
        return False

    # Initialize Resend
    resend.api_key = settings.resend_api_key

    # Generate email content
    date_str = newsletter.date.strftime("%B %d, %Y")
    subject = f"Podcast Inspiration - {date_str}"
    html_content = generate_email_html(newsletter)

    try:
        params = {
            "from": "Podcast Inspiration <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }

        response = resend.Emails.send(params)
        logger.info(f"Email sent successfully: {response}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def send_test_email(settings: Settings, recipient_email: Optional[str] = None) -> bool:
    """Send a test email to verify configuration.

    Args:
        settings: Application settings.
        recipient_email: Override recipient email.

    Returns:
        True if test email was sent successfully.
    """
    if not settings.has_resend:
        logger.error("Resend API key not configured")
        return False

    to_email = recipient_email or settings.newsletter_email
    if not to_email:
        logger.error("No recipient email configured")
        return False

    resend.api_key = settings.resend_api_key

    try:
        params = {
            "from": "Podcast Inspiration <onboarding@resend.dev>",
            "to": [to_email],
            "subject": "Podcast Inspiration - Test Email",
            "html": """
            <html>
            <body style="font-family: sans-serif; padding: 20px;">
                <h1>Test Email</h1>
                <p>Your Podcast Inspiration email configuration is working correctly!</p>
                <p>You will receive curated podcast recommendations at this email address.</p>
            </body>
            </html>
            """,
        }

        response = resend.Emails.send(params)
        logger.info(f"Test email sent: {response}")
        return True

    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        return False
