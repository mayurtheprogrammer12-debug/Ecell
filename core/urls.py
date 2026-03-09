from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.views.static import serve
from django.urls import re_path

urlpatterns = [
    path("ennovate-portal-26/", admin.site.urls),
    path("", include("registrations.urls")),
    path("dashboard/", include("dashboard.urls")),
]

# Serve media files (screenshots) regardless of DEBUG status for reliability on cPanel
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
