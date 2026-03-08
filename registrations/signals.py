import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from .models import UserRegistration

logger = logging.getLogger(__name__)

@receiver(post_save, sender=UserRegistration)
def send_registration_emails(sender, instance, created, **kwargs):
    # Determine the dashboard URL, you might want to configure this in settings for production
    dashboard_url = "https://ennovatex.up.railway.app/dashboard/"

    # 1. Registration Confirmation
    if created and not instance.registration_email_sent:
        try:
            subject = "Registration Successful – PCCOE Entrepreneurship Event"
            context = {
                'participant_name': instance.name,
                'dashboard_url': dashboard_url,
                'logo_url': "https://ennovatex.up.railway.app/static/images/logo.png" # Assuming a static logo path
            }
            html_message = render_to_string('emails/registration_success.html', context)
            plain_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                to=[instance.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            
            # Use update() to prevent recursion
            UserRegistration.objects.filter(pk=instance.pk).update(registration_email_sent=True)
            logger.info(f"Registration email sent successfully to {instance.email}")
        except Exception as e:
            logger.error(f"Failed to send registration email to {instance.email}: {str(e)}")

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
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                to=[instance.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            
            UserRegistration.objects.filter(pk=instance.pk).update(round2_email_sent=True)
            logger.info(f"Round 2 selection email sent successfully to {instance.email}")
        except Exception as e:
            logger.error(f"Failed to send Round 2 email to {instance.email}: {str(e)}")
