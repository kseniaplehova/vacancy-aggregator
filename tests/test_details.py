import asyncio

import httpx

from apps.vacancies.services.schemas import RawVacancy
from apps.vacancies.services.sources import Source


class Pages(Source):
    name = "pages"
    has_details = True
    details_limit = 1
    delay = 0

    def page_url(self, query, page):
        return "https://site.test/list"

    def parse(self, text):
        return [
            RawVacancy(source=self.name, source_id=str(n), url=f"https://site.test/vacancy/{n}", title=f"Вакансия {n}")
            for n in range(1, 6)
        ]

    def parse_detail(self, html, vacancy):
        if not html:
            return False
        vacancy.description = html
        return True


def collect(handler, **kwargs):
    async def run():
        source = Pages()
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True) as client:
            vacancies = await source.fetch(client, "python", details=True, **kwargs)
        return source, vacancies

    return asyncio.run(run())


def test_details_are_loaded_and_known_ones_are_skipped():
    requested = []

    def handler(request):
        requested.append(request.url.path)
        return httpx.Response(200, text="полное описание")

    source, vacancies = collect(handler, skip_details={"2", "4"})
    assert requested == ["/list", "/vacancy/1", "/vacancy/3", "/vacancy/5"]
    assert [v.detailed for v in vacancies] == [True, False, True, False, True]
    assert vacancies[0].description == "полное описание"
    assert not source.detail_errors


def test_failures_are_counted_by_reason():
    def handler(request):
        if request.url.path == "/vacancy/2":
            return httpx.Response(500)
        if request.url.path == "/vacancy/3":
            return httpx.Response(200, text="")
        return httpx.Response(200, text="полное описание")

    source, vacancies = collect(handler)
    assert [v.detailed for v in vacancies] == [True, False, False, True, True]
    assert source.detail_errors == {"HTTP 500": 1, "на странице нет описания": 1}


def test_captcha_stops_further_requests():
    requested = []

    def handler(request):
        requested.append(request.url.path)
        if request.url.path == "/vacancy/2":
            return httpx.Response(302, headers={"location": "https://site.test/account/captcha"})
        return httpx.Response(200, text="полное описание")

    source, vacancies = collect(handler)
    assert requested == ["/list", "/vacancy/1", "/vacancy/2", "/account/captcha"]
    assert [v.detailed for v in vacancies] == [True, False, False, False, False]
    assert source.detail_errors == {
        "проверка «я не робот»": 1,
        "пропущено после проверки «я не робот»": 3,
    }
