import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Import data'

    def handle(self, *args, **options):
        with open(
            'data/ingredients.csv',
            newline='',
            encoding='utf-8'
        ) as csvfile:
            reader = csv.reader(csvfile)
            for name, measurement_unit in reader:
                if not Ingredient.objects.filter(name=name).exists():
                    Ingredient.objects.create(
                        name=name,
                        measurement_unit=measurement_unit
                    )
