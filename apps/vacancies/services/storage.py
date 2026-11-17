from django.db import transaction
from django.utils import timezone

from apps.vacancies.models import Vacancy

from .schemas import RawVacancy

#: поля, которые при повторном сборе обновляются данными источника
UPDATED_FIELDS = ("url", "title", "company", "city", "salary", "description", "published", "origin", "origin_url")


def known_details() -> dict[str, set[str]]:
    """Номера вакансий по источникам, чьи страницы уже успешно загружались."""
    known: dict[str, set[str]] = {}
    for source, source_id in Vacancy.objects.filter(detailed=True).values_list("source", "source_id"):
        known.setdefault(source, set()).add(source_id)
    return known


@transaction.atomic
def save_vacancies(raw_vacancies: list[RawVacancy]) -> tuple[int, int]:
    """Записывает собранные вакансии в базу; возвращает число новых и обновлённых.

    Вакансия, которая уже есть в базе (тот же источник и номер в нём),
    не дублируется: у неё обновляются поля и отметка «последний раз встречалась».
    """
    now = timezone.now()
    by_source: dict[str, dict[str, RawVacancy]] = {}
    for raw in raw_vacancies:
        by_source.setdefault(raw.source, {})[raw.source_id] = raw

    new, changed = [], []
    for source, items in by_source.items():
        existing = {v.source_id: v for v in Vacancy.objects.filter(source=source, source_id__in=items)}
        for source_id, raw in items.items():
            vacancy = existing.get(source_id)
            if vacancy is None:
                vacancy = Vacancy(source=source, source_id=source_id, first_seen=now)
                new.append(vacancy)
            else:
                changed.append(vacancy)
            for name in UPDATED_FIELDS:
                value = getattr(raw, name)
                # короткая карточка из списка не должна затирать уже сохранённое описание
                if value is not None or getattr(vacancy, name) is None:
                    setattr(vacancy, name, value)
            vacancy.detailed = vacancy.detailed or raw.detailed
            vacancy.last_seen = now

    Vacancy.objects.bulk_create(new)
    Vacancy.objects.bulk_update(changed, [*UPDATED_FIELDS, "detailed", "last_seen"])
    return len(new), len(changed)
