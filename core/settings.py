import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'unsafe-default-key')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*', 'ennovatex.up.railway.app'] # Add your actual domain here later (e.g. 'ennovatex.com')

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "whitenoise.runserver_nostatic", # Added for WhiteNoise
    # Local Apps
    "registrations",
    "payments",
    "referrals",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware", # Added for WhiteNoise
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

import dj_database_url

# Static and Media Roots for cPanel
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
# If a Railway volume is detected, use it. Otherwise, use a local data folder (cPanel)
if os.path.exists('/data'):
    DATA_ROOT = Path('/data')
else:
    # On cPanel, we'll use a 'data' folder in our app root
    DATA_ROOT = BASE_DIR / 'data'
    if not os.path.exists(DATA_ROOT):
        os.makedirs(DATA_ROOT, exist_ok=True)

# Database
# Use dj-database-url to parse the DATABASE_URL environment variable if it exists
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + str(DATA_ROOT / 'db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

MEDIA_ROOT = DATA_ROOT / 'media'

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# Static files storage using WhiteNoise for production
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# CSRF settings for new domain
CSRF_TRUSTED_ORIGINS = [
    "https://*.railway.app",
    "https://*.up.railway.app",
    "https://*.yournewdomain.com", # Placeholder: replace with your actual domain
]

# Security settings for production
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False') == 'True'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('mayur.kharat25@pccoepune.org')
EMAIL_HOST_PASSWORD = os.getenv('kejx cull awbl iudy')



# Registration settings
BASE_PARTICIPANT_FEE = 1
PCCOE_DOMAIN = "@pccoepune.org"

UNFOLD = {
    "SITE_TITLE": "Event Admin",
    "SITE_HEADER": "E-Cell Dashboard",
    "SITE_URL": "/",
    "COLORS": {
        "primary": {
            "50": "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "59 130 246",
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
            "950": "23 37 84",
        },
    },
    "TABS": [
        {
            "models": [
                "registrations.userregistration",
                "payments.paymentrecord",
                "referrals.referralcode",
            ],
            "items": [
                {
                    "title": "Registrations",
                    "link": "/admin/registrations/userregistration/",
                    "icon": "people",
                },
                {
                    "title": "Payments",
                    "link": "/admin/payments/paymentrecord/",
                    "icon": "payments",
                },
                 {
                    "title": "Referrals",
                    "link": "/admin/referrals/referralcode/",
                    "icon": "campaign",
                },
            ],
        },
    ],
}
