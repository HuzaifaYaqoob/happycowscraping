



from django.core.management.base import BaseCommand

import csv


from djangoscraping.crobjob import scrapinghappycow
class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def handle(self, *args, **options):
        scrapinghappycow()

        self.stdout.write(self.style.SUCCESS('Successfully added scrapinghappycow'))

