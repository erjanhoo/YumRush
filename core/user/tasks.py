from celery import shared_task
from django.core.mail import send_mail

from django.conf import settings


@shared_task
def send_otp_email(user_email,otp_code):
    send_mail(
        subject='Code',
        message=f'Your OTP code is {otp_code}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )