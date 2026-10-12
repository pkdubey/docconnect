#!/usr/bin/env python
"""
Full test data seed script — creates all user types + real data for API testing.

Usage:
    python scripts/seed_test_data.py

Creates:
    - 1 Super Admin
    - 1 Platform Admin
    - 5 Doctors (verified + unverified)
    - 2 Hospitals with branches, departments, staff
    - Jobs, Applications, Connections, Posts, Comments, Availability, Shifts
"""
import os
import sys
import django
from datetime import date, timedelta, datetime
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docconnect_backend.settings.development')
django.setup()

from django.contrib.auth.hashers import make_password
from apps.accounts.models import User
from apps.core.models import Specialization, Qualification, Council, Community, CommunityMember
from apps.doctors.models import (
    DoctorProfile, DoctorQualification, DoctorExperience,
    DoctorRegistration, Connection, Post, PostLike, PostComment
)
from apps.hospitals.models import Hospital, HospitalBranch, HospitalDepartment, HospitalUser
from apps.jobs.models import JobPost, JobApplication
from apps.availability.models import DoctorAvailability, AvailabilitySlot
from apps.shifts.models import ShiftRequirement, ShiftRequest
from apps.notifications.models import Notification

PASSWORD = "Test@1234"

# ── Helpers ───────────────────────────────────────────────────

def make_user(phone, user_type, **kwargs):
    user, created = User.objects.get_or_create(
        phone=phone,
        defaults={"user_type": user_type, "password": make_password(PASSWORD), **kwargs}
    )
    if not created:
        print(f"  [skip] User {phone} already exists")
    return user, created


def p(msg):
    print(f"  {msg}")


# ── 1. Master Data ────────────────────────────────────────────

def seed_masters():
    specs = ["General Medicine", "Cardiology", "Neurology", "Anesthesiology",
             "Orthopedics", "Pediatrics", "Dermatology", "Radiology"]
    quals = ["MBBS", "MD", "MS", "DM", "DNB"]
    councils_data = [
        {"name": "National Medical Commission", "short": "NMC"},
        {"name": "Medical Council of India", "short": "MCI"},
        {"name": "Maharashtra Medical Council", "short": "MMC"},
    ]
    for s in specs:
        Specialization.objects.get_or_create(name=s)
    for q in quals:
        Qualification.objects.get_or_create(name=q)
    for c in councils_data:
        Council.objects.get_or_create(name=c["name"], defaults={"short": c["short"]})
    p(f"Masters: {len(specs)} specializations, {len(quals)} qualifications, {len(councils_data)} councils")
    return (
        {s: Specialization.objects.get(name=s) for s in specs},
        {q: Qualification.objects.get(name=q) for q in quals},
        Council.objects.first(),
    )


# ── 2. Admin Users ────────────────────────────────────────────

def seed_admins():
    super_admin, _ = make_user(
        "9999999999", "ADMIN",
        is_staff=True, is_superuser=True, is_super_admin=True,
        metadata={"first_name": "Super", "last_name": "Admin"}
    )
    platform_admin, _ = make_user(
        "9999999998", "ADMIN",
        is_staff=True,
        metadata={"first_name": "Platform", "last_name": "Admin"}
    )
    p(f"Admins: super={super_admin.phone}, platform={platform_admin.phone}")
    return super_admin, platform_admin


# ── 3. Doctors ────────────────────────────────────────────────

