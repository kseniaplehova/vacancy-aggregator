"""Редакционное расстояние (расстояние Левенштейна)."""
from .base import Matcher
from .normalize import key_of


def distance(a: str, b: str) -> int:
    """Наименьшее число вставок, удалений и замен символа, превращающих ``a`` в ``b``.

    Классическая динамика по таблице len(a) × len(b); в памяти держатся только
    две строки таблицы. Время — O(len(a) · len(b)).
    """
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a  # короткая строка идёт по столбцам: меньше памяти
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,  # удаление
                    current[j - 1] + 1,  # вставка
                    previous[j - 1] + (char_a != char_b),  # замена или совпадение
                )
            )
        previous = current
    return previous[-1]


def similarity(a: str, b: str) -> float:
    """Расстояние, приведённое к отрезку [0, 1]: 1 — строки равны."""
    longest = max(len(a), len(b))
    return 1.0 if longest == 0 else 1 - distance(a, b) / longest


class LevenshteinMatcher(Matcher):
    """Сравнивает строки «название + компания».

    На полных описаниях метод не применяется: время растёт как произведение
    длин, и пара текстов по 3000 знаков — это 9 миллионов шагов.
    """

    name = "Левенштейн (название + компания)"

    def prepare(self, records):
        return [key_of(r) for r in records]

    def similarity(self, a: str, b: str) -> float:
        return similarity(a, b)
