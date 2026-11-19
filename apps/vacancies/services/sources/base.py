import asyncio
import json
import re
from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Collection

import httpx
from bs4 import BeautifulSoup, Tag

from ..schemas import RawVacancy

BELARUS = re.compile(r"belarus|minsk|brest|grodno|gomel|vitebsk|mogilev|беларус|минск", re.IGNORECASE)
CITY_NAMES = {
    "minsk": "Минск",
    "brest": "Брест",
    "grodno": "Гродно",
    "gomel": "Гомель",
    "vitebsk": "Витебск",
    "mogilev": "Могилёв",
    "belarus": "Беларусь",
}
BLOCK_TAGS =["p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr"]


def text_of(tag: Tag | None, sep: str = " ") -> str | None:
    if tag is None:
        return None
    return " ".join(tag.get_text(sep).split()) or None


def local_city(name: str | None) -> str | None:
    if not name:
        return None
    return CITY_NAMES.get(name.strip().lower(), name.strip())


def html_to_text(html: str | None) -> str | None:
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(BLOCK_TAGS):
        tag.append("\n")
    for tag in soup.find_all("br"):
        tag.replace_with("\n")
    lines = (" ".join(line.split()) for line in soup.get_text().splitlines())
    return "\n".join(line for line in lines if line) or None


def job_posting(soup: BeautifulSoup) -> dict | None:
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or "")
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "JobPosting":
            return data
    return None


class SourceBlocked(Exception):
    pass


class Source(ABC):
    name: str
    delay: float = 1.0
    paginated: bool = True
    has_details: bool = False
    details_limit: int = 3

    @abstractmethod
    def page_url(self, query: str, page: int) -> str:
        pass

    @abstractmethod
    def parse(self, text: str) -> list[RawVacancy]:
        pass

    def parse_detail(self, html: str, vacancy: RawVacancy) -> bool:
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
        self.detail_errors: Counter[str] = Counter()
        vacancies: list[RawVacancy] = []
        seen: set[str] = set()
        for page in range(1, (pages if self.paginated else 1) + 1):
            if page > 1:
                await asyncio.sleep(self.delay)
            text = await self.get(client, self.page_url(query, page))
            fresh = [v for v in self.parse(text) if v.source_id not in seen]
            if not fresh:
                break
            seen.update(v.source_id for v in fresh)
            vacancies.extend(fresh)
        if details and self.has_details:
            await self._fetch_details(client, [v for v in vacancies if v.source_id not in skip_details])
        return vacancies

    async def get(self, client: httpx.AsyncClient, url: str) -> str:
        response = await client.get(url)
        response.raise_for_status()
        if "captcha" in response.url.path:
            raise SourceBlocked("сайт запросил проверку «я не робот»")
        return response.text

    async def load_detail(self, client: httpx.AsyncClient, vacancy: RawVacancy) -> bool:
        return self.parse_detail(await self.get(client, vacancy.url), vacancy)

    async def _fetch_details(self, client: httpx.AsyncClient, vacancies: list[RawVacancy]) -> None:
        limit = asyncio.Semaphore(self.details_limit)
        blocked = False

        async def load(vacancy: RawVacancy) -> None:
            nonlocal blocked
            async with limit:
                if blocked:
                    self.detail_errors["пропущено после проверки «я не робот»"] += 1
                    return
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
