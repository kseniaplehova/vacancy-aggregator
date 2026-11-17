import asyncio
import time
from dataclasses import dataclass, field

import httpx

from .models import Vacancy
from .sources import Source

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
    "Accept-Language": "ru,en;q=0.8",
}


@dataclass
class SourceReport:
    """Чем закончился опрос одного источника."""

    source: str
    seconds: float
    vacancies: list[Vacancy] = field(default_factory=list)
    error: str | None = None


@dataclass
class CollectResult:
    reports: list[SourceReport]
    seconds: float

    @property
    def vacancies(self) -> list[Vacancy]:
        return [v for report in self.reports for v in report.vacancies]


async def _poll(source: Source, client: httpx.AsyncClient, query: str, pages: int) -> SourceReport:
    """Опрашивает источник; ошибка не выбрасывается, а попадает в отчёт."""
    started = time.perf_counter()
    try:
        vacancies = await source.fetch(client, query, pages)
        error = None
    except Exception as exc:  # сбой одного источника не должен ронять остальные
        vacancies = []
        error = f"{type(exc).__name__}: {exc}"
    return SourceReport(source.name, time.perf_counter() - started, vacancies, error)


async def collect(
    sources: list[Source], query: str, pages: int = 1, *, concurrent: bool = True
) -> CollectResult:
    """Собирает вакансии со всех источников.

    ``concurrent=False`` опрашивает источники по очереди — этот режим нужен
    для сравнения с асинхронным в экспериментах.
    """
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        # время считается без создания клиента: оно одинаково в обоих режимах
        started = time.perf_counter()
        if concurrent:
            reports = await asyncio.gather(*(_poll(s, client, query, pages) for s in sources))
        else:
            reports = [await _poll(s, client, query, pages) for s in sources]
        seconds = time.perf_counter() - started
    return CollectResult(list(reports), seconds)
