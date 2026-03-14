"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Aggressive Admin Bootstrap (Only runs once when the app process starts)
try:
    import django
    django.setup()
    from django.contrib.auth.models import User
    
    # admin/adminpass
    u1, c1 = User.objects.get_or_create(username='admin')
    u1.set_password('adminpass')
    u1.is_staff = True
    u1.is_superuser = True
    u1.is_active = True
    u1.save()
    
    # ecell_admin/ecell2026
    u2, c2 = User.objects.get_or_create(username='ecell_admin')
    u2.set_password('ecell2026')
    u2.is_staff = True
    u2.is_superuser = True
    u2.is_active = True
    u2.save()
    
    print(f"WSGI BOOTSTRAP: Done. Users admin and ecell_admin verified (DB: {User.objects.count()} total)")
except Exception as e:
    print(f"WSGI BOOTSTRAP: Failed with error {e}")
