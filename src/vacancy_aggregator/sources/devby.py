from ..models import Vacancy
from .base import Source, html_to_text, text_of

BASE = "https://jobs.devby.io"


class DevBy(Source):
    name = "jobs.devby.io"
    has_details = True

    def parse_detail(self, html: str, vacancy: Vacancy) -> None:
        soup = self.soup(html)
        # сначала блок «Специализация / Уровень / Опыт», затем сам текст вакансии
        parts = [text_of(soup.select_one(".vacancy__info-block")), html_to_text(str(soup.select_one(".vacancy__text") or ""))]
        vacancy.description = "\n".join(p for p in parts if p) or vacancy.description

    def page_url(self, query: str, page: int) -> str:
        # поиска по тексту у сайта нет: отдаётся весь список IT-вакансий
        return f"{BASE}/?page={page}"

    def parse(self, html: str) -> list[Vacancy]:
        vacancies = []
        for item in self.soup(html).select(".vacancies-list-item"):
            link = item.select_one("a.vacancies-list-item__link_block")
            if link is None:  # рекламная вставка в списке
                continue
            tags = [text_of(t) for t in item.select(".vacancies-list-item__technology-tag__name")]
            vacancies.append(
                Vacancy(
                    source=self.name,
                    source_id=link["href"].rstrip("/").rsplit("/", 1)[-1],
                    url=BASE + link["href"],
                    title=text_of(link),
                    company=text_of(item.select_one(".vacancies-list-item__company")),
                    salary=text_of(item.select_one(".vacancies-list-item__salary")),
                    description=", ".join(t for t in tags if t) or None,
                )
            )
        return vacancies
