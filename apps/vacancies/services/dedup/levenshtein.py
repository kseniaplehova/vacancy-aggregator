from .base import Matcher
from .normalize import key_of


def distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (char_a != char_b),
                )
            )
        previous = current
    return previous[-1]


def similarity(a: str, b: str) -> float:
    longest = max(len(a), len(b))
    return 1.0 if longest == 0 else 1 - distance(a, b) / longest


class LevenshteinMatcher(Matcher):
    name = "Левенштейн (название + компания)"

    def prepare(self, records):
        return [key_of(r) for r in records]

    def similarity(self, a: str, b: str) -> float:
        return similarity(a, b)
