import os
import logging
from typing import Dict

from mailjet_rest import Client
from agents import Agent, function_tool

logger = logging.getLogger(__name__)

@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Send an email with the given subject and HTML body """
    logger.info(f"Attempting to send email with subject: {subject}")
    api_key = os.environ.get('MAILJET_API_KEY')
    api_secret = os.environ.get('MAILJET_API_SECRET')
    
    if not api_key or not api_secret:
        error_msg = "MAILJET_API_KEY or MAILJET_API_SECRET not configured. Email not sent."
        logger.warning(error_msg)
        return {"status": "error", "message": error_msg}
    
    try:
        logger.debug("Creating Mailjet client")
        mailjet = Client(auth=(api_key, api_secret), version='v3.1')
        
        data = {
            'Messages': [
                {
                    "From": {
                        "Email": "sergei.lerner@me.com",  # put your verified sender here
                        "Name": "Deep Research"
                    },
                    "To": [
                        {
                            "Email": "sergei.lerner@me.com",  # put your recipient here
                        }
                    ],
                    "Subject": subject,
                    "HTMLPart": html_body
                }
            ]
        }
        
        logger.debug("Sending email via Mailjet API")
        result = mailjet.send.create(data=data)
        logger.info(f"Email response status code: {result.status_code}")
        print("Email response", result.status_code)
        
        if result.status_code == 200:
            logger.info("Email sent successfully")
            return {"status": "success"}
        else:
            error_msg = f"Mailjet API returned status {result.status_code}"
            logger.error(error_msg)
            if hasattr(result, 'json'):
                logger.error(f"Response body: {result.json()}")
            return {"status": "error", "message": error_msg}
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        return {"status": "error", "message": error_msg}

INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
