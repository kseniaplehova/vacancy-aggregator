from urllib.parse import urlencode

from ..models import Vacancy
from .base import Source, html_to_text, text_of

BASE = "https://belmeta.com"


class Belmeta(Source):
    name = "belmeta.com"
    has_details = True

    def parse_detail(self, html: str, vacancy: Vacancy) -> None:
        soup = self.soup(html)
        vacancy.description = html_to_text(str(soup.select_one(".p-job-details .text") or "")) or vacancy.description
        # у вакансий с других площадок кнопка отклика называет первоисточник: «Отклик на rabota.by»
        apply = text_of(soup.select_one('a[href*="/jrd?"]'))
        if apply and " на " in apply:
            vacancy.origin = apply.rsplit(" на ", 1)[-1]

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
