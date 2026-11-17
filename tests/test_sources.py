from pathlib import Path

import pytest

from apps.vacancies.services.schemas import RawVacancy
from apps.vacancies.services.sources import Belmeta, DevBy, Greenhouse, Lever, MyJob, RabotaBy
from apps.vacancies.services.sources.base import html_to_text

FIXTURES = Path(__file__).parent / "fixtures"
SOURCES = {
    "rabota_by.html": RabotaBy(),
    "devby.html": DevBy(),
    "belmeta.html": Belmeta(),
    "myjob.html": MyJob(),
    "greenhouse.json": Greenhouse("tripledotstudios"),
    "lever.json": Lever("idt", company="IDT"),
}


def read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def parse(file: str) -> list[RawVacancy]:
    return SOURCES[file].parse(read(file))


def detail(source, file: str) -> RawVacancy:
    """Пустая вакансия, дополненная данными с сохранённой страницы."""
    vacancy = RawVacancy(source=source.name, source_id="1", url="https://example.org", title="x")
    source.parse_detail(read(file), vacancy)
    return vacancy


@pytest.mark.parametrize("file", SOURCES)
def test_required_fields(file):
    vacancies = parse(file)
    assert vacancies
    for v in vacancies:
        assert v.source == SOURCES[file].name
        assert v.source_id and v.title and v.company
        assert v.url.startswith("https://")
    assert len({v.source_id for v in vacancies}) == len(vacancies)


def test_rabota_by():
    first, second, third, _ = parse("rabota_by.html")
    assert first.source_id == "139566399"
    assert first.url == "https://rabota.by/vacancy/139566399"
    assert first.title == "AI-разработчик"
    assert first.company == "ООО Авансум"
    assert first.city == "Могилёв"
    assert first.salary == "2 500 – 4 000 Br за месяц, на руки"
    assert second.salary == "от 4 000 Br за месяц, на руки"
    assert third.salary is None


def test_rabota_by_detail():
    vacancy = detail(RabotaBy(), "rabota_by_detail.html")
    assert vacancy.description.startswith("Работа только в офисе в Минске.")
    assert len(vacancy.description) > 3000
    assert vacancy.published == "2026-11-17T10:00:20.114+03:00"


def test_devby_skips_banner():
    vacancies = parse("devby.html")
    assert len(vacancies) == 6  # седьмой элемент списка — рекламная вставка
    assert vacancies[0].title == "Rust Blockchain Developer"
    assert vacancies[0].salary == "$1500—4000"
    assert vacancies[1].salary is None
    assert vacancies[-1].description == "spring core, hibernate, sql, jpa, spring mvc"


def test_devby_detail():
    description = detail(DevBy(), "devby_detail.html").description
    assert description.startswith("Специализация: C/C++ Уровень: Intern")
    assert "Нанимаем студентов" in description


def test_belmeta():
    first = parse("belmeta.html")[0]
    assert first.source_id == "15772120"
    # слово запроса подсвечено тегом, пробел внутри названия появиться не должен
    assert first.title == "Python-разработчик (по работе с ИИ-агентами)"
    assert first.company == "Жук Антон Геннадьевич"
    assert first.city == "Минск"
    assert first.salary == "От 4 000 BYN"
    assert first.published == "Сегодня"
    assert "Python." in first.description


def test_belmeta_detail_names_origin():
    vacancy = detail(Belmeta(), "belmeta_detail.html")
    assert vacancy.origin == "rabota.by"
    # до запроса к сайту здесь адрес кнопки отклика; настоящий адрес подставляет load_detail
    assert vacancy.origin_url == "https://belmeta.com/jrd?id=15772120&src=js"
    assert "FastAPI" in vacancy.description
    assert len(vacancy.description) > 3000


def test_myjob():
    second = parse("myjob.html")[1]
    assert second.source_id == "jgd3yu4e7w2ri91j6xuy1ih3"
    assert second.title == "Инженер-системотехник"
    assert second.company == "АБН-групп"
    assert second.city == "Минск"
    assert second.salary == "от 3000 BYN"


def test_myjob_detail():
    vacancy = detail(MyJob(), "myjob_detail.html")
    assert "Составление и ведение технической документации" in vacancy.description
    assert vacancy.published == "2026-11-16T22:01:58.188Z"


def test_greenhouse_keeps_only_belarus():
    vacancies = parse("greenhouse.json")
    # в образце три вакансии: одна лондонская и две минские
    assert [v.city for v in vacancies] == ["Minsk", "Minsk"]
    first = vacancies[0]
    assert first.title == "Data Analyst"
    assert first.company == "Tripledot Studios"
    assert first.url == "https://job-boards.eu.greenhouse.io/tripledotstudios/jobs/4988633101"
    assert "Tripledot Studios is one of the largest" in first.description
    assert "<" not in first.description and "&lt;" not in first.description


def test_lever_keeps_only_belarus():
    vacancies = parse("lever.json")
    # в образце три вакансии: одна тбилисская и две минские
    assert [v.title for v in vacancies] == [
        "Engineering Manager (Node.js/Vue.js) - POS Systems",
        "Junior/Middle DevOps",
    ]
    junior = vacancies[1]
    assert junior.company == "IDT"
    assert junior.city == "Minsk"
    assert junior.published.startswith("2025-06-03T15:17:00")
    assert junior.description.startswith("IDT is looking for a professional")


def test_html_to_text_breaks_lines_only_between_blocks():
    html = "<p>Нужен <strong>Python</strong>-разработчик.</p><ul><li>FastAPI</li><li>SQL</li></ul>Офис<br>в Минске"
    assert html_to_text(html) == "Нужен Python-разработчик.\nFastAPI\nSQL\nОфис\nв Минске"
    assert html_to_text("") is None
