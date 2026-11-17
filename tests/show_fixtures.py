"""Печатает, что парсеры достают из сохранённых страниц: python tests/show_fixtures.py"""
from pathlib import Path

from vacancy_aggregator.sources import Belmeta, DevBy, Greenhouse, Lever, MyJob, RabotaBy

FIXTURES = Path(__file__).parent / "fixtures"
SOURCES = {
    "rabota_by.html": RabotaBy(),
    "devby.html": DevBy(),
    "belmeta.html": Belmeta(),
    "myjob.html": MyJob(),
    "greenhouse.json": Greenhouse("tripledotstudios"),
    "lever.json": Lever("idt", company="IDT"),
}

for file, source in SOURCES.items():
    print(f"== {source.name}")
    vacancies = source.parse((FIXTURES / file).read_text(encoding="utf-8"))
    detail = FIXTURES / file.replace(".html", "_detail.html")
    if detail.exists() and detail != FIXTURES / file:
        print(f"  (описание первой вакансии взято из {detail.name})")
        source.parse_detail(detail.read_text(encoding="utf-8"), vacancies[0])
    for v in vacancies:
        print(f"  {v.source_id} | {v.title} | {v.company} | {v.city} | {v.salary} | {v.published} | {v.origin}")
        print(f"    {v.url}")
        print(f"    {len(v.description or '')} симв.: {(v.description or '')[:90]!r}")
