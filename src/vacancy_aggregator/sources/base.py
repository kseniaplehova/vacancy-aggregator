import asyncio
import json
import re
from abc import ABC, abstractmethod

import httpx
from bs4 import BeautifulSoup, Tag

from ..models import Vacancy

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
    def parse(self, text: str) -> list[Vacancy]:
        """Достаёт вакансии из одной страницы списка (разметка или JSON)."""

    def parse_detail(self, html: str, vacancy: Vacancy) -> None:
        """Дополняет вакансию данными с её собственной страницы."""

    async def fetch(
        self, client: httpx.AsyncClient, query: str, pages: int = 1, *, details: bool = False
    ) -> list[Vacancy]:
        vacancies: list[Vacancy] = []
        seen: set[str] = set()
        for page in range(1, (pages if self.paginated else 1) + 1):
            if page > 1:
                await asyncio.sleep(self.delay)
            response = await client.get(self.page_url(query, page))
            response.raise_for_status()
            # страница без новых вакансий — список закончился
            fresh = [v for v in self.parse(response.text) if v.source_id not in seen]
            if not fresh:
                break
            seen.update(v.source_id for v in fresh)
            vacancies.extend(fresh)
        if details and self.has_details:
            await self._fetch_details(client, vacancies)
        return vacancies

    async def _fetch_details(self, client: httpx.AsyncClient, vacancies: list[Vacancy]) -> None:
        limit = asyncio.Semaphore(self.details_limit)

        async def load(vacancy: Vacancy) -> None:
            async with limit:
                try:
                    response = await client.get(vacancy.url)
                    response.raise_for_status()
                    self.parse_detail(response.text, vacancy)
                except httpx.HTTPError:
                    pass  # вакансия остаётся с данными из списка
                await asyncio.sleep(self.delay / self.details_limit)

        await asyncio.gather(*(load(v) for v in vacancies))

    @staticmethod
    def soup(html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")
