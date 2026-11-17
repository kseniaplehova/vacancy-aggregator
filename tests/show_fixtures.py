"""Печатает, что парсеры достают из сохранённых страниц: python tests/show_fixtures.py"""
from pathlib import Path

from vacancy_aggregator.sources import ALL_SOURCES

FIXTURES = Path(__file__).parent / "fixtures"

for cls in ALL_SOURCES:
    source = cls()
    html = (FIXTURES / f"{cls.__module__.rsplit('.', 1)[-1]}.html").read_text(encoding="utf-8")
    print(f"== {source.name}")
    for v in source.parse(html):
        print(f"  {v.source_id} | {v.title} | {v.company} | {v.city} | {v.salary} | {v.published}")
        print(f"    {v.url}")
        print(f"    {(v.description or '')[:80]}")
