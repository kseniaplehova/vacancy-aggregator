import random
import zlib
from collections import defaultdict
from itertools import combinations

from .base import Matcher
from .normalize import text_of, word_shingles

PRIME = 4_294_967_311
MAX_HASH = 2**32


class MinHasher:
    def __init__(self, size: int = 64, seed: int = 1):
        self.size = size
        rng = random.Random(seed)
        self.coefficients = [(rng.randrange(1, PRIME), rng.randrange(0, PRIME)) for _ in range(size)]

    def signature(self, items: set[str]) -> tuple[int, ...]:
        hashes = [zlib.crc32(item.encode("utf-8")) for item in items]
        if not hashes:
            return (MAX_HASH,) * self.size
        return tuple(min((a * x + b) % PRIME for x in hashes) for a, b in self.coefficients)


def estimate(a: tuple[int, ...], b: tuple[int, ...]) -> float:
    return sum(x == y for x, y in zip(a, b)) / len(a)


def lsh_candidates(signatures: list[tuple[int, ...]], bands: int = 16) -> set[tuple[int, int]]:
    rows = len(signatures[0]) // bands if signatures else 0
    candidates: set[tuple[int, int]] = set()
    for band in range(bands):
        buckets: dict[tuple[int, ...], list[int]] = defaultdict(list)
        for index, signature in enumerate(signatures):
            buckets[signature[band * rows : (band + 1) * rows]].append(index)
        for bucket in buckets.values():
            candidates.update(combinations(bucket, 2))
    return candidates


class MinHashMatcher(Matcher):
    name = "MinHash (весь текст)"

    def __init__(self, size: int = 64):
        self.hasher = MinHasher(size)

    def prepare(self, records):
        return [self.hasher.signature(word_shingles(text_of(r))) for r in records]

    def similarity(self, a, b) -> float:
        return estimate(a, b)
