import asyncio
import json
import re
from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Collection

import httpx
from bs4 import BeautifulSoup, Tag

from ..schemas import RawVacancy

#: города и названия страны, по которым вакансию считаем белорусской
BELARUS = re.compile(r"belarus|minsk|brest|grodno|gomel|vitebsk|mogilev|беларус|минск", re.IGNORECASE)
BLOCK_TAGS = ["p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr"]


def text_of(tag: Tag | None, sep: str = " ") -> str | None:
    """Текст элемента без лишних пробелов; None, если элемента или текста нет.

    ``sep`` вставляется между вложенными элементами. Пустой нужен там, где сайт
    подсвечивает слова запроса тегами внутри слова: «<b>Python</b>-разработчик».
    """
    if tag is None:
        return None
    return " ".join(tag.get_text(sep).split()) or None


def html_to_text(html: str | None) -> str | None:
    """Убирает разметку из описания вакансии, сохраняя разбиение на строки."""
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    # перенос строки ставится только на границах абзацев и пунктов списка,
    # иначе каждое выделенное слово оказалось бы на отдельной строке
    for tag in soup.find_all(BLOCK_TAGS):
        tag.append("\n")
    for tag in soup.find_all("br"):
        tag.replace_with("\n")
    lines = (" ".join(line.split()) for line in soup.get_text().splitlines())
    return "\n".join(line for line in lines if line) or None


def job_posting(soup: BeautifulSoup) -> dict | None:
    """Блок schema.org/JobPosting, который сайты кладут в страницу для поисковиков."""
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or "")
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "JobPosting":
            return data
    return None


class SourceBlocked(Exception):
    """Сайт распознал автоматические запросы и требует подтвердить, что запрос делает человек."""


class Source(ABC):
    """Источник вакансий.

    Чтобы добавить новый источник, достаточно унаследоваться, задать ``name``
    и реализовать ``page_url`` и ``parse``; обход страниц уже есть в ``fetch``.
    Если полное описание лежит на странице вакансии, дополнительно
    переопределяется ``parse_detail`` и выставляется ``has_details``.
    """

    name: str
    #: пауза между запросами к одному сайту, чтобы не нагружать его
    delay: float = 1.0
    #: False — весь список приходит одним ответом, листать нечего
    paginated: bool = True
    #: True — за полным описанием нужно идти на страницу вакансии
    has_details: bool = False
    #: сколько страниц вакансий одного сайта загружается одновременно
    details_limit: int = 3

    @abstractmethod
    def page_url(self, query: str, page: int) -> str:
        """Адрес страницы списка; ``page`` считается с единицы."""

    @abstractmethod
    def parse(self, text: str) -> list[RawVacancy]:
        """Достаёт вакансии из одной страницы списка (разметка или JSON)."""

    def parse_detail(self, html: str, vacancy: RawVacancy) -> bool:
        """Дополняет вакансию данными с её страницы; False — описания на странице нет."""
        return False

    async def fetch(
        self,
        client: httpx.AsyncClient,
        query: str,
        pages: int = 1,
        *,
        details: bool = False,
        skip_details: Collection[str] = (),
    ) -> list[RawVacancy]:
        """Собирает вакансии источника.

        ``skip_details`` — номера вакансий, полное описание которых уже известно:
        их страницы повторно не запрашиваются.
        """
        #: почему не удалось получить описание: причина → число вакансий
        self.detail_errors: Counter[str] = Counter()
        vacancies: list[RawVacancy] = []
        seen: set[str] = set()
        for page in range(1, (pages if self.paginated else 1) + 1):
            if page > 1:
                await asyncio.sleep(self.delay)
            text = await self.get(client, self.page_url(query, page))
            # страница без новых вакансий — список закончился
            fresh = [v for v in self.parse(text) if v.source_id not in seen]
            if not fresh:
                break
            seen.update(v.source_id for v in fresh)
            vacancies.extend(fresh)
        if details and self.has_details:
            await self._fetch_details(client, [v for v in vacancies if v.source_id not in skip_details])
        return vacancies

    async def get(self, client: httpx.AsyncClient, url: str) -> str:
        """Загружает страницу; если сайт вместо неё показал проверку «я не робот» — SourceBlocked."""
        response = await client.get(url)
        response.raise_for_status()
        if "captcha" in response.url.path:
            raise SourceBlocked("сайт запросил проверку «я не робот»")
        return response.text

    async def load_detail(self, client: httpx.AsyncClient, vacancy: RawVacancy) -> bool:
        """Загружает страницу вакансии и дополняет вакансию её данными."""
        return self.parse_detail(await self.get(client, vacancy.url), vacancy)

    async def _fetch_details(self, client: httpx.AsyncClient, vacancies: list[RawVacancy]) -> None:
        limit = asyncio.Semaphore(self.details_limit)
        blocked = False

        async def load(vacancy: RawVacancy) -> None:
            nonlocal blocked
            async with limit:
                if blocked:
                    # сайт попросил остановиться: оставшиеся страницы не запрашиваем
                    self.detail_errors["пропущено после проверки «я не робот»"] += 1
                    return
                # при сбое вакансия остаётся с данными из списка, а причина попадает в отчёт
                try:
                    vacancy.detailed = await self.load_detail(client, vacancy)
                    if not vacancy.detailed:
                        self.detail_errors["на странице нет описания"] += 1
                except SourceBlocked:
                    blocked = True
                    self.detail_errors["проверка «я не робот»"] += 1
                except httpx.HTTPStatusError as exc:
                    self.detail_errors[f"HTTP {exc.response.status_code}"] += 1
                except httpx.HTTPError as exc:
                    self.detail_errors[type(exc).__name__] += 1
                await asyncio.sleep(self.delay / self.details_limit)

        await asyncio.gather(*(load(v) for v in vacancies))

    @staticmethod
    def soup(html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")
