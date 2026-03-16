# accounts/email_utils.py
import logging
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site

logger = logging.getLogger('django')


def send_verification_email(request, user):
    """
    Send account verification email after registration
    Returns: dict with success status and message
    """
    try:
        current_site = get_current_site(request)
        mail_subject = 'Please activate your account'
        
        message = render_to_string('accounts/account_verification_email.html', {
            'user': user,
            'domain': current_site,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        
        send_email = EmailMessage(
            subject=mail_subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        
        send_email.send(fail_silently=False)
        logger.info(f"Verification email sent to {user.email}")
        
        return {
            'success': True,
            'message': 'Verification email sent successfully'
        }
    
    except Exception as e:
        logger.error(f"Verification email error for {user.email}: {str(e)}")
        return {
            'success': False,
            'message': f'Email sending failed: {str(e)}'
        }


def send_password_reset_email(request, user):
    """
    Send password reset email
    Returns: dict with success status and message
    """
    try:
        current_site = get_current_site(request)
        mail_subject = 'Reset Your Password'
        
        message = render_to_string('accounts/reset_password_email.html', {
            'user': user,
            'domain': current_site,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        
        send_email = EmailMessage(
            subject=mail_subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        
        send_email.send(fail_silently=False)
        logger.info(f"Password reset email sent to {user.email}")
        
        return {
            'success': True,
            'message': 'Password reset email sent successfully'
        }
    
    except Exception as e:
        logger.error(f"Password reset email error for {user.email}: {str(e)}")
        return {
            'success': False,
            'message': f'Email sending failed: {str(e)}'
        }


def send_order_confirmation_email(order):
    """
    Send order confirmation email
    Returns: dict with success status and message
    """
    try:
        mail_subject = f'Order Confirmation - Order #{order.order_number}'
        
        message = render_to_string('orders/order_recieved_email.html', {
            'order': order,
            'order_number': order.order_number,
        })
        
        send_email = EmailMessage(
            subject=mail_subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.user.email]
        )
        
        send_email.send(fail_silently=False)
        logger.info(f"Order confirmation email sent to {order.user.email}")
        
        return {
            'success': True,
            'message': 'Order confirmation email sent'
        }
    
    except Exception as e:
        logger.error(f"Order confirmation email error: {str(e)}")
        return {
            'success': False,
            'message': f'Email sending failed: {str(e)}'
        }
