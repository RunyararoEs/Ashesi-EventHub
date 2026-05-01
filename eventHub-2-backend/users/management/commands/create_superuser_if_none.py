from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates a superuser if none exists'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        # Delete existing admin to recreate with correct role
        User.objects.filter(email='admin@eventhub.com').delete()
        User.objects.create_superuser(
            email='admin@eventhub.com',
            username='SystemAdmin',
            password='Admin1234!',
            role='system_admin',
        )
        self.stdout.write('Superuser created successfully.')