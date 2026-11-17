from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from apps.vacancies.models import Favorite, Vacancy
from apps.vacancies.services.dedup.pipeline import choose_main, group_duplicates
from apps.vacancies.services.schemas import RawVacancy
from apps.vacancies.services.storage import deduplicate, save_vacancies

NOW = datetime(2026, 11, 17, tzinfo=timezone.utc)
counter = iter(range(1, 10_000))


def record(source, title, company, city="Минск", **fields):
    pk = next(counter)
    defaults = dict(
        pk=pk, url=f"https://{source}/{pk}", origin=None, origin_url=None, detailed=True, description="", first_seen=NOW
    )
    return SimpleNamespace(source=source, title=title, company=company, city=city, **{**defaults, **fields})


def titles(groups):
    return sorted(sorted(f"{r.source}: {r.title}" for r in group) for group in groups)


def test_same_vacancy_from_two_sources_is_grouped():
    a = record("rabota.by", "Python-разработчик (по работе с ИИ-агентами)", "ИП Жук Антон Геннадьевич")
    b = record("belmeta.com", "Python-разработчик (по работе с ИИ-агентами)", "Жук Антон Геннадьевич")
    other = record("myjob.by", "Бухгалтер", "ООО Ромашка")
    assert group_duplicates([a, b, other]) == [[a, b]]


def test_company_written_differently_still_matches():
    a = record("rabota.by", "Аналитик продаж", "ОАО Пивоваренная компания Аливария")
    b = record("belmeta.com", "Аналитик продаж", "Аливария")
    assert len(group_duplicates([a, b])) == 1


def test_what_must_not_be_grouped():
    base = record("rabota.by", "Инженер-программист (C++ разработчик)", "Государственное предприятие НЦОТ")
    not_duplicates = [
        # похожее, но другое название у той же компании
        record("belmeta.com", "Инженер-программист (Rust-разработчик)", "Государственное предприятие НЦОТ"),
        # то же название у другой компании
        record("myjob.by", "Инженер-программист (C++ разработчик)", "ООО Ромашка"),
        # та же вакансия в другом городе
        record("jobs.devby.io", "Инженер-программист (C++ разработчик)", "НЦОТ", city="Гомель"),
        # название компании совпадает наполовину, города нет
        record("lever:idt", "Инженер-программист (C++ разработчик)", "Государственное предприятие БелТест", city=None),
        # тот же источник: повторы внутри одного источника не объединяются
        record("rabota.by", "Инженер-программист (C++ разработчик)", "Государственное предприятие НЦОТ"),
    ]
    assert group_duplicates([base, *not_duplicates]) == []


def test_link_to_origin_groups_even_when_texts_differ():
    original = record("rabota.by", "Senior Project Manager", "Научсофт")
    copy = record("belmeta.com", "Руководитель проектов", None, origin="rabota.by", origin_url=original.url)
    assert group_duplicates([original, copy]) == [[original, copy]]


def test_groups_are_transitive():
    a = record("rabota.by", "Data Engineer", "ООО Мак")
    b = record("belmeta.com", "Data Engineer", "Мак", origin="rabota.by", origin_url=a.url)
    c = record("myjob.by", "Data Engineer", "Мак")
    groups = group_duplicates([a, b, c])
    assert titles(groups) == [["belmeta.com: Data Engineer", "myjob.by: Data Engineer", "rabota.by: Data Engineer"]]


def test_main_record_is_origin_with_full_description():
    copy = record("belmeta.com", "QA", "Юнидев", origin="rabota.by", description="длинное описание " * 10)
    short = record("myjob.by", "QA", "Юнидев", detailed=False, description="коротко")
    full = record("rabota.by", "QA", "Юнидев", description="полное описание")
    assert choose_main([copy, short, full]) is full


def raw(source, source_id, title="Python Developer", company="Acme", **fields):
    return RawVacancy(
        source=source, source_id=source_id, url=f"https://{source}/{source_id}", title=title, company=company, **fields
    )


@pytest.mark.django_db
def test_deduplicate_marks_duplicates_and_moves_favorites(django_user_model):
    save_vacancies(
        [
            raw("rabota.by", "1", description="полное описание", detailed=True),
            raw("belmeta.com", "7", origin="rabota.by"),
            raw("rabota.by", "2", title="Бухгалтер", company="Ромашка"),
        ]
    )
    main = Vacancy.objects.get(source="rabota.by", source_id="1")
    copy = Vacancy.objects.get(source="belmeta.com")
    user = django_user_model.objects.create_user("ksenia", "ksenia@example.org", "pass")
    Favorite.objects.create(user=user, vacancy=copy)

    assert deduplicate() == (1, 1)
    copy.refresh_from_db()
    assert copy.duplicate_of == main
    assert Vacancy.objects.filter(duplicate_of__isnull=True).count() == 2
    # избранное переехало с дубликата на основную запись
    assert list(Favorite.objects.values_list("vacancy_id", flat=True)) == [main.pk]

    # вакансия изменилась и перестала быть дубликатом — разметка снимается
    Vacancy.objects.filter(pk=copy.pk).update(title="Совсем другая вакансия", company="Другая компания")
    assert deduplicate() == (0, 0)
    copy.refresh_from_db()
    assert copy.duplicate_of is None
