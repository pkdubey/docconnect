#!/usr/bin/env python
"""
Create a DocConnect admin user.

DEVELOPMENT usage (default credentials — NEVER use in production):
    python scripts/create_admin.py

PRODUCTION usage (always pass explicit credentials):
    python scripts/create_admin.py --phone <phone> --password <strong_password> --super

WARNING: The default phone/password below are for LOCAL DEVELOPMENT ONLY.
         Production deployments MUST supply credentials via CLI args or
         environment variables. The deployment pipeline must NOT call this
         script with default credentials.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docconnect_backend.settings.development')

import django
django.setup()

_DEV_PHONE = '9999999999'
_DEV_PASSWORD = 'admin123'


def create_admin(phone: str, password: str, is_super: bool = False):
    from apps.accounts.models import User

    env = os.environ.get('DJANGO_ENV', 'development')

    # Block predictable dev credentials in production
    if env == 'production' and phone == _DEV_PHONE:
        print('[ERROR] Default development phone cannot be used in production.')
        sys.exit(1)
    if env == 'production' and password == _DEV_PASSWORD:
        print('[ERROR] Default development password cannot be used in production.')
        sys.exit(1)

    if env != 'development':
        print(f'[INFO] Creating admin in environment: {env}')

    if User.objects.filter(phone=phone).exists():
        user = User.objects.get(phone=phone)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.user_type = 'ADMIN'
        user.is_super_admin = is_super
        user.status = 'ACTIVE'
        user.save()
        print(f'[OK] Updated existing user {phone} — is_super_admin={is_super}')
    else:
        user = User.objects.create_superuser(phone=phone, user_type='ADMIN', password=password)
        user.is_super_admin = is_super
        user.save(update_fields=['is_super_admin'])
        print(f'[OK] Admin created — phone: {phone} — is_super_admin={is_super}')

    print(f'     Login at: http://localhost:8000/admin/')
    if env == 'development':
        print('     [DEV ONLY] Change this password before any non-local use.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create DocConnect admin user')
    # Defaults are DEV ONLY — production must always pass explicit values
    parser.add_argument('--phone', default=_DEV_PHONE,
                        help='[DEV DEFAULT: 9999999999] — override in production')
    parser.add_argument('--password', default=_DEV_PASSWORD,
                        help='[DEV DEFAULT: admin123] — override in production')
    parser.add_argument('--super', dest='is_super', action='store_true',
                        help='Grant Super Admin privileges (is_super_admin=True)')
    args = parser.parse_args()
    create_admin(args.phone, args.password, args.is_super)
