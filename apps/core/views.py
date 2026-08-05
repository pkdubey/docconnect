import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q as models_Q


# ── Helpers ───────────────────────────────────────────────────

def _get_initials(name):
    parts = name.strip().split()
    return (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()

AVATAR_COLORS = ['#0a66c2','#e16b00','#057642','#cc1016','#915907','#6b46c1','#0891b2','#be185d']

def _color(pk):
    return AVATAR_COLORS[hash(str(pk)) % len(AVATAR_COLORS)]


# ── Auth Views ───────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    error = None
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, phone=phone, password=password)
        if user is not None:
            login(request, user)
            return redirect(request.GET.get('next', '/'))
        error = 'Invalid phone number or password.'
    return render(request, 'login.html', {'error': error})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    error = None
    if request.method == 'POST':
        from apps.accounts.models import User
        from apps.doctors.models import DoctorProfile
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        confirm = request.POST.get('confirm_password', '').strip()
        user_type = request.POST.get('user_type', 'DOCTOR')
        email = request.POST.get('email', '').strip() or None
        if not first_name or not last_name:
            error = 'First name and last name are required.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif User.objects.filter(phone=phone).exists():
            error = 'An account with this phone number already exists.'
        else:
            try:
                user = User.objects.create_user(phone=phone, user_type=user_type, password=password, email=email)
                user.metadata = {'first_name': first_name, 'last_name': last_name}
                user.save(update_fields=['metadata'])
                if user_type == 'DOCTOR':
                    DoctorProfile.objects.create(user=user, first_name=first_name, last_name=last_name)
                login(request, user)
                return redirect('/')
            except Exception as e:
                error = str(e)
    return render(request, 'register.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('/login/')


# ── Views ─────────────────────────────────────────────────────

@login_required
def home(request):
    stats = {'doctors': 0, 'hospitals': 0, 'jobs': 0}
    urgent_jobs = []
    suggested_doctors = []
    try:
        from apps.doctors.models import DoctorProfile
        from apps.hospitals.models import Hospital
        from apps.jobs.models import JobPost
        stats['doctors'] = DoctorProfile.objects.filter(verification_status='VERIFIED').count()
        stats['hospitals'] = Hospital.objects.filter(verification_status='VERIFIED').count()
        stats['jobs'] = JobPost.objects.filter(status='PUBLISHED').count()
        urgent_jobs = list(JobPost.objects.filter(status='PUBLISHED', is_urgent=True)
                           .select_related('hospital').order_by('-published_at')[:3])
        suggested_doctors_raw = list(DoctorProfile.objects.filter(verification_status='VERIFIED')
                                 .exclude(user=request.user)
                                 .order_by('-created_at')[:4])
        # Build connection state map
        conn_map = {}
        if request.user.user_type == 'DOCTOR':
            try:
                from apps.doctors.models import Connection
                from django.db.models import Q as _Q
                my_profile = request.user.doctor_profile
                doc_ids = [d.id for d in suggested_doctors_raw]
                for c in Connection.objects.filter(
                    _Q(sender=my_profile, receiver__in=doc_ids) |
                    _Q(receiver=my_profile, sender__in=doc_ids)
                ):
                    other_id = c.receiver_id if c.sender_id == my_profile.id else c.sender_id
                    conn_map[str(other_id)] = {
                        'status': c.status,
                        'id': str(c.id),
                        'direction': 'sent' if c.sender_id == my_profile.id else 'received',
                    }
            except Exception:
                pass
        suggested_doctors = [{
            'id': str(d.id),
            'color': _color(d.id),
            'initials': _get_initials(d.full_name),
            'full_name': d.full_name,
            'headline': d.headline,
            'professional_location': d.professional_location,
            'photo': d.photo_base64 or '',
            'conn_status': conn_map.get(str(d.id), {}).get('status'),
            'conn_id': conn_map.get(str(d.id), {}).get('id'),
            'conn_direction': conn_map.get(str(d.id), {}).get('direction'),
        } for d in suggested_doctors_raw]
    except Exception:
        pass
    return render(request, 'home.html', {
        'stats': stats,
        'urgent_jobs': urgent_jobs,
        'suggested_doctors': suggested_doctors,
    })


@login_required
def network(request):
    from apps.doctors.models import DoctorProfile, Connection
    search = request.GET.get('q', '')
    spec_filter = request.GET.get('spec', '')
    city_filter = request.GET.get('city', '')
    exp_filter = request.GET.get('exp', '')
    verified_only = request.GET.get('verified', '')

    qs = DoctorProfile.objects.select_related('user').exclude(user=request.user).order_by('-created_at')
    if search:
        qs = qs.filter(
            models_Q(first_name__icontains=search) | models_Q(last_name__icontains=search) | models_Q(headline__icontains=search)
        )
    if city_filter:
        qs = qs.filter(professional_location__city__icontains=city_filter)
    if verified_only:
        qs = qs.filter(verification_status='VERIFIED')
    if exp_filter:
        qs = qs.filter(experience_years__gte=exp_filter)

    doctors_raw = list(qs[:30])

    # Build connection state map for current user
    conn_map = {}  # doctor_id -> {'status', 'id', 'direction'}
    if request.user.user_type == 'DOCTOR':
        try:
            my_profile = request.user.doctor_profile
            doctor_ids = [d.id for d in doctors_raw]
            conns = Connection.objects.filter(
                models_Q(sender=my_profile, receiver__in=doctor_ids) |
                models_Q(receiver=my_profile, sender__in=doctor_ids)
            )
            for c in conns:
                other_id = c.receiver_id if c.sender_id == my_profile.id else c.sender_id
                conn_map[str(other_id)] = {
                    'status': c.status,
                    'id': str(c.id),
                    'direction': 'sent' if c.sender_id == my_profile.id else 'received',
                }
        except Exception:
            pass

    doctors = []
    for d in doctors_raw:
        conn_info = conn_map.get(str(d.id), {})
        doctors.append({
            'obj': d,
            'color': _color(d.id),
            'initials': _get_initials(d.full_name),
            'full_name': d.full_name,
            'headline': d.headline,
            'experience_years': d.experience_years,
            'professional_location': d.professional_location,
            'verification_status': d.verification_status,
            'photo': d.photo_base64 or '',
            'conn_status': conn_info.get('status'),
            'conn_id': conn_info.get('id'),
            'conn_direction': conn_info.get('direction'),
        })

    # Pending incoming requests count for badge
    pending_count = 0
    if request.user.user_type == 'DOCTOR':
        try:
            pending_count = Connection.objects.filter(
                receiver=request.user.doctor_profile, status='PENDING'
            ).count()
        except Exception:
            pass

    return render(request, 'network.html', {
        'doctors': doctors,
        'search': search,
        'spec_filter': spec_filter,
        'city_filter': city_filter,
        'exp_filter': exp_filter,
        'verified_only': verified_only,
        'total': len(doctors),
        'pending_count': pending_count,
    })


@login_required
def jobs(request):
    from apps.jobs.models import JobPost
    job_type = request.GET.get('type', '')
    city = request.GET.get('city', '')
    urgent = request.GET.get('urgent', '')
    search = request.GET.get('q', '')

    qs = JobPost.objects.filter(status='PUBLISHED').select_related('hospital').order_by('-published_at', '-created_at')
    if job_type:
        qs = qs.filter(job_type=job_type)
    if city:
        qs = qs.filter(location__city__icontains=city)
    if urgent:
        qs = qs.filter(is_urgent=True)
    if search:
        from django.db.models import Q
        qs = qs.filter(Q(title__icontains=search) | Q(hospital__name__icontains=search))

    jobs_list = list(qs[:40])

    JOB_TYPES = [
        ('FULL_TIME', 'Full Time'), ('PART_TIME', 'Part Time'),
        ('LOCUM', 'Locum'), ('VISITING', 'Visiting'), ('CONTRACT', 'Contract'),
    ]
    return render(request, 'jobs.html', {
        'jobs': jobs_list,
        'job_types': JOB_TYPES,
        'total': len(jobs_list),
        'filter_type': job_type,
        'filter_city': city,
        'filter_urgent': urgent,
        'search': search,
    })


@login_required
def availability(request):
    from apps.availability.models import DoctorAvailability
    from apps.shifts.models import ShiftRequirement

    avail_type = request.GET.get('type', '')
    city = request.GET.get('city', '')
    urgency = request.GET.get('urgency', '')

    avail_qs = DoctorAvailability.objects.filter(is_active=True).select_related('doctor').prefetch_related('slots').order_by('-created_at')
    if avail_type:
        avail_qs = avail_qs.filter(availability_type=avail_type)
    if city:
        avail_qs = avail_qs.filter(preferred_location__city__icontains=city)

    shift_qs = ShiftRequirement.objects.filter(status='OPEN').select_related('hospital').order_by('-created_at')
    if urgency:
        shift_qs = shift_qs.filter(urgency=urgency)
    if city:
        shift_qs = shift_qs.filter(location__city__icontains=city)

    availabilities_raw = list(avail_qs[:20])
    availabilities = []
    for a in availabilities_raw:
        availabilities.append({
            'obj': a,
            'color': _color(a.doctor.id),
            'initials': _get_initials(a.doctor.full_name),
            'doctor_name': a.doctor.full_name,
            'availability_type_display': a.get_availability_type_display(),
            'available_from': a.available_from,
            'available_until': a.available_until,
            'preferred_location': a.preferred_location or {},
            'minimum_compensation': a.minimum_compensation,
            'preferred_radius_km': a.preferred_radius_km,
            'notes': a.notes,
            'slots': list(a.slots.all()[:5]),
        })

    shift_requirements = list(shift_qs[:20])

    AVAIL_TYPES = [('LOCUM','Locum'),('VISITING','Visiting'),('TEMPORARY','Temporary'),('PART_TIME','Part Time')]
    URGENCIES = [('NORMAL','Normal'),('URGENT','Urgent'),('IMMEDIATE','Immediate')]

    return render(request, 'availability.html', {
        'availabilities': availabilities,
        'shift_requirements': shift_requirements,
        'avail_types': AVAIL_TYPES,
        'urgencies': URGENCIES,
        'filter_type': avail_type,
        'filter_city': city,
        'filter_urgency': urgency,
    })


@login_required
@require_POST
def post_availability(request):
    try:
        from apps.availability.models import DoctorAvailability
        doctor = request.user.doctor_profile
        data = request.POST
        DoctorAvailability.objects.create(
            doctor=doctor,
            availability_type=data.get('availability_type', 'LOCUM'),
            available_from=data.get('available_from'),
            available_until=data.get('available_until'),
            preferred_location={'city': data.get('city', ''), 'state': data.get('state', '')},
            preferred_radius_km=data.get('radius_km') or None,
            minimum_compensation=data.get('min_compensation') or None,
            notes=data.get('notes', ''),
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def post_shift(request):
    try:
        from apps.shifts.models import ShiftRequirement
        from apps.hospitals.models import HospitalUser
        import uuid
        hospital_user = HospitalUser.objects.get(user=request.user)
        data = request.POST
        from apps.core.models import Specialization, Qualification
        specialty_name = data.get('specialty', '')
        spec = Specialization.objects.filter(name__icontains=specialty_name).first() if specialty_name else Specialization.objects.first()
        qual = Qualification.objects.filter(name='MBBS').first() or Qualification.objects.first()
        ShiftRequirement.objects.create(
            hospital=hospital_user.hospital,
            specialty_id=spec.id if spec else uuid.uuid4(),
            qualification_ids=[str(qual.id)] if qual else [],
            requirement_date=data.get('requirement_date'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            location={'city': data.get('city', ''), 'state': data.get('state', '')},
            compensation=data.get('compensation', 0),
            doctors_required=data.get('doctors_required', 1),
            urgency=data.get('urgency', 'NORMAL'),
            notes=data.get('notes', ''),
            created_by=request.user,
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def messaging(request):
    conversations = []
    active_conv = None
    active_messages = []
    active_conv_doctor_id = None

    if request.user.is_authenticated:
        try:
            from apps.messaging.models import Conversation, ConversationParticipant, Message
            participant_qs = ConversationParticipant.objects.filter(
                user=request.user, is_active=True
            ).select_related('conversation').order_by('-conversation__updated_at')

            for p in participant_qs[:20]:
                conv = p.conversation
                last_msg = conv.messages.order_by('-created_at').first()
                other = conv.participants.exclude(user=request.user).select_related('user').first()
                name = other.user.phone if other else conv.title or 'Group'
                try:
                    if other and hasattr(other.user, 'doctor_profile'):
                        dp = other.user.doctor_profile
                        name = f"Dr. {dp.full_name}"
                except Exception:
                    pass
                photo = ''
                try:
                    if other and hasattr(other.user, 'doctor_profile'):
                        photo = other.user.doctor_profile.photo_base64 or ''
                except Exception:
                    pass
                conversations.append({
                    'id': str(conv.id),
                    'name': name,
                    'initials': _get_initials(name),
                    'color': _color(conv.id),
                    'photo': photo,
                    'last_msg': last_msg.content[:60] if last_msg and last_msg.content else '',
                    'time': last_msg.created_at.strftime('%I:%M %p') if last_msg else '',
                    'unread': p.last_read_at is None or (last_msg and last_msg.created_at > p.last_read_at),
                })

            conv_id = request.GET.get('conv')
            if conv_id and conversations:
                try:
                    active_conv = next((c for c in conversations if c['id'] == conv_id), conversations[0])
                    from apps.messaging.models import Message
                    active_messages = list(Message.objects.filter(
                        conversation_id=conv_id
                    ).select_related('sender').order_by('created_at')[:100])
                    # Resolve doctor profile id for Profile button
                    other_p = ConversationParticipant.objects.filter(
                        conversation_id=conv_id
                    ).exclude(user=request.user).select_related('user').first()
                    if other_p:
                        try:
                            active_conv_doctor_id = str(other_p.user.doctor_profile.id)
                        except Exception:
                            pass
                except Exception:
                    pass
            elif conversations:
                active_conv = conversations[0]
        except Exception:
            pass

    return render(request, 'messaging.html', {
        'conversations': conversations,
        'active_conv': active_conv,
        'active_messages': active_messages,
        'active_conv_doctor_id': active_conv_doctor_id,
    })


@login_required
@require_POST
def send_message(request):
    try:
        from apps.messaging.models import Message, ConversationParticipant
        data = json.loads(request.body)
        conv_id = data.get('conversation_id')
        content = data.get('content', '').strip()
        if not content:
            return JsonResponse({'error': 'Empty message'}, status=400)
        # verify user is participant
        ConversationParticipant.objects.get(conversation_id=conv_id, user=request.user)
        msg = Message.objects.create(
            conversation_id=conv_id,
            sender=request.user,
            content=content,
            message_type='TEXT',
        )
        # update conversation updated_at
        from apps.messaging.models import Conversation
        Conversation.objects.filter(id=conv_id).update(updated_at=timezone.now())
        return JsonResponse({
            'id': str(msg.id),
            'content': msg.content,
            'created_at': msg.created_at.strftime('%I:%M %p'),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def notifications(request):
    notifs = []
    unread_count = 0
    if request.user.is_authenticated:
        try:
            from apps.notifications.models import Notification
            notifs = list(Notification.objects.filter(user=request.user).order_by('-created_at')[:30])
            unread_count = sum(1 for n in notifs if not n.is_read)
        except Exception:
            pass
    return render(request, 'notifications.html', {
        'notifications': notifs,
        'unread_count': unread_count,
    })


@login_required
@require_POST
def mark_notifications_read(request):
    try:
        from apps.notifications.models import Notification
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def mark_notification_read(request):
    try:
        import json as _json
        from apps.notifications.models import Notification
        data = _json.loads(request.body)
        Notification.objects.filter(id=data.get('id'), user=request.user).update(
            is_read=True, read_at=timezone.now()
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def change_password_view(request):
    from django.contrib import messages as dj_messages
    if request.method == 'POST':
        current = request.POST.get('current_password', '')
        new_pw = request.POST.get('new_password', '')
        confirm = request.POST.get('confirm_password', '')
        if not request.user.check_password(current):
            dj_messages.error(request, 'Current password is incorrect.')
        elif new_pw != confirm:
            dj_messages.error(request, 'New passwords do not match.')
        elif len(new_pw) < 8:
            dj_messages.error(request, 'Password must be at least 8 characters.')
        else:
            request.user.set_password(new_pw)
            request.user.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            dj_messages.success(request, 'Password updated successfully.')
            return redirect('/settings/?tab=security')
    return render(request, 'change_password.html')


@login_required
def settings_view(request):
    from django.contrib import messages as dj_messages
    active_tab = request.GET.get('tab', 'account')

    SECTIONS = [
        {'key': 'account', 'label': 'Account', 'icon': '👤'},
        {'key': 'profile', 'label': 'Visibility', 'icon': '👁️'},
        {'key': 'notifications', 'label': 'Notifications', 'icon': '🔔'},
        {'key': 'security', 'label': 'Sign in & Security', 'icon': '🔒'},
    ]

    NOTIF_PREFS = [
        {'key': 'notif_jobs', 'label': 'Job Alerts', 'desc': 'New jobs matching your profile', 'checked': True},
        {'key': 'notif_connections', 'label': 'Connection Requests', 'desc': 'When someone wants to connect', 'checked': True},
        {'key': 'notif_messages', 'label': 'Messages', 'desc': 'New messages in your inbox', 'checked': True},
        {'key': 'notif_shifts', 'label': 'Shift Requests', 'desc': 'Urgent shift requirements near you', 'checked': False},
    ]

    from apps.accounts.models import RefreshSession
    session_count = RefreshSession.objects.filter(user=request.user, revoked_at__isnull=True).count()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'account':
            email = request.POST.get('email', '').strip() or None
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            try:
                request.user.email = email
                if first_name or last_name:
                    meta = request.user.metadata or {}
                    if first_name:
                        meta['first_name'] = first_name
                    if last_name:
                        meta['last_name'] = last_name
                    request.user.metadata = meta
                    request.user.save(update_fields=['email', 'metadata'])
                else:
                    request.user.save(update_fields=['email'])
                dj_messages.success(request, 'Account updated successfully.')
            except Exception as e:
                dj_messages.error(request, str(e))

        elif form_type == 'profile' and request.user.user_type == 'DOCTOR':
            try:
                dp = request.user.doctor_profile
                dp.profile_visibility = request.POST.get('profile_visibility', dp.profile_visibility)
                dp.career_visibility = request.POST.get('career_visibility', dp.career_visibility)
                dp.open_to_opportunities = 'open_to_opportunities' in request.POST
                dp.save(update_fields=['profile_visibility', 'career_visibility', 'open_to_opportunities'])
                dj_messages.success(request, 'Visibility settings saved.')
            except Exception as e:
                dj_messages.error(request, str(e))

        elif form_type == 'notifications':
            dj_messages.success(request, 'Notification preferences saved.')

        elif form_type == 'revoke_sessions':
            RefreshSession.objects.filter(user=request.user).update(revoked_at=timezone.now())
            dj_messages.success(request, 'All other sessions signed out.')

        elif form_type == 'deactivate':
            request.user.status = 'INACTIVE'
            request.user.save(update_fields=['status'])
            logout(request)
            return redirect('/login/')

        return redirect(f'/settings/?tab={active_tab}')

    return render(request, 'settings.html', {
        'sections': SECTIONS,
        'active_tab': active_tab,
        'notif_prefs': NOTIF_PREFS,
        'session_count': session_count,
    })


@login_required
def profile_view(request, doctor_id):
    from apps.doctors.models import DoctorProfile
    try:
        doctor = DoctorProfile.objects.prefetch_related(
            'qualifications', 'experiences', 'registrations'
        ).get(id=doctor_id)
    except DoctorProfile.DoesNotExist:
        from django.http import Http404
        raise Http404

    if doctor.profile_visibility == 'CONNECTIONS_ONLY' and doctor.user != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('This profile is private.')
    if doctor.profile_visibility == 'DOCTORS_ONLY' and request.user.user_type != 'DOCTOR' and doctor.user != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Visible to doctors only.')

    is_own_profile = (doctor.user == request.user)
    from apps.core.models import Specialization
    from apps.doctors.models import Connection
    spec_name = ''
    if doctor.primary_specialization_id:
        spec = Specialization.objects.filter(id=doctor.primary_specialization_id).first()
        spec_name = spec.name if spec else ''
    interest_names = []
    if doctor.clinical_interests:
        interest_names = list(Specialization.objects.filter(
            id__in=doctor.clinical_interests
        ).values_list('name', flat=True))

    # Connection state
    conn_status = None  # None = no relation
    conn_id = None
    conn_direction = None  # 'sent' or 'received'
    connection_count = 0
    if not is_own_profile and request.user.user_type == 'DOCTOR':
        try:
            my_profile = request.user.doctor_profile
            conn = Connection.objects.filter(
                sender=my_profile, receiver=doctor
            ).first() or Connection.objects.filter(
                sender=doctor, receiver=my_profile
            ).first()
            if conn:
                conn_status = conn.status
                conn_id = str(conn.id)
                conn_direction = 'sent' if conn.sender == my_profile else 'received'
        except Exception:
            pass
    try:
        connection_count = Connection.objects.filter(
            status='ACCEPTED'
        ).filter(models_Q(sender=doctor) | models_Q(receiver=doctor)).count()
    except Exception:
        pass

    return render(request, 'profile.html', {
        'doctor': doctor,
        'experiences': doctor.experiences.order_by('-start_date'),
        'qualifications': doctor.qualifications.order_by('-year'),
        'registrations': doctor.registrations.all(),
        'is_own_profile': is_own_profile,
        'color': _color(doctor.id),
        'initials': _get_initials(doctor.full_name),
        'connection_count': connection_count,
        'spec_name': spec_name,
        'interest_names': interest_names,
        'conn_status': conn_status,
        'conn_id': conn_id,
        'conn_direction': conn_direction,
    })


@login_required
def job_detail_view(request, job_id):
    from apps.jobs.models import JobPost, JobApplication
    try:
        job = JobPost.objects.select_related('hospital').get(id=job_id, status='PUBLISHED')
    except JobPost.DoesNotExist:
        from django.http import Http404
        raise Http404

    already_applied = False
    application_status = None
    if request.user.is_authenticated and request.user.user_type == 'DOCTOR':
        try:
            app = JobApplication.objects.get(job=job, doctor=request.user.doctor_profile)
            already_applied = True
            application_status = app.status
        except (JobApplication.DoesNotExist, Exception):
            pass

    if request.method == 'POST' and 'apply' in request.path:
        return apply_to_job_view(request, job_id)

    return render(request, 'job_detail.html', {
        'job': job,
        'already_applied': already_applied,
        'application_status': application_status,
    })


@login_required
def apply_to_job_view(request, job_id):
    from apps.jobs.models import JobPost, JobApplication
    from django.contrib import messages as dj_messages
    if request.method != 'POST':
        return redirect(f'/jobs/{job_id}/')
    if request.user.user_type != 'DOCTOR':
        dj_messages.error(request, 'Only doctors can apply.')
        return redirect(f'/jobs/{job_id}/')
    try:
        job = JobPost.objects.get(id=job_id, status='PUBLISHED')
        doctor = request.user.doctor_profile
    except Exception as e:
        dj_messages.error(request, str(e))
        return redirect(f'/jobs/{job_id}/')
    if JobApplication.objects.filter(job=job, doctor=doctor).exists():
        dj_messages.warning(request, 'You have already applied for this job.')
    else:
        app = JobApplication.objects.create(job=job, doctor=doctor)
        from apps.jobs.models import ApplicationHistory
        ApplicationHistory.objects.create(
            application=app, from_status=None, to_status='APPLIED', changed_by=request.user
        )
        dj_messages.success(request, f'Applied to {job.title} successfully!')
    return redirect(f'/jobs/{job_id}/')


@login_required
def withdraw_job_view(request, job_id):
    from apps.jobs.models import JobApplication
    from django.contrib import messages as dj_messages
    if request.method == 'POST':
        try:
            app = JobApplication.objects.get(job_id=job_id, doctor=request.user.doctor_profile)
            if app.status not in ['HIRED', 'REJECTED', 'WITHDRAWN']:
                app.status = 'WITHDRAWN'
                app.save(update_fields=['status', 'updated_at'])
                dj_messages.success(request, 'Application withdrawn.')
        except Exception:
            pass
    return redirect(request.META.get('HTTP_REFERER', '/my-applications/'))


@login_required
def my_applications_view(request):
    if request.user.user_type != 'DOCTOR':
        return redirect('/')
    from apps.jobs.models import JobApplication
    status_filter = request.GET.get('status', '')
    try:
        qs = JobApplication.objects.filter(
            doctor=request.user.doctor_profile
        ).select_related('job', 'job__hospital').prefetch_related('history').order_by('-applied_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        total = JobApplication.objects.filter(doctor=request.user.doctor_profile).count()
    except Exception:
        qs = []
        total = 0
    return render(request, 'my_applications.html', {
        'applications': qs,
        'status_filter': status_filter,
        'total': total,
    })


@login_required
def withdraw_application_view(request, application_id):
    from apps.jobs.models import JobApplication
    from django.contrib import messages as dj_messages
    if request.method == 'POST':
        try:
            app = JobApplication.objects.get(id=application_id, doctor=request.user.doctor_profile)
            if app.status not in ['HIRED', 'REJECTED', 'WITHDRAWN']:
                app.status = 'WITHDRAWN'
                app.save(update_fields=['status', 'updated_at'])
                dj_messages.success(request, 'Application withdrawn.')
        except Exception:
            pass
    return redirect('/my-applications/')


@login_required
@require_POST
def upload_profile_photo(request):
    import base64
    try:
        dp = request.user.doctor_profile
        f = request.FILES.get('photo')
        if not f:
            return JsonResponse({'error': 'No file'}, status=400)
        if f.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'Max 5MB'}, status=400)
        dp.photo_base64 = 'data:{};base64,{}'.format(f.content_type, base64.b64encode(f.read()).decode())
        dp.save(update_fields=['photo_base64'])
        return JsonResponse({'url': dp.photo_base64})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def upload_cover_photo(request):
    import base64
    try:
        dp = request.user.doctor_profile
        f = request.FILES.get('cover')
        if not f:
            return JsonResponse({'error': 'No file'}, status=400)
        if f.size > 8 * 1024 * 1024:
            return JsonResponse({'error': 'Max 8MB'}, status=400)
        dp.cover_base64 = 'data:{};base64,{}'.format(f.content_type, base64.b64encode(f.read()).decode())
        dp.save(update_fields=['cover_base64'])
        return JsonResponse({'url': dp.cover_base64})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def profile_me_view(request):
    if request.user.user_type != 'DOCTOR':
        return redirect('/')
    try:
        dp = request.user.doctor_profile
        return redirect(f'/profile/{dp.id}/')
    except Exception:
        return redirect('/register/')


@login_required
def profile_edit_view(request):
    if request.user.user_type != 'DOCTOR':
        return redirect('/')
    from django.contrib import messages as dj_messages
    try:
        dp = request.user.doctor_profile
    except Exception:
        return redirect('/')
    from apps.core.models import Specialization
    specializations = list(Specialization.objects.filter(is_active=True).order_by('name'))
    if request.method == 'POST':
        form_type = request.POST.get('form_type', '')
        try:
            if form_type == 'qualification':
                from apps.doctors.models import DoctorQualification
                DoctorQualification.objects.create(
                    doctor=dp,
                    degree=request.POST.get('degree', '').strip(),
                    institution=request.POST.get('institution', '').strip(),
                    year=int(request.POST.get('year', 0)),
                    specialization=request.POST.get('specialization', '').strip() or None,
                )
                dj_messages.success(request, 'Qualification added.')
                return redirect('/profile/me/edit/')
            elif form_type == 'experience':
                from apps.doctors.models import DoctorExperience
                end_date = request.POST.get('end_date', '').strip() or None
                DoctorExperience.objects.create(
                    doctor=dp,
                    role=request.POST.get('role', '').strip(),
                    hospital_name=request.POST.get('hospital_name', '').strip(),
                    location=request.POST.get('location', '').strip() or None,
                    start_date=request.POST.get('start_date'),
                    end_date=end_date,
                    is_current='is_current' in request.POST,
                    description=request.POST.get('description', '').strip() or None,
                )
                dj_messages.success(request, 'Experience added.')
                return redirect('/profile/me/edit/')
            elif form_type == 'delete_qual':
                from apps.doctors.models import DoctorQualification
                DoctorQualification.objects.filter(id=request.POST.get('item_id'), doctor=dp).delete()
                dj_messages.success(request, 'Qualification removed.')
                return redirect('/profile/me/edit/')
            elif form_type == 'delete_exp':
                from apps.doctors.models import DoctorExperience
                DoctorExperience.objects.filter(id=request.POST.get('item_id'), doctor=dp).delete()
                dj_messages.success(request, 'Experience removed.')
                return redirect('/profile/me/edit/')
            else:
                dp.first_name = request.POST.get('first_name', dp.first_name).strip()
                dp.last_name = request.POST.get('last_name', dp.last_name).strip()
                dp.headline = request.POST.get('headline', '').strip() or None
                dp.about = request.POST.get('about', '').strip() or None
                exp = request.POST.get('experience_years', '').strip()
                dp.experience_years = float(exp) if exp else dp.experience_years
                spec_id = request.POST.get('primary_specialization_id', '').strip()
                dp.primary_specialization_id = spec_id if spec_id else None
                city = request.POST.get('city', '').strip()
                state = request.POST.get('state', '').strip()
                if city or state:
                    dp.professional_location = {
                        'city': city, 'state': state,
                        'address': request.POST.get('address', '').strip(),
                        'pincode': request.POST.get('pincode', '').strip(),
                    }
                dp.open_to_opportunities = 'open_to_opportunities' in request.POST
                dp.save(update_fields=[
                    'first_name', 'last_name', 'headline', 'about',
                    'experience_years', 'primary_specialization_id',
                    'professional_location', 'open_to_opportunities', 'updated_at',
                ])
                dj_messages.success(request, 'Profile updated successfully.')
                return redirect(f'/profile/{dp.id}/')
        except Exception as e:
            dj_messages.error(request, str(e))
    return render(request, 'profile_edit.html', {
        'doctor': dp,
        'specializations': specializations,
        'color': _color(dp.id),
        'initials': _get_initials(dp.full_name),
        'experiences': dp.experiences.order_by('-start_date'),
        'qualifications': dp.qualifications.order_by('-year'),
    })


@login_required
def add_registration_view(request):
    if request.user.user_type != 'DOCTOR':
        return redirect('/')
    from django.contrib import messages as dj_messages
    from apps.core.models import Council
    councils = list(Council.objects.filter(is_active=True).order_by('name'))
    if request.method == 'POST':
        try:
            from apps.doctors.models import DoctorRegistration
            dp = request.user.doctor_profile
            council_id = request.POST.get('council_id', '').strip()
            reg_number = request.POST.get('registration_number', '').strip()
            reg_year = int(request.POST.get('registration_year', 0))
            if not council_id or not reg_number or not reg_year:
                dj_messages.error(request, 'All fields are required.')
            elif DoctorRegistration.objects.filter(council_id=council_id, registration_number=reg_number).exists():
                dj_messages.error(request, 'This registration already exists.')
            else:
                DoctorRegistration.objects.create(
                    doctor=dp, council_id=council_id,
                    registration_number=reg_number, registration_year=reg_year,
                    is_primary=not dp.registrations.exists(),
                )
                if dp.verification_status == 'UNVERIFIED':
                    dp.verification_status = 'PENDING'
                    dp.save(update_fields=['verification_status'])
                dj_messages.success(request, 'Registration submitted for verification.')
                return redirect(f'/profile/{dp.id}/')
        except Exception as e:
            dj_messages.error(request, str(e))
    return render(request, 'add_registration.html', {'councils': councils})


@login_required
def register_hospital_view(request):
    from django.contrib import messages as dj_messages
    if request.user.user_type not in ('HOSPITAL_ADMIN', 'ADMIN'):
        dj_messages.error(request, 'Only hospital admins can register a hospital.')
        return redirect('/hospitals/')
    from apps.hospitals.models import Hospital, HospitalUser
    if HospitalUser.objects.filter(user=request.user).exists():
        dj_messages.warning(request, 'You are already associated with a hospital.')
        return redirect('/hospitals/')
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            h_type = request.POST.get('type', 'HOSPITAL')
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()
            bed_count = request.POST.get('bed_count', '').strip()
            phone = request.POST.get('phone', '').strip() or None
            website = request.POST.get('website', '').strip() or None
            about = request.POST.get('about', '').strip() or None
            if not name or not city or not state:
                dj_messages.error(request, 'Name, city and state are required.')
            else:
                hospital = Hospital.objects.create(
                    name=name, type=h_type, about=about,
                    location={'city': city, 'state': state, 'address': request.POST.get('address', '').strip()},
                    bed_count=int(bed_count) if bed_count else None,
                    phone=phone, website=website, verification_status='PENDING',
                )
                HospitalUser.objects.create(user=request.user, hospital=hospital, role='ADMIN')
                dj_messages.success(request, f'{name} registered successfully. Pending verification.')
                return redirect('/hospitals/')
        except Exception as e:
            dj_messages.error(request, str(e))
    HOSPITAL_TYPES = [('HOSPITAL','Hospital'),('CLINIC','Clinic'),('NURSING_HOME','Nursing Home'),('MEDICAL_COLLEGE','Medical College')]
    return render(request, 'register_hospital.html', {'hospital_types': HOSPITAL_TYPES})


@login_required
def post_job_view(request):
    from django.contrib import messages as dj_messages
    from apps.hospitals.models import HospitalUser
    try:
        hu = HospitalUser.objects.select_related('hospital').get(user=request.user)
    except HospitalUser.DoesNotExist:
        dj_messages.error(request, 'You must be associated with a hospital to post jobs.')
        return redirect('/jobs/')
    from apps.core.models import Specialization
    specializations = list(Specialization.objects.filter(is_active=True).order_by('name'))
    JOB_TYPES = [('FULL_TIME','Full Time'),('PART_TIME','Part Time'),('LOCUM','Locum'),('VISITING','Visiting'),('CONTRACT','Contract')]
    SHIFT_TYPES = [('DAY','Day'),('NIGHT','Night'),('ROTATIONAL','Rotational'),('FLEXIBLE','Flexible')]
    if request.method == 'POST':
        try:
            from apps.jobs.models import JobPost
            from django.utils import timezone
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()
            if not title or not description or not city:
                dj_messages.error(request, 'Title, description and city are required.')
            else:
                spec_id = request.POST.get('specialty_id', '').strip() or None
                sal_min = request.POST.get('salary_min', '').strip()
                sal_max = request.POST.get('salary_max', '').strip()
                exp_min = request.POST.get('experience_min_years', '0').strip()
                save_as = request.POST.get('save_as', 'PUBLISHED')
                status = 'DRAFT' if save_as == 'DRAFT' else 'PUBLISHED'
                jp = JobPost.objects.create(
                    hospital=hu.hospital,
                    title=title,
                    specialty_id=spec_id or '00000000-0000-0000-0000-000000000000',
                    qualification_ids=[],
                    description=description,
                    responsibilities=request.POST.get('responsibilities', '').strip() or None,
                    requirements=request.POST.get('requirements', '').strip() or None,
                    location={'city': city, 'state': state},
                    salary_min=float(sal_min) if sal_min else None,
                    salary_max=float(sal_max) if sal_max else None,
                    salary_visibility=request.POST.get('salary_visibility', 'PUBLIC'),
                    job_type=request.POST.get('job_type', 'FULL_TIME'),
                    experience_min_years=float(exp_min) if exp_min else 0,
                    shift_type=request.POST.get('shift_type', 'DAY'),
                    positions=int(request.POST.get('positions', 1) or 1),
                    is_urgent='is_urgent' in request.POST,
                    status=status,
                    posted_by=request.user,
                    published_at=timezone.now() if status == 'PUBLISHED' else None,
                )
                if status == 'DRAFT':
                    dj_messages.success(request, f'Job "{title}" saved as draft.')
                    return redirect('/hospitals/me/jobs/')
                dj_messages.success(request, f'Job "{title}" posted successfully!')
                return redirect(f'/jobs/{jp.id}/')
        except Exception as e:
            dj_messages.error(request, str(e))
    return render(request, 'post_job.html', {
        'hospital': hu.hospital,
        'specializations': specializations,
        'job_types': JOB_TYPES,
        'shift_types': SHIFT_TYPES,
    })


@login_required
def hospital_detail_view(request, hospital_id):
    from apps.hospitals.models import Hospital
    from apps.jobs.models import JobPost
    from django.db.models import Count, Q
    try:
        hospital = Hospital.objects.get(id=hospital_id)
    except Hospital.DoesNotExist:
        from django.http import Http404
        raise Http404
    jobs_list = list(JobPost.objects.filter(hospital=hospital, status='PUBLISHED').order_by('-published_at')[:10])
    branches = list(hospital.branches.all())
    departments = list(hospital.departments.all())
    is_following = False
    is_hospital_admin = False
    if request.user.is_authenticated:
        from apps.hospitals.models import HospitalFollow, HospitalUser
        is_following = HospitalFollow.objects.filter(user=request.user, hospital=hospital).exists()
        is_hospital_admin = HospitalUser.objects.filter(user=request.user, hospital=hospital, role__in=['ADMIN','HR']).exists()
    follower_count = hospital.followers.count()
    return render(request, 'hospital_detail.html', {
        'hospital': hospital,
        'jobs': jobs_list,
        'branches': branches,
        'departments': departments,
        'color': _color(hospital.id),
        'is_following': is_following,
        'is_hospital_admin': is_hospital_admin,
        'follower_count': follower_count,
    })


@login_required
@require_POST
def request_shift_view(request, requirement_id):
    from django.contrib import messages as dj_messages
    if request.user.user_type != 'DOCTOR':
        dj_messages.error(request, 'Only doctors can request shifts.')
        return redirect('/availability/')
    try:
        from apps.shifts.models import ShiftRequirement, ShiftRequest
        from apps.notifications.models import Notification
        req = ShiftRequirement.objects.select_related('hospital', 'created_by').get(id=requirement_id, status='OPEN')
        doctor = request.user.doctor_profile
        if ShiftRequest.objects.filter(requirement=req, doctor=doctor).exists():
            dj_messages.warning(request, 'You have already requested this shift.')
        else:
            sr = ShiftRequest.objects.create(requirement=req, doctor=doctor)
            dj_messages.success(request, f'Shift request sent to {req.hospital.name}!')
            # Notify the hospital admin/creator
            Notification.objects.create(
                user=req.created_by,
                type='SHIFT_REQUEST',
                title=f'Dr. {doctor.full_name} requested your shift',
                body=f'{req.hospital.name} · {req.requirement_date} · ₹{req.compensation}',
                data_json={'shift_request_id': str(sr.id), 'requirement_id': str(req.id)},
                deep_link=f'/shifts/hospital/?status=REQUESTED',
            )
            # Also notify the doctor themselves for confirmation
            Notification.objects.create(
                user=request.user,
                type='SHIFT_REQUEST_SENT',
                title=f'Shift request sent to {req.hospital.name}',
                body=f'{req.requirement_date} · {req.start_time}–{req.end_time} · ₹{req.compensation}',
                data_json={'shift_request_id': str(sr.id)},
                deep_link='/shifts/mine/',
            )
    except Exception as e:
        dj_messages.error(request, str(e))
    return redirect('/availability/')


@login_required
def doctor_search_json(request):
    from apps.doctors.models import DoctorProfile
    from django.db.models import Q
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse([], safe=False)
    qs = DoctorProfile.objects.filter(
        Q(first_name__icontains=q) | Q(last_name__icontains=q)
    ).exclude(user=request.user)[:8]
    return JsonResponse([{
        'id': str(d.id),
        'full_name': d.full_name,
        'headline': d.headline or '',
        'initials': _get_initials(d.full_name),
        'color': _color(d.id),
    } for d in qs], safe=False)


@login_required
@require_POST
def send_connection_request(request, doctor_id):
    from django.contrib import messages as dj_messages
    from apps.doctors.models import DoctorProfile, Connection
    from apps.notifications.models import Notification
    if request.user.user_type != 'DOCTOR':
        dj_messages.error(request, 'Only doctors can connect.')
        return redirect(f'/profile/{doctor_id}/')
    try:
        my_profile = request.user.doctor_profile
        target = DoctorProfile.objects.select_related('user').get(id=doctor_id)
        if target.user == request.user:
            dj_messages.error(request, 'You cannot connect with yourself.')
            return redirect(f'/profile/{doctor_id}/')
        # Check existing in either direction
        existing = Connection.objects.filter(
            sender=my_profile, receiver=target
        ).first() or Connection.objects.filter(
            sender=target, receiver=my_profile
        ).first()
        if existing:
            if existing.status == 'ACCEPTED':
                dj_messages.info(request, 'You are already connected.')
            elif existing.status == 'PENDING':
                dj_messages.info(request, 'Connection request already sent.')
            elif existing.status in ('DECLINED', 'WITHDRAWN'):
                # Allow re-request
                existing.sender = my_profile
                existing.receiver = target
                existing.status = 'PENDING'
                existing.save()
                Notification.objects.create(
                    user=target.user,
                    type='CONNECTION_REQUEST',
                    title=f'Dr. {my_profile.full_name} wants to connect',
                    body=f'Dr. {my_profile.full_name} sent you a connection request.',
                    data_json={'from_doctor_id': str(my_profile.id)},
                    deep_link='/network/requests/',
                )
                dj_messages.success(request, f'Connection request sent to Dr. {target.full_name}!')
        else:
            conn = Connection.objects.create(sender=my_profile, receiver=target)
            Notification.objects.create(
                user=target.user,
                type='CONNECTION_REQUEST',
                title=f'Dr. {my_profile.full_name} wants to connect',
                body=f'Dr. {my_profile.full_name} sent you a connection request.',
                data_json={'from_doctor_id': str(my_profile.id), 'connection_id': str(conn.id)},
                deep_link='/network/requests/',
            )
            dj_messages.success(request, f'Connection request sent to Dr. {target.full_name}!')
    except DoctorProfile.DoesNotExist:
        dj_messages.error(request, 'Doctor not found.')
    except Exception as e:
        dj_messages.error(request, str(e))
    return redirect(f'/profile/{doctor_id}/')


@login_required
@require_POST
def respond_connection_view(request, connection_id):
    """Accept or decline a connection request."""
    from django.contrib import messages as dj_messages
    from apps.doctors.models import Connection
    from apps.notifications.models import Notification
    action = request.POST.get('action', '')
    try:
        my_profile = request.user.doctor_profile
        conn = Connection.objects.select_related('sender', 'sender__user').get(
            id=connection_id, receiver=my_profile, status='PENDING'
        )
        if action == 'accept':
            conn.status = 'ACCEPTED'
            conn.save()
            Notification.objects.create(
                user=conn.sender.user,
                type='CONNECTION_ACCEPTED',
                title=f'Dr. {my_profile.full_name} accepted your request',
                body=f'You are now connected with Dr. {my_profile.full_name}.',
                data_json={'doctor_id': str(my_profile.id)},
                deep_link=f'/profile/{my_profile.id}/',
            )
            dj_messages.success(request, f'Connected with Dr. {conn.sender.full_name}!')
        elif action == 'decline':
            conn.status = 'DECLINED'
            conn.save()
            dj_messages.success(request, 'Connection request declined.')
    except Exception as e:
        dj_messages.error(request, str(e))
    return redirect('/network/requests/')


@login_required
@require_POST
def withdraw_connection_view(request, doctor_id):
    """Withdraw a sent pending request or remove an accepted connection."""
    from django.contrib import messages as dj_messages
    from apps.doctors.models import DoctorProfile, Connection
    try:
        my_profile = request.user.doctor_profile
        target = DoctorProfile.objects.get(id=doctor_id)
        conn = Connection.objects.filter(
            sender=my_profile, receiver=target
        ).first() or Connection.objects.filter(
            sender=target, receiver=my_profile
        ).first()
        if conn:
            conn.status = 'WITHDRAWN'
            conn.save()
            dj_messages.success(request, 'Connection removed.')
    except Exception as e:
        dj_messages.error(request, str(e))
    return redirect(f'/profile/{doctor_id}/')


@login_required
def my_connections_view(request):
    """Show pending incoming requests + accepted connections."""
    from apps.doctors.models import Connection
    tab = request.GET.get('tab', 'requests')
    try:
        my_profile = request.user.doctor_profile
        pending = list(Connection.objects.filter(
            receiver=my_profile, status='PENDING'
        ).select_related('sender', 'sender__user').order_by('-created_at'))
        connected_qs = Connection.objects.filter(
            status='ACCEPTED'
        ).filter(
            models_Q(sender=my_profile) | models_Q(receiver=my_profile)
        ).select_related('sender', 'sender__user', 'receiver', 'receiver__user').order_by('-updated_at')
        # Annotate each connection with the "other" doctor for easy template use
        connected = []
        for c in connected_qs:
            other = c.receiver if c.sender_id == my_profile.id else c.sender
            connected.append({'conn': c, 'other': other})
    except Exception:
        pending = []
        connected = []
    return render(request, 'my_connections.html', {
        'pending': pending,
        'connected': connected,
        'tab': tab,
        'pending_count': len(pending),
    })


@login_required
def start_conversation(request, doctor_id):
    from apps.doctors.models import DoctorProfile
    from apps.messaging.models import Conversation, ConversationParticipant
    from django.db.models import Q
    try:
        target = DoctorProfile.objects.select_related('user').get(id=doctor_id)
        target_user = target.user
        if target_user == request.user:
            return redirect('/messaging/')
        # Find existing direct conversation between these two users
        my_convs = ConversationParticipant.objects.filter(
            user=request.user, conversation__type='DIRECT'
        ).values_list('conversation_id', flat=True)
        existing = ConversationParticipant.objects.filter(
            user=target_user, conversation_id__in=my_convs
        ).first()
        if existing:
            conv_id = existing.conversation_id
        else:
            conv = Conversation.objects.create(type='DIRECT')
            ConversationParticipant.objects.create(conversation=conv, user=request.user)
            ConversationParticipant.objects.create(conversation=conv, user=target_user)
            conv_id = conv.id
    except DoctorProfile.DoesNotExist:
        return redirect('/messaging/')
    except Exception:
        return redirect('/messaging/')
    return redirect(f'/messaging/?conv={conv_id}')


@login_required
def my_shift_requests_view(request):
    """Doctor's shift requests page."""
    if request.user.user_type != 'DOCTOR':
        return redirect('/')
    from apps.shifts.models import ShiftRequest
    status_filter = request.GET.get('status', '')
    try:
        qs = ShiftRequest.objects.filter(
            doctor=request.user.doctor_profile
        ).select_related('requirement', 'requirement__hospital').order_by('-requested_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
    except Exception:
        qs = []
    return render(request, 'my_shift_requests.html', {
        'shift_requests': qs,
        'status_filter': status_filter,
    })


@login_required
def hospital_shift_requests_view(request):
    """Hospital view: manage all shift requests across their requirements."""
    from apps.hospitals.models import HospitalUser
    from apps.shifts.models import ShiftRequest, ShiftRequirement
    from django.contrib import messages as dj_messages
    try:
        hu = HospitalUser.objects.select_related('hospital').get(user=request.user)
    except HospitalUser.DoesNotExist:
        dj_messages.error(request, 'Not associated with a hospital.')
        return redirect('/')
    status_filter = request.GET.get('status', '')
    qs = ShiftRequest.objects.filter(
        requirement__hospital=hu.hospital
    ).select_related('requirement', 'doctor').order_by('-requested_at')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'hospital_shift_requests.html', {
        'shift_requests': list(qs[:50]),
        'hospital': hu.hospital,
        'status_filter': status_filter,
    })


@login_required
@require_POST
def update_shift_request_view(request, request_id):
    """Hospital confirms/completes/cancels a shift request."""
    from apps.hospitals.models import HospitalUser
    from apps.shifts.models import ShiftRequest
    from django.contrib import messages as dj_messages
    from django.utils import timezone
    action = request.POST.get('action', '')
    try:
        hu = HospitalUser.objects.get(user=request.user)
        sr = ShiftRequest.objects.select_related('requirement').get(
            id=request_id, requirement__hospital=hu.hospital
        )
        if action == 'confirm' and sr.status == 'ACCEPTED_BY_DOCTOR':
            sr.status = 'CONFIRMED_BY_HOSPITAL'
            sr.confirmed_at = timezone.now()
            sr.save()
            dj_messages.success(request, 'Shift confirmed.')
        elif action == 'complete' and sr.status == 'CONFIRMED_BY_HOSPITAL':
            sr.status = 'COMPLETED'
            sr.completed_at = timezone.now()
            sr.save()
            req = sr.requirement
            confirmed = req.requests.filter(status__in=['CONFIRMED_BY_HOSPITAL', 'COMPLETED']).count()
            if confirmed >= req.doctors_required:
                req.status = 'FILLED'
                req.save(update_fields=['status'])
            dj_messages.success(request, 'Shift marked as completed.')
        elif action == 'cancel':
            if sr.status not in ('COMPLETED', 'CANCELLED'):
                sr.status = 'CANCELLED'
                sr.cancelled_at = timezone.now()
                sr.save()
                dj_messages.success(request, 'Shift request cancelled.')
        else:
            dj_messages.error(request, 'Invalid action.')
    except Exception as e:
        dj_messages.error(request, str(e))
    return redirect(request.META.get('HTTP_REFERER', '/shifts/hospital/'))


@login_required
@require_POST
def doctor_respond_shift_view(request, request_id):
    """Doctor accepts or declines a shift request."""
    from apps.shifts.models import ShiftRequest
    from django.contrib import messages as dj_messages
    from django.utils import timezone
    action = request.POST.get('action', '')
    try:
        sr = ShiftRequest.objects.get(id=request_id, doctor=request.user.doctor_profile, status='REQUESTED')
        if action == 'accept':
            sr.status = 'ACCEPTED_BY_DOCTOR'
            sr.accepted_at = timezone.now()
            sr.save()
            dj_messages.success(request, 'Shift accepted.')
        elif action == 'decline':
            sr.status = 'DECLINED_BY_DOCTOR'
            sr.declined_at = timezone.now()
            sr.save()
            dj_messages.success(request, 'Shift declined.')
        elif action == 'cancel':
            if sr.status not in ('COMPLETED', 'CANCELLED'):
                sr.status = 'CANCELLED'
                sr.cancelled_at = timezone.now()
                sr.save()
                dj_messages.success(request, 'Shift request cancelled.')
    except Exception as e:
        dj_messages.error(request, str(e))
    return redirect('/shifts/mine/')


@login_required
def hospital_staff_view(request):
    from apps.hospitals.models import HospitalUser, Hospital
    from django.contrib import messages as dj_messages
    from django.contrib.auth import get_user_model
    try:
        hu = HospitalUser.objects.select_related('hospital').get(user=request.user)
    except HospitalUser.DoesNotExist:
        dj_messages.error(request, 'Not associated with a hospital.')
        return redirect('/')

    staff = list(
        HospitalUser.objects.filter(hospital=hu.hospital)
        .select_related('user', 'branch', 'department')
        .order_by('role', 'created_at')
    )

    if request.method == 'POST' and hu.role == 'ADMIN':
        action = request.POST.get('action', '')
        if action == 'invite':
            User = get_user_model()
            phone = request.POST.get('phone', '').strip()
            role = request.POST.get('role', 'HR')
            designation = request.POST.get('designation', '').strip() or None
            if not phone:
                dj_messages.error(request, 'Phone is required.')
            elif HospitalUser.objects.filter(hospital=hu.hospital, user__phone=phone).exists():
                dj_messages.warning(request, 'User already in your hospital.')
            else:
                invited, _ = User.objects.get_or_create(
                    phone=phone,
                    defaults={'user_type': 'HOSPITAL_HR', 'status': 'ACTIVE'},
                )
                if HospitalUser.objects.filter(user=invited).exclude(hospital=hu.hospital).exists():
                    dj_messages.error(request, 'User is already in another hospital.')
                else:
                    HospitalUser.objects.get_or_create(
                        user=invited, hospital=hu.hospital,
                        defaults={'role': role, 'designation': designation},
                    )
                    dj_messages.success(request, f'{phone} added as {role}.')
            return redirect('/hospitals/me/staff/')
        elif action == 'remove':
            member_id = request.POST.get('member_id', '')
            HospitalUser.objects.filter(
                id=member_id, hospital=hu.hospital
            ).exclude(user=request.user).delete()
            dj_messages.success(request, 'Staff member removed.')
            return redirect('/hospitals/me/staff/')
        elif action == 'toggle_status':
            member_id = request.POST.get('member_id', '')
            member = HospitalUser.objects.filter(id=member_id, hospital=hu.hospital).exclude(user=request.user).first()
            if member:
                member.status = 'INACTIVE' if member.status == 'ACTIVE' else 'ACTIVE'
                member.save(update_fields=['status'])
                dj_messages.success(request, 'Status updated.')
            return redirect('/hospitals/me/staff/')

    return render(request, 'hospital_staff.html', {
        'hospital': hu.hospital,
        'my_role': hu.role,
        'staff': staff,
        'is_admin': hu.role == 'ADMIN',
    })


@login_required
@require_POST
def follow_hospital_view(request, hospital_id):
    from apps.hospitals.models import Hospital, HospitalFollow
    try:
        hospital = Hospital.objects.get(id=hospital_id)
        follow, created = HospitalFollow.objects.get_or_create(user=request.user, hospital=hospital)
        if not created:
            follow.delete()
    except Exception:
        pass
    return redirect(f'/hospitals/{hospital_id}/')


@login_required
@require_POST
def upload_hospital_logo(request, hospital_id):
    import base64
    from apps.hospitals.models import Hospital, HospitalUser
    try:
        hu = HospitalUser.objects.get(user=request.user, hospital_id=hospital_id)
        if hu.role not in ('ADMIN', 'HR'):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        f = request.FILES.get('logo')
        if not f:
            return JsonResponse({'error': 'No file'}, status=400)
        if f.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'Max 5MB'}, status=400)
        hospital = hu.hospital
        hospital.logo_base64 = 'data:{};base64,{}'.format(f.content_type, base64.b64encode(f.read()).decode())
        hospital.save(update_fields=['logo_base64'])
        return JsonResponse({'url': hospital.logo_base64})
    except HospitalUser.DoesNotExist:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def hospital_applicants_view(request, job_id):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobPost, JobApplication, ApplicationHistory
    from django.contrib import messages as dj_messages
    try:
        hu = HospitalUser.objects.select_related('hospital').get(user=request.user)
    except HospitalUser.DoesNotExist:
        return redirect('/')

    try:
        job = JobPost.objects.get(id=job_id, hospital=hu.hospital)
    except JobPost.DoesNotExist:
        from django.http import Http404
        raise Http404

    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '').strip()
        VALID = ['PROFILE_VIEWED', 'SHORTLISTED', 'INTERVIEW', 'OFFERED', 'HIRED', 'REJECTED']
        if new_status in VALID:
            try:
                app = JobApplication.objects.get(id=app_id, job=job)
                old_status = app.status
                app.status = new_status
                app.save(update_fields=['status', 'updated_at'])
                ApplicationHistory.objects.create(
                    application=app,
                    from_status=old_status,
                    to_status=new_status,
                    changed_by=request.user,
                    notes=notes or None,
                )
                dj_messages.success(request, f'Application status updated to {new_status}.')
            except Exception as e:
                dj_messages.error(request, str(e))
        return redirect(f'/jobs/{job_id}/applicants/')

    status_filter = request.GET.get('status', '')
    qs = JobApplication.objects.filter(job=job).select_related(
        'doctor', 'doctor__user'
    ).prefetch_related('history').order_by('-applied_at')
    if status_filter:
        qs = qs.filter(status=status_filter)

    applicants = []
    for app in qs:
        applicants.append({
            'app': app,
            'doctor': app.doctor,
            'color': _color(app.doctor.id),
            'initials': _get_initials(app.doctor.full_name),
            'photo': app.doctor.photo_base64 or '',
        })

    STATUS_CHOICES = ['APPLIED', 'PROFILE_VIEWED', 'SHORTLISTED', 'INTERVIEW', 'OFFERED', 'HIRED', 'REJECTED', 'WITHDRAWN']
    return render(request, 'hospital_applicants.html', {
        'job': job,
        'applicants': applicants,
        'status_filter': status_filter,
        'status_choices': STATUS_CHOICES,
        'total': qs.count(),
        'hospital': hu.hospital,
    })


@login_required
def hospital_jobs_view(request):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobPost
    from django.contrib import messages as dj_messages
    try:
        hu = HospitalUser.objects.select_related('hospital').get(user=request.user)
    except HospitalUser.DoesNotExist:
        dj_messages.error(request, 'Not associated with a hospital.')
        return redirect('/')
    jobs_list = list(JobPost.objects.filter(hospital=hu.hospital).order_by('-created_at')[:50])
    return render(request, 'hospital_jobs.html', {
        'jobs': jobs_list,
        'hospital': hu.hospital,
    })


@login_required
@require_POST
def publish_job_view(request, job_id):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobPost
    from django.contrib import messages as dj_messages
    try:
        hu = HospitalUser.objects.get(user=request.user)
        job = JobPost.objects.get(id=job_id, hospital=hu.hospital, status='DRAFT')
        job.status = 'PUBLISHED'
        job.published_at = timezone.now()
        job.save(update_fields=['status', 'published_at'])
        dj_messages.success(request, f'Job "{job.title}" published successfully!')
    except JobPost.DoesNotExist:
        dj_messages.error(request, 'Job not found or already published.')
    except Exception as e:
        dj_messages.error(request, str(e))
    return redirect('/hospitals/me/jobs/')


@login_required
def my_availability_view(request):
    if request.user.user_type != 'DOCTOR':
        return redirect('/')
    from apps.availability.models import DoctorAvailability
    from django.contrib import messages as dj_messages
    if request.method == 'POST' and request.POST.get('action') == 'deactivate':
        avail_id = request.POST.get('avail_id')
        try:
            a = DoctorAvailability.objects.get(id=avail_id, doctor=request.user.doctor_profile)
            a.is_active = False
            a.save(update_fields=['is_active'])
            dj_messages.success(request, 'Availability deactivated.')
        except Exception:
            pass
        return redirect('/availability/mine/')
    availabilities = list(
        DoctorAvailability.objects.filter(doctor=request.user.doctor_profile)
        .prefetch_related('slots').order_by('-created_at')
    )
    return render(request, 'my_availability.html', {'availabilities': availabilities})


@login_required
def badge_counts(request):
    unread_messages = 0
    unread_notifications = 0
    try:
        from apps.messaging.models import ConversationParticipant, Message
        from django.db.models import Q
        participants = ConversationParticipant.objects.filter(user=request.user, is_active=True)
        for p in participants:
            last = p.conversation.messages.order_by('-created_at').first()
            if last and last.sender != request.user:
                if p.last_read_at is None or last.created_at > p.last_read_at:
                    unread_messages += 1
    except Exception:
        pass
    try:
        from apps.notifications.models import Notification
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    except Exception:
        pass
    return JsonResponse({'unread_messages': unread_messages, 'unread_notifications': unread_notifications})


@login_required
def hospitals(request):
    from apps.hospitals.models import Hospital
    from django.db.models import Count, Q

    search = request.GET.get('q', '')
    h_type = request.GET.get('type', '')
    city = request.GET.get('city', '')
    verified_only = request.GET.get('verified', '')

    qs = Hospital.objects.annotate(
        open_jobs=Count('job_posts', filter=Q(job_posts__status='PUBLISHED'))
    ).order_by('-created_at')

    if search:
        qs = qs.filter(name__icontains=search)
    if h_type:
        qs = qs.filter(type=h_type)
    if city:
        qs = qs.filter(location__city__icontains=city)
    if verified_only:
        qs = qs.filter(verification_status='VERIFIED')

    hospitals_list = list(qs[:30])

    HOSPITAL_TYPES = [('HOSPITAL','Hospital'),('CLINIC','Clinic'),('NURSING_HOME','Nursing Home'),('MEDICAL_COLLEGE','Medical College')]

    return render(request, 'hospitals.html', {
        'hospitals': hospitals_list,
        'hospital_types': HOSPITAL_TYPES,
        'search': search,
        'filter_type': h_type,
        'filter_city': city,
        'verified_only': verified_only,
        'total': len(hospitals_list),
    })
