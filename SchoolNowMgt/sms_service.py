"""
Africa's Talking SMS Service Wrapper for Django School Management System.

This module provides a thin wrapper around the Africa's Talking SMS API.
It handles phone number normalization for Ugandan formats and manages
delivery status tracking through the SMSLog model.

SETTINGS EXPECTED (add to settings.py):
    AT_USERNAME = "your_africastalking_username"
    AT_API_KEY = "your_africastalking_api_key"
    AT_SENDER_ID = "YourSchool"   # optional shortcode, blank='' in sandbox
    AT_SANDBOX = True             # set False in production
"""

import africastalking
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Africa's Talking at module load
africastalking.initialize(
    username=settings.AT_USERNAME,
    api_key=settings.AT_API_KEY,
)
sms_client = africastalking.SMS


def send_sms(recipient_phone, message):
    """
    Send a single SMS via Africa's Talking and return delivery status.
    
    Args:
        recipient_phone (str): Phone number in any Ugandan format
                              (0772123456, 256772123456, +256772123456)
        message (str): SMS message content
    
    Returns:
        tuple: (success: bool, provider_response: str)
               - success: True if status=='Success' from Africa's Talking
               - provider_response: Raw response from API or error message
    
    Phone Normalisation:
        - Strip whitespace
        - If starts with '0', replace leading '0' with '+256' (Uganda code)
        - If starts with '256' without '+', prepend '+'
        - If starts with '+', leave unchanged
        - Otherwise log warning and return (False, "Invalid phone number format")
    """
    try:
        # Step 1: Normalise phone number
        normalised_phone = recipient_phone.strip()
        
        if normalised_phone.startswith('0'):
            # Replace leading 0 with +256
            normalised_phone = '+256' + normalised_phone[1:]
        elif normalised_phone.startswith('256') and not normalised_phone.startswith('+256'):
            # Add + prefix if missing
            normalised_phone = '+' + normalised_phone
        elif normalised_phone.startswith('+256'):
            # Already correct format
            pass
        else:
            # Invalid format
            logger.warning(f"Invalid phone number format: {recipient_phone}")
            return (False, "Invalid phone number format")
        
        # Step 2: Build recipients list
        recipients = [normalised_phone]
        
        # Step 3: Call Africa's Talking API
        response = sms_client.send(
            message=message,
            recipients=recipients,
            sender_id=settings.AT_SENDER_ID or None,
        )
        
        # Step 4: Parse response
        # Africa's Talking returns: {'SMSMessageData': {'Recipients': [{'status': 'Success', ...}], ...}}
        try:
            sms_data = response.get('SMSMessageData', {})
            recipients_data = sms_data.get('Recipients', [])
            
            if recipients_data and recipients_data[0].get('status') == 'Success':
                logger.info(f"SMS sent successfully to {normalised_phone}")
                return (True, str(response))
            else:
                logger.warning(f"SMS delivery failed for {normalised_phone}: {response}")
                return (False, str(response))
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Error parsing Africa's Talking response: {e}")
            return (False, str(response))
    
    except Exception as e:
        # Step 5: Exception handling
        logger.error(f"Error sending SMS to {recipient_phone}: {str(e)}")
        return (False, str(e))