DOCTORS_DATA = [
    {
        "phone": "9000000001",
        "first_name": "Arjun", "last_name": "Sharma",
        "headline": "Cardiologist · AIIMS Delhi · 12 yrs",
        "about": "Senior cardiologist with expertise in interventional cardiology.",
        "spec": "Cardiology", "exp": 12, "verified": True,
        "location": {"city": "Delhi", "state": "Delhi", "pincode": "110001"},
    },
    {
        "phone": "9000000002",
        "first_name": "Priya", "last_name": "Mehta",
        "headline": "Anesthesiologist · KEM Mumbai · 8 yrs",
        "about": "Experienced anesthesiologist specializing in cardiac anesthesia.",
        "spec": "Anesthesiology", "exp": 8, "verified": True,
        "location": {"city": "Mumbai", "state": "Maharashtra", "pincode": "400012"},
    },
    {
        "phone": "9000000003",
        "first_name": "Rahul", "last_name": "Verma",
        "headline": "Neurologist · NIMHANS Bangalore · 6 yrs",
        "about": "Neurologist focused on epilepsy and movement disorders.",
        "spec": "Neurology", "exp": 6, "verified": True,
        "location": {"city": "Bangalore", "state": "Karnataka", "pincode": "560029"},
    },
    {
        "phone": "9000000004",
        "first_name": "Sneha", "last_name": "Patel",
        "headline": "Pediatrician · Ahmedabad · 4 yrs",
        "about": "Pediatrician with interest in neonatal care.",
        "spec": "Pediatrics", "exp": 4, "verified": False,
        "location": {"city": "Ahmedabad", "state": "Gujarat", "pincode": "380001"},
    },
    {
        "phone": "9000000005",
        "first_name": "Vikram", "last_name": "Singh",
        "headline": "Orthopedic Surgeon · Jaipur · 10 yrs",
        "about": "Orthopedic surgeon specializing in joint replacement.",
        "spec": "Orthopedics", "exp": 10, "verified": True,
        "location": {"city": "Jaipur", "state": "Rajasthan", "pincode": "302001"},
    },
]


def seed_doctors(specs, council):
    profiles = []
    for d in DOCTORS_DATA:
        user, created = make_user(d["phone"], "DOCTOR")
        spec = specs.get(d["spec"])
        profile, _ = DoctorProfile.objects.get_or_create(
            user=user,
            defaults={
                "first_name": d["first_name"],
                "last_name": d["last_name"],
                "headline": d["headline"],
                "about": d["about"],
                "primary_specialization_id": spec.id if spec else None,
                "experience_years": Decimal(str(d["exp"])),
                "verification_status": "VERIFIED" if d["verified"] else "UNVERIFIED",
                "open_to_opportunities": True,
                "professional_location": d["location"],
            }
        )
        # Qualification
        DoctorQualification.objects.get_or_create(
            doctor=profile, degree="MBBS",
            defaults={"institution": "AIIMS", "year": 2010}
        )
        # Experience
        DoctorExperience.objects.get_or_create(
            doctor=profile, role="Senior Consultant",
            defaults={
                "hospital_name": f"{d['location']['city']} Medical Center",
                "start_date": date(2018, 1, 1),
                "is_current": True,
            }
        )
        # Registration (for verified doctors)
        if d["verified"] and council:
            DoctorRegistration.objects.get_or_create(
                doctor=profile,
                council_id=council.id,
                registration_number=f"REG{d['phone'][-6:]}",
                defaults={"registration_year": 2012, "verification_status": "VERIFIED"}
            )
        profiles.append(profile)
    p(f"Doctors: {len(profiles)} created/found")
    return profiles


# ── 4. Hospitals ──────────────────────────────────────────────

HOSPITALS_DATA = [
    {
        "phone": "8000000001",
        "name": "Apollo Hospitals Delhi",
        "type": "HOSPITAL",
        "city": "Delhi", "state": "Delhi", "pincode": "110001",
        "beds": 500,
    },
    {
        "phone": "8000000002",
        "name": "Fortis Healthcare Mumbai",
        "type": "HOSPITAL",
        "city": "Mumbai", "state": "Maharashtra", "pincode": "400053",
        "beds": 350,
    },
]


def seed_hospitals():
    hospitals = []
    for h in HOSPITALS_DATA:
        admin_user, _ = make_user(h["phone"], "HOSPITAL_ADMIN")
        hospital, _ = Hospital.objects.get_or_create(
            name=h["name"],
            defaults={
                "type": h["type"],
                "location": {"city": h["city"], "state": h["state"], "pincode": h["pincode"]},
                "bed_count": h["beds"],
                "verification_status": "VERIFIED",
            }
        )
        # Link admin via HospitalUser
        HospitalUser.objects.get_or_create(
            hospital=hospital, user=admin_user,
            defaults={"role": "ADMIN"}
        )
        # Branch
        branch, _ = HospitalBranch.objects.get_or_create(
            hospital=hospital, name=f"{h['city']} Main Branch",
            defaults={"location": {"city": h["city"], "state": h["state"]}}
        )
        # Departments
        for dept_name in ["Cardiology", "ICU", "Emergency", "OPD"]:
            HospitalDepartment.objects.get_or_create(
                hospital=hospital, name=dept_name,
                defaults={"branch": branch}
            )
        # HR user
        hr_user, _ = make_user(f"{h['phone'][:-1]}9", "HOSPITAL_HR")
        HospitalUser.objects.get_or_create(
            user=hr_user,
            defaults={"hospital": hospital, "role": "HR", "branch": branch}
        )
        hospitals.append(hospital)
    p(f"Hospitals: {len(hospitals)} created/found")
    return hospitals


