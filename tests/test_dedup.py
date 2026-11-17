from types import SimpleNamespace

import pytest

from apps.vacancies.services.dedup import all_matchers
from apps.vacancies.services.dedup.evaluation import evaluate, quality_at
from apps.vacancies.services.dedup.jaccard import jaccard
from apps.vacancies.services.dedup.levenshtein import distance, similarity
from apps.vacancies.services.dedup.minhash import MinHasher, estimate, lsh_candidates
from apps.vacancies.services.dedup.normalize import (
    char_shingles,
    key_of,
    normalize,
    normalize_company,
    word_shingles,
)
from apps.vacancies.services.dedup.vectors import cosine, tfidf_vectors


def record(title, company=None, description=None):
    return SimpleNamespace(title=title, company=company, description=description)


DESCRIPTION = (
    "Ищем разработчика на Python в команду платформы. Стек: Python 3.13, FastAPI, PostgreSQL, Docker. "
    "Работа в офисе в Минске, гибкий график, оплачиваемый отпуск и больничный, обучение за счёт компании."
)
ORIGINAL = record("Python-разработчик (по работе с ИИ-агентами)", "ИП Жук Антон Геннадьевич", DESCRIPTION)
# та же вакансия у агрегатора: другая запись компании, у описания обрезано начало
COPY = record("Python-разработчик (по работе с ИИ-агентами)", "Жук Антон Геннадьевич", DESCRIPTION[40:])
OTHER = record(
    "Бухгалтер по расчёту заработной платы",
    "ООО Ромашка",
    "Начисление заработной платы, отчётность в ФСЗН, работа в 1С. Опыт от трёх лет, знание законодательства.",
)


def test_normalize():
    assert normalize("  Senior C++/C# Разработчик — Ёлка!  ") == "senior c++ c# разработчик елка"
    assert normalize(None) == ""
    assert normalize_company("ООО «Авансум»") == "авансум"
    assert normalize_company("ИП Жук Антон Геннадьевич") == "жук антон геннадьевич"
    assert key_of(ORIGINAL) == key_of(COPY)


def test_shingles():
    assert word_shingles("a b c d", 2) == {"a b", "b c", "c d"}
    assert word_shingles("python", 2) == {"python"}
    assert word_shingles("") == set()
    assert char_shingles("abcd", 3) == {"abc", "bcd"}


@pytest.mark.parametrize(
    "a, b, expected",
    [("", "", 0), ("abc", "", 3), ("кот", "кит", 1), ("kitten", "sitting", 3), ("flaw", "lawn", 2)],
)
def test_levenshtein_distance(a, b, expected):
    assert distance(a, b) == expected
    assert distance(b, a) == expected


def test_levenshtein_similarity():
    assert similarity("python", "python") == 1.0
    assert similarity("", "") == 1.0
    assert similarity("abc", "xyz") == 0.0
    assert similarity("kitten", "sitting") == pytest.approx(1 - 3 / 7)


def test_jaccard():
    assert jaccard({1, 2, 3}, {2, 3, 4}) == 0.5
    assert jaccard({1}, {2}) == 0.0
    assert jaccard(set(), set()) == 1.0


def test_minhash_estimates_jaccard():
    a = {f"слово{i}" for i in range(0, 300)}
    b = {f"слово{i}" for i in range(100, 400)}  # настоящий коэффициент Жаккара — 0.5
    hasher = MinHasher(size=256)
    assert estimate(hasher.signature(a), hasher.signature(b)) == pytest.approx(0.5, abs=0.1)
    assert estimate(hasher.signature(a), hasher.signature(a)) == 1.0
    # сигнатура не зависит от запуска программы
    assert hasher.signature(a) == MinHasher(size=256).signature(a)


def test_lsh_finds_similar_pair_without_comparing_everything():
    hasher = MinHasher(size=64)
    base = {f"w{i}" for i in range(200)}
    sets = [base, base | {"x1", "x2"}, {f"q{i}" for i in range(200)}, {f"z{i}" for i in range(200)}]
    candidates = lsh_candidates([hasher.signature(s) for s in sets])
    assert (0, 1) in candidates
    assert (2, 3) not in candidates


def test_tfidf_cosine():
    vectors = tfidf_vectors([["python", "django"], ["python", "django"], ["бухгалтер", "1с"], []])
    assert cosine(vectors[0], vectors[1]) == pytest.approx(1.0)
    assert cosine(vectors[0], vectors[2]) == 0.0
    assert vectors[3] == {}


@pytest.mark.parametrize("matcher", all_matchers(), ids=lambda m: m.name)
def test_every_matcher_ranks_duplicate_above_other(matcher):
    original, copy, other = matcher.prepare([ORIGINAL, COPY, OTHER])
    duplicate_score = matcher.similarity(original, copy)
    other_score = matcher.similarity(original, other)
    assert 0.0 <= other_score < duplicate_score <= 1.0
    assert matcher.similarity(original, original) == pytest.approx(1.0)


def test_quality_at_threshold():
    scores = {(0, 0): 0.9, (0, 1): 0.6, (1, 0): 0.2, (1, 1): 0.4}
    gold = {(0, 0), (1, 1)}
    strict = quality_at(scores, gold, 0.8)
    assert (strict.precision, strict.recall) == (1.0, 0.5)
    loose = quality_at(scores, gold, 0.4)
    assert loose.precision == pytest.approx(2 / 3)
    assert loose.recall == 1.0
    assert quality_at(scores, gold, 0.95).f1 == 0.0


def test_evaluate_picks_threshold_that_separates_duplicates():
    result = evaluate(all_matchers()[0], [COPY], [ORIGINAL, OTHER], gold={(0, 0)})
    assert result.pairs == 2
    assert result.best.f1 == 1.0
