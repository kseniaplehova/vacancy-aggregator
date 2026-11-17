import html
import json

from ..schemas import RawVacancy
from .base import BELARUS, Source, html_to_text


class Greenhouse(Source):
    """Карьерная страница компании на сервисе найма Greenhouse.

    Сервис отдаёт все вакансии компании одним JSON-ответом вместе с описаниями,
    поэтому ни листать страницы, ни ходить за подробностями не нужно.
    """

    paginated = False

    def __init__(self, board: str):
        self.board = board
        self.name = f"greenhouse:{board}"

    def page_url(self, query: str, page: int) -> str:
        return f"https://boards-api.greenhouse.io/v1/boards/{self.board}/jobs?content=true"

    def parse(self, text: str) -> list[RawVacancy]:
        vacancies = []
        for job in json.loads(text)["jobs"]:
            location = job.get("location", {}).get("name") or ""
            # компании международные, оставляем только белорусские вакансии
            if not BELARUS.search(location):
                continue
            vacancies.append(
                RawVacancy(
                    source=self.name,
                    source_id=str(job["id"]),
                    url=job["absolute_url"],
                    title=job["title"].strip(),
                    company=job.get("company_name"),
                    city=location or None,
                    # описание приходит как разметка с заменёнными спецсимволами
                    description=html_to_text(html.unescape(job.get("content") or "")),
                    published=job.get("first_published") or job.get("updated_at"),
                )
            )
        return vacancies