# ── 5. Jobs ───────────────────────────────────────────────────

def seed_jobs(hospitals, specs):
    jobs = []
    job_data = [
        {
            "hospital": hospitals[0],
            "title": "Senior Cardiologist",
            "spec": "Cardiology",
            "job_type": "FULL_TIME",
            "exp": 5, "salary_min": 200000, "salary_max": 350000,
            "urgent": True,
        },
        {
            "hospital": hospitals[0],
            "title": "Locum Anesthesiologist",
            "spec": "Anesthesiology",
            "job_type": "LOCUM",
            "exp": 3, "salary_min": 8000, "salary_max": 15000,
            "urgent": True,
        },
        {
            "hospital": hospitals[1],
            "title": "Consultant Neurologist",
            "spec": "Neurology",
            "job_type": "VISITING",
            "exp": 4, "salary_min": 150000, "salary_max": 250000,
            "urgent": False,
        },
        {
            "hospital": hospitals[1],
            "title": "Pediatric Specialist",
            "spec": "Pediatrics",
            "job_type": "FULL_TIME",
            "exp": 2, "salary_min": 100000, "salary_max": 180000,
            "urgent": False,
        },
    ]
    from django.utils import timezone
    for jd in job_data:
        spec = specs.get(jd["spec"])
        dept = HospitalDepartment.objects.filter(hospital=jd["hospital"]).first()
        hospital_admin = HospitalUser.objects.filter(hospital=jd["hospital"], role="ADMIN").first()
        posted_by = hospital_admin.user if hospital_admin else User.objects.filter(user_type="ADMIN").first()
        mbbs_qual = Qualification.objects.filter(name="MBBS").first()
        job, _ = JobPost.objects.get_or_create(
            hospital=jd["hospital"], title=jd["title"],
            defaults={
                "department": dept,
                "specialty_id": spec.id if spec else None,
                "qualification_ids": [mbbs_qual.id] if mbbs_qual else [],
                "job_type": jd["job_type"],
                "experience_min_years": jd["exp"],
                "salary_min": Decimal(str(jd["salary_min"])),
                "salary_max": Decimal(str(jd["salary_max"])),
                "salary_visibility": "PUBLIC",
                "shift_type": "DAY",
                "location": jd["hospital"].location,
                "description": f"We are looking for a {jd['title']} to join our team.",
                "positions": 2,
                "is_urgent": jd["urgent"],
                "status": "PUBLISHED",
                "posted_by": posted_by,
                "published_at": timezone.now(),
                "closing_date": date.today() + timedelta(days=30),
            }
        )
        jobs.append(job)
    p(f"Jobs: {len(jobs)} created/found")
    return jobs


# ── 6. Applications ───────────────────────────────────────────

def seed_applications(doctors, jobs):
    apps = []
    pairs = [(doctors[0], jobs[0]), (doctors[1], jobs[1]), (doctors[2], jobs[2])]
    for doc, job in pairs:
        app, _ = JobApplication.objects.get_or_create(
            job=job, doctor=doc,
            defaults={"status": "APPLIED", "applied_at": datetime.now()}
        )
        apps.append(app)
    p(f"Applications: {len(apps)} created/found")
    return apps


# ── 7. Connections ────────────────────────────────────────────

def seed_connections(doctors):
    pairs = [(doctors[0], doctors[1]), (doctors[1], doctors[2]), (doctors[0], doctors[2])]
    count = 0
    for sender, receiver in pairs:
        _, created = Connection.objects.get_or_create(
            sender=sender, receiver=receiver,
            defaults={"status": "ACCEPTED"}
        )
        if created:
            count += 1
    p(f"Connections: {count} created")


# ── 8. Posts & Comments ───────────────────────────────────────

