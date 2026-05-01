from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = 'notifications'

    def ready(self):
        """
        Import signals when the app loads so Django registers all
        the receivers. Without this, the @receiver decorators in
        signals.py are never executed and nothing gets connected.
        """
        import notifications.signals  # noqa: F401
