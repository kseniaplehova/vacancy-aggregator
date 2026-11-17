import asyncio
import json
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.vacancies.services.collector import collect
from apps.vacancies.services.sources import default_sources
from apps.vacancies.services.storage import deduplicate, known_details, save_vacancies

#: пауза между поисковыми запросами, чтобы не нагружать сайты
PAUSE_BETWEEN_QUERIES = 5


class Command(BaseCommand):
    help = "Собирает вакансии из всех источников, записывает их в базу и размечает дубликаты."

    def add_arguments(self, parser):
        parser.add_argument(
            "--query",
            action="append",
            help="поисковый запрос; можно указать несколько раз. "
            "Без него берутся запросы из настройки COLLECT_QUERIES",
        )
        parser.add_argument("--pages", type=int, default=1, help="сколько страниц брать с каждого источника")
        parser.add_argument("--details", action="store_true", help="загружать полные описания вакансий")
        parser.add_argument("--sequential", action="store_true", help="опрашивать источники по очереди")
        parser.add_argument("--no-save", action="store_true", help="не записывать в базу, только показать отчёт")
        parser.add_argument("--out", type=Path, help="дополнительно сохранить собранное в файл JSON")

    def handle(self, *args, **options):
        queries = options["query"] or settings.COLLECT_QUERIES
        collected = []
        for number, query in enumerate(queries):
            if number:
                time.sleep(PAUSE_BETWEEN_QUERIES)
            if len(queries) > 1:
                self.stdout.write(self.style.MIGRATE_HEADING(f"Запрос «{query}»"))
            collected.extend(self.collect_query(query, options))

        if not options["no_save"]:
            groups, duplicates = deduplicate()
            self.stdout.write(self.style.SUCCESS(f"дубликаты: {duplicates} записей объединено в {groups} групп"))

        if options["out"]:
            out: Path = options["out"]
            out.parent.mkdir(parents=True, exist_ok=True)
            payload = [vacancy.to_dict() for vacancy in collected]
            out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            self.stdout.write(f"сохранено в {out}")

    def collect_query(self, query, options):
        result = asyncio.run(
            collect(
                default_sources(),
                query,
                options["pages"],
                concurrent=not options["sequential"],
                details=options["details"],
                # страницы вакансий, уже загруженные в прошлые разы, повторно не запрашиваются
                known=known_details() if options["details"] else None,
            )
        )

        for report in result.reports:
            if report.error:
                line = self.style.ERROR(f"ошибка: {report.error}")
            else:
                line = f"{len(report.vacancies)} вакансий"
            if report.detail_errors:
                reasons = ", ".join(f"{reason}: {count}" for reason, count in report.detail_errors.items())
                line += self.style.WARNING(f"  (без описания — {reasons})")
            self.stdout.write(f"{report.source:<32} {report.seconds:6.2f} с  {line}")
        self.stdout.write(f"{'всего':<32} {result.seconds:6.2f} с  {len(result.vacancies)} вакансий")

        if not options["no_save"]:
            added, updated = save_vacancies(result.vacancies)
            self.stdout.write(self.style.SUCCESS(f"в базе: {added} новых, {updated} обновлено"))
        return result.vacancies