def seed_posts(doctors):
    posts_data = [
        {
            "doctor": doctors[0],
            "post_type": "UPDATE",
            "content": "Excited to share that our cardiology department has successfully performed 100+ angioplasties this year. Proud of the team! #Cardiology #Healthcare",
        },
        {
            "doctor": doctors[1],
            "post_type": "CASE",
            "content": "Interesting case: 45-year-old patient presented with difficult airway. Used video laryngoscopy successfully. Always be prepared! #Anesthesiology #ClinicalCase",
            "is_anonymous": True,
            "patient_privacy_confirmed": True,
        },
        {
            "doctor": doctors[2],
            "post_type": "ARTICLE",
            "content": "New research on epilepsy management: Levetiracetam vs Valproate in focal seizures — a comparative analysis from our center. Key finding: similar efficacy, better tolerability with LEV.",
        },
        {
            "doctor": doctors[4],
            "post_type": "UPDATE",
            "content": "Just completed a complex total knee replacement using robotic assistance. The precision is remarkable. #Orthopedics #RoboticSurgery",
        },
    ]
    created_posts = []
    for pd in posts_data:
        post, created = Post.objects.get_or_create(
            author=pd["doctor"],
            post_type=pd["post_type"],
            defaults={
                "posted_by": pd["doctor"].user,
                "content": pd["content"],
                "is_anonymous": pd.get("is_anonymous", False),
                "patient_privacy_confirmed": pd.get("patient_privacy_confirmed", False),
            }
        )
        created_posts.append(post)

    # Likes
    if created_posts:
        for doc in doctors[:3]:
            PostLike.objects.get_or_create(
                post=created_posts[0], liked_by=doc.user,
                defaults={"doctor": doc}
            )
        PostLike.objects.get_or_create(
            post=created_posts[2], liked_by=doctors[0].user,
            defaults={"doctor": doctors[0]}
        )

    # Comments
    if created_posts:
        PostComment.objects.get_or_create(
            post=created_posts[0], author=doctors[1].user,
            defaults={"content": "Congratulations! Remarkable achievement for the team."}
        )
        PostComment.objects.get_or_create(
            post=created_posts[0], author=doctors[2].user,
            defaults={"content": "Inspiring work! Keep it up."}
        )
        PostComment.objects.get_or_create(
            post=created_posts[2], author=doctors[0].user,
            defaults={"content": "Great research! We had similar findings at our center."}
        )

    p(f"Posts: {len(created_posts)} created/found, with likes and comments")
    return created_posts


# ── 9. Availability ───────────────────────────────────────────

def seed_availability(doctors):
    avail_data = [
        {"doctor": doctors[1], "type": "LOCUM", "city": "Mumbai", "state": "Maharashtra", "min_pay": 8000},
        {"doctor": doctors[4], "type": "VISITING", "city": "Jaipur", "state": "Rajasthan", "min_pay": 5000},
    ]
    for ad in avail_data:
        avail, created = DoctorAvailability.objects.get_or_create(
            doctor=ad["doctor"],
            availability_type=ad["type"],
            defaults={
                "available_from": date.today(),
                "available_until": date.today() + timedelta(days=30),
                "preferred_location": {"city": ad["city"], "state": ad["state"]},
                "preferred_radius_km": 50,
                "minimum_compensation": Decimal(str(ad["min_pay"])),
                "is_active": True,
            }
        )
        if created:
            AvailabilitySlot.objects.get_or_create(
                availability=avail,
                slot_date=date.today() + timedelta(days=3),
                defaults={"start_time": "09:00", "end_time": "17:00", "is_booked": False}
            )
    p(f"Availability: {len(avail_data)} records created/found")


# ── 10. Shift Requirements ────────────────────────────────────

def seed_shifts(hospitals, specs):
    spec = specs.get("Anesthesiology")
    hospital_admin = HospitalUser.objects.filter(hospital=hospitals[0], role="ADMIN").first()
    created_by = hospital_admin.user if hospital_admin else User.objects.filter(user_type="ADMIN").first()
    mbbs_qual = Qualification.objects.filter(name="MBBS").first()
    req, _ = ShiftRequirement.objects.get_or_create(
        hospital=hospitals[0],
        requirement_date=date.today() + timedelta(days=2),
        defaults={
            "specialty_id": spec.id if spec else None,
            "qualification_ids": [mbbs_qual.id] if mbbs_qual else [],
            "start_time": "08:00",
            "end_time": "20:00",
            "doctors_required": 2,
            "compensation": Decimal("12000"),
            "urgency": "URGENT",
            "location": hospitals[0].location,
            "status": "OPEN",
            "notes": "ICU coverage needed urgently",
            "created_by": created_by,
        }
    )
    p("Shift requirements: 1 created/found")


