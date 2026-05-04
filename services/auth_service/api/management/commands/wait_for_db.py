import time
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Waits for database to be ready"

    def handle(self, *args, **kwargs):
        self.stdout.write("Waiting for database...")
        db_ready = False
        while not db_ready:
            try:
                connection.ensure_connection()
                db_ready = True
            except OperationalError:
                self.stdout.write("Database not ready, waiting 1 second...")
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS("Database ready!"))
