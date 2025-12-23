import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to wait for database availability"""

    def handle(self, *args, **options):
        self.stdout.write("Waiting for the database to be available...")
        db_conn = None
        while not db_conn:
            try:
                db_conn = connections["default"]
                db_conn.ensure_connection()
            except OperationalError:
                self.stdout.write("Database is unavailable, waiting for 1 second...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database available!"))
