import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag

FILENAMES = {
    'ingredients': 'ingredients.csv',
    'tags': 'tags.csv'
}


class Command(BaseCommand):
    help = 'Import data'

    def handle(self, *args, **options):
        try:
            csvfile = open(f'data/{FILENAMES["ingredients"]}',
                           newline='',
                           encoding='utf-8')
        except FileNotFoundError:
            self.stderr.write('Не удалось открыть файл '
                              f'data/{FILENAMES["ingredients"]}')
        else:
            with csvfile:
                reader = csv.reader(csvfile)
                self.stdout.write('Загрузка данных из файла '
                                  f'{FILENAMES["ingredients"]} в БД началась.')
                for name, measurement_unit in reader:
                    if not Ingredient.objects.filter(name=name).exists():
                        Ingredient.objects.create(
                            name=name,
                            measurement_unit=measurement_unit
                        )
                self.stdout.write('Загрузка данных из файла '
                                  f'{FILENAMES["ingredients"]} '
                                  'в БД закончена.')

        try:
            csvfile = open(f'data/{FILENAMES["tags"]}',
                           newline='',
                           encoding='utf-8')
        except FileNotFoundError:
            self.stderr.write('Не удалось открыть файл '
                              f'data/{FILENAMES["tags"]}')
        else:
            with csvfile:
                reader = csv.reader(csvfile)
                self.stdout.write('Загрузка данных из файла '
                                  f'{FILENAMES["tags"]} в БД началась.')
                for name, color, slug in reader:
                    if not Tag.objects.filter(slug=slug).exists():
                        Tag.objects.create(
                            name=name,
                            color=color,
                            slug=slug
                        )
                self.stdout.write('Загрузка данных из файла '
                                  f'{FILENAMES["tags"]} в БД закончена.')
