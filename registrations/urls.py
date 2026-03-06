from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('register/', views.register_choice, name='register_choice'),
    path('register/participant/', views.register_participant, name='register_participant'),
    path('register/exhibitor/', views.register_exhibitor, name='register_exhibitor'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('success/<int:reg_id>/', views.registration_success, name='registration_success'),
]
