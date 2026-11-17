import pytest

from apps.vacancies.models import Vacancy
from apps.vacancies.services.schemas import RawVacancy
from apps.vacancies.services.storage import save_vacancies


def raw(source_id="1", source="rabota.by", **fields):
    return RawVacancy(
        source=source, source_id=source_id, url="https://example.org/1", title="Python Developer", **fields
    )


@pytest.mark.django_db
def test_save_adds_then_updates():
    first = save_vacancies([raw("1", description="полный текст"), raw("2")])
    # повторный сбор: та же вакансия без описания, одна новая
    # и вакансия с тем же номером из другого источника
    second = save_vacancies([raw("1", salary="от 4 000 BYN"), raw("3"), raw("1", source="belmeta.com")])

    assert first == (2, 0)
    assert second == (2, 1)
    assert Vacancy.objects.count() == 4

    vacancy = Vacancy.objects.get(source="rabota.by", source_id="1")
    assert vacancy.salary == "от 4 000 BYN"
    assert vacancy.description == "полный текст"  # не затёрлось пустым значением
    assert vacancy.last_seen > vacancy.first_seen


@pytest.mark.django_db
def test_same_vacancy_twice_in_one_batch_is_saved_once():
    assert save_vacancies([raw("1"), raw("1")]) == (1, 0)
    assert Vacancy.objects.count() == 1
