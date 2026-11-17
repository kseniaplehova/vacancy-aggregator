import re

from ..schemas import RawVacancy
from .base import Source, html_to_text, job_posting, text_of

BASE = "https://myjob.by"
SALARY = re.compile(r"\d.*(BYN|USD|EUR|RUB)")


class MyJob(Source):
    name = "myjob.by"
    #: раздел сайта; поиск по тексту находит слишком мало, поэтому берётся весь раздел IT
    category = "it-internet-telekom"
    has_details = True

    def parse_detail(self, html: str, vacancy: RawVacancy) -> bool:
        posting = job_posting(self.soup(html))
        description = html_to_text(posting.get("description")) if posting else None
        if not description:
            return False
        vacancy.description = description
        vacancy.published = posting.get("datePosted") or vacancy.published
        return True

    def page_url(self, query: str, page: int) -> str:
        return f"{BASE}/categories/{self.category}?page={page}"

    def parse(self, html: str) -> list[RawVacancy]:
        vacancies = []
        for card in self.soup(html).select('[data-slot="card"]'):
            link = card.select_one('a[href^="/jobs/"]')
            title = text_of(card.select_one('[data-slot="card-title"]'))
            if link is None or title is None:
                continue
            href = link["href"]
            vacancies.append(
                RawVacancy(
                    source=self.name,
                    # в конце адреса — идентификатор вакансии
                    source_id=href.rsplit("-", 1)[-1],
                    url=BASE + href,
                    title=title,
                    company=text_of(card.select_one('[data-slot="card-header"] p')),
                    city=text_of(card.select_one('a[href^="/cities/"]'))
                    or text_of(card.select_one('a[href^="/regions/"]')),
                    salary=self._salary(card),
                    description=text_of(card.select_one('[data-slot="card-content"] > p')),
                )
            )
        return vacancies

    @staticmethod
    def _salary(card) -> str | None:
        found = [t for t in map(text_of, card.find_all("span")) if t and SALARY.search(t) and len(t) < 60]
        return min(found, key=len) if found else None
