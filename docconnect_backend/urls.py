from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.core.admin_site import docconnect_admin
from apps.core.views import (
    home, network, jobs, availability, messaging, notifications, hospitals,
    post_availability, post_shift, send_message, mark_notifications_read,
    login_view, register_view, logout_view, settings_view, change_password_view,
)

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('network/', network, name='network'),
    path('jobs/', jobs, name='jobs'),
    path('availability/', availability, name='availability'),
    path('availability/post/', post_availability, name='post_availability'),
    path('availability/shift/', post_shift, name='post_shift'),
    path('messaging/', messaging, name='messaging'),
    path('messaging/send/', send_message, name='send_message'),
    path('notifications/', notifications, name='notifications'),
    path('notifications/read-all/', mark_notifications_read, name='mark_notifications_read'),
    path('hospitals/', hospitals, name='hospitals'),
    path('settings/', settings_view, name='settings'),
    path('change-password/', change_password_view, name='change_password'),
    path('admin/', docconnect_admin.urls),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
