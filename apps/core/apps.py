from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    label = 'core'

    def ready(self):
        # Explicitly import all admin modules so docconnect_admin (custom AdminSite)
        # gets all models registered — Django auto-discovery only works for default site.
        import apps.accounts.admin       # noqa
        import apps.doctors.admin        # noqa
        import apps.hospitals.admin      # noqa
        import apps.jobs.admin           # noqa
        import apps.availability.admin   # noqa
        import apps.shifts.admin         # noqa
        import apps.messaging.admin      # noqa
        import apps.notifications.admin  # noqa
        import apps.core.admin           # noqa
