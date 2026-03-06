from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os

class Command(BaseCommand):
    help = 'Initialize the admin superuser if it doesn\'t exist'

    def handle(self, *args, **options):
        username = os.getenv('ADMIN_USERNAME', 'admin')
        password = os.getenv('ADMIN_PASSWORD', 'adminpass')
        email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        
        user_query = User.objects.filter(username=username)
        if not user_query.exists():
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser "{username}"'))
        else:
            user = user_query.first()
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" already exists. Password has been reset to ensure access.'))
