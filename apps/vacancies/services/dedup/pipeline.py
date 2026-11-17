"""Поиск дубликатов среди всех собранных вакансий и объединение их в группы."""
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Sequence

from .jaccard import jaccard
from .normalize import char_shingles, normalize, normalize_company

#: с какой похожести названий две вакансии одной компании считаются одной и той же
TITLE_THRESHOLD = 0.8
#: слово, встречающееся в названиях стольких компаний, компанию не определяет («групп», «компания»)
COMMON_WORD_LIMIT = 50


@dataclass
class Prepared:
    """Вакансия в виде, готовом к сравнению; строится один раз."""

    record: Any
    title: set[str]
    company: frozenset[str]
    city: str


def prepare(record: Any) -> Prepared:
    return Prepared(
        record=record,
        title=char_shingles(normalize(record.title)),
        company=frozenset(normalize_company(record.company).split()),
        city=normalize(record.city),
    )


def same_company(a: frozenset[str], b: frozenset[str]) -> bool:
    """«Аливария» и «ОАО Пивоваренная компания Аливария» — одна компания.

    Порог выше половины: «Ивьевская средняя школа» и «Геранёнская средняя школа»
    совпадают двумя словами из четырёх, но это разные организации.
    """
    if not a or not b:
        return False
    return a <= b or b <= a or jaccard(set(a), set(b)) >= 0.6


def is_duplicate(a: Prepared, b: Prepared) -> bool:
    """Две записи из разных источников описывают одну вакансию."""
    if a.record.source == b.record.source:
        return False
    # агрегатор сам назвал первоисточник — совпадение точное, сравнивать тексты не нужно
    if a.record.origin_url == b.record.url or b.record.origin_url == a.record.url:
        return True
    if a.city and b.city and a.city != b.city:
        return False
    return same_company(a.company, b.company) and jaccard(a.title, b.title) >= TITLE_THRESHOLD


def candidate_pairs(prepared: Sequence[Prepared]) -> set[tuple[int, int]]:
    """Пары, которые имеет смысл сравнивать.

    Перебор всех пар растёт как квадрат числа вакансий. Вместо него строится
    указатель «слово из названия компании → вакансии», и сравниваются только
    вакансии, у которых есть общее слово. Пары, связанные прямой ссылкой
    на первоисточник, добавляются всегда.
    """
    by_word: dict[str, list[int]] = defaultdict(list)
    by_url: dict[str, int] = {}
    for index, item in enumerate(prepared):
        by_url[item.record.url] = index
        for word in item.company:
            by_word[word].append(index)

    pairs: set[tuple[int, int]] = set()
    for indexes in by_word.values():
        if len(indexes) > COMMON_WORD_LIMIT:
            continue
        pairs.update((i, j) for position, i in enumerate(indexes) for j in indexes[position + 1 :])
    for index, item in enumerate(prepared):
        origin = by_url.get(item.record.origin_url)
        if origin is not None and origin != index:
            pairs.add((min(index, origin), max(index, origin)))
    return pairs


def group_duplicates(records: Sequence[Any]) -> list[list[Any]]:
    """Группы записей об одной вакансии (в группе не меньше двух записей).

    Если A дублирует B, а B дублирует C, все три попадают в одну группу:
    пары объединяются системой непересекающихся множеств.
    """
    prepared = [prepare(record) for record in records]
    parent = list(range(len(prepared)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]  # сжатие пути
            index = parent[index]
        return index

    for i, j in candidate_pairs(prepared):
        if is_duplicate(prepared[i], prepared[j]):
            parent[find(i)] = find(j)

    groups: dict[int, list[Any]] = defaultdict(list)
    for index, item in enumerate(prepared):
        groups[find(index)].append(item.record)
    return [group for group in groups.values() if len(group) > 1]


def choose_main(group: Sequence[Any]) -> Any:
    """Запись, которая будет показана пользователю вместо всей группы.

    Предпочтение — первоисточнику перед агрегатором, затем записи с полным
    и более длинным описанием, затем той, что появилась раньше.
    """
    return min(
        group,
        key=lambda r: (bool(r.origin), not r.detailed, -len(r.description or ""), r.first_seen, r.pk),
    )
