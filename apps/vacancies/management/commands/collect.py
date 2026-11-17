import asyncio
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.vacancies.services.collector import collect
from apps.vacancies.services.sources import default_sources
from apps.vacancies.services.storage import known_details, save_vacancies


class Command(BaseCommand):
    help = "Собирает вакансии из всех источников и записывает их в базу."

    def add_arguments(self, parser):
        parser.add_argument("--query", default="python", help="поисковый запрос (по умолчанию: python)")
        parser.add_argument("--pages", type=int, default=1, help="сколько страниц брать с каждого источника")
        parser.add_argument("--details", action="store_true", help="загружать полные описания вакансий")
        parser.add_argument("--sequential", action="store_true", help="опрашивать источники по очереди")
        parser.add_argument("--no-save", action="store_true", help="не записывать в базу, только показать отчёт")
        parser.add_argument("--out", type=Path, help="дополнительно сохранить собранное в файл JSON")

    def handle(self, *args, **options):
        result = asyncio.run(
            collect(
                default_sources(),
                options["query"],
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

        if options["out"]:
            out: Path = options["out"]
            out.parent.mkdir(parents=True, exist_ok=True)
            payload = [v.to_dict() for v in result.vacancies]
            out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            self.stdout.write(f"сохранено в {out}")
