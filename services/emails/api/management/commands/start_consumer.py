from django.core.management.base import BaseCommand

from microservices.consumer import main


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        main()
