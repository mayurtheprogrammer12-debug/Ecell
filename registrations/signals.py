import logging
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from .models import UserRegistration

logger = logging.getLogger(__name__)


def send_email_in_background(subject, plain_message, from_email, to_email, html_message, instance_pk, email_type):
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=from_email,
            to=[to_email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        
        # Update the database to reflect that the email was sent
        if email_type == 'registration':
            UserRegistration.objects.filter(pk=instance_pk).update(registration_email_sent=True)
        elif email_type == 'round2':
            UserRegistration.objects.filter(pk=instance_pk).update(round2_email_sent=True)
            
        logger.info(f"{email_type} email sent successfully to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send {email_type} email to {to_email}: {str(e)}")


@receiver(post_save, sender=UserRegistration)
def send_registration_emails(sender, instance, created, **kwargs):
    dashboard_url = "https://ennovatex.up.railway.app/dashboard/"

    # 1. Registration Confirmation
    # We only send this if it's new AND (either FREE or PENDING payment verification after redirection from payment page)
    # The condition `not instance.registration_email_sent` prevents duplicate emails.
    if not instance.registration_email_sent:
        # Check if the registration is complete (either FREE or success redirect has happened setting it to PENDING)
        # Note: In register_participant, it's set to PENDING before payment, but here we want to ensure it's "valid" 
        # to send. If a user closes the payment page without submitting, it might still stay PENDING.
        # However, the user requested "after the payment page is redirect to payment success".
        # This usually happens in payment_verify view which keeps status as PENDING but updates transaction_id.
        
        should_send = False
        if instance.payment_status == 'FREE':
            should_send = True
        elif instance.payment_status == 'PENDING' and instance.payment_attempts.filter(transaction_id__isnull=False).exists():
            # This means they at least provided a transaction ID on the success/verify page
            should_send = True

        if should_send:
            try:
                subject = "Registration Successful – PCCOE Entrepreneurship Event"
                context = {
                    'participant_name': instance.name,
                    'dashboard_url': dashboard_url,
                    'logo_url': "https://ennovatex.up.railway.app/static/images/logo.png"
                }
                html_message = render_to_string('emails/registration_success.html', context)
                plain_message = strip_tags(html_message)
                
                # Send synchronously to prevent serverless environments from terminating the background thread
                send_email_in_background(
                    subject, plain_message, 'prince@ennovatex26.in', instance.email, html_message, instance.pk, 'registration'
                )
            except Exception as e:
                logger.error(f"Failed to initialize registration email thread: {str(e)}")

    # 2. Round 2 Selection
    if instance.selected_for_round2 and not instance.round2_email_sent:
        try:
            subject = "Congratulations! You have qualified for Round 2"
            context = {
                'participant_name': instance.name,
                'dashboard_url': dashboard_url,
                'logo_url': "https://ennovatex.up.railway.app/static/images/logo.png"
            }
            html_message = render_to_string('emails/round2_selection.html', context)
            plain_message = strip_tags(html_message)
            
            # Send synchronously to prevent serverless environments from terminating the background thread
            send_email_in_background(
                subject, plain_message, 'prince@ennovatex26.in', instance.email, html_message, instance.pk, 'round2'
            )
        except Exception as e:
            logger.error(f"Failed to initialize Round 2 email thread: {str(e)}")