# ── 11. Communities ───────────────────────────────────────────

def seed_communities(doctors, specs):
    communities_data = [
        {"name": "Cardiology Network India", "spec": "Cardiology"},
        {"name": "Neurology Forum", "spec": "Neurology"},
        {"name": "Anesthesia & Critical Care", "spec": "Anesthesiology"},
    ]
    for cd in communities_data:
        spec = specs.get(cd["spec"])
        community, _ = Community.objects.get_or_create(
            name=cd["name"],
            defaults={
                "description": f"Professional community for {cd['spec']} specialists.",
                "specialty_id": spec.id if spec else None,
                "is_active": True,
            }
        )
        # Add first 2 doctors as members
        for doc in doctors[:2]:
            CommunityMember.objects.get_or_create(community=community, user=doc.user)
    p(f"Communities: {len(communities_data)} created/found")


# ── 12. Notifications ─────────────────────────────────────────

def seed_notifications(doctors):
    notif_data = [
        {"user": doctors[0].user, "type": "CONNECTION_REQUEST", "title": "New connection request", "body": "Dr. Priya Mehta wants to connect with you."},
        {"user": doctors[1].user, "type": "JOB_MATCH", "title": "New job match", "body": "A new Locum Anesthesiologist position matches your profile."},
        {"user": doctors[2].user, "type": "POST_LIKE", "title": "Someone liked your post", "body": "Dr. Arjun Sharma liked your article."},
    ]
    for nd in notif_data:
        Notification.objects.get_or_create(
            user=nd["user"], type=nd["type"], title=nd["title"],
            defaults={"body": nd["body"], "is_read": False}
        )
    p(f"Notifications: {len(notif_data)} created/found")


# ── Main ──────────────────────────────────────────────────────

def main():
    print("\n DocConnect -- Test Data Seed")
    print("=" * 45)

    print("\n[1] Master Data")
    specs, quals, council = seed_masters()

    print("\n[2] Admin Users")
    seed_admins()

    print("\n[3] Doctors")
    doctors = seed_doctors(specs, council)

    print("\n[4] Hospitals")
    hospitals = seed_hospitals()

    print("\n[5] Jobs")
    jobs = seed_jobs(hospitals, specs)

    print("\n[6] Applications")
    seed_applications(doctors, jobs)

    print("\n[7] Connections")
    seed_connections(doctors)

    print("\n[8] Posts & Comments")
    seed_posts(doctors)

    print("\n[9] Availability")
    seed_availability(doctors)

    print("\n[10] Shift Requirements")
    seed_shifts(hospitals, specs)

    print("\n[11] Communities")
    seed_communities(doctors, specs)

    print("\n[12] Notifications")
    seed_notifications(doctors)

    print("[OK] Seed complete!\n")
    print("Test Credentials (password for all: Test@1234)")
    print("-" * 45)
    print(f"{'Role':<20} {'Phone':<15}")
    print("-" * 45)
    print(f"{'Super Admin':<20} {'9999999999':<15}")
    print(f"{'Platform Admin':<20} {'9999999998':<15}")
    print(f"{'Doctor (Verified)':<20} {'9000000001':<15}  Dr. Arjun Sharma")
    print(f"{'Doctor (Verified)':<20} {'9000000002':<15}  Dr. Priya Mehta")
    print(f"{'Doctor (Verified)':<20} {'9000000003':<15}  Dr. Rahul Verma")
    print(f"{'Doctor (Unverified)':<20} {'9000000004':<15}  Dr. Sneha Patel")
    print(f"{'Doctor (Verified)':<20} {'9000000005':<15}  Dr. Vikram Singh")
    print(f"{'Hospital Admin':<20} {'8000000001':<15}  Apollo Delhi")
    print(f"{'Hospital Admin':<20} {'8000000002':<15}  Fortis Mumbai")
    print(f"{'Hospital HR':<20} {'8000000009':<15}  Apollo HR")
    print(f"{'Hospital HR':<20} {'8000000029':<15}  Fortis HR")
    print("-" * 45)
    print("\nAPI Testing:")
    print("  POST /api/v1/auth/login/  body: {phone, password}")
    print("  GET  /api/v1/feed/        (requires Bearer token)")
    print("  GET  /api/v1/feed/home/   (requires Bearer token)")


if __name__ == '__main__':
    main()
