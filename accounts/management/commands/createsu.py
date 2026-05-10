from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = "Create superuser if not exists"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        first_name = os.environ.get("DJANGO_SUPERUSER_FIRSTNAME", "Admin")
        last_name = os.environ.get("DJANGO_SUPERUSER_LASTNAME", "User")

        if not email or not password:
            self.stdout.write(self.style.WARNING("Env vars missing, skipping."))
            return

        # Email OR username dono mein se koi bhi exist kare toh skip karo
        if User.objects.filter(email=email).exists() or User.objects.filter(username=username).exists():
            self.stdout.write("Superuser already exists, skipping.")
            return

        User.objects.create_superuser(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password
        )
        self.stdout.write(self.style.SUCCESS("Superuser created"))
