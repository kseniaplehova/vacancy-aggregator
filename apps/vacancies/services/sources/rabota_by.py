import re
from urllib.parse import urlencode, urlsplit

from ..schemas import RawVacancy
from .base import Source, html_to_text, job_posting, text_of

SALARY = re.compile(r"\d[\d\s  ]*.*(Br|\$|€|₽)")
VACANCY_ID = re.compile(r"/vacancy/(\d+)")


class RabotaBy(Source):
    name = "rabota.by"
    #: код Беларуси в справочнике регионов сайта
    area = 16
    has_details = True
    # при частых запросах сайт показывает проверку «я не робот», поэтому
    # страницы вакансий загружаются по одной и с паузой
    details_limit = 1
    delay = 2.0

    def parse_detail(self, html: str, vacancy: RawVacancy) -> bool:
        posting = job_posting(self.soup(html))
        description = html_to_text(posting.get("description")) if posting else None
        if not description:
            return False
        vacancy.description = description
        vacancy.published = posting.get("datePosted") or vacancy.published
        return True

    def page_url(self, query: str, page: int) -> str:
        # на сайте страницы нумеруются с нуля
        params = {"text": query, "area": self.area, "page": page - 1}
        return f"https://rabota.by/search/vacancy?{urlencode(params)}"

    def parse(self, html: str) -> list[RawVacancy]:
        vacancies = []
        for card in self.soup(html).select('[data-qa~="vacancy-serp__vacancy"]'):
            link = card.select_one('a[data-qa="serp-item__title"]')
            match = VACANCY_ID.search(link["href"]) if link else None
            if not match:
                continue
            vacancies.append(
                RawVacancy(
                    source=self.name,
                    source_id=match.group(1),
                    # без параметров поиска: адрес одной вакансии должен быть одинаковым
                    url=urlsplit(link["href"])._replace(query="").geturl(),
                    title=text_of(link),
                    company=text_of(card.select_one('[data-qa="vacancy-serp__vacancy-employer-text"]')),
                    city=self._city(card),
                    salary=self._salary(card),
                )
            )
        return vacancies

    @staticmethod
    def _city(card) -> str | None:
        address = text_of(card.select_one('[data-qa="vacancy-serp__vacancy-address"]'))
        return address.split(",")[0].strip() if address else None

    @staticmethod
    def _salary(card) -> str | None:
        # у зарплаты нет своей метки, поэтому ищем самый короткий текст с числом и валютой
        found = [t for t in map(text_of, card.find_all("span")) if t and SALARY.match(_strip_prefix(t))]
        return min(found, key=len) if found else None


def _strip_prefix(text: str) -> str:
    return re.sub(r"^(от|до)\s+", "", text)
