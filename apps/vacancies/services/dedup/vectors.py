import math
from collections import Counter

from .base import Matcher
from .normalize import key_of, text_of

Vector = dict[str, float]


def tfidf_vectors(documents: list[list[str]]) -> list[Vector]:
    total = len(documents)
    document_frequency = Counter(word for document in documents for word in set(document))
    vectors = []
    for document in documents:
        vector = {
            word: count * (math.log((1 + total) / (1 + document_frequency[word])) + 1)
            for word, count in Counter(document).items()
        }
        length = math.sqrt(sum(weight * weight for weight in vector.values()))
        vectors.append({word: weight / length for word, weight in vector.items()} if length else {})
    return vectors


def cosine(a: Vector, b: Vector) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(weight * b.get(word, 0.0) for word, weight in a.items())


class TfidfKeyMatcher(Matcher):
    name = "TF-IDF + косинус (название + компания)"

    def prepare(self, records):
        return tfidf_vectors([key_of(r).split() for r in records])

    def similarity(self, a: Vector, b: Vector) -> float:
        return cosine(a, b)


class TfidfTextMatcher(Matcher):
    name = "TF-IDF + косинус (весь текст)"

    def prepare(self, records):
        return tfidf_vectors([text_of(r).split() for r in records])

    def similarity(self, a: Vector, b: Vector) -> float:
        return cosine(a, b)
