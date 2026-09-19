from .base import *

DEBUG = True

# Separate test database — never touches the real docconnect_db
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('TEST_DB_NAME', default='docconnect_test'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='Pkdubey@00'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'TEST': {
            'NAME': env('TEST_DB_NAME', default='docconnect_test'),
        },
    }
}

# Dummy cache — no Redis needed during tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable SMS in tests
SMS_PROVIDER = 'dummy'
SMS_API_KEY = 'test'

# Fast password hashing in tests
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Disable Celery task execution in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
