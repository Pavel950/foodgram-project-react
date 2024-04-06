import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag

FILES = (
    {
        'filename': 'ingredients.csv',
        'header': ('name', 'measurement_unit'),
        'model': Ingredient
    },
    {
        'filename': 'tags.csv',
        'header': ('name', 'color', 'slug'),
        'model': Tag
    }
)


class Command(BaseCommand):
    help = 'Import data'

    def handle(self, *args, **options):
        for file in FILES:
            try:
                csvfile = open(f'data/{file["filename"]}',
                               newline='',
                               encoding='utf-8')
            except FileNotFoundError:
                self.stderr.write('Не удалось открыть файл '
                                  f'data/{file["filename"]}')
            else:
                with csvfile:
                    reader = csv.reader(csvfile)
                    self.stdout.write('Загрузка данных из файла '
                                      f'{file["filename"]} в БД началась.')
                    for row in reader:
                        single_data_dict = {
                            key: value for key, value in zip(
                                file['header'],
                                row
                            )
                        }
                        file['model'].objects.get_or_create(**single_data_dict)
                    self.stdout.write('Загрузка данных из файла '
                                      f'{file["filename"]} в БД закончена.')
