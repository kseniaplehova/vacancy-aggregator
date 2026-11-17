import asyncio
import time
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field

import httpx

from .schemas import RawVacancy
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
    vacancies: list[RawVacancy] = field(default_factory=list)
    error: str | None = None
    #: вакансии, оставшиеся без полного описания: причина → количество
    detail_errors: dict[str, int] = field(default_factory=dict)


@dataclass
class CollectResult:
    reports: list[SourceReport]
    seconds: float

    @property
    def vacancies(self) -> list[RawVacancy]:
        return [v for report in self.reports for v in report.vacancies]


async def _poll(
    source: Source,
    client: httpx.AsyncClient,
    query: str,
    pages: int,
    details: bool,
    skip_details: Collection[str],
) -> SourceReport:
    """Опрашивает источник; ошибка не выбрасывается, а попадает в отчёт."""
    started = time.perf_counter()
    try:
        vacancies = await source.fetch(client, query, pages, details=details, skip_details=skip_details)
        error = None
    except Exception as exc:  # сбой одного источника не должен ронять остальные
        vacancies = []
        error = f"{type(exc).__name__}: {exc}"
    detail_errors = dict(getattr(source, "detail_errors", {}))
    return SourceReport(source.name, time.perf_counter() - started, vacancies, error, detail_errors)


async def collect(
    sources: list[Source],
    query: str,
    pages: int = 1,
    *,
    concurrent: bool = True,
    details: bool = False,
    known: Mapping[str, Collection[str]] | None = None,
) -> CollectResult:
    """Собирает вакансии со всех источников.

    ``concurrent=False`` опрашивает источники по очереди — этот режим нужен
    для сравнения с асинхронным в экспериментах. ``details=True`` дополнительно
    загружает страницу каждой вакансии ради полного описания. ``known`` —
    номера вакансий по источникам, описание которых уже есть: их страницы
    не запрашиваются повторно.
    """
    known = known or {}
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        # время считается без создания клиента: оно одинаково в обоих режимах
        started = time.perf_counter()
        polls = [_poll(s, client, query, pages, details, known.get(s.name, ())) for s in sources]
        if concurrent:
            reports = await asyncio.gather(*polls)
        else:
            reports = [await poll for poll in polls]
        seconds = time.perf_counter() - started
    return CollectResult(list(reports), seconds)
