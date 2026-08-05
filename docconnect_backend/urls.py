from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.core.admin_site import docconnect_admin
from apps.core.views import (
    home, network, jobs, availability, messaging, notifications, hospitals,
    post_availability, post_shift, send_message, mark_notifications_read, mark_notification_read,
    login_view, register_view, logout_view, settings_view, change_password_view,
    profile_view, profile_me_view, profile_edit_view,
    job_detail_view, apply_to_job_view, withdraw_job_view,
    my_applications_view, withdraw_application_view,
    hospital_detail_view, register_hospital_view,
    post_job_view, add_registration_view, request_shift_view,
    send_connection_request, respond_connection_view, withdraw_connection_view, my_connections_view,
    start_conversation, doctor_search_json,
    my_shift_requests_view, hospital_shift_requests_view,
    update_shift_request_view, doctor_respond_shift_view,
    hospital_staff_view, follow_hospital_view,
    upload_profile_photo, upload_cover_photo,
    upload_hospital_logo, hospital_applicants_view, hospital_jobs_view, my_availability_view,
    badge_counts, publish_job_view,
)

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),

    # Network
    path('network/', network, name='network'),
    path('network/requests/', my_connections_view, name='my_connections'),
    path('network/connections/<uuid:connection_id>/respond/', respond_connection_view, name='respond_connection'),

    # Jobs — literal paths first
    path('jobs/', jobs, name='jobs'),
    path('jobs/post/', post_job_view, name='post_job'),
    path('my-applications/', my_applications_view, name='my_applications'),
    path('my-applications/<uuid:application_id>/withdraw/', withdraw_application_view, name='withdraw_application'),
    path('jobs/<uuid:job_id>/', job_detail_view, name='job_detail'),
    path('jobs/<uuid:job_id>/apply/', apply_to_job_view, name='apply_job'),
    path('jobs/<uuid:job_id>/withdraw/', withdraw_job_view, name='withdraw_job'),
    path('jobs/<uuid:job_id>/applicants/', hospital_applicants_view, name='hospital_applicants'),

    # Availability
    path('availability/', availability, name='availability'),
    path('availability/post/', post_availability, name='post_availability'),
    path('availability/shift/', post_shift, name='post_shift'),
    path('availability/mine/', my_availability_view, name='my_availability'),
    path('availability/shift/<uuid:requirement_id>/request/', request_shift_view, name='request_shift'),

    # Messaging
    path('messaging/', messaging, name='messaging'),
    path('messaging/send/', send_message, name='send_message'),

    # Notifications
    path('notifications/', notifications, name='notifications'),
    path('notifications/read-all/', mark_notifications_read, name='mark_notifications_read'),
    path('notifications/read/', mark_notification_read, name='mark_notification_read'),

    # Hospitals — literal paths before uuid
    path('hospitals/', hospitals, name='hospitals'),
    path('hospitals/register/', register_hospital_view, name='register_hospital'),
    path('hospitals/me/staff/', hospital_staff_view, name='hospital_staff'),
    path('hospitals/me/jobs/', hospital_jobs_view, name='hospital_jobs'),
    path('hospitals/me/jobs/<uuid:job_id>/publish/', publish_job_view, name='publish_job'),
    path('hospitals/<uuid:hospital_id>/', hospital_detail_view, name='hospital_detail'),
    path('hospitals/<uuid:hospital_id>/follow/', follow_hospital_view, name='follow_hospital'),
    path('hospitals/<uuid:hospital_id>/logo/', upload_hospital_logo, name='upload_hospital_logo'),

    # Profile — literal paths before uuid
    path('profile/me/', profile_me_view, name='profile_me'),
    path('profile/me/edit/', profile_edit_view, name='profile_edit'),
    path('profile/me/photo/', upload_profile_photo, name='upload_profile_photo'),
    path('profile/me/cover/', upload_cover_photo, name='upload_cover_photo'),
    path('profile/me/registrations/add/', add_registration_view, name='add_registration'),
    path('profile/<uuid:doctor_id>/', profile_view, name='profile'),
    path('profile/<uuid:doctor_id>/connect/', send_connection_request, name='connect_doctor'),
    path('profile/<uuid:doctor_id>/disconnect/', withdraw_connection_view, name='disconnect_doctor'),
    path('profile/<uuid:doctor_id>/message/', start_conversation, name='start_conversation'),

    # Doctors
    path('doctors/search-json/', doctor_search_json, name='doctor_search_json'),

    # Shifts
    path('shifts/mine/', my_shift_requests_view, name='my_shift_requests'),
    path('shifts/mine/<uuid:request_id>/respond/', doctor_respond_shift_view, name='doctor_respond_shift'),
    path('shifts/hospital/', hospital_shift_requests_view, name='hospital_shift_requests'),
    path('shifts/hospital/<uuid:request_id>/update/', update_shift_request_view, name='update_shift_request'),

    # Settings
    path('settings/', settings_view, name='settings'),
    path('change-password/', change_password_view, name='change_password'),

    # API
    path('api/badge-counts/', badge_counts, name='badge_counts'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('admin/', docconnect_admin.urls),
]
