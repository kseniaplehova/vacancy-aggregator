from pathlib import Path

import pytest

from vacancy_aggregator.sources import ALL_SOURCES, Belmeta, DevBy, MyJob, RabotaBy

FIXTURES = Path(__file__).parent / "fixtures"


def parse(cls):
    html = (FIXTURES / f"{cls.__module__.rsplit('.', 1)[-1]}.html").read_text(encoding="utf-8")
    return cls().parse(html)


@pytest.mark.parametrize("cls", ALL_SOURCES)
def test_required_fields(cls):
    vacancies = parse(cls)
    assert vacancies
    for v in vacancies:
        assert v.source == cls.name
        assert v.source_id and v.title and v.company
        assert v.url.startswith("https://")
    assert len({v.source_id for v in vacancies}) == len(vacancies)


def test_rabota_by():
    first, second, third, _ = parse(RabotaBy)
    assert first.source_id == "139566399"
    assert first.url == "https://rabota.by/vacancy/139566399"
    assert first.title == "AI-разработчик"
    assert first.company == "ООО Авансум"
    assert first.city == "Могилёв"
    assert first.salary == "2 500 – 4 000 Br за месяц, на руки"
    assert second.salary == "от 4 000 Br за месяц, на руки"
    assert third.salary is None


def test_devby_skips_banner():
    vacancies = parse(DevBy)
    assert len(vacancies) == 6  # седьмой элемент списка — рекламная вставка
    assert vacancies[0].title == "Rust Blockchain Developer"
    assert vacancies[0].salary == "$1500—4000"
    assert vacancies[1].salary is None
    assert vacancies[-1].description == "spring core, hibernate, sql, jpa, spring mvc"


def test_belmeta():
    first = parse(Belmeta)[0]
    assert first.source_id == "15772120"
    # слово запроса подсвечено тегом, пробел внутри названия появиться не должен
    assert first.title == "Python-разработчик (по работе с ИИ-агентами)"
    assert first.company == "Жук Антон Геннадьевич"
    assert first.city == "Минск"
    assert first.salary == "От 4 000 BYN"
    assert first.published == "Сегодня"
    assert "Python." in first.description


def test_myjob():
    second = parse(MyJob)[1]
    assert second.source_id == "jgd3yu4e7w2ri91j6xuy1ih3"
    assert second.title == "Инженер-системотехник"
    assert second.company == "АБН-групп"
    assert second.city == "Минск"
    assert second.salary == "от 3000 BYN"
