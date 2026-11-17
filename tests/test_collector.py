import asyncio

from apps.vacancies.services.collector import collect
from apps.vacancies.services.schemas import RawVacancy
from apps.vacancies.services.sources import Source


class Fake(Source):
    """Источник без сети: ждёт ``wait`` секунд и отдаёт одну вакансию."""

    def __init__(self, name: str, wait: float = 0.0, fail: bool = False):
        self.name, self.wait, self.fail = name, wait, fail

    def page_url(self, query, page):
        return ""

    def parse(self, html):
        return []

    async def fetch(self, client, query, pages=1, *, details=False, skip_details=()):
        await asyncio.sleep(self.wait)
        if self.fail:
            raise RuntimeError("источник недоступен")
        return [RawVacancy(source=self.name, source_id="1", url="https://example.org/1", title=query)]


def run(sources, **kwargs):
    return asyncio.run(collect(sources, "python", **kwargs))


def test_failure_of_one_source_does_not_affect_others():
    result = run([Fake("a"), Fake("b", fail=True), Fake("c")])
    assert [r.source for r in result.reports] == ["a", "b", "c"]
    assert [len(r.vacancies) for r in result.reports] == [1, 0, 1]
    assert "источник недоступен" in result.reports[1].error
    assert len(result.vacancies) == 2


def test_concurrent_is_faster_than_sequential():
    sources = [Fake(str(i), wait=0.2) for i in range(4)]
    concurrent = run(sources)
    sequential = run(sources, concurrent=False)
    assert len(concurrent.vacancies) == len(sequential.vacancies) == 4
    assert sequential.seconds > 0.75  # четыре ожидания подряд
    assert concurrent.seconds < 0.5  # ожидания идут одновременно
