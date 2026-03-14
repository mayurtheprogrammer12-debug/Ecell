from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('register/', views.register_choice, name='register_choice'),
    path('register/participant/', views.register_participant, name='register_participant'),
    path('register/exhibitor/', views.register_exhibitor, name='register_exhibitor'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('success/<int:reg_id>/', views.registration_success, name='registration_success'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('round1/submit/', views.round1_submit, name='round1_submit'),
    path('round2/', views.round2_view, name='round2'),
    path('round2/search-members/', views.search_team_members, name='search_team_members'),
    path('round2/manage-team/', views.manage_team, name='manage_team'),
    path('round2/add-member/', views.add_team_member, name='add_team_member'),
    path('round2/remove-member/', views.remove_team_member, name='remove_team_member'),
    path('round2/confirm-team/', views.confirm_team, name='confirm_team'),
    path('round3/upload-ppt/', views.upload_round3_ppt, name='upload_round3_ppt'),
    path('attendance/checkin/<uuid:session_id>/', views.attendance_checkin, name='attendance_checkin'),
    path('attendance/session/<uuid:session_id>/qr/', views.show_session_qr, name='show_session_qr'),
]
