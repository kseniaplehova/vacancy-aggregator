from django.core.management.base import BaseCommand, CommandError

from apps.vacancies.models import Vacancy
from apps.vacancies.services.dedup import all_matchers
from apps.vacancies.services.dedup.evaluation import evaluate

AGGREGATOR = "belmeta.com"
ORIGIN = "rabota.by"


class Command(BaseCommand):
    help = (
        "Сравнивает методы дедупликации на эталонных парах: вакансия Belmeta "
        "и та вакансия rabota.by, на которую Belmeta сама ссылается как на первоисточник."
    )

    def handle(self, *args, **options):
        originals = list(Vacancy.objects.filter(source=ORIGIN).order_by("id"))
        index_by_url = {vacancy.url: index for index, vacancy in enumerate(originals)}

        # берём только те вакансии агрегатора, чей первоисточник есть в базе:
        # для остальных правильный ответ «дубликата нет» проверить нечем
        copies, gold = [], set()
        for vacancy in Vacancy.objects.filter(source=AGGREGATOR, origin=ORIGIN).order_by("id"):
            if vacancy.origin_url in index_by_url:
                gold.add((len(copies), index_by_url[vacancy.origin_url]))
                copies.append(vacancy)

        if not gold:
            raise CommandError(
                "Эталонных пар нет. Сначала соберите вакансии с описаниями: "
                "python manage.py collect --pages 10 --details"
            )

        self.stdout.write(
            f"{AGGREGATOR}: {len(copies)} вакансий, {ORIGIN}: {len(originals)} вакансий, "
            f"пар для сравнения: {len(copies) * len(originals)}, из них дубликатов: {len(gold)}\n"
        )
        header = f"{'метод':<40} {'порог':>5} {'точность':>9} {'полнота':>8} {'F1':>6} {'подготовка, с':>14} {'сравнение, с':>13}"
        self.stdout.write(header)
        self.stdout.write("-" * len(header))
        for matcher in all_matchers():
            result = evaluate(matcher, copies, originals, gold)
            best = result.best
            self.stdout.write(
                f"{result.method:<40} {best.threshold:>5.2f} {best.precision:>9.3f} {best.recall:>8.3f} "
                f"{best.f1:>6.3f} {result.prepare_seconds:>14.3f} {result.compare_seconds:>13.3f}"
            )
