#!/usr/bin/env python
"""
Seed master data: specializations, qualifications, medical councils
Run: python scripts/seed_data.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docconnect_backend.settings.development')
django.setup()

from apps.core.models import Specialization, Qualification, Council

SPECIALIZATIONS = [
    "General Medicine", "General Surgery", "Pediatrics", "Obstetrics & Gynecology",
    "Orthopedics", "Cardiology", "Neurology", "Dermatology", "Psychiatry",
    "Radiology", "Anesthesiology", "Ophthalmology", "ENT", "Urology",
    "Nephrology", "Gastroenterology", "Pulmonology", "Endocrinology",
    "Oncology", "Emergency Medicine",
]

QUALIFICATIONS = ["MBBS", "MD", "MS", "DM", "MCh", "DNB", "BDS", "MDS", "BAMS", "BHMS"]

COUNCILS = [
    {"name": "Medical Council of India", "short": "MCI"},
    {"name": "National Medical Commission", "short": "NMC"},
    {"name": "Maharashtra Medical Council", "short": "MMC"},
    {"name": "Delhi Medical Council", "short": "DMC"},
    {"name": "Karnataka Medical Council", "short": "KMC"},
    {"name": "Tamil Nadu Medical Council", "short": "TNMC"},
]


def seed():
    spec_created = sum(1 for name in SPECIALIZATIONS if Specialization.objects.get_or_create(name=name)[1])
    qual_created = sum(1 for name in QUALIFICATIONS if Qualification.objects.get_or_create(name=name)[1])
    council_created = sum(1 for c in COUNCILS if Council.objects.get_or_create(name=c['name'], defaults={'short': c['short']})[1])

    print("[OK] Master data seeded")
    print(f"   - Specializations: {spec_created} created ({len(SPECIALIZATIONS)} total)")
    print(f"   - Qualifications:  {qual_created} created ({len(QUALIFICATIONS)} total)")
    print(f"   - Councils:        {council_created} created ({len(COUNCILS)} total)")


if __name__ == '__main__':
    seed()
