from urllib.parse import urlencode, urlsplit

import httpx

from ..schemas import RawVacancy
from .base import Source, html_to_text, text_of

BASE = "https://belmeta.com"


class Belmeta(Source):
    name = "belmeta.com"
    has_details = True

    def parse_detail(self, html: str, vacancy: RawVacancy) -> None:
        soup = self.soup(html)
        vacancy.description = html_to_text(str(soup.select_one(".p-job-details .text") or "")) or vacancy.description
        # у вакансий с других площадок кнопка отклика называет первоисточник: «Отклик на rabota.by»
        apply = soup.select_one('a[href*="/jrd?"]')
        label = text_of(apply)
        if label and " на " in label:
            vacancy.origin = label.rsplit(" на ", 1)[-1]
            vacancy.origin_url = BASE + apply["href"]

    async def load_detail(self, client: httpx.AsyncClient, vacancy: RawVacancy) -> None:
        await super().load_detail(client, vacancy)
        if vacancy.origin_url:
            # кнопка отклика перенаправляет на первоисточник: берём адрес, не переходя по нему
            response = await client.get(vacancy.origin_url, follow_redirects=False)
            target = response.headers.get("location")
            vacancy.origin_url = urlsplit(target)._replace(query="").geturl() if target else None

    def page_url(self, query: str, page: int) -> str:
        return f"{BASE}/vacansii?{urlencode({'q': query, 'page': page})}"

    def parse(self, html: str) -> list[RawVacancy]:
        vacancies = []
        for job in self.soup(html).select("article.job[data-id]"):
            link = job.select_one("a.job-title")
            if link is None:
                continue
            vacancies.append(
                RawVacancy(
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
