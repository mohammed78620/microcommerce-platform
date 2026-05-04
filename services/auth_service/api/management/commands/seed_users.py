# auth_service/management/commands/seed_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Seed initial users"

    def handle(self, *args, **kwargs):
        users = [
            {
                "username": "john_doe",
                "email": "johndoe@example.com",
                "password": "password123",
                "first_name": "John",
                "last_name": "Doe",
                "is_staff": False,
            },
            {
                "username": "root",
                "email": "admin@example.com",
                "password": "root",
                "first_name": "Admin",
                "last_name": "User",
                "is_staff": True,
                "is_superuser": True,
            },
        ]

        for user_data in users:
            if not User.objects.filter(username=user_data["username"]).exists():
                User.objects.create_user(**user_data)
                self.stdout.write(self.style.SUCCESS(f'Created user: {user_data["username"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'User already exists: {user_data["username"]}'))
