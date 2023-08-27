import csv
import os

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from food.models import Ingredient, Tag

FILES = {
    Ingredient: 'ingredients.csv',
    Tag: 'tags.csv',
}


class Command(BaseCommand):
    """Загрузка данных ингредиентов и тегов."""

    def handle(self, *args, **options):
        parent_directory_backend = os.getcwd()
        for models, files in FILES.items():
            path_csv_files = os.path.join(
                parent_directory_backend,
                # 'backend',  # if local dev / no in containers - discommend
                'data',
                files,
            )
            with open(file=path_csv_files, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        model_write, create = models.objects.get_or_create(
                            **row,
                        )
                        if not create:
                            model_write = models.objects.update(**row)
                            print('данные обновлены')
                        model_write.save()
                    except IntegrityError as err:
                        print(
                            f'{err} - данные в '
                            f'таблице {models.__name__} '
                            f'или уже существуют, или не валидные',
                        )
        print('Работа завершена')
