from .base import Matcher
from .normalize import char_shingles, key_of, text_of, word_shingles


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    common = len(a & b)
    return common / (len(a) + len(b) - common)


class JaccardKeyMatcher(Matcher):
    name = "Жаккар (название + компания)"

    def prepare(self, records):
        return [char_shingles(key_of(r)) for r in records]

    def similarity(self, a: set, b: set) -> float:
        return jaccard(a, b)


class JaccardTextMatcher(Matcher):
    name = "Жаккар (весь текст)"

    def prepare(self, records):
        return [word_shingles(text_of(r)) for r in records]

    def similarity(self, a: set, b: set) -> float:
        return jaccard(a, b)
