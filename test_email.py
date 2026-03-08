import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from registrations.models import UserRegistration

try:
    reg = UserRegistration.objects.create(
        name="Test Sender",
        email="testsender@example.com",
        phone="1234567890",
        registration_type="PARTICIPANT"
    )
    print("Created successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
