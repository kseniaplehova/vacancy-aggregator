from .base import Matcher
from .jaccard import JaccardKeyMatcher, JaccardTextMatcher
from .levenshtein import LevenshteinMatcher
from .minhash import MinHashMatcher
from .vectors import TfidfKeyMatcher, TfidfTextMatcher


def all_matchers() -> list[Matcher]:
    return [
        LevenshteinMatcher(),
        JaccardKeyMatcher(),
        TfidfKeyMatcher(),
        JaccardTextMatcher(),
        MinHashMatcher(),
        TfidfTextMatcher(),
    ]


__all__ = [
    "all_matchers",
    "Matcher",
    "JaccardKeyMatcher",
    "JaccardTextMatcher",
    "LevenshteinMatcher",
    "MinHashMatcher",
    "TfidfKeyMatcher",
    "TfidfTextMatcher",
]
