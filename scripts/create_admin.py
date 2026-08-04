#!/usr/bin/env python
"""
Create a superadmin user.
Usage: python scripts/create_admin.py
       python scripts/create_admin.py --phone 9999999999 --password admin123
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docconnect_backend.settings.development')

import django
django.setup()


def create_admin(phone: str, password: str):
    from apps.accounts.models import User

    if User.objects.filter(phone=phone).exists():
        user = User.objects.get(phone=phone)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.user_type = 'ADMIN'
        user.status = 'ACTIVE'
        user.save()
        print(f"[OK] Updated existing user {phone} as superadmin")
    else:
        User.objects.create_superuser(phone=phone, user_type='ADMIN', password=password)
        print(f"[OK] Superadmin created — phone: {phone}")

    print(f"     Login at: http://localhost:8000/admin/")
    print(f"     Phone:    {phone}")
    print(f"     Password: {password}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create DocConnect superadmin')
    parser.add_argument('--phone', default='9999999999')
    parser.add_argument('--password', default='admin123')
    args = parser.parse_args()
    create_admin(args.phone, args.password)
