import asyncio
from abc import ABC, abstractmethod

import httpx
from bs4 import BeautifulSoup, Tag

from ..models import Vacancy


def text_of(tag: Tag | None, sep: str = " ") -> str | None:
    """Текст элемента без лишних пробелов; None, если элемента или текста нет.

    ``sep`` вставляется между вложенными элементами. Пустой нужен там, где сайт
    подсвечивает слова запроса тегами внутри слова: «<b>Python</b>-разработчик».
    """
    if tag is None:
        return None
    return " ".join(tag.get_text(sep).split()) or None


class Source(ABC):
    """Источник вакансий.

    Чтобы добавить новый источник, достаточно унаследоваться, задать ``name``
    и реализовать ``page_url`` и ``parse``; обход страниц уже есть в ``fetch``.
    """

    name: str
    #: пауза между запросами к одному сайту, чтобы не нагружать его
    delay: float = 1.0

    @abstractmethod
    def page_url(self, query: str, page: int) -> str:
        """Адрес страницы списка; ``page`` считается с единицы."""

    @abstractmethod
    def parse(self, html: str) -> list[Vacancy]:
        """Достаёт вакансии из разметки одной страницы списка."""

    async def fetch(self, client: httpx.AsyncClient, query: str, pages: int = 1) -> list[Vacancy]:
        vacancies: list[Vacancy] = []
        seen: set[str] = set()
        for page in range(1, pages + 1):
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
        return vacancies

    @staticmethod
    def soup(html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")
