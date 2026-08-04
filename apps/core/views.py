import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone


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
                                 .order_by('-created_at')[:4])
        suggested_doctors = [{
            'color': _color(d.id),
            'initials': _get_initials(d.full_name),
            'full_name': d.full_name,
            'headline': d.headline,
            'professional_location': d.professional_location,
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
    from apps.doctors.models import DoctorProfile
    search = request.GET.get('q', '')
    spec_filter = request.GET.get('spec', '')
    city_filter = request.GET.get('city', '')
    exp_filter = request.GET.get('exp', '')
    verified_only = request.GET.get('verified', '')

    qs = DoctorProfile.objects.select_related('user').order_by('-created_at')
    if search:
        qs = qs.filter(first_name__icontains=search) | DoctorProfile.objects.filter(last_name__icontains=search) | DoctorProfile.objects.filter(headline__icontains=search)
        qs = qs.select_related('user').order_by('-created_at')
    if verified_only:
        qs = qs.filter(verification_status='VERIFIED')
    if exp_filter:
        qs = qs.filter(experience_years__gte=exp_filter)

    doctors_raw = list(qs[:30])
    doctors = []
    for d in doctors_raw:
        doctors.append({
            'obj': d,
            'color': _color(d.id),
            'initials': _get_initials(d.full_name),
            'full_name': d.full_name,
            'headline': d.headline,
            'experience_years': d.experience_years,
            'professional_location': d.professional_location,
            'verification_status': d.verification_status,
        })

    return render(request, 'network.html', {
        'doctors': doctors,
        'search': search,
        'spec_filter': spec_filter,
        'city_filter': city_filter,
        'exp_filter': exp_filter,
        'verified_only': verified_only,
        'total': len(doctors),
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
        qs = qs.filter(title__icontains=search) | JobPost.objects.filter(status='PUBLISHED', hospital__name__icontains=search)
        qs = qs.select_related('hospital').order_by('-published_at', '-created_at')

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

    shift_qs = ShiftRequirement.objects.filter(status='OPEN').select_related('hospital').order_by('-created_at')
    if urgency:
        shift_qs = shift_qs.filter(urgency=urgency)

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
        ShiftRequirement.objects.create(
            hospital=hospital_user.hospital,
            specialty_id=uuid.uuid4(),  # placeholder — real impl needs specialty lookup
            qualification_ids=[],
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
                conversations.append({
                    'id': str(conv.id),
                    'name': name,
                    'initials': _get_initials(name),
                    'color': _color(conv.id),
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
            try:
                request.user.email = email
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
