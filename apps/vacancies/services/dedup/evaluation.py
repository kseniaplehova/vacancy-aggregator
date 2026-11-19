import time
from dataclasses import dataclass
from typing import Any, Sequence

from .base import Matcher

Pair = tuple[int, int]


@dataclass
class Quality:
    threshold: float
    precision: float
    recall: float
    f1: float


@dataclass
class Evaluation:
    method: str
    best: Quality
    prepare_seconds: float
    compare_seconds: float
    pairs: int


def score_pairs(
    matcher: Matcher, left: Sequence[Any], right: Sequence[Any]
) -> tuple[dict[Pair, float], float, float]:
    started = time.perf_counter()
    prepared = matcher.prepare([*left, *right])
    prepare_seconds = time.perf_counter() - started
    left_prepared, right_prepared = prepared[: len(left)], prepared[len(left) :]

    started = time.perf_counter()
    scores = {
        (i, j): matcher.similarity(a, b)
        for i, a in enumerate(left_prepared)
        for j, b in enumerate(right_prepared)
    }
    return scores, prepare_seconds, time.perf_counter() - started


def quality_at(scores: dict[Pair, float], gold: set[Pair], threshold: float) -> Quality:
    found = {pair for pair, score in scores.items() if score >= threshold}
    correct = len(found & gold)
    precision = correct / len(found) if found else 0.0
    recall = correct / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if correct else 0.0
    return Quality(threshold, precision, recall, f1)


def evaluate(
    matcher: Matcher,
    left: Sequence[Any],
    right: Sequence[Any],
    gold: set[Pair],
    thresholds: Sequence[float] = tuple(round(0.05 * step, 2) for step in range(1, 20)),
) -> Evaluation:
    scores, prepare_seconds, compare_seconds = score_pairs(matcher, left, right)
    best = max((quality_at(scores, gold, t) for t in thresholds), key=lambda q: (q.f1, q.threshold))
    return Evaluation(matcher.name, best, prepare_seconds, compare_seconds, len(scores))
