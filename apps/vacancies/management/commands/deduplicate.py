from django.core.management.base import BaseCommand

from apps.vacancies.models import Vacancy
from apps.vacancies.services.dedup.normalize import text_of
from apps.vacancies.services.storage import deduplicate


class Command(BaseCommand):
    help = "Заново размечает дубликаты среди всех вакансий в базе."

    def handle(self, *args, **options):
        vacancies = list(Vacancy.objects.all())
        for vacancy in vacancies:
            vacancy.search_text = text_of(vacancy)
        Vacancy.objects.bulk_update(vacancies, ["search_text"], batch_size=200)

        groups, duplicates = deduplicate()
        total = len(vacancies)
        self.stdout.write(
            self.style.SUCCESS(
                f"вакансий: {total}, дубликатов: {duplicates} в {groups} группах, "
                f"к показу: {total - duplicates}"
            )
        )
