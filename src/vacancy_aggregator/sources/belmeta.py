from urllib.parse import urlencode

from ..models import Vacancy
from .base import Source, text_of

BASE = "https://belmeta.com"


class Belmeta(Source):
    name = "belmeta.com"

    def page_url(self, query: str, page: int) -> str:
        return f"{BASE}/vacansii?{urlencode({'q': query, 'page': page})}"

    def parse(self, html: str) -> list[Vacancy]:
        vacancies = []
        for job in self.soup(html).select("article.job[data-id]"):
            link = job.select_one("a.job-title")
            if link is None:
                continue
            vacancies.append(
                Vacancy(
                    source=self.name,
                    source_id=job["data-id"],
                    url=BASE + link["href"],
                    title=text_of(link, sep=""),
                    company=text_of(job.select_one(".job-data.company")),
                    city=text_of(job.select_one(".job-data.region")),
                    salary=text_of(job.select_one(".job-data.salary")),
                    description=text_of(job.select_one(".desc"), sep=""),
                    published=text_of(job.select_one(".from")),
                )
            )
        return vacancies
