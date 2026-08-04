#!/usr/bin/env python
"""
Rebuild full-text search vectors for all searchable models.
Run after bulk data imports or if search is returning stale results.
Usage: python scripts/update_search_vectors.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docconnect_backend.settings.development')

import django
django.setup()

from django.contrib.postgres.search import SearchVector


def update_user_vectors():
    from apps.accounts.models import User
    User.objects.update(
        search_vector=SearchVector('phone', weight='A') + SearchVector('email', weight='B')
    )
    count = User.objects.count()
    print(f"[OK] Users search vectors updated ({count} records)")


def update_doctor_vectors():
    from apps.doctors.models import DoctorProfile
    DoctorProfile.objects.update(
        search_vector=(
            SearchVector('first_name', weight='A') +
            SearchVector('last_name', weight='A') +
            SearchVector('headline', weight='B') +
            SearchVector('about', weight='C')
        )
    )
    count = DoctorProfile.objects.count()
    print(f"[OK] DoctorProfile search vectors updated ({count} records)")


def update_job_vectors():
    from apps.jobs.models import JobPost
    JobPost.objects.update(
        search_vector=(
            SearchVector('title', weight='A') +
            SearchVector('description', weight='B') +
            SearchVector('responsibilities', weight='C')
        )
    )
    count = JobPost.objects.count()
    print(f"[OK] JobPost search vectors updated ({count} records)")


if __name__ == '__main__':
    print("Rebuilding search vectors...")
    update_user_vectors()
    update_doctor_vectors()
    update_job_vectors()
    print("Done.")
