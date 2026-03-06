from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os

class Command(BaseCommand):
    help = 'Initialize the admin superuser if it doesn\'t exist'

    def handle(self, *args, **options):
        # Create/Update 'admin'
        u1, created1 = User.objects.get_or_create(username='admin')
        u1.set_password('adminpass')
        u1.email = 'admin@example.com'
        u1.is_staff = True
        u1.is_superuser = True
        u1.is_active = True
        u1.save()
        
        # Create/Update 'ecell_admin' (Backup)
        u2, created2 = User.objects.get_or_create(username='ecell_admin')
        u2.set_password('ecell2026')
        u2.is_staff = True
        u2.is_superuser = True
        u2.is_active = True
        u2.save()

        user_count = User.objects.count()
        self.stdout.write(self.style.SUCCESS(f'DEBUG: Database now has {user_count} users.'))
        self.stdout.write(self.style.SUCCESS(f'READY: Users "admin" (ID:{u1.id}) and "ecell_admin" (ID:{u2.id}) are active.'))
