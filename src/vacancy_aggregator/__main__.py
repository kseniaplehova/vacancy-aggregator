import argparse
import asyncio
import json
from pathlib import Path

from .collector import collect
from .sources import default_sources


def main() -> None:
    parser = argparse.ArgumentParser(prog="vacancy_aggregator", description="Сбор вакансий из источников")
    parser.add_argument("--query", default="python", help="поисковый запрос (по умолчанию: python)")
    parser.add_argument("--pages", type=int, default=1, help="сколько страниц брать с каждого источника")
    parser.add_argument("--sequential", action="store_true", help="опрашивать источники по очереди")
    parser.add_argument("--details", action="store_true", help="загружать полные описания вакансий")
    parser.add_argument("--out", type=Path, help="файл JSON, куда сохранить собранное")
    args = parser.parse_args()

    result = asyncio.run(
        collect(
            default_sources(),
            args.query,
            args.pages,
            concurrent=not args.sequential,
            details=args.details,
        )
    )

    for report in result.reports:
        status = f"ошибка: {report.error}" if report.error else f"{len(report.vacancies)} вакансий"
        print(f"{report.source:<32} {report.seconds:6.2f} с  {status}")
    print(f"{'всего':<32} {result.seconds:6.2f} с  {len(result.vacancies)} вакансий")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        payload = [v.to_dict() for v in result.vacancies]
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"сохранено в {args.out}")


if __name__ == "__main__":
    main()
