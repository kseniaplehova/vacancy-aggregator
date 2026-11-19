import json
from datetime import datetime, timezone

from ..schemas import RawVacancy
from .base import BELARUS, Source, html_to_text, local_city


class Lever(Source):
    paginated = False

    def __init__(self, site: str, company: str):
        self.site = site
        self.company = company
        self.name = f"lever:{site}"

    def page_url(self, query: str, page: int) -> str:
        return f"https://api.lever.co/v0/postings/{self.site}?mode=json"

    def parse(self, text: str) -> list[RawVacancy]:
        vacancies = []
        for job in json.loads(text):
            location = job.get("categories", {}).get("location") or ""
            if job.get("country") != "BY" and not BELARUS.search(location):
                continue
            vacancies.append(
                RawVacancy(
                    source=self.name,
                    source_id=job["id"],
                    url=job["hostedUrl"],
                    title=job["text"].strip(),
                    company=self.company,
                    city=local_city(location),
                    description=self._description(job),
                    published=self._date(job.get("createdAt")),
                )
            )
        return vacancies

    @staticmethod
    def _description(job: dict) -> str | None:
        parts = [html_to_text(job.get("description"))]
        for block in job.get("lists", []):
            parts += [block.get("text"), html_to_text(block.get("content"))]
        parts.append(html_to_text(job.get("additional")))
        return "\n".join(p for p in parts if p) or None

    @staticmethod
    def _date(milliseconds: int | None) -> str | None:
        if not milliseconds:
            return None
        return datetime.fromtimestamp(milliseconds / 1000, timezone.utc).isoformat()
